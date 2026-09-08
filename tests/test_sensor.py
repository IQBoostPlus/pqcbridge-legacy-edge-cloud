"""Baseline tests for fake sensor reading generation.

TODO: Student review required - negative tests (invalid inputs,
unexpected device IDs, boundary values) should be added here.
"""
import datetime

from device import sensor


def test_reading_has_required_fields():
    reading = sensor.generate_reading("dev-01", 1)
    assert set(reading) >= {"device_id", "timestamp", "temperature_c",
                            "unit", "sequence"}
    assert reading["device_id"] == "dev-01"
    assert reading["sequence"] == 1
    assert reading["unit"] == "celsius"


def test_temperature_within_expected_range():
    for sequence in range(50):
        reading = sensor.generate_reading("dev-01", sequence)
        assert sensor.TEMPERATURE_MIN_C <= reading["temperature_c"] \
            <= sensor.TEMPERATURE_MAX_C


def test_timestamp_is_parseable_utc_iso():
    reading = sensor.generate_reading("dev-01", 1)
    timestamp = datetime.datetime.fromisoformat(reading["timestamp"])
    assert timestamp.tzinfo is not None


def test_timestamp_is_injectable_for_deterministic_tests():
    fixed = datetime.datetime(2026, 1, 1, 12, 0,
                              tzinfo=datetime.timezone.utc)
    reading = sensor.generate_reading("dev-01", 7, timestamp=fixed)
    assert reading["timestamp"] == "2026-01-01T12:00:00+00:00"
