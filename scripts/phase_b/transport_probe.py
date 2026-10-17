"""Container-only acceptance of the production-candidate TLS transport API.

Run in a pinned, network-none container with fresh /tmp tmpfs credentials.
Uses application APIs in fresh Python subprocesses; OpenSSL CLI is an
independent peer and certificate fixture generator, never app transport.
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


CHILD = r'''
import sys
from common.secure_transport import (initialize_tls_policy, client_context,
    server_context, peer_fingerprint, read_frame, send_frame, SocketFrameReader)
initialize_tls_policy()
import json,socket,time
from pathlib import Path
role=sys.argv[1];root=Path(sys.argv[2]);identity=sys.argv[3]
tls={name+'_file':str(root/(identity+suffix)) for name,suffix in [('cert','.crt'),('key','.key')]}
tls['ca_file']=str(root/'ca.crt');tls['server_hostname']='localhost'
listener=None
frame_started=None
try:
    if role.startswith('server'):
        context=server_context(tls)
        listener=socket.socket();listener.settimeout(5);listener.bind(('127.0.0.1',0));listener.listen(1)
        (root/'ready.json').write_text(json.dumps({'port':listener.getsockname()[1]}))
        raw,_=listener.accept();raw.settimeout(5)
        with raw,context.wrap_socket(raw,server_side=True) as connection:
            fingerprint=peer_fingerprint(connection)
            with SocketFrameReader(connection) as stream:
                stream.set_deadline(.2 if role=='server_trickle' else 5)
                frame_started=time.monotonic()
                frame=read_frame(stream)
                if frame!={'marker':'phase-b-request'}:raise ValueError('unexpected request')
                if role=='server_coalesced':
                    for sequence in (1,2):
                        if not stream.wait_readable(.1):raise ValueError('buffered TLS frame not readable')
                        stream.set_deadline(5)
                        if read_frame(stream)!={'sequence':sequence}:raise ValueError('queued frame mismatch')
                send_frame(connection,{'marker':'phase-b-ack'})
                print(json.dumps({'status':'accepted','protocol':connection.version(),
                    'peer_sha256':fingerprint,'session_reused':connection.session_reused,'received':frame}),flush=True)
    else:
        tls['server_hostname']=sys.argv[5]
        context=client_context(tls)
        with socket.create_connection(('127.0.0.1',int(sys.argv[4])),timeout=5) as raw:
            with context.wrap_socket(raw,server_hostname=tls['server_hostname']) as connection:
                fingerprint=peer_fingerprint(connection)
                if role=='client_coalesced':
                    connection.sendall(b'{"marker":"phase-b-request"}\n{"sequence":1}\n{"sequence":2}\n')
                elif role=='client_trickle':
                    for byte in b'{"marker":"'+b'x'*60+b'"}\n':
                        connection.sendall(bytes([byte]));time.sleep(.035)
                else:
                    send_frame(connection,{'marker':'phase-b-request'})
                with SocketFrameReader(connection) as stream:
                    stream.set_deadline(5)
                    frame=read_frame(stream)
                if frame!={'marker':'phase-b-ack'}:raise ValueError('unexpected response')
                print(json.dumps({'status':'accepted','protocol':connection.version(),
                    'peer_sha256':fingerprint,'session_reused':connection.session_reused,'received':frame}),flush=True)
except Exception as exc:
    print(json.dumps({'status':'rejected','error_type':type(exc).__name__,
        'error':str(exc),'verify_code':getattr(exc,'verify_code',None),
        'frame_elapsed_seconds':None if frame_started is None else time.monotonic()-frame_started}),flush=True)
    sys.exit(2)
finally:
    if listener is not None:listener.close()
'''


def run(arguments, *, env, data=None):
    result = subprocess.run(arguments, input=data, env=env, capture_output=True,
                            text=True, timeout=10)
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def finish(process):
    stdout, stderr = process.communicate(timeout=7)
    return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr}


def stop(process):
    if process.poll() is None:
        process.kill()
        process.communicate(timeout=2)


def endpoint(result):
    rows = [json.loads(line) for line in result["stdout"].splitlines() if line.startswith("{")]
    assert len(rows) == 1, result
    return rows[0]


def main():
    project = Path(__file__).resolve().parents[2]
    root = Path(tempfile.mkdtemp(prefix="pqc-phase-b-transport-"))
    empty = root / "empty.cnf"
    empty.write_text("# isolated fixture generator\n")
    env = dict(os.environ)
    for name in ("OPENSSL_CONF", "OPENSSL_CONF_INCLUDE", "OPENSSL_MODULES", "OPENSSL_ENGINES"):
        env.pop(name, None)
    env["OPENSSL_CONF"] = str(empty)
    configured = dict(env, OPENSSL_CONF=str(project / "deploy/phase_b/tls-policy.cnf"))
    cases = []
    report = {"status": "failed", "scope": "actual secure_transport APIs; fresh local synthetic peers",
              "runtime": {"python": platform.python_version(), "platform": platform.platform()},
              "source_sha256": {str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (project / "common/secure_transport.py",
                                             project / "deploy/phase_b/tls-policy.cnf",
                                             Path(__file__).resolve())},
              "cases": cases}
    fingerprints = {}

    def provision(*arguments):
        result = run(["openssl", *arguments], env=env)
        assert result["exit_code"] == 0, result
        return result

    def server(role="server"):
        ready = root / "ready.json"
        ready.unlink(missing_ok=True)
        process = subprocess.Popen([sys.executable, "-B", "-c", CHILD, role, str(root), "server"],
                                   env=configured, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 3
            while not ready.exists():
                assert process.poll() is None and time.monotonic() < deadline, "server readiness failed"
                time.sleep(.02)
            return process, json.loads(ready.read_text())["port"]
        except BaseException:
            stop(process)
            raise

    def accepted(result, peer, received):
        item = endpoint(result)
        assert result["exit_code"] == 0 and item["status"] == "accepted", result
        assert item["protocol"] == "TLSv1.3" and not item["session_reused"], item
        assert item["peer_sha256"] == fingerprints[peer] and item["received"] == {"marker": received}, item

    def cli_case(name, identity="client", group="X25519MLKEM768", error=None, verify_code=None):
        process, port = server()
        item = {"case": name, "expected": "reject" if error else "accept"}
        cases.append(item)
        command = ["openssl", "s_client", "-connect", "127.0.0.1:" + str(port), "-servername", "localhost",
                   "-verify_hostname", "localhost", "-verify_return_error", "-CAfile", str(root / "ca.crt"),
                   "-tls1_3", "-groups", group, "-brief", "-ign_eof", "-ignore_unexpected_eof"]
        if identity:
            command += ["-cert", str(root / (identity + ".crt")), "-key", str(root / (identity + ".key"))]
        try:
            item["client"] = run(command, data='{"marker":"phase-b-request"}\n', env=env)
            item["server"] = finish(process)
            if error:
                rejected = endpoint(item["server"])
                assert item["server"]["exit_code"] == 2 and rejected["status"] == "rejected", item
                assert error in rejected["error"].lower(), item
                if verify_code is not None:
                    assert rejected["verify_code"] == verify_code, item
                assert item["client"]["exit_code"] != 0 and not item["client"]["stdout"], item
            else:
                accepted(item["server"], "client", "phase-b-request")
                assert item["client"]["exit_code"] == 0, item
                assert item["client"]["stdout"] == '{"marker":"phase-b-ack"}\n', item
                assert "Negotiated TLS1.3 group: X25519MLKEM768" in item["client"]["stderr"], item
                item["negotiated_group"] = "X25519MLKEM768"
            item["passed"] = True
        finally:
            stop(process)

    try:
        report["runtime"]["openssl"] = provision("version")["stdout"].strip()
        for name in ("ca", "other-ca"):
            provision("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(root / (name + ".key")),
                      "-out", str(root / (name + ".crt")), "-days", "1", "-subj", "/CN=Phase B " + name,
                      "-addext", "basicConstraints=critical,CA:TRUE",
                      "-addext", "keyUsage=critical,keyCertSign,cRLSign")
        for name, ca, purpose in (("server", "ca", "serverAuth"), ("client", "ca", "clientAuth"),
                                  ("untrusted-client", "other-ca", "clientAuth")):
            provision("req", "-new", "-newkey", "rsa:2048", "-nodes", "-keyout", str(root / (name + ".key")),
                      "-out", str(root / (name + ".csr")), "-subj", "/CN=" + name)
            extension = root / (name + ".ext")
            extension.write_text("basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\n"
                                 "extendedKeyUsage=" + purpose + "\n" +
                                 ("subjectAltName=DNS:localhost\n" if purpose == "serverAuth" else ""))
            provision("x509", "-req", "-in", str(root / (name + ".csr")), "-CA", str(root / (ca + ".crt")),
                      "-CAkey", str(root / (ca + ".key")), "-CAcreateserial", "-out", str(root / (name + ".crt")),
                      "-days", "1", "-extfile", str(extension))
            der = subprocess.run(["openssl", "x509", "-in", str(root / (name + ".crt")), "-outform", "DER"],
                                 env=env, capture_output=True, check=True, timeout=5).stdout
            fingerprints[name] = hashlib.sha256(der).hexdigest()
        reader_only = "--reader-only" in sys.argv
        report["mode"] = "reader-only" if reader_only else "full"
        if not reader_only:
            cli_case("actual_api_server_hybrid")
            cli_case("actual_api_server_classical_rejected", group="X25519", error="no suitable key share")
            cli_case("actual_api_missing_client_certificate", identity=None, error="peer did not return a certificate")
            cli_case("actual_api_untrusted_client", identity="untrusted-client", error="unable to get local issuer certificate", verify_code=20)
        for hostname in (("localhost",) if reader_only else ("localhost", "wrong.invalid")):
            process, port = server("server_coalesced" if reader_only else "server")
            item = {"case": "actual_api_tls_coalesced_frames" if reader_only else "actual_api_python_roundtrip" if hostname == "localhost" else "actual_api_wrong_hostname",
                    "expected": "accept" if hostname == "localhost" else "reject"}
            cases.append(item)
            try:
                item["client"] = run([sys.executable, "-B", "-c", CHILD, "client_coalesced" if reader_only else "client", str(root), "client", str(port), hostname], env=configured)
                item["server"] = finish(process)
                if hostname == "localhost":
                    accepted(item["client"], "server", "phase-b-ack")
                    accepted(item["server"], "client", "phase-b-request")
                else:
                    rejected = endpoint(item["client"])
                    assert item["client"]["exit_code"] == 2 and rejected["verify_code"] == 62, item
                    assert item["server"]["exit_code"] == 2 and endpoint(item["server"])["status"] == "rejected", item
                item["passed"] = True
            finally:
                stop(process)
        if reader_only:
            process, port = server("server_trickle")
            item = {"case": "actual_api_tls_whole_frame_trickle_deadline", "expected": "reject"}
            cases.append(item)
            try:
                started = time.monotonic()
                item["client"] = run([sys.executable, "-B", "-c", CHILD, "client_trickle", str(root), "client", str(port), "localhost"], env=configured)
                item["server"] = finish(process)
                rejected = endpoint(item["server"])
                assert item["server"]["exit_code"] == 2 and rejected["error_type"] == "TimeoutError", item
                assert .18 <= rejected["frame_elapsed_seconds"] < .8, item
                assert item["client"]["exit_code"] != 0 and endpoint(item["client"])["status"] == "rejected", item
                assert time.monotonic() - started < 2, item
                item["passed"] = True
            finally:
                stop(process)
            report["status"] = "passed"
            report["passed_count"] = sum(item.get("passed", False) for item in cases)
            print(json.dumps(report, indent=2))
            return 0
        process, port = server()
        item = {"case": "actual_api_plaintext_rejected", "expected": "reject"}
        cases.append(item)
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=3) as plain:
                plain.sendall(b'{"marker":"phase-b-request"}\n')
                try:
                    item["received_hex"] = plain.recv(4096).hex()
                except ConnectionResetError:
                    item["received_hex"] = ""
            item["server"] = finish(process)
            rejected = endpoint(item["server"])
            assert item["server"]["exit_code"] == 2 and "WRONG_VERSION_NUMBER" in rejected["error"], item
            assert b"phase-b-ack".hex() not in item["received_hex"], item
            item["passed"] = True
        finally:
            stop(process)
        report["status"] = "passed"
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    report["passed_count"] = sum(item.get("passed", False) for item in cases)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
