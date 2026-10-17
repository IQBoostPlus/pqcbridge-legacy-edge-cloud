# A-01: Preserved and isolated current baseline

Captured on 2026-10-16. The local Python baseline and subsequent isolated Docker
simulation smoke are complete. The Docker result is recorded separately in
[A-06](A06_DOCKER_SIMULATION.md), preserving the earlier unavailable-engine evidence.
This report establishes the simulation baseline; it does not close the Phase A
transport or independent legacy compatibility gates.

## Source and preservation

The original HEAD is `681986bc0119d51913140575f98720c90fb378ac`. The user started
on `main` with modified `CLAUDE.md` and `README.md`, and untracked `docs/`.
Implementation runs on `codex/phase-a-validation` at the same HEAD. No commits,
pushes, resets, cleans, stash operations, application-source edits, or original
state migrations were performed for A-01.

The owner preserved 70 original files, including `.env`, ignored state and the
existing user documents, at:

`D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z`

That location contains `baseline-manifest.json` and `initial-working-tree.patch`.
After the successful run all 70 file hashes still matched that manifest. The
runner also compared the original `.env`, `cloud_state`, `device_state`, README,
CLAUDE and existing non-Phase-A documentation before and after execution: no
changes. Hash comparisons establish file-content preservation, not unchanged
timestamps, process state or an OS-wide snapshot.

## Isolation audit performed before execution

Existing tests were read before running. File-writing tests use `tmp_path`;
socket tests explicitly bind loopback ephemeral ports. Importing the application
modules does not invoke their entry points. No existing test needs the original
cloud private key, device sequence file, or root `.env`.

The runner copies `common`, `device`, `gateway`, `cloud`, `tests`, the pytest
configuration, dependency list and deployment configuration into an external
runtime. It excludes the original `.env`, cloud/device state and bytecode caches.
The existing virtual environment is used read-only; no dependencies are installed
or upgraded. Bytecode generation, pytest caching and automatic plugin discovery
are disabled. Pytest temporary files, its log and JUnit XML stay under the external
runtime. The suite uses the committed demo credentials because its existing tests
assert their values; the separate smoke run uses fresh random credentials.

Child processes receive a small explicit environment. Inherited application
credentials/configuration, Python settings and proxy settings are not passed.
HTTP probes explicitly bypass system proxies. A child Python audit hook rejects
writes outside its runtime, non-loopback socket binds/connections and nested
subprocess launches. This is a guard for this inspected Python test program,
not a native-code/hostile-process sandbox.

The current health service hard-codes `0.0.0.0`. To avoid exposing test health
endpoints, the launcher substitutes a child-local `ThreadingHTTPServer` subclass
that binds `127.0.0.1`. Application files are unchanged. This deliberate launch
adaptation means the smoke does **not** validate the unmodified deployment's
health binding or access controls. All four actual smoke socket binds were
recorded by the audit hook and were IPv4 loopback.

The production-style bootstrap script was not run: it writes `.env` and starts
Compose services. Docker checks below are read-only and use a copied Compose
file plus an explicitly empty external env file.

## Current observed results

The machine is Windows 11, build 26200, AMD64. The interpreter is the existing
`.venv\Scripts\python.exe`, Python 3.12.0. Runtime packages are `pytest 9.1.1`
and `cryptography 50.0.1`, matching `requirements.txt`. Python's `ssl` module
reports OpenSSL 3.0.11; cryptography's backend reports OpenSSL 4.0.2. These are
different runtime stacks. The cryptography ML-KEM result does not establish
hybrid TLS support in Python `ssl`.

The **existing suite currently passed 136 tests**, zero failures, errors or
skips. Pytest reported 8.27 seconds; the guarded child invocation took 9.437
seconds. This is a new run, separate from the historical P08 count of 136.

The **subprocess smoke currently passed**. Three separate application processes
ran the existing Device, Gateway and Cloud entry points. Fresh random per-device
and gateway credentials were configured through files/environment in the
external runtime. A fresh cloud ML-KEM private key was generated locally before
launch; its public fingerprint was derived from that local key generation and
provisioned to the gateway, rather than scraped from cloud service logs.

