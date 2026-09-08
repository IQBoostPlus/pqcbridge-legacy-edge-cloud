"""Baseline tests for gateway and cloud message processing logic,
updated for the P03-approved protocol design implemented in P04:

  - hello messages carry an AEAD auth tag (F-02)
  - legacy readings carry a sequence bound into the AAD (F-05)
  - protected readings bind the session_id as AAD (F-01/F-05)
  - fallback policy per P03 section 8 (F-02)

Design changes from P01 are documented in review/P03; old tests that
encoded the changed behavior were updated accordingly (P04 section
16).
"""
import json

import pytest

from cloud import processing as cloud_processing
from common import crypto, protocol
from gateway import processing as gateway_processing

KEY = bytes.fromhex("ab" * 32)


def _reading_bytes(device_id="dev-01", sequence=1):
    return json.dumps({
        "device_id": device_id,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "temperature_c": 21.5,
        "unit": "celsius",
        "sequence": sequence,
    }).encode("utf-8")


def _legacy_message(key, device_id="dev-01", seq=1):
    aad = protocol.legacy_message_aad(device_id, seq)
    envelope = crypto.encrypt_legacy_payload(
        key, _reading_bytes(device_id, seq), aad)
    return {"type": protocol.MSG_LEGACY_READING, "device_id": device_id,
            "seq": seq, **envelope}


def _hello(device_id="dev-01", capabilities=None):
    capabilities = capabilities or [protocol.CAP_CHACHA20_POLY1305]
    return crypto.build_hello(device_id, capabilities, KEY)


# --- hello parsing and path decision ------------------------------------------

def test_parse_hello_accepts_valid_authenticated_hello():
    parsed = gateway_processing.parse_hello(_hello())
    assert parsed["device_id"] == "dev-01"
    assert parsed["capabilities"] == [protocol.CAP_CHACHA20_POLY1305]


def test_parse_hello_rejects_wrong_type():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_hello(
            {"type": protocol.MSG_LEGACY_READING, "device_id": "d"})


def test_parse_hello_rejects_missing_device_id():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_hello(
            {"type": protocol.MSG_HELLO, "capabilities": [],
             "auth_nonce": "AA==", "auth_tag": "AA=="})


def test_parse_hello_rejects_missing_auth_fields():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_hello(
            {"type": protocol.MSG_HELLO, "device_id": "dev-01",
             "capabilities": []})


def test_parse_hello_rejects_non_list_capabilities():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_hello(
            {"type": protocol.MSG_HELLO, "device_id": "d",
             "capabilities": "ml-kem-768", "auth_nonce": "AA==",
             "auth_tag": "AA=="})


def test_path_decision():
    assert gateway_processing.determine_path(
        [protocol.CAP_CHACHA20_POLY1305]) == "legacy"
    assert gateway_processing.determine_path(
        [protocol.CAP_MLKEM_768]) == "modern"
    # P03 policy: both capabilities is an ambiguous claim, never
    # auto-downgraded (documented design change from P01).
    assert gateway_processing.determine_path(
        [protocol.CAP_CHACHA20_POLY1305, protocol.CAP_MLKEM_768]) == "both"
    assert gateway_processing.determine_path([]) == "unknown"


def test_evaluate_hello_allows_authenticated_fallback():
    assert gateway_processing.evaluate_hello(
        _hello(), KEY) == gateway_processing.ALLOW_FALLBACK


def test_parse_then_evaluate_hello_allows_fallback():
    # Regression for the P04 integration finding: the gateway runs
    # parse_hello() then evaluate_hello(); parse must preserve the
    # auth fields so the tag can actually be verified.
    parsed = gateway_processing.parse_hello(_hello())
    assert gateway_processing.evaluate_hello(
        parsed, KEY) == gateway_processing.ALLOW_FALLBACK


def test_evaluate_hello_rejects_bad_tag():
    hello = _hello()
    hello["auth_tag"] = protocol.b64e(b"\x00" * 16)
    assert gateway_processing.evaluate_hello(
        hello, KEY) == gateway_processing.REJECT_UNAUTHENTICATED


# --- legacy path (device -> gateway) ------------------------------------------

def test_decrypt_legacy_message_round_trip():
    message = _legacy_message(KEY)
    plaintext, seq = gateway_processing.decrypt_legacy_message(
        message, KEY, "dev-01")
    assert json.loads(plaintext)["device_id"] == "dev-01"
    assert seq == 1


def test_decrypt_legacy_message_rejects_wrong_key():
    message = _legacy_message(KEY)
    with pytest.raises(crypto.LegacyDecryptionError):
        gateway_processing.decrypt_legacy_message(
            message, bytes.fromhex("cd" * 32), "dev-01")


def test_decrypt_legacy_message_rejects_device_id_mismatch():
    message = _legacy_message(KEY, device_id="dev-01")
    with pytest.raises(gateway_processing.ProcessingError):
        gateway_processing.decrypt_legacy_message(message, KEY, "dev-02")


def test_decrypt_legacy_message_rejects_malformed_plaintext():
    aad = protocol.legacy_message_aad("dev-01", 1)
    envelope = crypto.encrypt_legacy_payload(KEY, b"not json at all", aad)
    message = {"type": protocol.MSG_LEGACY_READING, "device_id": "dev-01",
               "seq": 1, **envelope}
    with pytest.raises(gateway_processing.ProcessingError):
        gateway_processing.decrypt_legacy_message(message, KEY, "dev-01")


def test_decrypt_legacy_message_rejects_missing_seq():
    message = _legacy_message(KEY)
    del message["seq"]
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.decrypt_legacy_message(message, KEY, "dev-01")


# --- protected path (gateway -> cloud) ----------------------------------------

def test_protected_reading_round_trip():
    session_key = crypto.derive_session_key(bytes.fromhex("ef" * 32))
    protected = gateway_processing.build_protected_reading(
        _reading_bytes(), session_key, "sess-1")
    reading = cloud_processing.decrypt_protected_reading(
        protected, session_key, "sess-1")
    assert reading["device_id"] == "dev-01"
    assert reading["temperature_c"] == 21.5


def test_protected_reading_rejects_wrong_session_key():
    session_key = crypto.derive_session_key(bytes.fromhex("ef" * 32))
    other_key = crypto.derive_session_key(bytes.fromhex("fe" * 32))
    protected = gateway_processing.build_protected_reading(
        _reading_bytes(), session_key, "sess-1")
    with pytest.raises(crypto.CryptoError):
        cloud_processing.decrypt_protected_reading(
            protected, other_key, "sess-1")


def test_protected_reading_rejects_wrong_session_id():
    session_key = crypto.derive_session_key(bytes.fromhex("ef" * 32))
    protected = gateway_processing.build_protected_reading(
        _reading_bytes(), session_key, "sess-1")
    with pytest.raises(cloud_processing.ProcessingError):
        cloud_processing.decrypt_protected_reading(
            protected, session_key, "sess-2")


def test_protected_reading_rejects_wrong_type():
    session_key = crypto.derive_session_key(bytes.fromhex("ef" * 32))
    with pytest.raises(cloud_processing.ProcessingError):
        cloud_processing.decrypt_protected_reading(
            {"type": protocol.MSG_LEGACY_READING}, session_key, "sess-1")
