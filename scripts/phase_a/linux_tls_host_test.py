"""A failed cleanup query must not suppress the durable failure report."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import linux_tls_host


class CleanupFailureTest(unittest.TestCase):
    def test_cleanup_timeout_still_persists_failure(self):
        calls = []

        def fake(command, **kwargs):
            args = command[3:]
            calls.append(args)
            if args[:2] == ['context', 'inspect']:
                out = json.dumps([{'Endpoints': {'docker': {'Host': 'npipe:////./pipe/test'}}}])
            elif args[0] == 'info':
                out = '"test-engine"'
            elif args[:2] == ['image', 'inspect']:
                out = linux_tls_host.IMAGE
            elif args[0] == 'run':
                out = json.dumps({'status': 'passed'})
            elif len([call for call in calls if call[0] == 'ps']) == 1:
                raise subprocess.TimeoutExpired(command, 20)
            else:
                out = ''
            return subprocess.CompletedProcess(command, 0, out.encode(), b'')

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(sys, 'argv', ['linux_tls_host.py']), \
                    patch.object(subprocess, 'run', side_effect=fake), \
                    contextlib.redirect_stdout(io.StringIO()):
                exit_code = linux_tls_host.main(root, root / 'evidence')
            report = json.loads(next((root / 'evidence').glob('*.json')).read_text())
            raw = json.loads((Path(report['runtime_root']) / 'host-result.json').read_text())
            self.assertEqual(exit_code, 1)
            self.assertEqual(report['status'], raw['status'])
            self.assertEqual(report['commands'], raw['commands'])
            self.assertEqual(report['status'], 'failed')
            self.assertEqual(report['cleanup_errors'][0]['type'], 'TimeoutExpired')
            self.assertEqual(len([call for call in calls if call[0] == 'ps']), 2)
            self.assertTrue((Path(report['runtime_root']) / 'linux_tls_host.observed.py').is_file())


if __name__ == '__main__':
    unittest.main()
