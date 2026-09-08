"""Simulated cloud service (project prompt section 4).

P04 changes (P03-approved):
  - F-04: handshake messages are field-validated (no more handler
    thread crashes on malformed input).
  - F-01: the cloud prints the SHA-256 fingerprint of its ML-KEM
    public key so the gateway can pin it; the keypair is persisted to
    CLOUD_KEY_FILE so the fingerprint stays stable across restarts
    (required for pinning + the F-07 reconnect demo).
  - F-05: per-device sequence enforcement on protected readings
    (defense in depth).
  - F-07/F-11: sessions are evicted when the gateway disconnects.
  - F-08: metrics semantics per P03 section F-08.

IMPORTANT (project prompt section 4): never print or log private
keys, shared secrets, or session keys. The public-key fingerprint is
a safe identifier and is the ONLY key-related value ever logged.
"""
import argparse
import socket
import threading
import time
from pathlib import Path

from common import config, crypto, health, protocol
from common.logging_setup import get_logger, setup_logging
from common.metrics import Metrics
from common.replay import ReplayGuard
from cloud import processing
from cloud.store import ReadingStore

logger = get_logger("cloud")


class SessionRegistry:
    """Maps session_id -> (session_key, gateway_id) for active sessions.

    P04 (F-07/F-11): sessions are REMOVED when the owning gateway
    connection closes, so stale session keys do not accumulate.
    Never holds the ML-KEM private key; never logs keys.
    """

    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()

    def add(self, session_id: str, session_key: bytes,
            gateway_id: str) -> None:
        with self._lock:
            self._sessions[session_id] = (session_key, gateway_id)

    def get(self, session_id: str):
        with self._lock:
            return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


class CloudServer:
    """TCP server accepting gateway connections."""

    def __init__(self, host: str, port: int, cloud_id: str,
                 registry: SessionRegistry, private_key,
                 public_key_raw: bytes, store: ReadingStore,
                 metrics: Metrics):
        self._host = host
        self._port = port
        self._cloud_id = cloud_id
        self._registry = registry
        self._private_key = private_key  # NEVER logged or exposed
        self._public_key_raw = public_key_raw  # public - safe to send
        self._store = store
        self._metrics = metrics
        self._replay = ReplayGuard()

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._host, self._port))
            server.listen(16)
            logger.info("cloud listening for gateways on %s:%d",
                        self._host, self._port)
            while True:
                conn, addr = server.accept()
                logger.info("gateway connection from %s:%d", *addr)
                self._metrics.inc("gateway_connections")
                threading.Thread(target=self._handle, args=(conn, addr),
                                 daemon=True).start()

    def _handle(self, conn: socket.socket, addr) -> None:
        session_id = None
        with conn:
            conn.settimeout(60)
            stream = conn.makefile("rb")
            try:
                session_id, session_key = self._establish_session(conn,
                                                                  stream)
                self._receive_readings(stream, session_id, session_key)
            except protocol.ConnectionClosedError:
                logger.info("gateway %s:%d disconnected", addr[0], addr[1])
            except (protocol.ProtocolError, processing.ProcessingError,
                    crypto.CryptoError, OSError) as exc:
                # F-04: malformed handshake messages land here as a
                # controlled protocol error - no more thread crashes.
                logger.warning("closing gateway connection %s:%d: %s",
                               addr[0], addr[1], exc)
                self._metrics.inc("errors")
            finally:
                if session_id is not None:
                    # F-07/F-11: evict the session when the
                    # connection ends (disconnect eviction).
                    self._registry.remove(session_id)
                    logger.info("session %s evicted", session_id)

    def _establish_session(self, conn: socket.socket, stream):
        """ML-KEM-768 decapsulation side of key establishment."""
        gateway_id = processing.parse_mlkem_request(
            protocol.read_message(stream))

        # Send our ML-KEM public key (public material - safe to send;
        # the gateway verifies its fingerprint - F-01).
        conn.sendall(protocol.encode_message({
            "type": protocol.MSG_MLKEM_PUBKEY,
            "cloud_id": self._cloud_id,
            "public_key": protocol.b64e(self._public_key_raw),
        }))

        session_id, ciphertext = processing.parse_mlkem_encaps(
            protocol.read_message(stream))

        start = time.perf_counter()
        # Library call (common/crypto.py). The shared secret is used
        # only to derive the session key and is never logged.
        shared_secret = crypto.mlkem_decapsulate(self._private_key,
                                                 ciphertext)
        session_key = crypto.derive_session_key(shared_secret)
        self._metrics.observe("mlkem_decapsulate_s",
                              time.perf_counter() - start, unit="s")
        self._metrics.inc("mlkem_sessions_established")
        self._registry.add(session_id, session_key, gateway_id)
        logger.info("ML-KEM-768 session %s established with gateway %s",
                    session_id, gateway_id)

        conn.sendall(protocol.encode_message({
            "type": protocol.MSG_MLKEM_ESTABLISHED,
            "session_id": session_id,
            "status": "ok",
        }))
        return session_id, session_key

    def _receive_readings(self, stream, session_id: str,
                          session_key: bytes) -> None:
        while True:
            message = protocol.read_message(stream)
            self._metrics.inc("messages_received")
            try:
                reading = processing.decrypt_protected_reading(
                    message, session_key, session_id)
            except (processing.ProcessingError, crypto.CryptoError) as exc:
                logger.warning("dropping protected message: %s", exc)
                self._metrics.inc("messages_rejected")
                continue
            sequence = reading.get("sequence")
            if not isinstance(sequence, int) or isinstance(sequence, bool):
                logger.warning("dropping reading without a valid sequence")
                self._metrics.inc("messages_rejected")
                continue
            if not self._replay.check_and_update(reading["device_id"],
                                                 sequence):
                # F-05: defense in depth - a compromised gateway cannot
                # replay stale readings into the cloud.
                logger.warning("REPLAY REJECTED for %s: sequence %d is "
                               "not newer than the last accepted one",
                               reading["device_id"], sequence)
                self._metrics.inc("messages_rejected")
                continue
            self._store.add(reading)
            self._metrics.inc("messages_processed")
            logger.info("stored reading from %s: seq=%s temp=%.2f C",
                        reading["device_id"], sequence,
                        reading["temperature_c"])


