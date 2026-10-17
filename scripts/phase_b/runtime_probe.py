"""Additional real-service expiry/identity/retry regressions in an owned lab.

Uses the unchanged service entry points. Certificate issuance and policy edits
are explicit synthetic operator fixtures, not a lifecycle-management feature.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
import uuid

from docker_probe import Lab, write_json, validate_runtime


def update(lab, role, change):
    path = lab.root / (role + '.json')
    document = json.loads(path.read_text())
    change(document)
    write_json(path, document)


def renew(lab):
    end = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    for role in ('cloud', 'gateway'):
        update(lab, role, lambda doc: doc.update(policy_expires_at=end))


def source(lab, sequence):
    key = json.loads((lab.root / 'gateway.json').read_text())['devices']['dev-lab']['key_hex']
    program = '''import socket,json,time
from common import crypto,protocol
from device.sensor import generate_reading,reading_to_bytes
key=bytes.fromhex(KEY)
hello=crypto.build_hello('dev-lab',[protocol.CAP_CHACHA20_POLY1305],key)
reading=generate_reading('dev-lab',SEQUENCE)
message={'type':protocol.MSG_LEGACY_READING,'device_id':'dev-lab','seq':SEQUENCE,**crypto.encrypt_legacy_payload(key,reading_to_bytes(reading),protocol.legacy_message_aad('dev-lab',SEQUENCE))}
with socket.create_connection(('gateway',5001),timeout=3) as s:
 s.sendall(protocol.encode_message(hello)+protocol.encode_message(message))
print(json.dumps({'sent_sequence':SEQUENCE}))
'''.replace('KEY', repr(key)).replace('SEQUENCE', str(sequence))
    return lab.probe(program)


def wait_delivery(lab, count):
    lab.wait(lambda: lab.http('gateway')['storage']['acknowledged_total'] == count,
             seconds=65)
    status = lab.http('gateway')
    assert status['storage']['pending'] == 0
    assert lab.http('cloud')['storage']['committed_total'] == count
    return status


def short_cloud_certificate(lab, seconds):
    # A separate bounded fixture container gets this run's synthetic issuer.
    # The application continues to get only its own read-only leaf mount.
    program = '''from cryptography import x509
from cryptography.hazmat.primitives import serialization,hashes
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
r=Path('/lab/credentials')
ca=x509.load_pem_x509_certificate((r/'ca.crt').read_bytes())
issuer=serialization.load_pem_private_key((r/'ca.key').read_bytes(),password=None)
old=x509.load_pem_x509_certificate((r/'cloud.crt').read_bytes())
now=datetime.now(timezone.utc)
builder=x509.CertificateBuilder().subject_name(old.subject).issuer_name(ca.subject).public_key(old.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(seconds=3)).not_valid_after(now+timedelta(seconds=SECONDS))
for ext in old.extensions:builder=builder.add_extension(ext.value,ext.critical)
cert=builder.sign(issuer,hashes.SHA256())
(r/'cloud-short.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print(json.dumps({'not_after':cert.not_valid_after_utc.timestamp()}))
'''.replace('SECONDS', str(seconds))
    result = lab.run('run', '--rm', '--pull', 'never', '--label',
                     'pqc.phase_b.owner=' + lab.project, '--network', 'none',
                     '--memory', '256m', '--cpus', '.5', '--pids-limit', '64',
                     '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                     '--entrypoint', 'python',
                     '--mount', 'type=bind,source=' + str(lab.root) + ',target=/lab',
                     '-i', lab.project + ':phase-b', '-', data=program)
    shutil.copyfile(lab.root / 'credentials/cloud-short.crt',
                    lab.root / 'cloud-credentials/cloud.crt')
    return json.loads(result.stdout)['not_after']


def execute(root, cli):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'cases': [], 'runtime_root': str(root),
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'boundary': 'real unmodified services; public source/TLS/HTTP; synthetic operator config/certificate fixtures'}
    lab = Lab(root, cli)
    try:
        lab.prepare()
        report['project'] = lab.project
        report['source_sha256'] = {str(p.relative_to(root / 'source')):
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / 'source').rglob('*')) if p.is_file()}
        report['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        shutil.copyfile(__file__, root / 'runtime_probe.observed.py')
        update(lab, 'cloud', lambda doc: doc.update(limits={'cloud_rows': 1}))
        update(lab, 'gateway', lambda doc: doc['tls'].update(server_hostname='wrong-cloud.invalid'))
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud', 'gateway')
        lab.wait(lambda: lab.http('gateway'))
        source(lab, 1)
        refused = lab.wait(lambda: (value if (value := lab.http('gateway'))['metrics'].get('delivery_retry', 0) >= 2
                                   and value['storage']['pending'] == 1 else None))
        assert not refused['cloud_connected'] and not refused['ready']
        assert lab.http('cloud')['storage']['committed_total'] == 0
        report['cases'].append({'name': 'invalid_cloud_hostname_rejected_authorized_event_retained',
                                'passed': True, 'gateway': refused})
        lab.compose('stop', '--timeout', '3', 'gateway')
        update(lab, 'gateway', lambda doc: doc['tls'].update(server_hostname='cloud'))
        renew(lab)
        lab.compose('start', 'gateway')
        wait_delivery(lab, 1)
        report['cases'].append({'name': 'explicit_cloud_identity_configuration_recovery', 'passed': True})

        # Committed cloud quota refuses the next valid event after successful
        # TLS. Repeated app failures must back off despite fresh handshakes.
        source(lab, 2)
        collector = '''import urllib.request,json,time
url='http://127.0.0.1:8001/health'
request=urllib.request.Request(url,headers={'Authorization':'Bearer '+TOKEN})
seen=None; changes=[];end=time.monotonic()+19
while time.monotonic()<end:
 value=json.load(urllib.request.urlopen(request,timeout=2))
 count=value['metrics'].get('delivery_retry',0)
 if count!=seen:changes.append({'elapsed':time.monotonic(), 'retry':count,'sessions':value['metrics'].get('cloud_sessions',0)});seen=count
 time.sleep(.1)
print(json.dumps({'changes':changes,'health':value}))
'''.replace('TOKEN', repr(lab.health_token))
        timing = json.loads(lab.compose('exec', '-T', 'gateway', 'python', '-c', collector, timeout=25).stdout)
        transitions = timing['changes'][1:]  # Initial snapshot is not an attempt timestamp.
        intervals = [b['elapsed'] - a['elapsed'] for a, b in zip(transitions, transitions[1:])]
        assert len(intervals) >= 2, timing
        assert intervals[-1] >= 3 and intervals[-1] > intervals[0] * 1.35, timing
        assert all(b['retry'] == a['retry'] + 1 for a, b in zip(transitions, transitions[1:])), timing
        assert timing['health']['storage']['pending'] == 1
        assert lab.http('cloud')['storage']['committed_total'] == 1
        report['cases'].append({'name': 'application_refusal_exponential_backoff_despite_new_tls_sessions',
                                'passed': True, 'interval_seconds': intervals, 'observation': timing})
        lab.compose('stop', '--timeout', '3', 'cloud')
        update(lab, 'cloud', lambda doc: doc.pop('limits'))
        renew(lab)
        lab.compose('start', 'cloud')
        wait_delivery(lab, 2)

        # Stop normal gateway so the valid probe owns the sole enrolled peer
        # channel. Continuous fragments cannot extend the cloud lease.
        lab.compose('stop', '--timeout', '3', 'gateway')
        expiry = time.time() + 5
        update(lab, 'cloud', lambda doc: doc.update(policy_expires_at=datetime.fromtimestamp(expiry, timezone.utc).isoformat()))
        trickle = '''from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
from common import secure_transport as transport
import socket,time,json,ssl
r='/run/lab/credentials/'
context=transport.client_context({'ca_file':r+'ca.crt','cert_file':r+'gateway.crt','key_file':r+'gateway.key','server_hostname':'cloud'})
with socket.create_connection(('cloud',5443),timeout=3) as raw:
 with context.wrap_socket(raw,server_hostname='cloud') as channel:
  channel.settimeout(.08);started=time.time();closed=False
  channel.sendall(b'{')
  while time.time()-started<7:
   try:
    channel.sendall(b' ')
    if not channel.recv(1):closed=True;break
   except socket.timeout:pass
   except (ssl.SSLError,ConnectionError,OSError):closed=True;break
   time.sleep(.02)
  result={'closed':closed,'started':started,'closed_at':time.time(),'elapsed':time.time()-started}
assert closed,result
print(json.dumps(result))
'''
        result = lab.probe(trickle)
        assert result['elapsed'] < 5.3 and result['closed_at'] <= expiry + 1, result
        assert lab.http('cloud')['storage']['committed_total'] == 2
        report['cases'].append({'name': 'active_tls_fragment_frame_clipped_to_policy_expiry',
                                'passed': True, 'lease_expires': expiry, 'observation': result})
        renew(lab)

        # Existing connections must also close at a real certificate notAfter.
        lab.compose('stop', '--timeout', '3', 'cloud')
        cert_end = short_cloud_certificate(lab, 20)
        renew(lab)
        lab.compose('start', 'cloud', 'gateway')
        connected = lab.wait(lambda: lab.http('gateway')['cloud_connected'], seconds=12)
        assert connected
        report['short_certificate_not_after'] = cert_end
        lab.wait(lambda: (value if not (value := lab.http('cloud'))['policy_valid'] else None), seconds=25)
        expired = lab.wait(lambda: (value if not (value := lab.http('gateway'))['cloud_connected'] else None), seconds=8)
        assert not expired['ready']
        assert lab.http_status('cloud', '/live') == 200
        assert lab.http_status('cloud', '/ready', True) == 503
        source(lab, 3)
        pending = lab.wait(lambda: (value if (value := lab.http('gateway'))['storage']['pending'] == 1 else None))
        assert lab.http('cloud')['storage']['committed_total'] == 2
        report['cases'].append({'name': 'real_active_cloud_certificate_expiry_disconnects_and_retains_buffer',
                                'passed': True, 'gateway': pending, 'observed_at': time.time()})
        lab.compose('stop', '--timeout', '3', 'cloud')
        shutil.copyfile(root / 'credentials/cloud.crt', root / 'cloud-credentials/cloud.crt')
        renew(lab)
        lab.compose('start', 'cloud')
        report['final_gateway_health'] = wait_delivery(lab, 3)
        report['final_cloud_health'] = lab.http('cloud')
        report['cases'].append({'name': 'operator_certificate_restore_drains_original_event', 'passed': True})
        # An explicit synthetic registry mismatch is a nonretryable denial.
        # The gateway must retain the accepted event as an observable exception.
        lab.compose('stop', '--timeout', '3', 'cloud')
        def mismatch(document):
            for peer in document['gateway_peers'].values():
                peer['devices']['dev-lab'] = str(uuid.uuid4())
        update(lab, 'cloud', mismatch)
        renew(lab)
        lab.compose('start', 'cloud')
        source(lab, 4)
        exceptional = lab.wait(lambda: (value if (value := lab.http('gateway'))['storage']['quarantined'] == 1 else None), seconds=65)
        state = exceptional['storage']
        assert exceptional['business_delivery'] == 'exceptional' and not exceptional['ready']
        assert state['accepted_total'] == state['acknowledged_total'] + state['pending'] + state['quarantined'] == 4
        assert state['acknowledged_total'] == 3 and state['pending'] == 0
        assert lab.http('cloud')['storage']['committed_total'] == 3
        report['cases'].append({'name': 'cloud_authorization_mismatch_quarantines_and_reconciles',
                                'passed': True, 'gateway': exceptional})
        report['final_gateway_health'] = exceptional
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if lab.local_endpoint_verified:
            try:
                logs = lab.compose('logs', '--no-color', check=False)
                (root / 'application.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
            except Exception as exc:
                report['log_collection_error'] = type(exc).__name__
        report['cleanup'] = lab.cleanup()
        if not report['cleanup']['verified']:
            report['status'] = 'failed'
        write_json(root / 'runtime-result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--docker-cli')
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    result = execute(args.runtime_root, args.docker_cli)
    write_json(args.evidence, result)
    print(json.dumps({'status': result['status'], 'cases': len(result['cases']),
                      'error': result.get('error'), 'cleanup': result.get('cleanup')}))
    return result['status'] != 'passed'


if __name__ == '__main__':
    raise SystemExit(main())
