"""Public CLI safety: no Docker or state activity for protected destinations."""
import subprocess
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).with_name('docker_probe.py')
REPO = PROBE.resolve().parents[2]


class DockerCLIContract(unittest.TestCase):
    def test_checkout_runtime_is_rejected(self):
        target = REPO / 'cloud_state' / 'docker-contract-must-not-exist'
        result = subprocess.run([sys.executable, str(PROBE), '--runtime-root',
                                 str(target)], capture_output=True, text=True,
                                timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('runtime must be outside the repository', result.stderr)
        self.assertFalse(target.exists())

    def test_existing_external_runtime_is_rejected_without_changing_sentinel(self):
        with tempfile.TemporaryDirectory(prefix='pqc-docker-contract-') as name:
            runtime = Path(name)
            sentinel = runtime / 'sentinel'
            sentinel.write_bytes(b'preserve-existing-runtime')
            result = subprocess.run([sys.executable, str(PROBE), '--runtime-root',
                                     str(runtime)], capture_output=True, text=True,
                                    timeout=10)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('runtime already exists', result.stderr)
            self.assertEqual(sentinel.read_bytes(), b'preserve-existing-runtime')

    def test_plan_uses_private_network_fresh_keys_and_no_original_state(self):
        with tempfile.TemporaryDirectory(prefix='pqc-docker-contract-') as name:
            runtime = Path(name) / 'run'
            result = subprocess.run([sys.executable, str(PROBE), '--runtime-root',
                                     str(runtime), '--plan-only'],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            import json
            compose = json.loads((runtime / 'compose.json').read_text())
            self.assertTrue(compose['networks']['default']['internal'])
            for service in compose['services'].values():
                self.assertNotIn('ports', service)
                self.assertNotIn('network_mode', service)
                self.assertEqual(service['labels']['pqc.phase_a.owner'],
                                 compose['name'])
            self.assertFalse((runtime / 'source' / '.env').exists())
            self.assertFalse((runtime / 'source' / 'cloud_state').exists())
            self.assertFalse((runtime / 'source' / 'device_state').exists())
            source = (runtime / 'source' / 'device' / 'device.py').read_bytes()
            self.assertEqual(source, (REPO / 'device' / 'device.py').read_bytes())
            secret_env = compose['services']['device']['environment']
            self.assertEqual(len(secret_env['DEVICE_KEY_HEX']), 64)
            self.assertNotEqual(secret_env['DEVICE_KEY_HEX'], 'a1a2a3a4a5a6a7a8b1b2b3b4b5b6b7b8c1c2c3c4c5c6c7c8d1d2d3d4d5d6d7d8')

    @unittest.skipUnless(os.name == 'nt', 'Windows Docker CLI shim')
    def test_remote_context_is_rejected_before_any_docker_mutation(self):
        with tempfile.TemporaryDirectory(prefix='pqc-docker-contract-') as name:
            root = Path(name)
            fake = root / 'fake.py'
            fake.write_text('''import json,sys
from pathlib import Path
args=sys.argv[1:]
with (Path(__file__).parent/'calls.jsonl').open('a') as log:
    log.write(json.dumps(args)+'\\n')
if args[2:]==['context','inspect','desktop-linux']:
    print(json.dumps([{'Endpoints':{'docker':{'Host':'tcp://unowned.example:2375'}}}]))
else:
    raise SystemExit(99)
''', encoding='utf-8')
            (root / 'docker.cmd').write_text('@"' + sys.executable + '" "' +
                                             str(fake) + '" %*\n')
            env = dict(os.environ)
            env['PATH'] = str(root) + os.pathsep + env['PATH']
            runtime = root / 'run'
            result = subprocess.run([sys.executable, str(PROBE), '--runtime-root',
                                     str(runtime), '--docker-cli', str(root / 'docker.cmd')], env=env, capture_output=True,
                                    text=True, timeout=15)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            import json
            report = json.loads((runtime / 'result.json').read_text())
            self.assertFalse(report['deployment_accepted'])
            self.assertIn('refusing non-local Docker endpoint', report['error'])
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            self.assertEqual(calls, [['--context', 'desktop-linux', 'context', 'inspect', 'desktop-linux']])

    @unittest.skipUnless(os.name == 'nt', 'Windows Docker CLI shim')
    def test_cleanup_refuses_object_without_run_ownership(self):
        with tempfile.TemporaryDirectory(prefix='pqc-docker-contract-') as name:
            root = Path(name)
            fake = root / 'fake.py'
            fake.write_text('''import json,sys
from pathlib import Path
args=sys.argv[3:]
with (Path(__file__).parent/'calls.jsonl').open('a') as log:
    log.write(json.dumps(args)+'\\n')
if args[:2]==['context','inspect']:
    print(json.dumps([{'Endpoints':{'docker':{'Host':'npipe:////./pipe/test-only'}}}]))
elif args[0]=='version':
    print(json.dumps({'Server':{'Version':'fake-control-only'}}))
elif args[:2]==['container','inspect']:
    print(json.dumps([{'Config':{'Labels':{'unrelated':'preserve'}}}]))
elif args[:2]==['ps','-aq']:
    print('unowned-control-object')
elif args[0]=='compose':
    if 'up' in args:
        raise SystemExit(23)
    if 'down' in args:
        raise SystemExit('UNSAFE CLEANUP ATTEMPT')
else:
    raise SystemExit(99)
''', encoding='utf-8')
            (root / 'docker.cmd').write_text('@"' + sys.executable + '" "' +
                                             str(fake) + '" %*\n')
            env = dict(os.environ)
            env['PATH'] = str(root) + os.pathsep + env['PATH']
            runtime = root / 'run'
            result = subprocess.run([sys.executable, str(PROBE), '--runtime-root',
                                     str(runtime), '--docker-cli', str(root / 'docker.cmd')], env=env, capture_output=True,
                                    text=True, timeout=15)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            import json
            report = json.loads((runtime / 'result.json').read_text())
            self.assertFalse(report['deployment_accepted'])
            self.assertIn('ownership label mismatch', report['cleanup']['error'])
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            self.assertFalse(any('down' in call for call in calls))

    @unittest.skipUnless(os.name == 'nt', 'Windows executable resolution')
    def test_windows_native_cli_wins_over_docker_posix_shell_script(self):
        from docker_probe import resolve_docker_cli
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='pqc-docker-resolver-') as name:
            root = Path(name)
            (root / 'docker').write_text('#!/usr/bin/env sh\nexit 99\n')
            executable = root / 'docker.exe'
            executable.write_bytes(b'MZsynthetic-resolution-only')
            with patch.dict(os.environ, {'PATH': str(root)}):
                self.assertEqual(Path(resolve_docker_cli()), executable)


if __name__ == '__main__':
    unittest.main()
