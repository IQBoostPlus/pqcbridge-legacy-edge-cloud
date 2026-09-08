"""Fail-first regression tests for F-03/F-04 (P04.2): malformed
handshake messages must produce controlled ProtocolErrors - never
uncaught KeyErrors or component crashes.

Baseline behavior (P02 evidence, re-confirmed in P04): missing
`public_key` crashed the gateway process; missing `ciphertext` crashed
a cloud handler thread with a raw traceback.
"""
import pytest

from cloud import processing as cloud_processing
from common import crypto, protocol
from gateway import processing as gateway_processing


# --- gateway side: mlkem_pubkey reply validation (F-03) ----------------------

def test_parse_mlkem_pubkey_reply_missing_public_key():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_mlkem_pubkey_reply(
            {"type": protocol.MSG_MLKEM_PUBKEY, "cloud_id": "x"})


def test_parse_mlkem_pubkey_reply_wrong_type():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_mlkem_pubkey_reply(
            {"type": protocol.MSG_MLKEM_ENCAPS, "cloud_id": "x",
             "public_key": "AA=="})


def test_parse_mlkem_pubkey_reply_bad_base64():
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_mlkem_pubkey_reply(
            {"type": protocol.MSG_MLKEM_PUBKEY, "cloud_id": "x",
             "public_key": "!!!not-base64!!!"})


def test_parse_mlkem_pubkey_reply_wrong_length():
    raw = b"\x00" * 100  # ML-KEM-768 public keys are 1184 bytes
    with pytest.raises(protocol.ProtocolError):
        gateway_processing.parse_mlkem_pubkey_reply(
            {"type": protocol.MSG_MLKEM_PUBKEY, "cloud_id": "x",
             "public_key": protocol.b64e(raw)})


def test_parse_mlkem_pubkey_reply_valid():
    key = crypto.generate_mlkem_keypair()
    raw = crypto.public_key_bytes(key.public_key())
    result = gateway_processing.parse_mlkem_pubkey_reply(
        {"type": protocol.MSG_MLKEM_PUBKEY, "cloud_id": "x",
         "public_key": protocol.b64e(raw)})
    assert result == raw


# --- cloud side: mlkem_request / mlkem_encaps validation (F-04) --------------

def test_parse_mlkem_request_missing_gateway_id():
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_request(
            {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY})


def test_parse_mlkem_request_valid():
    gateway_id = cloud_processing.parse_mlkem_request(
        {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY, "gateway_id": "gw-01",
         "auth_nonce": "AA==", "auth_tag": "AA=="})
    assert gateway_id == "gw-01"


def test_parse_mlkem_request_missing_auth_fields():
    # P08 BF-01: a handshake request without gateway auth fields is
    # structurally malformed.
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_request(
            {"type": protocol.MSG_MLKEM_REQUEST_PUBKEY, "gateway_id": "gw-01"})


def test_parse_mlkem_encaps_missing_ciphertext():
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_encaps(
            {"type": protocol.MSG_MLKEM_ENCAPS, "gateway_id": "g",
             "session_id": "s"})


def test_parse_mlkem_encaps_bad_base64():
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_encaps(
            {"type": protocol.MSG_MLKEM_ENCAPS, "gateway_id": "g",
             "session_id": "s", "ciphertext": "!!!"})


def test_parse_mlkem_encaps_wrong_length():
    # ML-KEM-768 ciphertexts are 1088 bytes
    with pytest.raises(protocol.ProtocolError):
        cloud_processing.parse_mlkem_encaps(
            {"type": protocol.MSG_MLKEM_ENCAPS, "gateway_id": "g",
             "session_id": "s", "ciphertext": protocol.b64e(b"\x00" * 10)})


def test_parse_mlkem_encaps_valid():
    key = crypto.generate_mlkem_keypair()
    _, ciphertext = crypto.mlkem_encapsulate(key.public_key())
    session_id, raw = cloud_processing.parse_mlkem_encaps(
        {"type": protocol.MSG_MLKEM_ENCAPS, "gateway_id": "g",
         "session_id": "sess", "ciphertext": protocol.b64e(ciphertext)})
    assert raw == ciphertext
    assert session_id == "sess"
