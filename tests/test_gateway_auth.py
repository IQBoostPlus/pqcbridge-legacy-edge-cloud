"""Fail-first regression tests for P08 BF-01: gateway-to-cloud
authentication.

Baseline defect (reproduced in P08): the cloud verified its OWN
ML-KEM public key via fingerprint pinning (F-01) but did NOT
authenticate the connecting gateway. `gateway_id` was self-declared,
so any unauthenticated client could complete the ML-KEM handshake,
establish a cloud-accepted session and inject readings (BF-01 -> the
BF-06/BF-07 compound attack).

Expected behavior after P08: the gateway's handshake request carries
an AEAD tag over its identity claim, verified by the cloud BEFORE the
session is accepted. Unknown gateways, wrong credentials and tampered
identity claims are rejected; a valid gateway still works.
"""
import json
import socket
import threading
import time

import pytest

from cloud import processing as cloud_processing
from cloud.cloud import CloudServer, SessionRegistry
from cloud.store import ReadingStore
from common import config, crypto, protocol
from common.metrics import Metrics


READING_BYTES = (
    b'{"device_id":"dev-01","timestamp":"2026-09-08T00:00:00+00:00",'
    b'"temperature_c":21.5,"unit":"celsius","sequence":1}')


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_cloud():
    key = crypto.generate_mlkem_keypair()
    public = crypto.public_key_bytes(key.public_key())
    registry = SessionRegistry()
    metrics = Metrics()
    server = CloudServer("127.0.0.1", _free_port(), "cloud-test", registry,
                         key, public, ReadingStore(), metrics)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", server._port),
                                          timeout=1):
                return server, registry, metrics
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("cloud test server did not start")


def _connect(port):
    sock = socket.create_connection(("127.0.0.1", port), timeout=5)
    sock.settimeout(5)
    return sock


def _authenticated_handshake(port, gateway_id, key, session_id="sess-1"):
    """Full ML-KEM handshake WITH gateway authentication."""
    sock = _connect(port)
    stream = sock.makefile("rb")
    auth = crypto.build_gateway_auth(gateway_id, key)
    sock.sendall(protocol.encode_message({
        "type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
        "gateway_id": gateway_id,
        **auth,
    }))
    reply = json.loads(stream.readline())
    assert reply["type"] == protocol.MSG_MLKEM_PUBKEY
    shared, ct = crypto.mlkem_encapsulate(
        crypto.load_public_key(protocol.b64d(reply["public_key"])))
    sock.sendall(protocol.encode_message({
        "type": protocol.MSG_MLKEM_ENCAPS,
        "gateway_id": gateway_id,
        "session_id": session_id,
        "ciphertext": protocol.b64e(ct),
    }))
    est = json.loads(stream.readline())
    assert est["type"] == protocol.MSG_MLKEM_ESTABLISHED
    return sock, stream, crypto.derive_session_key(shared)


def _send_protected(sock, session_key, session_id):
    env = crypto.encrypt_session_payload(
        session_key, READING_BYTES, protocol.session_message_aad(session_id))
    sock.sendall(protocol.encode_message({
        "type": protocol.MSG_PROTECTED_READING,
        "session_id": session_id,
        **env,
    }))


# --- unit level: request validation requires auth fields ----------------------

def test_parse_mlkem_request_requires_auth_fields():
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_request(
            {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY, "gateway_id": "gw-01"})


def test_parse_mlkem_request_accepts_authenticated_request():
    gateway_id = cloud_processing.parse_mlkem_request({
        "type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
        "gateway_id": "gw-01",
        "auth_nonce": "AA==",
        "auth_tag": "AA==",
    })
    assert gateway_id == "gw-01"


def test_verify_gateway_request_auth_valid():
    auth = crypto.build_gateway_auth("gw-01", config.gateway_key("gw-01"))
    request = {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
               "gateway_id": "gw-01", **auth}
    cloud_processing.verify_gateway_request_auth(
        request, config.gateway_key("gw-01"))  # must not raise


def test_verify_gateway_request_auth_rejects_wrong_key():
    auth = crypto.build_gateway_auth("gw-01", bytes.fromhex("ab" * 32))
    request = {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
               "gateway_id": "gw-01", **auth}
    with pytest.raises(crypto.AuthenticationError):
        cloud_processing.verify_gateway_request_auth(
            request, config.gateway_key("gw-01"))


def test_verify_gateway_request_auth_rejects_tampered_identity():
    auth = crypto.build_gateway_auth("gw-01", config.gateway_key("gw-01"))
    request = {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
               "gateway_id": "gw-01", **auth}
    request["gateway_id"] = "gw-02"  # identity changed after the tag was made
    with pytest.raises(crypto.AuthenticationError):
        cloud_processing.verify_gateway_request_auth(
            request, bytes.fromhex("cd" * 32))


# --- real TCP: unauthenticated gateway must NOT establish a session ------------

def test_unauthenticated_gateway_cannot_inject_reading():
    server, registry, metrics = _start_cloud()
    errors_before = metrics.snapshot()["counters"].get("errors", 0)
    sock = _connect(server._port)
    # BF-01: no auth fields at all (self-declared identity only).
    sock.sendall(protocol.encode_message({
        "type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
        "gateway_id": "attacker-gw",
    }))
    # Rejection proof (metric-based, like the P05/P06 live-TCP tests):
    # the session is never registered, nothing is stored, and the
    # malformed request is counted as a controlled error.
    time.sleep(0.4)
    assert registry.count() == 0
    assert server._store.count() == 0
    assert metrics.snapshot()["counters"].get("errors", 0) \
        >= errors_before + 1
    sock.close()


def test_unknown_gateway_rejected():
    server, registry, metrics = _start_cloud()
    rejected_before = metrics.snapshot()["counters"].get(
        "messages_rejected", 0)
    sock = _connect(server._port)
    auth = crypto.build_gateway_auth("gw-999", bytes.fromhex("ab" * 32))
    sock.sendall(protocol.encode_message({
        "type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
        "gateway_id": "gw-999",
        **auth,
    }))
    time.sleep(0.4)
    assert registry.count() == 0
    assert metrics.snapshot()["counters"].get("messages_rejected", 0) \
        >= rejected_before + 1
    sock.close()


def test_valid_gateway_authentication_establishes_and_forwards():
    server, registry, metrics = _start_cloud()
    sock, stream, session_key = _authenticated_handshake(
        server._port, "gw-01", config.gateway_key("gw-01"))
    assert registry.count() == 1
    _send_protected(sock, session_key, "sess-1")
    deadline = time.time() + 5
    while time.time() < deadline and server._store.count() == 0:
        time.sleep(0.05)
    assert server._store.count() == 1
    sock.close()
