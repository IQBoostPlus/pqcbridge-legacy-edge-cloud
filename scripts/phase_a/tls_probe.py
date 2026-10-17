"""Isolated, fail-closed TLS CLI interoperability probe (not app transport).

Only Python's standard library is used. Credentials and raw process output stay
in --artifacts, outside the checkout; --summary contains no private material.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import ssl
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openssl", required=True, type=Path)
    parser.add_argument("--client-openssl", type=Path,
                        help="Optional distinct OpenSSL client for interoperability")
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    executable = args.openssl.resolve(strict=True)
    client_executable = (args.client_openssl or args.openssl).resolve(strict=True)
    root = args.artifacts.resolve()
    checkout = Path(__file__).resolve().parents[2]
    if root == checkout or checkout in root.parents:
        parser.error("Credential/raw artifact directory must be outside checkout")
    root.mkdir(parents=True, exist_ok=False)
    (root / "empty-openssl.cnf").write_text("# Isolated probe configuration\n")
    env = dict(os.environ)
    # Do not inherit machine/user OpenSSL configuration or provider selection.
    for key in ("OPENSSL_CONF", "OPENSSL_CONF_INCLUDE", "OPENSSL_MODULES", "OPENSSL_ENGINES"):
        env.pop(key, None)
    env["OPENSSL_CONF"] = str(root / "empty-openssl.cnf")
    commands = []

    def run(label: str, *parts: str, expected: int = 0, binary=None) -> str:
        command = [str(binary or executable), *parts]
        result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                text=True, timeout=30)
        (root / f"{label}.log").write_text(result.stdout + result.stderr)
        commands.append({"label": label, "args": list(parts), "returncode": result.returncode})
        if result.returncode != expected:
            raise RuntimeError(f"{label}: unexpected exit {result.returncode}; see external log")
        return result.stdout + result.stderr

    version = run("version", "version", "-a")
    client_version = run("client-version", "version", "-a", binary=client_executable)
    groups = run("groups", "list", "-tls1_3", "-tls-groups")
    # Conventional certificate signatures authenticate hybrid key exchange.
    for ca in ("ca", "other-ca"):
        run(ca, "req", "-new", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", f"{ca}.key", "-out", f"{ca}.pem", "-days", "2",
            "-subj", f"/CN=Phase-A-{ca}", "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    for name, issuer, purpose, days in (
        ("server", "ca", "serverAuth", "1"),
        ("client", "ca", "clientAuth", "1"),
        ("untrusted-client", "other-ca", "clientAuth", "1"),
        ("expired-client", "ca", "clientAuth", "-1"),
    ):
        run(f"{name}-csr", "req", "-new", "-newkey", "rsa:2048", "-nodes",
            "-keyout", f"{name}.key", "-out", f"{name}.csr", "-subj", f"/CN={name}")
        ext = ["basicConstraints=critical,CA:FALSE", "keyUsage=critical,digitalSignature",
               f"extendedKeyUsage={purpose}"]
        if name == "server":
            ext.append("subjectAltName=DNS:localhost,IP:127.0.0.1")
        (root / f"{name}.ext").write_text("\n".join(ext) + "\n")
        if days == "-1":
            (root / "ca-index.txt").write_text("")
            (root / "ca-serial.txt").write_text("1000\n")
            (root / "expired-sign.cnf").write_text(
                "[ca]\ndefault_ca=probe\n[probe]\ndatabase=ca-index.txt\n"
                "serial=ca-serial.txt\nnew_certs_dir=.\ncertificate=ca.pem\n"
                "private_key=ca.key\ndefault_md=sha256\npolicy=names\n"
                "[names]\ncommonName=supplied\n")
            run(f"{name}-sign", "ca", "-batch", "-notext", "-config", "expired-sign.cnf",
                "-in", f"{name}.csr", "-out", f"{name}.pem", "-extfile", f"{name}.ext",
                "-startdate", "20000101000000Z", "-enddate", "20000102000000Z")
        else:
            run(f"{name}-sign", "x509", "-req", "-in", f"{name}.csr",
                "-CA", f"{issuer}.pem", "-CAkey", f"{issuer}.key", "-CAcreateserial",
                "-out", f"{name}.pem", "-days", days, "-extfile", f"{name}.ext")
    # Record actual notBefore/notAfter so expiration is independently inspectable.
    expired_dates = run("expired-dates", "x509", "-in", "expired-client.pem", "-noout", "-dates")
    ca_fingerprint = run("ca-fingerprint", "x509", "-in", "ca.pem", "-noout", "-fingerprint", "-sha256").strip()
    cases = []

    def probe(label: str, server_group: str, client_group: str, *, identity="client",
              trust="ca", hostname="localhost", protocol="-tls1_3", reject=None) -> None:
        # Reserve an ephemeral loopback port, then let OpenSSL bind it. A rare
        # race fails this probe; it is never counted as a TLS-policy rejection.
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        common = ["-no-CAfile", "-no-CApath", "-no-CAstore", "-verify_return_error"]
        server_args = ["s_server", "-accept", f"127.0.0.1:{port}", "-cert", "server.pem",
                       "-key", "server.key", "-CAfile", "ca.pem", "-Verify", "2",
                       "-tls1_3", "-groups", server_group, "-no_ticket", "-num_tickets", "0",
                       "-max_early_data", "0", "-recv_max_early_data", "0",
                       "-naccept", "1", "-rev", *common]
        client_args = ["s_client", "-connect", f"127.0.0.1:{port}", "-servername", "localhost",
                       "-verify_hostname", hostname, "-CAfile", f"{trust}.pem", protocol,
                       "-groups", client_group, "-brief", "-ign_eof", *common]
        if identity:
            client_args += ["-cert", f"{identity}.pem", "-key", f"{identity}.key"]
        client_log = root / f"{label}-client.log"
        server_log = root / f"{label}-server.log"
        payload = f"phase-a-{label}-application-proof"
        marker = payload[::-1]
        server = client = None
        client_return = server_return = None
        start = time.monotonic()
        try:
            with server_log.open("w") as server_output, client_log.open("w") as client_output:
                server = subprocess.Popen([str(executable), *server_args], cwd=root, env=env,
                                          stdin=subprocess.DEVNULL, stdout=server_output, stderr=server_output)
                # Startup detection uses the server's ACCEPT line; no connection
                # consumes -naccept before the actual test client arrives.
                deadline = time.monotonic() + 5
                while "ACCEPT" not in server_log.read_text(errors="replace"):
                    if server.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError(f"{label}: server startup failed (not a TLS rejection)")
                    time.sleep(0.025)
                client = subprocess.Popen([str(client_executable), *client_args], cwd=root, env=env,
                                          stdin=subprocess.PIPE, stdout=client_output, stderr=client_output)
                client.stdin.write((payload + "\n").encode())
                client.stdin.flush()
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    output = client_log.read_text(errors="replace")
                    if marker in output or client.poll() is not None:
                        break
                    time.sleep(0.025)
                client_return = client.poll()
                # Close the diagnostic positive connection after evidence is
                # received; process termination is never itself a pass signal.
                if client.poll() is None:
                    client.terminate()
                client.wait(timeout=3)
                try:
                    server_return = server.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    server.terminate()
                    server.wait(timeout=3)
        finally:
            for process in (client, server):
                if process and process.poll() is None:
                    process.kill()
                    process.wait(timeout=3)
        client_text = client_log.read_text(errors="replace")
        server_text = server_log.read_text(errors="replace")
        group_match = re.search(r"(?:Negotiated TLS1.3 group|Peer Temp Key|Server Temp Key):\s*([^\r\n]+)", client_text)
        negotiated = group_match.group(1).strip() if group_match else None
        bidirectional = marker in client_text
        certificate_ok = "Verification: OK" in client_text
        client_certificate_ok = ("Verification: OK" in server_text
                                 and "Peer certificate: CN=client" in server_text)
        server_accepted = "CONNECTION ESTABLISHED" in server_text
        tls13 = "Protocol version: TLSv1.3" in client_text
        reasons = []
        if reject:
            client_pattern, server_pattern = reject
            client_match = re.search(client_pattern, client_text, re.I)
            server_match = re.search(server_pattern, server_text, re.I)
            passed = bool(client_match and server_match and client_return not in (None, 0)
                          and not bidirectional and not server_accepted)
            reasons = [m.group(0) if m else None for m in (client_match, server_match)]
        else:
            expected_group = "X25519MLKEM768" if "MLKEM" in server_group else "X25519"
            passed = bool(bidirectional and certificate_ok and client_certificate_ok
                          and server_accepted and tls13 and negotiated
                          and expected_group.lower() in negotiated.lower()
                          and "verify error" not in server_text.lower())
        cases.append({"case": label, "passed": passed, "expected": "reject" if reject else "accept",
                      "protocol_tls13": tls13, "negotiated_group": negotiated,
                      "server_certificate_verified": certificate_ok,
                      "client_certificate_verified_by_server": client_certificate_ok,
                      "server_handshake_accepted": server_accepted,
                      "application_round_trip": bidirectional,
                      "rejection_evidence": reasons,
                      "client_natural_exit": client_return, "server_natural_exit": server_return,
                      "elapsed_seconds": round(time.monotonic() - start, 4),
                      "server_args": server_args, "client_args": client_args,
                      "client_log_sha256": hashlib.sha256(client_log.read_bytes()).hexdigest(),
                      "server_log_sha256": hashlib.sha256(server_log.read_bytes()).hexdigest()})

    hybrid = "X25519MLKEM768" in groups
    selected = "X25519MLKEM768" if hybrid else "X25519"
    probe("valid-mutual-auth", selected, selected)
    probe("missing-client-certificate", selected, selected, identity=None,
          reject=(r"alert certificate required", r"peer did not return a certificate"))
    probe("untrusted-client-certificate", selected, selected, identity="untrusted-client",
          reject=(r"alert unknown ca", r"certificate verify failed"))
    probe("expired-client-certificate", selected, selected, identity="expired-client",
          reject=(r"alert certificate expired", r"certificate has expired"))
    probe("untrusted-server-certificate", selected, selected, trust="other-ca",
          reject=(r"certificate verify failed", r"alert unknown ca"))
    probe("server-hostname-mismatch", selected, selected, hostname="wrong.invalid",
          reject=(r"hostname mismatch", r"alert bad certificate"))
    probe("tls12-peer-rejected", selected, "X25519", protocol="-tls1_2",
          reject=(r"alert protocol version", r"unsupported protocol"))
    if hybrid:
        probe("mandatory-hybrid-rejects-classical", selected, "X25519",
              reject=(r"alert handshake failure", r"no suitable key share"))
        probe("conventional-control", "X25519", "X25519")
    report = {"schema_version": 1, "scope": "local isolated OpenSSL CLI prevalidation; not application or deployment acceptance",
              "status": "PASS_LOCAL_PREVALIDATION" if hybrid and all(c["passed"] for c in cases) else "BLOCKED_OR_FAILED",
              "utc_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "python": sys.version, "python_ssl": ssl.OPENSSL_VERSION,
              "os": platform.platform(), "openssl_path": str(executable),
              "openssl_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "openssl_version": version, "tls13_groups": groups.strip(),
              "client_openssl_path": str(client_executable), "client_openssl_version": client_version,
              "client_openssl_sha256": hashlib.sha256(client_executable.read_bytes()).hexdigest(),
              "hybrid_supported": hybrid, "test_ca_fingerprint": ca_fingerprint,
              "expired_certificate_dates": expired_dates.strip(),
              "effective_policy": {"server_protocol": "TLSv1.3 only", "client_protocol": "TLSv1.3 except negative TLS1.2 case",
                                   "mutual_authentication": "mandatory client certificate, fatal verification errors",
                                   "groups": selected, "early_data_maximum": 0, "tickets": 0,
                                   "trust": "fresh isolated explicit CA only; default trust stores disabled",
                                   "openssl_config": "fresh explicit empty configuration, inherited provider variables removed"},
              "certificate_commands": commands, "cases": cases,
              "raw_artifacts": str(root)}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "passed": sum(c["passed"] for c in cases),
                      "total": len(cases), "summary": str(args.summary)}))
    return 0 if report["status"] == "PASS_LOCAL_PREVALIDATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
