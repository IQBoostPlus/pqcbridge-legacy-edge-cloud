"""Thin wrappers around the `cryptography` library.

IMPORTANT (project prompt section 6):
  - NO cryptographic algorithms are implemented from scratch here.
  - ChaCha20-Poly1305, HKDF-SHA256 and ML-KEM-768 are all provided by
    the `cryptography` library (built on its bundled OpenSSL >= 3.5).

P04 changes (P03-approved):
  - AEAD wrappers accept AAD (F-09 refactor + F-05 context binding)
  - hello AEAD tags (F-02)
  - ML-KEM public-key fingerprints for pinning (F-01)
  - ML-KEM private-key persistence (P04.8: needed so the cloud's
    public key fingerprint stays stable across restarts - otherwise
    the pin would break on every cloud restart and the F-07 reconnect
    demo would be impossible)

IMPORTANT (project prompt section 4):
  - NEVER log or print private keys, shared secrets or session keys.
    Use public_key_fingerprint() or session IDs as safe identifiers.
"""
import hashlib
import os
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import mlkem
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)

from common import protocol

MLKEM768PrivateKey = mlkem.MLKEM768PrivateKey
MLKEM768PublicKey = mlkem.MLKEM768PublicKey

# Verified against cryptography 50.0.1 during P04.1.
MLKEM768_PUBLIC_KEY_BYTES = 1184
MLKEM768_CIPHERTEXT_BYTES = 1088

# HKDF info string ties the derived key to its purpose (key
# separation). Library implementation (cryptography.hazmat).
SESSION_KEY_INFO = b"pqc-bridge/gateway-cloud-session/v1"

# Standard nonce size for ChaCha20-Poly1305.
NONCE_LENGTH = 12

# ML-KEM-768 produces a 32-byte shared secret.
MLKEM_SHARED_SECRET_LENGTH = 32


class CryptoError(Exception):
    """Base error for cryptographic failures in the prototype."""


class AuthenticationError(CryptoError):
    """An AEAD-authenticated message failed verification."""


class LegacyDecryptionError(CryptoError):
    """A legacy (per-device-key) message failed authentication."""


class MLKEMDecapsulationError(CryptoError):
    """ML-KEM decapsulation failed."""


# --- AEAD core (F-09: one implementation, four thin wrappers) -----------------

def _aead_encrypt(key: bytes, plaintext: bytes, aad) -> dict:
    """Core ChaCha20-Poly1305 encrypt (library call).

    aad: authenticated (not encrypted) context, or None.
    """
    nonce = os.urandom(NONCE_LENGTH)
    chacha = ChaCha20Poly1305(key)
    return {
        "nonce": protocol.b64e(nonce),
        "ciphertext": protocol.b64e(chacha.encrypt(nonce, plaintext, aad)),
    }


def _aead_decrypt(key: bytes, envelope: dict, aad, error_cls) -> bytes:
    """Core ChaCha20-Poly1305 decrypt (library call).

    Raises error_cls on malformed envelopes or authentication failure.

    P06 (NEW-1): a nonce field that decodes to the wrong length is
    malformed attacker-controlled input and raises ProtocolError
    BEFORE the AEAD call - ChaCha20Poly1305.decrypt() would otherwise
    raise an unhandled ValueError ("Nonce must be 12 bytes"), which
    killed handler threads with uncontrolled tracebacks and bypassed
    the error metrics (see review/P05 NEW-1). Only the length is
    reported, never the nonce bytes.
    """
    try:
        nonce = protocol.b64d(envelope["nonce"])
        ciphertext = protocol.b64d(envelope["ciphertext"])
    except (KeyError, TypeError) as exc:
        raise error_cls("malformed envelope") from exc
    if len(nonce) != NONCE_LENGTH:
        raise protocol.ProtocolError(
            f"invalid nonce length ({len(nonce)})")
    try:
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise error_cls(
            "authentication failed (wrong key or tampered data)") from exc


def encrypt_legacy_payload(key: bytes, plaintext: bytes, aad=None) -> dict:
    """Encrypt a legacy-path payload (library call)."""
    return _aead_encrypt(key, plaintext, aad)


def decrypt_legacy_payload(key: bytes, envelope: dict, aad=None) -> bytes:
    """Decrypt a legacy-path payload. Raises LegacyDecryptionError."""
    return _aead_decrypt(key, envelope, aad, LegacyDecryptionError)


def encrypt_session_payload(key: bytes, plaintext: bytes, aad=None) -> dict:
    """Encrypt a protected-path payload (library call)."""
    return _aead_encrypt(key, plaintext, aad)


def decrypt_session_payload(key: bytes, envelope: dict, aad=None) -> bytes:
    """Decrypt a protected-path payload. Raises CryptoError."""
    return _aead_decrypt(key, envelope, aad, CryptoError)


# --- Authenticated hello (F-02) ----------------------------------------------

