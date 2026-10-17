"""Owned, bounded, synthetic-only Docker acceptance for the opt-in secure path.

Raw synthetic credentials and logs stay in a NEW directory outside the checkout.
No host port, host network, old state, environment file or production target is used.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
OWNER = 'pqc.phase_b.owner'
BASE = 'sha256:b23cfa27684e7af4be489c0d3683e184c72e3440bc45a408bbcbd5762b42b0f4'
TLS_IMAGE = 'sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
DEVICE_OBSERVER = '''import json
from device import device,sensor
original=sensor.reading_to_bytes
def record(reading):
 print('PHASE_B_SOURCE='+json.dumps(reading,sort_keys=True),flush=True)
 return original(reading)
sensor.reading_to_bytes=record
device.main(['--device-id','dev-lab','--gateway-host','gateway','--gateway-port','5001','--interval','1','--state-dir','/var/lib/pqc'])
'''


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def validate_runtime(path):
    path = path.resolve()
    if path == REPO or REPO in path.parents or path.exists():
        raise ValueError('runtime must be a fresh directory outside checkout')


def copy_source(target):
    target.mkdir(parents=True)
    for name in ('common', 'gateway', 'cloud', 'device'):
        shutil.copytree(REPO / name, target / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (target / 'deploy/phase_b').mkdir(parents=True)
    for name in ('Dockerfile', 'tls-policy.cnf'):
        shutil.copyfile(REPO / 'deploy/phase_b' / name,
                        target / 'deploy/phase_b' / name)


CERTIFICATES = r'''
import hashlib,json,os,subprocess
from pathlib import Path
r=Path('/lab/credentials');r.mkdir(exist_ok=True)
os.environ['OPENSSL_CONF']='/dev/null'
def run(*args):
 p=subprocess.run(['openssl',*args],capture_output=True,timeout=15)
 if p.returncode:raise RuntimeError(p.stderr.decode())
 return p.stdout
for ca in ['ca','other-ca']:
 run('req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(r/(ca+'.key')),'-out',str(r/(ca+'.crt')),'-days','1','-subj','/CN=Phase B '+ca,'-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign')
hashes={}
for name,ca,purpose in [('cloud','ca','serverAuth'),('gateway','ca','clientAuth'),('unauthorized','ca','clientAuth'),('untrusted','other-ca','clientAuth')]:
 run('req','-new','-newkey','rsa:2048','-nodes','-keyout',str(r/(name+'.key')),'-out',str(r/(name+'.csr')),'-subj','/CN='+name)
 ext=r/(name+'.ext');ext.write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage='+purpose+'\n'+('subjectAltName=DNS:cloud\n' if name=='cloud' else ''))
 run('x509','-req','-in',str(r/(name+'.csr')),'-CA',str(r/(ca+'.crt')),'-CAkey',str(r/(ca+'.key')),'-CAcreateserial','-out',str(r/(name+'.crt')),'-days','1','-extfile',str(ext))
 hashes[name]=hashlib.sha256(run('x509','-in',str(r/(name+'.crt')),'-outform','DER')).hexdigest()
print(json.dumps(hashes))
'''


class Lab:
    def __init__(self, root, cli):
        self.root = root
        self.cli = cli or shutil.which('docker.exe' if os.name == 'nt' else 'docker')
        if not self.cli:
            raise ValueError('Docker native CLI not found')
        self.project = 'pqc-b-' + secrets.token_hex(8)
        self.counter = 0
        self.env = {key: value for key, value in os.environ.items()
                    if not key.upper().startswith(('DOCKER_', 'COMPOSE_'))}
        self.prefix = ['compose', '--project-name', self.project,
                       '--project-directory', str(root), '--env-file', str(root / 'empty.env'),
                       '-f', str(root / 'compose.json')]
        self.health_token = secrets.token_hex(32)
        self.local_endpoint_verified = False
        self.resource_creation_attempted = False

    def run(self, *args, timeout=25, data=None, check=True):
        self.counter += 1
        p = subprocess.run([self.cli, '--context', 'desktop-linux', *args],
                           capture_output=True, text=True, input=data, timeout=timeout,
                           encoding='utf-8', errors='replace', env=self.env, cwd=self.root)
        write_json(self.root / ('command-%03d.json' % self.counter),
                   {'arguments': list(args), 'exit_code': p.returncode,
                    'stdout': p.stdout, 'stderr': p.stderr})
        if check and p.returncode:
            raise RuntimeError('Docker command failed: command-%03d.json' % self.counter)
        return p

    def compose(self, *args, **kwargs):
        return self.run(*(self.prefix + list(args)), **kwargs)

    def http(self, role, route='/health', authenticated=True):
        port = 8001 if role == 'gateway' else 8002
        code = ('import urllib.request,json; r=urllib.request.Request(' +
                repr('http://127.0.0.1:%s%s' % (port, route)) + ',headers=' +
                repr({'Authorization': 'Bearer ' + self.health_token} if authenticated else {}) +
                '); print(json.dumps(json.load(urllib.request.urlopen(r,timeout=2))))')
        return json.loads(self.compose('exec', '-T', role, 'python', '-c', code).stdout)

    def http_status(self, role, route, authenticated=False):
        port = 8001 if role == 'gateway' else 8002
        headers = {'Authorization': 'Bearer ' + self.health_token} if authenticated else {}
        code = ('import urllib.request,urllib.error,json\ntry:\n r=urllib.request.urlopen('
                'urllib.request.Request(' + repr('http://127.0.0.1:%d%s' % (port, route)) +
                ',headers=' + repr(headers) + '),timeout=2); status=r.status\n'
                'except urllib.error.HTTPError as e:status=e.code\nprint(json.dumps(status))')
        return json.loads(self.compose('exec', '-T', role, 'python', '-c', code).stdout)

    def wait(self, fn, seconds=35):
        until = time.monotonic() + seconds
        error = None
        while time.monotonic() < until:
            try:
                value = fn()
                if value:
                    return value
            except (RuntimeError, ValueError, KeyError) as exc:
                error = type(exc).__name__
            time.sleep(.5)
        raise TimeoutError('bounded wait expired; last error=' + str(error))

    def prepare(self):
        copy_source(self.root / 'source')
        (self.root / 'empty.env').write_text('')
        info = json.loads(self.run('context', 'inspect', 'desktop-linux').stdout)[0]
        if not info['Endpoints']['docker']['Host'].startswith(('npipe://', 'unix://')):
            raise ValueError('remote Docker endpoint refused')
        self.local_endpoint_verified = True
        for image in (BASE, TLS_IMAGE):
            if self.run('image', 'inspect', image, '--format', '{{.Id}}').stdout.strip() != image:
                raise ValueError('local immutable image unavailable')
        cert_name = self.project + '-certs'
        self.cert_container = cert_name
        self.resource_creation_attempted = True
        certs = self.run('run', '--pull', 'never', '--name', cert_name,
                        '--label', OWNER + '=' + self.project, '--network', 'none',
                        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                        '--memory', '256m', '--cpus', '.5', '--pids-limit', '64',
                        '--mount', 'type=bind,source=' + str(self.root) + ',target=/lab',
                        '-i', TLS_IMAGE, 'python', '-', data=CERTIFICATES, timeout=100)
        fingerprints = json.loads(certs.stdout)
        for role in ('cloud', 'gateway'):
            credentials = self.root / (role + '-credentials')
            credentials.mkdir()
            for name in ('ca.crt', role + '.crt', role + '.key'):
                shutil.copyfile(self.root / 'credentials' / name, credentials / name)
        key, incarnation = secrets.token_hex(32), str(uuid.uuid4())
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        tls = lambda name: {'ca_file': '/run/lab/credentials/ca.crt',
                            'cert_file': '/run/lab/credentials/' + name + '.crt',
                            'key_file': '/run/lab/credentials/' + name + '.key',
                            'server_hostname': 'cloud'}
        common = {'state_dir': '/var/lib/pqc', 'health_token': self.health_token,
                  'policy_expires_at': expiry, 'listen_host': '0.0.0.0'}
        gateway = {**common, 'gateway_id': 'gw-lab',
                   'devices': {'dev-lab': {'key_hex': key, 'source_incarnation': incarnation}},
                   'cloud_host': 'cloud', 'cloud_port': 5443, 'listen_port': 5001,
                   'health_port': 8001, 'tls': tls('gateway')}
        cloud = {**common, 'gateway_peers': {fingerprints['gateway']: {
                     'gateway_id': 'gw-lab', 'devices': {'dev-lab': incarnation}}},
                 'listen_port': 5443, 'health_port': 8002, 'tls': tls('cloud')}
        write_json(self.root / 'gateway.json', gateway)
        write_json(self.root / 'cloud.json', cloud)
        labels = {OWNER: self.project}
        services = {}
        for role in ('cloud', 'gateway', 'device'):
            svc = {'image': self.project + ':phase-b', 'labels': labels,
                   'environment': {'PYTHONUNBUFFERED': '1'}, 'read_only': True,
                   'tmpfs': ['/tmp:rw,noexec,nosuid,size=8388608'],
                   'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges'],
                   'pids_limit': 64, 'cpus': .5, 'mem_limit': '256m',
                   'logging': {'driver': 'json-file', 'options': {'max-size': '8m', 'max-file': '2'}}}
            if role in ('cloud', 'gateway'):
                svc['command'] = [role, '--config', '/run/lab/' + role + '.json']
                svc['volumes'] = [role + '_state:/var/lib/pqc',
                    str(self.root / (role + '.json')) + ':/run/lab/' + role + '.json:ro',
                    str(self.root / (role + '-credentials')) + ':/run/lab/credentials:ro']
            else:
                svc['entrypoint'] = ['python', '-u', '-c']
                svc['command'] = [DEVICE_OBSERVER]
                svc['environment']['DEVICE_KEY_HEX'] = key
                svc['volumes'] = ['device_state:/var/lib/pqc']
            services[role] = svc
        base_tag = self.project + '-verified-base:phase-b'
        self.run('tag', BASE, base_tag)
        if self.run('image', 'inspect', base_tag, '--format', '{{.Id}}').stdout.strip() != BASE:
            raise ValueError('local base tag verification failed')
        services['cloud']['build'] = {'context': './source', 'dockerfile': 'deploy/phase_b/Dockerfile',
                                    'network': 'none', 'args': {'BASE_IMAGE': base_tag}}
        services['probe'] = {'image': self.project + ':phase-b', 'labels': labels,
            'profiles': ['probe'], 'entrypoint': ['python'], 'read_only': True,
            'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges'],
            'pids_limit': 64, 'cpus': .5, 'mem_limit': '256m',
            'volumes': [str(self.root / 'credentials') + ':/run/lab/credentials:ro'],
            'logging': {'driver': 'json-file', 'options': {'max-size': '8m', 'max-file': '2'}}}
        write_json(self.root / 'compose.json', {'name': self.project, 'services': services,
            'networks': {'default': {'internal': True, 'labels': labels}},
            'volumes': {role + '_state': {'labels': labels} for role in ('cloud', 'gateway', 'device')}})
        self.fingerprints = fingerprints
        self.compose('config', '--quiet')
        self.compose('build', '--pull=false', 'cloud', timeout=100)

    def probe(self, code):
        value = self.compose('run', '--rm', '-T', '--no-deps', '--pull', 'never',
                             'probe', '-c', code, timeout=15)
        return json.loads(value.stdout)

    def tls_negative(self, mode, event):
        # The probe only connects to this run's cloud service on an internal network.
        code = r'''
import json,socket,ssl,subprocess
from pathlib import Path
mode=MODE
event=EVENT
import base64,hashlib
raw=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
from common.delivery import event_upload
request=json.dumps(event_upload(raw),sort_keys=True,separators=(',',':')).encode()+b'\n'
r='/run/lab/credentials/'
reply=b'';reason=None
try:
 if mode=='plaintext':
  with socket.create_connection(('cloud',5443),timeout=3) as s:
   s.sendall(request);reply=s.recv(4096)
 elif mode=='classical':
  p=subprocess.run(['openssl','s_client','-connect','cloud:5443','-servername','cloud','-CAfile',r+'ca.crt','-cert',r+'gateway.crt','-key',r+'gateway.key','-tls1_3','-groups','X25519','-brief'],input=request,capture_output=True,timeout=5)
  reason=p.stderr.decode();reply=p.stdout
  assert p.returncode!=0
 else:
  c=ssl.create_default_context(cafile=r+'ca.crt');c.minimum_version=c.maximum_version=ssl.TLSVersion.TLSv1_3
  if mode!='no_certificate':c.load_cert_chain(r+mode+'.crt',r+mode+'.key')
  with socket.create_connection(('cloud',5443),timeout=3) as raw:
   with c.wrap_socket(raw,server_hostname='cloud') as s:
    s.sendall(request);reply=s.recv(4096)
except (ssl.SSLError,ConnectionError,OSError) as e:reason=type(e).__name__
assert not reply,repr(reply)
print(json.dumps({'rejected':True,'reason':reason,'application_bytes':len(reply)}))
'''.replace('MODE', repr(mode)).replace('EVENT', repr(event))
        return self.probe(code)

    def upload(self, event, *, mode='duplicate'):
        code = r'''
from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
import json,socket
from common import delivery,secure_transport
event=EVENT
mode=MODE
if mode=='conflict':event['payload']['temperature_c']+=1
if mode=='unauthorized_device':event['device_id']='dev-not-enrolled'
raw=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
tls={'ca_file':'/run/lab/credentials/ca.crt','cert_file':'/run/lab/credentials/gateway.crt','key_file':'/run/lab/credentials/gateway.key','server_hostname':'cloud'}
context=secure_transport.client_context(tls)
ack=None;reason=None
try:
 with socket.create_connection(('cloud',5443),timeout=3) as connection:
  with context.wrap_socket(connection,server_hostname='cloud') as s:
   secure_transport.send_frame(s,delivery.event_upload(raw))
   with s.makefile('rb') as stream:ack=secure_transport.read_frame(stream)
except (ValueError,OSError) as exc:reason=type(exc).__name__
if mode=='duplicate':assert delivery.matching_ack(raw,ack)
else:assert ack is None or ack.get('status')!='committed'
print(json.dumps({'mode':mode,'ack':ack,'reason':reason}))
'''.replace('EVENT', repr(event)).replace('MODE', repr(mode))
        return self.probe(code)

    def coalesced_source(self, sequences):
        """One public source write containing HELLO and readings, then silence."""
        config = json.loads((self.root / 'gateway.json').read_text())
        code = r'''
import json,socket,time,urllib.request
from common import crypto,protocol
from device.sensor import generate_reading,reading_to_bytes
key=bytes.fromhex(KEY)
sequences=SEQUENCES
frames=[protocol.encode_message(crypto.build_hello('dev-lab',[protocol.CAP_CHACHA20_POLY1305],key))]
sources=[]
def health():
 request=urllib.request.Request('http://127.0.0.1:8001/health',headers={'Authorization':'Bearer '+TOKEN})
 return json.load(urllib.request.urlopen(request,timeout=2))
accepted_before=health()['storage']['accepted_total']
for sequence in sequences:
 reading=generate_reading('dev-lab',sequence);sources.append(reading)
 envelope=crypto.encrypt_legacy_payload(key,reading_to_bytes(reading),protocol.legacy_message_aad('dev-lab',sequence))
 frames.append(protocol.encode_message({'type':protocol.MSG_LEGACY_READING,'device_id':'dev-lab','seq':sequence,**envelope}))
with socket.create_connection(('gateway',5001),timeout=3) as connection:
 connection.sendall(b''.join(frames))
 # No second send/shutdown: complete buffered frames must progress unaided.
 time.sleep(2)
 accepted_while_open=health()['storage']['accepted_total']
 assert accepted_while_open==accepted_before+len(sequences),(accepted_before,accepted_while_open)
print(json.dumps({'source_readings':sources,'socket_writes':1,'silent_seconds':2,'accepted_before':accepted_before,'accepted_while_open':accepted_while_open}))
'''.replace('KEY', repr(config['devices']['dev-lab']['key_hex'])).replace('SEQUENCES', repr(list(sequences))).replace('TOKEN', repr(self.health_token))
        return json.loads(self.compose('exec', '-T', 'gateway', 'python', '-c', code, timeout=10).stdout)

    def cleanup(self):
        errors, removed = [], []
        if not self.resource_creation_attempted:
            return {'verified': True, 'errors': [], 'remaining': {}, 'removed': [],
                    'reason': 'No container, network or volume creation attempted'}
        # Ownership is verified for each object before any removal. The cert
        # container is not a Compose service but carries the same private label.
        for kind, args in (('container', ['ps', '-aq']),
                           ('network', ['network', 'ls', '-q']),
                           ('volume', ['volume', 'ls', '-q'])):
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
        remaining = {}
        for kind, args in (('containers', ['ps', '-aq']), ('networks', ['network', 'ls', '-q']),
                           ('volumes', ['volume', 'ls', '-q'])):
            try:
                ids = set(self.run(*args, '--filter', 'label=' + OWNER + '=' + self.project).stdout.split())
                ids.update(self.run(*args, '--filter', 'label=com.docker.compose.project=' + self.project).stdout.split())
                remaining[kind] = sorted(ids)
            except Exception as exc:
                errors.append({'kind': kind, 'error': str(exc)})
        return {'verified': not errors and not any(remaining.values()),
                'errors': errors, 'remaining': remaining, 'removed': removed,
                'image_policy': 'unique acceptance image retained; cached bases unchanged'}


def execute(root, docker_cli=None):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'runtime_root': str(root), 'cases': [],
              'started_utc': datetime.now(timezone.utc).isoformat()}
    lab = None
    try:
        lab = Lab(root, docker_cli)
        report['project'] = lab.project
        lab.prepare()
        report['image'] = lab.compose('images', '-q', 'cloud').stdout.strip()
        report['source_sha256'] = {str(path.relative_to(root / 'source')):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / 'source').rglob('*')) if path.is_file()}
        report['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        shutil.copyfile(Path(__file__), root / 'docker_probe.observed.py')
        report['certificate_fingerprints'] = lab.fingerprints
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud', 'gateway')
        report['cloud_initial_health'] = lab.wait(lambda: lab.http('cloud'))
        report['gateway_initial_health'] = lab.wait(lambda: lab.http('gateway'))
        report['runtime'] = json.loads(lab.compose('exec', '-T', 'cloud', 'python', '-c',
            'import json,ssl,sys,platform,cryptography;print(json.dumps({"python":sys.version,"ssl":ssl.OPENSSL_VERSION,"cryptography":cryptography.__version__,"platform":platform.platform()}))').stdout)
        for role in ('cloud', 'gateway'):
            assert lab.http_status(role, '/live') == 200
            assert lab.http_status(role, '/health') in (401, 403)
        assert lab.http_status('cloud', '/readings') in (401, 403)
        report['cases'].append({'name': 'health_and_readings_require_local_bearer', 'passed': True})
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'device')
        def readings():
            data = lab.http('cloud', '/readings')
            rows = data if isinstance(data, list) else data.get('readings', [])
            return rows if len(rows) >= 3 else None
        report['first_readings'] = lab.wait(readings)
        assert all(row['gateway_id'] == 'gw-lab' and row['device_id'] == 'dev-lab'
                   for row in report['first_readings'])
        report['cases'].append({'name': 'legacy_device_to_hybrid_cloud', 'passed': True,
                                'readings': len(report['first_readings'])})
        source_log = lab.compose('logs', '--no-log-prefix', '--no-color', 'device').stdout
        source_rows = [json.loads(line.split('PHASE_B_SOURCE=', 1)[1])
                       for line in source_log.splitlines() if 'PHASE_B_SOURCE=' in line]
        for event in report['first_readings']:
            source = next(row for row in source_rows if row['sequence'] == event['source_sequence'])
            assert event['payload'] == {'temperature_c': source['temperature_c'], 'unit': source['unit']}
        report['cases'].append({'name': 'source_plaintext_matches_cloud_payload', 'passed': True})
        lab.compose('stop', '--timeout', '3', 'device')
        for mode in ('plaintext', 'classical', 'no_certificate', 'untrusted', 'unauthorized'):
            result = lab.tls_negative(mode, report['first_readings'][0])
            report['cases'].append({'name': mode + '_cloud_rejected', 'passed': True, 'result': result})
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 0)
        # The selected model admits one active connection per gateway identity.
        # Stop the actual gateway before replaying its previously committed event.
        lab.compose('stop', '--timeout', '3', 'gateway')
        committed = lab.http('cloud')['storage']['committed_total']
        for mode in ('duplicate', 'duplicate', 'conflict', 'unauthorized_device'):
            result = lab.upload(report['first_readings'][0], mode=mode)
            report['cases'].append({'name': 'upload_' + mode, 'passed': True, 'result': result})
        assert lab.http('cloud')['storage']['committed_total'] == committed
        report['cases'].append({'name': 'duplicate_conflict_and_unauthorized_no_extra_commit', 'passed': True})
        lab.compose('start', 'gateway')
        lab.wait(lambda: lab.http('gateway'))
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 0)
        lab.compose('stop', '--timeout', '3', 'cloud')
        outage_started = time.monotonic()
        lab.compose('start', 'device')
        pending = lab.wait(lambda: (data if (data := lab.http('gateway'))['storage']['pending'] >= 3 else None))
        assert lab.http_status('gateway', '/ready', authenticated=True) == 503
        lab.compose('stop', '--timeout', '3', 'device')
        count_before_restart = pending['storage']['pending']
        lab.compose('restart', '--timeout', '3', 'gateway')
        restarted = lab.wait(lambda: lab.http('gateway'))
        assert restarted['storage']['pending'] >= count_before_restart
        report['cases'].append({'name': 'outage_queue_survives_gateway_restart', 'passed': True,
                                'pending_before': count_before_restart,
                                'pending_after': restarted['storage']['pending']})
        lab.compose('start', 'cloud')
        recovery_started = time.monotonic()
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        recovered = lab.http('cloud', '/readings')
        assert len(recovered) > committed
        assert len({(event['gateway_id'], event['event_id']) for event in recovered}) == len(recovered)
        report['cases'].append({'name': 'outage_restart_recovery_without_duplicate_business_rows',
            'passed': True, 'outage_seconds': round(recovery_started - outage_started, 3),
            'drain_seconds': round(time.monotonic() - recovery_started, 3),
            'committed_after': len(recovered)})
        # Lowering the admitted row count is an explicit laboratory profile;
        # existing accepted events have drained before this operator change.
        lab.compose('stop', '--timeout', '3', 'cloud', 'gateway')
        gateway_config = json.loads((root / 'gateway.json').read_text())
        gateway_config['limits'] = {'queue_rows': 3}
        write_json(root / 'gateway.json', gateway_config)
        lab.compose('start', 'gateway')
        before_capacity = lab.wait(lambda: lab.http('gateway'))
        lab.compose('start', 'device')
        full = lab.wait(lambda: (data if (data := lab.http('gateway'))['storage']['pending'] == 3
                               and data['storage']['refused'] >= 1 else None))
        lab.compose('stop', '--timeout', '3', 'device')
        assert full['storage']['accepted_total'] - before_capacity['storage']['accepted_total'] == 3
        assert full['metrics'].get('source_refused_queue_row_quota', 0) >= 1
        assert full['loss_count_unknown'] is True
        assert full['business_delivery'] == 'backlog'
        assert lab.http_status('gateway', '/ready', authenticated=True) == 503
        report['cases'].append({'name': 'bounded_queue_refuses_without_acceptance', 'passed': True,
                               'pending': 3, 'refused': full['storage']['refused']})
        lab.compose('start', 'cloud')
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        report['cases'].append({'name': 'accepted_queue_preserved_through_capacity_recovery', 'passed': True})
        # Resume with greater sequences than any source write, including refused
        # writes. This uses a public authenticated source socket and real crypto.
        source_log = lab.compose('logs', '--no-log-prefix', '--no-color', 'device').stdout
        sequences = [json.loads(line.split('PHASE_B_SOURCE=', 1)[1])['sequence']
                     for line in source_log.splitlines() if 'PHASE_B_SOURCE=' in line]
        first_sequence = max(sequences) + 1
        coalesced = lab.coalesced_source((first_sequence, first_sequence + 1))
        rows = lab.wait(lambda: (rows if all(any(row['source_sequence'] == seq for row in rows)
                        for seq in (first_sequence, first_sequence + 1)) else None)
                        if isinstance(rows := lab.http('cloud', '/readings'), list) else None)
        for source in coalesced['source_readings']:
            event = next(row for row in rows if row['source_sequence'] == source['sequence'])
            assert event['payload'] == {'temperature_c': source['temperature_c'], 'unit': source['unit']}
        report['cases'].append({'name': 'coalesced_hello_two_readings_one_write_no_followup',
                                'passed': True, **coalesced})
        delivered = lab.wait(lambda: (data if (data := lab.http('gateway'))['business_delivery'] == 'delivered'
                                     and data['storage']['pending'] == 0 else None))
        assert delivered['last_matching_ack_at']
        assert delivered['ready'] is True
        assert lab.http_status('gateway', '/ready', authenticated=True) == 200
        report['cases'].append({'name': 'business_delivery_and_reasoned_refusal_are_observable',
                               'passed': True, 'capacity_health': full, 'recovered_health': delivered})
        report['final_cloud_health'] = lab.http('cloud')
        report['final_gateway_health'] = lab.http('gateway')
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
                      'cases': report['cases'], 'cleanup': report.get('cleanup'),
                      'error': report.get('error')}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
