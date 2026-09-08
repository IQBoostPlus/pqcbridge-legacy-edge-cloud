"""Central configuration for the legacy-edge-cloud simulation.

All values are simulation defaults and can be overridden with
environment variables (used by docker-compose).

P04 changes (P03-approved):
  - per-device key registry replaces the single shared PSK (F-06)
  - cloud ML-KEM public-key fingerprint pin (F-01)
  - device state directory and cloud key file (F-05/F-07)

Configuration policy (F-10 decision): the defaults in THIS file are
authoritative for default values; docker-compose.yml may override
them per deployment and MUST use the same environment variable names.
"""
import json
import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw)


# --- Hosts and ports -------------------------------------------------------

# Device -> Gateway
DEVICE_GATEWAY_HOST = _env("GATEWAY_HOST", "127.0.0.1")
DEVICE_GATEWAY_PORT = _env_int("GATEWAY_PORT", 5001)

# Gateway's listener for devices
GATEWAY_LISTEN_HOST = _env("GATEWAY_LISTEN_HOST", "0.0.0.0")
GATEWAY_LISTEN_PORT = _env_int("GATEWAY_LISTEN_PORT", 5001)

# Gateway -> Cloud
GATEWAY_CLOUD_HOST = _env("CLOUD_HOST", "127.0.0.1")
GATEWAY_CLOUD_PORT = _env_int("CLOUD_PORT", 5002)

# Cloud's listener for gateways
CLOUD_LISTEN_HOST = _env("CLOUD_LISTEN_HOST", "0.0.0.0")
CLOUD_LISTEN_PORT = _env_int("CLOUD_LISTEN_PORT", 5002)

# Health endpoints
GATEWAY_HEALTH_PORT = _env_int("GATEWAY_HEALTH_PORT", 8001)
CLOUD_HEALTH_PORT = _env_int("CLOUD_HEALTH_PORT", 8002)

# Reading generation interval (seconds)
DEVICE_INTERVAL_SECONDS = _env_int("DEVICE_INTERVAL_SECONDS", 5)


# --- Device/gateway credential registry (F-06, P08 BF-01/BF-03A) -------------
#
# The registry SIMULATES provisioning: each device/gateway id maps to
# its own 32-byte ChaCha20-Poly1305 key. It is NOT a production
# provisioning system.
#
# P08 BF-03A: credential secrets are NO LONGER embedded in this Python
# source. They are read from configuration (environment or a JSON
# file). The committed `demo_*_keys.json` files contain DEMO-ONLY
# material so the educational local run works out of the box; a real
# deployment must supply its own keys via DEVICE_KEYS_FILE /
# DEVICE_KEYS_JSON / GATEWAY_KEYS_FILE / GATEWAY_KEYS_JSON and must
# NOT commit real secrets.

_DEMO_DEVICE_KEYS_FILE = Path(__file__).with_name("demo_device_keys.json")
_DEMO_GATEWAY_KEYS_FILE = Path(__file__).with_name("demo_gateway_keys.json")


def _load_keys_json(raw_json: str, source_name: str) -> dict:
    """Parse a key-id -> hex-key JSON document into bytes."""
    registry = {}
    for key_id, key_hex in json.loads(raw_json).items():
        key = bytes.fromhex(key_hex)
        if len(key) != 32:
            raise ValueError(
                f"key for '{key_id}' in {source_name} is not 32 bytes")
        registry[key_id] = key
    return registry


def _keys_from_env_or_file(inline_env: str, file_env: str,
                           demo_path: Path) -> dict:
    """Resolve a key registry from inline env, a file env, or the demo file."""
    inline = os.environ.get(inline_env)
    if inline is not None:
        return _load_keys_json(inline, inline_env)
    file_value = os.environ.get(file_env)
    if file_value is not None:
        return _load_keys_json(
            Path(file_value).read_text(encoding="utf-8"), file_env)
    return _load_keys_json(demo_path.read_text(encoding="utf-8"), demo_path.name)


def device_keys() -> dict:
    """Return the device-id -> key-bytes registry (F-06, P08 BF-03A)."""
    return _keys_from_env_or_file(
        "DEVICE_KEYS_JSON", "DEVICE_KEYS_FILE", _DEMO_DEVICE_KEYS_FILE)


def device_key(device_id: str) -> bytes:
    """Return one device's key. Raises KeyError for unknown devices -
    the gateway uses this to reject unknown device ids (F-06)."""
    return device_keys()[device_id]


def gateway_keys() -> dict:
    """Return the gateway-id -> key-bytes registry (P08 BF-01)."""
    return _keys_from_env_or_file(
        "GATEWAY_KEYS_JSON", "GATEWAY_KEYS_FILE", _DEMO_GATEWAY_KEYS_FILE)


def gateway_key(gateway_id: str) -> bytes:
    """Return one gateway's key. Raises KeyError for unknown gateways -
    the cloud uses this to reject unknown gateway ids (P08 BF-01)."""
    return gateway_keys()[gateway_id]


def local_device_key() -> bytes:
    """The key of the simulated device running this process (P08 BF-03A).

    Override with DEVICE_KEY_HEX. Defaults to the demo key matching the
    default device id "dev-01".
    """
    raw = os.environ.get("DEVICE_KEY_HEX")
    if raw is not None:
        return bytes.fromhex(raw)
    return device_keys()["dev-01"]


def local_gateway_key() -> bytes:
    """The key of the simulated gateway running this process (P08 BF-01).

    Override with GATEWAY_KEY_HEX. Defaults to the demo key matching the
    default gateway id "gw-01".
    """
    raw = os.environ.get("GATEWAY_KEY_HEX")
    if raw is not None:
        return bytes.fromhex(raw)
    return gateway_keys()["gw-01"]


# --- Cloud ML-KEM public key pin (F-01) -------------------------------------

def cloud_public_key_sha256() -> str:
    """The provisioned SHA-256 fingerprint of the cloud's ML-KEM
    public key (the trust anchor). Empty means 'not configured' and
    the gateway FAILS CLOSED.

    Pinning protects against substitution only when this value is
    provisioned through a trusted mechanism (P04 section 12).
    """
    return _env("CLOUD_PUBLIC_KEY_SHA256", "")


# --- State persistence (F-05 / F-07) ----------------------------------------

# Cloud's persisted ML-KEM keypair (keeps the pinned fingerprint
# stable across cloud restarts).
CLOUD_KEY_FILE = _env("CLOUD_KEY_FILE", "cloud_state/cloud.key")

# Device's persisted sequence counter (survives device restarts).
DEVICE_STATE_DIR = _env("DEVICE_STATE_DIR", "device_state")
