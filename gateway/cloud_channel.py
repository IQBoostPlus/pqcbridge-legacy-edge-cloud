"""The gateway's client-side ML-KEM session with the cloud service.

P04 changes (P03-approved):
  - F-01: the cloud's ML-KEM public key is verified against a
    provisioned SHA-256 fingerprint BEFORE encapsulation.
  - F-03: handshake replies are field-validated (ProtocolError) - a
    malformed reply can no longer crash the gateway.
  - F-07: five-state session lifecycle (DISCONNECTED -> CONNECTING ->
    ESTABLISHING -> ESTABLISHED -> FAILED -> ...); send failures
    invalidate the session and trigger reconnection; a NEW session id
    is generated per establishment attempt.

IMPORTANT (documented limitation, P03 section 7.1): the cloud does
NOT authenticate the gateway - gateway_id is self-declared.
"""
import enum
import secrets
import socket
import threading
import time

from common import config, crypto, protocol
from common.logging_setup import get_logger
from common.metrics import Metrics
from gateway import processing

logger = get_logger("gateway.cloud_channel")

RETRY_DELAY_SECONDS = 3.0


class State(enum.Enum):
    """Cloud session state machine (P03 section 10 / F-07)."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ESTABLISHING = "establishing"
    ESTABLISHED = "established"
    FAILED = "failed"


class CloudChannel:
    """Maintains one ML-KEM-protected session to the cloud."""

    def __init__(self, gateway_id: str, host: str, port: int,
                 metrics: Metrics, auto_reconnect: bool = True,
                 gateway_key: bytes = None):
        self.gateway_id = gateway_id
        # P08 BF-01: the gateway's own credential (from config by
        # default). NEVER logged or exposed.
        self.gateway_key = (gateway_key if gateway_key is not None
                            else config.local_gateway_key())
        self.host = host
        self.port = port
        self.metrics = metrics
        self.state = State.DISCONNECTED
        # session_id is a safe identifier - NOT a secret. It is
        # generated per establishment attempt (P03 F-07).
        self.session_id = None
        self.session_key = None  # NEVER logged or exposed
        self._sock = None
        self._send_lock = threading.Lock()
        self._auto_reconnect = auto_reconnect
        self._reconnecting = False
        self._reconnect_lock = threading.Lock()

    def is_established(self) -> bool:
        return (self.state is State.ESTABLISHED
                and self._sock is not None
                and self.session_key is not None)

    def connect_and_establish(self, max_attempts=None) -> bool:
        """Blocking connect + ML-KEM establishment with retry.

        Returns True on success. max_attempts=None retries forever
        (startup behavior); a limit is used by tests.
        """
        attempts = 0
        while True:
            attempts += 1
            self.state = State.CONNECTING
            try:
                self._establish_once()
                self.state = State.ESTABLISHED
                return True
            except (OSError, protocol.ProtocolError,
                    crypto.CryptoError) as exc:
                self.metrics.inc("errors")
                self.state = State.FAILED
                logger.warning("cloud session attempt %d failed (%s)",
                               attempts, exc)
                self.state = State.DISCONNECTED
                if max_attempts is not None and attempts >= max_attempts:
                    return False
                time.sleep(RETRY_DELAY_SECONDS)

    def _establish_once(self) -> None:
        # NEW session id per attempt (P03 F-07).
        session_id = secrets.token_hex(8)
        sock = socket.create_connection((self.host, self.port), timeout=10)
        stream = sock.makefile("rb")
        start = time.perf_counter()
        try:
            self.state = State.ESTABLISHING
            # 1. Request the cloud's ML-KEM public key.
            #    P08 BF-01: authenticate the request with an AEAD tag
            #    over the gateway identity claim (proves possession of
            #    the gateway credential; the cloud rejects otherwise).
            auth = crypto.build_gateway_auth(self.gateway_id,
                                             self.gateway_key)
            sock.sendall(protocol.encode_message({
                "type": protocol.MSG_MLKEM_REQUEST_PUBKEY,
                "gateway_id": self.gateway_id,
                **auth,
            }))
            # 2. Validate the reply (F-03) and verify the pin (F-01)
            # BEFORE encapsulating to the received key.
            reply = protocol.read_message(stream)
            public_key_raw = processing.parse_mlkem_pubkey_reply(reply)
            processing.verify_cloud_public_key(
                public_key_raw, config.cloud_public_key_sha256())
            public_key = crypto.load_public_key(public_key_raw)
            # 3. Encapsulate (library call): shared secret + ciphertext.
            # The shared secret never leaves this process unencrypted.
            shared_secret, ciphertext = crypto.mlkem_encapsulate(public_key)
            # 4. Send the ciphertext; the cloud derives the same
            # secret via decapsulation.
            sock.sendall(protocol.encode_message({
                "type": protocol.MSG_MLKEM_ENCAPS,
                "gateway_id": self.gateway_id,
                "session_id": session_id,
                "ciphertext": protocol.b64e(ciphertext),
            }))
            reply = protocol.read_message(stream)
            processing.parse_mlkem_established_reply(reply, session_id)
            # 5. Derive the symmetric session key (HKDF, library call).
            self.session_key = crypto.derive_session_key(shared_secret)
            self.session_id = session_id
            self.metrics.inc("mlkem_sessions_established")
            self.metrics.observe("mlkem_establish_s",
                                 time.perf_counter() - start, unit="s")
            logger.info("ML-KEM-768 session %s established with cloud",
                        session_id)
            self._sock = sock
        except Exception:
            sock.close()
            raise

    def send_reading(self, reading_bytes: bytes) -> None:
        """Forward one device reading over the protected session.

        Raises crypto.CryptoError when the session is not usable. A
        send failure invalidates the session (F-07) and starts a
        background reconnect when auto_reconnect is enabled.
        """
        if not self.is_established():
            raise crypto.CryptoError("no established cloud session")
        message = processing.build_protected_reading(
            reading_bytes, self.session_key, self.session_id)
        payload = protocol.encode_message(message)
        with self._send_lock:
            try:
                self._sock.sendall(payload)
            except OSError as exc:
                self._invalidate()
                raise crypto.CryptoError("cloud session failed") from exc

    def _invalidate(self) -> None:
        """FAILED transition: the session is no longer usable (P03 §10)."""
        old_session_id = self.session_id
        self._sock = None
        self.session_key = None
        self.state = State.FAILED
        logger.warning("cloud session %s FAILED; will reconnect",
                       old_session_id)
        if self._auto_reconnect:
            self._start_reconnect()

    def _start_reconnect(self) -> None:
        with self._reconnect_lock:
            if self._reconnecting:
                return
            self._reconnecting = True
        threading.Thread(target=self._reconnect_loop, daemon=True,
                         name="cloud-reconnect").start()

    def _reconnect_loop(self) -> None:
        try:
            # connect_and_establish retries until it succeeds.
            self.connect_and_establish()
        finally:
            with self._reconnect_lock:
                self._reconnecting = False
