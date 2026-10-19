"""Trusted, bounded manifest adapter for the existing secure service.

This module validates configuration, not TLS handshakes. The managed bootstrap
owns the pre-import OpenSSL gate and transport owns certificate-chain validation.
Only the local role's leaf and key references need to be mounted in its process.
"""
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sqlite3
import threading
import time
import uuid

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID

from common.secure_runtime import Configuration, ServiceError, load_document, timestamp


PROFILES = {'hybrid-standard-v1': 5, 'hybrid-conservative-v1': 3}


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _fingerprint(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ServiceError('invalid manifest fingerprint')


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,128}', value):
        raise ServiceError('invalid manifest identity')


def _reference(value):
    if (not isinstance(value, str) or len(value) > 1024 or '\x00' in value
            or not (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute())):
        raise ServiceError('invalid manifest credential reference')


class ManagedConfiguration(Configuration):
    """Keep B's private provisions and apply public, revocable authorization.

    Publication sequence, content digest, immutable credential metadata and
    revocation tombstones survive a process restart. Lease renewal alone does
    not change a channel token; per-peer authorization changes do.
    """
    dynamic_tls = True

    def __init__(self, path, role):
        if role not in ('gateway', 'cloud'):
            raise ServiceError('invalid service role')
        super().__init__(path, role)
        self._base = copy.deepcopy(self.value)
        self._base_tls = copy.deepcopy(self.tls)
        self._lock = threading.RLock()
        self._manifest = None
        self._usable = False
        self._error = 'unavailable'
        self._closed = False
        self._own_fingerprint = None
        self._db = None
        self._manifest_path = Path(self.value['management']['manifest_file'])
        if not self._manifest_path.is_absolute():
            raise ServiceError('absolute manifest path required')
        self._groups = {}
        if role == 'cloud':
            for spec in self._base['gateway_peers'].values():
                group = self._groups.setdefault(spec['gateway_id'], {})
                for device, incarnation in spec['devices'].items():
                    if device in group and group[device] != incarnation:
                        raise ServiceError('ambiguous baseline incarnation')
                    group[device] = incarnation
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        database = self.state_dir / 'managed-config.sqlite3'
        if database.is_symlink():
            raise ServiceError('unsafe managed state path')
        try:
            self._db = sqlite3.connect(str(database), timeout=5, isolation_level=None,
                                      check_same_thread=False)
            self._db.execute('PRAGMA journal_mode=WAL')
            self._db.execute('PRAGMA synchronous=FULL')
            self._db.execute('PRAGMA wal_autocheckpoint=16')
            self._db.execute('PRAGMA journal_size_limit=65536')
            tables = {r[0] for r in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if tables and tables != {'guard'}:
                raise ServiceError('unsupported managed state schema')
            if not tables:
                self._db.execute('BEGIN IMMEDIATE')
                self._db.execute('CREATE TABLE guard (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
                self._db.execute('INSERT INTO guard VALUES(1,?)', (_json({
                    'schema_version': 1, 'sequence': 0, 'digest': '', 'revoked': [],
                    'credentials': {}, 'wall': 0}),))
                self._db.commit()
            self._state()
            self._permissions()
            self._refresh()
        except (sqlite3.Error, OSError, ValueError, KeyError, TypeError):
            self.close()
            raise ServiceError('managed state unavailable') from None

    def _permissions(self):
        try:
            self.state_dir.chmod(0o700)
            for path in self.state_dir.glob('managed-config.sqlite3*'):
                path.chmod(0o600)
        except OSError:
            if os.name != 'nt':
                raise

    def _state(self):
        row = self._db.execute('SELECT body FROM guard WHERE id=1').fetchone()
        state = json.loads(row[0]) if row else None
        if (not isinstance(state, dict) or set(state) != {
                'schema_version', 'sequence', 'digest', 'revoked', 'credentials', 'wall'}
                or state['schema_version'] != 1 or type(state['sequence']) is not int
                or not 0 <= state['sequence'] < 2**63
                or not isinstance(state['credentials'], dict) or len(state['credentials']) > 12
                or not isinstance(state['revoked'], list) or len(state['revoked']) > 12
                or not isinstance(state['wall'], (float, int))):
            raise ServiceError('invalid managed state schema')
        return state

    def _validate(self, value, now):
        if set(value) != {'schema_version', 'sequence', 'issued_at', 'expires_at',
                         'cloud_credential', 'credentials', 'targets'}:
            raise ServiceError('invalid manifest fields')
        if (type(value['schema_version']) is not int or value['schema_version'] != 1
                or type(value['sequence']) is not int or not 1 <= value['sequence'] < 2**63):
            raise ServiceError('invalid manifest version')
        issued, expiry = timestamp(value['issued_at']), timestamp(value['expires_at'])
        if not 0 < expiry - issued <= 300 or issued > now + 1:
            raise ServiceError('invalid manifest lease')
        credentials, targets = value['credentials'], value['targets']
        if not isinstance(credentials, dict) or not 1 <= len(credentials) <= 12:
            raise ServiceError('invalid credential registry')
        for fp, cert in credentials.items():
            _fingerprint(fp)
            if (not isinstance(cert, dict) or set(cert) != {'role', 'subject_id', 'cert_file',
                    'key_file', 'not_before', 'not_after', 'revoked'}
                    or cert['role'] not in ('gateway', 'cloud') or type(cert['revoked']) is not bool):
                raise ServiceError('invalid credential descriptor')
            _identifier(cert['subject_id'])
            _reference(cert['cert_file']); _reference(cert['key_file'])
            if not 0 < timestamp(cert['not_after']) - timestamp(cert['not_before']) <= 86400:
                raise ServiceError('invalid credential lifetime')
        _fingerprint(value['cloud_credential'])
        if credentials[value['cloud_credential']]['role'] != 'cloud':
            raise ServiceError('invalid cloud credential')
        if not isinstance(targets, dict) or not 1 <= len(targets) <= 3:
            raise ServiceError('invalid target registry')
        for gateway, target in targets.items():
            _identifier(gateway)
            if (not isinstance(target, dict) or set(target) != {'enabled', 'version', 'profile',
                    'active_credential', 'accepted_credentials', 'devices'}
                    or type(target['enabled']) is not bool or type(target['version']) is not int
                    or not 1 <= target['version'] <= 100 or target['profile'] not in PROFILES):
                raise ServiceError('invalid managed target')
            active, accepted, devices = target['active_credential'], target['accepted_credentials'], target['devices']
            _fingerprint(active)
            if (not isinstance(accepted, dict) or not 1 <= len(accepted) <= 3
                    or accepted.get(active, 'missing') is not None):
                raise ServiceError('invalid credential overlap')
            for fp, deadline in accepted.items():
                _fingerprint(fp)
                cert = credentials[fp]
                if cert['role'] != 'gateway' or cert['subject_id'] != gateway:
                    raise ServiceError('invalid gateway credential')
                if fp != active and (deadline is None or timestamp(deadline) > min(
                        issued + 60, timestamp(cert['not_after']))):
                    raise ServiceError('invalid overlap deadline')
            if not isinstance(devices, dict) or len(devices) > 3:
                raise ServiceError('invalid managed devices')
            for device, incarnation in devices.items():
                _identifier(device)
                if str(uuid.UUID(incarnation)) != incarnation:
                    raise ServiceError('invalid managed incarnation')

    def _remember(self, value, now):
        digest = hashlib.sha256(_json(value).encode()).hexdigest()
        self._db.execute('BEGIN IMMEDIATE')
        try:
            state = self._state()
            if (value['sequence'] < state['sequence'] or (value['sequence'] == state['sequence']
                    and digest != state['digest']) or now + 1 < state['wall']):
                raise ServiceError('manifest rollback refused')
            known = state['credentials']
            revoked = set(state['revoked'])
            for fp, cert in value['credentials'].items():
                immutable = dict(cert); immutable.pop('revoked')
                if fp in known and known[fp] != immutable:
                    raise ServiceError('credential reference changed')
                known[fp] = immutable
                if cert['revoked']:
                    revoked.add(fp)
            if len(known) > 12 or len(revoked) > 12:
                raise ServiceError('managed state credential quota')
            updated = {'schema_version': 1, 'sequence': value['sequence'], 'digest': digest,
                       'revoked': sorted(revoked), 'credentials': known, 'wall': max(now, state['wall'])}
            # Bound the role guard independently and include its files in B's
            # total state quota. No history deletion or state reset is performed.
            used = sum(p.stat().st_size for p in self.state_dir.iterdir() if p.is_file())
            own = sum(p.stat().st_size for p in self.state_dir.glob('managed-config.sqlite3*') if p.is_file())
            if own > 1024 * 1024 or used + len(_json(updated)) * 4 + 32768 >= self.limits['state_bytes']:
                raise ServiceError('managed state quota')
            if (value['sequence'] != state['sequence'] or digest != state['digest']
                    or int(now) > int(state['wall'])):
                self._db.execute('UPDATE guard SET body=? WHERE id=1', (_json(updated),))
            self._db.commit()
            return revoked
        except BaseException:
            self._db.rollback()
            raise

    def _credential_valid(self, fp, now):
        cert = self._manifest['credentials'][fp]
        return (fp not in self._revoked and not cert['revoked']
                and timestamp(cert['not_before']) <= now < timestamp(cert['not_after']))

    def _local_leaf(self, fp):
        descriptor = self._manifest['credentials'][fp]
        if descriptor['role'] != self.role:
            raise ServiceError('local credential role mismatch')
        if self.role == 'gateway' and descriptor['subject_id'] != self._base['gateway_id']:
            raise ServiceError('local credential subject mismatch')
        if self.role == 'cloud':
            baseline_fp = self.local_cert.fingerprint(hashes.SHA256()).hex()
            known = self._state()['credentials'].get(baseline_fp)
            subjects = self.local_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            baseline_subject = known['subject_id'] if known else (subjects[0].value if subjects else None)
            if descriptor['subject_id'] != baseline_subject:
                raise ServiceError('local cloud subject mismatch')
        cert = x509.load_pem_x509_certificate(Path(descriptor['cert_file']).read_bytes())
        if (cert.fingerprint(hashes.SHA256()).hex() != fp
                or cert.not_valid_before_utc.timestamp() != timestamp(descriptor['not_before'])
                or cert.not_valid_after_utc.timestamp() != timestamp(descriptor['not_after'])):
            raise ServiceError('local certificate metadata mismatch')
        tls = dict(self._base_tls)
        tls.update(cert_file=descriptor['cert_file'], key_file=descriptor['key_file'])
        self.tls = tls
        self.cert_end = cert.not_valid_after_utc.timestamp()
        self._own_fingerprint = fp

    def _refresh(self):
        with self._lock:
            self._usable = False
            if self._closed:
                return
            try:
                now = time.time()
                expected = self.wall_start + time.monotonic() - self.mono_start
                if now + 1 < expected:
                    self.clock_uncertain = True
                live_base = load_document(self.path)
                if live_base != self._base or self.clock_uncertain:
                    raise ServiceError('immutable base or clock changed')
                value = load_document(self._manifest_path)
                self._validate(value, max(now, expected))
                revoked = self._remember(value, max(now, expected))
                self._manifest, self._revoked = value, revoked
                if self.role == 'gateway':
                    target = value['targets'].get(self._base['gateway_id'])
                    if target is None:
                        raise ServiceError('gateway target missing')
                    for device, incarnation in target['devices'].items():
                        if (device not in self._base['devices'] or
                                self._base['devices'][device]['source_incarnation'] != incarnation):
                            raise ServiceError('managed source exceeds baseline provision')
                    fp = target['active_credential']
                else:
                    fp = value['cloud_credential']
                self._local_leaf(fp)
                self._usable = True
                self._error = None
                if self.role == 'cloud':
                    self.value['gateway_peers'] = self._peers(max(now, expected))
            except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error):
                self._usable = False
                self._error = 'manifest_unavailable_or_invalid'
                if self.role == 'cloud':
                    self.value['gateway_peers'] = {}

    def _peers(self, now):
        result = {}
        for gateway, target in self._manifest['targets'].items():
            if not target['enabled'] or gateway not in self._groups:
                continue
            devices = target['devices']
            # Public management cannot expand private baseline provisions.
            if any(self._groups[gateway].get(d) != i for d, i in devices.items()):
                raise ServiceError('managed peer exceeds baseline provision')
            for fp, deadline in target['accepted_credentials'].items():
                if self._credential_valid(fp, now) and (deadline is None or timestamp(deadline) > now):
                    result[fp] = {'gateway_id': gateway, 'devices': dict(devices)}
        return result

    def remaining(self):
        self._refresh()
        with self._lock:
            if not self._usable:
                return 0
            now = max(time.time(), self.wall_start + time.monotonic() - self.mono_start)
            if not self._credential_valid(self._own_fingerprint, now):
                return 0
            if self.role == 'gateway':
                target = self._manifest['targets'][self._base['gateway_id']]
                if not target['enabled'] or not self._credential_valid(self._manifest['cloud_credential'], now):
                    return 0
            return max(0, min(timestamp(self._manifest['expires_at']), self.cert_end) - now)

    def operation_timeout(self, peer_fingerprint=None):
        self._refresh()
        with self._lock:
            if not self._usable:
                return 3
            gateway = self._base['gateway_id'] if self.role == 'gateway' else None
            if self.role == 'cloud' and peer_fingerprint in self.value['gateway_peers']:
                gateway = self.value['gateway_peers'][peer_fingerprint]['gateway_id']
            return PROFILES[self._manifest['targets'][gateway]['profile']] if gateway else 5

    def channel_token(self, peer_fingerprint, *, local_fingerprint=None):
        with self._lock:
            if self.remaining() <= 0:
                return None
            # The runtime passes the actual context's captured leaf identity.
            # Keep this comparison atomic with the freshly refreshed token, so
            # rotation during a handshake cannot relabel an old TLS context.
            if local_fingerprint is not None and local_fingerprint != self._own_fingerprint:
                return None
            if self.role == 'gateway':
                if peer_fingerprint != self._manifest['cloud_credential']:
                    return None
                gateway = self._base['gateway_id']
            else:
                peer = self.value['gateway_peers'].get(peer_fingerprint)
                if peer is None:
                    return None
                gateway = peer['gateway_id']
            target = self._manifest['targets'][gateway]
            content = {'local': self._own_fingerprint, 'peer': peer_fingerprint,
                       'gateway': gateway, 'version': target['version'], 'profile': target['profile'],
                       'enabled': target['enabled'], 'devices': target['devices'],
                       'active': target['active_credential'],
                       'peer_deadline': target['accepted_credentials'].get(peer_fingerprint)
                       if self.role == 'cloud' else None}
            return hashlib.sha256(_json(content).encode()).hexdigest()

    def channel_current(self, peer_fingerprint, token):
        current = self.channel_token(peer_fingerprint)
        return token is not None and current is not None and current == token

    def source_allowed(self, device_id, spec):
        self._refresh()
        with self._lock:
            if not self._usable or self.role != 'gateway':
                return False
            target = self._manifest['targets'][self._base['gateway_id']]
            return (target['enabled'] and self._base['devices'].get(device_id) == spec
                    and target['devices'].get(device_id) == spec.get('source_incarnation'))

    def management_status(self):
        valid = self.valid()
        with self._lock:
            result = {'managed': True, 'valid': valid, 'state': 'Pending' if valid else 'Unknown',
                      'sequence': self._manifest['sequence'] if self._manifest else None,
                      'local_fingerprint': self._own_fingerprint, 'error': self._error}
            if self.role == 'gateway' and self._manifest:
                target = self._manifest['targets'].get(self._base['gateway_id'])
                if target:
                    result.update(version=target['version'], desired_version=target['version'],
                                  profile=target['profile'], enabled=target['enabled'])
            # Application binds/applies a channel and supplies real ACK evidence;
            # desired configuration alone never claims effectiveness.
            return result

    def close(self):
        with self._lock:
            self._closed = True
            if self._db is not None:
                self._db.close()
                self._db = None
