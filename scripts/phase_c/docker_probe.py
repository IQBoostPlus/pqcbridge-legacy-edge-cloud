"""Owned two-group managed-service Docker acceptance using synthetic identities.

Only fresh external directories, cached images, an internal network and labelled
resources are admitted. The trusted offline administrator alone mounts issuer
keys; service mounts contain their own private leaves and public metadata.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location('phase_b_owned_lab', REPO / 'scripts/phase_b/docker_probe.py')
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
OWNER = 'pqc.phase_c.owner'
write_json = _base.write_json
copy_source = _base.copy_source


def validate_runtime(path):
    if not path.is_absolute():
        raise ValueError('runtime must be absolute')
    _base.validate_runtime(path)


INITIALIZE = r'''
import json,shutil,stat
from pathlib import Path
from common.credentials import create_issuer,issue_certificate
from common.management import ManagementStore
r=Path('/lab'); issuer=r/'issuer'; create_issuer(issuer)
spec=json.loads((r/'provisions.json').read_text())
descriptors={}
for name,role,subject,lifetime in [('cloud-a','cloud','cloud',86400),('gw-a','gateway','gw-lab',86400),('gw-b','gateway','gw-lab',86400),('gw-missing','gateway','gw-lab',86400),('gw-short','gateway','gw-lab',25),('gw-two','gateway','gw-two',86400)]:
 # The short leaf is issued when the expiry case starts, not during image setup.
 if name=='gw-short':continue
 d=issue_certificate(issuer,r/'issued'/name,role,subject,lifetime_seconds=lifetime)
 for owner in ['cloud','gateway','gateway_two','probe']:
  dest=r/(owner+'-credentials')/name;dest.mkdir(parents=True)
  shutil.copyfile(d['cert_file'],dest/'cert.pem')
  permitted=(owner=='cloud' and role=='cloud') or (owner=='gateway' and subject=='gw-lab' and name!='gw-missing') or (owner=='gateway_two' and subject=='gw-two') or (owner=='probe' and subject=='gw-lab')
  if permitted:shutil.copyfile(d['key_file'],dest/'key.pem');(dest/'key.pem').chmod(0o600)
 d['cert_file']='/run/lab/credentials/'+name+'/cert.pem'
 d['key_file']='/run/lab/credentials/'+name+'/key.pem'
 descriptors[name]=d
for owner in ['cloud','gateway','gateway_two','probe']:
 shutil.copyfile(issuer/'cert.pem',r/(owner+'-credentials')/'ca.pem')
store=ManagementStore(r/'catalog')
for gw,dev in [('gw-lab','dev-lab'),('gw-two','dev-two')]:
 store.enroll_gateway(gw,'lab-operator')
 store.enroll_device(dev,gw,spec[gw]['incarnation'],'/run/lab/source/'+dev,'lab-operator')
for descriptor in descriptors.values():store.register_credential(descriptor['fingerprint'],descriptor,'lab-operator')
for gw,name in [('gw-lab','gw-a'),('gw-two','gw-two')]:
 v=store.create_version(gw,'hybrid-standard-v1',descriptors[name]['fingerprint'],'lab-operator')
 store.begin_apply(gw,v,'lab-operator')
store.export(r/'control'/'manifest.json',descriptors['cloud-a']['fingerprint'])
store.close()
(r/'descriptors.json').write_text(json.dumps(descriptors))
# Windows bind-mount modes are not Linux storage-mode evidence. Exercise the
# same public issuer API on the container's private Linux tmpfs separately.
local=Path('/tmp/issuer-mode');create_issuer(local)
leaf=issue_certificate(local,Path('/tmp/leaf-mode'),'gateway','gw-mode',lifetime_seconds=60)
assert stat.S_IMODE((local/'key.pem').stat().st_mode)==0o600
assert stat.S_IMODE(local.stat().st_mode)==0o700
assert stat.S_IMODE(Path(leaf['key_file']).stat().st_mode)==0o600
assert stat.S_IMODE(Path(leaf['key_file']).parent.stat().st_mode)==0o700
print(json.dumps({'descriptors':descriptors,'issuer_permissions':'Linux tmpfs issuer+leaf directory0700/key0600; Windows bind artifacts have host ACL semantics'}))
'''


class Lab(_base.Lab):
    def __init__(self, root, cli):
        super().__init__(root, cli)
        self.project = 'pqc-c-' + secrets.token_hex(8)
        self.prefix = ['compose', '--project-name', self.project,
                       '--project-directory', str(root), '--env-file', str(root / 'empty.env'),
                       '-f', str(root / 'compose.json')]
        self.sequences = {'gateway': 0, 'gateway_two': 0}

    def admin(self, code, timeout=25):
        p = self.compose('run', '--rm', '-T', '--no-deps', '--pull', 'never',
                         'admin', '-c', code, timeout=timeout)
        return json.loads(p.stdout)

    def operation(self, operation, **fields):
        request = {'operation': operation, 'operator': 'lab-operator', **fields}
        request_path = self.root / 'request.json'
        write_json(request_path, request)
        p = self.compose('run', '--rm', '-T', '--no-deps', '--pull', 'never', 'admin',
                         '-m', 'common.management', '--state-dir', '/lab/catalog',
                         '--request-file', '/lab/request.json', check=False)
        result = json.loads(p.stdout)
        if p.returncode or not result['ok']:
            raise RuntimeError('management CLI refused: ' + result.get('error', 'unknown'))
        return result['result']

    def api(self, expression):
        return self.admin("from common.management import ManagementStore\nimport json\ns=ManagementStore('/lab/catalog')\ntry:\n result=" +
                          expression + "\n print(json.dumps(result))\nfinally:s.close()")

    def publish(self, lease=300):
        return self.operation('export', path='/lab/control/manifest.json',
                              cloud_credential=self.fingerprints['cloud-a'], lease_seconds=lease)

    def version(self, profile, leaf, overlap=None):
        fields = dict(gateway_id='gw-lab', profile=profile, active_credential=self.fingerprints[leaf])
        if overlap is not None:
            fields['accepted_credentials'] = overlap
        version = self.operation('create_version', **fields)
        self.operation('begin_apply', gateway_id='gw-lab', version=version)
        return version

    def observe(self, role='gateway'):
        health = self.http(role)
        gateway_id = 'gw-lab' if role == 'gateway' else 'gw-two'
        evidence = {key: health[key] for key in ('cloud_connected', 'business_delivery',
            'last_matching_ack_at', 'management_state', 'management_applied_at')}
        evidence.update(gateway_id=gateway_id, management_version=health['management_version'],
                        observed_at=datetime.now(timezone.utc).isoformat())
        return self.operation('observe', gateway_id=gateway_id, version=health['management_version'], evidence=evidence)

    def issue(self, name, lifetime=86400):
        code = r'''
import json,shutil
from pathlib import Path
from common.credentials import issue_certificate
from common.management import ManagementStore
r=Path('/lab');name=NAME
d=issue_certificate(r/'issuer',r/'issued'/name,'gateway','gw-lab',lifetime_seconds=LIFETIME)
for owner in ['cloud','gateway','gateway_two','probe']:
 dest=r/(owner+'-credentials')/name;dest.mkdir()
 shutil.copyfile(d['cert_file'],dest/'cert.pem')
 if owner in ['gateway','probe']:
  shutil.copyfile(d['key_file'],dest/'key.pem');(dest/'key.pem').chmod(0o600)
d['cert_file']='/run/lab/credentials/'+name+'/cert.pem';d['key_file']='/run/lab/credentials/'+name+'/key.pem'
s=ManagementStore(r/'catalog')
try:s.register_credential(d['fingerprint'],d,'lab-operator')
finally:s.close()
print(json.dumps(d))
'''.replace('NAME', repr(name)).replace('LIFETIME', str(lifetime))
        descriptor = self.admin(code)
        self.descriptors[name] = descriptor
        self.fingerprints[name] = descriptor['fingerprint']
        return descriptor

    def pending(self):
        code = "from common.delivery import GatewayQueue,decode_event\nimport json\ns=GatewayQueue('/var/lib/pqc')\ntry:print(json.dumps([decode_event(raw) for raw in s.pending(limit=100)]))\nfinally:s.close()"
        return json.loads(self.compose('exec', '-T', 'gateway', 'python', '-c', code).stdout)

    def hold_source(self):
        self.sequences['gateway'] += 1
        sequence = self.sequences['gateway']
        code = r'''
import json,socket,time
from datetime import datetime,timezone
from pathlib import Path
from common import crypto,protocol
from device.sensor import generate_reading,reading_to_bytes
key=bytes.fromhex(KEY);seq=SEQUENCE;dev='dev-lab'
reading=generate_reading(dev,seq)
hello=protocol.encode_message(crypto.build_hello(dev,[protocol.CAP_CHACHA20_POLY1305],key))
envelope=crypto.encrypt_legacy_payload(key,reading_to_bytes(reading),protocol.legacy_message_aad(dev,seq))
frame=protocol.encode_message({'type':protocol.MSG_LEGACY_READING,'device_id':dev,'seq':seq,**envelope})
result={'source':reading,'closed':False};started=time.monotonic()
try:
 with socket.create_connection(('127.0.0.1',5001),timeout=3) as s:
  s.sendall(hello+frame);s.settimeout(15);result['closed']=s.recv(1)==b''
except (ConnectionError,OSError) as exc:result['error']=type(exc).__name__
result['elapsed_seconds']=time.monotonic()-started
result['closed_at']=datetime.now(timezone.utc).isoformat()
Path('/tmp/held-source.json').write_text(json.dumps(result))
'''.replace('KEY', repr(self.provisions['gw-lab']['key'])).replace('SEQUENCE', str(sequence))
        self.compose('exec', '-d', 'gateway', 'python', '-c', code)
        return sequence

    def http(self, role, route='/health', authenticated=True):
        # Both gateway containers deliberately use their own loopback:8001.
        if role != 'gateway_two':
            return super().http(role, route, authenticated)
        code = ('import urllib.request,json; r=urllib.request.Request(' +
                repr('http://127.0.0.1:8001' + route) + ',headers=' +
                repr({'Authorization': 'Bearer ' + self.health_token} if authenticated else {}) +
                '); print(json.dumps(json.load(urllib.request.urlopen(r,timeout=2))))')
        return json.loads(self.compose('exec', '-T', role, 'python', '-c', code).stdout)

    def connection(self, role):
        # The namespace's kernel socket table is independent of application state.
        code = "import json;print(json.dumps(sorted(line.split()[1:4] for line in open('/proc/net/tcp').read().splitlines()[1:] if line.split()[2].endswith(':1543') and line.split()[3]=='01')))"
        return json.loads(self.compose('exec', '-T', role, 'python', '-c', code).stdout)

    def source(self, role='gateway'):
        self.sequences[role] += 1
        sequence = self.sequences[role]
        gateway_id, device = ('gw-lab', 'dev-lab') if role == 'gateway' else ('gw-two', 'dev-two')
        key = self.provisions[gateway_id]['key']
        code = r'''
import json,socket,time
from common import crypto,protocol
from device.sensor import generate_reading,reading_to_bytes
key=bytes.fromhex(KEY);dev=DEVICE;seq=SEQUENCE
reading=generate_reading(dev,seq)
hello=protocol.encode_message(crypto.build_hello(dev,[protocol.CAP_CHACHA20_POLY1305],key))
envelope=crypto.encrypt_legacy_payload(key,reading_to_bytes(reading),protocol.legacy_message_aad(dev,seq))
frame=protocol.encode_message({'type':protocol.MSG_LEGACY_READING,'device_id':dev,'seq':seq,**envelope})
with socket.create_connection(('127.0.0.1',5001),timeout=3) as s:
 s.sendall(hello+frame);time.sleep(.3)
print(json.dumps(reading))
'''.replace('KEY', repr(key)).replace('DEVICE', repr(device)).replace('SEQUENCE', str(sequence))
        source = json.loads(self.compose('exec', '-T', role, 'python', '-c', code, timeout=10).stdout)
        return source

    def delivered(self, role='gateway', version=None):
        def check():
            health = self.http(role)
            return health if (health['cloud_connected'] and health['business_delivery'] == 'delivered'
                              and health['storage']['pending'] == 0
                              and (version is None or health['management_version'] == version)) else None
        return self.wait(check, seconds=65)

    def row_for(self, source, gateway_id='gw-lab'):
        def check():
            rows = self.http('cloud', '/readings')
            return next((row for row in rows if row['gateway_id'] == gateway_id
                         and row['source_sequence'] == source['sequence']), None)
        row = self.wait(check, seconds=65)
        assert row['payload'] == {'temperature_c': source['temperature_c'], 'unit': source['unit']}
        assert row['source_incarnation'] == self.provisions[gateway_id]['incarnation']
        return row

    def leaf_upload(self, leaf, event, accepted):
        # Duplicate the exact real committed event. No synthetic business ACK.
        code = r'''
from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
import json,socket
from common import delivery,secure_transport
event=EVENT;leaf=LEAF
raw=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
tls={'ca_file':'/run/lab/credentials/ca.pem','cert_file':'/run/lab/credentials/'+leaf+'/cert.pem','key_file':'/run/lab/credentials/'+leaf+'/key.pem','server_hostname':'cloud'}
ack=None;reason=None
try:
 with socket.create_connection(('cloud',5443),timeout=3) as c:
  with secure_transport.client_context(tls).wrap_socket(c,server_hostname='cloud') as s:
   secure_transport.send_frame(s,delivery.event_upload(raw))
   with s.makefile('rb') as stream:ack=secure_transport.read_frame(stream)
except (ValueError,OSError) as exc:reason=type(exc).__name__
matched=delivery.matching_ack(raw,ack)
assert matched is ACCEPTED,(ack,reason)
print(json.dumps({'matching_committed_ack':matched,'reason':reason}))
'''.replace('EVENT', repr(event)).replace('LEAF', repr(leaf)).replace('ACCEPTED', repr(accepted))
        return json.loads(self.compose('run', '--rm', '-T', '--no-deps', '--pull', 'never',
                                      'probe', '-c', code, timeout=15).stdout)

    def prepare(self):
        copy_source(self.root / 'source')
        (self.root / 'empty.env').write_text('')
        (self.root / 'control').mkdir()
        (self.root / 'issued').mkdir()
        self.provisions = {gateway_id: {'key': secrets.token_hex(32), 'incarnation': str(uuid.uuid4())}
                           for gateway_id in ('gw-lab', 'gw-two')}
        write_json(self.root / 'provisions.json', self.provisions)
        info = json.loads(self.run('context', 'inspect', 'desktop-linux').stdout)[0]
        if not info['Endpoints']['docker']['Host'].startswith(('npipe://', 'unix://')):
            raise ValueError('remote Docker endpoint refused')
        self.local_endpoint_verified = True
        if self.run('image', 'inspect', _base.BASE, '--format', '{{.Id}}').stdout.strip() != _base.BASE:
            raise ValueError('local immutable image unavailable')
        tag = self.project + '-verified-base:phase-c'
        self.run('tag', _base.BASE, tag)
        if self.run('image', 'inspect', tag, '--format', '{{.Id}}').stdout.strip() != _base.BASE:
            raise ValueError('local base tag verification failed')
        labels = {OWNER: self.project}
        services = {}
        for role in ('cloud', 'gateway', 'gateway_two', 'admin', 'probe'):
            svc = {'image': self.project + ':phase-c', 'labels': labels,
                'entrypoint': ['python'], 'environment': {'PYTHONUNBUFFERED': '1'},
                'read_only': True, 'tmpfs': ['/tmp:rw,noexec,nosuid,size=8388608'],
                'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges'],
                'pids_limit': 64, 'cpus': .5, 'mem_limit': '256m',
                'logging': {'driver': 'json-file', 'options': {'max-size': '8m', 'max-file': '2'}}}
            if role in ('admin', 'probe'):
                svc['profiles'] = ['operator']
                if role == 'admin':
                    svc['network_mode'] = 'none'
                    svc['volumes'] = [str(self.root) + ':/lab:rw']
                else:
                    svc['volumes'] = [str(self.root / 'probe-credentials') + ':/run/lab/credentials:ro']
            else:
                actual = 'gateway' if role == 'gateway_two' else role
                svc['command'] = ['-m', 'common.managed_bootstrap', actual, '--config', '/run/lab/' + role + '.json']
                svc['volumes'] = [role + '_state:/var/lib/pqc',
                    str(self.root / (role + '.json')) + ':/run/lab/' + role + '.json:ro',
                    str(self.root / (role + '-credentials')) + ':/run/lab/credentials:ro',
                    str(self.root / 'control') + ':/run/lab/control:ro']
            services[role] = svc
        services['admin']['build'] = {'context': './source', 'dockerfile': 'deploy/phase_b/Dockerfile',
                                     'network': 'none', 'args': {'BASE_IMAGE': tag}}
        write_json(self.root / 'compose.json', {'name': self.project, 'services': services,
            'networks': {'default': {'internal': True, 'labels': labels}},
            'volumes': {role + '_state': {'labels': labels} for role in ('cloud', 'gateway', 'gateway_two')}})
        self.compose('config', '--quiet')
        self.resource_creation_attempted = True
        self.compose('build', '--pull=false', 'admin', timeout=100)
        initialized = self.admin(INITIALIZE, timeout=100)
        self.descriptors = initialized['descriptors']
        self.permissions = initialized['issuer_permissions']
        self.fingerprints = {name: descriptor['fingerprint'] for name, descriptor in self.descriptors.items()}
        common = {'state_dir': '/var/lib/pqc', 'health_token': self.health_token,
                  'policy_expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                  'listen_host': '0.0.0.0', 'management': {'manifest_file': '/run/lab/control/manifest.json'}}
        tls = lambda name: {'ca_file': '/run/lab/credentials/ca.pem',
                            'cert_file': '/run/lab/credentials/' + name + '/cert.pem',
                            'key_file': '/run/lab/credentials/' + name + '/key.pem', 'server_hostname': 'cloud'}
        for role, gateway_id, device_id, leaf in [('gateway', 'gw-lab', 'dev-lab', 'gw-a'),
                                                  ('gateway_two', 'gw-two', 'dev-two', 'gw-two')]:
            config = {**common, 'gateway_id': gateway_id, 'devices': {device_id: {
                'key_hex': self.provisions[gateway_id]['key'],
                'source_incarnation': self.provisions[gateway_id]['incarnation']}},
                'cloud_host': 'cloud', 'cloud_port': 5443, 'listen_port': 5001,
                'health_port': 8001, 'tls': tls(leaf)}
            write_json(self.root / (role + '.json'), config)
        cloud = {**common, 'gateway_peers': {self.fingerprints[leaf]: {
            'gateway_id': gateway_id, 'devices': {device_id: self.provisions[gateway_id]['incarnation']}}
            for gateway_id, device_id, leaf in [('gw-lab', 'dev-lab', 'gw-a'), ('gw-two', 'dev-two', 'gw-two')]},
            'listen_port': 5443, 'health_port': 8002, 'tls': tls('cloud-a')}
        write_json(self.root / 'cloud.json', cloud)

    def lifecycle(self, report, rows):
        def record(name, **evidence):
            report['cases'].append(dict(name=name, passed=True, **evidence))
        def unchanged(before):
            after = self.connection('gateway_two')
            assert before and after == before, (before, after)
            source = self.source('gateway_two')
            self.row_for(source, 'gw-two')
            return self.delivered('gateway_two', 1)

        # Canary changes preserve the second group's actual live TCP connection.
        unaffected = self.connection('gateway_two')
        before_sessions = self.http('gateway_two')['metrics']['cloud_sessions']
        canary = self.version('hybrid-conservative-v1', 'gw-a')
        self.publish()
        self.wait(lambda: self.http('gateway')['management_version'] == canary)
        self.source()
        self.delivered(version=canary)
        status = self.observe()
        assert status['state'] == 'Effective'
        other = unchanged(unaffected)
        assert other['metrics']['cloud_sessions'] == before_sessions
        assert self.http('gateway')['management']['profile'] == 'hybrid-conservative-v1'
        record('live_canary_profile_post_apply_ack_and_unaffected_group', status=status,
               unaffected_tcp_tuple=unaffected, unaffected_health=other)

        # Unknown or classical profiles fail at the real trusted CLI, never publish.
        for profile in ('unknown-profile', 'classical-only'):
            try:
                self.operation('create_version', gateway_id='gw-lab', profile=profile,
                               active_credential=self.fingerprints['gw-a'])
            except RuntimeError as exc:
                assert str(exc) == 'management CLI refused: unknown_profile'
            else:
                raise AssertionError('weakened/unknown profile accepted')
        assert self.operation('status', gateway_id='gw-lab')['desired_version'] == canary
        record('unknown_and_classical_profiles_refused_by_actual_cli')

        # A missing own key blocks the canary; the second group remains connected.
        failed = self.version('hybrid-standard-v1', 'gw-missing')
        self.publish()
        unhealthy = self.wait(lambda: (h if not h['ready'] and not h['cloud_connected']
                                      and h['management_desired_version'] == failed
                                      and h['management_version'] != failed
                                      and h.get('management_failure_reason') == 'tls_configuration_refused' else None)
                              if (h := self.http('gateway')) else None)
        assert self.http('gateway_two')['policy_valid']
        unchanged(unaffected)
        failed_evidence = {'gateway_id': 'gw-lab', 'management_version': failed,
            'cloud_connected': unhealthy['cloud_connected'], 'business_delivery': unhealthy['business_delivery'],
            'last_matching_ack_at': unhealthy['last_matching_ack_at'],
            'observed_at': datetime.now(timezone.utc).isoformat()}
        failed_evidence['management_failure_reason'] = unhealthy['management_failure_reason']
        # This is an explicitly unsuccessful observation of the requested version,
        # not a claim that its channel applied successfully.
        failed_status = self.operation('observe', gateway_id='gw-lab', version=failed, evidence=failed_evidence)
        assert failed_status['state'] == 'Failed'
        assert failed_status['failure_reason'] == 'tls_configuration_refused'
        failed_audit = self.operation('audit')[-1]
        assert failed_audit['operation'] == 'observe'
        assert failed_audit['result']['failure_reason'] == 'tls_configuration_refused'
        record('missing_key_canary_fails_closed_without_disrupting_other_group',
               health=unhealthy, status=failed_status, audit=failed_audit)
        self.admin("import shutil,json;shutil.copyfile('/lab/issued/gw-missing/key.pem','/lab/gateway-credentials/gw-missing/key.pem');print(json.dumps({'installed_existing_matching_key':True}))")
        self.wait(lambda: self.http('gateway')['management_version'] == failed, seconds=65)
        self.source()
        self.delivered(version=failed)
        assert self.observe()['state'] == 'Effective'
        record('failed_rotation_recovers_with_same_already_issued_key_and_fingerprint')

        # Restore a genuinely different safe profile, rather than merely a new
        # version carrying the same profile as the repaired failed migration.
        before_rollback = self.http('gateway')['management']['profile']
        assert before_rollback == 'hybrid-standard-v1'
        rollback = self.operation('rollback', gateway_id='gw-lab', version=canary)
        rolled = self.operation('status', gateway_id='gw-lab')
        assert rolled['state'] == 'Rolled back' and rollback > failed
        assert rolled['active_credential'] == self.fingerprints['gw-missing']
        assert rolled['profile'] == 'hybrid-conservative-v1'
        self.operation('begin_apply', gateway_id='gw-lab', version=rollback)
        self.publish()
        self.wait(lambda: self.http('gateway')['management_version'] == rollback)
        self.source()
        self.delivered(version=rollback)
        assert self.http('gateway')['management']['profile'] == 'hybrid-conservative-v1'
        assert self.observe()['state'] == 'Effective'
        unchanged(unaffected)
        record('profile_rollback_new_version_retains_current_valid_credential', status=rolled,
               previous_profile=before_rollback, restored_profile='hybrid-conservative-v1')

        # A real prior runtime observation ages to Unknown in the public catalog
        # time-aware query. This does not pretend to be a five-minute runtime wait.
        fresh = self.operation('status', gateway_id='gw-lab')
        projection = datetime.fromisoformat(fresh['evidence']['observed_at'].replace('Z', '+00:00')) + timedelta(seconds=301)
        stale = self.api("s.status('gw-lab',now=" + repr(projection.isoformat()) + ')')
        assert stale['state'] == 'Unknown'
        evidence = dict(fresh['evidence'])
        evidence['observed_at'] = (datetime.now(timezone.utc) - timedelta(seconds=301)).isoformat()
        try:
            self.operation('observe', gateway_id='gw-lab', version=rollback, evidence=evidence)
        except RuntimeError as exc:
            assert str(exc) == 'management CLI refused: invalid_observation'
        else:
            raise AssertionError('stale observation accepted')
        record('stale_actual_observation_refused_and_public_status_projects_unknown',
               boundary='Public catalog supplied-time query; no five-minute runtime claim')

        deadline = datetime.now(timezone.utc) + timedelta(seconds=24)
        rotation = self.version('hybrid-standard-v1', 'gw-b', {
            self.fingerprints['gw-b']: None, self.fingerprints['gw-missing']: deadline.isoformat()})
        self.publish()
        self.wait(lambda: self.http('gateway')['management_version'] == rotation)
        rotated_source = self.source()
        rotated_row = self.row_for(rotated_source)
        self.delivered(version=rotation)
        assert self.observe()['state'] == 'Effective'
        assert self.http('gateway')['management']['local_fingerprint'] == self.fingerprints['gw-b']
        self.compose('stop', '--timeout', '3', 'gateway')
        old_before = self.leaf_upload('gw-missing', rotated_row, True)
        while datetime.now(timezone.utc) <= deadline + timedelta(seconds=1):
            time.sleep(.5)
        old_after = self.leaf_upload('gw-missing', rotated_row, False)
        self.compose('start', 'gateway')
        self.source()
        self.delivered(version=rotation)
        unchanged(unaffected)
        record('gateway_rotation_real_old_leaf_overlap_then_retirement',
               overlap_seconds=24, deadline=deadline.isoformat(), old_before=old_before, old_after=old_after)

        # Revoke a currently connected leaf; test both active and new access.
        before_revoke = self.http('cloud')['storage']['committed_total']
        pre_revocation = (self.root / 'control/manifest.json').read_bytes()
        self.operation('revoke_credential', fingerprint=self.fingerprints['gw-b'])
        self.publish()
        revoked_at = time.monotonic()
        revoked = self.wait(lambda: (h if not h['policy_valid'] and not h['cloud_connected'] else None)
                            if (h := self.http('gateway')) else None, seconds=10)
        self.wait(lambda: not self.connection('gateway'), seconds=10)
        active_elapsed = time.monotonic() - revoked_at
        new_rejected = self.leaf_upload('gw-b', rotated_row, False)
        assert self.http('cloud')['storage']['committed_total'] == before_revoke
        unchanged(unaffected)
        record('emergency_revoke_disconnects_active_and_refuses_new_leaf', elapsed_seconds=round(active_elapsed, 3),
               revoked_health=revoked, new_connection=new_rejected)

        # Deliberately restore an older trusted-control file and restart roles.
        # Persisted sequence/tombstones must refuse it without touching data state.
        (self.root / 'control/manifest.json').write_bytes(pre_revocation)
        self.compose('restart', '--timeout', '3', 'cloud', 'gateway')
        self.wait(lambda: self.http('gateway'))
        self.wait(lambda: self.http('cloud'))
        assert not self.http('gateway')['policy_valid']
        assert not self.http('cloud')['policy_valid']
        record('old_control_snapshot_refused_after_real_role_restart')
        self.publish()
        self.issue('gw-recovery')
        recovery = self.version('hybrid-standard-v1', 'gw-recovery')
        self.publish()
        self.wait(lambda: self.http('gateway')['management_version'] == recovery, seconds=65)
        self.source()
        self.delivered(version=recovery)
        assert self.observe()['state'] == 'Effective'
        self.delivered('gateway_two', 1)
        record('fresh_nonrevoked_credential_recovers_without_namespace_reset')

        accepted = self.http('gateway')['storage']['accepted_total']
        held_sequence = self.hold_source()
        self.wait(lambda: self.http('gateway')['storage']['accepted_total'] == accepted + 1)
        self.operation('set_enabled', kind='device', asset_id='dev-lab', enabled=False)
        disabled_manifest = self.publish()
        disabled_at = time.monotonic()
        def held_result():
            code = "import json;print(open('/tmp/held-source.json').read())"
            return json.loads(self.compose('exec', '-T', 'gateway', 'python', '-c', code).stdout)
        held = self.wait(held_result, seconds=12)
        assert held['closed'] is True
        closed_after_publish = (datetime.fromisoformat(held['closed_at']) -
                                datetime.fromisoformat(disabled_manifest['issued_at'].replace('Z', '+00:00'))).total_seconds()
        assert 0 <= closed_after_publish <= 6
        disabled_accepted = self.http('gateway')['storage']['accepted_total']
        self.source()
        assert self.http('gateway')['storage']['accepted_total'] == disabled_accepted
        record('device_disable_closes_existing_source_and_refuses_new_source', held_source=held,
               verification_elapsed_seconds=round(time.monotonic() - disabled_at, 3),
               active_close_after_publish_seconds=round(closed_after_publish, 3), held_sequence=held_sequence)
        self.operation('set_enabled', kind='device', asset_id='dev-lab', enabled=True)
        self.publish()
        self.source()
        self.delivered(version=recovery)

        self.operation('set_enabled', kind='gateway', asset_id='gw-lab', enabled=False)
        self.publish()
        self.wait(lambda: not self.http('gateway')['cloud_connected'])
        self.leaf_upload('gw-recovery', rotated_row, False)
        assert self.http('gateway_two')['policy_valid']
        record('gateway_disable_rejects_active_and_new_business_access')
        self.operation('set_enabled', kind='gateway', asset_id='gw-lab', enabled=True)
        self.publish()
        self.wait(lambda: self.http('gateway')['cloud_connected'], seconds=65)
        self.source()
        self.delivered(version=recovery)

        short_lease = self.publish(lease=5)
        self.wait(lambda: not self.http('gateway')['policy_valid'], seconds=10)
        assert self.http('gateway', '/live')['live'] is True
        committed = self.http('cloud')['storage']['committed_total']
        accepted_before = self.http('gateway')['storage']['accepted_total']
        buffered_source = self.source()
        self.wait(lambda: self.http('gateway')['storage']['accepted_total'] == accepted_before + 1)
        queued = self.pending()
        queued_event = next(row for row in queued if row['source_sequence'] == buffered_source['sequence'])
        assert self.http('cloud')['storage']['committed_total'] == committed
        self.publish()
        drained = self.row_for(buffered_source)
        self.delivered(version=recovery)
        assert drained == queued_event
        record('offline_lease_expiry_buffers_then_renewal_drains_exact_same_event',
               lease_seconds=5, expired_manifest=short_lease['sequence'], queued_event=queued_event, cloud_event=drained)

        short = self.issue('gw-short', lifetime=45)
        expiry_version = self.version('hybrid-standard-v1', 'gw-short')
        self.publish()
        self.wait(lambda: self.http('gateway')['management_version'] == expiry_version, seconds=35)
        expiry_source = self.source()
        expiry_row = self.row_for(expiry_source)
        self.delivered(version=expiry_version)
        assert self.observe()['state'] == 'Effective'
        cert_after = datetime.fromisoformat(short['not_after'])
        while datetime.now(timezone.utc) < cert_after:
            time.sleep(.5)
        expiry_started = time.monotonic()
        expired = self.wait(lambda: (h if not h['policy_valid'] and not h['cloud_connected'] else None)
                            if (h := self.http('gateway')) else None, seconds=10)
        self.wait(lambda: not self.connection('gateway'), seconds=10)
        self.leaf_upload('gw-short', expiry_row, False)
        assert self.http('gateway_two')['policy_valid']
        record('managed_leaf_expiry_closes_existing_and_refuses_new_channel', lifetime_seconds=45,
               not_after=short['not_after'], detection_seconds=round(time.monotonic() - expiry_started, 3), health=expired)

    def cleanup(self):
        if not self.resource_creation_attempted:
            return {'verified': True, 'errors': [], 'remaining': {}, 'removed': []}
        errors, removed, remaining = [], [], {}
        for kind, args in [('container', ['ps', '-aq']), ('network', ['network', 'ls', '-q']),
                           ('volume', ['volume', 'ls', '-q'])]:
            try:
                ids = set(self.run(*args, '--filter', 'label=' + OWNER + '=' + self.project).stdout.split())
                ids.update(self.run(*args, '--filter', 'label=com.docker.compose.project=' + self.project).stdout.split())
                for object_id in ids:
                    obj = json.loads(self.run(kind, 'inspect', object_id).stdout)[0]
                    labels = obj.get('Config', {}).get('Labels', {}) if kind == 'container' else obj.get('Labels', {})
                    if (labels or {}).get(OWNER) != self.project:
                        raise RuntimeError('ownership mismatch; removal refused')
                    self.run(*(['rm', '-f'] if kind == 'container' else [kind, 'rm']), object_id)
                    removed.append({'kind': kind, 'id': object_id})
            except Exception as exc:
                errors.append({'kind': kind, 'error': type(exc).__name__ + ': ' + str(exc)})
        for kind, args in [('containers', ['ps', '-aq']), ('networks', ['network', 'ls', '-q']),
                           ('volumes', ['volume', 'ls', '-q'])]:
            try:
                ids = set(self.run(*args, '--filter', 'label=' + OWNER + '=' + self.project).stdout.split())
                ids.update(self.run(*args, '--filter', 'label=com.docker.compose.project=' + self.project).stdout.split())
                remaining[kind] = sorted(ids)
            except Exception as exc:
                errors.append({'kind': kind, 'error': str(exc)})
        return {'verified': not errors and not any(remaining.values()), 'errors': errors,
                'remaining': remaining, 'removed': removed,
                'image_policy': 'unique acceptance image retained; cached bases unchanged'}


def execute(root, docker_cli=None):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'runtime_root': str(root), 'cases': [],
              'started_utc': datetime.now(timezone.utc).isoformat()}
    lab = None
    try:
        report['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        shutil.copyfile(Path(__file__), root / 'docker_probe.observed.py')
        lab = Lab(root, docker_cli)
        report['project'] = lab.project
        lab.prepare()
        report['source_sha256'] = {str(path.relative_to(root / 'source')):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / 'source').rglob('*')) if path.is_file()}
        report['image'] = lab.run('image', 'inspect', lab.project + ':phase-c', '--format', '{{.Id}}').stdout.strip()
        report['certificate_fingerprints'] = lab.fingerprints
        report['cases'].append({'name': 'issuer_private_key_linux_permissions_and_role_mount_isolation',
                                'passed': True, 'permissions': lab.permissions})
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud', 'gateway', 'gateway_two')
        for role in ('cloud', 'gateway', 'gateway_two'):
            lab.wait(lambda role=role: lab.http(role))
            permitted = {'cloud': {'cloud-a'}, 'gateway': {'gw-a', 'gw-b'}, 'gateway_two': {'gw-two'}}[role]
            code = "from pathlib import Path;import json;print(json.dumps(sorted(p.parent.name for p in Path('/run/lab/credentials').glob('*/key.pem'))))"
            mounted = set(json.loads(lab.compose('exec', '-T', role, 'python', '-c', code).stdout))
            assert mounted == permitted, (role, mounted)
        report['runtime'] = json.loads(lab.compose('exec', '-T', 'cloud', 'python', '-c',
            'import json,ssl,sys,platform,cryptography;print(json.dumps({"python":sys.version,"ssl":ssl.OPENSSL_VERSION,"cryptography":cryptography.__version__,"platform":platform.platform()}))').stdout)
        rows = {}
        for role, gateway_id in [('gateway', 'gw-lab'), ('gateway_two', 'gw-two')]:
            source = lab.source(role)
            rows[role] = lab.row_for(source, gateway_id)
            health = lab.delivered(role, 1)
            observed = lab.observe(role)
            assert observed['state'] == 'Effective'
            report['cases'].append({'name': role + '_real_source_delivery_post_apply_effective',
                                    'passed': True, 'event': rows[role], 'health': health,
                                    'catalog_status': observed})
        lab.lifecycle(report, rows)
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if lab:
            try:
                logs = lab.compose('logs', '--no-color', timeout=15, check=False)
                (root / 'application.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
            except Exception as exc:
                report['log_collection_error'] = str(exc)
            report['cleanup'] = lab.cleanup()
            if not report['cleanup']['verified']:
                report['status'] = 'failed'
        write_json(root / 'result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--docker-cli')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    report = execute(args.runtime_root, args.docker_cli)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.evidence, report)
    print(json.dumps({'status': report['status'], 'runtime_root': str(args.runtime_root),
                      'cases': [case['name'] for case in report['cases']],
                      'cleanup': report.get('cleanup'), 'error': report.get('error')}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
