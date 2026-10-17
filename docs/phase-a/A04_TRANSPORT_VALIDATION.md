# A-04: TLS Transport Validation

Date: 2026-10-16. Status: **target Linux adapter feasibility passed; selected
for the revised simulation scope**. Windows checks: 27/27; final Linux checks:
22/22. This selects a transport approach for Phase B, not completed application
integration, business authorization or production acceptance.

The existing application still uses its original TCP/JSON-lines transport. This
work adds an isolated transport probe and evidence, without replacing the
application transport or claiming Phase B implementation is complete.

## Scope and source of requirements

The project sources describe a software-only simulation of legacy devices,
gateway, and cloud. The deployment baseline is Linux Docker using
`python:3.12-slim` in `Dockerfile.device`, `Dockerfile.gateway`, and
`Dockerfile.cloud`; CI uses Ubuntu and Python 3.12. The Windows developer
environment is a secondary validation environment. A real embedded device is
outside the original P01 scope; no unrecorded hardware requirement is invented
for this experiment. See `prompt/P01 - Initial Baseline Generation.md`,
`README.md`, and the A-02 scenario record for the overall scope reconciliation.

A-04 in `docs/SHORT_TERM_PLAN.md` requires actual TLS 1.3, mutual
authentication, negotiated hybrid group evidence, and rejection of peers
without required hybrid support. Importing an ML-KEM implementation does not
meet these requirements.

## Runtime versions and deployment boundary

- Windows developer Python 3.12: `ssl.OPENSSL_VERSION` is **OpenSSL 3.0.11
  19 Sep 2023**. The probe uses Python only to orchestrate processes. Python
  `ssl` does not carry the tested TLS sessions, and this run does not demonstrate
  hybrid support in that Python runtime.
- Git for Windows executable `D:\Git\usr\bin\openssl.exe`: executable and
  loaded library both report **OpenSSL 3.5.3, 16 Sep 2025**.
- MSYS executable `C:\msys64\usr\bin\openssl.exe`: executable and loaded
  library both report **OpenSSL 3.5.2, 5 Aug 2025**.
- Actual target experiment: immutable local image
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  Linux x86-64, Python **3.12.14**, Python ssl and CLI **OpenSSL 3.5.7**.
  The final TLS run observed WSL kernel 6.18.54.1. A06's earlier Docker baseline
  observed kernel 6.6.87.2; these are separate snapshots, not an assertion of
  unchanged host runtime. The original Dockerfiles still use a floating tag;
  only this experiment is pinned by immutable image identity.

The version output, executable SHA-256 hashes, exact arguments, and independent
endpoint log SHA-256 hashes are included in the sanitized JSON evidence. These
installed binaries are experiment candidates; their presence and successful
handshakes are not a dependency security/support audit or a release pin.

## Executed interoperability checks

Three separate suites passed **27/27 checks**, each using fresh credentials,
fresh endpoint processes, loopback ephemeral ports, and fresh full handshakes:

1. OpenSSL 3.5.3 server and OpenSSL 3.5.3 client: **9/9**.
   Evidence: `evidence/transport/windows-git-openssl.json`.
2. OpenSSL 3.5.3 server and OpenSSL 3.5.2 client: **9/9**.
   Evidence: `evidence/transport/windows-cross-openssl.json`.
3. OpenSSL 3.5.2 server and OpenSSL 3.5.3 client: **9/9**.
   Evidence: `evidence/transport/windows-reverse-cross-openssl.json`.

These Windows runs use distinct builds of the same TLS implementation family.
Their results alone do not establish Linux behavior. The target Python adapter
checks below add Linux feasibility; cross-vendor interoperability, actual event/ACK
integration, throughput, capacity, reconnection and rotation remain outside these checks.

For every suite, the positive hybrid connection reported all of:

```text
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_256_GCM_SHA384
Verification: OK
Verified peername: localhost
Negotiated TLS1.3 group: X25519MLKEM768
```

