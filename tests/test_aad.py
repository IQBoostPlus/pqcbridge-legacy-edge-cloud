"""Fail-first tests for P04.3 (F-09 + F-05 preparation): AEAD
authenticated data (AAD) support.

Baseline behavior: the AEAD wrappers took no AAD argument, so
security-relevant context (device id, sequence, session id) was not
bound to the ciphertext.
"""
import pytest

from common import crypto, protocol

KEY = bytes.fromhex("ab" * 32)


def test_correct_aad_decrypts():
    aad = b"dev-01:7"
    envelope = crypto.encrypt_legacy_payload(KEY, b"reading", aad)
    assert crypto.decrypt_legacy_payload(KEY, envelope, aad) == b"reading"


def test_modified_aad_fails():
    envelope = crypto.encrypt_legacy_payload(KEY, b"reading", b"dev-01:7")
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(KEY, envelope, b"dev-01:8")


def test_modified_ciphertext_fails():
    envelope = crypto.encrypt_legacy_payload(KEY, b"reading", b"dev-01:7")
    raw = bytearray(protocol.b64d(envelope["ciphertext"]))
    raw[-1] ^= 0x01
    envelope["ciphertext"] = protocol.b64e(bytes(raw))
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(KEY, envelope, b"dev-01:7")


def test_modified_nonce_fails():
    envelope = crypto.encrypt_legacy_payload(KEY, b"reading", b"dev-01:7")
    raw = bytearray(protocol.b64d(envelope["nonce"]))
    raw[0] ^= 0x01
    envelope["nonce"] = protocol.b64e(bytes(raw))
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(KEY, envelope, b"dev-01:7")


def test_session_payload_binds_session_id():
    session_key = crypto.derive_session_key(bytes.fromhex("ef" * 32))
    envelope = crypto.encrypt_session_payload(
        session_key, b"reading", protocol.session_message_aad("sess-1"))
    # Same key, different session AAD -> must fail
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt_session_payload(
            session_key, envelope, protocol.session_message_aad("sess-2"))
    # Correct AAD -> succeeds
    assert crypto.decrypt_session_payload(
        session_key, envelope,
        protocol.session_message_aad("sess-1")) == b"reading"
