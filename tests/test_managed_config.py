"""Trusted manifest policy through its public configuration boundary."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import uuid

import pytest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from common.managed_config import ManagedConfiguration


def fixture(tmp_path, role='gateway'):
    now = datetime.now(timezone.utc)
    credentials = {}
    for subject, kind in [('gw-one', 'gateway'), ('gw-next', 'gateway'), ('cloud', 'cloud')]:
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
        leaf = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(seconds=10))
                .not_valid_after(now + timedelta(minutes=10)).sign(key, hashes.SHA256()))
        cert_path = tmp_path / (subject + '.pem')
        key_path = tmp_path / (subject + '.key')
        cert_path.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        fp = leaf.fingerprint(hashes.SHA256()).hex()
        credentials[fp] = {'role': kind, 'subject_id': 'gw-one' if kind == 'gateway' else 'cloud',
                           'cert_file': str(cert_path), 'key_file': str(key_path),
                           'not_before': leaf.not_valid_before_utc.isoformat(),
                           'not_after': leaf.not_valid_after_utc.isoformat(), 'revoked': False}
    first, next_fp, cloud = credentials
    incarnation = str(uuid.uuid4())
    manifest = {'schema_version': 1, 'sequence': 1, 'issued_at': now.isoformat(),
                'expires_at': (now + timedelta(seconds=60)).isoformat(),
                'cloud_credential': cloud, 'credentials': credentials,
                'targets': {'gw-one': {'enabled': True, 'version': 1,
                    'profile': 'hybrid-standard-v1', 'active_credential': first,
                    'accepted_credentials': {first: None}, 'devices': {'dev-one': incarnation}}}}
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    own = credentials[first if role == 'gateway' else cloud]
    config = {'gateway_id': 'gw-one', 'devices': {'dev-one': {'key_hex': '11' * 32,
                   'source_incarnation': incarnation}},
              'gateway_peers': {first: {'gateway_id': 'gw-one', 'devices': {'dev-one': incarnation}}},
              'tls': {'ca_file': str(tmp_path / 'ca.pem'), 'cert_file': own['cert_file'],
                      'key_file': own['key_file'], 'server_hostname': 'cloud'},
              'state_dir': str(tmp_path / ('state-' + role)), 'health_token': 'x' * 32,
              'policy_expires_at': (now + timedelta(seconds=60)).isoformat(),
              'management': {'manifest_file': str(manifest_path)}}
    path = tmp_path / (role + '.json')
    path.write_text(json.dumps(config), encoding='utf-8')
    return path, manifest_path, manifest, (first, next_fp, cloud)


def test_live_target_updates_profile_without_changing_source_identity(tmp_path):
    path, manifest_path, manifest, (first, _, cloud) = fixture(tmp_path)
    before = path.read_bytes()
    config = ManagedConfiguration(path, 'gateway')
    spec = dict(config.value['devices']['dev-one'])
    token = config.channel_token(cloud)
    assert config.valid()
    assert config.operation_timeout() == 5
    manifest['sequence'] = 2
    manifest['targets']['gw-one']['version'] = 2
    manifest['targets']['gw-one']['profile'] = 'hybrid-conservative-v1'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    assert config.valid()
    assert config.operation_timeout() == 3
    assert config.source_allowed('dev-one', spec)
    assert config.value['devices']['dev-one'] == spec
    assert not config.channel_current(cloud, token)
    assert config.tls['cert_file'] == manifest['credentials'][first]['cert_file']
    assert path.read_bytes() == before
    config.close()


def publish(path, manifest, sequence=None):
    manifest['sequence'] = sequence if sequence is not None else manifest['sequence'] + 1
    path.write_text(json.dumps(manifest), encoding='utf-8')


def test_same_sequence_content_change_and_restart_rollback_refused(tmp_path):
    path, target, manifest, (_, _, cloud) = fixture(tmp_path)
    original = copy.deepcopy(manifest)
    config = ManagedConfiguration(path, 'gateway')
    token = config.channel_token(cloud)
    manifest['targets']['gw-one']['profile'] = 'hybrid-conservative-v1'
    target.write_text(json.dumps(manifest), encoding='utf-8')
    assert not config.valid()
    assert not config.channel_current(cloud, token)
    publish(target, manifest)
    assert config.valid()
    config.close()
    target.write_text(json.dumps(original), encoding='utf-8')
    restarted = ManagedConfiguration(path, 'gateway')
    assert not restarted.valid()
    assert restarted.management_status()['state'] == 'Unknown'
    restarted.close()


def test_rotation_allows_new_leaf_for_same_baseline_cloud_group(tmp_path):
    path, target, manifest, (first, next_fp, _) = fixture(tmp_path, 'cloud')
    config = ManagedConfiguration(path, 'cloud')
    assert config.channel_token(first)
    manifest['targets']['gw-one'].update(version=2, active_credential=next_fp,
        accepted_credentials={next_fp: None, first: (datetime.now(timezone.utc) + timedelta(seconds=.3)).isoformat()})
    publish(target, manifest)
    assert config.valid()
    assert config.channel_token(next_fp)
    assert config.channel_token(first)
    assert config.value['gateway_peers'][next_fp]['gateway_id'] == 'gw-one'
    time.sleep(.35)
    assert config.channel_token(first) is None
    assert config.channel_token(next_fp)
    config.close()


def test_gateway_rotation_reads_only_selected_leaf_and_preserves_pending_namespace(tmp_path):
    path, target, manifest, (first, next_fp, cloud) = fixture(tmp_path)
    config = ManagedConfiguration(path, 'gateway')
    old = config.channel_token(cloud)
    source = copy.deepcopy(config.value['devices'])
    manifest['targets']['gw-one'].update(version=2, active_credential=next_fp,
                                       accepted_credentials={next_fp: None})
    # Remove peer files to exercise role-isolated mounts without modifying
    # immutable public metadata. Only the selected local leaf is read.
    original_cloud = manifest['credentials'][cloud]
    Path(original_cloud['cert_file']).unlink()
    Path(original_cloud['key_file']).unlink()
    publish(target, manifest)
    assert config.valid()
    assert config.tls['cert_file'] == manifest['credentials'][next_fp]['cert_file']
    assert not config.channel_current(cloud, old)
    assert config.value['devices'] == source
    assert config.source_allowed('dev-one', source['dev-one'])
    assert first != next_fp
    config.close()


def test_revocation_tombstone_survives_restart_and_false_republication(tmp_path):
    path, target, manifest, (first, next_fp, _) = fixture(tmp_path, 'cloud')
    config = ManagedConfiguration(path, 'cloud')
    manifest['credentials'][next_fp]['revoked'] = True
    publish(target, manifest)
    assert config.valid()  # Unrelated inactive credential does not disable the cloud.
    config.close()
    manifest['credentials'][next_fp]['revoked'] = False
    manifest['targets']['gw-one'].update(version=2, active_credential=next_fp,
                                       accepted_credentials={next_fp: None})
    publish(target, manifest)
    config = ManagedConfiguration(path, 'cloud')
    assert config.valid()
    assert config.channel_token(next_fp) is None
    assert config.channel_token(first) is None
    config.close()


def test_unrelated_group_change_and_revocation_keep_original_channel_token(tmp_path):
    path, target, manifest, (first, second, _) = fixture(tmp_path, 'cloud')
    manifest['credentials'][second]['subject_id'] = 'gw-two'
    manifest['targets']['gw-two'] = copy.deepcopy(manifest['targets']['gw-one'])
    manifest['targets']['gw-two'].update(active_credential=second, accepted_credentials={second: None})
    base = json.loads(path.read_text())
    base['gateway_peers'][second] = {'gateway_id': 'gw-two', 'devices': dict(manifest['targets']['gw-two']['devices'])}
    path.write_text(json.dumps(base))
    target.write_text(json.dumps(manifest))
    config = ManagedConfiguration(path, 'cloud')
    token = config.channel_token(first)
    assert token and config.channel_token(second)
    manifest['targets']['gw-two'].update(version=2, profile='hybrid-conservative-v1')
    publish(target, manifest)
    assert config.operation_timeout(second) == 3
    assert config.operation_timeout(first) == 5
    assert config.channel_current(first, token)
    manifest['credentials'][second]['revoked'] = True
    publish(target, manifest)
    assert config.valid()
    assert config.channel_current(first, token)
    assert config.channel_token(second) is None
    config.close()


def test_expired_cloud_lease_allows_buffer_then_disabled_device_is_refused(tmp_path):
    path, target, manifest, (_, _, cloud) = fixture(tmp_path)
    now = datetime.now(timezone.utc)
    manifest.update(issued_at=(now - timedelta(seconds=2)).isoformat(),
                    expires_at=(now - timedelta(seconds=1)).isoformat())
    target.write_text(json.dumps(manifest))
    config = ManagedConfiguration(path, 'gateway')
    spec = dict(config.value['devices']['dev-one'])
    assert not config.valid()
    assert config.channel_token(cloud) is None
    assert config.source_allowed('dev-one', spec)
    manifest['targets']['gw-one']['devices'] = {}
    publish(target, manifest)
    assert not config.source_allowed('dev-one', spec)
    config.close()


@pytest.mark.parametrize('bad_change', [
    lambda m: m['targets']['gw-one'].update(profile='classical-only'),
    lambda m: m.update(expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()),
    lambda m: m['targets']['gw-one']['devices'].update({'dev-new': str(uuid.uuid4())}),
])
def test_invalid_or_unprovisioned_policy_fails_closed(tmp_path, bad_change):
    path, target, manifest, (_, _, cloud) = fixture(tmp_path)
    config = ManagedConfiguration(path, 'gateway')
    token = config.channel_token(cloud)
    bad_change(manifest)
    publish(target, manifest)
    assert not config.valid()
    assert not config.channel_current(cloud, token)
    assert not config.source_allowed('dev-one', config.value['devices']['dev-one'])
    config.close()


def test_own_der_metadata_and_immutable_base_are_checked(tmp_path):
    path, target, manifest, (first, next_fp, _) = fixture(tmp_path)
    # A valid file carrying a different actual leaf cannot impersonate this fingerprint.
    manifest['credentials'][first]['cert_file'] = manifest['credentials'][next_fp]['cert_file']
    target.write_text(json.dumps(manifest))
    config = ManagedConfiguration(path, 'gateway')
    assert not config.valid()
    config.close()
    # Use a clean guard directory because the wrong immutable reference was seen.
    base = json.loads(path.read_text())
    base['state_dir'] = str(tmp_path / 'new-state')
    base['tls']['cert_file'] = str(tmp_path / 'gw-one.pem')
    manifest['credentials'][first]['cert_file'] = base['tls']['cert_file']
    target.write_text(json.dumps(manifest)); path.write_text(json.dumps(base))
    config = ManagedConfiguration(path, 'gateway')
    assert config.valid()
    base['health_token'] = 'z' * 32
    path.write_text(json.dumps(base))
    assert not config.valid()
    config.close()


def test_lease_renewal_does_not_change_token_or_claim_effective(tmp_path):
    path, target, manifest, (_, _, cloud) = fixture(tmp_path)
    config = ManagedConfiguration(path, 'gateway')
    token = config.channel_token(cloud)
    manifest['expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=80)).isoformat()
    publish(target, manifest)
    assert config.channel_current(cloud, token)
    assert config.management_status()['state'] == 'Pending'
    assert config.management_status()['desired_version'] == 1
    config.close()


def test_captured_old_context_leaf_cannot_receive_token_for_rotated_leaf(tmp_path):
    path, target, manifest, (first, next_fp, cloud) = fixture(tmp_path)
    config = ManagedConfiguration(path, 'gateway')
    before = config.channel_token(cloud, local_fingerprint=first)
    assert before
    manifest['targets']['gw-one'].update(version=2, active_credential=next_fp,
                                       accepted_credentials={next_fp: None})
    publish(target, manifest)
    assert config.channel_token(cloud, local_fingerprint=first) is None
    after = config.channel_token(cloud, local_fingerprint=next_fp)
    assert after and after != before
    assert config.channel_current(cloud, after)
    assert not config.channel_current(cloud, before)
    config.close()
