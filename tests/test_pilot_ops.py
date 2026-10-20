"""Recovery must preserve accepted data and refuse altered/older authority."""
import json
from pathlib import Path
import sqlite3
import uuid

import pytest

from common.delivery import GatewayQueue, CloudStore, canonical_event, ack_for
from common.pilot_ops import alerts, checkpoint, restore, provision, validate, rotate, install_recovery, COHORT


def cohort(root):
    for name in COHORT:
        path = root / name
        if name.endswith('.json'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}')
        else:
            path.mkdir(parents=True)
    return root


def test_cold_restore_preserves_event_identity_source_progress_and_dedup(tmp_path):
    source = cohort(tmp_path / 'site')
    incarnation = str(uuid.uuid4())
    raw = canonical_event('gw', 'dev', incarnation,
                          {'device_id': 'dev', 'sequence': 1, 'timestamp': None,
                           'temperature_c': 21.5, 'unit': 'celsius'})
    gateway = GatewayQueue(source / 'states/gateway')
    cloud = CloudStore(source / 'states/cloud')
    gateway.accept(raw); cloud.commit(raw)
    gateway.close(); cloud.close()
    receipt = checkpoint(source, tmp_path / 'backup')
    restore(tmp_path / 'backup', tmp_path / 'restored', receipt['manifest_sha256'])
    gateway = GatewayQueue(tmp_path / 'restored/states/gateway')
    cloud = CloudStore(tmp_path / 'restored/states/cloud')
    try:
        assert gateway.pending() == [raw]
        assert cloud.commit(raw) == ack_for(raw)
        assert cloud.snapshot()['committed_total'] == 1
        gateway.acknowledge(raw, ack_for(raw))
        assert gateway.snapshot()['pending'] == 0
        with pytest.raises(ValueError):
            gateway.accept(raw)
    finally:
        gateway.close(); cloud.close()


def test_changed_checkpoint_or_wrong_current_receipt_never_creates_restore(tmp_path):
    source = cohort(tmp_path / 'site')
    first = checkpoint(source, tmp_path / 'first')
    (source / 'control/revoked.json').write_text('{"revoked":["new"]}')
    latest = checkpoint(source, tmp_path / 'latest')
    with pytest.raises(ValueError, match='receipt mismatch'):
        restore(tmp_path / 'first', tmp_path / 'stale', latest['manifest_sha256'])
    assert not (tmp_path / 'stale').exists()
    (tmp_path / 'first/payload/cloud.json').write_text('{"tampered":true}')
    with pytest.raises(ValueError, match='content mismatch'):
        restore(tmp_path / 'first', tmp_path / 'changed', first['manifest_sha256'])
    assert not (tmp_path / 'changed').exists()


def test_unknown_database_schema_refused_even_with_recomputed_manifest(tmp_path):
    source = cohort(tmp_path / 'site')
    db = sqlite3.connect(source / 'states/gateway.sqlite')
    db.execute('CREATE TABLE alien(value)'); db.execute('PRAGMA user_version=99'); db.close()
    with pytest.raises(ValueError, match='unknown delivery schema'):
        checkpoint(source, tmp_path / 'refused')


def test_restore_cannot_overwrite_existing_state(tmp_path):
    source = cohort(tmp_path / 'site')
    receipt = checkpoint(source, tmp_path / 'backup')
    with pytest.raises(ValueError, match='fresh isolated'):
        restore(tmp_path / 'backup', source, receipt['manifest_sha256'])


def test_operator_alerts_distinguish_live_disconnected_backlog_and_unknown_policy():
    report = alerts({'live': True, 'ready': False, 'service': 'gateway', 'policy_valid': True,
                     'cloud_connected': False, 'management_state': 'Unknown',
                     'storage': {'pending': 120, 'quarantined': 0},
                     'health_token': 'must-never-appear'})
    assert set(report['alerts']) == {'cloud_disconnected', 'delivery_backlog', 'policy_not_effective', 'not_ready'}
    assert 'must-never-appear' not in json.dumps(report)


def test_fresh_provision_is_synthetic_and_private_keys_are_role_isolated(tmp_path):
    assert provision(tmp_path)['scope'] == 'synthetic-only'
    for role in ('cloud', 'gateway'):
        assert (tmp_path / (role + '-credentials') / role / 'key.pem').is_file()
        other = 'gateway' if role == 'cloud' else 'cloud'
        assert not (tmp_path / (role + '-credentials') / other / 'key.pem').exists()
    assert (tmp_path / 'control/manifest.json').is_file()
    with pytest.raises(ValueError):
        provision(tmp_path)


def test_demo_key_and_modified_trust_refused(tmp_path):
    provision(tmp_path)
    assert validate(tmp_path)['valid'] is True
    path = tmp_path / 'gateway.json'
    original = json.loads(path.read_text())
    demo = json.loads((Path(__file__).resolve().parents[1] /
                       'common/demo_device_keys.json').read_text())
    original['devices']['dev-lab']['key_hex'] = next(iter(demo.values()))
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match='demo or invalid'):
        validate(tmp_path)
    (tmp_path / 'cloud-credentials/ca.pem').write_text('untrusted replacement')
    with pytest.raises(ValueError):
        validate(tmp_path)


def test_install_recovery_refuses_nonempty_role_state(tmp_path):
    destination = tmp_path / 'new'
    (destination / 'states/cloud').mkdir(parents=True)
    (destination / 'states/gateway').mkdir()
    (destination / 'states/cloud/newer-state').write_text('must preserve')
    with pytest.raises(ValueError, match='nonempty'):
        install_recovery(tmp_path / 'unread-backup', destination, 'a' * 64)
    assert (destination / 'states/cloud/newer-state').read_text() == 'must preserve'


def test_same_named_tables_with_wrong_columns_are_not_a_supported_schema(tmp_path):
    source = cohort(tmp_path / 'site')
    db = sqlite3.connect(source / 'states/gateway.sqlite')
    for name in ('metadata', 'events', 'sources'):
        db.execute('CREATE TABLE ' + name + '(wrong TEXT)')
    db.execute('PRAGMA user_version=1'); db.close()
    with pytest.raises(ValueError, match='unknown database structure'):
        checkpoint(source, tmp_path / 'refused')


def test_capacity_alerts_cover_row_limits_and_recorded_refusals():
    state = {'service': 'gateway', 'live': True, 'ready': False, 'policy_valid': True,
             'cloud_connected': True, 'storage': {'pending': 9999, 'quarantined': 1},
             'metrics': {'source_refused_queue_row_quota': 3}}
    assert 'queue_row_capacity' in alerts(state)['alerts']
    assert 'queue_row_quota' in alerts(state)['alerts']
    assert 'cloud_row_capacity' in alerts({**state, 'service': 'cloud',
        'storage': {'committed_total': 100000}})['alerts']


def test_current_cold_recovery_preserves_issuer_and_revokes_rotated_roles(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    provision(source)
    receipt = checkpoint(source, tmp_path / 'vault')
    restored = tmp_path / 'restored'
    restore(tmp_path / 'vault', restored, receipt['manifest_sha256'])
    before = json.loads((restored / 'public-trust.json').read_text())
    assert rotate(restored)['rotated'] is True
    assert validate(restored)['valid'] is True
    after = json.loads((restored / 'public-trust.json').read_text())
    manifest = json.loads((restored / 'control/manifest.json').read_text())
    for role in ('gateway', 'cloud'):
        assert before['credentials'][role]['fingerprint'] != after['credentials'][role]['fingerprint']
        assert manifest['credentials'][before['credentials'][role]['fingerprint']]['revoked'] is True
