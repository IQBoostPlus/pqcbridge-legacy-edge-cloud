"""Bounded launch of the pinned, already-local Linux TLS feasibility image."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import uuid

IMAGE = 'sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
DOCKER = r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'


def sanitize(value):
    """Retain transcript evidence while omitting synthetic public PEM bodies."""
    if isinstance(value, str):
        return re.sub(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',
                      '[synthetic public certificate PEM omitted; DER hash recorded]',
                      value, flags=re.DOTALL)
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def cleanup_container(run, name, token):
    """Attempt each bounded ownership/cleanup check even if another fails."""
    result = {'cleanup_verified': False, 'cleanup_errors': []}
    ids = []
    try:
        owned = run(['ps', '-a', '--filter', 'name=^/' + name + '$',
                     '--filter', 'label=pqc.phase_a.owner=' + token, '--format', '{{.ID}}'])
        if owned['exit_code']:
            raise RuntimeError('ownership query failed')
        ids = owned['stdout'].split()
    except Exception as exc:
        result['cleanup_errors'].append({'step': 'ownership', 'type': type(exc).__name__, 'error': str(exc)})
    if ids:
        try:
            removed = run(['rm', '-f', *ids])
            if removed['exit_code']:
                raise RuntimeError('owned container removal failed')
        except Exception as exc:
            result['cleanup_errors'].append({'step': 'remove', 'type': type(exc).__name__, 'error': str(exc)})
    try:
        remaining = run(['ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}'])
        result['cleanup_verified'] = remaining['exit_code'] == 0 and not remaining['stdout'].strip()
    except Exception as exc:
        result['cleanup_errors'].append({'step': 'verify', 'type': type(exc).__name__, 'error': str(exc)})
    return result


def main(artifact_parent=None, evidence_parent=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--minimal', action='store_true')
    args = parser.parse_args()
    checkout = Path(__file__).resolve().parents[2]
    token = uuid.uuid4().hex
    root = Path(artifact_parent or r'D:\Code\pqcbridge-phase-a-artifacts') / ('linux-tls-' + token)
    root.mkdir(exist_ok=False)
    name = 'pqc-linux-tls-' + token[:16]
    commands = []

    def run(arguments, *, data=None, timeout=20):
        try:
            result = subprocess.run([DOCKER, '--context', 'desktop-linux', *arguments],
                                    input=data, capture_output=True, timeout=timeout)
        except Exception as exc:
            commands.append({'arguments': arguments, 'exit_code': None,
                             'error': {'type': type(exc).__name__, 'message': str(exc)}})
            raise
        record = {'arguments': arguments, 'exit_code': result.returncode,
                  'stdout': result.stdout.decode(errors='replace'),
                  'stderr': result.stderr.decode(errors='replace')}
        commands.append(record)
        return record

    report = {'status': 'failed', 'runtime_root': str(root), 'container': name,
              'owner': token, 'image': IMAGE, 'commands': commands}
    host_source = Path(__file__).read_bytes()
    (root / 'linux_tls_host.observed.py').write_bytes(host_source)
    report['host_source_sha256'] = hashlib.sha256(host_source).hexdigest()
    exit_code = 1
    try:
        context = run(['context', 'inspect', 'desktop-linux'])
        endpoint = json.loads(context['stdout'])[0]['Endpoints']['docker']['Host']
        if not endpoint.startswith('npipe:////./pipe/'):
            raise RuntimeError('refusing non-local Docker endpoint')
        info = run(['info', '--format', '{{json .ServerVersion}}'])
        if info['exit_code']:
            raise RuntimeError('Docker server unavailable')
        inspection = run(['image', 'inspect', IMAGE, '--format', '{{.Id}}'])
        if inspection['exit_code'] or inspection['stdout'].strip() != IMAGE:
            raise RuntimeError('pinned local image missing or different')
        source = (checkout / 'scripts/phase_a/linux_tls_probe.py').read_bytes()
        (root / 'linux_tls_probe.observed.py').write_bytes(source)
        report['source_sha256'] = hashlib.sha256(source).hexdigest()
        invocation = ['run', '--rm', '--pull', 'never', '--name', name,
                      '--label', 'pqc.phase_a.owner=' + token,
                      '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,noexec,nosuid,size=33554432',
                      '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                      '--pids-limit', '64', '--memory', '256m', '--cpus', '1',
                      '--user', '65534:65534', '-i', IMAGE, 'python', '-I', '-']
        if args.minimal:
            invocation.append('--minimal')
        try:
            result = run(invocation, data=source, timeout=180)
        except subprocess.TimeoutExpired as exc:
            (root / 'timeout.stdout').write_bytes(exc.stdout or b'')
            (root / 'timeout.stderr').write_bytes(exc.stderr or b'')
            raise RuntimeError('bounded container execution timed out') from exc
        (root / 'container.stdout.json').write_text(result['stdout'], encoding='utf-8')
        (root / 'container.stderr.txt').write_text(result['stderr'], encoding='utf-8')
        report['probe'] = json.loads(result['stdout'])
        if result['exit_code'] or report['probe'].get('status') != 'passed':
            raise RuntimeError('probe assertions failed; inspect preserved result')
        report['status'] = 'passed'
        exit_code = 0
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        report.update(cleanup_container(run, name, token))
        if not report['cleanup_verified'] or report['cleanup_errors']:
            report['status'] = 'failed'
            exit_code = 1
        raw_report = json.dumps(report, indent=2).encode('utf-8')
        (root / 'host-result.json').write_bytes(raw_report)
        target = Path(evidence_parent or checkout / 'docs/phase-a/evidence/transport')
        target.mkdir(parents=True, exist_ok=True)
        suffix = 'minimal' if args.minimal else 'full'
        destination = target / ('linux-' + suffix + '-' + token[:12] + '.json')
        sanitized = sanitize(report)
        sanitized['raw_host_report_sha256'] = hashlib.sha256(raw_report).hexdigest()
        sanitized['sanitization'] = 'Public certificate PEM omitted; no private-key bytes emitted by probe'
        destination.write_text(json.dumps(sanitized, indent=2), encoding='utf-8')
        print(json.dumps({'status': report['status'], 'raw': str(root), 'evidence': str(destination),
                          'cleanup_verified': report['cleanup_verified'],
                          'error': report.get('error')}, indent=2))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
