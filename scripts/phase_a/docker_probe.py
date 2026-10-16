"""Bounded isolated Docker simulation. Never runs the checkout's Compose file."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from baseline import source_snapshot, write_json

REPO = Path(__file__).resolve().parents[2]
OWNER_LABEL = 'pqc.phase_a.owner'

# Instrument serialization only: the real device's run loop, encryption, sequence
# persistence and network code remain unchanged. Print exact synthetic plaintext
# before encryption so cloud readback can be compared without rounding ambiguity.
DEVICE_COMMAND = '''import json
from device import device, sensor
original = sensor.reading_to_bytes
def record(reading):
    print('PHASE_A_READING=' + json.dumps(reading, sort_keys=True), flush=True)
    return original(reading)
sensor.reading_to_bytes = record
device.main(['--device-id','dev-docker','--interval','1'])
'''


def prepare(runtime):
    runtime.mkdir(parents=True)
    source_snapshot(runtime / 'source')
    # These are the only credentials supplied to this separate deployment.
    device_key, gateway_key = secrets.token_hex(32), secrets.token_hex(32)
    project = 'pqc-a-' + secrets.token_hex(8)
    labels = {OWNER_LABEL: project}
    services = {}
    for role in ('cloud', 'gateway', 'device'):
        services[role] = {
            'build': {'context': './source', 'dockerfile': 'Dockerfile.' + role},
            'image': project + '-' + role + ':phase-a',
            'labels': labels, 'environment': {'PYTHONUNBUFFERED': '1'}}
    services['cloud']['environment'].update({
        'CLOUD_LISTEN_HOST': '0.0.0.0', 'CLOUD_KEY_FILE': '/app/cloud_state/cloud.key',
        'GATEWAY_KEYS_JSON': json.dumps({'gw-docker': gateway_key})})
    services['cloud']['volumes'] = ['cloud_state:/app/cloud_state']
    services['gateway']['environment'].update({
        'GATEWAY_LISTEN_HOST': '0.0.0.0', 'CLOUD_HOST': 'cloud',
        'CLOUD_PUBLIC_KEY_SHA256': '', 'GATEWAY_KEY_HEX': gateway_key,
        'DEVICE_KEYS_JSON': json.dumps({'dev-docker': device_key})})
    services['gateway']['command'] = ['python', '-m', 'gateway.gateway',
                                     '--gateway-id', 'gw-docker']
    services['device']['environment'].update({
        'GATEWAY_HOST': 'gateway', 'DEVICE_KEY_HEX': device_key,
        'DEVICE_STATE_DIR': '/app/device_state'})
    services['device']['volumes'] = ['device_state:/app/device_state']
    services['device']['command'] = ['python', '-u', '-c', DEVICE_COMMAND]
    compose = {'name': project, 'services': services,
               'networks': {'default': {'internal': True, 'labels': labels}},
               'volumes': {name: {'labels': labels}
                           for name in ('cloud_state', 'device_state')}}
    write_json(runtime / 'compose.json', compose)
    (runtime / 'empty.env').write_text('', encoding='utf-8')
    return compose


def hash_sources():
    paths = []
    for name in ('common', 'cloud', 'gateway', 'device'):
        paths.extend(p for p in (REPO / name).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in REPO.glob('Dockerfile.*'))
    paths.extend(p for name in ('requirements.txt', '.env', 'docker-compose.yml')
                 if (p := REPO / name).is_file())
    for name in ('cloud_state', 'device_state'):
        paths.extend(p for p in (REPO / name).rglob('*') if p.is_file())
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def resolve_docker_cli(explicit=None):
    """Windows installs include a POSIX `docker` shim beside native docker.exe."""
    candidate = (str(Path(explicit).resolve()) if explicit else
                 shutil.which('docker.exe' if os.name == 'nt' else 'docker'))
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('Docker CLI not installed or explicit path is not a file')
    return candidate


class DockerRun:
    def __init__(self, runtime, compose, docker_cli=None):
        self.runtime, self.compose = runtime, compose
        self.counter = 0
        self.cli = resolve_docker_cli(docker_cli)
        self.env = dict(os.environ)
        # Explicit local context and fresh project config override host defaults.
        for name in list(self.env):
            if name.upper().startswith(('DOCKER_', 'COMPOSE_')):
                del self.env[name]
        self.base = [self.cli, '--context', 'desktop-linux']
        self.prefix = ['compose', '--project-name', compose['name'],
                       '--project-directory', str(runtime), '--env-file',
                       str(runtime / 'empty.env'), '-f', str(runtime / 'compose.json')]

    def command(self, *arguments, timeout=30, check=True):
        self.counter += 1
        result = subprocess.run(self.base + list(arguments), cwd=self.runtime,
                                env=self.env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        # Configuration/inspect output may contain test credentials: raw only.
        write_json(self.runtime / ('command-%03d.json' % self.counter), {
            'arguments': list(arguments), 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr})
        if check and result.returncode:
            raise RuntimeError('Docker command failed; see command-%03d.json' % self.counter)
        return result

    def call(self, *arguments, **kwargs):
        return self.command(*(self.prefix + list(arguments)), **kwargs)

    def health(self, role, port, route='/health'):
        code = ('import json,urllib.request; print(json.dumps(json.load('
                'urllib.request.urlopen("http://127.0.0.1:%d%s",timeout=2))))'
                % (port, route))
        return json.loads(self.call('exec', '-T', role, 'python', '-c', code).stdout)

    def wait_for(self, predicate, timeout=40):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                value = predicate()
                if value:
                    return value
            except (RuntimeError, ValueError):
                pass
            time.sleep(0.5)
        raise TimeoutError('bounded container readiness/readback expired')

    def cleanup(self):
        # A unique name alone is insufficient: refuse deletion if any matching
        # object lacks this run's independent ownership label.
        project = self.compose['name']
        selected = []
        for kind, listargs in (
                ('container', ['ps', '-aq']),
                ('network', ['network', 'ls', '-q']),
                ('volume', ['volume', 'ls', '-q'])):
            ids = self.command(*listargs, '--filter',
                               'label=com.docker.compose.project=' + project).stdout.split()
            for object_id in ids:
                obj = json.loads(self.command(kind, 'inspect', object_id).stdout)[0]
                labels = (obj.get('Config', {}).get('Labels', {}) if kind == 'container'
                          else obj.get('Labels', {})) or {}
                if labels.get(OWNER_LABEL) != project:
                    raise RuntimeError('cleanup refused: ownership label mismatch')
                selected.append({'kind': kind, 'id': object_id})
        self.call('down', '--volumes', '--timeout', '5', timeout=45)
        remaining = {}
        for kind, args in (('containers', ['ps', '-aq']),
                           ('networks', ['network', 'ls', '-q']),
                           ('volumes', ['volume', 'ls', '-q'])):
            remaining[kind] = self.command(*args, '--filter',
                'label=com.docker.compose.project=' + project).stdout.split()
        if any(remaining.values()):
            raise RuntimeError('owned resources remain after cleanup')
        return {'status': 'passed', 'owned_resources_removed': selected,
                'remaining': remaining, 'images': 'retained under unique run tags'}


def execute(runtime, compose, docker_cli=None):
    before = hash_sources()
    result = {'status': 'blocked', 'deployment_accepted': False,
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'project': compose['name'], 'runtime_root': str(runtime),
              'hybrid_tls': 'not run; application remains original custom transport'}
    docker = None
    created = False
    try:
        docker = DockerRun(runtime, compose, docker_cli)
        result['docker_cli'] = docker.cli
        # Never target a remote Docker service even if local context was changed.
        context = json.loads(docker.command('context', 'inspect', 'desktop-linux').stdout)[0]
        host = context['Endpoints']['docker']['Host']
        if not (host.startswith('npipe://') or host.startswith('unix://')):
            raise RuntimeError('refusing non-local Docker endpoint')
        version = docker.command('version', '--format', '{{json .}}', check=False)
        result['docker_version'] = json.loads(version.stdout)
        if version.returncode or not result['docker_version'].get('Server'):
            result['blocker'] = version.stderr.strip()
            return result
        docker.call('config', '--quiet')
        docker.call('build', timeout=240)
        created = True  # up may create resources before returning a failure.
        docker.call('up', '-d', 'cloud', timeout=45)
        docker.wait_for(lambda: docker.health('cloud', 8002))
        pin = docker.call('exec', '-T', 'cloud', 'python', '-c',
            'from pathlib import Path; from common import crypto; '
            'key=crypto.load_mlkem_private_key(Path("/app/cloud_state/cloud.key")); '
            'print(crypto.public_key_fingerprint(crypto.public_key_bytes(key.public_key())))').stdout.strip()
        if len(pin) != 64 or any(ch not in '0123456789abcdef' for ch in pin):
            raise RuntimeError('invalid synthetic cloud fingerprint')
        compose['services']['gateway']['environment']['CLOUD_PUBLIC_KEY_SHA256'] = pin
        write_json(runtime / 'compose.json', compose)
        docker.call('up', '-d', 'gateway', timeout=45)
        docker.wait_for(lambda: docker.health('gateway', 8001).get('cloud_connected'))
        # Health startup precedes listener startup; only probe owned internal port.
        docker.wait_for(lambda: docker.call('exec', '-T', 'gateway', 'python', '-c',
            'import socket; socket.create_connection(("127.0.0.1",5001),timeout=1).close()',
            check=False).returncode == 0)
        docker.call('up', '-d', 'device', timeout=45)
        readings = docker.wait_for(lambda: (
            value if len(value := docker.health('cloud', 8002, '/readings')) >= 3 else None))
        docker.call('stop', '--timeout', '3', 'device')
        device_log = docker.call('logs', '--no-log-prefix', 'device').stdout
        expected = [json.loads(line.split('PHASE_A_READING=', 1)[1])
                    for line in device_log.splitlines() if 'PHASE_A_READING=' in line]
        received = {r['sequence']: r for r in readings}
        if len(expected) < 3 or any(received.get(r['sequence']) != r for r in expected[:3]):
            raise RuntimeError('cloud readback does not match exact first three source readings')
        result['smoke'] = {'status': 'passed', 'exact_readings': expected[:3],
                           'cloud_reading_count': len(readings),
                           'instrumentation': 'device serialization observer; unchanged source bytes'}
        versions = {}
        version_code = ('import json,platform,ssl,cryptography; '
            'from cryptography.hazmat.backends.openssl.backend import backend; '
            'print(json.dumps({"os":platform.platform(),"python":platform.python_version(),'
            '"cryptography":cryptography.__version__,"python_ssl":ssl.OPENSSL_VERSION,'
            '"cryptography_openssl":backend.openssl_version_text()}))')
        for role in ('cloud', 'gateway', 'device'):
            if role == 'device':
                # Stopped device: inspect runtime using the same immutable image.
                output = docker.call('run', '--rm', '--no-deps', role, 'python', '-c', version_code)
            else:
                output = docker.call('exec', '-T', role, 'python', '-c', version_code)
            versions[role] = json.loads(output.stdout)
            tag = compose['services'][role]['image']
            image = json.loads(docker.command('image', 'inspect', tag).stdout)[0]
            versions[role]['image_id'] = image['Id']
            versions[role]['repo_digests'] = image.get('RepoDigests', [])
        result.update(status='passed', deployment_accepted=True, runtimes=versions)
    except (RuntimeError, TimeoutError, subprocess.TimeoutExpired, ValueError, OSError) as exc:
        result.update(status='blocked' if not created else 'failed', error=str(exc))
    finally:
        if created and docker:
            try:
                docker.call('logs', '--no-color', check=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                result['log_capture_error'] = str(exc)
            try:
                result['cleanup'] = docker.cleanup()
            except Exception as exc:
                result.update(status='failed', deployment_accepted=False,
                              cleanup={'status': 'failed', 'error': str(exc)})
        else:
            result['cleanup'] = {'status': 'no resources created'}
        after = hash_sources()
        result['preservation'] = {'tracked_inputs': len(before),
                                  'changed': [p for p in before if after.get(p) != before[p]],
                                  'added': sorted(set(after) - set(before))}
        if result['preservation']['changed']:
            result.update(status='failed', deployment_accepted=False)
        result['completed_utc'] = datetime.now(timezone.utc).isoformat()
        result['probe_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write_json(runtime / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--plan-only', action='store_true',
                        help='create isolated source/config; do not contact Docker')
    parser.add_argument('--docker-cli', type=Path,
                        help='explicit Docker executable (also used by isolated control tests)')
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    if runtime.is_relative_to(REPO):
        parser.error('runtime must be outside the repository')
    if runtime.exists():
        parser.error('runtime already exists')
    compose = prepare(runtime)
    if args.plan_only:
        write_json(runtime / 'result.json', {'status': 'plan-only',
                   'deployment_accepted': False, 'project': compose['name']})
        return 0
    result = execute(runtime, compose, args.docker_cli)
    print(json.dumps({'status': result['status'], 'result': str(runtime / 'result.json')}))
    return 0 if result['deployment_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