def build_hello(device_id: str, capabilities: list, key: bytes) -> dict:
    """Build a hello with an AEAD tag over the capability claims.

    The tag is the ChaCha20-Poly1305 output over EMPTY plaintext with
    the claims as AAD - a MAC-only use of the library AEAD. It proves
    possession of the device key and authenticates the claims, so a
    MITM cannot strip or forge capabilities (downgrade resistance).
    """
    nonce = os.urandom(NONCE_LENGTH)
    claims = protocol.hello_claims_bytes(device_id, capabilities)
    tag = ChaCha20Poly1305(key).encrypt(nonce, b"", claims)
    return {
        "type": protocol.MSG_HELLO,
        "device_id": device_id,
        "capabilities": capabilities,
        "auth_nonce": protocol.b64e(nonce),
        "auth_tag": protocol.b64e(tag),
    }


def verify_hello_auth(key: bytes, hello: dict) -> None:
    """Verify the hello's AEAD tag. Raises AuthenticationError."""
    try:
        nonce = protocol.b64d(hello["auth_nonce"])
        tag = protocol.b64d(hello["auth_tag"])
        # P06 (NEW-1): a wrong-length nonce is malformed hello auth
        # input - reject it here (as AuthenticationError via the
        # existing conversion below) instead of letting the library
        # raise an unhandled ValueError (see review/P05 NEW-1).
        if len(nonce) != NONCE_LENGTH:
            raise protocol.ProtocolError("invalid nonce length")
        claims = protocol.hello_claims_bytes(
            hello["device_id"], hello["capabilities"])
    except (KeyError, TypeError, protocol.ProtocolError) as exc:
        raise AuthenticationError("malformed hello auth fields") from exc
    try:
        ChaCha20Poly1305(key).decrypt(nonce, tag, claims)  # empty plaintext
    except InvalidTag as exc:
        raise AuthenticationError("hello authentication failed") from exc


# --- ML-KEM-768 ---------------------------------------------------------------

def generate_mlkem_keypair():
    """Generate a fresh ML-KEM-768 keypair (library call).

    TODO: Student review required - key rotation is out of scope for
    the prototype (P03 F-11 deferred).
    """
    return MLKEM768PrivateKey.generate()


def save_mlkem_private_key(private_key, path) -> None:
    """Persist an ML-KEM private key as its raw seed bytes (64 bytes
    for ML-KEM-768; verified against cryptography 50.0.1 in P04.1).

    NOTE: file permissions are NOT hardened - prototype limitation.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(private_key.private_bytes_raw())


def load_mlkem_private_key(path):
    """Load a persisted ML-KEM private key. Raises ValueError on bad
    data."""
    return MLKEM768PrivateKey.from_seed_bytes(Path(path).read_bytes())


def public_key_bytes(public_key) -> bytes:
    """Raw-encode an ML-KEM public key for transport."""
    return public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)


def public_key_fingerprint(raw_public_key: bytes) -> str:
    """SHA-256 hex fingerprint of the raw public key.

    This is the SAFE identifier for key material: fingerprints may be
    logged and compared freely (P04 section 19)."""
    return hashlib.sha256(raw_public_key).hexdigest()


def load_public_key(data: bytes):
    """Decode raw public key bytes. Raises ProtocolError on bad input."""
    try:
        return MLKEM768PublicKey.from_public_bytes(data)
    except ValueError as exc:
        raise protocol.ProtocolError("invalid ML-KEM public key data") \
            from exc


def mlkem_encapsulate(public_key):
    """Perform ML-KEM-768 encapsulation (library call).

    Returns (shared_secret, ciphertext). Only the ciphertext is ever
    transmitted; the shared secret stays in memory.
    """
    shared_secret, ciphertext = public_key.encapsulate()
    return shared_secret, ciphertext


def mlkem_decapsulate(private_key, ciphertext: bytes) -> bytes:
    """Perform ML-KEM-768 decapsulation (library call).

    Raises MLKEMDecapsulationError on wrong-length ciphertexts.

    NOTE (student review point): a WRONG ciphertext of the correct
    length does NOT raise - FIPS 203 implicit rejection returns a
    pseudorandom rejection key. The resulting AEAD session then fails
    to authenticate. Do not rely on decapsulation raising to detect
    substituted ciphertexts.
    """
    try:
        return private_key.decapsulate(ciphertext)
    except ValueError as exc:
        raise MLKEMDecapsulationError("decapsulation failed") from exc


def derive_session_key(shared_secret: bytes) -> bytes:
    """Derive a 32-byte symmetric session key from the ML-KEM shared
    secret using HKDF-SHA256 (library call, cryptography.hazmat).

    A KDF with a context-specific `info` string is standard practice
    after ML-KEM key establishment; it also keeps the raw shared
    secret separate from the key actually used for traffic.
    """
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=SESSION_KEY_INFO)
    return hkdf.derive(shared_secret)
