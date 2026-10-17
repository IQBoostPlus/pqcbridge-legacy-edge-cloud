"""Deterministic process crashes at real public storage API boundaries.

This is explicit laboratory instrumentation, not the normal application entry.
The wrappers pause before/after original methods; all transactions, sockets,
validation and recovery still execute the application implementation.
"""
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback

from docker_probe import Lab, validate_runtime, write_json

LAUNCHER = r'''
import sys
sys.path.insert(0,'/app')
from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
from common import delivery, secure_runtime
import json,sys,time,hashlib,os
from pathlib import Path
role=sys.argv[1]
control=Path('/run/fault')
def gate(stage,raw,ack=None):
 try:chosen=json.loads((control/'gate.json').read_text())
 except (OSError,ValueError):return
 if chosen.get('stage')!=stage or chosen.get('role')!=role:return
 if ack is not None:assert delivery.matching_ack(raw,ack)
 record={'stage':stage,'role':role,'event':delivery.decode_event(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 with (control/'entered.json').open('w') as stream:
  json.dump(record,stream);stream.flush();os.fsync(stream.fileno())
 deadline=time.monotonic()+25
 while time.monotonic()<deadline:
  time.sleep(.05)
 raise RuntimeError('bounded laboratory crash gate expired')
original_accept=delivery.GatewayQueue.accept
def accept(self,raw):
 gate('before_gateway_accept',raw)
 return original_accept(self,raw)
delivery.GatewayQueue.accept=accept
original_pending=delivery.GatewayQueue.pending

def pending(self,*args,**kwargs):
 rows=original_pending(self,*args,**kwargs)
 if rows:gate('before_gateway_send',rows[0])
 return rows

delivery.GatewayQueue.pending=pending
original_commit=delivery.CloudStore.commit
def commit(self,raw):
 gate('before_cloud_commit',raw)
 ack=original_commit(self,raw)
 gate('after_cloud_commit',raw)
 return ack
delivery.CloudStore.commit=commit
original_ack=delivery.GatewayQueue.acknowledge
def acknowledge(self,raw,ack):
 gate('before_gateway_acknowledge',raw,ack)
 return original_ack(self,raw,ack)
delivery.GatewayQueue.acknowledge=acknowledge
sys.argv=[sys.argv[0],*sys.argv[2:]]
raise SystemExit(secure_runtime.service_main(role))
'''


def source(lab, sequence, *, expect_close=False):
    config = json.loads((lab.root / 'gateway.json').read_text())
    code = '''import socket,json
from common import crypto,protocol
from device.sensor import generate_reading,reading_to_bytes
key=bytes.fromhex(KEY)
hello=crypto.build_hello('dev-lab',[protocol.CAP_CHACHA20_POLY1305],key)
reading=generate_reading('dev-lab',SEQUENCE)
message={'type':protocol.MSG_LEGACY_READING,'device_id':'dev-lab','seq':SEQUENCE,**crypto.encrypt_legacy_payload(key,reading_to_bytes(reading),protocol.legacy_message_aad('dev-lab',SEQUENCE))}
with socket.create_connection(('gateway',5001),timeout=3) as connection:
 connection.sendall(protocol.encode_message(hello)+protocol.encode_message(message))
 closed=connection.recv(1)==b'' if EXPECT_CLOSE else None
 if EXPECT_CLOSE:assert closed
print(json.dumps({'source_sequence':SEQUENCE,'sent':True,'server_closed':closed}))
'''.replace('KEY', repr(config['devices']['dev-lab']['key_hex'])).replace('SEQUENCE', str(sequence)).replace('EXPECT_CLOSE', repr(expect_close))
    return lab.probe(code)


def pending_event(lab):
    # Read the real queue through its public API. This independent connection
    # neither edits private SQL nor fabricates acceptance/acknowledgement.
    code = "from common.delivery import GatewayQueue,decode_event;import json;q=GatewayQueue('/var/lib/pqc');print(json.dumps(decode_event(q.pending()[0])));q.close()"
    return json.loads(lab.compose('exec', '-T', 'gateway', 'python', '-c', code).stdout)


