"""Real protected health regressions with a disclosed external clock fixture.

TLS, storage, ACK and HTTP run the actual managed service. Only the gateway
runtime's wall-clock dependency is offset for the stale-evidence observation;
this does not claim five minutes of elapsed operation or move controller time.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from docker_probe import Lab, validate_runtime, write_json


LAUNCHER = '''import sys
sys.path.insert(0,'/app')
from common.secure_transport import initialize_tls_policy
initialize_tls_policy()
from common import secure_runtime
from common.managed_config import ManagedConfiguration
import json
from pathlib import Path
actual=secure_runtime.time
class Clock:
 def time(self):
  try:offset=float(json.loads(Path('/run/lab/control/clock.json').read_text())['offset'])
  except (OSError,ValueError,KeyError):offset=0
  if not 0<=offset<=3600:raise ValueError('invalid laboratory clock offset')
  return actual.time()+offset
 def __getattr__(self,name):return getattr(actual,name)
secure_runtime.time=Clock()
sys.argv=[sys.argv[0],*sys.argv[2:]]
raise SystemExit(secure_runtime.service_main('gateway',configuration_class=ManagedConfiguration))
'''


def execute(root, cli):
    validate_runtime(root)
    root.mkdir(parents=True)
    report = {'status': 'failed', 'cases': [], 'runtime_root': str(root),
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'instrumentation': 'real TLS/SQLite/HTTP and real business ACK; runtime-only external wall-clock offset for stale evidence'}
    lab = None
    try:
        lab = Lab(root, cli)
        lab.prepare()
        report['project'] = lab.project
        report['source_sha256'] = {str(p.relative_to(root / 'source')):
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / 'source').rglob('*')) if p.is_file()}
        report['harness_sha256'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                   for name in ('observation_probe.py', 'docker_probe.py')}
        shutil.copyfile(__file__, root / 'observation_probe.observed.py')
        (root / 'launcher.py').write_text(LAUNCHER, encoding='utf-8')
        write_json(root / 'control/clock.json', {'offset': 0})
        compose = json.loads((root / 'compose.json').read_text())
        compose['services']['gateway']['command'] = ['/run/launcher.py', 'gateway', '--config', '/run/lab/gateway.json']
        compose['services']['gateway']['volumes'].append(str(root / 'launcher.py') + ':/run/launcher.py:ro')
        write_json(root / 'compose.json', compose)
        lab.compose('up', '-d', '--no-build', '--pull', 'never', 'cloud', 'gateway')
        lab.wait(lambda: lab.http('gateway'))
        lab.source()
        baseline = lab.delivered(version=1)
        assert baseline['management_state'] == 'Effective'
        sessions = baseline['metrics']['cloud_sessions']
        lab.compose('stop', '--timeout', '3', 'cloud')
        disconnected = lab.wait(lambda: (value if not (value := lab.http('gateway'))['cloud_connected'] else None))
        report['cases'].append({'name': 'disconnected_gateway_reports_unknown',
            'passed': disconnected['management_state'] == 'Unknown', 'gateway': disconnected})
        lab.compose('start', 'cloud')
        reconnect = lab.wait(lambda: (value if (value := lab.http('gateway'))['cloud_connected']
                                     and value['metrics']['cloud_sessions'] > sessions else None), seconds=65)
        report['cases'].append({'name': 'same_version_new_channel_requires_new_business_ack',
            'passed': reconnect['management_state'] == 'Applying', 'baseline': baseline, 'reconnected': reconnect})
        # This old ACK has never been observed by the catalog. Its current-channel
        # boundary must still prevent promoting a reconnect to Effective.
        refused = False
        try:
            lab.observe()
        except RuntimeError as exc:
            refused = str(exc) == 'management CLI refused: ack_not_current_channel'
        catalog_case = {'name': 'catalog_requires_current_channel_business_proof',
                        'passed': False, 'prior_channel_ack_refused': refused}
        report['cases'].append(catalog_case)
        # Restore current-channel real proof, then model aging that proof.
        lab.source()
        delivered = lab.wait(lambda: (value if (value := lab.http('gateway'))['storage']['acknowledged_total'] == 2
                                      and value['management_state'] == 'Effective' else None), seconds=65)
        assert delivered['management_state'] == 'Effective'
        current = lab.observe()
        catalog_case.update(passed=refused and current['state'] == 'Effective',
                            current_channel_observation=current)
        write_json(root / 'control/clock.json', {'offset': 301})
        stale = lab.http('gateway')
        report['cases'].append({'name': 'stale_business_evidence_reports_unknown',
            'passed': stale['management_state'] == 'Unknown', 'gateway': stale, 'clock_offset_seconds': 301})
        write_json(root / 'control/clock.json', {'offset': 0})
        report['status'] = 'passed' if all(case['passed'] for case in report['cases']) else 'failed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if lab:
            try:
                logs = lab.compose('logs', '--no-color', check=False)
                (root / 'application.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
            except Exception as exc:
                report['log_collection_error'] = type(exc).__name__
            report['cleanup'] = lab.cleanup()
            if not report['cleanup']['verified']:
                report['status'] = 'failed'
        write_json(root / 'result.json', report)
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
