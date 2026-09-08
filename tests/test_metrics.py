"""Baseline tests for the metrics counters (project prompt sections 9
and 14), updated for the P03 F-08 decision: observations carry their
unit, snapshot keys no longer force a seconds suffix."""
from common.metrics import Metrics


def test_counter_increments():
    metrics = Metrics()
    metrics.inc("messages_received", 3)
    metrics.inc("messages_received")
    assert metrics.snapshot()["counters"]["messages_received"] == 4


def test_timing_aggregation_records_unit():
    metrics = Metrics()
    metrics.observe("latency", 0.1)
    metrics.observe("latency", 0.3)
    timing = metrics.snapshot()["timings"]["latency"]
    assert timing["count"] == 2
    assert timing["min"] == 0.1
    assert timing["max"] == 0.3
    assert timing["avg"] == 0.2
    assert timing["unit"] == "s"


def test_size_observation_records_bytes_unit():
    metrics = Metrics()
    metrics.observe("payload_bytes", 120, unit="bytes")
    stats = metrics.snapshot()["timings"]["payload_bytes"]
    assert stats["unit"] == "bytes"
    assert stats["min"] == 120
    assert stats["max"] == 120


def test_snapshot_is_a_copy():
    metrics = Metrics()
    metrics.inc("a")
    snapshot = metrics.snapshot()
    metrics.inc("a")
    assert snapshot["counters"]["a"] == 1