def renew(lab):
    for role in ('cloud', 'gateway'):
        path = lab.root / (role + '.json')
        config = json.loads(path.read_text())
        config['policy_expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        write_json(path, config)


def fault_suite(root, cli, selected_case='matrix'):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'runtime_root': str(root), 'cases': [],
              'instrumentation': 'bounded wrapper pauses real public storage methods; actual role SIGKILL and restart',
              'selected_case': selected_case,
              'started_utc': datetime.now(timezone.utc).isoformat()}
    lab = None
    try:
        lab = Lab(root, cli)
        lab.prepare()
        report['project'] = lab.project
        report['source_sha256'] = {str(path.relative_to(root / 'source')):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / 'source').rglob('*')) if path.is_file()}
        report['harness_sha256'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                    for name in ('fault_probe.py', 'docker_probe.py')}
        shutil.copyfile(Path(__file__), root / 'fault_probe.observed.py')
        report['image'] = lab.compose('images', '-q', 'cloud').stdout.strip()
        control = root / 'fault'
        control.mkdir()
        (root / 'fault_launcher.py').write_text(LAUNCHER, encoding='utf-8')
        compose = json.loads((root / 'compose.json').read_text())
        for role in ('cloud', 'gateway'):
            compose['services'][role]['entrypoint'] = ['python', '/run/fault_launcher.py']
            compose['services'][role]['volumes'].extend([
                str(root / 'fault_launcher.py') + ':/run/fault_launcher.py:ro',
                str(control) + ':/run/fault:rw'])
        write_json(root / 'compose.json', compose)
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud', 'gateway')
        lab.wait(lambda: lab.http('cloud')); lab.wait(lambda: lab.http('gateway'))
        if selected_case == 'before_gateway_send':
            marker = control / 'entered.json'
            write_json(control / 'gate.json', {'stage': 'before_gateway_send', 'role': 'gateway'})
            source(lab, 1)
            entered = lab.wait(lambda: json.loads(marker.read_text()) if marker.exists() else None, seconds=15)
            before = lab.http('gateway')['storage']
            assert before['accepted_total'] == before['pending'] == 1
            assert before['acknowledged_total'] == 0
            assert lab.http('cloud')['storage']['committed_total'] == 0
            lab.compose('kill', '--signal', 'SIGKILL', 'gateway')
            write_json(control / 'gate.json', {})
            lab.compose('start', 'gateway')
            lab.wait(lambda: lab.http('gateway'))
            lab.wait(lambda: lab.http('cloud')['storage']['committed_total'] == 1
                     and lab.http('gateway')['storage']['pending'] == 0, seconds=65)
            rows = lab.http('cloud', '/readings')
            assert rows == [entered['event']]
            report['final_gateway_health'] = lab.http('gateway')
            report['final_cloud_health'] = lab.http('cloud')
            assert report['final_gateway_health']['storage']['acknowledged_total'] == 1
            report['cases'].append({'name': 'durable_gateway_commit_before_first_send_kill_restart', 'passed': True,
                                   'marker': entered, 'gateway_before_kill': before,
                                   'cloud_committed_before_kill': 0, 'cloud_committed_after_recovery': 1,
                                   'gate_boundary': 'public pending returns persisted event; paused before returning to sender'})
            report['status'] = 'passed'
            return report
        stages = [('before_gateway_accept', 'gateway'), ('before_cloud_commit', 'cloud'),
                  ('after_cloud_commit', 'cloud'), ('before_gateway_acknowledge', 'gateway')]
        for sequence, (stage, role) in enumerate(stages, 1):
            renew(lab)
            marker = control / 'entered.json'
            marker.unlink(missing_ok=True)
            write_json(control / 'gate.json', {'stage': stage, 'role': role})
            source(lab, sequence)
            entered = lab.wait(lambda: json.loads(marker.read_text()) if marker.exists() else None, seconds=15)
            before_cloud = lab.http('cloud')['storage']['committed_total']
            before_queue = lab.http('gateway')['storage']
            if stage == 'before_gateway_accept':
                assert before_cloud == 0 and before_queue['accepted_total'] == 0
            elif stage == 'before_cloud_commit':
                assert before_cloud == sequence - 1 and before_queue['pending'] == 1
            else:
                assert before_cloud == sequence and before_queue['pending'] == 1
            lab.compose('kill', '--signal', 'SIGKILL', role)
            write_json(control / 'gate.json', {})
            lab.compose('start', role)
            lab.wait(lambda: lab.http(role))
            if stage == 'before_gateway_accept':
                source(lab, sequence)  # Same source sequence remains admissible.
            lab.wait(lambda: lab.http('cloud')['storage']['committed_total'] == sequence
                     and lab.http('gateway')['storage']['pending'] == 0, seconds=65)
            rows = lab.http('cloud', '/readings')
            assert len(rows) == sequence
            if stage != 'before_gateway_accept':
                assert sum(event['event_id'] == entered['event']['event_id'] for event in rows) == 1
                assert next(event for event in rows if event['event_id'] == entered['event']['event_id']) == entered['event']
            report['cases'].append({'name': stage + '_kill_restart', 'passed': True,
                'marker': entered, 'cloud_committed_before_kill': before_cloud,
                'gateway_before_kill': before_queue, 'cloud_committed_after_recovery': len(rows)})
        renew(lab)
        lab.compose('pause', 'cloud')
        retries = lab.http('gateway')['metrics'].get('delivery_retry', 0)
        source(lab, 5)
        half_open = lab.wait(lambda: (status if (status := lab.http('gateway'))['metrics'].get('delivery_retry', 0) > retries
                                    and status['storage']['pending'] == 1 else None), seconds=25)
        lab.compose('unpause', 'cloud')
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        assert lab.http('cloud')['storage']['committed_total'] == 5
        report['cases'].append({'name': 'half_open_paused_cloud_timeout_retry_recovery', 'passed': True,
                               'gateway_during_half_open': half_open})
        # Live lease shortening uses the supported operator-controlled renewal
        # file. It does not alter credentials, budgets or any application state.
        for role in ('cloud', 'gateway'):
            path = root / (role + '.json'); config = json.loads(path.read_text())
            config['policy_expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
            write_json(path, config)
        lab.wait(lambda: not lab.http('cloud')['policy_valid'] and not lab.http('gateway')['policy_valid'], seconds=10)
        assert lab.http_status('cloud', '/ready', True) == 503
        assert lab.http_status('gateway', '/ready', True) == 503
        before = lab.http('gateway')['storage']['accepted_total']
        committed_before_expiry = lab.http('cloud')['storage']['committed_total']
        source(lab, 6)
        buffered = lab.wait(lambda: (status if (status := lab.http('gateway'))['storage']['accepted_total'] == before + 1
                                     and status['storage']['pending'] == 1 else None))
        assert not buffered['cloud_connected'] and not buffered['ready']
        assert lab.http_status('gateway', '/live') == 200
        assert lab.http_status('cloud', '/live') == 200
        assert lab.http('cloud')['storage']['committed_total'] == committed_before_expiry
        buffered_event = pending_event(lab)
        assert buffered_event['source_sequence'] == 6
        report['cases'].append({'name': 'expired_policy_disconnects_cloud_but_buffers_authorized_source', 'passed': True,
                               'gateway_during_expiry': buffered, 'buffered_event': buffered_event,
                               'cloud_committed_unchanged': committed_before_expiry})
        renew(lab)
        lab.wait(lambda: lab.http('cloud')['storage']['committed_total'] == 6
                 and lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        recovered_rows = lab.http('cloud', '/readings')
        assert sum(row['event_id'] == buffered_event['event_id'] for row in recovered_rows) == 1
        assert lab.http('gateway')['storage']['accepted_total'] == before + 1
        report['cases'].append({'name': 'explicit_valid_policy_renewal_drains_same_buffered_event', 'passed': True,
                               'event_id': buffered_event['event_id'], 'source_resent': False})
        # Exercise the actual service byte budget with an operator-selected
        # lower laboratory ceiling. This is logical quota pressure, not an
        # assertion that the host disk reached physical ENOSPC.
        renew(lab)
        lab.compose('stop', '--timeout', '3', 'cloud')
        source(lab, 7)
        lab.wait(lambda: lab.http('gateway')['storage']['pending'] == 1)
        retained_event = pending_event(lab)
        accepted_before_quota = lab.http('gateway')['storage']['accepted_total']
        used_before_quota = lab.http('gateway')['state_bytes']
        lab.compose('stop', '--timeout', '3', 'gateway')
        gateway_path = root / 'gateway.json'
        gateway_config = json.loads(gateway_path.read_text())
        gateway_config['limits'] = {'state_bytes': used_before_quota + 98304, 'reserve_bytes': 65536}
        write_json(gateway_path, gateway_config)
        lab.compose('start', 'gateway')
        lab.wait(lambda: lab.http('gateway'))
        refusal = source(lab, 8, expect_close=True)
        quota_status = lab.wait(lambda: (status if (status := lab.http('gateway'))['metrics'].get('source_refused_state_byte_quota', 0) >= 1 else None))
        assert quota_status['storage']['accepted_total'] == accepted_before_quota
        assert quota_status['storage']['pending'] == 1
        assert quota_status['loss_count_unknown']
        assert pending_event(lab) == retained_event
        report['cases'].append({'name': 'service_state_byte_quota_refuses_and_preserves_pending', 'passed': True,
                               'profile': gateway_config['limits'], 'gateway_at_refusal': quota_status,
                               'source_refusal': refusal, 'preserved_event_id': retained_event['event_id'],
                               'boundary': 'real service logical byte budget, not physical ENOSPC'})
        lab.compose('stop', '--timeout', '3', 'gateway')
        gateway_config.pop('limits')
        write_json(gateway_path, gateway_config)
        renew(lab)
        lab.compose('start', 'cloud', 'gateway')
        lab.wait(lambda: lab.http('gateway'))
        lab.wait(lambda: lab.http('cloud')['storage']['committed_total'] == 7
                 and lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        assert sum(row['event_id'] == retained_event['event_id'] for row in lab.http('cloud', '/readings')) == 1
        # Sequence8 was explicitly refused before acceptance; resending it after
        # operator repair verifies the refusal did not advance source state.
        source(lab, 8)
        lab.wait(lambda: lab.http('cloud')['storage']['committed_total'] == 8
                 and lab.http('gateway')['storage']['pending'] == 0, seconds=65)
        report['cases'].append({'name': 'operator_bytequota_repair_drains_original_and_accepts_refused_sequence',
                               'passed': True, 'preserved_event_id': retained_event['event_id'],
                               'explicit_source_sequence_resubmitted': 8})
        report['final_gateway_health'] = lab.http('gateway')
        report['final_cloud_health'] = lab.http('cloud')
        final_storage = report['final_gateway_health']['storage']
        assert final_storage['accepted_total'] == final_storage['acknowledged_total'] == report['final_cloud_health']['storage']['committed_total'] == 8
        assert final_storage['pending'] == final_storage['quarantined'] == 0
        report['reconciliation'] = {'accepted': 8, 'acknowledged': 8, 'committed': 8,
                                    'pending': 0, 'quarantined': 0}
        report['status'] = 'passed'
    except Exception as exc:
        origin = traceback.extract_tb(exc.__traceback__)[-1]
        report['error'] = {'type': type(exc).__name__, 'message': str(exc),
                           'location': Path(origin.filename).name + ':' + str(origin.lineno)}
    finally:
        if lab:
            try:
                # Unpause before cleanup if an assertion interrupted that case.
                lab.compose('unpause', 'cloud', check=False)
                logs = lab.compose('logs', '--no-color', check=False)
                (root / 'application.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
            except Exception as exc:
                report['log_collection_error'] = str(exc)
            report['cleanup'] = lab.cleanup()
            if not report['cleanup']['verified']:
                report['status'] = 'failed'
        write_json(root / 'fault-result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--docker-cli')
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--case', choices=('matrix', 'before_gateway_send'), default='matrix')
    args = parser.parse_args()
    result = fault_suite(args.runtime_root, args.docker_cli, args.case)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.evidence, result)
    print(json.dumps({'status': result['status'], 'cases': len(result['cases']),
                      'cleanup': result.get('cleanup'), 'error': result.get('error'),
                      'runtime': str(args.runtime_root)}, indent=2))
    return result['status'] != 'passed'


if __name__ == '__main__':
    raise SystemExit(main())
