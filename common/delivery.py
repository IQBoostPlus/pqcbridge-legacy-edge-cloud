"""Bounded lab-v1 events and durable delivery state (synthetic data only).

SQLite FULL/WAL protects committed transactions subject to the host filesystem's
fsync guarantees. State ownership permissions are best effort on Windows; this
module does not provide encryption or protection from a compromised host.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid


class DeliveryError(ValueError):
    """A reading/event/state transition was refused; no acceptance is implied."""


_EVENT_FIELDS = {"schema_version", "gateway_id", "event_id", "device_id",
                 "source_incarnation", "accepted_at", "source_timestamp",
                 "source_sequence", "payload"}
_ACK_FIELDS = {"type", "schema_version", "gateway_id", "event_id", "digest", "status"}
_STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise DeliveryError("invalid_json") from exc


def _timestamp(value, *, normalized=False):
    if not isinstance(value, str) or len(value) > 64:
        raise DeliveryError("invalid_timestamp")
    if normalized and not _STAMP.fullmatch(value):
        raise DeliveryError("noncanonical_timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, OverflowError) as exc:
        raise DeliveryError("invalid_timestamp") from exc


def _uuid(value, *, version=None):
    try:
        parsed = uuid.UUID(value) if isinstance(value, str) else None
        if parsed is None or str(parsed) != value or (version and parsed.version != version):
            raise ValueError("noncanonical UUID")
    except (ValueError, AttributeError) as exc:
        raise DeliveryError("invalid_uuid") from exc


def _identity(value):
    try:
        encoded_length = len(value.encode("utf-8")) if isinstance(value, str) else 0
    except UnicodeError as exc:
        raise DeliveryError("invalid_identity") from exc
    if (not isinstance(value, str) or not value or encoded_length > 128
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise DeliveryError("invalid_identity")


def _validate_event(event):
    if type(event) is not dict or set(event) != _EVENT_FIELDS:
        raise DeliveryError("invalid_event_fields")
    if type(event["schema_version"]) is not int or event["schema_version"] != 1:
        raise DeliveryError("unsupported_schema")
    for field in ("gateway_id", "device_id"):
        _identity(event[field])
    _uuid(event["event_id"], version=4)
    _uuid(event["source_incarnation"])
    _timestamp(event["accepted_at"], normalized=True)
    if event["source_timestamp"] is not None:
        _timestamp(event["source_timestamp"], normalized=True)
    sequence = event["source_sequence"]
    if sequence is not None and (type(sequence) is not int or not 1 <= sequence <= 2**63 - 1):
        raise DeliveryError("invalid_sequence")
    payload = event["payload"]
    if type(payload) is not dict or set(payload) != {"temperature_c", "unit"}:
        raise DeliveryError("invalid_payload")
    temperature = payload["temperature_c"]
    if (type(temperature) not in (float, int) or
            (type(temperature) is float and not math.isfinite(temperature)) or
            payload["unit"] != "celsius" or len(_json(payload)) > 4096):
        raise DeliveryError("invalid_payload")


def canonical_event(gateway_id, device_id, source_incarnation, reading,
                    accepted_at=None, event_id=None):
    if type(reading) is not dict or set(reading) != {"device_id", "timestamp", "temperature_c", "unit", "sequence"}:
        raise DeliveryError("invalid_reading_fields")
    if reading["device_id"] != device_id:
        raise DeliveryError("source_metadata_mismatch")
    event = {"schema_version": 1, "gateway_id": gateway_id,
             "event_id": event_id if event_id is not None else str(uuid.uuid4()),
             "device_id": device_id, "source_incarnation": source_incarnation,
             "accepted_at": _timestamp(accepted_at if accepted_at is not None else
                                        datetime.now(timezone.utc).isoformat()),
             "source_timestamp": None if reading["timestamp"] is None else _timestamp(reading["timestamp"]),
             "source_sequence": reading["sequence"],
             "payload": {"temperature_c": reading["temperature_c"], "unit": reading["unit"]}}
    _validate_event(event)
    raw = _json(event)
    if len(raw) > 8192:
        raise DeliveryError("event_too_large")
    return raw


def decode_event(raw):
    if type(raw) is not bytes or not raw or len(raw) > 8192:
        raise DeliveryError("event_size_or_type")
    try:
        event = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise DeliveryError("invalid_event_json") from exc
    _validate_event(event)
    if _json(event) != raw:
        raise DeliveryError("noncanonical_event")
    return event


def event_upload(raw):
    decode_event(raw)
    upload = {"type": "event", "event": base64.b64encode(raw).decode("ascii"),
              "digest": hashlib.sha256(raw).hexdigest()}
    if len(_json(upload)) + 1 > 16384:
        raise DeliveryError("upload_too_large")
    return upload


def parse_upload(upload):
    if type(upload) is not dict or set(upload) != {"type", "event", "digest"} or upload["type"] != "event":
        raise DeliveryError("invalid_upload")
    if not isinstance(upload["event"], str) or not isinstance(upload["digest"], str):
        raise DeliveryError("invalid_upload")
    if len(_json(upload)) + 1 > 16384:
        raise DeliveryError("upload_too_large")
    try:
        raw = base64.b64decode(upload["event"], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise DeliveryError("invalid_base64") from exc
    if base64.b64encode(raw).decode("ascii") != upload["event"]:
        raise DeliveryError("noncanonical_base64")
    if not isinstance(upload["digest"], str) or not _DIGEST.fullmatch(upload["digest"]) or hashlib.sha256(raw).hexdigest() != upload["digest"]:
        raise DeliveryError("digest_mismatch")
    return raw, decode_event(raw)


def ack_for(raw):
    event = decode_event(raw)
    return {"type": "ack", "schema_version": 1, "gateway_id": event["gateway_id"],
            "event_id": event["event_id"], "digest": hashlib.sha256(raw).hexdigest(),
            "status": "committed"}


def matching_ack(raw, ack):
    return (type(ack) is dict and set(ack) == _ACK_FIELDS and
            type(ack.get("schema_version")) is int and ack == ack_for(raw))


class _Store:
    """One process may share this object across threads; SQLite owns transactions."""

    def __init__(self, state_dir, *, kind, max_rows, max_bytes, reserve_bytes):
        if any(type(v) is not int or v < 0 for v in (max_rows, max_bytes, reserve_bytes)) or reserve_bytes >= max_bytes:
            raise DeliveryError("invalid_storage_budget")
        self.directory = Path(state_dir)
        self.max_rows, self.max_bytes, self.reserve_bytes = max_rows, max_bytes, reserve_bytes
        self._lock = threading.RLock()
        self._volatile_refused = 0
        self._db = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            if self.directory.is_symlink():
                raise DeliveryError("symlink_state_directory")
            os.chmod(self.directory, 0o700)
            path = self.directory / (kind + ".sqlite")
            if path.is_symlink():
                raise DeliveryError("symlink_database")
            self._db = sqlite3.connect(path, isolation_level=None, timeout=5, check_same_thread=False)
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            tables = self._db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version not in (0, 1) or (version == 0 and tables):
                raise DeliveryError("unsupported_storage_schema")
            mode = self._db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if mode.lower() != "wal":
                raise DeliveryError("wal_unavailable")
            self._db.execute("PRAGMA synchronous=FULL")
            if self._db.execute("PRAGMA synchronous").fetchone()[0] != 2:
                raise DeliveryError("full_sync_unavailable")
            self._db.execute("PRAGMA busy_timeout=5000")
            if version == 0:
                self._db.executescript("""BEGIN IMMEDIATE;
                    CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE events (gateway TEXT NOT NULL, event_id TEXT NOT NULL,
                        raw BLOB NOT NULL, status TEXT NOT NULL, deadline REAL,
                        reason TEXT, PRIMARY KEY(gateway,event_id));
                    CREATE TABLE sources (gateway TEXT NOT NULL, device TEXT NOT NULL,
                        incarnation TEXT NOT NULL, sequence INTEGER NOT NULL,
                        PRIMARY KEY(gateway,device,incarnation));
                    PRAGMA user_version=1;
                    COMMIT;""")
                self._db.execute("INSERT INTO metadata VALUES ('kind',?)", (kind,))
            if self._db.execute("SELECT value FROM metadata WHERE key='kind'").fetchone() != (kind,):
                raise DeliveryError("storage_kind_mismatch")
            expected = {"metadata", "events", "sources"}
            if {r[0] for r in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")} != expected:
                raise DeliveryError("unsupported_storage_schema")
            self._permissions()
        except (sqlite3.Error, OSError) as exc:
            if self._db:
                self._db.close()
            raise DeliveryError("storage_unavailable") from exc
        except DeliveryError:
            if self._db:
                self._db.close()
            raise

    def _permissions(self):
        for path in self.directory.iterdir():
            if path.is_file() and not path.is_symlink():
                os.chmod(path, 0o600)

    def _size(self):
        total = 0
        for path in self.directory.rglob("*"):
            if path.is_symlink():
                raise DeliveryError("symlink_state_entry")
            if path.is_file():
                total += path.stat().st_size
        return total

    def _capacity(self, extra=0, *, use_reserve=False):
        # Conservative headroom for SQLite pages, indices and transaction frames.
        ceiling = self.max_bytes if use_reserve else self.max_bytes - self.reserve_bytes
        if self._size() + extra > ceiling:
            raise DeliveryError("state_byte_quota")

    def _metric(self, key, delta=0):
        row = self._db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        value = int(row[0]) if row else 0
        if delta:
            value += delta
            self._set(key, value)
        return value

    def _set(self, key, value):
        self._db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    def _transaction(self, action, *, admission=False):
        with self._lock:
            try:
                self._db.execute("BEGIN IMMEDIATE")
                result = action()
                self._capacity(use_reserve=not admission)
                self._db.execute("COMMIT")
                # Checkpoint keeps WAL growth bounded; a busy checkpoint never
                # invalidates an already committed transaction or its ACK.
                try:
                    self._db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    self._permissions()
                except (sqlite3.Error, OSError):
                    pass
                return result
            except (DeliveryError, sqlite3.Error, OSError) as exc:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                if admission:
                    self._volatile_refused += 1
                if isinstance(exc, DeliveryError):
                    raise
                raise DeliveryError("storage_transaction_failed") from exc

    def close(self):
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None


class GatewayQueue(_Store):
    def __init__(self, state_dir, max_rows=10000, max_bytes=256 * 1024 * 1024,
                 reserve_bytes=16 * 1024 * 1024):
        super().__init__(state_dir, kind="gateway", max_rows=max_rows,
                         max_bytes=max_bytes, reserve_bytes=reserve_bytes)
        self._wall_anchor = time.time()
        self._mono_anchor = time.monotonic()

    def accept(self, raw):
        event = decode_event(raw)
        def action():
            if self._metric("clock_uncertain"):
                raise DeliveryError("clock_uncertain")
            self._capacity(65536 + len(raw) * 4)
            if self._db.execute("SELECT count(*) FROM events").fetchone()[0] >= self.max_rows:
                raise DeliveryError("queue_row_quota")
            key = (event["gateway_id"], event["device_id"], event["source_incarnation"])
            sequence = event["source_sequence"]
            if sequence is not None:
                previous = self._db.execute("SELECT sequence FROM sources WHERE gateway=? AND device=? AND incarnation=?", key).fetchone()
                previous = previous[0] if previous else 0
                increment = sequence - previous
                if increment <= 0 or increment > 1024:
                    raise DeliveryError("source_sequence_refused")
                self._db.execute("INSERT INTO sources VALUES (?,?,?,?) ON CONFLICT(gateway,device,incarnation) DO UPDATE SET sequence=excluded.sequence", (*key, sequence))
                if increment > 1:
                    self._metric("source_gap", increment - 1)
            accepted_seconds = datetime.fromisoformat(event["accepted_at"].replace("Z", "+00:00")).timestamp()
            deadline = accepted_seconds + 86400
            self._db.execute("INSERT INTO events VALUES (?,?,?,'pending',?,NULL)",
                             (event["gateway_id"], event["event_id"], raw, deadline))
            self._metric("accepted_total", 1)
            observed = self._db.execute("SELECT value FROM metadata WHERE key='last_utc'").fetchone()
            self._set("last_utc", max(float(observed[0]) if observed else accepted_seconds, accepted_seconds))
        self._transaction(action, admission=True)

    def pending(self, limit=1):
        if type(limit) is not int or not 0 <= limit <= self.max_rows:
            raise DeliveryError("invalid_limit")
        with self._lock:
            if self._metric("clock_uncertain"):
                raise DeliveryError("clock_uncertain")
            return [bytes(row[0]) for row in self._db.execute("SELECT raw FROM events WHERE status='pending' ORDER BY rowid LIMIT ?", (limit,))]

    def acknowledge(self, raw, ack):
        if not matching_ack(raw, ack):
            raise DeliveryError("ack_mismatch")
        event = decode_event(raw)
        def action():
            row = self._db.execute("SELECT raw,status FROM events WHERE gateway=? AND event_id=?", (event["gateway_id"], event["event_id"])).fetchone()
            if row is None or bytes(row[0]) != raw or row[1] != "pending":
                raise DeliveryError("event_not_pending")
            self._db.execute("DELETE FROM events WHERE gateway=? AND event_id=?", (event["gateway_id"], event["event_id"]))
            self._metric("acknowledged_total", 1)
        self._transaction(action)

    def quarantine(self, raw, reason):
        event = decode_event(raw)
        if not isinstance(reason, str) or not reason or len(reason) > 128:
            raise DeliveryError("invalid_quarantine_reason")
        def action():
            cursor = self._db.execute("UPDATE events SET status='quarantined',reason=? WHERE gateway=? AND event_id=? AND raw=? AND status='pending'", (reason, event["gateway_id"], event["event_id"], raw))
            if cursor.rowcount != 1:
                raise DeliveryError("event_not_pending")
        self._transaction(action)

    def expire(self, now=None):
        if now is None:
            wall = time.time()
        elif isinstance(now, str):
            wall = datetime.fromisoformat(_timestamp(now).replace("Z", "+00:00")).timestamp()
        elif isinstance(now, datetime):
            if now.tzinfo is None:
                raise DeliveryError("timezone_required")
            wall = now.timestamp()
        elif type(now) in (int, float) and math.isfinite(now):
            wall = float(now)
        else:
            raise DeliveryError("invalid_clock")
        mono_now = time.monotonic()
        def action():
            row = self._db.execute("SELECT value FROM metadata WHERE key='last_utc'").fetchone()
            last = float(row[0]) if row else wall
            expected = self._wall_anchor + mono_now - self._mono_anchor
            # The explicit now seam models a wall clock, including tests. A
            # detected backward step never extends an event's original deadline.
            uncertain = wall < last or (now is None and wall + 1 < expected)
            self._set("clock_uncertain", int(uncertain))
            self._set("last_utc", max(last, wall))
            effective = max(wall, expected) if now is None else max(wall, last)
            count = self._db.execute("UPDATE events SET status='quarantined',reason='retry_expired' WHERE status='pending' AND deadline<=?", (effective,)).rowcount
            return count
        result = self._transaction(action)
        if not self._metric("clock_uncertain"):
            self._wall_anchor, self._mono_anchor = wall, mono_now
        return result

    def snapshot(self):
        with self._lock:
            counts = dict(self._db.execute("SELECT status,count(*) FROM events GROUP BY status"))
            return {"accepted_total": self._metric("accepted_total"),
                    "acknowledged_total": self._metric("acknowledged_total"),
                    "pending": counts.get("pending", 0), "quarantined": counts.get("quarantined", 0),
                    "refused": self._volatile_refused, "source_gap": self._metric("source_gap"),
                    "clock_uncertain": bool(self._metric("clock_uncertain"))}


class CloudStore(_Store):
    def __init__(self, state_dir, max_rows=100000, max_bytes=256 * 1024 * 1024,
                 reserve_bytes=16 * 1024 * 1024):
        super().__init__(state_dir, kind="cloud", max_rows=max_rows,
                         max_bytes=max_bytes, reserve_bytes=reserve_bytes)

    def commit(self, raw):
        event = decode_event(raw)
        key = event["gateway_id"], event["event_id"]
        # Read-only exact duplicate ACK works even when the admission quota is
        # full; the existing business row is also the unique deduplication row.
        with self._lock:
            existing = self._db.execute("SELECT raw FROM events WHERE gateway=? AND event_id=?", key).fetchone()
            if existing:
                if bytes(existing[0]) != raw:
                    self._volatile_refused += 1
                    raise DeliveryError("event_id_conflict")
                return ack_for(raw)
            def action():
                self._capacity(65536 + len(raw) * 4)
                if self._db.execute("SELECT count(*) FROM events").fetchone()[0] >= self.max_rows:
                    raise DeliveryError("cloud_row_quota")
                self._db.execute("INSERT INTO events VALUES (?,?,?,'committed',NULL,NULL)", (*key, raw))
                self._metric("committed_total", 1)
                return ack_for(raw)
            return self._transaction(action, admission=True)

    def readings(self, limit=100):
        if type(limit) is not int or not 0 <= limit <= self.max_rows:
            raise DeliveryError("invalid_limit")
        with self._lock:
            return [decode_event(bytes(row[0])) for row in self._db.execute("SELECT raw FROM events ORDER BY rowid DESC LIMIT ?", (limit,))]

    def snapshot(self):
        with self._lock:
            return {"committed_total": self._metric("committed_total"), "refused": self._volatile_refused}
