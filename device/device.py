"""Simulated legacy IoT device (project prompt section 2).

P04 changes (P03-approved):
  - the device authenticates its hello with an AEAD tag under its OWN
    per-device key (F-06/F-02)
  - readings carry a monotonic sequence persisted to disk and bound
    into the AEAD AAD (F-05)
  - the device MUST NOT implement or execute ML-KEM: the whole point
    of the "legacy" role is that some devices cannot move to PQC
    immediately and need the fallback path during migration

TODO: Student review required.
  - No reconnect/backoff logic: if the gateway is unreachable at
    startup the device exits (P03: deferred).
"""
import argparse
import socket
import time
from pathlib import Path

from common import config, crypto, protocol
from common.logging_setup import get_logger, setup_logging
from device import sensor, state

logger = get_logger("device")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulated legacy IoT device")
    parser.add_argument("--device-id", default="dev-01")
    parser.add_argument("--gateway-host", default=config.DEVICE_GATEWAY_HOST)
    parser.add_argument("--gateway-port", type=int,
                        default=config.DEVICE_GATEWAY_PORT)
    parser.add_argument("--interval", type=float,
                        default=config.DEVICE_INTERVAL_SECONDS)
    parser.add_argument("--state-dir", default=config.DEVICE_STATE_DIR)
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    key = config.local_device_key()
    state_path = Path(args.state_dir) / f"{args.device_id}.seq"
    sequence = state.load_sequence(state_path)
    logger.info("device %s starting (gateway %s:%d, interval %.1fs, "
                "sequence resumes at %d)", args.device_id,
                args.gateway_host, args.gateway_port, args.interval,
                sequence)
    sock = socket.create_connection((args.gateway_host, args.gateway_port),
                                    timeout=10)
    with sock:
        # Authenticated hello (F-02): the tag proves possession of the
        # device key and protects the capability claims.
        hello = crypto.build_hello(args.device_id,
                                   [protocol.CAP_CHACHA20_POLY1305], key)
        sock.sendall(protocol.encode_message(hello))
        logger.info("hello sent; capabilities: [%s]",
                    protocol.CAP_CHACHA20_POLY1305)
        while True:
            sequence += 1
            reading = sensor.generate_reading(args.device_id, sequence)
            plaintext = sensor.reading_to_bytes(reading)
            # F-05: the sequence is bound into the AEAD AAD, so
            # changing it breaks authentication.
            aad = protocol.legacy_message_aad(args.device_id, sequence)
            envelope = crypto.encrypt_legacy_payload(key, plaintext, aad)
            sock.sendall(protocol.encode_message({
                "type": protocol.MSG_LEGACY_READING,
                "device_id": args.device_id,
                "seq": sequence,
                **envelope,
            }))
            state.save_sequence(state_path, sequence)
            logger.info("reading #%d sent (temp=%.2f C)",
                        sequence, reading["temperature_c"])
            time.sleep(args.interval)


def main(argv=None) -> None:
    setup_logging()
    args = parse_args(argv)
    try:
        run(args)
    except KeyboardInterrupt:
        logger.info("device stopped by user")
    except OSError as exc:
        logger.error("device terminating due to connection error: %s", exc)


if __name__ == "__main__":
    main()
