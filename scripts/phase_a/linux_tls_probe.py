"""Container-only Python ssl adapter feasibility; never imports application code.

Use linux_tls_host.py. Fresh processes enforce exact immutable OpenSSL policy
before importing ssl. All credentials are synthetic, confined to /tmp tmpfs.
Only container-loopback connections are made; sockets, children and outer runtime
are bounded. CLI endpoint traces corroborate actual hybrid negotiation.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time

CONF = '''config_diagnostics = 1
openssl_conf = openssl_init
[openssl_init]
ssl_conf = ssl_section
[ssl_section]
system_default = tls_defaults
[tls_defaults]
MinProtocol = TLSv1.3
MaxProtocol = TLSv1.3
Groups = X25519MLKEM768
'''
REQUEST = 'phase-a-linux\n'
RESPONSE = 'phase-a-ack\n'

CHILD = r'''
import hashlib,json,os,sys
from pathlib import Path
role=sys.argv[1];root=Path(sys.argv[2]);policy=sys.argv[3]
configured=os.environ.get('OPENSSL_CONF')
if not configured or not Path(configured).is_file():
    print(json.dumps({'status':'config-rejected','reason':'missing policy file'}));sys.exit(3)
if Path(configured).read_text()!=policy:
    print(json.dumps({'status':'config-rejected','reason':'unexpected policy bytes'}));sys.exit(3)
import ssl,socket
context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if role=='server' else ssl.PROTOCOL_TLS_CLIENT)
context.minimum_version=context.maximum_version=ssl.TLSVersion.TLSv1_3
context.verify_mode=ssl.CERT_REQUIRED
context.load_verify_locations(str(root/'ca.crt'))
identity=sys.argv[4]
if identity!='none':context.load_cert_chain(str(root/(identity+'.crt')),str(root/(identity+'.key')))
def exact(connection,expected):
    data=b''
    while len(data)<len(expected):
        piece=connection.recv(len(expected)-len(data))
        if not piece:raise ValueError('EOF before exact message')
        data+=piece
    if data!=expected:raise ValueError('application bytes mismatch')
    return data
def accepted(connection,data):
    print(json.dumps({'status':'accepted','protocol':connection.version(),
        'cipher':connection.cipher(),'peer_identity':connection.getpeercert(),
        'peer_der_sha256':hashlib.sha256(connection.getpeercert(binary_form=True)).hexdigest(),
        'received_hex':data.hex(),'session_reused':connection.session_reused}),flush=True)
listener=None
try:
    if role=='server':
        context.num_tickets=0
        listener=socket.socket();listener.settimeout(5)
        listener.bind(('127.0.0.1',0));listener.listen(1)
        (root/'ready.json').write_text(json.dumps({'port':listener.getsockname()[1]}))
        raw,_=listener.accept();raw.settimeout(5)
        with context.wrap_socket(raw,server_side=True) as connection:
            data=exact(connection,b'phase-a-linux\n');connection.sendall(b'phase-a-ack\n')
            accepted(connection,data)
            try:connection.unwrap().close()
            except ssl.SSLError:pass
    else:
        with socket.create_connection(('127.0.0.1',int(sys.argv[5])),timeout=5) as raw:
            with context.wrap_socket(raw,server_hostname=sys.argv[6]) as connection:
                connection.sendall(b'phase-a-linux\n');data=exact(connection,b'phase-a-ack\n')
                accepted(connection,data)
                try:connection.unwrap().close()
                except ssl.SSLError:pass
except Exception as exc:
    print(json.dumps({'status':'rejected','error_type':type(exc).__name__,'error':str(exc),
        'verify_code':getattr(exc,'verify_code',None),'verify_message':getattr(exc,'verify_message',None)}),flush=True)
    sys.exit(2)
finally:
    if listener is not None:listener.close()
'''


def run(arguments, *, data=None, env=None):
    try:
        result = subprocess.run(arguments, input=data, capture_output=True,
                                text=True, timeout=12, env=env)
        return {'arguments': arguments, 'exit_code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as exc:
        return {'arguments': arguments, 'exit_code': None, 'timed_out': True,
                'stdout': (exc.stdout or b'').decode(errors='replace'),
                'stderr': (exc.stderr or b'').decode(errors='replace')}


def terminal(result):
    rows = [json.loads(line) for line in result['stdout'].splitlines() if line.startswith('{')]
    assert len(rows) == 1, 'must have exactly one endpoint result'
    return rows[0]


def finish(process, terminate=False):
    if terminate and process.poll() is None:
        process.terminate()
    try:
        out, err = process.communicate(timeout=7)
        return {'exit_code': process.returncode, 'stdout': out or '', 'stderr': err or ''}
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate(timeout=2)
        return {'exit_code': process.returncode, 'timed_out': True,
                'stdout': out or '', 'stderr': err or ''}


def main():
    minimal = '--minimal' in sys.argv
    root = Path(tempfile.mkdtemp(prefix='pqc-linux-tls-'))
    (root / 'policy.cnf').write_text(CONF)
    (root / 'endpoint.py').write_text(CHILD)
    (root / 'empty.cnf').write_text('# Isolated CLI policy\n')
    env = dict(os.environ)
    for name in ('OPENSSL_CONF', 'OPENSSL_CONF_INCLUDE', 'OPENSSL_MODULES', 'OPENSSL_ENGINES'):
        env.pop(name, None)
    env['OPENSSL_CONF'] = str(root / 'empty.cnf')
    configured = dict(env, OPENSSL_CONF=str(root / 'policy.cnf'))
    cases, provisioning = [], []
    hashes = {}
    report = {'status': 'failed', 'mode': 'minimal' if minimal else 'full',
              'runtime': {'python': platform.python_version(), 'platform': platform.platform()},
              'policy': CONF, 'policy_sha256': hashlib.sha256(CONF.encode()).hexdigest(),
              'cases': cases, 'provisioning': provisioning, 'certificate_der_sha256': hashes,
              'scope': 'isolated adapter feasibility; no application integration, authorization or durable ACK',
              'references': ['https://docs.openssl.org/3.5/man5/config/',
                             'https://docs.openssl.org/3.5/man3/SSL_CONF_cmd/',
                             'https://docs.python.org/3.12/library/ssl.html']}

    def provision(*arguments):
        result = run(['openssl', *arguments], env=env)
        provisioning.append(result)
        assert result['exit_code'] == 0, 'certificate provisioning failed'
        return result

    def python_server(identity='server'):
        ready = root / 'ready.json'
        ready.unlink(missing_ok=True)
        process = subprocess.Popen([sys.executable, '-I', str(root / 'endpoint.py'),
                                    'server', str(root), CONF, identity],
                                   env=configured, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 3
            while not ready.exists():
                assert process.poll() is None and time.monotonic() < deadline, 'Python server readiness failed'
                time.sleep(.02)
            return process, json.loads(ready.read_text())['port']
        except BaseException:
            finish(process, terminate=True)
            raise

    def python_client(port, *, hostname='localhost'):
        return run([sys.executable, '-I', str(root / 'endpoint.py'), 'client',
                    str(root), CONF, 'client', str(port), hostname], env=configured)

    def success(result, message, peer):
        endpoint = terminal(result)
        assert result['exit_code'] == 0 and not result.get('timed_out'), result
        assert endpoint['status'] == 'accepted' and endpoint['protocol'] == 'TLSv1.3', endpoint
        assert endpoint['received_hex'] == message.encode().hex(), endpoint
        assert endpoint['peer_der_sha256'] == hashes[peer], endpoint
        assert endpoint['peer_identity']['subject'] and not endpoint['session_reused'], endpoint

    def server_case(label, *, identity='client', group='X25519MLKEM768', protocol='-tls1_3', error=None, verify_code=None):
        process, port = python_server()
        record = {'case': label, 'expected': 'reject' if error else 'accept'}
        cases.append(record)
        args = ['openssl', 's_client', '-connect', '127.0.0.1:' + str(port),
                '-servername', 'localhost', '-verify_hostname', 'localhost', '-verify_return_error',
                '-CAfile', str(root / 'ca.crt'), protocol, '-groups', group, '-brief',
                '-ign_eof', '-ignore_unexpected_eof']
        if identity != 'none':
            args += ['-cert', str(root / (identity + '.crt')), '-key', str(root / (identity + '.key'))]
        try:
            record['client'] = run(args, data=REQUEST, env=env)
            record['server'] = finish(process)
        finally:
            if process.poll() is None:
                finish(process, terminate=True)
        if error:
            endpoint = terminal(record['server'])
            assert record['server']['exit_code'] == 2 and not record['server'].get('timed_out'), record
            assert endpoint['status'] == 'rejected' and endpoint['error_type'] in ('SSLError', 'SSLCertVerificationError'), record
            assert error in endpoint['error'].lower(), record
            if verify_code is not None:
                assert endpoint['verify_code'] == verify_code, record
            assert record['client']['exit_code'] not in (0, None), record
            assert not record['client']['stdout'], 'rejected identity must receive no application reply'
        else:
            success(record['server'], REQUEST, 'client')
            assert record['client']['exit_code'] == 0 and not record['client'].get('timed_out'), record
            assert RESPONSE in record['client']['stdout'], record
            assert 'Negotiated TLS1.3 group: X25519MLKEM768' in record['client']['stderr'], record
            record['negotiated_group'] = 'X25519MLKEM768'
        record['passed'] = True

    def client_case(label, *, identity='server', group='X25519MLKEM768',
                    protocol='-tls1_3', hostname='localhost', error=None, verify_code=None):
        # The reserved ephemeral port is released before CLI bind. A bind race
        # fails readiness rather than being mistaken for a TLS policy rejection.
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        log = root / (label + '.log')
        arguments = ['openssl', 's_server', '-accept', '127.0.0.1:' + str(port),
                     '-cert', str(root / (identity + '.crt')), '-key', str(root / (identity + '.key')),
                     '-CAfile', str(root / 'ca.crt'), '-Verify', '1', '-verify_return_error',
                     protocol, '-groups', group, '-num_tickets', '0', '-naccept', '1', '-ign_eof', '-trace']
        record = {'case': label, 'expected': 'reject' if error else 'accept', 'server_arguments': arguments}
        cases.append(record)
        with log.open('w') as output:
            process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=output,
                                       stderr=subprocess.STDOUT, env=env, text=True)
            try:
                deadline = time.monotonic() + 3
                while 'ACCEPT' not in log.read_text():
                    assert process.poll() is None and time.monotonic() < deadline, 'CLI server readiness failed'
                    time.sleep(.02)
                process.stdin.write(RESPONSE)
                process.stdin.flush()
                record['client'] = python_client(port, hostname=hostname)
                process.stdin.close()
                process.stdin = None
                record['server'] = finish(process)
            finally:
                if process.poll() is None:
                    finish(process, terminate=True)
        record['server']['stdout'] = log.read_text()
        if error:
            endpoint = terminal(record['client'])
            assert record['client']['exit_code'] == 2 and not record['client'].get('timed_out'), record
            assert endpoint['status'] == 'rejected' and endpoint['error_type'] in ('SSLError', 'SSLCertVerificationError'), record
            assert error in endpoint['error'].lower(), record
            if verify_code is not None:
                assert endpoint['verify_code'] == verify_code, record
            assert not record['server'].get('timed_out'), record
        else:
            success(record['client'], RESPONSE, 'server')
            assert not record['server'].get('timed_out'), record
            server_hello = record['server']['stdout'].split('ServerHello,', 1)[1].split('key_exchange:', 1)[0]
            assert 'extension_type=key_share(51)' in server_hello, record
            assert 'NamedGroup: X25519MLKEM768 (4588)' in server_hello, record
            record['negotiated_group'] = 'X25519MLKEM768'
        record['passed'] = True

    try:
        report['runtime']['openssl_cli'] = provision('version', '-a')['stdout']
        for ca in ('ca', 'other-ca'):
            provision('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(root / (ca + '.key')),
                      '-out', str(root / (ca + '.crt')), '-days', '1', '-subj', '/CN=Phase A ' + ca,
                      '-addext', 'basicConstraints=critical,CA:TRUE',
                      '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
        identities = [('server', 'ca', 'serverAuth'), ('client', 'ca', 'clientAuth')]
        if not minimal:
            identities += [('untrusted-server', 'other-ca', 'serverAuth'), ('expired-server', 'ca', 'serverAuth'),
                           ('untrusted-client', 'other-ca', 'clientAuth'), ('expired-client', 'ca', 'clientAuth')]
        for name, ca, purpose in identities:
            provision('req', '-new', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(root / (name + '.key')),
                      '-out', str(root / (name + '.csr')), '-subj', '/CN=' +
                      ('localhost' if purpose == 'serverAuth' else 'phase-a-client'))
            ext = root / (name + '.ext')
            ext.write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\n'
                           'extendedKeyUsage=' + purpose + '\n' +
                           ('subjectAltName=DNS:localhost\n' if purpose == 'serverAuth' else ''))
            if name.startswith('expired'):
                database = root / (name + '.index')
                serial = root / (name + '.serial')
                database.write_text('')
                serial.write_text('1000\n')
                signer = root / (name + '.sign.cnf')
                signer.write_text('[ca]\ndefault_ca=probe\n[probe]\ndatabase=' + str(database) +
                                  '\nserial=' + str(serial) + '\nnew_certs_dir=' + str(root) +
                                  '\ncertificate=' + str(root / (ca + '.crt')) + '\nprivate_key=' +
                                  str(root / (ca + '.key')) + '\ndefault_md=sha256\npolicy=names\n'
                                  'unique_subject=no\n[names]\ncommonName=supplied\n')
                provision('ca', '-batch', '-notext', '-config', str(signer),
                          '-in', str(root / (name + '.csr')), '-out', str(root / (name + '.crt')),
                          '-extfile', str(ext), '-startdate', '20000101000000Z', '-enddate', '20000102000000Z')
            else:
                provision('x509', '-req', '-in', str(root / (name + '.csr')), '-CA', str(root / (ca + '.crt')),
                          '-CAkey', str(root / (ca + '.key')), '-CAcreateserial', '-out', str(root / (name + '.crt')),
                          '-days', '1', '-extfile', str(ext))
            der = subprocess.run(['openssl', 'x509', '-in', str(root / (name + '.crt')), '-outform', 'DER'],
                                 env=env, capture_output=True, check=True, timeout=5).stdout
            hashes[name] = hashlib.sha256(der).hexdigest()
            provision('x509', '-in', str(root / (name + '.crt')), '-noout', '-subject', '-issuer', '-dates')
        server_case('python_server_hybrid')
        server_case('python_server_classical_rejected', group='X25519', error='no suitable key share')
        if not minimal:
            server, port = python_server()
            record = {'case': 'python_to_python_exact_roundtrip', 'expected': 'accept'}
            cases.append(record)
            try:
                record['client'] = python_client(port)
                record['server'] = finish(server)
            finally:
                if server.poll() is None:
                    finish(server, terminate=True)
            success(record['client'], RESPONSE, 'server')
            success(record['server'], REQUEST, 'client')
            record['passed'] = True
            server, port = python_server()
            record = {'case': 'python_server_plaintext_rejected', 'expected': 'reject'}
            cases.append(record)
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=3) as raw:
                    raw.sendall(REQUEST.encode())
                    try:
                        record['received_hex'] = raw.recv(4096).hex()
                    except ConnectionResetError:
                        record['received_hex'] = ''
                record['server'] = finish(server)
            finally:
                if server.poll() is None:
                    finish(server, terminate=True)
            endpoint = terminal(record['server'])
            assert record['server']['exit_code'] == 2 and not record['server'].get('timed_out'), record
            assert endpoint['status'] == 'rejected' and 'WRONG_VERSION_NUMBER' in endpoint['error'], record
            assert RESPONSE.encode().hex() not in record['received_hex'], record
            record['passed'] = True
            server_case('python_server_no_client_certificate', identity='none', error='peer did not return a certificate')
            server_case('python_server_untrusted_client', identity='untrusted-client', error='unable to get local issuer certificate', verify_code=20)
            server_case('python_server_expired_client', identity='expired-client', error='certificate has expired', verify_code=10)
            server_case('python_server_tls12_rejected', group='X25519', protocol='-tls1_2', error='unsupported protocol')
            client_case('python_client_hybrid')
            client_case('python_client_classical_rejected', group='X25519', error='handshake failure')
            client_case('python_client_untrusted_server', identity='untrusted-server', error='unable to get local issuer certificate', verify_code=20)
            client_case('python_client_expired_server', identity='expired-server', error='certificate has expired', verify_code=10)
            client_case('python_client_wrong_hostname', hostname='wrong.invalid', error='hostname mismatch', verify_code=62)
            client_case('python_client_tls12_rejected', group='X25519', protocol='-tls1_2', error='protocol version')
        for role in ('server', 'client'):
            for policy in ('unset', 'missing', 'wrong', 'malformed'):
                bad_env = dict(configured)
                if policy == 'unset':
                    bad_env.pop('OPENSSL_CONF')
                else:
                    path = root / (policy + '.cnf')
                    if policy == 'wrong':
                        path.write_text(CONF.replace('X25519MLKEM768', 'X25519'))
                    elif policy == 'malformed':
                        path.write_text('openssl_conf = broken\n[ invalid\n')
                    bad_env['OPENSSL_CONF'] = str(path)
                record = {'case': role + '_config_' + policy, 'expected': 'config-reject'}
                cases.append(record)
                result = run([sys.executable, '-I', str(root / 'endpoint.py'), role,
                              str(root), CONF, role, '1', 'localhost'], env=bad_env)
                record['endpoint'] = result
                endpoint = terminal(result)
                assert result['exit_code'] == 3 and endpoint['status'] == 'config-rejected', record
                record['passed'] = True
        import ssl
        report['runtime']['python_ssl'] = ssl.OPENSSL_VERSION
        report['passed_count'] = sum(case.get('passed', False) for case in cases)
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
