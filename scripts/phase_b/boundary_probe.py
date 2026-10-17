"""Owned Docker checks for expiry-after-commit, HTTP shutdown and worker limits.

Only delayed_commit instruments the application: it wraps real public commit,
preserves its transaction, then delays return five seconds. Other cases run the
normal bootstrap. No original state, host ports, pulls or external targets.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from docker_probe import Lab, validate_runtime, write_json


LAUNCHER = '''import sys
sys.path.insert(0,'/app')
from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
from common import delivery,secure_runtime
import time
original=delivery.CloudStore.commit
def commit(self,event):
 ack=original(self,event)
 time.sleep(5)
 return ack
delivery.CloudStore.commit=commit
sys.argv=[sys.argv[0],*sys.argv[2:]]
raise SystemExit(secure_runtime.service_main('cloud'))
'''


def valid_upload(lab, timeout=9):
    config = json.loads((lab.root / 'gateway.json').read_text())
    code = '''from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
import json,socket,time
from common import delivery,secure_transport
from device.sensor import generate_reading
raw=delivery.canonical_event('gw-lab','dev-lab',INCARNATION,generate_reading('dev-lab',1))
tls={'ca_file':'/run/lab/credentials/ca.crt','cert_file':'/run/lab/credentials/gateway.crt','key_file':'/run/lab/credentials/gateway.key','server_hostname':'cloud'}
context=secure_transport.client_context(tls)
started=time.monotonic();reply=None;error=None
try:
 with socket.create_connection(('cloud',5443),timeout=3) as plain:
  with context.wrap_socket(plain,server_hostname='cloud') as secured:
   secured.settimeout(TIMEOUT)
   secure_transport.send_frame(secured,delivery.event_upload(raw))
   with secured.makefile('rb') as stream:reply=secure_transport.read_frame(stream)
except (OSError,ValueError) as exc:error=type(exc).__name__
print(json.dumps({'reply':reply,'error':error,'elapsed_seconds':time.monotonic()-started,'event':delivery.decode_event(raw)}))
'''.replace('INCARNATION', repr(config['devices']['dev-lab']['source_incarnation'])).replace('TIMEOUT', repr(timeout))
    return lab.probe(code)


def execute(root, cli, selected_case):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'selected_case': selected_case, 'runtime_root': str(root),
              'started_utc': datetime.now(timezone.utc).isoformat(), 'cases': []}
    lab, child = None, None
    try:
        lab = Lab(root, cli)
        lab.prepare()
        report['project'] = lab.project
        report['source_sha256'] = {str(path.relative_to(root / 'source')):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / 'source').rglob('*')) if path.is_file()}
        report['harness_sha256'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                    for name in ('boundary_probe.py', 'docker_probe.py')}
        shutil.copyfile(Path(__file__), root / 'boundary_probe.observed.py')
        control = root / 'control'
        control.mkdir()
        compose = json.loads((root / 'compose.json').read_text())
        compose['services']['cloud']['volumes'].append(str(control) + ':/run/control:rw')
        if selected_case == 'delayed_commit':
            (root / 'launcher.py').write_text(LAUNCHER, encoding='utf-8')
            compose['services']['cloud']['volumes'].append(str(root / 'launcher.py') + ':/run/launcher.py:ro')
            compose['services']['cloud']['entrypoint'] = ['python', '/run/launcher.py']
            report['instrumentation'] = 'Real public CloudStore.commit completes, then wrapper delays return five seconds'
        else:
            report['instrumentation'] = 'Unmodified application bootstrap; owned bounded socket clients only'
        write_json(root / 'compose.json', compose)
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud')
        lab.wait(lambda: lab.http('cloud'))
        if selected_case == 'delayed_commit':
            config = json.loads((root / 'cloud.json').read_text())
            config['policy_expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=4)).isoformat()
            write_json(root / 'cloud.json', config)
            observation = valid_upload(lab)
            health = lab.http('cloud')
            passed = health['storage']['committed_total'] == 1 and observation['reply'] is None
            report['cases'].append({'name': 'no_ack_after_policy_expires_during_commit', 'passed': passed,
                                    'observation': observation, 'cloud_health': health})
        elif selected_case == 'health_shutdown':
            code = '''import socket,time
from pathlib import Path
with socket.create_connection(('127.0.0.1',8002),timeout=2) as connection:
 connection.sendall(b'GET /health HTTP/1.1\\r\\nX-Lab: ')
 Path('/run/control/started').write_text('started')
 until=time.monotonic()+15
 while time.monotonic()<until:
  try:connection.sendall(b'a')
  except OSError:break
  time.sleep(.2)
'''
            container = lab.compose('ps', '-q', 'cloud').stdout.strip()
            child = subprocess.Popen([lab.cli, '--context', 'desktop-linux', 'exec', container, 'python', '-c', code],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=lab.env, cwd=root)
            lab.wait(lambda: (control / 'started').exists(), seconds=8)
            started = time.monotonic()
            lab.compose('stop', '--timeout', '7', 'cloud', timeout=12)
            elapsed = time.monotonic() - started
            state = json.loads(lab.run('inspect', '--format', '{{json .State}}', container).stdout)
            report['cases'].append({'name': 'unfinished_http_trickle_sigterm_graceful_exit',
                'passed': state['ExitCode'] == 0 and not state['OOMKilled'] and elapsed <= 6,
                'elapsed_seconds': elapsed, 'container_state': state, 'trickle_interval_seconds': .2,
                'docker_stop_grace_seconds': 7})
        else:
            code = '''import json,socket,time,urllib.request
sockets=[]
try:
 for _ in range(4):
  sockets.append(socket.create_connection(('127.0.0.1',5443),timeout=2));time.sleep(.1)
 with socket.create_connection(('127.0.0.1',5443),timeout=2) as fifth:
  fifth.settimeout(2);closed=fifth.recv(1)==b''
 request=urllib.request.Request('http://127.0.0.1:8002/health',headers={'Authorization':'Bearer '+TOKEN})
 health=json.load(urllib.request.urlopen(request,timeout=2))
 print(json.dumps({'fifth_closed':closed,'health':health}))
finally:
 for connection in sockets:connection.close()
'''.replace('TOKEN', repr(lab.health_token))
            observation = json.loads(lab.compose('exec', '-T', 'cloud', 'python', '-c', code).stdout)
            lab.wait(lambda: lab.http('cloud')['metrics'].get('gateway_rejected', 0) >= 4)
            recovery = valid_upload(lab)
            passed = (observation['fifth_closed'] and observation['health']['metrics'].get('connections_refused', 0) >= 1
                      and observation['health']['live'] and recovery['reply'] is not None
                      and recovery['reply'].get('status') == 'committed')
            report['cases'].append({'name': 'four_pre_tls_slots_fifth_refused_and_recovery',
                                   'passed': passed, 'observation': observation, 'recovery': recovery})
        report['status'] = 'passed' if all(case['passed'] for case in report['cases']) else 'failed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if child is not None:
            try:
                stdout, stderr = child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                child.terminate()
                stdout, stderr = child.communicate(timeout=3)
            write_json(root / 'client-process.json', {'exit_code': child.returncode, 'stdout': stdout, 'stderr': stderr})
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
    parser.add_argument('--case', choices=('delayed_commit', 'health_shutdown', 'worker_limit'), required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    report = execute(args.runtime_root, args.docker_cli, args.case)
    write_json(args.evidence, report)
    print(json.dumps({'status': report['status'], 'cases': report['cases'], 'runtime_root': str(args.runtime_root),
                      'cleanup': report.get('cleanup'), 'error': report.get('error')}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
