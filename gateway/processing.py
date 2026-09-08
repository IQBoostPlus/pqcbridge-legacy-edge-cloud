"""Pure message-processing logic for the edge gateway.

Kept free of sockets/threads so pytest can exercise it directly
(project prompt section 10).

P04 changes (P03-approved):
  - F-02: hello capability claims are authenticated with an AEAD tag
    under the device's own key; fallback policy per P03 section 8.
  - F-03: handshake replies are validated field-by-field and raise
    ProtocolError instead of crashing on missing keys.
  - F-01: cloud public-key fingerprint pinning helper.
  - F-05: legacy readings carry a sequence bound into the AEAD AAD.

Remaining design questions (deferred, documented):
  - trusted vs untrusted devices beyond the key registry
  - credential expiry/rotation
  - migration from legacy cryptography to PQC
"""
import secrets

from common import crypto, protocol


class ProcessingError(Exception):
    """Raised when a device message cannot be processed."""


# Fallback policy outcomes (P03 section 8)
ALLOW_FALLBACK = "fallback"
REJECT_UNKNOWN_DEVICE = "unknown_device"
REJECT_UNAUTHENTICATED = "unauthenticated"
REJECT_MODERN = "modern_not_implemented"
REJECT_AMBIGUOUS = "ambiguous_capabilities"
REJECT_NO_CAPABILITIES = "no_capabilities"


def parse_hello(message: dict) -> dict:
    """Validate a device hello structurally (F-02) and return it.

    The hello MUST carry an AEAD auth tag (auth_nonce + auth_tag);
    the tag itself is verified by evaluate_hello(). NOTE: the FULL
    message (including auth fields) is returned - evaluate_hello()
    needs them; pruning them here broke live hello verification
    (found by the P04 integration smoke test, fixed + regression
    tested).
    """
    if message.get("type") != protocol.MSG_HELLO:
        raise protocol.ProtocolError("expected hello as first message")
    protocol.require_str(message, "device_id")
    capabilities = message.get("capabilities")
    if not isinstance(capabilities, list) or not all(
            isinstance(capability, str) for capability in capabilities):
        raise protocol.ProtocolError(
            "hello capabilities must be a list of strings")
    protocol.require_str(message, "auth_nonce")
    protocol.require_str(message, "auth_tag")
    return message


def determine_path(capabilities: list) -> str:
    """Raw capability mapping (P03 policy input).

    Returns "legacy", "modern", "both" or "unknown". A device claiming
    BOTH capabilities is ambiguous - never auto-downgrade (P03 §8).
    """
    has_modern = protocol.CAP_MLKEM_768 in capabilities
    has_legacy = protocol.CAP_CHACHA20_POLY1305 in capabilities
    if has_modern and has_legacy:
        return "both"
    if has_modern:
        return "modern"
    if has_legacy:
        return "legacy"
    return "unknown"


def evaluate_hello(hello: dict, device_key) -> str:
    """Apply the P03 section 8 fallback policy to a parsed hello.

    device_key is the key from the known-device registry, or None for
    unknown device ids (the gateway must look the device up BEFORE
    verifying - unknown ids are rejected without a key).

    Returns ALLOW_FALLBACK or a REJECT_* constant.
    """
    if device_key is None:
        return REJECT_UNKNOWN_DEVICE
    try:
        crypto.verify_hello_auth(device_key, hello)
    except crypto.AuthenticationError:
        # Tampered claims, wrong key, or impersonation (F-02).
        return REJECT_UNAUTHENTICATED
    path = determine_path(hello["capabilities"])
    if path == "legacy":
        return ALLOW_FALLBACK
    if path == "modern":
        # TODO: Student review required - the modern device path is not
        # implemented; rejecting is the P03-approved honest policy.
        return REJECT_MODERN
    if path == "both":
        return REJECT_AMBIGUOUS
    return REJECT_NO_CAPABILITIES


# --- handshake message validation (F-03) --------------------------------------

def parse_mlkem_pubkey_reply(reply: dict) -> bytes:
    """Validate a mlkem_pubkey handshake reply and return the raw
    public key bytes.

    Raises ProtocolError on ANY violation - the uniform handshake
    validation policy (F-03/F-04). Never raises KeyError.
    """
    if reply.get("type") != protocol.MSG_MLKEM_PUBKEY:
        raise protocol.ProtocolError("expected mlkem_pubkey")
    protocol.require_str(reply, "cloud_id")
    raw = protocol.b64d(protocol.require_str(reply, "public_key"))
    if len(raw) != crypto.MLKEM768_PUBLIC_KEY_BYTES:
        raise protocol.ProtocolError("ML-KEM public key has invalid length")
    return raw


def parse_mlkem_established_reply(reply: dict,
                                  expected_session_id: str) -> None:
    """Validate a mlkem_established reply. Raises ProtocolError."""
    if reply.get("type") != protocol.MSG_MLKEM_ESTABLISHED:
        raise protocol.ProtocolError("expected mlkem_established")
    if protocol.require_str(reply, "session_id") != expected_session_id:
        raise protocol.ProtocolError("session_id does not match")


# --- cloud public key pinning (F-01) ------------------------------------------

def verify_cloud_public_key(raw_public_key: bytes,
                            expected_fingerprint: str) -> None:
    """Verify the received ML-KEM public key against the provisioned
    SHA-256 fingerprint (the trust anchor).

    P03 F-01 decision: fingerprint pinning. FAILS CLOSED when no pin
    is configured. Pinning protects against substitution only when
    the pin was provisioned through a trusted mechanism (P04 §12).
    """
    if not expected_fingerprint:
        raise crypto.CryptoError(
            "cloud public key pin is not configured "
            "(CLOUD_PUBLIC_KEY_SHA256) - refusing to establish session")
    actual = crypto.public_key_fingerprint(raw_public_key)
    if not secrets.compare_digest(actual, expected_fingerprint):
        raise crypto.CryptoError(
            "cloud public key fingerprint mismatch - "
            "possible key substitution")


# --- message processing --------------------------------------------------------

def decrypt_legacy_message(message: dict, key: bytes,
                           expected_device_id: str):
    """Decrypt and minimally validate a legacy reading message.

    Returns (plaintext_bytes, sequence). Raises ProcessingError for
    structural problems and crypto.LegacyDecryptionError for
    authentication failures.
    """
    if message.get("type") != protocol.MSG_LEGACY_READING:
        raise ProcessingError("unexpected message type on legacy path")
    if message.get("device_id") != expected_device_id:
        # Weak identity check - the real binding is the per-device key
        # plus the AAD (F-05/F-06).
        # TODO: Student review required - revisit for modern devices.
        raise ProcessingError("device_id mismatch")
    sequence = protocol.require_int(message, "seq")
    aad = protocol.legacy_message_aad(expected_device_id, sequence)
    plaintext = crypto.decrypt_legacy_payload(key, message, aad)
    try:
        protocol.parse_reading_bytes(plaintext)
    except protocol.ProtocolError as exc:
        raise ProcessingError(str(exc)) from exc
    return plaintext, sequence


def build_protected_reading(reading_bytes: bytes, session_key: bytes,
                            session_id: str) -> dict:
    """Wrap a device reading for the protected gateway->cloud session.

    AAD = session_id (channel binding, F-01/F-05): the message cannot
    be moved to another session without breaking authentication.
    """
    envelope = crypto.encrypt_session_payload(
        session_key, reading_bytes, protocol.session_message_aad(session_id))
    return {
        "type": protocol.MSG_PROTECTED_READING,
        "session_id": session_id,
        **envelope,
    }
