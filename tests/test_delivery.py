"""Public durable-delivery contract checks using synthetic readings only."""
import json
import pytest

from common.delivery import canonical_event, decode_event, event_upload, parse_upload, ack_for, matching_ack, DeliveryError

INCARNATION = "19b17572-1729-46df-b2d0-539ef373042a"
EVENT_ID = "20748a21-0235-4bd5-b92d-5b15f1d553b2"

def event(sequence=1, **overrides):
    return canonical_event("gw-lab", "sensor-lab", INCARNATION,
        {"device_id": "sensor-lab", "timestamp": "2026-10-16T08:00:00Z",
         "temperature_c": 21.5, "unit": "celsius", "sequence": sequence},
        accepted_at="2026-10-16T08:00:01Z", event_id=overrides.pop("event_id", EVENT_ID), **overrides)

def test_event_upload_and_matching_ack_preserve_exact_persisted_bytes():
    raw = event()
    decoded = decode_event(raw)
    assert decoded["accepted_at"] == "2026-10-16T08:00:01.000000Z"
    assert decoded["source_timestamp"] == "2026-10-16T08:00:00.000000Z"
    assert parse_upload(event_upload(raw)) == (raw, decoded)
    assert matching_ack(raw, ack_for(raw))
    invalid = ack_for(raw) | {"event_id": "047241ed-001c-4874-9b51-7a607d8a3676"}
    assert not matching_ack(raw, invalid)
    with pytest.raises(DeliveryError):
        decode_event(json.dumps(decoded).encode())

def test_pending_commit_survives_restart_and_only_matching_ack_removes_it(tmp_path):
    from common.delivery import GatewayQueue, CloudStore
    raw = event()
    queue = GatewayQueue(tmp_path / "gateway")
    queue.accept(raw)
    queue.close()
    queue = GatewayQueue(tmp_path / "gateway")
    assert queue.pending() == [raw]
    cloud = CloudStore(tmp_path / "cloud")
    ack = cloud.commit(raw)
    assert cloud.commit(raw) == ack
    cloud.close()
    cloud = CloudStore(tmp_path / "cloud")
    assert cloud.readings() == [decode_event(raw)]
    assert cloud.snapshot()["committed_total"] == 1
    with pytest.raises(DeliveryError):
        queue.acknowledge(raw, ack | {"digest": "0" * 64})
    assert queue.pending() == [raw]
    queue.acknowledge(raw, ack)
    assert queue.snapshot()["acknowledged_total"] == 1
    assert queue.pending() == []
    queue.close()
    cloud.close()

def test_sequence_quota_and_quarantine_survive_restart_without_advancing_on_refusal(tmp_path):
    from common.delivery import GatewayQueue
    queue = GatewayQueue(tmp_path, max_rows=1)
    first = event()
    queue.accept(first)
    with pytest.raises(DeliveryError):
        queue.accept(event(2, event_id="047241ed-001c-4874-9b51-7a607d8a3676"))
    queue.quarantine(first, "test_conflict")
    assert queue.snapshot()["pending"] == 0
    assert queue.snapshot()["quarantined"] == 1
    queue.close()
    queue = GatewayQueue(tmp_path, max_rows=2)
    with pytest.raises(DeliveryError):
        queue.accept(event(1, event_id="047241ed-001c-4874-9b51-7a607d8a3676"))
    with pytest.raises(DeliveryError):
        queue.accept(event(1026, event_id="047241ed-001c-4874-9b51-7a607d8a3676"))
    second = event(3, event_id="047241ed-001c-4874-9b51-7a607d8a3676")
    queue.accept(second)
    assert queue.pending() == [second]
    assert queue.snapshot()["source_gap"] == 1
    assert queue.snapshot()["accepted_total"] == 2
    queue.close()

def test_cloud_full_quota_still_acks_exact_duplicate_and_refuses_conflict(tmp_path):
    from common.delivery import CloudStore
    cloud = CloudStore(tmp_path, max_rows=1)
    first = event()
    ack = cloud.commit(first)
    with pytest.raises(DeliveryError):
        cloud.commit(event(2))
    with pytest.raises(DeliveryError):
        cloud.commit(event(2, event_id="047241ed-001c-4874-9b51-7a607d8a3676"))
    assert cloud.commit(first) == ack
    assert cloud.snapshot()["committed_total"] == 1
    cloud.close()

def test_disk_admission_refusal_preserves_pending_and_reserve_allows_ack(tmp_path):
    from common.delivery import GatewayQueue
    queue = GatewayQueue(tmp_path, max_bytes=300000, reserve_bytes=100000)
    first = event()
    queue.accept(first)
    used = sum(path.stat().st_size for path in tmp_path.iterdir() if path.is_file())
    (tmp_path / "synthetic-disk-pressure.bin").write_bytes(b"x" * (200001 - used))
    with pytest.raises(DeliveryError, match="quota"):
        queue.accept(event(2, event_id="047241ed-001c-4874-9b51-7a607d8a3676"))
    assert queue.pending() == [first]
    queue.acknowledge(first, ack_for(first))
    assert queue.snapshot()["accepted_total"] == 1
    assert queue.snapshot()["pending"] == 0
    queue.close()

