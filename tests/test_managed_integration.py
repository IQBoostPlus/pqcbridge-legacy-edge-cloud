"""Deployment safety contracts; these do not establish Docker acceptance."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location('phase_c_probe', ROOT / 'scripts/phase_c/docker_probe.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_fresh_external_runtime_directories_are_admitted(tmp_path):
    module = load()
    for unsafe in (ROOT / 'tmp' / 'unsafe', tmp_path, Path('../relative-runtime')):
        with pytest.raises(ValueError):
            module.validate_runtime(unsafe)
    module.validate_runtime(tmp_path / 'fresh')


def test_frozen_source_excludes_checkout_secrets_state_and_generated_files(tmp_path):
    module = load()
    target = tmp_path / 'source'
    module.copy_source(target)
    assert (target / 'common/credentials.py').is_file()
    assert (target / 'common/management.py').is_file()
    for name in ('.env', '.git', 'cloud_state', 'device_state', 'tmp', 'docs'):
        assert not (target / name).exists()
    assert not list(target.rglob('*.pyc'))


def test_no_creation_needs_no_cleanup_command(tmp_path):
    module = load()
    lab = module.Lab(tmp_path, 'unused-docker')
    def forbid(*args, **kwargs):
        raise AssertionError('no Docker object was created')
    lab.run = forbid
    assert lab.cleanup()['verified'] is True
