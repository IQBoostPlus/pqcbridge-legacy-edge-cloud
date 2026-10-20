"""Owned 224 MiB valid-schema cold recovery and bounded-memory exercise.

The large metadata blob is a deliberate storage fixture, not business throughput
or a claim that the application accepts unbounded payloads.
"""
import argparse
import json
from pathlib import Path
import time

from package import Pilot, create, validate_root, write


def execute(root, cli):
    root = validate_root(root, fresh=True); root.mkdir(parents=True)
    report = {'status': 'failed', 'fixture_bytes': 224 * 1024 * 1024,
              'boundary': 'valid-schema synthetic unused metadata blob; cold recovery memory, not business capacity'}
    pilot = None; safe_cleanup = False
    try:
        pilot = Pilot(create(root / 'bundle'), cli); pilot.initialize()
        setup = """import sqlite3,json
from common.delivery import GatewayQueue,CloudStore
GatewayQueue('/bundle/states/gateway').close();CloudStore('/bundle/states/cloud').close()
d=sqlite3.connect('/bundle/states/cloud/cloud.sqlite');d.execute('PRAGMA journal_mode=DELETE')
d.execute("INSERT INTO metadata VALUES('pilot-padding',zeroblob(?))",(224*1024*1024,));d.commit();d.close()
print(json.dumps({'fixture_created':True}))
"""
        pilot.admin('-c', setup, timeout=90)
        vault = root / 'vault'; vault.mkdir()
        from package import protect_directory
        protect_directory(vault)
        override = pilot.root / 'memory-check-compose.json'
        write(override, {'services': {'admin': {'volumes': [str(vault) + ':/recovery:rw']}}})
        code = """import json,resource,time
from pathlib import Path
from common.pilot_ops import checkpoint,restore
start=time.monotonic();receipt=checkpoint(Path('/bundle'),Path('/recovery/snapshot'))
restored=restore(Path('/recovery/snapshot'),Path('/recovery/restored'),receipt['manifest_sha256'])
print(json.dumps({'receipt':receipt,'restored':restored['restored'],'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'elapsed_seconds':time.monotonic()-start}))
"""
        result = pilot.run(*(pilot.prefix + ['-f', str(override), 'run', '--rm', '-T', '--no-deps', '--pull', 'never',
            'admin', '-c', code]), timeout=180)
        report.update(json.loads(result.stdout))
        assert report['restored'] and report['peak_rss_kib'] < 256 * 1024
        safe_cleanup = True; report['status'] = 'passed'
    except Exception as exc:
        report['error_type'] = type(exc).__name__
    finally:
        report['cleanup'] = pilot.cleanup() if pilot and safe_cleanup else {
            'verified': False, 'retained': True, 'reason': 'recovery not verified; retain only current state'}
        if not report['cleanup']['verified']:
            report['status'] = 'failed'
        write(root / 'result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True); parser.add_argument('--docker-cli')
    args = parser.parse_args(); report = execute(args.runtime_root, args.docker_cli)
    print(json.dumps(report, indent=2)); return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
