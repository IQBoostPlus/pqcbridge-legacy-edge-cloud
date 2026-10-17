"""Contracts for the isolated Phase B deployment harness (no Docker by default)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IsolatedDeploymentContract(unittest.TestCase):
    def load(self):
        spec = importlib.util.spec_from_file_location(
            'phase_b_probe', ROOT / 'scripts/phase_b/docker_probe.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_checkout_runtime_is_refused(self):
        module = self.load()
        with self.assertRaises(ValueError):
            module.validate_runtime(ROOT / 'unsafe-runtime')

    def test_existing_runtime_is_refused(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                module.validate_runtime(Path(folder))

    def test_fresh_external_runtime_is_permitted(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder:
            module.validate_runtime(Path(folder) / 'new')

    def test_copy_excludes_secrets_and_state(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'source'
            module.copy_source(target)
            self.assertTrue((target / 'common/crypto.py').is_file())
            for name in ('.env', '.git', 'cloud_state', 'device_state'):
                self.assertFalse((target / name).exists())

    def test_preparation_failure_before_creation_needs_no_docker_cleanup(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder:
            lab = module.Lab(Path(folder), 'unused-docker')
            lab.local_endpoint_verified = True
            def refuse_unnecessary_command(*_args, **_kwargs):
                raise AssertionError('No Docker objects can exist before creation')
            lab.run = refuse_unnecessary_command
            result = lab.cleanup()
            self.assertTrue(result['verified'])
            self.assertEqual(result['removed'], [])


if __name__ == '__main__':
    unittest.main()
