"""Bounded, independently encoded peer for the existing simulated wire format.

This is compatibility/performance evidence, not a real-device protocol adapter.
No production protocol/crypto/sensor helpers are used by the peer. The baseline
launch helper supplies isolated real gateway/cloud processes and fresh keys.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import math
import os
from pathlib import Path
import socket
import sys
import time

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

if __package__:
    from .baseline import isolated_stack
else:
    from baseline import isolated_stack


def compact(value: dict) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def wire(value: dict) -> bytes:
    return compact(value) + b"\n"


def encode64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def hello(device_id: str, key: bytes) -> dict:
    claims = {"device_id": device_id, "capabilities": ["chacha20-poly1305"]}
    nonce = os.urandom(12)
    return {
        "type": "hello", **claims, "auth_nonce": encode64(nonce),
        "auth_tag": encode64(ChaCha20Poly1305(key).encrypt(
            nonce, b"", compact(claims))),
    }


def reading(device_id: str, key: bytes, sequence: int) -> tuple[dict, dict]:
    value = {
        "device_id": device_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "temperature_c": 23.5, "unit": "celsius", "sequence": sequence,
    }
    return value, protect_reading(device_id, key, sequence, value)


def protect_reading(device_id: str, key: bytes, sequence: int, value: dict) -> dict:
    nonce = os.urandom(12)
    ciphertext = ChaCha20Poly1305(key).encrypt(
        nonce, compact(value), f"{device_id}:{sequence}".encode("utf-8"))
    envelope = {
        "type": "legacy_reading", "device_id": device_id, "seq": sequence,
        "nonce": encode64(nonce), "ciphertext": encode64(ciphertext),
    }
    return envelope


def wait_for(callback, predicate, label: str, seconds: float = 8.0):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        last = callback()
        if predicate(last):
            return last
        time.sleep(0.02)
    raise RuntimeError(f"deadline exceeded: {label}")


def counters(stack) -> dict:
    return stack.gateway_health().get("counters", {})


def rejected(stack, previous: int) -> dict:
    return wait_for(lambda: counters(stack),
                    lambda value: value.get("messages_rejected", 0) > previous,
                    "gateway rejection counter")


def expect_closed(stack, packet: bytes) -> None:
    with socket.create_connection(("127.0.0.1", stack.gateway_port), 3) as peer:
        peer.settimeout(3)
        peer.sendall(packet)
        peer.shutdown(socket.SHUT_WR)
        try:
            received = peer.recv(1)
        except ConnectionResetError:
            received = b""
        if received:
            raise RuntimeError("rejected peer received unexpected application data")


def percentile(samples: list[float], fraction: float) -> float:
    return sorted(samples)[max(0, math.ceil(len(samples) * fraction) - 1)]


def execute(stack) -> dict:
    samples = []
    sizes = []
    negatives = []
    with socket.create_connection(("127.0.0.1", stack.gateway_port), 3) as peer:
        peer.settimeout(3)
        greeting = hello(stack.device_id, stack.device_key)
        peer.sendall(wire(greeting))
        nominal_start = time.perf_counter()
        last_packet = None
        # Repository nominal interval; three observations span two intervals.
        for index in range(3):
            delay = nominal_start + index * 5.0 - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            payload, packet = reading(stack.device_id, stack.device_key, index + 1)
            started = time.perf_counter()
            peer.sendall(wire(packet))
            observed = wait_for(stack.readings,
                                lambda rows: payload in rows,
                                "independent reading available in cloud readback")
            ended = time.perf_counter()
            if payload not in observed:
                raise RuntimeError("cloud readback changed independent payload")
            samples.append({
                "sequence": index + 1, "send_monotonic_s": started,
                "observed_monotonic_s": ended,
                "readback_latency_upper_bound_ms": (ended - started) * 1000,
            })
            sizes.append({"plaintext_bytes": len(compact(payload)),
                          "wire_bytes": len(wire(packet))})
            last_packet = packet

        previous = counters(stack).get("messages_rejected", 0)
        peer.sendall(wire(last_packet))
        rejected(stack, previous)
        negatives.append({"case": "exact_reading_replay", "outcome": "rejected"})

        payload, valid = reading(stack.device_id, stack.device_key, 4)
        tampered = {**valid, "seq": 999999}
        previous = counters(stack).get("messages_rejected", 0)
        peer.sendall(wire(tampered))
        rejected(stack, previous)
        peer.sendall(wire(valid))
        wait_for(stack.readings, lambda rows: payload in rows,
                 "valid next reading after unauthenticated sequence tampering")
        negatives.append({"case": "outer_sequence_tampering",
                          "outcome": "rejected; valid next sequence delivered"})

        for label, device_id, key in (
                ("wrong_device_key", stack.device_id, os.urandom(32)),
                ("unknown_device", "unregistered-phase-a", os.urandom(32))):
            previous = counters(stack).get("messages_rejected", 0)
            expect_closed(stack, wire(hello(device_id, key)))
            rejected(stack, previous)
            negatives.append({"case": label, "outcome": "rejected_and_closed"})

        previous_errors = counters(stack).get("errors", 0)
        expect_closed(stack, b'{"type":\n')
        wait_for(lambda: counters(stack),
                 lambda value: value.get("errors", 0) > previous_errors,
                 "malformed input counted as controlled error")
        negatives.append({"case": "malformed_json_hello",
                          "outcome": "closed; controlled error counter increased"})

        # Burst is a diagnostic profile, not a newly frozen business workload.
        initial_count = stack.cloud_health()["stored_readings"]
        if initial_count != 4:
            raise RuntimeError(f"unexpected pre-burst cloud count: {initial_count}")
        burst_start = time.perf_counter()
        for sequence in range(5, 105):
            _, packet = reading(stack.device_id, stack.device_key, sequence)
            peer.sendall(wire(packet))
        after = wait_for(stack.cloud_health,
                         lambda value: value["stored_readings"] >= 104,
                         "100 burst readings observed by cloud")
        burst_seconds = time.perf_counter() - burst_start
        tail = stack.readings()
        if after["stored_readings"] != 104:
            raise RuntimeError("rejected traffic added unexpected cloud records")
        if [row["sequence"] for row in tail] != list(range(95, 105)):
            raise RuntimeError("cloud readback tail did not match burst sequence")
        if any(row["temperature_c"] != 23.5 for row in tail):
            raise RuntimeError("cloud readback changed burst content")

        # Reproduce payload/outer-identity binding after timed profiles so the
        # deliberate poisoning cannot contaminate nominal measurements.
        foreign, _ = reading("unassigned-device-phase-a", stack.device_key, 1)
        peer.sendall(wire(protect_reading(
            stack.device_id, stack.device_key, 105, foreign)))
        wait_for(stack.readings, lambda rows: foreign in rows,
                 "foreign inner identity accepted through authenticated device")
        poisoned, _ = reading(stack.device_id, stack.device_key, 999999)
        peer.sendall(wire(protect_reading(
            stack.device_id, stack.device_key, 106, poisoned)))
        wait_for(stack.readings, lambda rows: poisoned in rows,
                 "inner sequence distinct from authenticated outer sequence")
        cloud_rejected_before = stack.cloud_health().get("counters", {}).get(
            "messages_rejected", 0)
        _, ordinary = reading(stack.device_id, stack.device_key, 107)
        peer.sendall(wire(ordinary))
        final_cloud = wait_for(stack.cloud_health,
                               lambda value: value.get("counters", {}).get(
                                   "messages_rejected", 0) > cloud_rejected_before,
                               "ordinary inner sequence blocked after poison")
        if final_cloud["stored_readings"] != 106:
            raise RuntimeError("unexpected cloud count during identity/sequence probe")

    latencies = [item["readback_latency_upper_bound_ms"] for item in samples]
    return {
        "scope": "independently encoded peer for repository simulated protocol",
        "real_legacy_protocol_acceptance": False,
        "nominal_profile": {
            "active_devices": 1, "interval_seconds": 5, "samples": samples,
            "readback_latency_upper_bound_p50_ms": percentile(latencies, 0.5),
            "readback_latency_upper_bound_p95_ms": percentile(latencies, 0.95),
            "wire_sizes": sizes, "hello_wire_bytes": len(wire(greeting)),
            "poll_interval_seconds": 0.02,
        },
        "burst_diagnostic": {
            "active_devices": 1, "messages": 100, "elapsed_seconds": burst_seconds,
            "observed_delivery_rate_messages_per_second": 100 / burst_seconds,
            "last_sequences": [row["sequence"] for row in tail],
        },
        "negative_controls": negatives,
        "pre_attack_cloud_stored_readings": after["stored_readings"],
        "final_cloud_stored_readings": final_cloud["stored_readings"],
        "gateway_health": stack.gateway_health(), "cloud_health": final_cloud,
        "open_security_findings": [{
            "id": "A03-05",
            "outcome": "reproduced with an enrolled device credential",
            "foreign_inner_device_stored": True,
            "outer_sequence_106_inner_sequence_999999_stored": True,
            "following_valid_sequence_107_rejected_by_cloud": True,
            "scope": "device-side identity/sequence binding; cloud authorization inference separate",
        }],
        "limitations": [
            "No real device, standard legacy protocol, WAN or Linux Docker run.",
            "No durable acceptance, cloud ACK or crash recovery is provided.",
            "Readback timings include HTTP observation and polling overhead.",
            "Three nominal samples do not establish a performance guarantee.",
            "Burst diagnostic does not measure a sustainable capacity limit.",
            "Child-only loopback health adaptation excludes unmodified deployment acceptance.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path,
                        help="New external directory for test state, logs and evidence")
    args = parser.parse_args()
    report = {"recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "python": sys.version.split()[0], "outcome": "failed"}
    # Entering isolated_stack enforces external/new runtime before writing.
    with isolated_stack(args.runtime) as stack:
        try:
            report.update(execute(stack))
            report["outcome"] = "completed_with_open_findings"
        except Exception as exc:
            report["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            (args.runtime / "legacy-results.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
