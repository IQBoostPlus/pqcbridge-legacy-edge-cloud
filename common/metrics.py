"""Tiny metrics counters for baseline evaluation (project prompt
sections 9 and 14).

P04 (F-08 decision): observations carry an explicit unit (e.g. "s",
"bytes"); snapshot aggregates are avg/min/max with a `unit` field -
no forced seconds suffix. Metric semantics per P03 section F-08:

  messages_received      - messages read from the wire
  messages_processed     - messages accepted after full validation
  messages_forwarded     - gateway: readings sent to the cloud
  messages_rejected      - drops for policy/protocol reasons
                           (replay, bad MAC, unknown device, malformed)
  errors                 - unexpected failures (exceptions, faults)
  fallback_activations   - hellos that authenticated AND activated
                           the legacy fallback path
  legacy_devices_detected- distinct known device ids that activated
                           fallback
  mlkem_sessions_established - successful ML-KEM establishments

Intentionally NOT an observability platform.
"""
import threading


class _Stats:
    __slots__ = ("count", "total", "min", "max", "unit")

    def __init__(self, unit: str):
        self.count = 0
        self.total = 0.0
        self.min = float("inf")
        self.max = 0.0
        self.unit = unit

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)


class Metrics:
    """Thread-safe counters + scalar observations (timings, sizes)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._stats = {}

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def observe(self, name: str, value: float, unit: str = "s") -> None:
        """Record a scalar observation (seconds, bytes, ...)."""
        with self._lock:
            stats = self._stats.get(name)
            if stats is None or stats.unit != unit:
                stats = _Stats(unit)
                self._stats[name] = stats
            stats.add(value)

    def snapshot(self) -> dict:
        """Return a plain dict of counters and stat aggregates."""
        with self._lock:
            timings = {}
            for name, stats in self._stats.items():
                timings[name] = {
                    "count": stats.count,
                    "avg": round(stats.total / stats.count, 6)
                    if stats.count else None,
                    "min": round(stats.min, 6) if stats.count else None,
                    "max": round(stats.max, 6) if stats.count else None,
                    "unit": stats.unit,
                }
            return {"counters": dict(self._counters), "timings": timings}
