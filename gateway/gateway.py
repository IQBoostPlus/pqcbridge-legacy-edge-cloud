"""Edge gateway: receives readings from legacy devices and forwards
them to the cloud over an ML-KEM-768-protected session (project prompt
section 3).

P04 changes (P03-approved):
  - F-02/F-06: device hellos are authenticated with per-device keys;
    fallback policy per P03 section 8 (only known legacy devices with
    valid tags are admitted).
  - F-05: per-device monotonic sequence enforcement (ReplayGuard).
  - F-07/F-13: cloud session state is reported truthfully in /health.
  - F-08: metrics semantics per P03 section F-08.

Fallback policy summary (P03 section 8):
  legacy-only + known device + valid tag -> FALLBACK (weaker posture)
  modern / both / unknown caps / unknown device / bad tag -> REJECT
"""
import argparse
import socket
import threading
import time

from common import config, crypto, health, protocol
from common.logging_setup import get_logger, setup_logging
from common.metrics import Metrics
from common.replay import ReplayGuard
from gateway import processing
from gateway.cloud_channel import CloudChannel

logger = get_logger("gateway")


class DeviceServer:
    """TCP server accepting connections from simulated devices."""

    def __init__(self, host: str, port: int, cloud_channel: CloudChannel,
                 metrics: Metrics):
        self._host = host
        self._port = port
        self._cloud = cloud_channel
        self._metrics = metrics
        self._replay = ReplayGuard()
        self._seen_lock = threading.Lock()
        self._seen_devices = set()

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._host, self._port))
            server.listen(16)
            logger.info("gateway listening for devices on %s:%d",
                        self._host, self._port)
            while True:
                conn, addr = server.accept()
                logger.info("device connection attempt from %s:%d", *addr)
                self._metrics.inc("device_connections")
                threading.Thread(target=self._handle, args=(conn, addr),
                                 daemon=True).start()

    def _handle(self, conn: socket.socket, addr) -> None:
        with conn:
            conn.settimeout(60)
            stream = conn.makefile("rb")
            try:
                hello = processing.parse_hello(
                    protocol.read_message(stream))
                self._admit_or_serve(stream, hello)
            except protocol.ConnectionClosedError:
                logger.info("device %s:%d disconnected", addr[0], addr[1])
            except (protocol.ProtocolError, processing.ProcessingError,
                    crypto.CryptoError, OSError) as exc:
                logger.warning("closing device connection %s:%d: %s",
                               addr[0], addr[1], exc)
                self._metrics.inc("errors")

    def _admit_or_serve(self, stream, hello: dict) -> None:
        """Apply the P03 section 8 fallback policy, then serve."""
        device_id = hello["device_id"]
        # Look up the device FIRST: unknown ids are rejected without
        # even attempting tag verification (P03 section 4 F-02).
        try:
            device_key = config.device_key(device_id)
        except KeyError:
            logger.warning("rejecting UNKNOWN device %s", device_id)
            self._metrics.inc("messages_rejected")
            return
        decision = processing.evaluate_hello(hello, device_key)
        if decision == processing.REJECT_UNAUTHENTICATED:
            logger.warning("rejecting device %s: hello authentication "
                           "FAILED (tampered claims or wrong key)",
                           device_id)
            self._metrics.inc("messages_rejected")
            return
        if decision == processing.REJECT_MODERN:
            # TODO: Student review required - the modern device path is
            # not implemented; rejection is the P03-approved policy.
            logger.warning("rejecting device %s: claims the modern path "
                           "(NOT IMPLEMENTED in this baseline)", device_id)
            self._metrics.inc("messages_rejected")
            return
        if decision == processing.REJECT_AMBIGUOUS:
            logger.warning("rejecting device %s: ambiguous capability "
                           "claims (never auto-downgrade)", device_id)
            self._metrics.inc("messages_rejected")
            return
        if decision == processing.REJECT_NO_CAPABILITIES:
            logger.warning("rejecting device %s: no supported "
                           "capabilities", device_id)
            self._metrics.inc("messages_rejected")
            return
        # ALLOW_FALLBACK: an authenticated legacy device.
        self._metrics.inc("fallback_activations")
        with self._seen_lock:
            if device_id not in self._seen_devices:
                self._seen_devices.add(device_id)
                self._metrics.inc("legacy_devices_detected")
        # Deliberately a warning: the fallback path provides a WEAKER
        # security posture than the modern PQC path (P03 section 7.7).
        logger.warning(
            "FALLBACK ACTIVATED: device %s uses the legacy path "
            "(ChaCha20-Poly1305). This is WEAKER than the modern PQC "
            "path.", device_id)
        self._serve_legacy(stream, device_id, device_key)

    def _serve_legacy(self, stream, device_id: str,
                      device_key: bytes) -> None:
        while True:
            message = protocol.read_message(stream)
            self._metrics.inc("messages_received")
            try:
                reading_bytes, sequence = processing.decrypt_legacy_message(
                    message, device_key, device_id)
            except (processing.ProcessingError,
                    crypto.LegacyDecryptionError) as exc:
                logger.warning("dropping message from %s: %s",
                               device_id, exc)
                self._metrics.inc("messages_rejected")
                continue
            if not self._replay.check_and_update(device_id, sequence):
                # F-05: duplicate or stale sequence -> replay rejected.
                logger.warning("REPLAY REJECTED for %s: sequence %d is "
                               "not newer than the last accepted one",
                               device_id, sequence)
                self._metrics.inc("messages_rejected")
                continue
            self._metrics.inc("messages_processed")
            start = time.perf_counter()
            self._cloud.send_reading(reading_bytes)
            self._metrics.inc("messages_forwarded")
            self._metrics.observe("forward_s",
                                  time.perf_counter() - start, unit="s")
            self._metrics.observe("payload_bytes", len(reading_bytes),
                                  unit="bytes")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Edge gateway")
    parser.add_argument("--gateway-id", default="gw-01")
    parser.add_argument("--listen-host", default=config.GATEWAY_LISTEN_HOST)
    parser.add_argument("--listen-port", type=int,
                        default=config.GATEWAY_LISTEN_PORT)
    parser.add_argument("--cloud-host", default=config.GATEWAY_CLOUD_HOST)
    parser.add_argument("--cloud-port", type=int,
                        default=config.GATEWAY_CLOUD_PORT)
    parser.add_argument("--health-port", type=int,
                        default=config.GATEWAY_HEALTH_PORT)
    return parser.parse_args(argv)


def main(argv=None) -> None:
    setup_logging()
    args = parse_args(argv)
    metrics = Metrics()
    cloud_channel = CloudChannel(args.gateway_id, args.cloud_host,
                                 args.cloud_port, metrics)
    logger.info("gateway %s starting; connecting to cloud %s:%d",
                args.gateway_id, args.cloud_host, args.cloud_port)
    cloud_channel.connect_and_establish()

    health.make_health_server(args.health_port, "gateway", lambda: {
        # F-13: truthful operational status (P03 section F-13).
        "status": "ok" if cloud_channel.is_established() else "degraded",
        "cloud_session_id": cloud_channel.session_id,
        "cloud_connected": cloud_channel.is_established(),
        "cloud_state": cloud_channel.state.value,
        **metrics.snapshot(),
    })

    server = DeviceServer(args.listen_host, args.listen_port,
                          cloud_channel, metrics)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("gateway stopped by user")


if __name__ == "__main__":
    main()
