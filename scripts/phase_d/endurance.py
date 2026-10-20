"""Human-authorized 30-minute Docker experiment; no external target or service."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import time

from package import Pilot, ROLES, create, validate_root, write
from acceptance import launch_load, reconcile, sample, wait, worker_result, percentile

ACCEPTANCE_SECONDS = 1800
ROTATION_SECONDS = 450


def execute(root, cli, seconds=ACCEPTANCE_SECONDS):
    root = validate_root(root, fresh=True); root.mkdir(parents=True)
    report = {'status': 'running', 'scope': 'synthetic owned Docker', 'expected_seconds': seconds,
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'acceptance_profile': 'human-revised-30-minute-20261020',
              'acceptance_seconds': ACCEPTANCE_SECONDS, 'rotation_interval_seconds': ROTATION_SECONDS,
              'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'rotations': [], 'resource_samples': 0}
    write(root / 'progress.json', report)
    pilot = None
    try:
        pilot = Pilot(create(root / 'bundle'), cli)
        report['installation'] = pilot.initialize(); pilot.start()
        wait(pilot, lambda: pilot.health('gateway')['cloud_connected'])
        report['source_sha256'] = pilot.release['source_sha256']
        report['workload_started_utc'] = datetime.now(timezone.utc).isoformat()
        report['earliest_finish_utc'] = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
        launch_load(pilot, 'endurance', seconds)
        wait(pilot, lambda: worker_result(pilot, 'endurance'), seconds=15)
        started = time.monotonic(); last_renew = started; last_rotation = started
        while True:
            if (root / 'STOP').exists():
                raise InterruptedError('operator stop requested')
            current = time.monotonic()
            if current - last_renew >= 150:
                pilot.renew(); last_renew = time.monotonic()
            if current - last_rotation >= ROTATION_SECONDS:
                result = pilot.rotate()
                report['rotations'].append({'elapsed_seconds': current - started, **result})
                last_rotation = time.monotonic()
            observed = worker_result(pilot, 'endurance')
            resource = sample(pilot)
            for line in resource['docker']:
                if float(line['MemPerc'].rstrip('%')) >= 100 or int(line['PIDs']) > 64:
                    raise AssertionError('resource budget breached')
            for role in ROLES:
                identity = pilot.compose('ps', '-q', role).stdout.strip()
                info = json.loads(pilot.run('inspect', identity).stdout)[0]
                assert info['HostConfig']['NanoCpus'] == 500000000
                assert info['HostConfig']['Memory'] == 256 * 1024 * 1024
                assert info['HostConfig']['PidsLimit'] == 64
                assert not info['State']['OOMKilled'] and info['RestartCount'] == 0
                assert all(binding is None for binding in info['NetworkSettings']['Ports'].values())
            with (root / 'resource-samples.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(resource) + '\n')
            report['resource_samples'] += 1
            report['elapsed_seconds'] = observed['elapsed_seconds']
            report['sent'] = observed['sent']
            report['latest'] = observed.get('latest')
            write(root / 'progress.json', report)
            if observed['status'] != 'running':
                assert observed['status'] == 'passed'
                assert observed['elapsed_seconds'] >= seconds
                assert observed['sent'] >= int(seconds // 5)
                assert observed['missed_schedule'] == 0
                report['reconciliation'] = reconcile(pilot)
                report['worker'] = observed
                report['delivery_p95_seconds'] = percentile(observed['latencies_seconds'])
                report['full_24_hour_gate'] = seconds >= 86400
                report['full_one_hour_gate'] = seconds >= 3600
                report['full_30_minute_gate'] = seconds >= ACCEPTANCE_SECONDS
                if report['full_30_minute_gate']:
                    assert len(report['rotations']) >= 3, 'missing in-run credential rotations'
                    assert report['delivery_p95_seconds'] <= 1, 'durable ACK latency budget breached'
                report['status'] = 'passed' if report['full_30_minute_gate'] else 'diagnostic_passed'
                break
            if current - started > seconds + 150:
                raise TimeoutError('endurance worker overran bounded duration')
            # A standalone test process sleeps; no agent work is blocked by it.
            time.sleep(30)
    except Exception as exc:
        report['status'] = 'interrupted' if isinstance(exc, InterruptedError) else 'failed'
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if pilot:
            checkpoint_verified = False
            try:
                pilot.compose('stop', '--timeout', '10', *ROLES)
                report['recovery_receipt'] = pilot.backup(root / 'final-state-vault')
                checkpoint_verified = True
            except Exception as exc:
                report['backup_error_type'] = type(exc).__name__
                report['status'] = 'failed'
            if checkpoint_verified:
                try:
                    report['cleanup'] = pilot.cleanup()
                    if not report['cleanup']['verified']:
                        report['status'] = 'failed'
                except Exception as exc:
                    report['cleanup'] = {'verified': False, 'error_type': type(exc).__name__}
                    report['status'] = 'failed'
            else:
                report['cleanup'] = {'verified': False, 'retained': True,
                    'reason': 'cold checkpoint unavailable; preserve owned current state',
                    'bundle': str(pilot.root)}
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write(root / 'result.json', report)
        write(root / 'progress.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--docker-cli')
    parser.add_argument('--diagnostic', action='store_true')
    args = parser.parse_args()
    report = execute(args.runtime_root, args.docker_cli, 35 if args.diagnostic else ACCEPTANCE_SECONDS)
    print(json.dumps({'status': report['status'], 'elapsed_seconds': report.get('elapsed_seconds'),
                      'error': report.get('error'), 'cleanup': report.get('cleanup')}))
    return 0 if report['status'] in ('passed', 'diagnostic_passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
