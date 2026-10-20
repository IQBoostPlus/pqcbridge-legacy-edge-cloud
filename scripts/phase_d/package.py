"""Versioned, offline, synthetic-only Compose package and operator controller."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE / 'source' if (HERE / 'source/common').is_dir() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from common.pilot_ops import alerts, COHORT

BASE = 'sha256:b23cfa27684e7af4be489c0d3683e184c72e3440bc45a408bbcbd5762b42b0f4'
OWNER = 'pqc.phase_d.owner'
VERSION = 'pilot-lab-v1'
ROLES = ('cloud', 'gateway')


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding='utf-8')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protect_directory(root):
    if os.name == 'nt':
        result = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'],
                                capture_output=True, text=True, timeout=10, check=True)
        sid = next(csv.reader([result.stdout.strip()]))[1]
        if not re.fullmatch('S-1-[0-9-]+', sid):
            raise ValueError('Windows owner SID unavailable')
        subprocess.run(['icacls', str(root), '/inheritance:r', '/grant:r',
                        '*' + sid + ':(OI)(CI)F', '*S-1-5-18:(OI)(CI)F',
                        '*S-1-5-32-544:(OI)(CI)F'], capture_output=True, timeout=15, check=True)
    else:
        root.chmod(0o700)


def validate_root(root, fresh=False):
    if not root.is_absolute() or root.is_symlink():
        raise ValueError('absolute external root required')
    resolved = root.resolve()
    if resolved == REPO or REPO in resolved.parents or any(p.is_symlink() for p in root.parents):
        raise ValueError('checkout or symlink runtime refused')
    if fresh and root.exists():
        raise ValueError('new external directory required')
    return resolved


def create(root, revision=VERSION):
    if revision not in (VERSION, 'pilot-lab-v1.1'):
        raise ValueError('unsupported same-schema package revision')
    root = validate_root(root, fresh=True)
    root.mkdir(parents=True)
    protect_directory(root)
    for name in ('common', 'cloud', 'gateway', 'device'):
        target = root / 'source' / name
        target.mkdir(parents=True)
        for path in (REPO / name).iterdir():
            if path.is_file() and (path.suffix == '.py' or path.name in ('demo_device_keys.json', 'demo_gateway_keys.json')):
                if path.is_symlink():
                    raise ValueError('symlink source refused')
                shutil.copyfile(path, target / path.name)
    (root / 'source/deploy/phase_b').mkdir(parents=True)
    shutil.copyfile(REPO / 'deploy/phase_b/tls-policy.cnf', root / 'source/deploy/phase_b/tls-policy.cnf')
    (root / 'source/deploy/phase_d').mkdir(parents=True)
    shutil.copyfile(REPO / 'deploy/phase_d/Dockerfile', root / 'source/deploy/phase_d/Dockerfile')
    (root / 'source/scripts/phase_d').mkdir(parents=True)
    shutil.copyfile(REPO / 'scripts/phase_d/worker.py', root / 'source/scripts/phase_d/worker.py')
    shutil.copyfile(REPO / 'requirements.txt', root / 'source/requirements.txt')
    (root / 'empty.env').write_text('')
    project = 'pqc-d-' + secrets.token_hex(8)
    services = {}
    labels = {OWNER: project}
    for role in (*ROLES, 'admin'):
        svc = {'image': project + ':' + VERSION, 'labels': labels,
               'entrypoint': ['python'], 'environment': {'PYTHONUNBUFFERED': '1'},
               'read_only': True, 'tmpfs': ['/tmp:rw,noexec,nosuid,size=8388608'],
               'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges'],
               'pids_limit': 64, 'cpus': .5, 'mem_limit': '256m',
               'logging': {'driver': 'json-file', 'options': {'max-size': '8m', 'max-file': '2'}}}
        if role == 'admin':
            svc.update(profiles=['operator'], network_mode='none', volumes=[str(root) + ':/bundle:rw',
                'cloud_state:/bundle/states/cloud:rw', 'gateway_state:/bundle/states/gateway:rw'])
            svc['build'] = {'context': './source', 'dockerfile': 'deploy/phase_d/Dockerfile',
                            'network': 'none', 'args': {'BASE_IMAGE': project + '-base:locked', 'PACKAGE_VERSION': revision}}
        else:
            svc['command'] = ['-m', 'common.managed_bootstrap', role, '--config', '/run/pilot/config.json']
            svc['volumes'] = [role + '_state:/var/lib/pqc:rw',
                str(root / (role + '.json')) + ':/run/pilot/config.json:ro',
                str(root / (role + '-credentials')) + ':/run/pilot/credentials:ro',
                str(root / 'control') + ':/run/pilot/control:ro']
        services[role] = svc
    compose = {'name': project, 'services': services,
               'volumes': {role + '_state': {'labels': labels} for role in ROLES},
               'networks': {'default': {'internal': True, 'labels': labels}}}
    write(root / 'compose.json', compose)
    source_hashes = {p.relative_to(root / 'source').as_posix(): digest(p)
                     for p in sorted((root / 'source').rglob('*')) if p.is_file()}
    write(root / 'release.json', {'format': VERSION, 'package_revision': revision, 'scope': 'synthetic-only', 'project': project,
        'base_image': BASE, 'source_sha256': source_hashes, 'image': None,
        'compose_sha256': hashlib.sha256((root / 'compose.json').read_bytes()).hexdigest(),
        'dependencies': (REPO / 'requirements.txt').read_text(),
        'created_utc': datetime.now(timezone.utc).isoformat()})
    shutil.copyfile(Path(__file__), root / 'package.observed.py')
    return root


class Pilot:
    def __init__(self, root, cli=None):
        self.root = validate_root(root)
        self.release = json.loads((root / 'release.json').read_text())
        self.project = self.release['project']
        if not re.fullmatch(r'pqc-d-[0-9a-f]{16}', self.project) or self.release['scope'] != 'synthetic-only':
            raise ValueError('owned synthetic package required')
        self.cli = cli or shutil.which('docker')
        if not self.cli:
            raise ValueError('Docker CLI unavailable')
        self.env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('DOCKER_', 'COMPOSE_'))}
        self.prefix = ['compose', '--project-name', self.project, '--project-directory', str(root),
                       '--env-file', str(root / 'empty.env'), '-f', str(root / 'compose.json')]
        self.verify_source()
        if self.release.get('compose_sha256') != hashlib.sha256((root / 'compose.json').read_bytes()).hexdigest():
            raise ValueError('package deployment drift')

    def verify_source(self):
        actual = {p.relative_to(self.root / 'source').as_posix(): digest(p)
                  for p in sorted((self.root / 'source').rglob('*')) if p.is_file()}
        if actual != self.release['source_sha256']:
            raise ValueError('package source drift')

    def run(self, *args, timeout=30, check=True):
        if not getattr(self, '_local_verified', False):
            context = subprocess.run([self.cli, '--context', 'desktop-linux', 'context', 'inspect', 'desktop-linux'],
                                     capture_output=True, text=True, env=self.env, timeout=10, check=True)
            endpoint = json.loads(context.stdout)[0]['Endpoints']['docker']['Host']
            if not endpoint.startswith(('npipe://', 'unix://')):
                raise ValueError('remote Docker endpoint refused')
            self._local_verified = True
        p = subprocess.run([self.cli, '--context', 'desktop-linux', *args], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', cwd=self.root,
                           env=self.env, timeout=timeout)
        if check and p.returncode:
            # Raw Docker output can contain sensitive mount/config paths.
            (self.root / 'last-docker-error.txt').write_text(p.stderr, encoding='utf-8')
            raise RuntimeError('Docker operation failed; private error retained in runtime')
        return p

    def compose(self, *args, **kwargs):
        return self.run(*(self.prefix + list(args)), **kwargs)

    def admin(self, *args, timeout=45):
        p = self.compose('run', '--rm', '-T', '--no-deps', '--pull', 'never', 'admin', *args, timeout=timeout)
        return json.loads(p.stdout)

    def initialize(self, provision=True):
        endpoint = json.loads(self.run('context', 'inspect', 'desktop-linux').stdout)[0]['Endpoints']['docker']['Host']
        if not endpoint.startswith(('npipe://', 'unix://')):
            raise ValueError('remote Docker refused')
        base = self.release['base_image']
        if base != BASE or self.run('image', 'inspect', base, '--format', '{{.Id}}').stdout.strip() != base:
            raise ValueError('validated immutable local base required')
        self.run('tag', base, self.project + '-base:locked')
        self.compose('config', '--quiet')
        self.compose('build', '--pull=false', 'admin', timeout=150)
        image = self.run('image', 'inspect', self.project + ':' + VERSION, '--format', '{{.Id}}').stdout.strip()
        if not re.fullmatch('sha256:[0-9a-f]{64}', image):
            raise ValueError('immutable candidate image required')
        compose = json.loads((self.root / 'compose.json').read_text())
        for svc in compose['services'].values():
            svc['image'] = image
        write(self.root / 'compose.json', compose)
        self.release['image'] = image
        self.release['compose_sha256'] = hashlib.sha256((self.root / 'compose.json').read_bytes()).hexdigest()
        write(self.root / 'release.json', self.release)
        result = self.admin('-m', 'common.pilot_ops', 'provision', '--root', '/bundle', timeout=100) if provision else {}
        if provision:
            self.seal_trust()
        return {**result, 'image': image, 'project': self.project}

    def export_images(self):
        archive = self.root / 'images.tar'
        if archive.exists():
            raise ValueError('existing image archive preserved')
        self.run('image', 'save', '-o', str(archive), BASE, self.release['image'], timeout=180)
        with archive.open('rb') as stream:
            self.release['images_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        write(self.root / 'release.json', self.release)
        return {'image_archive_sha256': self.release['images_sha256'], 'bytes': archive.stat().st_size}

    def import_images(self):
        with (self.root / 'images.tar').open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if not self.release.get('images_sha256') or actual != self.release['images_sha256']:
            raise ValueError('image archive drift')
        self.run('image', 'load', '-i', str(self.root / 'images.tar'), timeout=180)
        for image in (BASE, self.release['image']):
            if self.run('image', 'inspect', image, '--format', '{{.Id}}').stdout.strip() != image:
                raise ValueError('loaded image mismatch')
        return {'imported': True, 'image': self.release['image']}

    def seal_trust(self):
        self.release['trust_sha256'] = hashlib.sha256((self.root / 'public-trust.json').read_bytes()).hexdigest()
        write(self.root / 'release.json', self.release)

    def rotate(self):
        result = self.admin('-m', 'common.pilot_ops', 'rotate', '--root', '/bundle', timeout=100)
        self.seal_trust()
        return result

    def start(self):
        if self.release.get('trust_sha256') != hashlib.sha256((self.root / 'public-trust.json').read_bytes()).hexdigest():
            raise ValueError('provisioning trust drift')
        self.admin('-m', 'common.pilot_ops', 'validate', '--root', '/bundle')
        self.renew()
        self.compose('up', '-d', '--no-build', '--pull', 'never', *ROLES)
        return {'started': True}

    def backup(self, vault):
        self.stopped()
        vault = validate_root(vault, fresh=True)
        if vault == self.root or self.root in vault.parents:
            raise ValueError('independent fresh recovery vault required')
        vault.mkdir(parents=True)
        protect_directory(vault)
        override = self.root / 'recovery-compose.json'
        write(override, {'services': {'admin': {'volumes': [str(vault) + ':/recovery:rw']}}})
        p = self.run(*(self.prefix + ['-f', str(override), 'run', '--rm', '-T', '--no-deps', '--pull', 'never',
            'admin', '-m', 'common.pilot_ops', 'checkpoint', '--source', '/bundle',
            '--destination', '/recovery/snapshot']), timeout=90)
        return json.loads(p.stdout)

    def recover(self, vault, receipt):
        if any((self.root / name).exists() for name in COHORT if name != 'states'):
            raise ValueError('restore requires an empty unprovisioned package')
        vault = validate_root(vault)
        override = self.root / 'recovery-compose.json'
        write(override, {'services': {'admin': {'volumes': [str(vault) + ':/recovery:ro']}}})
        p = self.run(*(self.prefix + ['-f', str(override), 'run', '--rm', '-T', '--no-deps', '--pull', 'never',
            'admin', '-m', 'common.pilot_ops', 'install-recovery', '--snapshot', '/recovery/snapshot',
            '--destination', '/bundle', '--expected-digest', receipt]), timeout=90)
        self.seal_trust()
        return json.loads(p.stdout)

    def renew(self):
        code = """import json
