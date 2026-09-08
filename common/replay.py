"""Per-device monotonic sequence tracking (P03 section 9 / F-05).

In-memory only: a gateway/cloud restart loses the state, so replays
of pre-restart messages are accepted until the device sends again.
This limitation was ACCEPTED in P03 and is documented in the README -
do NOT silently solve it by adding a database (P04 section 11).
"""
import threading


class ReplayGuard:
    """Thread-safe per-device 'highest accepted sequence' registry.

    check_and_update(device_id, seq) returns True and records the
    sequence when seq > last seen for that device; returns False for
    duplicates or stale sequences.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._last_sequence = {}

    def check_and_update(self, device_id: str, sequence: int) -> bool:
        with self._lock:
            last = self._last_sequence.get(device_id, 0)
            if sequence <= last:
                return False
            self._last_sequence[device_id] = sequence
            return True
