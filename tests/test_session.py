"""Fail-first regression tests for F-07 (P04.9): session lifecycle.

Uses a tiny scriptable TCP 'cloud' to exercise CloudChannel without
the full stack. Baseline behavior: no state machine, no reconnect,
the session stayed 'established' forever after a cloud failure.

Tests cover (P04 section 13): normal establishment, failed send,
session invalidation, reconnect, new session id per attempt, health
state, malformed handshake survival, and pin-mismatch rejection.
"""
import socket
import struct
import threading
import time

import pytest

from common import crypto, protocol
from common.metrics import Metrics
from gateway.cloud_channel import CloudChannel, State


class FakeCloud:
    """A scriptable TCP server that speaks just enough of the cloud
    handshake protocol for the test case."""

    def __init__(self, handler):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(4)
        self.port = self._server.getsockname()[1]
        self._handler = handler
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop,
                                        daemon=True)
        self._thread.start()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _ = self._server.accept()
            except OSError:
                break
            threading.Thread(target=self._handler, args=(conn,),
                             daemon=True).start()

    def close(self):
        self._running = False
        self._server.close()


def _pin_env(monkeypatch, key):
    raw = crypto.public_key_bytes(key.public_key())
    monkeypatch.setenv("CLOUD_PUBLIC_KEY_SHA256",
                       crypto.public_key_fingerprint(raw))


def _success_handler(key):
    def handler(conn):
        try:
            with conn:
                stream = conn.makefile("rb")
                protocol.read_message(stream)  # mlkem_request_pubkey
                conn.sendall(protocol.encode_message({
                    "type": protocol.MSG_MLKEM_PUBKEY,
                    "cloud_id": "test-cloud",
                    "public_key": protocol.b64e(
                        crypto.public_key_bytes(key.public_key())),
                }))
                encaps = protocol.read_message(stream)
                conn.sendall(protocol.encode_message({
                    "type": protocol.MSG_MLKEM_ESTABLISHED,
                    "session_id": encaps["session_id"],
                    "status": "ok",
                }))
        except protocol.ConnectionClosedError:
            pass  # the client gave up on the handshake - normal in tests
    return handler


def _rst_after_handshake_handler(key):
    """Like _success_handler but forces a TCP RST after the handshake
    so the client's next send fails immediately."""

    def handler(conn):
        try:
            with conn:
                stream = conn.makefile("rb")
                protocol.read_message(stream)
                conn.sendall(protocol.encode_message({
                    "type": protocol.MSG_MLKEM_PUBKEY,
                    "cloud_id": "test-cloud",
                    "public_key": protocol.b64e(
                        crypto.public_key_bytes(key.public_key())),
                }))
                encaps = protocol.read_message(stream)
                conn.sendall(protocol.encode_message({
                    "type": protocol.MSG_MLKEM_ESTABLISHED,
                    "session_id": encaps["session_id"],
                    "status": "ok",
                }))
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                struct.pack("ii", 1, 0))
        except protocol.ConnectionClosedError:
            pass  # the client gave up on the handshake - normal in tests
    return handler


def _channel(port, metrics=None, auto_reconnect=False):
    return CloudChannel("gw-01", "127.0.0.1", port,
                        metrics or Metrics(),
                        auto_reconnect=auto_reconnect)


# --- normal establishment -----------------------------------------------------

def test_establishment_success(monkeypatch):
    key = crypto.generate_mlkem_keypair()
    _pin_env(monkeypatch, key)
    cloud = FakeCloud(_success_handler(key))
    channel = _channel(cloud.port)
    assert channel.connect_and_establish(max_attempts=2) is True
    assert channel.state is State.ESTABLISHED
    assert channel.session_id


def test_health_state_starts_disconnected():
    channel = _channel(1)
    assert channel.state is State.DISCONNECTED
    assert channel.state.value == "disconnected"
    assert not channel.is_established()


# --- malformed handshake must not crash the gateway (F-03) -------------------

def test_malformed_pubkey_reply_fails_cleanly(monkeypatch):
    def bad_handler(conn):
        with conn:
            stream = conn.makefile("rb")
            protocol.read_message(stream)
            # missing public_key (P02 demo D payload)
            conn.sendall(protocol.encode_message(
                {"type": protocol.MSG_MLKEM_PUBKEY, "cloud_id": "x"}))

    metrics = Metrics()
    cloud = FakeCloud(bad_handler)
    channel = CloudChannel("gw-01", "127.0.0.1", cloud.port, metrics,
                           auto_reconnect=False)
    assert channel.connect_and_establish(max_attempts=1) is False
    assert metrics.snapshot()["counters"]["errors"] >= 1
    assert channel.state is State.DISCONNECTED


# --- pin mismatch must reject the handshake (F-01) ----------------------------

def test_pin_mismatch_rejected(monkeypatch):
    cloud_key = crypto.generate_mlkem_keypair()
    other_key = crypto.generate_mlkem_keypair()
    monkeypatch.setenv(
        "CLOUD_PUBLIC_KEY_SHA256",
        crypto.public_key_fingerprint(
            crypto.public_key_bytes(other_key.public_key())))
    metrics = Metrics()
    cloud = FakeCloud(_success_handler(cloud_key))
    channel = CloudChannel("gw-01", "127.0.0.1", cloud.port, metrics,
                           auto_reconnect=False)
    assert channel.connect_and_establish(max_attempts=1) is False
    assert metrics.snapshot()["counters"]["errors"] >= 1


# --- session invalidation and reconnect (F-07) --------------------------------

def test_failed_send_invalidates_session(monkeypatch):
    key = crypto.generate_mlkem_keypair()
    _pin_env(monkeypatch, key)
    cloud = FakeCloud(_rst_after_handshake_handler(key))
    channel = _channel(cloud.port)
    assert channel.connect_and_establish(max_attempts=2)
    time.sleep(0.3)  # let the RST arrive
    with pytest.raises(crypto.CryptoError):
        channel.send_reading(b"{}")
    assert channel.state is State.FAILED
    assert channel.session_key is None
    assert not channel.is_established()


def test_new_session_id_per_establishment_attempt(monkeypatch):
    key = crypto.generate_mlkem_keypair()
    _pin_env(monkeypatch, key)
    cloud = FakeCloud(_success_handler(key))
    channel = _channel(cloud.port)
    assert channel.connect_and_establish(max_attempts=2)
    first_session_id = channel.session_id
    channel._invalidate()
    assert channel.connect_and_establish(max_attempts=2)
    assert channel.session_id != first_session_id
