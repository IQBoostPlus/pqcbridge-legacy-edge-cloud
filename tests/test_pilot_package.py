"""Exported package works outside the original checkout and rejects drift."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


def controller():
    path = Path(__file__).resolve().parents[1] / 'scripts/phase_d/package.py'
    spec = importlib.util.spec_from_file_location('pilot_package_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_exported_controller_has_no_original_checkout_dependency(tmp_path):
    module = controller()
    root = module.create(tmp_path / 'bundle')
    run = subprocess.run([sys.executable, str(root / 'package.observed.py'), '--help'],
                         cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    assert 'restore' in run.stdout and 'backup' in run.stdout
    assert not (root / 'source/scripts/phase_b').exists()
    assert not (root / 'source/.env').exists()
    compose = json.loads((root / 'compose.json').read_text())
    assert compose['networks']['default']['internal'] is True
    for service in compose['services'].values():
        assert 'ports' not in service and service['read_only'] is True
        assert service['cap_drop'] == ['ALL']


def test_controller_refuses_source_or_deployment_drift(tmp_path):
    module = controller(); root = module.create(tmp_path / 'bundle')
    module.Pilot(root, cli='unused')
    path = root / 'source/common/crypto.py'
    path.write_bytes(path.read_bytes() + b'\n# unexpected\n')
    with pytest.raises(ValueError, match='source drift'):
        module.Pilot(root, cli='unused')


def test_initialization_cannot_reuse_or_build_inside_checkout(tmp_path):
    module = controller()
    with pytest.raises(ValueError):
        module.create(tmp_path)
    with pytest.raises(ValueError):
        module.create(Path(__file__).resolve().parents[1] / 'tmp/disallowed-package')
