# A-06: Isolated Docker simulation

Observed: 2026-10-16. Status: **actual isolated baseline passed**. The original
application still uses its custom TCP transport; TLS adapter feasibility is
reported separately in [A04](A04_TRANSPORT_VALIDATION.md).
Source HEAD: `681986bc0119d51913140575f98720c90fb378ac`.

## Actual result

The user manually opened Docker Desktop after earlier startup attempts failed.
The subsequent real deployment completed at `2026-10-16T08:21:11Z` with
`status=passed`, `deployment_accepted=true`. See
[the recorded result](evidence/docker/docker-result-native-cli.json).
The raw runtime is
`D:\Code\pqcbridge-phase-a-artifacts\docker-ad91c651551244cd81f91f150719c24c`.

The runner built the three original Dockerfiles in a copied context, launched
cloud/gateway/device with fresh synthetic credentials and state, and compared
every field of three actual simulated-device readings against the cloud HTTP
readback snapshot. Sequences 1-3 matched device ID, timestamps, temperature and
unit. Device generation continued during stop grace: logs contain six generated
readings overall. Three is the verified pre-stop snapshot, not total generation.

The accelerated smoke interval was one second; the selected normal workload is
one device every five seconds. This run establishes bounded container execution
and exact readback, not normal-load endurance, durable queue/ACK, recovery,
CPU/memory/log budgets, latency SLOs or Linux hybrid TLS.

## Runtime and immutable identities

Docker Desktop 4.91.0 (239619), Engine 29.8.0, API 1.56, Linux amd64 on WSL2
kernel 6.6.87.2. All three containers measured Python 3.12.14, cryptography
50.0.1, Python ssl OpenSSL 3.5.7 and cryptography OpenSSL 4.0.2. These are
separate loaded TLS/crypto libraries; cryptography's version is not Python TLS
negotiation evidence. Image IDs and repository digests are retained in JSON.

| Role | Immutable built image ID |
| --- | --- |
| cloud | `sha256:4e035850aea9c37da8aa58a80d65e074120bd7f5e4810b43ae05af5a2c34be87` |
| gateway | `sha256:b23cfa27684e7af4be489c0d3683e184c72e3440bc45a408bbcbd5762b42b0f4` |
| device | `sha256:91d86465857c6256a64e603852f0c9cb1cfa6d1e9eae20c84e4d6ae6b67ad828` |

The original Dockerfiles still refer to the floating `python:3.12-slim` tag.
The local cached base selected for the separate TLS feasibility experiment is
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
That immutable experiment selection does not silently pin the original files,
prove dependency vulnerability status or establish a maintained release package.

## Isolation, cleanup and preservation

The runner refuses existing runtime directories and paths inside the checkout.
It never runs the original bootstrap or Compose stack. It generates a random
project (`pqc-a-f464a7c89a57ba9a` in this run), a private internal network,
fresh cloud/device volumes and synthetic gateway/device credentials. Original
root .env, keys and device sequence state are excluded. There were no host-port
publications or host bind mounts. Device serialization was observed through an
in-memory wrapper; source bytes were unchanged.

The new cloud public-key fingerprint was derived inside its container and
provisioned into only the isolated gateway configuration. It was not scraped
from service logs. Before removal the runner verified every matching object's
independent owner label. Owned containers, network and volumes were removed;
subsequent queries returned empty lists. Unique image tags remain intentionally.
Thirty original application/config/state inputs had no changed or added files.

Independent Standards review reconciled all 36 raw command records with the
sanitized result, actual image IDs, no published ports/bind mounts, internal
network, ownership labels, post-cleanup emptiness, source hashes, exact readback
and probe SHA-256. The raw result and repository copy matched. These checks
support this bounded run, not an OS-wide state snapshot.

## Runner fixes and preserved earlier failures

Earlier `docker version` reported Server=null and a missing LinuxEngine pipe.
A supported Desktop start attempt timed out. The backend log at
2026-10-16T08:04:40.462087800Z reported failure to rename sailor-ingest.sock
because Windows could not access it. Its underlying cause was not established.
No socket deletion, factory reset, state cleanup, service/config mutation or
host upgrade was performed. Manual desktop startup later restored availability.
[The startup observation](evidence/docker/desktop-startup-observation.json)
is historical evidence, not the current engine state.

Two later harness runs stopped with WinError 193 before executing Docker:
[docker-result.json](evidence/docker/docker-result.json) and
[docker-result-after-manual-start.json](evidence/docker/docker-result-after-manual-start.json).
Python shutil.which('docker') had selected the adjacent extensionless POSIX
script. Windows resolution now selects native docker.exe, with an optional
explicit --docker-cli path. These preserved failures do not invalidate the
subsequent successful run or prove the daemon was unavailable.

Six targeted public CLI contract checks passed after the fix:
[recorded output](evidence/docker/cli-contract-tests-after-cli-fix.txt).
They cover unsafe runtime refusal/sentinel preservation, copied source/private
network planning, remote-endpoint refusal, owner-label cleanup refusal and the
Windows executable selection regression. Fake CLI cases explicitly select the
fake program, avoiding accidental access to the real daemon. Review also fixed
a lifecycle defect so log-collection failure cannot skip the independent cleanup
attempt. Contract checks establish refusal behavior; actual runtime proof comes
from the separate successful deployment above.

## Reproduction

Use a new external runtime and preserve prior evidence:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/docker_probe.py `
  --docker-cli 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' `
  --runtime-root 'D:\Code\pqcbridge-phase-a-artifacts\new-unique-docker-run'
```

The runtime must not exist. --plan-only prepares copied configuration without
contacting Docker. A real exit 0 requires readback, runtime evidence, cleanup
and original-input preservation. Protected destinations exit 2; runtime/engine
failures exit 1. Do not rerun a passed experiment merely to recover context.
