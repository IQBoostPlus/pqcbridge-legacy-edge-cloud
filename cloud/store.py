"""In-memory storage for received readings (project prompt section 4).

Deliberately no database: a small bounded deque is enough for the
simulation.

TODO: Student review required - persistence and access control are out
of scope for the baseline.
"""
import collections
import threading


class ReadingStore:
    """Thread-safe, bounded in-memory store of received readings."""

    def __init__(self, max_readings: int = 1000):
        self._readings = collections.deque(maxlen=max_readings)
        self._lock = threading.Lock()

    def add(self, reading: dict) -> None:
        with self._lock:
            self._readings.append(reading)

    def recent(self, n: int = 10) -> list:
        with self._lock:
            items = list(self._readings)
        return items[-n:]

    def count(self) -> int:
        with self._lock:
            return len(self._readings)
