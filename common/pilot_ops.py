"""Offline operator operations for the synthetic Docker pilot package.

Never imported by a service before its mandatory TLS bootstrap. Recovery is a
cold, coordinated checkpoint, not live backup or permission to rewind a site.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import uuid


COHORT = ('catalog', 'control', 'cloud-credentials', 'gateway-credentials',
          'cloud.json', 'gateway.json', 'public-trust.json', 'states', 'issuer', 'issued')
FORMAT = 'pqc-pilot-cold-v1'


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
    path.chmod(0o600)


def external(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink():
        raise ValueError('absolute nonsymlink external path required')
    resolved = path.resolve()
    app = Path(__file__).resolve().parents[1]
    if resolved == app or app in resolved.parents:
        raise ValueError('runtime must be outside application')
    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError('symlink parent refused')
    return resolved


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlink entry refused')
        if path.is_file():
            with path.open('rb') as stream:
                result[path.relative_to(root).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
        elif not path.is_dir():
            raise ValueError('special file refused')
    return result


def check_database(path, immutable=False):
    """Check without creating a missing database or accepting unknown schemas."""
    db = sqlite3.connect(path.as_uri() + ('?mode=ro&immutable=1' if immutable else '?mode=ro'), uri=True)
    try:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('database integrity refused')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if path.name in ('gateway.sqlite', 'cloud.sqlite'):
            if db.execute('PRAGMA user_version').fetchone()[0] != 1 or tables != {'metadata', 'events', 'sources'}:
                raise ValueError('unknown delivery schema')
        elif path.name == 'managed-config.sqlite3':
            if tables != {'guard'} or db.execute('PRAGMA user_version').fetchone()[0] != 0:
                raise ValueError('unknown guard schema')
        elif path.name == 'management.sqlite3':
            if tables != {'catalog', 'audit'} or db.execute('PRAGMA user_version').fetchone()[0] != 0:
                raise ValueError('unknown catalog schema')
        else:
            raise ValueError('unknown database name')
        expected = {
            'metadata': [('key', 'TEXT', 0, 1), ('value', 'TEXT', 1, 0)],
            'events': [('gateway', 'TEXT', 1, 1), ('event_id', 'TEXT', 1, 2),
                       ('raw', 'BLOB', 1, 0), ('status', 'TEXT', 1, 0),
                       ('deadline', 'REAL', 0, 0), ('reason', 'TEXT', 0, 0)],
            'sources': [('gateway', 'TEXT', 1, 1), ('device', 'TEXT', 1, 2),
                        ('incarnation', 'TEXT', 1, 3), ('sequence', 'INTEGER', 1, 0)],
            'catalog': [('id', 'INTEGER', 0, 1), ('body', 'TEXT', 1, 0)],
            'audit': [('id', 'INTEGER', 0, 1), ('body', 'TEXT', 1, 0)],
            'guard': [('id', 'INTEGER', 0, 1), ('body', 'TEXT', 1, 0)],
        }
        for table in tables:
            actual = [(r[1], r[2], r[3], r[5]) for r in db.execute('PRAGMA table_info(' + table + ')')]
            if actual != expected[table]:
                raise ValueError('unknown database structure')
        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]:
            raise ValueError('unknown database trigger')
        if 'catalog' in tables or 'guard' in tables:
            table = 'catalog' if 'catalog' in tables else 'guard'
            body = db.execute('SELECT body FROM ' + table + ' WHERE id=1').fetchone()
            if (not body or json.loads(body[0]).get('schema_version') != 1
                    or db.execute('SELECT count(*) FROM ' + table).fetchone()[0] != 1):
                raise ValueError('unknown control schema')
    finally:
        db.close()


def checkpoint(source, destination):
    """Called only after the package controller verifies BOTH services stopped.

    The returned digest must be kept independently as the current recovery
    authority. Private checkpoint contents must not enter logs or ordinary docs.
    """
    source, destination = external(source), external(destination)
    if destination.exists() or destination == source or source in destination.parents:
        raise ValueError('fresh independent checkpoint directory required')
    for name in COHORT:
        if not (source / name).exists():
            raise ValueError('incomplete cold cohort')
    destination.mkdir(parents=True, mode=0o700)
    payload = destination / 'payload'
    payload.mkdir(mode=0o700)
    for name in COHORT:
        item = source / name
        # Inspect before copying so copytree cannot follow credential symlinks.
        if item.is_symlink():
            raise ValueError('symlink cohort refused')
        if item.is_dir():
            files(item)
            shutil.copytree(item, payload / name)
        else:
            shutil.copyfile(item, payload / name)
    # Services are stopped; checkpoint each SQLite DB and remove its copied
    # WAL/SHM only after SQLite has materialized it in the main file.
    for path in sorted(payload.rglob('*')):
        if path.suffix in ('.sqlite', '.sqlite3'):
            check_database(path)
            db = sqlite3.connect(path)
            try:
                if db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0] != 0:
                    raise ValueError('database checkpoint busy')
            finally:
                db.close()
    for path in payload.rglob('*'):
        path.chmod(0o700 if path.is_dir() else 0o600)
    manifest = {'format': FORMAT, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'checkpoint_id': str(uuid.uuid4()), 'files': files(payload)}
    write_json(destination / 'manifest.json', manifest)
    digest = hashlib.sha256((destination / 'manifest.json').read_bytes()).hexdigest()
    return {'format': FORMAT, 'checkpoint_id': manifest['checkpoint_id'],
            'manifest_sha256': digest, 'file_count': len(manifest['files'])}


def restore(snapshot, destination, expected_digest):
    snapshot, destination = external(snapshot), external(destination)
    if destination.exists() or snapshot == destination or snapshot in destination.parents:
        raise ValueError('fresh isolated restore destination required')
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise ValueError('independently retained current receipt required')
    raw = (snapshot / 'manifest.json').read_bytes()
    if not secrets.compare_digest(hashlib.sha256(raw).hexdigest(), expected_digest):
        raise ValueError('recovery receipt mismatch')
    manifest = json.loads(raw)
    payload = snapshot / 'payload'
    if (manifest.get('format') != FORMAT or payload.is_symlink()
            or set(p.name for p in payload.iterdir()) != set(COHORT)
            or files(payload) != manifest.get('files')):
        raise ValueError('checkpoint content mismatch')
    for path in payload.rglob('*'):
        if path.suffix in ('.sqlite', '.sqlite3'):
            check_database(path, immutable=True)
    shutil.copytree(payload, destination)
    for path in [destination, *destination.rglob('*')]:
        path.chmod(0o700 if path.is_dir() else 0o600)
    return {'restored': True, 'checkpoint_id': manifest['checkpoint_id'],
            'manifest_sha256': expected_digest}


def install_recovery(snapshot, destination, expected_digest):
    """Install only into a new package with two empty mounted Linux volumes."""
    destination = external(destination)
    for name in COHORT:
        path = destination / name
        if name == 'states':
            if any(any((path / role).iterdir()) for role in ('gateway', 'cloud')):
                raise ValueError('nonempty recovery state volume')
        elif path.exists():
            raise ValueError('existing recovery cohort refused')
    result = restore(snapshot, destination / 'recovered', expected_digest)
    for name in COHORT:
        source = destination / 'recovered' / name
        if name == 'states':
            for role in ('gateway', 'cloud'):
                shutil.copytree(source / role, destination / name / role, dirs_exist_ok=True)
        else:
            source.rename(destination / name)
    return result


def alerts(health):
    """Fixed actionable summaries; never echo keys, payloads or health tokens."""
    result = []
    if not health.get('live'):
        result.append('service_not_live')
    if not health.get('policy_valid'):
        result.append('policy_or_credential_expired')
    if health.get('service') == 'gateway' and not health.get('cloud_connected'):
        result.append('cloud_disconnected')
    storage = health.get('storage', {})
    if storage.get('pending', 0):
        result.append('delivery_backlog')
    if storage.get('quarantined', 0):
        result.append('quarantined_data')
    if health.get('management_state') in ('Applying', 'Failed', 'Unknown'):
        result.append('policy_not_effective')
    if not health.get('ready'):
        result.append('not_ready')
    if health.get('loss_count_unknown'):
        result.append('source_loss_count_unknown')
    if health.get('state_bytes', 0) >= 240 * 1024 * 1024:
        result.append('state_capacity')
    if storage.get('pending', 0) + storage.get('quarantined', 0) >= 10000:
        result.append('queue_row_capacity')
    if storage.get('committed_total', 0) >= 100000:
        result.append('cloud_row_capacity')
    metrics = health.get('metrics', {})
    for reason in ('queue_row_quota', 'state_byte_quota', 'storage_transaction_failed'):
        if metrics.get('source_refused_' + reason, 0):
            result.append(reason)
    return {'service': health.get('service'), 'alerts': result,
            'ready': health.get('ready', False), 'storage': storage,
            'state_bytes': health.get('state_bytes'),
            'management_state': health.get('management_state'),
            'management_failure_reason': health.get('management_failure_reason')}


def validate(root):
    """Refuse demo source credentials and drift from provisioned public trust."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    root = external(root)
    trust = json.loads((root / 'public-trust.json').read_text())
    if trust['scope'] != 'synthetic-only':
        raise ValueError('synthetic-only package')
    demo = set()
    for name in ('demo_device_keys.json', 'demo_gateway_keys.json'):
        demo.update(json.loads((Path(__file__).parent / name).read_text()).values())
    for role in ('gateway', 'cloud'):
        config = json.loads((root / (role + '.json')).read_text())
        credential_dir = root / (role + '-credentials')
        if hashlib.sha256((credential_dir / 'ca.pem').read_bytes()).hexdigest() != trust['ca_sha256']:
            raise ValueError('trust anchor mismatch')
        relative = Path(trust['credentials'][role]['cert_file']).relative_to('/run/pilot/credentials')
        cert = x509.load_pem_x509_certificate((credential_dir / relative).read_bytes())
        if cert.fingerprint(hashes.SHA256()).hex() != trust['credentials'][role]['fingerprint']:
            raise ValueError('leaf fingerprint mismatch')
        if role == 'gateway':
            for spec in config['devices'].values():
                key = spec['key_hex']
                if not isinstance(key, str) or len(bytes.fromhex(key)) != 32 or key.lower() in demo:
                    raise ValueError('demo or invalid source credential')
    return {'valid': True, 'scope': 'synthetic-only'}


