"""Public framing and fresh-process TLS policy boundaries."""
import io
import os
from pathlib import Path
import subprocess
import sys
import socket
from contextlib import contextmanager
import threading
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deploy" / "phase_b" / "tls-policy.cnf"


def test_unconfigured_bootstrap_refuses_before_application_load(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    env = dict(os.environ)
    env.pop("OPENSSL_CONF", None)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "common.secure_bootstrap", "cloud",
         "--config", str(config)], cwd=ROOT, env=env, capture_output=True,
        text=True, timeout=5,
    )
    assert result.returncode == 3
    assert "TLS startup rejected" in result.stderr
    assert "OPENSSL_CONF" in result.stderr


def test_read_frame_preserves_next_frame_and_rejects_ambiguous_json():
    from common.secure_transport import TransportError, read_frame
    stream = io.BytesIO(b'{"temperature_c":21.5}\n{"sequence":2}\n')
    assert read_frame(stream) == {"temperature_c": 21.5}
    assert read_frame(stream) == {"sequence": 2}
    for body in (b'{"x":1,"x":2}\n', b'{"x":NaN}\n', b'{"x":Infinity}\n',
                 b'{"x":1e999}\n', b'[]\n', b'{"x":1}', b'\xff\n', b''):
        with pytest.raises(TransportError):
            read_frame(io.BytesIO(body))


def test_send_frame_bound_and_invalid_numbers_never_reach_socket():
    from common.secure_transport import TransportError, read_frame, send_frame
    sender, receiver = socket.socketpair()
    with sender, receiver:
        sender.settimeout(1)
        receiver.settimeout(.2)
        send_frame(sender, {"unit": "celsius", "temperature_c": 21.5})
        assert read_frame(receiver.makefile("rb")) == {"temperature_c": 21.5, "unit": "celsius"}
        for value in ({"x": float("nan")}, {"x": float("inf")}, {"x": "x" * 20}, [1]):
            with pytest.raises(TransportError):
                send_frame(sender, value, max_bytes=16)
        with pytest.raises(TimeoutError):
            receiver.recv(1)
    with pytest.raises(TransportError):
        read_frame(io.BytesIO(b'{"x":123}\n'), max_bytes=5)


@pytest.mark.parametrize("role", ["client", "server"])
@pytest.mark.parametrize("case", ["missing", "wrong", "override", "early_ssl", "early_hashlib"])
def test_fresh_process_refuses_uncontrolled_tls_policy(tmp_path, case, role):
    config = tmp_path / "tls.cnf"
    env = dict(os.environ)
    for name in ("OPENSSL_CONF", "OPENSSL_CONF_INCLUDE", "OPENSSL_MODULES", "OPENSSL_ENGINES"):
        env.pop(name, None)
    env["OPENSSL_CONF"] = str(config)
    code = f"from common.secure_transport import {role}_context;{role}_context({{}})"
    if case == "wrong":
        config.write_bytes(POLICY.read_bytes().replace(b"X25519MLKEM768", b"X25519"))
    elif case != "missing":
        config.write_bytes(POLICY.read_bytes())
    if case == "override":
        env["OPENSSL_MODULES"] = str(tmp_path)
    if case == "early_ssl":
        code = "import ssl;" + code
    if case == "early_hashlib":
        code = "import hashlib;" + code
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                            env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode != 0
    assert "TransportError" in result.stderr
    assert "ImportError" not in result.stderr


def test_direct_application_entrypoint_requires_bootstrap_even_with_policy_env():
    env = dict(os.environ, OPENSSL_CONF=str(POLICY), PQCBRIDGE_TLS_INITIALIZED="1")
    result = subprocess.run(
        [sys.executable, "-B", "-c", "from common.secure_transport import require_initialized;require_initialized()"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode != 0
    assert "secure bootstrap is required" in result.stderr


@contextmanager
def tcp_pair():
    with socket.socket() as listener:
        listener.settimeout(2)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=2) as sender:
            receiver, _ = listener.accept()
            with receiver:
                receiver.settimeout(1)
                yield sender, receiver


def test_coalesced_source_frames_stay_readable_without_new_network_input():
    from common.secure_transport import SocketFrameReader, read_frame
    with tcp_pair() as (sender, receiver):
        sender.sendall(b'{"type":"hello"}\n{"sequence":1}\n{"sequence":2}\n')
        with SocketFrameReader(receiver) as reader:
            reader.set_deadline(1)
            assert read_frame(reader) == {"type": "hello"}
            for sequence in (1, 2):
                assert reader.wait_readable(.05)
                reader.set_deadline(1)
                assert read_frame(reader) == {"sequence": sequence}
            assert not reader.wait_readable(.02)
        # Closing a reader leaves the connection under its owner's control.
        sender.sendall(b"x")
        assert receiver.recv(1) == b"x"


def test_continuous_trickle_cannot_extend_a_whole_frame_deadline():
    from common.secure_transport import SocketFrameReader, read_frame
    with tcp_pair() as (sender, receiver):
        stopped = threading.Event()

        def trickle():
            try:
                for byte in b'{"marker":"' + b"x" * 60 + b'"}\n':
                    if stopped.is_set():
                        break
                    sender.sendall(bytes([byte]))
                    if stopped.wait(.035):
                        break
            except OSError:
                pass

        producer = threading.Thread(target=trickle)
        producer.start()
        try:
            with SocketFrameReader(receiver) as reader:
                reader.set_deadline(.2)
                started = time.monotonic()
                with pytest.raises(TimeoutError):
                    read_frame(reader)
                assert time.monotonic() - started < .8
        finally:
            stopped.set()
            producer.join(timeout=1)
        assert not producer.is_alive()