The device sent sequences 1, 2 and 3 at a 0.2-second requested interval. The real
cloud `/readings` endpoint returned all three readings with the expected device
ID and consecutive sequences. Cloud counters reported 3 received and 3 processed;
gateway counters reported 3 forwarded and one established cloud session. Four
ephemeral ports were used (cloud 54142, gateway 54143, cloud health 54144 and
gateway health 54145). A readiness probe makes an extra short device connection.
The generator was deliberately terminated after the third observed reading;
Windows reset that device socket, incrementing gateway `errors` once. This
shutdown artifact is retained in the evidence and is not described as an
error-free sustained run. All owned service children were stopped afterwards.

Cloud readings are held in the existing in-memory `ReadingStore`. This result
does not establish durable gateway acceptance, durable cloud writes, delivery
acknowledgements, recovery, TLS, a real legacy device, production load or security
closure.

Docker CLI 29.8.0 and Compose 5.5.1 are installed. The isolated
`docker compose ... config --quiet` check passed. Docker runtime/build checks
were not run at this initial baseline: `docker version` reported no server and a missing
`dockerDesktopLinuxEngine` pipe. Existing Docker configuration, containers and
volumes were not changed. The first config attempt lacked Windows plugin search
environment variables; the successful read-only check retains Windows profile
and program-path variables for Docker CLI discovery only.

After the user manually started Docker Desktop, the separate A-06 runner built
the original three Dockerfiles in a copied context and verified all fields of
three real simulated-device readings through gateway and cloud container HTTP
readback. Engine 29.8.0 / Docker Desktop 4.91.0 ran Linux Python 3.12.14,
cryptography 50.0.1, Python OpenSSL 3.5.7 and cryptography OpenSSL 4.0.2.
All owned containers/network/volumes were removed; unique image tags remain.
The run's 30 application/config/state inputs were unchanged. This accelerated
one-second smoke supplements the subprocess result; it does not test hybrid
TLS, durable delivery, normal-load endurance or selected resource budgets.
See [actual Docker evidence](evidence/docker/docker-result-native-cli.json).

## Reproduction

From the repository root, select an unused external runtime directory:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/baseline.py --runtime-root D:/Code/pqcbridge-phase-a-artifacts/reproduce-a01-new
```

The default sanitized report is `docs/phase-a/evidence/baseline/result.json`.
Use `--evidence-dir` to select another report directory. Existing runtime
directories and any runtime path inside the checkout are refused. The run is
bounded by a 90-second suite timeout, short readiness deadlines, and child
termination/kill deadlines. Dynamic port allocation briefly releases reserved
ports before child bind; contention produces a bounded failure, not permission
to reuse an existing service.

The CLI safety test is:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/baseline_contract_test.py
```

Set `BASELINE_RUN_INTEGRATION=1` and `BASELINE_CONTRACT_RUNTIME` to a new external
directory to include the CLI integration contract. Its acceptance boundary is
the executable baseline runner, the existing socket protocol, and the real cloud
HTTP reading endpoint. The CLI safety test and integration contract were each
observed failing before their respective implementation slices, and both passed
in the successful run. They are **two additional harness checks**, not part of
the reported 136 existing tests.

The reusable `isolated_stack(runtime, source=None, python=None)` context manager
in `scripts/phase_a/baseline.py` owns fresh cloud/gateway child processes and
external synthetic state. It exposes `gateway_port`, `device_id`, `device_key`,
`readings()`, `cloud_health()`, `gateway_health()` and optional `start_device()`
for the owner's A-05 public wire client. It stops only its own children.

## Evidence and failed harness attempt

The sanitized machine-readable current result is
[`evidence/baseline/result.json`](evidence/baseline/result.json). Raw pytest XML,
logs, copied source and synthetic credentials/state are retained externally at
`D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z\baseline-runtime-02`.
Synthetic private key and credential files are not copied into the repository.

The earlier `baseline-runtime` is preserved as failed harness evidence: the
write guard rejected pytest's default Windows `NUL` log file, so pytest exited
before test execution. The launcher was corrected to put that log explicitly
inside the isolated runtime. This was a harness setup failure; it is not an
application regression and is not counted as a successful suite run.
