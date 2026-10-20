"""Real package installation, performance, 600s outage and isolated upgrade lab."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import traceback

from package import Pilot, ROLES, create, validate_root, write


def percentile(values, percent=95):
    if not values:
        raise ValueError('no measured samples')
    return sorted(values)[math.ceil(len(values) * percent / 100) - 1]


def wait(pilot, predicate, seconds=65):
    end = time.monotonic() + seconds
    last_renew = 0
    while time.monotonic() < end:
        if time.monotonic() - last_renew >= 150:
            pilot.renew(); last_renew = time.monotonic()
        try:
            result = predicate()
            if result:
                return result
        except (ValueError, RuntimeError, KeyError):
            pass
        time.sleep(.3)
    raise TimeoutError('bounded pilot wait expired')


def worker_result(pilot, name):
    code = 'import json; print(open(' + repr('/var/lib/pqc/' + name + '.json') + ').read())'
    return json.loads(pilot.compose('exec', '-T', 'gateway', 'python', '-c', code).stdout)


def launch_load(pilot, name, seconds, interval=5, wait_ack=True):
    args = ['exec', '-d', 'gateway', 'python', '/app/pilot_worker.py', 'load',
            '--seconds', str(seconds), '--interval', str(interval),
            '--result', '/var/lib/pqc/' + name + '.json']
    if not wait_ack:
        args.append('--no-wait-ack')
    pilot.compose(*args)


def sample(pilot):
    ids = pilot.compose('ps', '-q', *ROLES).stdout.split()
    raw = pilot.run('stats', '--no-stream', '--format', '{{json .}}', *ids).stdout
    stats = [json.loads(line) for line in raw.splitlines() if line.strip()]
    health = {role: pilot.health(role) for role in ROLES}
    if len(stats) != 2 or any(h['state_bytes'] >= 240 * 1024 * 1024 for h in health.values()):
        raise AssertionError('resource sampling or storage bound failed')
    return {'utc': datetime.now(timezone.utc).isoformat(), 'docker': stats,
            'state_bytes': {role: h['state_bytes'] for role, h in health.items()}}


def reconcile(pilot):
    gateway, cloud = pilot.health('gateway'), pilot.health('cloud')
    gs, cs = gateway['storage'], cloud['storage']
    assert gs['pending'] == gs['quarantined'] == 0
    assert gs['accepted_total'] == gs['acknowledged_total'] == cs['committed_total']
    code = "import json,sqlite3,hashlib; d=sqlite3.connect('file:/var/lib/pqc/cloud.sqlite?mode=ro',uri=True); r=d.execute('SELECT gateway,event_id,raw FROM events ORDER BY gateway,event_id').fetchall(); print(json.dumps({'rows':len(r),'unique_ids':len({(x[0],x[1]) for x in r}),'business_sha256':hashlib.sha256(b''.join(bytes(x[2]) for x in r)).hexdigest()}));d.close()"
    business = json.loads(pilot.compose('exec', '-T', 'cloud', 'python', '-c', code).stdout)
    assert business['rows'] == business['unique_ids'] == cs['committed_total']
    return {'gateway': gs, 'cloud': cs, 'business': business}


def execute(root, cli, load_seconds=500, outage_seconds=600):
    root = validate_root(root, fresh=True); root.mkdir(parents=True)
    report = {'status': 'running', 'scope': 'synthetic Docker only', 'cases': [],
              'started_utc': datetime.now(timezone.utc).isoformat(), 'resources': [],
              'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    pilots = []
    def record(name, **data):
        report['cases'].append({'name': name, 'passed': True, **data}); write(root / 'progress.json', report)
    try:
        pilot = Pilot(create(root / 'initial'), cli); pilots.append(pilot)
        initialized = pilot.initialize(); pilot.start()
        wait(pilot, lambda: pilot.health('gateway')['cloud_connected'])
        record('fresh_offline_installation', **initialized, source_sha256=pilot.release['source_sha256'])
        # Matching RSA identities, same loopback/hardware/context settings;
        # only the benchmark process's group policy differs.
        for group in ('X25519', 'X25519MLKEM768'):
            code = """import os,subprocess,json