The server separately reported `Peer certificate: CN=client`,
`Verification: OK`, and `Peer Temp Key: X25519MLKEM768`. It accepted a
synthetic application line and returned that line reversed through TLS. The
client received the exact reversed marker. A negotiated group alone is not the
application success condition.

Certificates use conventional RSA-2048/SHA-256 signatures (PKCS#1 v1.5);
TLS CertificateVerify uses RSA-PSS/SHA-256. **Hybrid key establishment does not mean post-quantum certificate
authentication**. The certificates are short-lived disposable test identities,
not the project's gateway credential enrollment or authorization system.

## Negative outcomes

Each suite exercised the following actual TLS rejection cases:

- Missing client certificate: client `alert certificate required`; server
  `peer did not return a certificate`.
- Client signed by an untrusted CA: client `alert unknown ca`; server
  `certificate verify failed`.
- Expired client certificate: client `alert certificate expired`; server
  `certificate has expired`. Its actual validity was 2000-01-01 to 2000-01-02
  UTC, signed by the trusted test CA; time verification was never disabled.
- Untrusted server CA: client `certificate verify failed`; server
  `alert unknown ca`.
- Wrong server hostname: client `hostname mismatch`; server
  `alert bad certificate`.
- TLS 1.2 client: client `alert protocol version`; server
  `unsupported protocol`.
- Conventional-only X25519 client against the mandatory-hybrid server:
  client `alert handshake failure`; server `no suitable key share`.

A negative check passes only when both endpoint logs contain the expected TLS
failure, the client exits naturally with a nonzero status, the server never
reports an established connection, and no application round trip occurs.
Startup failures, timeouts, generic network errors, and process termination
cannot satisfy these checks. OpenSSL `s_server` can exit with status 0 after
handling a rejected connection, so its process exit status is recorded but is
not treated as proof of authentication success.

The ninth check is a separately configured conventional TLS 1.3 X25519 mutual
authentication control. It passed with application round trip and the group
reported as `X25519, 253 bits`. This deliberately separate control proves
that the conventional client is functional; it is not an automatic fallback
path for the hybrid profile.

## Effective configuration and isolation

The probe invokes OpenSSL directly with an absolute executable path, writes a
fresh explicit empty configuration, removes inherited OpenSSL provider/config
variables from the child environment, and disables default trust stores.
Each run creates an independent CA, server certificate with localhost SAN,
client certificate with clientAuth EKU, and deliberately invalid identities.

The hybrid server policy is explicit: `-tls1_3 -groups X25519MLKEM768
-Verify 2 -verify_return_error -no_ticket -num_tickets 0 -max_early_data 0
-recv_max_early_data 0`. Clients require trusted certificate validation and
hostname verification through `-verify_return_error -verify_hostname
localhost`, and use TLS 1.3 except for the deliberate TLS 1.2 rejection check.
Both endpoints use only the generated trust anchor. No `-early_data`,
resumption session file, external listener, application port, or original
configuration is used. Session resumption and 0-RTT are disabled for this
experiment.

After a successful marker round trip, the client process is terminated to close
the diagnostic connection; the positive pass condition was already met before
termination. This is not an orderly TLS shutdown test. Every child process is
bounded by timeouts and cleaned up, including on exceptions.

All private keys, raw logs, and initial unsuccessful setup attempts remain
outside the repository under
`D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z\`.
The final raw run directories are `transport-git-openssl-final`,
`transport-git-server-msys-client`, and `transport-msys-server-git-client`.
No credential bytes or raw certificate/key files are included in repository
evidence. An initial attempt to use `x509 -days -1` to construct an expired
certificate was rejected by OpenSSL; the probe now uses explicit historical
CA signing dates, and all final suites use that corrected path.

## Reproduction

From the repository root, with a **new external artifact directory**:

```powershell
python scripts/phase_a/tls_probe.py `
  --openssl 'D:\Git\usr\bin\openssl.exe' `
  --client-openssl 'C:\msys64\usr\bin\openssl.exe' `
  --artifacts 'D:\Code\pqcbridge-phase-a-artifacts\new-transport-run' `
  --summary 'docs/phase-a/evidence/transport/new-transport-run.json'
```

Use the same executable for both endpoints by omitting `--client-openssl`.
Use explicit Linux executable paths in a clean candidate container to repeat
the same checks. Unsupported CLI options, missing groups, or absent hybrid
evidence must block acceptance; do not weaken the profile to make the suite
green. The recorded per-case elapsed values include process orchestration and
are **not handshake latency benchmarks**.

## Selected Linux Python adapter and actual result

Select direct in-process Python `ssl.SSLContext`, linked to OpenSSL 3.5, with a
fixed OpenSSL policy loaded before library initialization in a fresh process.
The public Python `set_ecdh_curve` API rejected X25519MLKEM768; successful
library-version discovery alone was insufficient. The tested solution uses the
official configuration mechanism, not ctypes or a diagnostic server as the
application transport. OpenSSL applies `system_default` to each new SSL context.
[OpenSSL configuration documentation](https://docs.openssl.org/3.5/man5/config/).

```ini
config_diagnostics = 1
openssl_conf = openssl_init
[openssl_init]
ssl_conf = ssl_section
[ssl_section]
system_default = tls_defaults
[tls_defaults]
MinProtocol = TLSv1.3
MaxProtocol = TLSv1.3
Groups = X25519MLKEM768
```

Each endpoint verifies the exact policy bytes before importing ssl. Python
contexts explicitly require TLS 1.3 and trusted peer certificates; the client
also verifies the server hostname. `getpeercert` exposes the verified certificate
and its DER SHA-256 fingerprint directly to the same process that reads bounded
application bytes. No plaintext backend or propagated identity header exists.
This avoids the proxy identity-forwarding boundary; the TLS socket's rejection
of plaintext was tested. These APIs are documented by [Python ssl](https://docs.python.org/3.12/library/ssl.html).

Final evidence: [linux-full-e3864eb459b7.json](evidence/transport/linux-full-e3864eb459b7.json).
Raw host output, observed probe and host source copies:
`D:\Code\pqcbridge-phase-a-artifacts\linux-tls-e3864eb459b74570ac90b3d0b4ddacd0`.
The saved source hashes match the actually executed copies; earlier minimal and
unsuccessful attempts remain separately preserved. The repository result omits
public certificate PEM and records the original external report's SHA-256;
it is a documented sanitized copy, not a byte-identical copy of the raw report.

The **22/22** checks are:

| Boundary | Checks | Observed outcome |
| --- | ---: | --- |
| Python server / CLI client, CLI server / Python client, Python / Python | 3 | Exact request/response bytes, TLS 1.3, verified certificate identity/fingerprint and fresh sessions |
| Incompatible traditional-only group, both endpoint roles | 2 | Fatal handshake failure; no application response; no fallback |
| Missing client certificate | 1 | Python server rejects before application consumption |
| Untrusted and expired client/server certificates | 4 | Specific issuer verification code 20 or expiry code 10 |
| Wrong server hostname | 1 | Hostname mismatch code 62 |
| TLS 1.2 peers, both roles | 2 | Protocol policy rejection |
| Plaintext sent to Python TLS socket | 1 | WRONG_VERSION_NUMBER, no application ACK |
| Unset/missing/wrong/malformed policy, client and server roles | 8 | Startup configuration rejection, exit 3 |

The CLI client reported the negotiated group X25519MLKEM768 against the Python
server. For the Python client, the actual ServerHello key_share selected-group
value was checked as NamedGroup 4588 by the CLI trace; advertising a supported
group list alone is not this evidence. Direct Python/Python transfer separately
proves both adapter roles can exchange exact bytes. Python exposes the verified
peer identity but not a public negotiated-group getter here; future observability
must distinguish fixed-policy inference from directly observed handshake traces.

TLS 1.3 clients can print CONNECTION ESTABLISHED before learning that the server
rejected their client certificate. Negative acceptance therefore requires the
rejecting Python endpoint's specific TLS verification error, natural nonzero
client outcome/fatal alert and no application ACK; that intermediate client log
is not server-side mTLS acceptance. Timeouts and generic startup failures do not
count as expected TLS rejection. Synthetic expired certificates use explicitly
historical signing dates, never disabled time checks.

All sessions use fresh contexts/processes; server `num_tickets=0`, no external
PSK, session reuse or early-data API is enabled. OpenSSL defaults to rejecting
early data; the adapter does not enable it. The run verifies full handshakes and
records `session_reused=false`; it is not a resumption or active 0-RTT attack
suite. [OpenSSL early-data defaults](https://docs.openssl.org/3.5/man3/SSL_read_early_data/).

The container uses `--pull never`, `--network none`, a read-only root, a bounded
32 MiB private /tmp tmpfs, non-root uid 65534, no capabilities, no-new-privileges,
64 PID/256 MiB/one CPU caps and a 180-second outer timeout. There are no host
ports or original-data mounts. Generated private keys stay in the container
and disappear with tmpfs; retained output contains no private-key bytes. Raw
safe output and immutable source copies are retained externally. Cleanup is
owner/name constrained and was verified. This experiment's one-CPU cap differs
from the future half-CPU lab-v1 acceptance budget, which has not been tested.

A narrow cleanup-failure regression checks that a Docker query timeout cannot
prevent a persistent failed report or the independent remaining-resource query;
uncertain cleanup exits nonzero. It is a host-runner check, not another TLS case.

Reproduce only when a fresh validation is justified, using the existing local
image and a new external runtime automatically allocated by the host runner:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/linux_tls_host.py
```

Two earlier full attempts failed in certificate provisioning (`x509 -days -1`)
and in an overstrict intermediate-client-log assertion. They were harness
failures, not accepted negatives. The earlier 21-check full pass is retained;
the final 22-check result above adds precise negotiated-group, plaintext and
output-sanitization evidence. Do not sum repeated suites as independent samples.

## Selection decision and Phase B boundary

The revised A04 simulation feasibility gate is met: the immutable target runtime
carries a mandatory-hybrid TLS 1.3 mTLS channel, rejects invalid policy/identity
and exposes authenticated identities to bounded application reads. OpenSSL 3.5
is an LTS series and Python 3.12 remains in security maintenance; this does not
certify the pinned patch/image as current or vulnerability-free. Release package
maintenance and dependency updates remain D work, with revalidation after change.
[OpenSSL lifecycle](https://openssl-library.org/post/2025-02-20-openssl-3.5-lts/),
[Python maintenance status](https://www.python.org/downloads/).

B01 must implement this policy/loader boundary in the gateway and cloud, bind the
verified certificate identity to a logical gateway and permitted devices, remove
any alternate plaintext ingestion path and reject inconsistent source metadata.
B must integrate the selected event/ACK framing, durable state and fault matrix;
C must implement credential/policy lifecycle and revocation. The original app
is unchanged and its A03 findings remain open until those changes are verified.
A feasibility pass is not engineering release/security acceptance.

## Authoritative references

- [OpenSSL 3.5 SSL_CONF_cmd](https://docs.openssl.org/3.5/man3/SSL_CONF_cmd/)
  documents the hybrid TLS groups introduced in 3.5 and explicit group policy.
- [OpenSSL 3.5 s_client](https://docs.openssl.org/3.5/man1/openssl-s_client/)
  documents hostname checking, group selection, TLS-version options, and
  fatal verification through `-verify_return_error`.
- [OpenSSL 3.5 s_server](https://docs.openssl.org/3.5/man1/openssl-s_server/)
  documents mandatory client certificates using `-Verify`, verification-error
  handling, reverse echo, and session-ticket/early-data controls.

These references explain the configuration. Actual negotiated-group and
certificate rejection results come from the saved runtime evidence.
