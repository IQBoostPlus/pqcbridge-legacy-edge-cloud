"""Fail-first tests for F-06 (P04.5): per-device key registry.

Baseline behavior: one global PSK was shared by every device;
device_id was self-declared, so one compromised device could
impersonate any other.

The registry is a simulation of provisioning and is NOT a production
provisioning system (P03/P04 documented limitation).
"""
import pytest

from common import config


def test_registry_maps_known_devices():
    keys = config.device_keys()
    assert "dev-01" in keys and "dev-02" in keys
    assert all(len(key) == 32 for key in keys.values())


def test_default_device_key_matches_registry_entry():
    # the simulated device "dev-01" gets the key listed for it
    assert config.local_device_key() == config.device_keys()["dev-01"]


def test_unknown_device_rejected():
    with pytest.raises(KeyError):
        config.device_key("dev-999")


def test_registry_env_override(monkeypatch):
    monkeypatch.setenv("DEVICE_KEYS_JSON",
                       '{"dev-x": "' + "ab" * 32 + '"}')
    assert config.device_key("dev-x") == bytes.fromhex("ab" * 32)


def test_device_key_env_override(monkeypatch):
    monkeypatch.setenv("DEVICE_KEY_HEX", "cd" * 32)
    assert config.local_device_key() == bytes.fromhex("cd" * 32)
