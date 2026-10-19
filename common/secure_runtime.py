"""Opt-in engineering service integration. Start through secure_bootstrap.

Reuses the simulated legacy AEAD wire boundary; it does not run V1 cloud
handshakes or expose a plaintext cloud ingestion backend. Synthetic lab scope.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
from pathlib import Path
import secrets
import signal
import socket
import threading
import time
import uuid

from cryptography import x509
from common import delivery, secure_transport as transport
from gateway import processing


class ServiceError(ValueError):
    pass


def timestamp(value):
    if not isinstance(value, str):
        raise ServiceError('invalid policy expiry')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('timezone required')
        return result.timestamp()
    except ValueError as exc:
        raise ServiceError('invalid policy expiry') from exc


def load_document(path):
    raw = Path(path).read_bytes()
    if len(raw) > 65535:
        raise ServiceError('configuration too large')
    def unique(pairs):
        document = {}
        for key, value in pairs:
            if key in document:
                raise ServiceError('duplicate configuration key')
            document[key] = value
        return document
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ServiceError('configuration must be an object')
    # Validate finite values and Unicode without restricting file whitespace.
    json.dumps(value, allow_nan=False, ensure_ascii=False).encode('utf-8')
    return value


class Configuration:
    """Trusted read-only configuration; only lease expiry may be renewed live."""
    def __init__(self, path, role):
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ServiceError('absolute config path required')
        self.value = load_document(self.path)
        self.role = role
        self.tls = self.value['tls']
        for name in ('ca_file', 'cert_file', 'key_file'):
            if not Path(self.tls[name]).is_absolute():
                raise ServiceError('absolute credential paths required')
        self.state_dir = Path(self.value['state_dir']).resolve()
        checkout = Path(__file__).resolve().parents[1]
        if self.state_dir == checkout or checkout in self.state_dir.parents:
            raise ServiceError('state must be outside application checkout')
        if not Path(self.value['state_dir']).is_absolute():
            raise ServiceError('absolute state path required')
        self.token = self.value['health_token']
        if not isinstance(self.token, str) or len(self.token) < 32:
            raise ServiceError('independent health credential required')
        self.limits = dict(self.value.get('limits', {}))
        ceilings = {'queue_rows': 10000, 'cloud_rows': 100000,
                    'state_bytes': 256 * 1024 * 1024, 'reserve_bytes': 16 * 1024 * 1024}
        for key, ceiling in ceilings.items():
            item = self.limits.get(key, ceiling)
            if type(item) is not int or item < (0 if key == 'reserve_bytes' else 1) or item > ceiling:
                raise ServiceError('invalid bounded limit')
            self.limits[key] = item
        if self.limits['reserve_bytes'] >= self.limits['state_bytes']:
            raise ServiceError('invalid storage reserve')
        self.local_cert = x509.load_pem_x509_certificate(Path(self.tls['cert_file']).read_bytes())
        self.cert_end = self.local_cert.not_valid_after_utc.timestamp()
        if self.cert_end - self.local_cert.not_valid_before_utc.timestamp() > 86400:
            raise ServiceError('lab identity lifetime exceeds 24 hours')
        self.wall_start, self.mono_start = time.time(), time.monotonic()
        self.clock_uncertain = False
        if timestamp(self.value['policy_expires_at']) > time.time() + 300:
            raise ServiceError('policy lease exceeds five minutes')
        if role == 'gateway':
            if not isinstance(self.value['gateway_id'], str) or not self.value['gateway_id']:
                raise ServiceError('invalid gateway identity')
            devices = self.value['devices']
            if not isinstance(devices, dict) or not 1 <= len(devices) <= 3:
                raise ServiceError('bounded simulator device registry required')
            for device, spec in devices.items():
                if not isinstance(device, str) or not device or len(device) > 128:
                    raise ServiceError('invalid device identity')
                if len(bytes.fromhex(spec['key_hex'])) != 32:
                    raise ServiceError('invalid source key')
                uuid.UUID(spec['source_incarnation'])
        else:
            peers = self.value['gateway_peers']
            if not isinstance(peers, dict) or not 1 <= len(peers) <= 3:
                raise ServiceError('bounded certificate registry required')
            for fingerprint, spec in peers.items():
                if len(fingerprint) != 64 or any(c not in '0123456789abcdef' for c in fingerprint):
                    raise ServiceError('invalid certificate fingerprint')
                if not isinstance(spec['gateway_id'], str) or not spec['gateway_id']:
                    raise ServiceError('invalid registered gateway')
                if not isinstance(spec['devices'], dict) or not spec['devices']:
                    raise ServiceError('device authorization map required')
                for incarnation in spec['devices'].values():
                    uuid.UUID(incarnation)

    def remaining(self):
        now = time.time()
        expected = self.wall_start + time.monotonic() - self.mono_start
        if now + 1 < expected:
            self.clock_uncertain = True
        try:
            live = load_document(self.path)
            original = dict(self.value); renewed = dict(live)
            original.pop('policy_expires_at', None); renewed.pop('policy_expires_at', None)
            # Identity, keys, budgets and endpoints cannot drift on a lease renewal.
            if original != renewed or self.clock_uncertain:
                return 0
            end = timestamp(live['policy_expires_at'])
            if end > now + 300:
                return 0
            transport.require_initialized()
            return max(0, min(end, self.cert_end) - max(now, expected))
        except (OSError, ValueError, KeyError, TypeError):
            return 0

    def valid(self):
        return self.remaining() > 0


def certificate_remaining(connection):
    peer = x509.load_der_x509_certificate(connection.getpeercert(binary_form=True))
    return peer.not_valid_after_utc.timestamp() - time.time()


class Service:
    def __init__(self, config):
        self.config = config
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.metrics = {}
        self.connections = set()
        self.threads = []
        self.active = set()
        self.slots = threading.BoundedSemaphore(4)
        self.cloud_connected = False
        self.last_matching_ack_at = None
        self.channel_tokens = {}
        self.management_applied_version = None
        self.management_applied_at = None
        self.management_ack_version = None
        self.management_failure_reason = None
        limits = config.limits
        cls = delivery.GatewayQueue if config.role == 'gateway' else delivery.CloudStore
        self.store = cls(config.state_dir,
                         max_rows=limits['queue_rows' if config.role == 'gateway' else 'cloud_rows'],
                         max_bytes=limits['state_bytes'], reserve_bytes=limits['reserve_bytes'])
        self.health_server = None

    def count(self, key):
        with self.lock:
            self.metrics[key] = self.metrics.get(key, 0) + 1

    def channel_budget(self, connection):
        """Refresh authorization after storage/encoding, before network use."""
        remaining = min(self.config.remaining(), certificate_remaining(connection))
        if remaining <= 0:
            raise ServiceError('identity or policy expired')
        cap = 5
        if getattr(self.config, 'dynamic_tls', False):
            with self.lock:
                binding = self.channel_tokens.get(connection)
            if binding is None or not self.config.channel_current(binding[0], binding[1]):
                raise ServiceError('managed channel authorization changed')
            cap = self.config.operation_timeout(binding[0])
        return min(cap, remaining)

    @staticmethod
    def local_fingerprint(tls):
        certificate = x509.load_pem_x509_certificate(Path(tls['cert_file']).read_bytes())
        from cryptography.hazmat.primitives import serialization
        return hashlib.sha256(certificate.public_bytes(serialization.Encoding.DER)).hexdigest()

    def bind_channel(self, connection, local_fingerprint):
        if not getattr(self.config, 'dynamic_tls', False):
            return
        if not self.config.valid():
            raise ServiceError('managed policy expired during handshake')
        # Context identity is captured before handshake. Never label an old
        # credential's channel with a newly published version/token.
        if self.local_fingerprint(dict(self.config.tls)) != local_fingerprint:
            raise ServiceError('local TLS credential changed during handshake')
        peer = transport.peer_fingerprint(connection)
        token = self.config.channel_token(peer, local_fingerprint=local_fingerprint)
        if token is None or not self.config.channel_current(peer, token):
            raise ServiceError('managed peer refused')
        with self.lock:
            self.channel_tokens[connection] = (peer, token)
        self.channel_budget(connection)
        if self.config.role == 'gateway':
            status = self.config.management_status()
            version = status.get('version', status.get('desired_version'))
            with self.lock:
                # Every new authenticated channel needs its own business proof,
                # including a reconnect/leaf rotation with the same version.
                self.management_applied_version = version
                self.management_applied_at = datetime.now(timezone.utc).isoformat()
                self.management_ack_version = None

    def send_frame(self, connection, message):
        connection.settimeout(self.channel_budget(connection))
        transport.send_frame(connection, message)

    def status(self):
        state = self.store.snapshot()
        with self.lock:
            connected, metrics = self.cloud_connected, dict(self.metrics)
        used = sum(p.stat().st_size for p in self.config.state_dir.iterdir() if p.is_file())
        quota_ok = used < self.config.limits['state_bytes'] - self.config.limits['reserve_bytes']
        if self.config.role == 'gateway':
            quota_ok = quota_ok and state['pending'] + state['quarantined'] < self.config.limits['queue_rows']
        else:
            quota_ok = quota_ok and state['committed_total'] < self.config.limits['cloud_rows']
        valid = self.config.valid()
        managed = getattr(self.config, 'dynamic_tls', False)
        if managed and self.config.role == 'gateway':
            with self.lock:
                bindings = list(self.channel_tokens.values())
            connected = connected and any(self.config.channel_current(peer, token)
                                           for peer, token in bindings)
        ready = valid and quota_ok and not state.get('clock_uncertain', False)
        if self.config.role == 'gateway':
            if state['quarantined']:
                business = 'exceptional'
                ready = False
            elif state['pending']:
                business = 'backlog'
            elif not state['accepted_total']:
                business = 'not_yet_delivered'
            elif state['acknowledged_total'] == state['accepted_total']:
                business = 'delivered'
            else:
                business = 'unreconciled'
                ready = False
        else:
            business = 'committed' if state['committed_total'] else 'not_yet_committed'
        if self.config.role == 'gateway':
            ready = ready and connected
        result = {'live': not self.stop.is_set(), 'service': self.config.role, 'ready': ready,
                'policy_valid': valid, 'cloud_connected': connected,
                'storage': state, 'metrics': metrics, 'business_delivery': business,
                'last_matching_ack_at': self.last_matching_ack_at,
                'state_bytes': used, 'loss_count_unknown': metrics.get('source_refused', 0) > 0}
        if managed:
            information = self.config.management_status()
            result['management'] = information
            if self.config.role == 'gateway':
                desired = information.get('version', information.get('desired_version'))
                with self.lock:
                    applied, applied_at, ack_version = (self.management_applied_version,
                        self.management_applied_at, self.management_ack_version)
                fresh_ack = (self.last_matching_ack_at is not None and
                             time.time() - timestamp(self.last_matching_ack_at) <= 300)
                effective = (valid and connected and fresh_ack and desired == applied
                             and ack_version == applied and applied_at is not None
                             and timestamp(self.last_matching_ack_at) >= timestamp(applied_at))
                result.update(gateway_id=self.config.value['gateway_id'],
                              management_version=applied,
                              management_desired_version=desired,
                              management_applied_at=applied_at,
                              management_failure_reason=self.management_failure_reason,
                              management_state=('Unknown' if not valid or not connected or
                                  (self.last_matching_ack_at is not None and not fresh_ack)
                                  else 'Effective' if effective else 'Applying'))
        return result

    def start_health(self):
        service = self
        class Handler(BaseHTTPRequestHandler):
            def handle(self):
                # A per-recv socket timeout alone permits an endless trickle.
                # Bound the entire request, including headers and response.
                def expire_request():
                    try:
                        self.connection.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                deadline = threading.Timer(5, expire_request)
                deadline.daemon = True
                deadline.start()
                try:
                    super().handle()
                finally:
                    deadline.cancel()

            def do_GET(self):
                try:
                    if self.path == '/live':
                        value, code = {'live': True, 'service': service.config.role}, 200
                    elif not secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + service.config.token):
                        value, code = {'error': 'unauthorized'}, 401
                    elif self.path == '/readings' and service.config.role == 'cloud':
                        value, code = service.store.readings(min(100, service.config.limits['cloud_rows'])), 200
                    elif self.path in ('/ready', '/health'):
                        value = service.status()
                        code = 503 if self.path == '/ready' and not value['ready'] else 200
                    else:
                        value, code = {'error': 'not_found'}, 404
                    body = json.dumps(value, allow_nan=False).encode()
                except (OSError, ValueError):
                    body, code = b'{"error":"unavailable"}', 503
                self.send_response(code); self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body))); self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_args):
                pass
        class BoundedHTTP(HTTPServer):
            def get_request(self):
                request, address = super().get_request(); request.settimeout(5)
                service.track(request)
                return request, address

            def shutdown_request(self, request):
                try:
                    super().shutdown_request(request)
                finally:
                    service.untrack(request)
        self.health_server = BoundedHTTP(('127.0.0.1', self.config.value['health_port']), Handler)
        worker = threading.Thread(target=self.health_server.serve_forever, daemon=True)
        worker.start(); self.threads.append(worker)

    def claim(self, identity):
        with self.lock:
            if identity in self.active:
                return False
            self.active.add(identity)
            return True

    def release(self, identity):
        with self.lock:
            self.active.discard(identity)

    def track(self, connection):
        with self.lock:
            self.connections.add(connection)

    def untrack(self, connection):
        with self.lock:
            self.connections.discard(connection)
            self.channel_tokens.pop(connection, None)

    def handle_device(self, connection):
        identity = None
        claimed = False
        reading_inflight = False
        try:
            with connection, transport.SocketFrameReader(connection) as stream:
                stream.set_deadline(5)
                hello = processing.parse_hello(transport.read_frame(stream, 65536))
                identity = hello['device_id']
                spec = self.config.value['devices'].get(identity)
                if spec is None or processing.evaluate_hello(hello, bytes.fromhex(spec['key_hex'])) != processing.ALLOW_FALLBACK:
                    raise ServiceError('source authorization refused')
                if not self.claim(identity):
                    identity = None
                    raise ServiceError('source connection already active')
                claimed = True
                while not self.stop.is_set():
                    if (getattr(self.config, 'dynamic_tls', False)
                            and not self.config.source_allowed(identity, spec)):
                        raise ServiceError('managed source disabled or changed')
                    # Idle source intervals are not partial-frame operations.
                    if not stream.wait_readable(1):
                        continue
                    stream.set_deadline(5)
                    message = transport.read_frame(stream, 65536)
                    reading_inflight = True
                    raw, sequence = processing.decrypt_legacy_message(message, bytes.fromhex(spec['key_hex']), identity)
                    reading = transport.read_frame(io.BytesIO(raw + b'\n'), 65536)
                    if reading.get('device_id') != identity or type(reading.get('sequence')) is not int or reading['sequence'] != sequence:
                        raise ServiceError('authenticated metadata mismatch')
                    event = delivery.canonical_event(self.config.value['gateway_id'], identity,
                                                     spec['source_incarnation'], reading)
                    if (getattr(self.config, 'dynamic_tls', False)
                            and not self.config.source_allowed(identity, spec)):
                        raise ServiceError('managed source authorization changed')
                    self.store.accept(event)
                    self.count('durably_accepted')
                    reading_inflight = False
        except Exception as exc:
            # No exception message/payload/credentials are logged. Uncertain
            # in-flight source loss is distinct from already durable acceptance.
            self.count('source_refused' if reading_inflight else 'source_connection_closed')
            if reading_inflight:
                safe_reasons = {'queue_row_quota', 'state_byte_quota', 'source_sequence_refused',
                                'clock_uncertain', 'storage_transaction_failed'}
                reason = str(exc) if isinstance(exc, delivery.DeliveryError) and str(exc) in safe_reasons else 'invalid_reading'
                self.count('source_refused_' + reason)
            self.count('source_error_' + type(exc).__name__)
        finally:
            if claimed:
                self.release(identity)

    def handle_gateway(self, raw_connection, context):
        identity = None
        connection = raw_connection
        try:
            remaining = self.config.remaining()
            if remaining <= 0:
                raise ServiceError('policy expired')
            local_identity = None
            if getattr(self.config, 'dynamic_tls', False):
                tls = dict(self.config.tls)
                local_identity = self.local_fingerprint(tls)
                context = transport.server_context(tls)
            raw_connection.settimeout(min(5, remaining))
            connection = context.wrap_socket(raw_connection, server_side=True)
            self.track(connection)
            self.bind_channel(connection, local_identity)
            peer = self.config.value['gateway_peers'].get(transport.peer_fingerprint(connection))
            if peer is None:
                raise ServiceError('gateway certificate not registered')
            identity = peer['gateway_id']
            if not self.claim(identity):
                identity = None
                raise ServiceError('gateway connection already active')
            self.count('authenticated_connections')
            with connection, transport.SocketFrameReader(connection) as stream:
                while not self.stop.is_set():
                    remaining = self.channel_budget(connection)
                    if not stream.wait_readable(min(1, remaining)):
                        continue
                    remaining = self.channel_budget(connection)
                    stream.set_deadline(min(5, remaining))
                    try:
                        frame = transport.read_frame(stream)
                    except (socket.timeout, TimeoutError):
                        break  # Do not reuse a timed-out buffered TLS stream.
                    event_bytes, event = delivery.parse_upload(frame)
                    self.channel_budget(connection)
                    if event['gateway_id'] != identity or peer['devices'].get(event['device_id']) != event['source_incarnation']:
                        self.count('unauthorized_events')
                        self.send_frame(connection, {'type': 'error', 'reason': 'unauthorized'})
                        break
                    try:
                        ack = self.store.commit(event_bytes)
                    except delivery.DeliveryError as exc:
                        reason = 'conflict' if str(exc) == 'event_id_conflict' else 'capacity_or_storage'
                        self.count('commit_refused')
                        self.send_frame(connection, {'type': 'error', 'reason': reason})
                        break
                    self.send_frame(connection, ack)
                    self.count('committed_acks_sent')
        except Exception as exc:
            self.count('gateway_rejected')
            self.count('gateway_error_' + type(exc).__name__)
        finally:
            if identity is not None:
                self.release(identity)
            self.untrack(connection)
            connection.close()

    def deliver(self):
        delay = 1
        while not self.stop.is_set():
            connection = None
            try:
                self.store.expire()
                if not self.config.valid():
                    raise ServiceError('identity or policy expired')
                tls = dict(self.config.tls)
                local_identity = self.local_fingerprint(tls) if getattr(self.config, 'dynamic_tls', False) else None
                context = transport.client_context(tls)
                remaining = self.config.remaining()
                connection = socket.create_connection((self.config.value['cloud_host'], self.config.value['cloud_port']), timeout=min(5, remaining))
                self.track(connection)
                remaining = self.config.remaining()
                if remaining <= 0:
                    raise ServiceError('policy expired during connect')
                connection.settimeout(min(5, remaining))
                secured = context.wrap_socket(connection, server_hostname=tls['server_hostname'])
                self.untrack(connection); connection = secured; self.track(connection)
                self.bind_channel(connection, local_identity)
                connection.settimeout(self.channel_budget(connection))
                with self.lock:
                    self.cloud_connected = True
                self.count('cloud_sessions')
                with transport.SocketFrameReader(connection) as stream:
                    while not self.stop.is_set():
                        self.store.expire()
                        remaining = self.channel_budget(connection)
                        events = self.store.pending()
                        if not events:
                            if stream.wait_readable(0):
                                raise ServiceError('cloud closed or sent unexpected idle data')
                            self.stop.wait(.25)
                            continue
                        event = events[0]
                        self.send_frame(connection, delivery.event_upload(event))
                        remaining = self.channel_budget(connection)
                        stream.set_deadline(min(5, remaining))
                        ack = transport.read_frame(stream)
                        if ack.get('type') == 'error':
                            if ack.get('reason') in ('conflict', 'unauthorized'):
                                self.store.quarantine(event, ack['reason'])
                            raise ServiceError('cloud refused event')
                        self.channel_budget(connection)
                        if not delivery.matching_ack(event, ack):
                            raise delivery.DeliveryError('ack_mismatch')
                        self.store.acknowledge(event, ack)
                        self.last_matching_ack_at = datetime.now(timezone.utc).isoformat()
                        if getattr(self.config, 'dynamic_tls', False):
                            with self.lock:
                                self.management_ack_version = self.management_applied_version
                                self.management_failure_reason = None
                        self.count('matching_acks')
                        delay = 1
            except Exception as exc:
                self.count('delivery_retry')
                self.count('delivery_error_' + type(exc).__name__)
                if getattr(self.config, 'dynamic_tls', False):
                    reasons = {'TransportError': 'tls_configuration_refused',
                               'SSLCertVerificationError': 'tls_identity_refused',
                               'ServiceError': 'channel_or_policy_refused',
                               'DeliveryError': 'delivery_state_refused',
                               'FileNotFoundError': 'tls_configuration_refused',
                               'ConnectionRefusedError': 'network_unavailable',
                               'TimeoutError': 'network_unavailable',
                               'gaierror': 'network_unavailable'}
                    with self.lock:
                        self.management_failure_reason = reasons.get(type(exc).__name__, 'delivery_unavailable')
            finally:
                with self.lock:
                    self.cloud_connected = False
                if connection is not None:
                    self.untrack(connection)
                    connection.close()
            self.stop.wait(delay * (.8 + secrets.randbelow(201) / 1000))
            delay = min(30, delay * 2)

    def serve(self):
        self.start_health()
        context = (transport.server_context(self.config.tls)
                   if self.config.role == 'cloud' and not getattr(self.config, 'dynamic_tls', False) else None)
        if self.config.role == 'gateway':
            worker = threading.Thread(target=self.deliver, daemon=True)
            worker.start(); self.threads.append(worker)
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.config.value['listen_host'], self.config.value['listen_port']))
            listener.listen(8); listener.settimeout(.5)
            print(json.dumps({'event': 'service_started', 'role': self.config.role}), flush=True)
            while not self.stop.is_set():
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                if not self.slots.acquire(blocking=False):
                    self.count('connections_refused'); connection.close(); continue
                connection.settimeout(5); self.track(connection)
                def handle(conn=connection):
                    try:
                        if self.config.role == 'cloud':
                            self.handle_gateway(conn, context)
                        else:
                            self.handle_device(conn)
                    finally:
                        self.untrack(conn); conn.close(); self.slots.release()
                worker = threading.Thread(target=handle, daemon=True)
                worker.start()
                self.threads = [thread for thread in self.threads if thread.is_alive()]
                self.threads.append(worker)
        self.close()

    def close(self):
        self.stop.set()
        with self.lock:
            connections = list(self.connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        if self.health_server:
            self.health_server.shutdown(); self.health_server.server_close()
        for worker in self.threads:
            worker.join(timeout=6)
        if any(worker.is_alive() for worker in self.threads):
            raise ServiceError('bounded shutdown did not finish')
        self.store.close()
        if getattr(self.config, 'dynamic_tls', False):
            self.config.close()


def service_main(role, configuration_class=Configuration):
    parser = argparse.ArgumentParser(description='Opt-in lab-v1 engineering ' + role)
    parser.add_argument('--config', required=True)
    arguments = parser.parse_args()
    service = None
    try:
        config = configuration_class(arguments.config, role)
        service = Service(config)
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, lambda *_args: service.stop.set())
        service.serve()
        return 0
    except Exception as exc:
        print(json.dumps({'event': 'service_failed', 'role': role, 'error_type': type(exc).__name__}), flush=True)
        return 2
    finally:
        if service is not None and not service.stop.is_set():
            service.close()
