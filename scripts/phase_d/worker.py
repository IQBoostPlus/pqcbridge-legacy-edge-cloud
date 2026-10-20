"""Synthetic source and isolated TLS comparison inside owned pilot containers."""
import argparse
import json
from pathlib import Path
import socket
import threading
import time
import urllib.request


def save(path, value):
    temporary = path.with_suffix('.new')
    temporary.write_text(json.dumps(value, sort_keys=True))
    temporary.replace(path)


def health(config):
    request = urllib.request.Request('http://127.0.0.1:8001/health',
                                    headers={'Authorization': 'Bearer ' + config['health_token']})
    return json.load(urllib.request.urlopen(request, timeout=2))


def load(seconds, interval, result, wait_ack=True):
    from common import crypto, protocol
    from device.sensor import generate_reading, reading_to_bytes
    config = json.loads(Path('/run/pilot/config.json').read_text())
    device, spec = next(iter(config['devices'].items()))
    key = bytes.fromhex(spec['key_hex'])
    # Persisted source checkpoint, not host wall clock or a reused in-memory ID.
    import sqlite3
    db = sqlite3.connect('file:/var/lib/pqc/gateway.sqlite?mode=ro', uri=True)
    try:
        row = db.execute('SELECT sequence FROM sources WHERE gateway=? AND device=? AND incarnation=?',
                         (config['gateway_id'], device, spec['source_incarnation'])).fetchone()
        sequence = row[0] if row else 0
    finally:
        db.close()
    before = health(config)['storage']
    started = time.monotonic(); deadline = started + seconds
    state = {'status': 'running', 'elapsed_seconds': 0, 'sent': 0, 'latencies_seconds': [],
             'baseline': before, 'interval_seconds': interval, 'expected_seconds': seconds,
             'max_pending': 0, 'max_state_bytes': 0, 'missed_schedule': 0}
    save(result, state)
    try:
        due = started
        while time.monotonic() < deadline:
            if result.with_suffix('.stop').exists():
                raise RuntimeError('operator stop requested')
            if time.monotonic() < due:
                time.sleep(min(due - time.monotonic(), .5)); continue
            if time.monotonic() - due > interval:
                state['missed_schedule'] += 1
            sequence += 1
            reading = generate_reading(device, sequence)
            hello = protocol.encode_message(crypto.build_hello(device, [protocol.CAP_CHACHA20_POLY1305], key))
            frame = protocol.encode_message({'type': protocol.MSG_LEGACY_READING, 'device_id': device,
                'seq': sequence, **crypto.encrypt_legacy_payload(key, reading_to_bytes(reading),
                                                                protocol.legacy_message_aad(device, sequence))})
            sent_at = time.monotonic()
            with socket.create_connection(('127.0.0.1', 5001), timeout=3) as connection:
                connection.sendall(hello + frame)
                # Let the unchanged source reader consume before closing.
                time.sleep(.015)
            state['sent'] += 1
            if wait_ack:
                until = time.monotonic() + 65
                while time.monotonic() < until:
                    observed = health(config)
                    if observed['storage']['acknowledged_total'] >= before['acknowledged_total'] + state['sent']:
                        state['latencies_seconds'].append(time.monotonic() - sent_at)
                        break
                    time.sleep(.01)
                else:
                    raise TimeoutError('matching durable acknowledgement timeout')
            observed = health(config)
            state['max_pending'] = max(state['max_pending'], observed['storage']['pending'])
            state['max_state_bytes'] = max(state['max_state_bytes'], observed['state_bytes'])
            state['elapsed_seconds'] = time.monotonic() - started
            state['latest'] = {'storage': observed['storage'], 'state_bytes': observed['state_bytes'],
                               'management_state': observed.get('management_state')}
            save(result, state)
            due += interval
        state['elapsed_seconds'] = time.monotonic() - started
        state['status'] = 'passed'
    except Exception as exc:
        state['status'] = 'failed'; state['error_type'] = type(exc).__name__
        state['elapsed_seconds'] = time.monotonic() - started
    finally:
        save(result, state)
    return state['status'] == 'passed'


def tls(samples):
    """Policy is selected in a fresh isolated admin process before ssl import.

    This comparison never calls or alters the mandatory service TLS policy.
    """
    import ssl
    root = Path('/bundle')
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    for context in (server, client):
        context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.verify_mode = ssl.CERT_REQUIRED
        context.options |= ssl.OP_NO_TICKET
        context.load_verify_locations(root / 'cloud-credentials/ca.pem')
    server.num_tickets = 0
    server.load_cert_chain(root / 'cloud-credentials/cloud/cert.pem', root / 'cloud-credentials/cloud/key.pem')
    client.load_cert_chain(root / 'gateway-credentials/gateway/cert.pem', root / 'gateway-credentials/gateway/key.pem')
    listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen(4); listener.settimeout(10)
    errors = []
    def serve():
        try:
            for _ in range(samples):
                raw, _ = listener.accept()
                with server.wrap_socket(raw, server_side=True) as channel:
                    channel.settimeout(5); channel.recv(1); channel.sendall(b'x')
        except Exception as exc:
            errors.append(type(exc).__name__)
    thread = threading.Thread(target=serve); thread.start()
    durations = []; resumed = 0
    try:
        for _ in range(samples):
            with socket.create_connection(listener.getsockname(), timeout=5) as raw:
                start = time.perf_counter()
                with client.wrap_socket(raw, server_hostname='cloud') as channel:
                    durations.append(time.perf_counter() - start)
                    resumed += int(channel.session_reused)
                    assert channel.version() == 'TLSv1.3'
                    channel.sendall(b'x'); assert channel.recv(1) == b'x'
        thread.join(timeout=10)
        assert not thread.is_alive() and not errors and resumed == 0
    finally:
        listener.close()
    return {'samples': samples, 'full_handshake_seconds': durations, 'resumed': resumed,
            'tls': 'TLSv1.3', 'authentication': 'same synthetic mTLS RSA leaves',
            'ssl': ssl.OPENSSL_VERSION, 'boundary': 'single-group controlled OpenSSL policy; loopback admin benchmark'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('load', 'tls'))
    parser.add_argument('--seconds', type=float, default=500)
    parser.add_argument('--interval', type=float, default=5)
    parser.add_argument('--samples', type=int, default=100)
    parser.add_argument('--result', type=Path, default=Path('/var/lib/pqc/pilot-load.json'))
    parser.add_argument('--no-wait-ack', action='store_true')
    args = parser.parse_args()
    if args.action == 'tls':
        print(json.dumps(tls(args.samples))); return 0
    if not 0 < args.seconds <= 90000 or not .01 <= args.interval <= 5:
        parser.error('bounded seconds and interval required')
    return 0 if load(args.seconds, args.interval, args.result, not args.no_wait_ack) else 1


if __name__ == '__main__':
    raise SystemExit(main())
