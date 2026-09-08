"""Simple JSON-lines application protocol shared by all components.

Design choice (assumption + trade-off): a tiny newline-delimited JSON
protocol over raw TCP is used instead of HTTP/MQTT to keep the
simulation understandable for students. No TLS - see README
"Security limitations".

P04 changes (P03-approved):
  - hello messages carry an AEAD auth tag over the capability claims
    (F-02, downgrade resistance)
  - legacy readings carry a plaintext `seq` field bound into the AEAD
    AAD (F-05, replay protection)
  - protected readings bind the session_id as AAD (F-01/F-05 channel
    binding)
  - uniform handshake field validation helpers (F-03/F-04)
  - F-15: oversized vs. truncated messages are distinguished
"""
import base64
import json

MAX_MESSAGE_BYTES = 64 * 1024  # 64 KiB cap on a single message

# Message types
MSG_HELLO = "hello"
MSG_LEGACY_READING = "legacy_reading"
MSG_MLKEM_REQUEST_PUBKEY = "mlkem_request_pubkey"
MSG_MLKEM_PUBKEY = "mlkem_pubkey"
MSG_MLKEM_ENCAPS = "mlkem_encaps"
MSG_MLKEM_ESTABLISHED = "mlkem_established"
MSG_PROTECTED_READING = "protected_reading"
MSG_ERROR = "error"

# Device capability names (project prompt section 3: two paths)
CAP_CHACHA20_POLY1305 = "chacha20-poly1305"
CAP_MLKEM_768 = "ml-kem-768"


class ProtocolError(Exception):
    """Raised when an incoming message violates the wire protocol."""


class ConnectionClosedError(Exception):
    """Raised when the peer closes the connection cleanly."""


def b64e(data: bytes) -> str:
    """Base64-encode bytes for embedding in JSON messages."""
    return base64.b64encode(data).decode("ascii")


def b64d(text: str) -> bytes:
    """Inverse of b64e(). Raises ProtocolError on malformed input."""
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, TypeError) as exc:
        raise ProtocolError("invalid base64 field") from exc


def require_str(message: dict, field: str) -> str:
    """Return message[field] as a non-empty string or raise
    ProtocolError. Part of the uniform handshake validation policy
    (F-03/F-04)."""
    value = message.get(field)
    if not isinstance(value, str) or not value:
        raise ProtocolError(
            f"message missing required string field '{field}'")
    return value


def require_int(message: dict, field: str) -> int:
    """Return message[field] as an int (bools excluded) or raise
    ProtocolError."""
    value = message.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError(
            f"message missing required integer field '{field}'")
    return value


def encode_message(message: dict) -> bytes:
    """Serialize a message to JSON + newline."""
    try:
        return json.dumps(message, separators=(",", ":")).encode("utf-8") \
            + b"\n"
    except (TypeError, ValueError) as exc:
        raise ProtocolError("cannot serialize message") from exc


def read_message(stream) -> dict:
    """Read one newline-delimited JSON object from a buffered stream.

    stream: any object with readline(limit) -> bytes (a socket makefile
    or a BufferedReader). Enforces MAX_MESSAGE_BYTES so that a peer
    cannot make us buffer unbounded data.

    F-15: distinguishes an oversized message from a message truncated
    at EOF (missing trailing newline).
    """
    line = stream.readline(MAX_MESSAGE_BYTES + 1)
    if not line:
        raise ConnectionClosedError("peer closed the connection")
    if len(line) > MAX_MESSAGE_BYTES:
        raise ProtocolError("message exceeds maximum allowed size")
    if not line.endswith(b"\n"):
        raise ProtocolError("connection closed mid-message "
                            "(missing newline)")
    try:
        message = json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProtocolError("message is not valid JSON") from exc
    if not isinstance(message, dict):
        raise ProtocolError("message must be a JSON object")
    return message


# --- AAD construction (P03 F-05: binding security context) --------------------

def legacy_message_aad(device_id: str, sequence: int) -> bytes:
    """AAD for device->gateway readings: binds device id and sequence
    so neither can be changed without breaking authentication."""
    return f"{device_id}:{sequence}".encode("utf-8")


def session_message_aad(session_id: str) -> bytes:
    """AAD for gateway->cloud readings: binds the message to its
    ML-KEM session (channel binding, F-01/F-05)."""
    return session_id.encode("utf-8")


def hello_claims_bytes(device_id: str, capabilities: list) -> bytes:
    """Canonical serialization of the hello claims authenticated by
    the hello's AEAD tag (F-02). Sender and verifier MUST both use
    this exact format."""
    return json.dumps(
        {"device_id": device_id, "capabilities": capabilities},
        separators=(",", ":")).encode("utf-8")


def gateway_auth_claims_bytes(gateway_id: str) -> bytes:
    """Canonical serialization of the gateway identity claim
    authenticated by the gateway handshake AEAD tag (P08 BF-01).
    Sender and verifier MUST both use this exact format. The `scope`
    field gives domain separation from the device hello claims."""
    return json.dumps(
        {"gateway_id": gateway_id, "scope": "gateway-cloud-handshake"},
        separators=(",", ":")).encode("utf-8")


def parse_reading_bytes(plaintext: bytes) -> dict:
    """Validate that decrypted plaintext is a JSON sensor reading.

    P04 (F-05): readings MUST carry an integer `sequence` for replay
    protection - a documented protocol change from P01.

    TODO: Student review required - add stricter validation (value
    ranges, timestamp sanity).
    """
    try:
        reading = json.loads(plaintext.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProtocolError("plaintext is not valid JSON") from exc
    required = {"device_id", "timestamp", "temperature_c", "sequence"}
    if not isinstance(reading, dict) or not required.issubset(reading):
        raise ProtocolError("reading is missing required fields")
    return reading
