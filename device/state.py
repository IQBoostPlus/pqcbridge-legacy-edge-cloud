"""Persistent per-device sequence counter (P03 section 9 / F-05).

The counter survives device restarts so replay protection does not
wedge the device after a restart. If the file is lost (e.g. the
Docker volume is deleted) the counter resets - a documented
operational limitation accepted in P03.
"""
from pathlib import Path


def load_sequence(path: Path) -> int:
    """Last persisted sequence, or 0 if the file is missing/corrupt."""
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def save_sequence(path: Path, sequence: int) -> None:
    """Persist the current sequence.

    TODO: Student review required - not atomic; a crash mid-write
    could corrupt the counter (accepted for the prototype).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(sequence), encoding="utf-8")