def rotate(root):
    """Renew both synthetic roles without resetting messages or revocations."""
    from common.credentials import issue_certificate
    from common.management import ManagementStore
    root = external(root)
    trust = json.loads((root / 'public-trust.json').read_text())
    generation = secrets.token_hex(6)
    descriptors = {}
    for role, subject in (('cloud', 'cloud'), ('gateway', 'gw-lab')):
        name = role + '-' + generation
        issued = root / 'issued' / name
        d = issue_certificate(root / 'issuer', issued, role, subject, lifetime_seconds=86400)
        for owner in ('cloud', 'gateway'):
            target = root / (owner + '-credentials') / name
            target.mkdir(mode=0o700)
            shutil.copyfile(issued / 'cert.pem', target / 'cert.pem')
            if owner == role:
                shutil.copyfile(issued / 'key.pem', target / 'key.pem')
                (target / 'key.pem').chmod(0o600)
        d.update(cert_file='/run/pilot/credentials/' + name + '/cert.pem',
                 key_file='/run/pilot/credentials/' + name + '/key.pem')
        descriptors[role] = d
    store = ManagementStore(root / 'catalog')
    try:
        for d in descriptors.values():
            store.register_credential(d['fingerprint'], d, 'pilot-admin')
        version = store.create_version('gw-lab', 'hybrid-standard-v1',
                                       descriptors['gateway']['fingerprint'], 'pilot-admin')
        store.begin_apply('gw-lab', version, 'pilot-admin')
        for d in trust['credentials'].values():
            store.revoke_credential(d['fingerprint'], 'pilot-admin')
        trust['credentials'] = descriptors
        temporary = root / ('trust-' + generation + '.new')
        write_json(temporary, trust); os.replace(temporary, root / 'public-trust.json')
        manifest = store.export(root / 'control/manifest.json', descriptors['cloud']['fingerprint'])
    finally:
        store.close()
    return {'rotated': True, 'version': version, 'manifest_sequence': manifest['sequence']}


