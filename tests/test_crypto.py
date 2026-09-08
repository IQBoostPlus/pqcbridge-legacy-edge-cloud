"""Baseline tests for the cryptography wrappers (project prompt
section 10): ChaCha20-Poly1305 round trip, ML-KEM-768 round trip,
session key derivation.

All primitives come from the `cryptography` library - no algorithm is
implemented from scratch in this project.

TODO: Student review required - add negative tests: malformed
envelopes, empty ciphertexts, nonce-reuse behavior, and property tests
for the ML-KEM shared-secret length across many keypairs.
"""
import pytest

from common import crypto, protocol


def test_legacy_payload_round_trip():
    key = bytes.fromhex("00" * 32)
    plaintext = b'{"device_id": "dev-01", "temperature_c": 21.5}'
    envelope = crypto.encrypt_legacy_payload(key, plaintext)
    assert crypto.decrypt_legacy_payload(key, envelope) == plaintext


def test_legacy_payload_rejects_wrong_key():
    key1 = bytes.fromhex("00" * 32)
    key2 = bytes.fromhex("11" * 32)
    envelope = crypto.encrypt_legacy_payload(key1, b"secret")
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(key2, envelope)


def test_legacy_payload_rejects_tampered_ciphertext():
    key = bytes.fromhex("00" * 32)
    envelope = crypto.encrypt_legacy_payload(key, b"secret")
    raw = bytearray(protocol.b64d(envelope["ciphertext"]))
    raw[-1] ^= 0x01
    envelope["ciphertext"] = protocol.b64e(bytes(raw))
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(key, envelope)


def test_legacy_payload_rejects_malformed_envelope():
    with pytest.raises(crypto.LegacyDecryptionError):
        crypto.decrypt_legacy_payload(bytes.fromhex("00" * 32), {})


def test_mlkem_round_trip():
    private_key = crypto.generate_mlkem_keypair()
    shared_secret, ciphertext = crypto.mlkem_encapsulate(
        private_key.public_key())
    assert crypto.mlkem_decapsulate(private_key, ciphertext) == shared_secret


def test_mlkem_shared_secret_is_32_bytes():
    private_key = crypto.generate_mlkem_keypair()
    shared_secret, _ = crypto.mlkem_encapsulate(private_key.public_key())
    assert len(shared_secret) == crypto.MLKEM_SHARED_SECRET_LENGTH


def test_mlkem_public_key_serialization_round_trip():
    private_key = crypto.generate_mlkem_keypair()
    raw = crypto.public_key_bytes(private_key.public_key())
    restored = crypto.load_public_key(raw)
    shared_secret, ciphertext = crypto.mlkem_encapsulate(restored)
    assert crypto.mlkem_decapsulate(private_key, ciphertext) == shared_secret


def test_mlkem_public_key_rejects_garbage():
    with pytest.raises(protocol.ProtocolError):
        crypto.load_public_key(b"not a public key")


def test_session_key_derivation_is_deterministic():
    shared = bytes.fromhex("ab" * 32)
    assert crypto.derive_session_key(shared) == crypto.derive_session_key(shared)


def test_session_key_derivation_varies_with_secret():
    key_a = crypto.derive_session_key(bytes.fromhex("ab" * 32))
    key_b = crypto.derive_session_key(bytes.fromhex("cd" * 32))
    assert key_a != key_b
    assert len(key_a) == 32
