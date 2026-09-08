"""Pure processing helpers for the cloud service (project prompt
section 4). Kept free of sockets/threads for direct testing.

P04 changes (P03-approved):
  - F-04: handshake messages are field-validated (ProtocolError) -
    malformed input can no longer crash a handler thread.
  - F-05: protected readings bind the session_id as AAD.
"""
from common import crypto, protocol


class ProcessingError(Exception):
    """Raised when a protected message cannot be processed."""


def parse_mlkem_request(request: dict) -> str:
    """Validate mlkem_request_pubkey; returns the gateway_id.

    P08 BF-01: the request must also carry the AEAD auth fields
    (auth_nonce + auth_tag) over the gateway identity claim. Raises
    ProtocolError on ANY structural violation (uniform handshake
    validation policy, F-03/F-04)."""
    if request.get("type") != protocol.MSG_MLKEM_REQUEST_PUBKEY:
        raise protocol.ProtocolError(
            "expected mlkem_request_pubkey as first message")
    gateway_id = protocol.require_str(request, "gateway_id")
    protocol.require_str(request, "auth_nonce")
    protocol.require_str(request, "auth_tag")
    return gateway_id


def verify_gateway_request_auth(request: dict, gateway_key: bytes) -> None:
    """Verify a gateway handshake request's AEAD tag (P08 BF-01).

    Raises crypto.AuthenticationError when the tag is missing,
    tampered, or produced with the wrong key.
    """
    crypto.verify_gateway_auth(
        gateway_key,
        request["gateway_id"],
        request["auth_nonce"],
        request["auth_tag"],
    )


def parse_mlkem_encaps(encaps: dict):
    """Validate mlkem_encaps; returns (session_id, raw ciphertext).

    Raises ProtocolError on ANY violation. Never raises KeyError."""
    if encaps.get("type") != protocol.MSG_MLKEM_ENCAPS:
        raise protocol.ProtocolError("expected mlkem_encaps")
    session_id = protocol.require_str(encaps, "session_id")
    ciphertext = protocol.b64d(protocol.require_str(encaps, "ciphertext"))
    if len(ciphertext) != crypto.MLKEM768_CIPHERTEXT_BYTES:
        raise protocol.ProtocolError("ML-KEM ciphertext has invalid length")
    return session_id, ciphertext


def decrypt_protected_reading(message: dict, session_key: bytes,
                              session_id: str) -> dict:
    """Decrypt and validate a protected reading from a gateway.

    AAD = session_id (channel binding, F-01/F-05): the message cannot
    be moved to another session without breaking authentication.
    Returns the parsed reading dict.
    """
    if message.get("type") != protocol.MSG_PROTECTED_READING:
        raise ProcessingError("unexpected message type on protected path")
    if protocol.require_str(message, "session_id") != session_id:
        # TODO: Student review required - session binding is minimal;
        # the AAD provides the cryptographic binding.
        raise ProcessingError("session_id mismatch")
    plaintext = crypto.decrypt_session_payload(
        session_key, message, protocol.session_message_aad(session_id))
    try:
        return protocol.parse_reading_bytes(plaintext)
    except protocol.ProtocolError as exc:
        raise ProcessingError(str(exc)) from exc
