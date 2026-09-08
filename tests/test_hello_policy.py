"""Fail-first tests for F-02 (P04.6): authenticated hello + fallback
policy.

Baseline behavior: hello capability claims were plaintext and
self-declared - a MITM or malicious device could manipulate them at
will (downgrade attack).

P03 policy (review/P03 section 8): fallback is permitted ONLY for
known devices whose authenticated hello claims legacy-only
capabilities. Everything else is rejected.
"""
import pytest

from common import crypto, protocol
from gateway import processing

KEY_A = bytes.fromhex("ab" * 32)  # dev-01's key
KEY_B = bytes.fromhex("cd" * 32)  # dev-02's key


def test_valid_legacy_hello_allows_fallback():
    hello = crypto.build_hello("dev-01", [protocol.CAP_CHACHA20_POLY1305],
                               KEY_A)
    assert processing.evaluate_hello(hello, KEY_A) == processing.ALLOW_FALLBACK


def test_modern_capable_device_rejected():
    hello = crypto.build_hello("dev-01", [protocol.CAP_MLKEM_768], KEY_A)
    assert processing.evaluate_hello(hello, KEY_A) == processing.REJECT_MODERN


def test_both_capabilities_rejected():
    hello = crypto.build_hello(
        "dev-01", [protocol.CAP_CHACHA20_POLY1305, protocol.CAP_MLKEM_768],
        KEY_A)
    assert processing.evaluate_hello(
        hello, KEY_A) == processing.REJECT_AMBIGUOUS


def test_unknown_device_rejected():
    hello = crypto.build_hello("dev-999", [protocol.CAP_CHACHA20_POLY1305],
                               KEY_A)
    assert processing.evaluate_hello(
        hello, None) == processing.REJECT_UNKNOWN_DEVICE


def test_no_capabilities_rejected():
    hello = crypto.build_hello("dev-01", [], KEY_A)
    assert processing.evaluate_hello(
        hello, KEY_A) == processing.REJECT_NO_CAPABILITIES


def test_malformed_hello_rejected():
    with pytest.raises(protocol.ProtocolError):
        processing.parse_hello({"type": protocol.MSG_HELLO,
                                "device_id": "dev-01",
                                "capabilities": []})


def test_modified_capability_claim_rejected():
    # downgrade attempt: capabilities changed after the tag was made
    hello = crypto.build_hello("dev-01", [protocol.CAP_CHACHA20_POLY1305],
                               KEY_A)
    hello["capabilities"] = [protocol.CAP_MLKEM_768]
    assert processing.evaluate_hello(
        hello, KEY_A) == processing.REJECT_UNAUTHENTICATED


def test_unauthenticated_hello_rejected():
    hello = crypto.build_hello("dev-01", [protocol.CAP_CHACHA20_POLY1305],
                               KEY_A)
    hello["auth_tag"] = protocol.b64e(b"\x00" * 16)  # wrong tag
    assert processing.evaluate_hello(
        hello, KEY_A) == processing.REJECT_UNAUTHENTICATED


def test_impersonation_rejected():
    # hello claims dev-02 but is tagged with dev-01's key
    hello = crypto.build_hello("dev-02", [protocol.CAP_CHACHA20_POLY1305],
                               KEY_A)
    assert processing.evaluate_hello(
        hello, KEY_B) == processing.REJECT_UNAUTHENTICATED
