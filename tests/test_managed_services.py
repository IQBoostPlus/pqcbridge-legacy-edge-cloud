"""Managed process entry must keep the pre-import TLS startup boundary."""
import os
from pathlib import Path
import subprocess
import sys


def test_managed_entry_refuses_uncontrolled_tls_before_loading_configuration():
    environment = dict(os.environ)
    environment.pop('OPENSSL_CONF', None)
    result = subprocess.run([sys.executable, '-B', '-m', 'common.managed_bootstrap',
                             'gateway', '--config', 'missing.json'],
                            cwd=Path(__file__).resolve().parents[1], env=environment,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 3
    assert 'TLS startup rejected' in result.stderr
    assert 'ManagedConfiguration' not in result.stderr