from pathlib import Path
p=Path('/tmp/benchmark.cnf');p.write_bytes(Path('/run/pqc/tls-policy.cnf').read_bytes().replace(b'Groups = X25519MLKEM768',b'Groups = GROUP'))
e=dict(os.environ,OPENSSL_CONF=str(p));r=subprocess.run(['python','/app/pilot_worker.py','tls','--samples','100'],env=e,capture_output=True,text=True,timeout=60)
assert r.returncode==0,r.stderr
print(r.stdout)
""".replace('GROUP', group)
            measured = pilot.admin('-c', code, timeout=80)
            p95 = percentile(measured['full_handshake_seconds'])
            assert p95 <= 1 and measured['resumed'] == 0
            record('isolated_full_handshakes_' + group, p95_seconds=p95, **measured)
        launch_load(pilot, 'normal', load_seconds)
        report['resources'].append(sample(pilot))
        last_resource = time.monotonic()
        def normal_done():
            nonlocal last_resource
            value = worker_result(pilot, 'normal')
            if time.monotonic() - last_resource >= 30:
                report['resources'].append(sample(pilot)); last_resource = time.monotonic()
                write(root / 'progress.json', report)
            return value if value['status'] != 'running' else None
        normal = wait(pilot, normal_done, seconds=load_seconds + 90)
        write(root / 'normal-load.json', normal)
        assert normal['status'] == 'passed', 'normal worker failed: ' + normal.get('error_type', 'unknown')
        assert normal['missed_schedule'] == 0, 'normal workload schedule missed'
        p95 = percentile(normal['latencies_seconds'])
        assert p95 <= 1, 'normal delivery p95 exceeds one second'
        if load_seconds >= 500:
            assert len(normal['latencies_seconds']) >= 100
        record('normal_load_durable_ack_latency', p95_seconds=p95, measurements=normal,
               reconciliation=reconcile(pilot), full_100_sample_gate=load_seconds >= 500)
        # Deliberately reduced, supported admission budget: overload is measured
        # separately from the frozen normal workload, never a scale claim.
        pilot.compose('stop', '--timeout', '5', *ROLES)
        config_path = pilot.root / 'gateway.json'
        original_config = json.loads(config_path.read_text())
        write(config_path, {**original_config, 'limits': {'queue_rows': 3}})
        pilot.renew(); pilot.compose('up', '-d', '--no-build', '--pull', 'never', 'gateway')
        wait(pilot, lambda: pilot.health('gateway')['live'])
        before_overload = pilot.health('gateway')['storage']
        launch_load(pilot, 'overload', 1, interval=.05, wait_ack=False)
        result = wait(pilot, lambda: (r if (r := worker_result(pilot, 'overload'))['status'] != 'running' else None))
        wait(pilot, lambda: pilot.health('gateway')['metrics'].get('source_refused_queue_row_quota', 0) > 0)
        overloaded = pilot.health('gateway')
        assert overloaded['storage']['pending'] == 3
        assert overloaded['storage']['accepted_total'] == before_overload['accepted_total'] + 3
        assert overloaded['loss_count_unknown'] is True
        record('overload_closes_unacknowledged_sources_without_false_acceptance',
               configured_queue_rows=3, attempted=result['sent'], health=overloaded,
               boundary='supported lower row limit; no real-device backpressure or exact source loss count')
        pilot.compose('stop', '--timeout', '5', 'gateway')
        write(config_path, original_config); pilot.start()
        wait(pilot, lambda: pilot.health('gateway')['storage']['pending'] == 0)
        reconcile(pilot)
        pilot.compose('stop', '--timeout', '5', 'cloud')
        outage_started = time.monotonic()
        launch_load(pilot, 'outage', outage_seconds, wait_ack=False)
        result = wait(pilot, lambda: (r if (r := worker_result(pilot, 'outage'))['status'] != 'running' else None),
                      seconds=outage_seconds + 45)
        assert result['status'] == 'passed'
        before = pilot.health('gateway')['storage']
        assert before['pending'] > 0
        actual_outage = time.monotonic() - outage_started
        assert actual_outage >= outage_seconds
        pilot.renew(); pilot.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud')
        wait(pilot, lambda: pilot.health('cloud')['live'])
        available_at = time.monotonic()
        wait(pilot, lambda: pilot.health('gateway')['storage']['acknowledged_total'] > before['acknowledged_total'], seconds=60)
        first_ack = time.monotonic() - available_at
        wait(pilot, lambda: pilot.health('gateway')['storage']['pending'] == 0, seconds=65)
        drained = time.monotonic() - available_at
        record('actual_cloud_outage_and_complete_drain', outage_seconds=actual_outage,
               selected_600_second_gate=outage_seconds >= 600, first_ack_seconds=first_ack,
               drain_seconds=drained, accepted_backlog=before['pending'], reconciliation=reconcile(pilot))
        previous = reconcile(pilot)
        pilot.compose('stop', '--timeout', '10', *ROLES)
        receipt = pilot.backup(root / 'vault-1')
        upgraded = Pilot(create(root / 'upgraded', 'pilot-lab-v1.1'), cli); pilots.append(upgraded)
        upgraded.initialize(provision=False); upgraded.recover(root / 'vault-1', receipt['manifest_sha256'])
        upgraded.start(); wait(upgraded, lambda: upgraded.health('gateway')['cloud_connected'])
        assert reconcile(upgraded) == previous
        assert pilot.release['image'] != upgraded.release['image']
        record('isolated_current_checkpoint_restore_and_same_schema_package_upgrade', receipt=receipt,
               from_image=pilot.release['image'], to_image=upgraded.release['image'], reconciliation=previous,
               boundary='v1 to v1.1 packaging label; unchanged business/storage schemas')
        launch_load(upgraded, 'post-upgrade', 1)
        result = wait(upgraded, lambda: (r if (r := worker_result(upgraded, 'post-upgrade'))['status'] != 'running' else None))
        assert result['status'] == 'passed'
        rotation = upgraded.rotate()
        wait(upgraded, lambda: upgraded.health('gateway')['cloud_connected'])
        launch_load(upgraded, 'post-restore-rotation', 1)
        result = wait(upgraded, lambda: (r if (r := worker_result(upgraded, 'post-restore-rotation'))['status'] != 'running' else None))
        assert result['status'] == 'passed'
        record('restored_offline_issuer_rotates_both_roles_and_delivers', rotation=rotation,
               reconciliation=reconcile(upgraded))
        current = reconcile(upgraded)
        upgraded.compose('stop', '--timeout', '10', *ROLES)
        current_receipt = upgraded.backup(root / 'vault-2')
        rollback = Pilot(create(root / 'rollback'), cli); pilots.append(rollback)
        rollback.initialize(provision=False); rollback.recover(root / 'vault-2', current_receipt['manifest_sha256'])
        rollback.start(); wait(rollback, lambda: rollback.health('gateway')['cloud_connected'])
        assert reconcile(rollback) == current
        record('rollback_package_with_current_state_preserves_new_business_record',
               receipt=current_receipt, reconciliation=current)
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = {'type': type(exc).__name__, 'message': str(exc),
            'frames': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                       for f in traceback.extract_tb(exc.__traceback__)]}
    finally:
        report['cleanup'] = []
        for index, pilot in enumerate(reversed(pilots)):
            try:
                checkpoint_verified = False
                try:
                    for name in ('normal', 'overload', 'outage', 'post-upgrade', 'post-restore-rotation'):
                        try:
                            value = worker_result(pilot, name)
                            write(root / (pilot.project + '-' + name + '.json'), value)
                        except Exception:
                            pass
                    pilot.compose('stop', '--timeout', '10', *ROLES)
                    report.setdefault('retained_cold_state', []).append(pilot.backup(root / ('retained-state-' + str(index))))
                    checkpoint_verified = True
                except Exception as exc:
                    report.setdefault('preservation_errors', []).append(type(exc).__name__)
                    report['status'] = 'failed'
                report['cleanup'].append(pilot.cleanup() if checkpoint_verified else {
                    'verified': False, 'retained': True, 'project': pilot.project,
                    'reason': 'cold checkpoint unavailable; preserve owned current state'})
            except Exception as exc:
                report['cleanup'].append({'verified': False, 'error_type': type(exc).__name__})
        if any(not c['verified'] for c in report['cleanup']):
            report['status'] = 'failed'
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write(root / 'result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--docker-cli')
    parser.add_argument('--diagnostic', action='store_true', help='short debug only; never satisfies D load/outage gates')
    args = parser.parse_args()
    report = execute(args.runtime_root, args.docker_cli, 10 if args.diagnostic else 500, 8 if args.diagnostic else 600)
    print(json.dumps({'status': report['status'], 'cases': [c['name'] for c in report['cases']],
                      'error': report.get('error'), 'cleanup': report['cleanup']}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