def test_retry_deadline_and_backward_clock_are_persistent(tmp_path):
    from common.delivery import GatewayQueue
    queue = GatewayQueue(tmp_path)
    raw = event()
    queue.accept(raw)
    assert queue.expire("2026-10-16T09:00:00Z") == 0
    assert queue.expire("2026-10-16T08:59:59Z") == 0
    assert queue.snapshot()["clock_uncertain"]
    with pytest.raises(DeliveryError, match="clock_uncertain"):
        queue.pending()
    queue.close()
    queue = GatewayQueue(tmp_path)
    assert queue.snapshot()["clock_uncertain"]
    assert queue.expire("2026-10-16T09:00:00Z") == 0
    assert queue.pending() == [raw]
    assert queue.expire("2026-10-17T08:00:01Z") == 1
    assert queue.pending() == []
    assert queue.snapshot()["quarantined"] == 1
    assert queue.snapshot()["accepted_total"] == 1
    queue.close()

@pytest.mark.parametrize("mutation", [
    {"source_sequence": True}, {"source_sequence": 0},
    {"source_sequence": 2**63}, {"schema_version": True},
    {"source_incarnation": "not-a-uuid"},
    {"payload": {"temperature_c": True, "unit": "celsius"}},
    {"payload": {"temperature_c": float("nan"), "unit": "celsius"}},
    {"accepted_at": "2026-10-16T08:00:01Z"}, {"unknown": 1},
    {"device_id": "\ud800"},
])
def test_malformed_event_is_refused_before_storage(mutation):
    value = decode_event(event()) | mutation
    with pytest.raises(DeliveryError):
        decode_event(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

@pytest.mark.parametrize("crash_boundary", ["accepted", "cloud_committed", "acknowledged"])
def test_abrupt_process_exit_at_delivery_boundaries_reconciles(tmp_path, crash_boundary):
    import subprocess
    import sys
    from pathlib import Path
    from common.delivery import GatewayQueue, CloudStore
    raw = event()
    script = f'''
import os
from common.delivery import GatewayQueue, CloudStore
q = GatewayQueue({str(tmp_path / "gateway")!r})
q.accept({raw!r})
if {crash_boundary!r} == "accepted": os._exit(17)
c = CloudStore({str(tmp_path / "cloud")!r})
ack = c.commit({raw!r})
if {crash_boundary!r} == "cloud_committed": os._exit(17)
q.acknowledge({raw!r}, ack)
os._exit(17)
'''
    completed = subprocess.run([sys.executable, "-B", "-c", script],
                               cwd=Path(__file__).resolve().parents[1], timeout=15,
                               capture_output=True, text=True)
    assert completed.returncode == 17, completed.stderr
    queue = GatewayQueue(tmp_path / "gateway")
    cloud = CloudStore(tmp_path / "cloud")
    if crash_boundary == "acknowledged":
        assert queue.pending() == []
        assert queue.snapshot()["acknowledged_total"] == 1
    else:
        assert queue.pending() == [raw]
        queue.acknowledge(raw, cloud.commit(raw))
    assert cloud.snapshot()["committed_total"] == 1
    assert cloud.commit(raw) == ack_for(raw)
    assert len(cloud.readings()) == 1
    assert queue.snapshot()["accepted_total"] == queue.snapshot()["acknowledged_total"] == 1
    queue.close()
    cloud.close()

def test_unknown_storage_schema_is_refused_without_resetting_data(tmp_path):
    import sqlite3
    from common.delivery import GatewayQueue
    # External incompatible-version fixture, not an inspection of implementation
    # state: a newer release owns this database and the public constructor must
    # refuse to reinterpret or migrate it.
    database = tmp_path / "gateway.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA user_version=987")
        connection.execute("CREATE TABLE future_data(value)")
        connection.execute("INSERT INTO future_data VALUES ('preserve-me')")
    original = database.read_bytes()
    with pytest.raises(DeliveryError, match="schema"):
        GatewayQueue(tmp_path)
    assert database.read_bytes() == original

def test_clock_progress_at_acceptance_survives_crash_before_first_expiry_scan(tmp_path):
    from common.delivery import GatewayQueue
    queue = GatewayQueue(tmp_path)
    queue.accept(event())
    queue.close()
    queue = GatewayQueue(tmp_path)
    queue.expire("2026-10-16T07:59:59Z")
    assert queue.snapshot()["clock_uncertain"]
    with pytest.raises(DeliveryError, match="clock_uncertain"):
        queue.pending()
    queue.close()