from common.management import ManagementStore
from pathlib import Path
r=Path('/bundle');t=json.loads((r/'public-trust.json').read_text())
s=ManagementStore(r/'catalog')
try: m=s.export(r/'control/manifest.json',t['credentials']['cloud']['fingerprint'])
finally:s.close()
print(json.dumps({'sequence':m['sequence'],'lease_seconds':300}))
"""
        return self.admin('-c', code)

    def health(self, role):
        port = 8001 if role == 'gateway' else 8002
        code = ("import json,urllib.request; c=json.load(open('/run/pilot/config.json')); "
                "r=urllib.request.Request('http://127.0.0.1:" + str(port) + "/health',headers={'Authorization':'Bearer '+c['health_token']}); "
                "print(json.dumps(json.load(urllib.request.urlopen(r,timeout=2))))")
        return json.loads(self.compose('exec', '-T', role, 'python', '-c', code).stdout)

    def status(self):
        trust = json.loads((self.root / 'public-trust.json').read_text())
        result = {}
        for role in ROLES:
            try:
                observed = self.health(role)
                summary = alerts(observed)
                descriptor = trust['credentials'][role]
                remaining = (datetime.fromisoformat(descriptor['not_after']) - datetime.now(timezone.utc)).total_seconds()
                summary['credential_remaining_seconds'] = max(0, int(remaining))
                if remaining <= 3600:
                    summary['alerts'].append('credential_expiring_soon')
                if observed.get('management', {}).get('local_fingerprint') != descriptor['fingerprint']:
                    summary['alerts'].append('credential_or_policy_mismatch')
                result[role] = summary
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                result[role] = {'service': role, 'ready': False, 'alerts': ['health_unavailable']}
        return result

    def stopped(self):
        for role in ROLES:
            ids = self.compose('ps', '-a', '-q', role).stdout.split()
            for identity in ids:
                obj = json.loads(self.run('inspect', identity).stdout)[0]
                if obj['Config']['Labels'].get(OWNER) != self.project or obj['State']['Running']:
                    raise ValueError('both owned services must be stopped')

    def cleanup(self):
        removed = []
        for kind, listing, delete in [('container', ['ps', '-aq'], ['rm', '-f']),
                                       ('network', ['network', 'ls', '-q'], ['network', 'rm']),
                                       ('volume', ['volume', 'ls', '-q'], ['volume', 'rm'])]:
            ids = self.run(*listing, '--filter', 'label=' + OWNER + '=' + self.project).stdout.split()
            for identity in ids:
                obj = json.loads(self.run(kind, 'inspect', identity).stdout)[0]
                labels = obj['Config']['Labels'] if kind == 'container' else obj['Labels']
                if labels.get(OWNER) != self.project:
                    raise ValueError('ownership mismatch')
                self.run(*delete, identity); removed.append(identity)
        remaining = {kind: self.run(*listing, '--filter', 'label=' + OWNER + '=' + self.project).stdout.split()
                     for kind, listing in [('containers', ['ps', '-aq']), ('networks', ['network', 'ls', '-q']),
                                           ('volumes', ['volume', 'ls', '-q'])]}
        return {'verified': not any(remaining.values()), 'remaining': remaining,
                'removed': removed, 'state_policy': 'only ownership-verified lab volumes removed; private cold checkpoints retained'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'restore', 'start', 'stop', 'status', 'renew', 'rotate', 'backup', 'cleanup', 'export', 'import'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--docker-cli')
    parser.add_argument('--checkpoint-root', type=Path)
    parser.add_argument('--expected-digest')
    parser.add_argument('--package-version', choices=(VERSION, 'pilot-lab-v1.1'), default=VERSION)
    parser.add_argument('--scope', choices=('simulation',), default='simulation')
    args = parser.parse_args()
    try:
        if args.action in ('init', 'restore'):
            create(args.root, args.package_version)
        pilot = Pilot(args.root, args.docker_cli)
        if args.action == 'init':
            result = pilot.initialize()
        elif args.action == 'restore':
            if not args.checkpoint_root or not args.expected_digest:
                raise ValueError('checkpoint and current independent receipt required')
            pilot.initialize(provision=False)
            result = pilot.recover(args.checkpoint_root, args.expected_digest)
        elif args.action == 'start':
            result = pilot.start()
        elif args.action == 'stop':
            pilot.compose('stop', '--timeout', '10', *ROLES)
            pilot.stopped(); result = {'stopped': True}
        elif args.action == 'renew':
            result = pilot.renew()
        elif args.action == 'rotate':
            result = pilot.rotate()
        elif args.action == 'export':
            result = pilot.export_images()
        elif args.action == 'import':
            result = pilot.import_images()
        elif args.action == 'status':
            result = pilot.status()
        elif args.action == 'backup':
            if not args.checkpoint_root:
                raise ValueError('independent checkpoint root required')
            result = pilot.backup(args.checkpoint_root)
        else:
            result = pilot.cleanup()
        print(json.dumps(result, indent=2)); return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError, KeyError):
        print(json.dumps({'ok': False, 'error': 'pilot_controller_refused'})); return 2


if __name__ == '__main__':
    raise SystemExit(main())
