"""Fake sensor reading generation for the simulated legacy device.

The device is intentionally simple (project prompt section 2): it only
knows symmetric crypto (ChaCha20-Poly1305 with a pre-shared key) and
MUST NOT implement or execute ML-KEM.
"""
import datetime
import json
import random
from typing import Optional

READING_UNIT = "celsius"
TEMPERATURE_MIN_C = 15.0
TEMPERATURE_MAX_C = 35.0


def generate_reading(device_id: str, sequence: int,
                     timestamp: Optional[datetime.datetime] = None) -> dict:
    """Create one fake sensor reading.

    `timestamp` is injectable so tests can be deterministic.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc)
    return {
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "temperature_c": round(random.uniform(TEMPERATURE_MIN_C,
                                              TEMPERATURE_MAX_C), 2),
        "unit": READING_UNIT,
        "sequence": sequence,
    }


def reading_to_bytes(reading: dict) -> bytes:
    """Serialize a reading to JSON bytes for encryption."""
    return json.dumps(reading, separators=(",", ":")).encode("utf-8")
