"""Bounded Phase A evidence probes; never point these at an external service.

Only fresh credentials, in-memory keys, synthetic readings and owned loopback
sockets are used. A zero exit status means the stated observations reproduced;
it does NOT mean that the current application is secure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

from common import crypto, protocol  # noqa: E402
from common.metrics import Metrics  # noqa: E402
from cloud.cloud import CloudServer, SessionRegistry  # noqa: E402
from cloud.store import ReadingStore  # noqa: E402
from gateway.cloud_channel import CloudChannel  # noqa: E402
from gateway.processing import build_protected_reading  # noqa: E402


def worker(connections: int) -> None:
    """Use the unchanged CloudServer handler behind a bounded listener.

    This deliberately replaces only the unlimited accept/thread loop, not the
    handshake, authentication, processing, replay guard or storage behavior.
    No health endpoint is opened and no application state is read or written.
    """
    logging.basicConfig(level=logging.WARNING)
    private_key = crypto.generate_mlkem_keypair()
    registry, store, metrics = SessionRegistry(), ReadingStore(), Metrics()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(15)
        server = CloudServer("127.0.0.1", listener.getsockname()[1],
                             "phase-a-cloud", registry, private_key,
                             crypto.public_key_bytes(private_key.public_key()),
                             store, metrics)
        print(json.dumps({"port": listener.getsockname()[1]}), flush=True)
        for index in range(connections):
            conn, addr = listener.accept()
            server._handle(conn, addr)
            print(json.dumps({"index": index, "store_count": store.count(),
                              "stored_sequences": [r["sequence"] for r in store.recent()],
                              "active_sessions": registry.count(),
                              "metrics": metrics.snapshot()}), flush=True)


def line_reader(pipe, output):
    for line in pipe:
        output.put(line)


def receive_line(output):
    return json.loads(output.get(timeout=20))


def reading(sequence):
    return json.dumps({"device_id": "phase-a-synthetic-victim",
                       "timestamp": "2026-10-16T00:00:00Z",
                       "temperature_c": 21.0, "sequence": sequence}).encode()


def exchange(port, captured_request, sequence=None, *, mismatched=False):
    """The attacker receives only captured request bytes, never the PSK."""
    observed = {"public_key_received": False, "established": False}
    with socket.create_connection(("127.0.0.1", port), timeout=3) as conn:
        conn.settimeout(3)
        stream = conn.makefile("rb")
        try:
            conn.sendall(captured_request)
            public_reply = protocol.read_message(stream)
            observed["public_key_received"] = True
            public = crypto.load_public_key(protocol.b64d(public_reply["public_key"]))
            shared, ciphertext = crypto.mlkem_encapsulate(public)
            session = secrets.token_hex(8)
            conn.sendall(protocol.encode_message({
                "type": protocol.MSG_MLKEM_ENCAPS,
                "gateway_id": "different-unauthenticated-encaps-id",
                "session_id": session,
                "ciphertext": protocol.b64e(bytes(len(ciphertext)) if mismatched else ciphertext),
            }))
            reply = protocol.read_message(stream)
            observed["established"] = reply["type"] == protocol.MSG_MLKEM_ESTABLISHED
            observed["session_id_matched"] = reply["session_id"] == session
            if sequence is not None:
                key = crypto.derive_session_key(shared)
                conn.sendall(protocol.encode_message(build_protected_reading(
                    reading(sequence), key, session)))
        except (protocol.ConnectionClosedError, OSError):
            observed["connection_closed"] = True
        finally:
            # makefile holds another socket reference: explicitly close it so
            # the unchanged handler sees EOF and its result is observable.
            stream.close()
    return observed


def fake_cloud_confirmation(*, wrong_session=False):
    """Pinned public key responder with no access to its private key."""
    public = crypto.public_key_bytes(crypto.generate_mlkem_keypair().public_key())
    previous_pin = os.environ.get("CLOUD_PUBLIC_KEY_SHA256")
    os.environ["CLOUD_PUBLIC_KEY_SHA256"] = crypto.public_key_fingerprint(public)
    observations = {"decapsulation_performed": False}
    failure = []
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(5)

        def respond():
            try:
                conn, _ = listener.accept()
                with conn:
                    conn.settimeout(5)
                    with conn.makefile("rb") as stream:
                        protocol.read_message(stream)
                        conn.sendall(protocol.encode_message({"type": protocol.MSG_MLKEM_PUBKEY,
                            "cloud_id": "phase-a-pinned-public-key-only",
                            "public_key": protocol.b64e(public)}))
                        encaps = protocol.read_message(stream)
                        conn.sendall(protocol.encode_message({"type": protocol.MSG_MLKEM_ESTABLISHED,
                            "session_id": "wrong-session" if wrong_session else encaps["session_id"],
                            "status": "ok"}))
                        if not wrong_session:
                            observations["protected_payload_received"] = (
                                protocol.read_message(stream)["type"] == protocol.MSG_PROTECTED_READING)
            except Exception as exc:
                failure.append(type(exc).__name__)

        thread = threading.Thread(target=respond, daemon=True)
        thread.start()
        channel = CloudChannel("phase-a-gateway", "127.0.0.1", listener.getsockname()[1],
                               Metrics(), auto_reconnect=False, gateway_key=os.urandom(32))
        try:
            observations["gateway_reports_established"] = channel.connect_and_establish(max_attempts=1)
            if channel.is_established():
                channel.send_reading(reading(1))
            if channel._sock:
                channel._sock.close()
            thread.join(timeout=6)
            assert not thread.is_alive(), "owned responder failed to stop"
            assert not failure, failure
        finally:
            if previous_pin is None:
                os.environ.pop("CLOUD_PUBLIC_KEY_SHA256", None)
            else:
                os.environ["CLOUD_PUBLIC_KEY_SHA256"] = previous_pin
    return observations


def recorded_key_compromise():
    """Exercise current crypto wrappers on a synthetic recorded transcript."""
    cloud_private = crypto.generate_mlkem_keypair()
    wrong_private = crypto.generate_mlkem_keypair()
    archive = []
    for index in range(2):
        shared, ciphertext = crypto.mlkem_encapsulate(cloud_private.public_key())
        session = f"recorded-session-{index}"
        envelope = crypto.encrypt_session_payload(crypto.derive_session_key(shared),
                    reading(index + 1), protocol.session_message_aad(session))
        archive.append((ciphertext, session, envelope))
    del shared
    recovered, wrong_rejected = 0, 0
    for ciphertext, session, envelope in archive:
        key = crypto.derive_session_key(crypto.mlkem_decapsulate(cloud_private, ciphertext))
        recovered += crypto.decrypt_session_payload(key, envelope,
                         protocol.session_message_aad(session)) == reading(recovered + 1)
        try:
            wrong_key = crypto.derive_session_key(crypto.mlkem_decapsulate(wrong_private, ciphertext))
            crypto.decrypt_session_payload(wrong_key, envelope, protocol.session_message_aad(session))
        except crypto.CryptoError:
            wrong_rejected += 1
    return {"synthetic_recorded_sessions": len(archive), "recovered_after_private_key_disclosure": recovered,
            "wrong_private_key_rejected": wrong_rejected, "network_capture": False}


def run(output: Path, raw_dir: Path):
    # Validate before creating either output parent: an accidental checkout
    # path must never touch original state, and prior raw evidence is retained.
    raw_dir = raw_dir.resolve()
    if raw_dir.is_relative_to(ROOT):
        raise ValueError("raw directory must be outside the repository")
    if raw_dir.exists():
        raise ValueError("raw directory must be new; existing evidence is never reused")
    raw_dir.mkdir(parents=True, exist_ok=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    gateway_key = os.urandom(32)
    auth = crypto.build_gateway_auth("phase-a-gateway", gateway_key)
    request = {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
               "gateway_id": "phase-a-gateway", **auth}
    captured = protocol.encode_message(request)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               GATEWAY_KEYS_JSON=json.dumps({"phase-a-gateway": gateway_key.hex()}))
    records = []
    with (raw_dir / "cloud-stderr.log").open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                                    "--worker", "--connections", "7"], env=env,
                                   cwd=ROOT, stdout=subprocess.PIPE, stderr=stderr,
                                   text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        output_queue = queue.Queue()
        threading.Thread(target=line_reader, args=(process.stdout, output_queue), daemon=True).start()
        try:
            port = receive_line(output_queue)["port"]
            cases = [("valid_control", captured, 1, False),
                     ("captured_auth_new_kem_sequence_poison", captured, 99999, False),
                     ("legitimate_lower_sequence_suppressed", captured, 2, False),
                     ("captured_auth_plausible_replacement", captured, 100000, False),
                     ("bad_tag_control", protocol.encode_message(dict(request, auth_tag=protocol.b64e(bytes(16)))), None, False),
                     ("unknown_gateway_control", protocol.encode_message(dict(request, gateway_id="unknown")), None, False),
                     ("wrong_kem_shared_secret", captured, 100001, True)]
            for name, wire, sequence, mismatched in cases:
                observation = exchange(port, wire, sequence, mismatched=mismatched)
                records.append({"case": name, "client": observation, "cloud": receive_line(output_queue)})
            assert process.wait(timeout=5) == 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
    checks = {
        "valid_control_stored": records[0]["cloud"]["store_count"] == 1,
        "captured_auth_replayed_new_kem_stored": records[1]["cloud"]["store_count"] == 2,
        "legitimate_lower_sequence_suppressed": records[2]["cloud"]["store_count"] == 2,
        "replacement_stored": records[3]["cloud"]["store_count"] == 3,
        "bad_tag_rejected_before_public_key": not records[4]["client"]["public_key_received"],
        "unknown_id_rejected_before_public_key": not records[5]["client"]["public_key_received"],
        "cloud_acknowledges_wrong_shared_secret": records[6]["client"]["established"],
        "wrong_shared_secret_payload_rejected": records[6]["cloud"]["store_count"] == 3,
        "sessions_evicted_after_each_disconnect": all(r["cloud"]["active_sessions"] == 0 for r in records),
    }
    fake = fake_cloud_confirmation()
    fake_negative = fake_cloud_confirmation(wrong_session=True)
    recorded = recorded_key_compromise()
    checks.update({"gateway_accepts_public_key_only_responder": fake["gateway_reports_established"],
                   "fake_cloud_receives_encrypted_payload": fake["protected_payload_received"],
                   "wrong_session_ack_rejected": not fake_negative["gateway_reports_established"],
                   "recorded_sessions_recovered_with_private_key": recorded["recovered_after_private_key_disclosure"] == 2,
                   "wrong_private_key_cannot_decrypt": recorded["wrong_private_key_rejected"] == 2})
    result = {"schema": "phase-a-security-evidence/v1", "utc": datetime.now(timezone.utc).isoformat(),
              "claim": "risk reproduction, not remediation or deployment acceptance",
              "isolation": "fresh process env, fresh in-memory keys, owned 127.0.0.1 port-0 listeners; no existing state",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "runtime": {"python": sys.version.split()[0], "cryptography": __import__("cryptography").__version__},
              "checks": checks, "all_observations_reproduced": all(checks.values()),
              "network_cases": records, "gateway_key_confirmation": fake,
              "gateway_key_confirmation_negative_control": fake_negative,
              "long_term_key_compromise": recorded}
    rendered = json.dumps(result, indent=2) + "\n"
    output.write_text(rendered, encoding="utf-8")
    (raw_dir / "security-result.json").write_text(rendered, encoding="utf-8")
    print(json.dumps({"checks": checks, "all_observations_reproduced": all(checks.values())}))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--connections", type=int, default=7, help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/phase-a/evidence/security/security-result.json")
    parser.add_argument("--raw-dir", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.connections)
    else:
        if args.raw_dir is None:
            parser.error("--raw-dir is required; use an isolated artifact directory outside the repository")
        raise SystemExit(run(args.output, args.raw_dir))
