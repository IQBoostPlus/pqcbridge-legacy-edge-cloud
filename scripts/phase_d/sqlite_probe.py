"""Tight real GatewayQueue expiry/snapshot concurrency regression probe."""
import argparse
import json
from pathlib import Path
import tempfile
import threading
import time
import uuid
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import delivery


def run(seconds=5, disable_cache=False):
    if not 0 < seconds <= 60:
        raise ValueError('probe duration must be positive and at most 60 seconds')
    original = delivery.sqlite3.connect
    if disable_cache:
        delivery.sqlite3.connect = lambda *args, **kwargs: original(*args, **kwargs, cached_statements=0)
    failures = []; reads = [0]; errors = []
    try:
        with tempfile.TemporaryDirectory() as directory:
            queue = delivery.GatewayQueue(directory)
            incarnation = str(uuid.uuid4())
            for sequence in range(1, 18):
                raw = delivery.canonical_event('gw-lab', 'dev-lab', incarnation, {
                    'device_id': 'dev-lab', 'sequence': sequence, 'timestamp': None,
                    'temperature_c': 21.5, 'unit': 'celsius'})
                queue.accept(raw)
                if sequence <= 7:
                    queue.acknowledge(raw, delivery.ack_for(raw))
            until = time.monotonic() + seconds
            stop = threading.Event()
            def expire():
                try:
                    while time.monotonic() < until and not stop.is_set():
                        queue.expire()
                except Exception as exc:
                    errors.append(type(exc).__name__); stop.set()
            def observe():
                try:
                    while time.monotonic() < until and not stop.is_set():
                        snapshot = queue.snapshot(); reads[0] += 1
                        if snapshot['accepted_total'] != 17 or snapshot['acknowledged_total'] != 7:
                            failures.append(snapshot); stop.set()
                except Exception as exc:
                    errors.append(type(exc).__name__); stop.set()
            threads = [threading.Thread(target=expire), *[threading.Thread(target=observe) for _ in range(3)]]
            for thread in threads: thread.start()
            for thread in threads: thread.join(timeout=seconds + 10)
            if any(thread.is_alive() for thread in threads):
                errors.append('thread_not_stopped')
            if reads[0] == 0:
                errors.append('no_observations')
            database = dict(queue._db.execute('SELECT key,value FROM metadata'))
            queue.close()
    finally:
        delivery.sqlite3.connect = original
    return {'status': 'failed' if failures or errors else 'passed', 'reads': reads[0],
            'failures': failures, 'errors': errors, 'disable_statement_cache': disable_cache,
            'database_counters': {k: database.get(k) for k in ('accepted_total', 'acknowledged_total')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=5)
    parser.add_argument('--disable-cache', action='store_true')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args(); report = run(args.seconds, args.disable_cache)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2)); return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