def load_or_generate_keypair(key_path: Path):
    """Load the persisted ML-KEM keypair, or generate + persist a new
    one (P04.8: the pinned fingerprint must stay stable across cloud
    restarts)."""
    if key_path.exists():
        try:
            private_key = crypto.load_mlkem_private_key(key_path)
            logger.info("loaded existing ML-KEM keypair from %s",
                        key_path)
            return private_key
        except (ValueError, OSError) as exc:
            logger.error("could not load keypair from %s (%s); "
                         "generating a new one", key_path, exc)
    private_key = crypto.generate_mlkem_keypair()
    crypto.save_mlkem_private_key(private_key, key_path)
    logger.info("generated new ML-KEM keypair; persisted to %s",
                key_path)
    return private_key


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulated cloud service")
    parser.add_argument("--cloud-id", default="cloud-01")
    parser.add_argument("--listen-host", default=config.CLOUD_LISTEN_HOST)
    parser.add_argument("--listen-port", type=int,
                        default=config.CLOUD_LISTEN_PORT)
    parser.add_argument("--health-port", type=int,
                        default=config.CLOUD_HEALTH_PORT)
    parser.add_argument("--key-file", default=config.CLOUD_KEY_FILE)
    return parser.parse_args(argv)


def main(argv=None) -> None:
    setup_logging()
    args = parse_args(argv)
    metrics = Metrics()
    store = ReadingStore()
    registry = SessionRegistry()
    private_key = load_or_generate_keypair(Path(args.key_file))
    public_key_raw = crypto.public_key_bytes(private_key.public_key())
    # The fingerprint is a SAFE identifier (P04 section 19) and is the
    # trust anchor the gateway pins (F-01). Never log the key itself.
    logger.info("cloud %s ML-KEM public key SHA-256 fingerprint:",
                args.cloud_id)
    logger.info("  %s", crypto.public_key_fingerprint(public_key_raw))
    logger.info("provision this value as CLOUD_PUBLIC_KEY_SHA256 on the "
                "gateway (F-01 pinning)")

    server = CloudServer(args.listen_host, args.listen_port, args.cloud_id,
                         registry, private_key, public_key_raw, store,
                         metrics)
    health.make_health_server(
        args.health_port, "cloud",
        lambda: {
            "mlkem_ready": True,
            "stored_readings": store.count(),
            "active_sessions": registry.count(),
            **metrics.snapshot(),
        },
        # Demo endpoint: recent non-sensitive application data.
        extra_routes={"/readings": lambda: store.recent(10)},
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("cloud stopped by user")


if __name__ == "__main__":
    main()
