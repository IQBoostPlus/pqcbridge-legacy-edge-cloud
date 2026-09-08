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


# --- Per-device key registry (F-06) -----------------------------------------
#
# The registry SIMULATES device provisioning: each device id maps to
# its own 32-byte ChaCha20-Poly1305 key. It is NOT a production
# provisioning system, and the keys below are demo-only values.
# Read dynamically so environment changes take effect at call time.

_DEFAULT_DEVICE_KEYS_JSON = json.dumps({
    "dev-01": "a1a2a3a4a5a6a7a8b1b2b3b4b5b6b7b8"
              "c1c2c3c4c5c6c7c8d1d2d3d4d5d6d7d8",
    "dev-02": "e1e2e3e4e5e6e7e8f1f2f3f4f5f6f7f8"
              "01020304050607081112131415161718",
})


def device_keys() -> dict:
    """Return the device-id -> key-bytes registry."""
    raw = _env("DEVICE_KEYS_JSON", _DEFAULT_DEVICE_KEYS_JSON)
    registry = {}
    for device_id, key_hex in json.loads(raw).items():
        key = bytes.fromhex(key_hex)
        if len(key) != 32:
            raise ValueError(f"device key for '{device_id}' is not 32 bytes")
        registry[device_id] = key
    return registry


def device_key(device_id: str) -> bytes:
    """Return one device's key. Raises KeyError for unknown devices -
    the gateway uses this to reject unknown device ids (F-06)."""
    return device_keys()[device_id]


# The simulated device's OWN key. In a real deployment this would come
# from secure provisioning, not a shared registry variable.
_DEVICE_KEY_HEX_DEFAULT = ("a1a2a3a4a5a6a7a8b1b2b3b4b5b6b7b8"
                           "c1c2c3c4c5c6c7c8d1d2d3d4d5d6d7d8")


def local_device_key() -> bytes:
    """The key of the simulated device running this process."""
    return bytes.fromhex(_env("DEVICE_KEY_HEX", _DEVICE_KEY_HEX_DEFAULT))


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
