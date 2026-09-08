"""Fail-first tests for P08 BF-03A: device/gateway credentials must
not be hard-coded in Python source.

Baseline defect (reproduced in P08): the per-device keys (and the
device's own key) were embedded directly in `common/config.py`. Any
reader of the source tree obtained every simulated credential, enabling
device impersonation (BF-03A -> attack chain 3).

Expected behavior after P08: credentials are loaded from configuration
(environment or a JSON file). The committed `demo_*_keys.json` files
contain only clearly-labelled demo material for the local run; real
secret files are excluded by `.gitignore`.
"""
from pathlib import Path

import pytest

from common import config


def test_config_source_has_no_embedded_device_key_secrets():
    source = (Path(config.__file__).parent / "config.py").read_text(
        encoding="utf-8")
    for secret in ("a1a2a3a4a5a6a7a8", "e1e2e3e4e5e6e7e8"):
        assert secret not in source


def test_demo_device_keys_loads_known_devices():
    keys = config.device_keys()
    assert set(keys) == {"dev-01", "dev-02"}
    assert all(len(key) == 32 for key in keys.values())


def test_demo_gateway_keys_loads_known_gateway():
    keys = config.gateway_keys()
    assert set(keys) == {"gw-01"}
    assert len(keys["gw-01"]) == 32


def test_local_gateway_key_matches_registry():
    assert config.local_gateway_key() == config.gateway_keys()["gw-01"]


def test_device_keys_file_override(monkeypatch, tmp_path):
    keys_file = tmp_path / "device_keys.json"
    keys_file.write_text('{"dev-x": "' + "ab" * 32 + '"}', encoding="utf-8")
    monkeypatch.setenv("DEVICE_KEYS_FILE", str(keys_file))
    assert config.device_key("dev-x") == bytes.fromhex("ab" * 32)


def test_gateway_keys_file_override(monkeypatch, tmp_path):
    keys_file = tmp_path / "gateway_keys.json"
    keys_file.write_text('{"gw-x": "' + "cd" * 32 + '"}', encoding="utf-8")
    monkeypatch.setenv("GATEWAY_KEYS_FILE", str(keys_file))
    assert config.gateway_key("gw-x") == bytes.fromhex("cd" * 32)


def test_demo_files_are_not_ignored_by_gitignore():
    gitignore = (Path(config.__file__).parent.parent / ".gitignore").read_text(
        encoding="utf-8")
    assert "demo_device_keys.json" not in gitignore
    assert "demo_gateway_keys.json" not in gitignore
