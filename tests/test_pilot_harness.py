"""A failed cold backup must never trigger destructive lab-volume cleanup."""
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('module_name', ['acceptance', 'endurance'])
def test_preservation_failure_retains_only_current_state(monkeypatch, tmp_path, module_name):
    directory = Path(__file__).resolve().parents[1] / 'scripts/phase_d'
    monkeypatch.syspath_prepend(str(directory))
    module = importlib.import_module(module_name)
    removed = []
    class FailedLab:
        def __init__(self, root, cli):
            self.root = root
            self.project = 'pqc-d-test'
        def initialize(self):
            raise OSError('injected initialization fault')
        def compose(self, *args, **kwargs):
            if args[0] != 'stop':
                raise RuntimeError('no worker in this fixture')
        def backup(self, vault):
            raise OSError('injected unavailable checkpoint storage')
        def cleanup(self):
            removed.append(True)
            raise AssertionError('must not delete the only state copy')
    monkeypatch.setattr(module, 'Pilot', FailedLab)
    monkeypatch.setattr(module, 'create', lambda path: path)
    result = module.execute(tmp_path / 'run', 'unused')
    assert result['status'] == 'failed'
    assert removed == []
    cleanup = result['cleanup'][0] if isinstance(result['cleanup'], list) else result['cleanup']
    assert cleanup['retained'] is True
    assert cleanup['verified'] is False


@pytest.mark.parametrize('duration,elapsed,expected', [
    (1800, 1799, 'failed'),
    (1800, 1800, 'failed'),
    (35, 35, 'diagnostic_passed'),
])
def test_endurance_cannot_promote_partial_or_rotation_free_evidence(
        monkeypatch, tmp_path, duration, elapsed, expected):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts/phase_d'))
    module = importlib.import_module('endurance')
    class Lab:
        def __init__(self, root, cli):
            self.root = root
            self.release = {'source_sha256': {}}
        def initialize(self):
            return {'scope': 'test fixture'}
        def start(self):
            pass
        def compose(self, *args):
            return SimpleNamespace(stdout='')
        def backup(self, vault):
            return {'verified': True}
        def cleanup(self):
            return {'verified': True}
    monkeypatch.setattr(module, 'Pilot', Lab)
    monkeypatch.setattr(module, 'create', lambda path: path)
    monkeypatch.setattr(module, 'ROLES', ())
    monkeypatch.setattr(module, 'wait', lambda *args, **kwargs: None)
    monkeypatch.setattr(module, 'launch_load', lambda *args: None)
    monkeypatch.setattr(module, 'sample', lambda *args: {'docker': []})
    monkeypatch.setattr(module, 'reconcile', lambda *args: {'verified': True})
    monkeypatch.setattr(module.time, 'monotonic', lambda: 0)
    monkeypatch.setattr(module, 'worker_result', lambda *args: {
        'status': 'passed', 'elapsed_seconds': elapsed, 'sent': int(duration // 5),
        'missed_schedule': 0, 'latencies_seconds': [.5] * 100})
    result = module.execute(tmp_path / 'run', 'unused', duration)
    assert result['status'] == expected
    assert result['cleanup']['verified']
    if elapsed == duration == 1800:
        assert result['error']['message'] == 'missing in-run credential rotations'
