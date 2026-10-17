"""Public service entry points require the validated bootstrap process."""
import os
from pathlib import Path
import subprocess
import sys


def test_cloud_cannot_start_without_secure_bootstrap():
    env = dict(os.environ)
    env.pop('OPENSSL_CONF', None)
    result = subprocess.run([sys.executable, '-B', '-m', 'cloud.secure', '--config',
                             'missing-config.json'], cwd=Path(__file__).resolve().parents[1],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'secure bootstrap is required' in result.stderr.lower()
