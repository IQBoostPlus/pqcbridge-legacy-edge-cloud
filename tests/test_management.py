"""Public catalog and local operator CLI contracts (synthetic references only)."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

from common.management import ManagementError, ManagementStore


def test_catalog_enrollment_disable_audit_and_reopen(tmp_path):
    state = tmp_path / 'catalog'
    store = ManagementStore(state)
    store.enroll_gateway('gw-1', 'alice')
    store.enroll_device('dev-1', 'gw-1', str(uuid.uuid4()), '/run/source-key-ref', 'alice')
    store.set_enabled('device', 'dev-1', False, 'bob')
    assert [record['operator'] for record in store.audit()] == ['alice', 'alice', 'bob']
    store.close()
    store = ManagementStore(state)
    assert len(store.audit()) == 3
    with pytest.raises(ManagementError):
        store.enroll_gateway('gw-1', 'alice')
    assert len(store.audit()) == 3
    store.close()


def descriptor(role, subject_id, **changes):
    now = datetime.now(timezone.utc)
    value = {'role': role, 'subject_id': subject_id,
             'cert_file': '/run/certs/' + subject_id + '.pem',
             'key_file': '/run/private/' + subject_id + '.pem',
             'not_before': (now - timedelta(seconds=30)).isoformat(),
             'not_after': (now + timedelta(hours=1)).isoformat(), 'revoked': False}
    return {**value, **changes}


def ready_catalog(tmp_path):
    store = ManagementStore(tmp_path / 'catalog')
    store.enroll_gateway('gw-1', 'alice')
    store.enroll_device('dev-1', 'gw-1', '0b9cf314-1fbf-4b4a-959a-0adc7c20fafa',
                        '/run/device.key', 'alice')
    store.register_credential('a' * 64, descriptor('gateway', 'gw-1'), 'issuer')
    store.register_credential('c' * 64, descriptor('cloud', 'cloud'), 'issuer')
    return store


def test_policy_manifest_current_assets_and_durable_publication(tmp_path):
    store = ready_catalog(tmp_path)
    assert store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice') == 1
    first = store.manifest('c' * 64)
    assert first['sequence'] == 1
    assert first['targets']['gw-1']['devices'] == {'dev-1': '0b9cf314-1fbf-4b4a-959a-0adc7c20fafa'}
    store.set_enabled('device', 'dev-1', False, 'alice')
    store.export(tmp_path / 'published.json', 'c' * 64)
    second = json.loads((tmp_path / 'published.json').read_text())
    assert second['sequence'] == 2
    assert second['targets']['gw-1']['devices'] == {}
    store.close()
    store = ManagementStore(tmp_path / 'catalog')
    assert store.manifest('c' * 64)['sequence'] == 3
    store.close()


def observation(version, **changes):
    # Windows may give adjacent calls the same wall-clock value. Model an ACK
    # received after the preceding operator action, rather than assuming time
    # advanced between Python statements. Keep the production strict ordering.
    previous = datetime.now(timezone.utc)
    deadline = time.monotonic() + 1
    while datetime.now(timezone.utc) <= previous:
        if time.monotonic() >= deadline:
            raise AssertionError('test wall clock did not advance within one second')
        time.sleep(.001)
    now = datetime.now(timezone.utc).isoformat()
    return {'gateway_id': 'gw-1', 'management_version': version,
            'management_state': 'Effective', 'management_applied_at': now,
            'cloud_connected': True, 'business_delivery': 'delivered',
            'last_matching_ack_at': now, 'observed_at': now, **changes}


def test_effectiveness_requires_post_apply_ack_and_becomes_unknown_when_stale(tmp_path):
    store = ready_catalog(tmp_path)
    version = store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    assert store.status('gw-1')['state'] == 'Pending'
    store.begin_apply('gw-1', version, 'alice')
    assert store.status('gw-1')['state'] == 'Applying'
    proof = observation(version)
    store.observe('gw-1', version, proof, 'alice')
    assert store.status('gw-1')['effective_version'] == 1
    assert store.status('gw-1')['state'] == 'Effective'
    assert store.status('gw-1', now=datetime.now(timezone.utc) + timedelta(seconds=301))['state'] == 'Unknown'
    store.close()
    store = ManagementStore(tmp_path / 'catalog')
    assert store.status('gw-1')['state'] == 'Effective'
    store.close()


def test_rollback_restores_profile_without_resurrecting_revoked_credential(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.register_credential('b' * 64, descriptor('gateway', 'gw-1'), 'issuer')
    store.create_version('gw-1', 'hybrid-conservative-v1', 'b' * 64, 'alice')
    store.revoke_credential('a' * 64, 'alice')
    assert store.rollback('gw-1', 1, 'alice') == 3
    status = store.status('gw-1')
    assert status['state'] == 'Rolled back'
    assert status['desired_version'] == 3
    target = store.manifest('c' * 64)['targets']['gw-1']
    assert target['profile'] == 'hybrid-standard-v1'
    assert target['active_credential'] == 'b' * 64
    assert target['accepted_credentials'] == {'b' * 64: None}
    store.begin_apply('gw-1', 3, 'alice')
    assert store.status('gw-1')['state'] == 'Applying'
    store.close()


def test_local_cli_persists_request_file_operation_and_rejects_secret_field(tmp_path):
    request_file = tmp_path / 'request.json'
    command = [sys.executable, '-m', 'common.management', '--state-dir',
               str(tmp_path / 'catalog'), '--request-file', str(request_file)]
    request_file.write_text(json.dumps({'operation': 'enroll_gateway',
                                       'gateway_id': 'gw-1', 'operator': 'alice'}))
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'ok': True, 'result': {'gateway_id': 'gw-1', 'enabled': True}}
    request_file.write_text(json.dumps({'operation': 'status', 'gateway_id': 'gw-1',
                                       'operator': 'alice', 'private_key': 'NEVER_ECHO'}))
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert json.loads(result.stdout) == {'ok': False, 'error': 'invalid_request'}
    assert 'NEVER_ECHO' not in result.stdout + result.stderr
    store = ManagementStore(tmp_path / 'catalog')
    assert len(store.audit()) == 1
    store.close()


def test_revocation_immediately_invalidates_recorded_effective_status_and_is_publishable(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    store.observe('gw-1', 1, observation(1), 'alice')
    store.revoke_credential('a' * 64, 'alice')
    assert store.status('gw-1')['state'] == 'Unknown'
    manifest = store.manifest('c' * 64)
    assert manifest['credentials']['a' * 64]['revoked'] is True
    assert manifest['targets']['gw-1']['active_credential'] == 'a' * 64
    assert len(store.audit()) == 9
    store.close()


def test_invalid_policy_input_refuses_without_poisoning_next_transaction(tmp_path):
    store = ready_catalog(tmp_path)
    with pytest.raises(ManagementError, match='unknown_profile'):
        store.create_version('gw-1', ['classical'], 'a' * 64, 'alice')
    assert store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice') == 1
    assert len(store.audit()) == 5
    store.close()


def test_stale_wrong_target_and_reused_ack_do_not_change_effectiveness(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    old = observation(1)
    store.begin_apply('gw-1', 1, 'alice')
    with pytest.raises(ManagementError, match='ack_not_post_apply_or_reused'):
        store.observe('gw-1', 1, old, 'alice')
    with pytest.raises(ManagementError, match='invalid_observation'):
        store.observe('gw-1', 1, observation(1, gateway_id='gw-2'), 'alice')
    proof = observation(1)
    store.observe('gw-1', 1, proof, 'alice')
    with pytest.raises(ManagementError, match='ack_not_post_apply_or_reused'):
        store.observe('gw-1', 1, proof, 'alice')
    assert store.status('gw-1')['state'] == 'Effective'
    assert len(store.audit()) == 7
    store.close()


def test_failed_business_observation_does_not_claim_effective_version(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    store.observe('gw-1', 1, observation(1, cloud_connected=False,
                                      business_delivery='backlog', last_matching_ack_at=None), 'alice')
    assert store.status('gw-1')['state'] == 'Failed'
    assert store.status('gw-1')['effective_version'] is None
    store.close()


@pytest.mark.parametrize('channel_state', ['Applying', 'Effective'])
def test_unobserved_ack_from_previous_channel_cannot_become_effective(tmp_path, channel_state):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    old_ack = observation(1)['last_matching_ack_at']
    reconnected = observation(1, management_state=channel_state,
                              last_matching_ack_at=old_ack)
    before, audit = store.status('gw-1'), store.audit()
    with pytest.raises(ManagementError, match='^ack_not_current_channel$'):
        store.observe('gw-1', 1, reconnected, 'alice')
    assert store.status('gw-1') == before
    assert store.audit() == audit
    current = observation(1, management_applied_at=reconnected['management_applied_at'])
    accepted = store.observe('gw-1', 1, current, 'alice')
    assert accepted['state'] == 'Effective'
    assert accepted['evidence']['management_state'] == 'Effective'
    assert accepted['evidence']['management_applied_at'] == (
        datetime.fromisoformat(reconnected['management_applied_at']).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
    assert store.audit()[-1]['result']['evidence'] == accepted['evidence']
    store.close()
    store = ManagementStore(tmp_path / 'catalog')
    assert store.status('gw-1')['evidence'] == accepted['evidence']
    store.close()


@pytest.mark.parametrize('missing', ['management_state', 'management_applied_at'])
def test_success_requires_current_channel_proof(tmp_path, missing):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    proof = observation(1)
    del proof[missing]
    before, audit = store.status('gw-1'), store.audit()
    with pytest.raises(ManagementError, match='^ack_not_current_channel$'):
        store.observe('gw-1', 1, proof, 'alice')
    assert store.status('gw-1') == before
    assert store.audit() == audit
    store.close()


@pytest.mark.parametrize('changes', [
    {'management_state': ['Effective']},
    {'management_state': 'NEVER_ECHO'},
    {'management_applied_at': '2026-01-01T00:00:00'},
    {'management_applied_at': 'NEVER_ECHO'},
    {'management_applied_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
])
def test_invalid_current_channel_proof_refuses_atomically(tmp_path, changes):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    before, audit = store.status('gw-1'), store.audit()
    with pytest.raises(ManagementError, match='^ack_not_current_channel$'):
        store.observe('gw-1', 1, observation(1, **changes), 'alice')
    assert store.status('gw-1') == before
    assert store.audit() == audit
    assert 'NEVER_ECHO' not in json.dumps(store.audit())
    store.close()


def test_failed_observation_without_channel_fields_remains_supported(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    proof = observation(1, cloud_connected=False, business_delivery='backlog',
                        last_matching_ack_at=None)
    del proof['management_state'], proof['management_applied_at']
    assert store.observe('gw-1', 1, proof, 'alice')['state'] == 'Failed'
    store.close()


@pytest.mark.parametrize('changes', [
    {'management_state': ['Unknown']},
    {'management_applied_at': '2026-01-01T00:00:00'},
])
def test_failed_observation_validates_optional_channel_fields(tmp_path, changes):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    proof = observation(1, cloud_connected=False, business_delivery='backlog',
                        last_matching_ack_at=None, **changes)
    before, audit = store.status('gw-1'), store.audit()
    with pytest.raises(ManagementError, match='^invalid_observation$'):
        store.observe('gw-1', 1, proof, 'alice')
    assert store.status('gw-1') == before
    assert store.audit() == audit
    store.close()


def test_cli_refuses_unproven_current_channel_then_accepts_matching_ack(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    baseline_audit = store.audit()
    store.close()
    request_file = tmp_path / 'request.json'
    command = [sys.executable, '-m', 'common.management', '--state-dir',
               str(tmp_path / 'catalog'), '--request-file', str(request_file)]
    evidence = observation(1, management_state='Applying')
    request = {'operation': 'observe', 'operator': 'alice', 'gateway_id': 'gw-1',
               'version': 1, 'evidence': evidence}
    request_file.write_text(json.dumps(request))
    refused = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert refused.returncode == 2
    assert json.loads(refused.stdout) == {'ok': False, 'error': 'ack_not_current_channel'}
    store = ManagementStore(tmp_path / 'catalog')
    assert store.status('gw-1')['state'] == 'Applying'
    assert store.audit() == baseline_audit
    store.close()
    evidence['management_state'] = 'Effective'
    request_file.write_text(json.dumps(request))
    accepted = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    result = json.loads(accepted.stdout)['result']
    assert result['state'] == 'Effective'
    assert result['evidence']['management_state'] == 'Effective'
    store = ManagementStore(tmp_path / 'catalog')
    assert store.audit()[-1]['result'] == result
    store.close()


def test_bounded_audit_refusal_is_atomic_and_durable(tmp_path):
    store = ManagementStore(tmp_path / 'catalog', max_audit=1)
    store.enroll_gateway('gw-1', 'alice')
    with pytest.raises(ManagementError, match='audit_quota'):
        store.enroll_gateway('gw-2', 'alice')
    store.close()
    store = ManagementStore(tmp_path / 'catalog', max_audit=1)
    assert store.status('gw-1')['state'] == 'Unknown'
    with pytest.raises(ManagementError, match='unknown_gateway'):
        store.status('gw-2')
    assert len(store.audit()) == 1
    store.close()


def test_gateway_device_credential_version_and_overlap_limits(tmp_path):
    store = ready_catalog(tmp_path)
    for name in ('gw-2', 'gw-3'):
        store.enroll_gateway(name, 'alice')
    with pytest.raises(ManagementError, match='gateway_quota'):
        store.enroll_gateway('gw-4', 'alice')
    for name in ('dev-2', 'dev-3'):
        store.enroll_device(name, 'gw-1', str(uuid.uuid4()), '/run/key', 'alice')
    with pytest.raises(ManagementError, match='device_quota'):
        store.enroll_device('dev-4', 'gw-1', str(uuid.uuid4()), '/run/key', 'alice')
    store.register_credential('b' * 64, descriptor('gateway', 'gw-1'), 'issuer')
    with pytest.raises(ManagementError, match='invalid_overlap'):
        store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice', {
            'a' * 64: None, 'b' * 64: (datetime.now(timezone.utc) + timedelta(seconds=61)).isoformat()})
    for _ in range(100):
        store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    with pytest.raises(ManagementError, match='version_quota'):
        store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    assert store.status('gw-1')['desired_version'] == 100
    store.close()


def test_cli_rejects_duplicate_keys_without_echoing_request(tmp_path):
    request = tmp_path / 'request.json'
    request.write_text('{"operation":"audit","operator":"alice","operator":"NEVER_ECHO"}')
    result = subprocess.run([sys.executable, '-m', 'common.management', '--state-dir',
                             str(tmp_path / 'catalog'), '--request-file', str(request)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert json.loads(result.stdout) == {'ok': False, 'error': 'invalid_request'}
    assert 'NEVER_ECHO' not in result.stdout + result.stderr


def test_small_state_budget_refuses_without_creating_gateway(tmp_path):
    store = ManagementStore(tmp_path / 'catalog', max_bytes=65536)
    with pytest.raises(ManagementError, match='state_byte_quota'):
        store.enroll_gateway('gw-1', 'alice')
    with pytest.raises(ManagementError, match='unknown_gateway'):
        store.status('gw-1')
    assert store.audit() == []
    store.close()


def test_descriptor_fingerprint_matches_and_credential_count_is_bounded(tmp_path):
    store = ready_catalog(tmp_path)
    with pytest.raises(ManagementError, match='fingerprint_mismatch'):
        store.register_credential('b' * 64, descriptor('gateway', 'gw-1', fingerprint='d' * 64), 'issuer')
    store.register_credential('b' * 64, descriptor('gateway', 'gw-1', fingerprint='b' * 64), 'issuer')
    for index in range(9):
        store.register_credential(format(index, '064x'), descriptor('gateway', 'gw-1'), 'issuer')
    with pytest.raises(ManagementError, match='credential_quota'):
        store.register_credential('e' * 64, descriptor('gateway', 'gw-1'), 'issuer')
    manifest = store.manifest('c' * 64)
    assert 'fingerprint' not in manifest['credentials']['b' * 64]
    assert len(manifest['credentials']) == 12
    store.close()


def test_failed_observation_retains_safe_diagnostic_in_status_audit_and_reopen(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    proof = observation(1, cloud_connected=False, business_delivery='backlog',
                        last_matching_ack_at=None, management_failure_reason='tls_configuration_refused')
    store.observe('gw-1', 1, proof, 'alice')
    assert store.status('gw-1')['failure_reason'] == 'tls_configuration_refused'
    assert store.status('gw-1')['evidence']['failure_reason'] == 'tls_configuration_refused'
    assert store.audit()[-1]['result']['failure_reason'] == 'tls_configuration_refused'
    store.close()
    store = ManagementStore(tmp_path / 'catalog')
    assert store.status('gw-1')['failure_reason'] == 'tls_configuration_refused'
    store.observe('gw-1', 1, observation(1), 'alice')
    assert store.status('gw-1')['failure_reason'] is None
    store.close()


@pytest.mark.parametrize('connected,expected', [
    (False, 'cloud_disconnected'), (True, 'business_delivery_unverified'),
])
def test_failed_observation_has_bounded_fallback_reason(tmp_path, connected, expected):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    store.observe('gw-1', 1, observation(1, cloud_connected=connected, business_delivery='backlog',
                                      last_matching_ack_at=None), 'alice')
    assert store.status('gw-1')['failure_reason'] == expected
    store.close()


def test_cli_observe_records_safe_alias_but_rejects_arbitrary_diagnostic_text(tmp_path):
    store = ready_catalog(tmp_path)
    store.create_version('gw-1', 'hybrid-standard-v1', 'a' * 64, 'alice')
    store.begin_apply('gw-1', 1, 'alice')
    store.close()
    request_file = tmp_path / 'request.json'
    command = [sys.executable, '-m', 'common.management', '--state-dir',
               str(tmp_path / 'catalog'), '--request-file', str(request_file)]
    evidence = observation(1, cloud_connected=False, business_delivery='backlog',
                           last_matching_ack_at=None, failure_reason='network_unavailable')
    request = {'operation': 'observe', 'operator': 'alice', 'gateway_id': 'gw-1',
               'version': 1, 'evidence': evidence}
    request_file.write_text(json.dumps(request))
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['result']['failure_reason'] == 'network_unavailable'
    evidence['failure_reason'] = 'NEVER_ECHO secret private-key bytes'
    request_file.write_text(json.dumps(request))
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert json.loads(result.stdout) == {'ok': False, 'error': 'invalid_failure_reason'}
    assert 'NEVER_ECHO' not in result.stdout + result.stderr
    store = ManagementStore(tmp_path / 'catalog')
    assert store.status('gw-1')['failure_reason'] == 'network_unavailable'
    assert len(store.audit()) == 7
    assert 'NEVER_ECHO' not in json.dumps(store.audit())
    store.close()