def provision(root):
    """Synthetic-only trust bootstrapping, inside a fresh offline admin container."""
    from common.credentials import create_issuer, issue_certificate
    from common.management import ManagementStore
    root = external(root)
    create_issuer(root / 'issuer')
    (root / 'issued').mkdir(mode=0o700)
    (root / 'control').mkdir(mode=0o700)
    key, incarnation = secrets.token_hex(32), str(uuid.uuid4())
    token = secrets.token_hex(32)
    descriptors = {}
    for role, subject in (('cloud', 'cloud'), ('gateway', 'gw-lab')):
        path = root / 'issued' / role
        descriptors[role] = issue_certificate(root / 'issuer', path, role, subject,
                                             lifetime_seconds=86400)
        descriptor = descriptors[role]
        descriptor['cert_file'] = '/run/pilot/credentials/' + role + '/cert.pem'
        descriptor['key_file'] = '/run/pilot/credentials/' + role + '/key.pem'
    for owner in ('cloud', 'gateway'):
        target = root / (owner + '-credentials')
        target.mkdir(mode=0o700)
        shutil.copyfile(root / 'issuer/cert.pem', target / 'ca.pem')
        for role in ('cloud', 'gateway'):
            path = target / role
            path.mkdir(mode=0o700)
            shutil.copyfile(root / 'issued' / role / 'cert.pem', path / 'cert.pem')
            if owner == role:
                shutil.copyfile(root / 'issued' / role / 'key.pem', path / 'key.pem')
                (path / 'key.pem').chmod(0o600)
    store = ManagementStore(root / 'catalog')
    try:
        store.enroll_gateway('gw-lab', 'pilot-admin')
        store.enroll_device('dev-lab', 'gw-lab', incarnation, '/run/pilot/source/dev-lab', 'pilot-admin')
        for descriptor in descriptors.values():
            store.register_credential(descriptor['fingerprint'], descriptor, 'pilot-admin')
        version = store.create_version('gw-lab', 'hybrid-standard-v1',
                                       descriptors['gateway']['fingerprint'], 'pilot-admin')
        store.begin_apply('gw-lab', version, 'pilot-admin')
        store.export(root / 'control/manifest.json', descriptors['cloud']['fingerprint'])
    finally:
        store.close()
    common = {'state_dir': '/var/lib/pqc', 'health_token': token,
              'policy_expires_at': (datetime.now(timezone.utc) + timedelta(seconds=300)).isoformat(),
              'listen_host': '0.0.0.0', 'management': {'manifest_file': '/run/pilot/control/manifest.json'}}
    def tls(role):
        return {'ca_file': '/run/pilot/credentials/ca.pem',
                'cert_file': '/run/pilot/credentials/' + role + '/cert.pem',
                'key_file': '/run/pilot/credentials/' + role + '/key.pem', 'server_hostname': 'cloud'}
    gateway = {**common, 'gateway_id': 'gw-lab', 'devices': {'dev-lab': {'key_hex': key,
        'source_incarnation': incarnation}}, 'cloud_host': 'cloud', 'cloud_port': 5443,
        'listen_port': 5001, 'health_port': 8001, 'tls': tls('gateway')}
    cloud = {**common, 'gateway_peers': {descriptors['gateway']['fingerprint']: {
        'gateway_id': 'gw-lab', 'devices': {'dev-lab': incarnation}}},
        'listen_port': 5443, 'health_port': 8002, 'tls': tls('cloud')}
    write_json(root / 'gateway.json', gateway)
    write_json(root / 'cloud.json', cloud)
    write_json(root / 'public-trust.json', {'scope': 'synthetic-only',
        'ca_sha256': hashlib.sha256((root / 'issuer/cert.pem').read_bytes()).hexdigest(),
        'credentials': descriptors})
    for role in ('gateway', 'cloud'):
        state = root / 'states' / role
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
    return {'provisioned': True, 'scope': 'synthetic-only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('provision'); p.add_argument('--root', type=Path, required=True)
    p = sub.add_parser('validate'); p.add_argument('--root', type=Path, required=True)
    p = sub.add_parser('rotate'); p.add_argument('--root', type=Path, required=True)
    p = sub.add_parser('checkpoint')
    p.add_argument('--source', type=Path, required=True); p.add_argument('--destination', type=Path, required=True)
    p = sub.add_parser('restore')
    p.add_argument('--snapshot', type=Path, required=True); p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--expected-digest', required=True)
    p = sub.add_parser('install-recovery')
    p.add_argument('--snapshot', type=Path, required=True); p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--expected-digest', required=True)
    args = vars(parser.parse_args()); action = args.pop('action')
    try:
        result = {'provision': provision, 'validate': validate, 'rotate': rotate, 'checkpoint': checkpoint,
                  'restore': restore, 'install-recovery': install_recovery}[action](**args)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, sqlite3.Error, KeyError):
        print(json.dumps({'ok': False, 'error': 'pilot_operation_refused'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
