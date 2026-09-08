"""Fail-first tests for F-01 (P04.8): cloud ML-KEM public-key
fingerprint pinning.

Baseline behavior: any received ML-KEM public key was accepted - a
MITM could substitute its own key and impersonate the cloud.

NOTE (P03/P04): pinning protects against substitution only when the
initial pinned fingerprint is provisioned through a trusted
mechanism. This remains an educational simulation, not a PKI.
"""
import pytest

from common import crypto
from gateway import processing


def _raw_public_key():
    key = crypto.generate_mlkem_keypair()
    return crypto.public_key_bytes(key.public_key())


def test_expected_key_accepted():
    raw = _raw_public_key()
    fingerprint = crypto.public_key_fingerprint(raw)
    processing.verify_cloud_public_key(raw, fingerprint)  # must not raise


def test_different_key_rejected():
    raw = _raw_public_key()
    other = _raw_public_key()
    fingerprint_of_other = crypto.public_key_fingerprint(other)
    with pytest.raises(crypto.CryptoError):
        processing.verify_cloud_public_key(raw, fingerprint_of_other)


def test_missing_pin_fails_closed():
    with pytest.raises(crypto.CryptoError):
        processing.verify_cloud_public_key(_raw_public_key(), "")


def test_changed_fingerprint_rejected():
    raw = _raw_public_key()
    fingerprint = crypto.public_key_fingerprint(raw)
    # flip the FIRST hex character (guaranteed different)
    tampered = ("1" if fingerprint[0] != "1" else "0") + fingerprint[1:]
    with pytest.raises(crypto.CryptoError):
        processing.verify_cloud_public_key(raw, tampered)


def test_fingerprint_is_64_hex_characters():
    fingerprint = crypto.public_key_fingerprint(_raw_public_key())
    assert len(fingerprint) == 64
    assert all(char in "0123456789abcdef" for char in fingerprint)
