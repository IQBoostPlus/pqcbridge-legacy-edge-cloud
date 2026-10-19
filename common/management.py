"""Bounded trusted local administration for the Docker simulation.

The catalog contains public metadata and absolute references, never key bytes.
SQLite FULL/WAL durability and atomic exports depend on filesystem fsync support.
This is a privileged operator interface, not a remote management service.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sqlite3
import threading
import tempfile
import uuid


class ManagementError(ValueError):
    """Refusal with no implied successful catalog transition."""


PROFILES = {'hybrid-standard-v1', 'hybrid-conservative-v1'}
FAILURE_REASONS = frozenset({
    'tls_configuration_refused', 'tls_identity_refused', 'channel_or_policy_refused',
    'delivery_state_refused', 'network_unavailable', 'delivery_unavailable',
    'cloud_disconnected', 'business_delivery_unverified',
})
_MAX_BYTES = 32 * 1024 * 1024


def _stamp(value=None):
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError as exc:
            raise ManagementError('invalid_timestamp') from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ManagementError('invalid_timestamp')
    return value.astimezone(timezone.utc)


def _utc(value=None):
    return _stamp(value).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ManagementError('invalid_json') from exc


def _identity(value):
    if (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,128}', value)):
        raise ManagementError('invalid_identifier')
    return value


def _fingerprint(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ManagementError('invalid_fingerprint')
    return value


def _reference(value):
    if (not isinstance(value, str) or len(value) > 1024 or '\x00' in value
            or not (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute())):
        raise ManagementError('invalid_reference')
    return value


def _external(path):
    value = Path(path)
    if not value.is_absolute():
        raise ManagementError('absolute_external_path_required')
    value = value.resolve()
    if value.is_relative_to(Path(__file__).resolve().parent.parent):
        raise ManagementError('path_inside_checkout')
    return value


class ManagementStore:
    """Catalog mutations and their bounded operator audit commit together."""

    def __init__(self, state_dir, max_bytes=_MAX_BYTES, max_audit=1000):
        if (type(max_bytes) is not int or not 65536 <= max_bytes <= _MAX_BYTES
                or type(max_audit) is not int or not 1 <= max_audit <= 1000):
            raise ManagementError('invalid_budget')
        self.state_dir = _external(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.max_bytes = max_bytes
        self.max_audit = max_audit
        self._lock = threading.RLock()
        self._db = None
        path = self.state_dir / 'management.sqlite3'
        if path.is_symlink():
            raise ManagementError('unsafe_state_path')
        try:
            self._db = sqlite3.connect(str(path), timeout=5, check_same_thread=False,
                                       isolation_level=None)
            self._db.execute('PRAGMA journal_mode=WAL')
            self._db.execute('PRAGMA synchronous=FULL')
            self._db.execute('PRAGMA busy_timeout=5000')
            tables = {r[0] for r in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if tables and tables != {'catalog', 'audit'}:
                raise ManagementError('unsupported_schema')
            if not tables:
                self._db.execute('BEGIN IMMEDIATE')
                self._db.execute('CREATE TABLE catalog (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
                self._db.execute('CREATE TABLE audit (id INTEGER PRIMARY KEY, body TEXT NOT NULL)')
                empty = {'schema_version': 1, 'sequence': 0, 'gateways': {},
                         'devices': {}, 'credentials': {}, 'versions': [], 'statuses': {}}
                self._db.execute('INSERT INTO catalog VALUES (1,?)', (_json(empty).decode(),))
                self._db.commit()
            self._load()
            self._permissions()
        except (sqlite3.Error, OSError, ManagementError) as exc:
            self.close()
            if isinstance(exc, ManagementError):
                raise
            raise ManagementError('storage_unavailable') from exc

    def _permissions(self):
        try:
            self.state_dir.chmod(0o700)
            for name in ('management.sqlite3', 'management.sqlite3-wal', 'management.sqlite3-shm'):
                path = self.state_dir / name
                if path.exists():
                    path.chmod(0o600)
        except OSError as exc:
            if os.name != 'nt':
                raise ManagementError('state_permissions_failed') from exc

    def _load(self):
        try:
            row = self._db.execute('SELECT body FROM catalog WHERE id=1').fetchone()
            value = json.loads(row[0]) if row else None
            expected = {'schema_version', 'sequence', 'gateways', 'devices',
                        'credentials', 'versions', 'statuses'}
            if type(value) is not dict or set(value) != expected or value['schema_version'] != 1:
                raise ManagementError('unsupported_schema')
            return value
        except (sqlite3.Error, ValueError, TypeError) as exc:
            raise ManagementError('invalid_catalog') from exc

    def _mutate(self, action, operator, change):
        _identity(operator)
        with self._lock:
            try:
                self._db.execute('BEGIN IMMEDIATE')
                data = self._load()
                count = self._db.execute('SELECT COUNT(*) FROM audit').fetchone()[0]
                if count >= self.max_audit:
                    raise ManagementError('audit_quota')
                result = change(data)
                record = {'operation': action, 'operator': operator, 'at': _utc(),
                          'sequence': data['sequence'], 'result': result}
                payload, audit = _json(data), _json(record)
                current = sum(p.stat().st_size for p in self.state_dir.glob('management.sqlite3*') if p.is_file())
                # Budget includes WAL/SHM and conservative transaction growth.
                if current + 4 * (len(payload) + len(audit)) + 32768 > self.max_bytes:
                    raise ManagementError('state_byte_quota')
                self._db.execute('UPDATE catalog SET body=? WHERE id=1', (payload.decode(),))
                self._db.execute('INSERT INTO audit(body) VALUES (?)', (audit.decode(),))
                self._db.commit()
                self._permissions()
                return copy.deepcopy(result)
            except (sqlite3.Error, OSError, ManagementError) as exc:
                if self._db.in_transaction:
                    self._db.rollback()
                if isinstance(exc, ManagementError):
                    raise
                raise ManagementError('storage_transaction_failed') from exc

    def enroll_gateway(self, gateway_id, operator):
        _identity(gateway_id)
        def change(data):
            if gateway_id in data['gateways']:
                raise ManagementError('asset_exists')
            if len(data['gateways']) >= 3:
                raise ManagementError('gateway_quota')
            data['gateways'][gateway_id] = {'enabled': True}
            return {'gateway_id': gateway_id, 'enabled': True}
        return self._mutate('enroll_gateway', operator, change)

    def enroll_device(self, device_id, gateway_id, incarnation, key_ref, operator):
        _identity(device_id)
        _identity(gateway_id)
        _reference(key_ref)
        try:
            if str(uuid.UUID(incarnation)) != incarnation:
                raise ValueError()
        except (ValueError, TypeError, AttributeError) as exc:
            raise ManagementError('invalid_incarnation') from exc
        def change(data):
            if gateway_id not in data['gateways']:
                raise ManagementError('unknown_gateway')
            if device_id in data['devices']:
                raise ManagementError('asset_exists')
            if sum(d['gateway_id'] == gateway_id for d in data['devices'].values()) >= 3:
                raise ManagementError('device_quota')
            value = {'gateway_id': gateway_id, 'incarnation': incarnation,
                     'key_ref': key_ref, 'enabled': True}
            data['devices'][device_id] = value
            return {'device_id': device_id, **value}
        return self._mutate('enroll_device', operator, change)

    def set_enabled(self, kind, asset_id, enabled, operator):
        _identity(asset_id)
        if kind not in ('gateway', 'device') or type(enabled) is not bool:
            raise ManagementError('invalid_asset_change')
        def change(data):
            values = data['gateways' if kind == 'gateway' else 'devices']
            if asset_id not in values:
                raise ManagementError('unknown_asset')
            values[asset_id]['enabled'] = enabled
            return {'kind': kind, 'asset_id': asset_id, 'enabled': enabled}
        return self._mutate('set_enabled', operator, change)

    def register_credential(self, fingerprint, descriptor, operator):
        _fingerprint(fingerprint)
        if type(descriptor) is not dict:
            raise ManagementError('invalid_descriptor')
        descriptor = copy.deepcopy(descriptor)
        if 'fingerprint' in descriptor:
            if descriptor.pop('fingerprint') != fingerprint:
                raise ManagementError('fingerprint_mismatch')
        if set(descriptor) != {'role', 'subject_id', 'cert_file', 'key_file',
                                'not_before', 'not_after', 'revoked'}:
            raise ManagementError('invalid_descriptor')
        if descriptor['role'] not in ('gateway', 'cloud') or type(descriptor['revoked']) is not bool:
            raise ManagementError('invalid_descriptor')
        _identity(descriptor['subject_id'])
        for field in ('cert_file', 'key_file'):
            _reference(descriptor[field])
        before, after = _stamp(descriptor['not_before']), _stamp(descriptor['not_after'])
        if not timedelta(0) < after - before <= timedelta(hours=24):
            raise ManagementError('invalid_certificate_lifetime')
        descriptor['not_before'], descriptor['not_after'] = _utc(before), _utc(after)
        def change(data):
            if fingerprint in data['credentials']:
                raise ManagementError('credential_exists')
            if len(data['credentials']) >= 12:
                raise ManagementError('credential_quota')
            if descriptor['role'] == 'gateway' and descriptor['subject_id'] not in data['gateways']:
                raise ManagementError('unknown_gateway')
            data['credentials'][fingerprint] = descriptor
            return {'fingerprint': fingerprint, 'role': descriptor['role'],
                    'subject_id': descriptor['subject_id'], 'revoked': descriptor['revoked']}
        return self._mutate('register_credential', operator, change)

    def revoke_credential(self, fingerprint, operator):
        _fingerprint(fingerprint)
        def change(data):
            if fingerprint not in data['credentials']:
                raise ManagementError('unknown_credential')
            data['credentials'][fingerprint]['revoked'] = True
            return {'fingerprint': fingerprint, 'revoked': True}
        return self._mutate('revoke_credential', operator, change)

    @staticmethod
    def _valid_credential(data, fingerprint, role, subject=None, now=None):
        _fingerprint(fingerprint)
        cert = data['credentials'].get(fingerprint)
        now = _stamp(now)
        if (cert is None or cert['role'] != role or cert['revoked']
                or (subject is not None and cert['subject_id'] != subject)
                or not _stamp(cert['not_before']) <= now < _stamp(cert['not_after'])):
            raise ManagementError('credential_not_authorized')
        return cert

    def _new_version(self, data, gateway_id, profile, active, accepted=None):
        if gateway_id not in data['gateways']:
            raise ManagementError('unknown_gateway')
        if not isinstance(profile, str) or profile not in PROFILES:
            raise ManagementError('unknown_profile')
        self._valid_credential(data, active, 'gateway', gateway_id)
        if len(data['versions']) >= 100:
            raise ManagementError('version_quota')
        now = _stamp()
        if accepted is None:
            accepted = {active: None}
        if type(accepted) is not dict or len(accepted) > 3 or accepted.get(active, 'missing') is not None:
            raise ManagementError('invalid_overlap')
        normalized = {}
        for fingerprint, deadline in accepted.items():
            cert = self._valid_credential(data, fingerprint, 'gateway', gateway_id, now)
            if fingerprint == active:
                normalized[fingerprint] = None
            else:
                expires = _stamp(deadline)
                if not now < expires <= min(now + timedelta(seconds=60), _stamp(cert['not_after'])):
                    raise ManagementError('invalid_overlap')
                normalized[fingerprint] = _utc(expires)
        version = 1 + max((v['version'] for v in data['versions'] if v['gateway_id'] == gateway_id), default=0)
        data['versions'].append({'gateway_id': gateway_id, 'version': version,
                                 'profile': profile, 'active_credential': active,
                                 'accepted_credentials': normalized})
        old = data['statuses'].get(gateway_id, {})
        data['statuses'][gateway_id] = {'gateway_id': gateway_id, 'desired_version': version,
                                       'effective_version': old.get('effective_version'),
                                       'state': 'Pending', 'profile': profile,
                                       'active_credential': active, 'evidence': None,
                                       'failure_reason': None,
                                       'last_ack_at': old.get('last_ack_at'),
                                       'apply_at': None, 'updated_at': _utc(now)}
        return version

    def create_version(self, gateway_id, profile, active_credential, operator, accepted_credentials=None):
        _identity(gateway_id)
        return self._mutate('create_version', operator, lambda data: self._new_version(
            data, gateway_id, profile, active_credential, accepted_credentials))

    @staticmethod
    def _version(data, gateway_id, version):
        if type(version) is not int or version < 1:
            raise ManagementError('invalid_version')
        for value in data['versions']:
            if value['gateway_id'] == gateway_id and value['version'] == version:
                return value
        raise ManagementError('unknown_version')

    def begin_apply(self, gateway_id, version, operator):
        _identity(gateway_id)
        def change(data):
            self._version(data, gateway_id, version)
            status = data['statuses'][gateway_id]
            if status['desired_version'] != version:
                raise ManagementError('version_not_desired')
            status.update(state='Applying', apply_at=_utc(), evidence=None,
                          failure_reason=None, updated_at=_utc())
            return copy.deepcopy(status)
        return self._mutate('begin_apply', operator, change)

    def observe(self, gateway_id, version, evidence, operator):
        """Record a privileged operator claim from protected runtime health.

        These checks reject stale/mismatched claims; the local operator remains
        responsible for obtaining evidence from the actual authenticated service.
        """
        _identity(gateway_id)
        if type(evidence) is not dict:
            raise ManagementError('invalid_observation')
        observed = _stamp(evidence.get('observed_at')) if evidence.get('observed_at') else None
        now = _stamp()
        if (observed is None or not now - timedelta(seconds=300) <= observed <= now
                or evidence.get('gateway_id') != gateway_id
                or type(evidence.get('management_version', evidence.get('version'))) is not int
                or evidence.get('management_version', evidence.get('version')) != version
                or type(evidence.get('cloud_connected')) is not bool
                or evidence.get('business_delivery') not in
                {'delivered', 'backlog', 'exceptional', 'unreconciled', 'not_yet_delivered'}):
            raise ManagementError('invalid_observation')
        ack = evidence.get('last_matching_ack_at')
        ack = _stamp(ack) if ack is not None else None
        if ack is not None and (ack > observed or ack < observed - timedelta(seconds=300)):
            raise ManagementError('invalid_ack_observation')
        reason = evidence.get('management_failure_reason', evidence.get('failure_reason'))
        if (reason is not None and (not isinstance(reason, str) or reason not in FAILURE_REASONS)
                or ('management_failure_reason' in evidence and 'failure_reason' in evidence
                    and evidence['management_failure_reason'] != evidence['failure_reason'])):
            raise ManagementError('invalid_failure_reason')
        success = evidence['cloud_connected'] and evidence['business_delivery'] == 'delivered'
        channel_state = evidence.get('management_state')
        channel_applied = evidence.get('management_applied_at')
        channel_error = 'ack_not_current_channel' if success else 'invalid_observation'
        if channel_state is not None and (
                not isinstance(channel_state, str)
                or channel_state not in {'Unknown', 'Applying', 'Effective'}):
            raise ManagementError(channel_error)
        if channel_applied is not None:
            try:
                channel_applied = _stamp(channel_applied)
            except ManagementError as exc:
                raise ManagementError(channel_error) from exc
            if channel_applied > observed:
                raise ManagementError(channel_error)
        def change(data):
            self._version(data, gateway_id, version)
            status = data['statuses'][gateway_id]
            if (status['desired_version'] != version or status['state'] not in ('Applying', 'Effective', 'Failed')
                    or status['apply_at'] is None or observed < _stamp(status['apply_at'])):
                raise ManagementError('observation_not_applying')
            failure_reason = None if success else (reason or (
                'cloud_disconnected' if not evidence['cloud_connected'] else 'business_delivery_unverified'))
            if success and (ack is None or ack <= _stamp(status['apply_at'])
                            or (status.get('last_ack_at') is not None
                                and ack <= _stamp(status['last_ack_at']))):
                raise ManagementError('ack_not_post_apply_or_reused')
            if success and (channel_state != 'Effective' or channel_applied is None
                            or channel_applied > ack):
                raise ManagementError('ack_not_current_channel')
            proof = {'gateway_id': gateway_id, 'management_version': version,
                     'management_state': channel_state,
                     'management_applied_at': _utc(channel_applied) if channel_applied else None,
                     'cloud_connected': evidence['cloud_connected'],
                     'business_delivery': evidence['business_delivery'],
                     'last_matching_ack_at': _utc(ack) if ack else None,
                     'observed_at': _utc(observed), 'failure_reason': failure_reason}
            status.update(state='Effective' if success else 'Failed', evidence=proof,
                          failure_reason=failure_reason, updated_at=_utc(now))
            if success:
                status.update(effective_version=version, last_ack_at=_utc(ack))
            return copy.deepcopy(status)
        return self._mutate('observe', operator, change)

    def status(self, gateway_id, now=None):
        _identity(gateway_id)
        now = _stamp(now)
        with self._lock:
            data = self._load()
            if gateway_id not in data['gateways']:
                raise ManagementError('unknown_gateway')
            result = copy.deepcopy(data['statuses'].get(gateway_id, {
                'gateway_id': gateway_id, 'desired_version': None,
                'effective_version': None, 'state': 'Unknown', 'evidence': None, 'failure_reason': None}))
            result.setdefault('failure_reason', None)
            proof = result.get('evidence')
            if proof and (now < _stamp(proof['observed_at'])
                          or now - _stamp(proof['observed_at']) > timedelta(seconds=300)):
                result['state'] = 'Unknown'
            if result['state'] == 'Effective':
                try:
                    self._valid_credential(data, result['active_credential'], 'gateway', gateway_id, now)
                    if not data['gateways'][gateway_id]['enabled']:
                        result['state'] = 'Unknown'
                except ManagementError:
                    result['state'] = 'Unknown'
            return result

    def rollback(self, gateway_id, version, operator):
        """Restore a previous profile, keeping only current authorized keys."""
        _identity(gateway_id)
        def change(data):
            previous = self._version(data, gateway_id, version)
            status = data['statuses'][gateway_id]
            if version >= status['desired_version']:
                raise ManagementError('rollback_requires_prior_version')
            current = self._version(data, gateway_id, status['desired_version'])
            active = current['active_credential']
            self._valid_credential(data, active, 'gateway', gateway_id)
            accepted = {active: None}
            now = _stamp()
            for fingerprint, deadline in current['accepted_credentials'].items():
                if fingerprint == active or deadline is None or _stamp(deadline) <= now:
                    continue
                try:
                    self._valid_credential(data, fingerprint, 'gateway', gateway_id, now)
                except ManagementError:
                    continue
                accepted[fingerprint] = deadline
            result = self._new_version(data, gateway_id, previous['profile'], active, accepted)
            data['statuses'][gateway_id]['state'] = 'Rolled back'
            return result
        return self._mutate('rollback', operator, change)

    def manifest(self, cloud_credential, lease_seconds=300, operator='manifest'):
        _fingerprint(cloud_credential)
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ManagementError('invalid_lease')
        def change(data):
            descriptor = data['credentials'].get(cloud_credential)
            if descriptor is None or descriptor['role'] != 'cloud':
                raise ManagementError('unknown_cloud_credential')
            now = _stamp()
            targets = {}
            for gateway_id, status in data['statuses'].items():
                version = self._version(data, gateway_id, status['desired_version'])
                accepted = {fingerprint: deadline for fingerprint, deadline in version['accepted_credentials'].items()
                            if deadline is None or _stamp(deadline) > now}
                devices = {device_id: device['incarnation'] for device_id, device in data['devices'].items()
                           if device['gateway_id'] == gateway_id and device['enabled']}
                targets[gateway_id] = {'enabled': data['gateways'][gateway_id]['enabled'],
                                       'version': version['version'], 'profile': version['profile'],
                                       'active_credential': version['active_credential'],
                                       'accepted_credentials': accepted, 'devices': devices}
            value = {'schema_version': 1, 'sequence': data['sequence'] + 1,
                     'issued_at': _utc(now), 'expires_at': _utc(now + timedelta(seconds=lease_seconds)),
                     'cloud_credential': cloud_credential, 'credentials': data['credentials'],
                     'targets': targets}
            if len(_json(value)) > 65535:
                raise ManagementError('manifest_byte_quota')
            data['sequence'] += 1
            return value
        return self._mutate('manifest', operator, change)

    def export(self, path, cloud_credential, lease_seconds=300, operator='manifest'):
        path = _external(path)
        if path.is_symlink() or not path.parent.is_dir():
            raise ManagementError('unsafe_export_path')
        # Serializes sequence creation and file replace across this catalog's
        # local CLI processes, preventing a slow writer restoring an older file.
        with self._lock:
            lock = path.with_name(path.name + '.lock')
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except OSError as exc:
                raise ManagementError('export_busy') from exc
            temporary = None
            try:
                os.close(fd)
                value = self.manifest(cloud_credential, lease_seconds, operator)
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.', delete=False) as output:
                    temporary = Path(output.name)
                    output.write(_json(value))
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, path)
                temporary = None
                if os.name != 'nt':
                    directory = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                return value
            except OSError as exc:
                raise ManagementError('export_failed') from exc
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
                lock.unlink(missing_ok=True)

    def audit(self):
        with self._lock:
            return [json.loads(row[0]) for row in self._db.execute('SELECT body FROM audit ORDER BY id')]

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None


def _request(path):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ManagementError('invalid_request')
            result[key] = value
        return result
    def bad_constant(value):
        raise ManagementError('invalid_request')
    with _external(path).open('rb') as source:
        raw = source.read(65536)
    if len(raw) > 65535:
        raise ManagementError('invalid_request')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=bad_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ManagementError('invalid_request') from exc
    if type(value) is not dict:
        raise ManagementError('invalid_request')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Trusted local phase C administration')
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--request-file', required=True)
    args = parser.parse_args(argv)
    store = None
    try:
        request = _request(args.request_file)
        operation = request.pop('operation', None)
        allowed = {
            'enroll_gateway': ({'gateway_id'}, set()),
            'enroll_device': ({'device_id', 'gateway_id', 'incarnation', 'key_ref'}, set()),
            'set_enabled': ({'kind', 'asset_id', 'enabled'}, set()),
            'register_credential': ({'fingerprint', 'descriptor'}, set()),
            'revoke_credential': ({'fingerprint'}, set()),
            'create_version': ({'gateway_id', 'profile', 'active_credential'}, {'accepted_credentials'}),
            'begin_apply': ({'gateway_id', 'version'}, set()),
            'observe': ({'gateway_id', 'version', 'evidence'}, set()),
            'rollback': ({'gateway_id', 'version'}, set()),
            'status': ({'gateway_id'}, set()),
            'manifest': ({'cloud_credential'}, {'lease_seconds'}),
            'export': ({'path', 'cloud_credential'}, {'lease_seconds'}),
            'audit': (set(), set()),
        }
        if not isinstance(operation, str) or operation not in allowed:
            raise ManagementError('invalid_request')
        operator = _identity(request.pop('operator', None))
        required, optional = allowed[operation]
        if not required <= request.keys() or request.keys() - required - optional:
            raise ManagementError('invalid_request')
        store = ManagementStore(args.state_dir)
        if operation not in ('status', 'audit'):
            request['operator'] = operator
        result = getattr(store, operation)(**request)
        print(_json({'ok': True, 'result': result}).decode())
        return 0
    except ManagementError as exc:
        print(_json({'ok': False, 'error': str(exc)}).decode())
        return 2
    except (OSError, TypeError, ValueError, OverflowError, RecursionError):
        print('{"ok":false,"error":"invalid_request"}')
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == '__main__':
    raise SystemExit(main())
