"""Expired-pending maintenance must not corrupt concurrent metric reads."""
import importlib.util
from pathlib import Path
import threading
import time
import uuid

from common import delivery


def test_expiry_and_health_snapshot_preserve_durable_counters():
    path = Path(__file__).resolve().parents[1] / 'scripts/phase_d/sqlite_probe.py'
    spec = importlib.util.spec_from_file_location('delivery_concurrency_probe', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    result = module.run(seconds=2)
    assert result['status'] == 'passed', result
    assert result['reads'] > 0
    assert result['database_counters'] == {'accepted_total': '17', 'acknowledged_total': '7'}


def test_expiry_samples_wall_clock_after_concurrent_acceptance_lock(monkeypatch, tmp_path):
    queue = delivery.GatewayQueue(tmp_path / 'queue')
    started, sampled = threading.Event(), threading.Event()
    original = time.time
    errors = []
    def clock():
        if threading.current_thread().name == 'd-expiry-clock-test':
            sampled.set()
        return original()
    monkeypatch.setattr(delivery.time, 'time', clock)
    def expire():
        started.set()
        try:
            queue.expire()
        except Exception as exc:
            errors.append(type(exc).__name__)
    thread = threading.Thread(target=expire, name='d-expiry-clock-test', daemon=True)
    try:
        with queue._lock:
            thread.start(); assert started.wait(2)
            assert not sampled.wait(.03), 'expiry sampled before owning the acceptance lock'
            raw = delivery.canonical_event('gw', 'dev', str(uuid.uuid4()), {
                'device_id': 'dev', 'sequence': 1, 'timestamp': None,
                'temperature_c': 21.5, 'unit': 'celsius'})
            queue.accept(raw)
        thread.join(timeout=3)
        assert not thread.is_alive() and not errors
        assert queue.snapshot()['clock_uncertain'] is False
    finally:
        thread.join(timeout=3)
        queue.close()
