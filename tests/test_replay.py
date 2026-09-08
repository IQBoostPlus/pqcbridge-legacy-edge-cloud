"""Fail-first tests for F-05 (P04.7): replay protection via
monotonic per-device sequence + AAD binding + device-side counter
persistence.

Baseline behavior (P02/P04 evidence): a captured valid encrypted
reading was accepted a second time; sequence numbers existed in the
plaintext but were never checked.
"""
import pytest

from common import crypto, protocol
from common.replay import ReplayGuard
from device import state as device_state
from gateway import processing

KEY = bytes.fromhex("ab" * 32)


def _reading_bytes(sequence=7):
    return (b'{"device_id": "dev-01", '
            b'"timestamp": "2026-01-01T00:00:00+00:00", '
            b'"temperature_c": 21.5, "unit": "celsius", '
            b'"sequence": ' + str(sequence).encode() + b'}')


def _legacy_message(seq=7, device_id="dev-01"):
    aad = protocol.legacy_message_aad(device_id, seq)
    envelope = crypto.encrypt_legacy_payload(KEY, _reading_bytes(seq), aad)
    return {"type": protocol.MSG_LEGACY_READING, "device_id": device_id,
            "seq": seq, **envelope}


# --- ReplayGuard semantics (P03 section 9) -----------------------------------

def test_guard_accepts_increasing_sequence():
    guard = ReplayGuard()
    assert guard.check_and_update("dev-01", 1)
    assert guard.check_and_update("dev-01", 2)


def test_guard_rejects_duplicate_sequence():
    guard = ReplayGuard()
    assert guard.check_and_update("dev-01", 2)
    assert not guard.check_and_update("dev-01", 2)


def test_guard_rejects_older_sequence():
    guard = ReplayGuard()
    assert guard.check_and_update("dev-01", 2)
    assert not guard.check_and_update("dev-01", 1)


def test_guard_accepts_next_sequence_after_rejection():
    guard = ReplayGuard()
    assert guard.check_and_update("dev-01", 1)
    assert guard.check_and_update("dev-01", 2)
    assert not guard.check_and_update("dev-01", 2)  # replay
    assert guard.check_and_update("dev-01", 3)      # valid next


def test_guard_tracks_devices_independently():
    guard = ReplayGuard()
    assert guard.check_and_update("dev-01", 5)
    assert guard.check_and_update("dev-02", 1)


# --- sequence is bound into the AEAD (P03 section 9) -------------------------

def test_sequence_bound_into_aad():
    envelope = crypto.encrypt_legacy_payload(
        KEY, b"reading", protocol.legacy_message_aad("dev-01", 7))
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(
            KEY, envelope, protocol.legacy_message_aad("dev-01", 8))


def test_decrypt_legacy_message_returns_plaintext_and_sequence():
    plaintext, seq = processing.decrypt_legacy_message(
        _legacy_message(seq=7), KEY, "dev-01")
    assert seq == 7
    assert b'"sequence": 7' in plaintext


def test_decrypt_legacy_message_rejects_missing_sequence():
    message = _legacy_message(seq=7)
    del message["seq"]
    with pytest.raises(protocol.ProtocolError):
        processing.decrypt_legacy_message(message, KEY, "dev-01")


def test_decrypt_legacy_message_rejects_tampered_sequence():
    message = _legacy_message(seq=7)
    message["seq"] = 8  # plaintext field changed without re-encrypting
    with pytest.raises(crypto.LegacyDecryptionError):
        processing.decrypt_legacy_message(message, KEY, "dev-01")


# --- device counter persistence (P03 section 9) ------------------------------

def test_counter_round_trip(tmp_path):
    path = tmp_path / "dev-01.seq"
    device_state.save_sequence(path, 5)
    assert device_state.load_sequence(path) == 5


def test_counter_missing_file_starts_at_zero(tmp_path):
    assert device_state.load_sequence(tmp_path / "missing.seq") == 0


def test_counter_corrupt_file_starts_at_zero(tmp_path):
    path = tmp_path / "dev-01.seq"
    path.write_text("not-a-number", encoding="utf-8")
    assert device_state.load_sequence(path) == 0
