# Phase B engineering simulation runbook

Scope: the opt-in local Docker/simulated-device path. This runbook is not a
Phase B acceptance or publication record; consult STATUS.md and current evidence.
Keep the original V1 entry points, Compose stack, `.env`, device keys/state and
unrelated user changes intact. Use a fresh isolated lab for every verification.

## Start through the controlled bootstrap

The image sets `OPENSSL_CONF=/run/pqc/tls-policy.cnf`. Preserve the exact LF bytes
of `deploy/phase_b/tls-policy.cnf`; it selects TLS 1.3 and only
`X25519MLKEM768`. Bootstrap validates those bytes and the supported OpenSSL 3.5
runtime before importing SSL or cryptography bindings. Inherited
`OPENSSL_CONF_INCLUDE`, `OPENSSL_MODULES` and `OPENSSL_ENGINES` are rejected.
Do not preload SSL, change the policy, or substitute direct service execution.

Inside the prepared image, launch one role per container:

```text
python -m common.secure_bootstrap gateway --config /run/lab/gateway.json
python -m common.secure_bootstrap cloud --config /run/lab/cloud.json
```

There is no plaintext ingestion backend in this opt-in cloud. The simulated
device retains its existing authenticated HELLO/AEAD TCP protocol to the gateway;
the gateway uploads immutable normalized events over mutually authenticated TLS.

## Trusted configuration

Configuration is a UTF-8 JSON object, at most 65,535 bytes. Duplicate keys and
nonfinite values are refused. Paths below are absolute paths **inside the owning
container**. Keep generated configuration, source keys, leaf private keys and
synthetic issuer material outside the checkout. Mount only the owning role's
trust/leaf files and configuration read-only; issuer private keys belong to the
separate offline fixture, not either application container.

Both roles require:

- `state_dir`: separate writable state volume, such as `/var/lib/pqc`, outside
  `/app` and the source checkout. Cloud and gateway must not share this volume.
- `listen_host`, `listen_port`: role listener; the isolated harness uses
  `0.0.0.0:5001` for gateway source TCP and `0.0.0.0:5443` for cloud TLS.
- `health_port`: the harness uses 8001/8002 for gateway/cloud. The application
  binds this listener to `127.0.0.1`; do not publish it to the host.
- `health_token`: independently generated random bearer credential, at least
  32 characters. Keep it out of reports, shell history and source control.
- `policy_expires_at`: timezone-aware UTC expiry, no more than five minutes
  ahead. Expiry and detected clock uncertainty fail closed for cloud delivery.
- `tls`: `ca_file`, `cert_file`, `key_file`, pointing to the owning role's files.
  Synthetic leaf validity must be at most 24 hours. Gateway additionally requires
  `server_hostname`, matching the cloud certificate's SAN; CN fallback is disabled.
- Optional `limits`: positive integer `queue_rows` <=10,000, `cloud_rows`
  <=100,000, `state_bytes` <=268,435,456, and integer `reserve_bytes` from zero
  to 16,777,216, strictly below `state_bytes`. Omitted values use these ceilings.
  Lower limits are explicit laboratory profiles, not changes to lab-v1 ceilings.

Gateway additionally requires `gateway_id`, `cloud_host`, `cloud_port`, and
`devices`. Each device ID maps to `{key_hex, source_incarnation}`: a fresh
32-byte source key encoded as 64 hex characters and an explicitly provisioned
UUID incarnation. The gateway registry is bounded to one through three devices.

Cloud additionally requires `gateway_peers`, bounded to one through three leaf
certificate entries. Each key is the verified gateway leaf certificate's DER
SHA-256 fingerprint, exactly 64 lowercase hex characters. Its value contains
`gateway_id` and `devices`, mapping each allowed device ID to its provisioned
incarnation UUID. Keep this mapping consistent with the gateway configuration.
The authenticated certificate selects this authorization record; submitted
gateway/device IDs cannot enlarge it. A CA-trusted but unregistered leaf is
insufficient authorization.

Only `policy_expires_at` may be renewed in the existing trusted configuration
while running. Renew it within the five-minute bound without changing identity,
credentials, endpoints or budgets. Other changes require an explicit reviewed
operator action and role restart in this lab. Lease renewal is not certificate
renewal, revocation management or an instruction to clear persistent state.

## State and recovery

Gateway acceptance atomically stores the event ID, canonical event bytes and
source checkpoint in SQLite. Cloud business commit and deduplication are one
transaction; only an exact matching committed ACK permits gateway removal.
WAL/FULL settings and Linux permissions are selected; the owning gateway/cloud
volumes survive role restarts. Separate fresh device state is also required.

The combined pending/quarantined gateway row limit is 10,000; cloud business and
deduplication rows are capped at 100,000. The 256 MiB per-role state budget includes
DB/WAL/SHM and quarantined data, with 16 MiB reserved for bounded metadata and
failure handling. Normalized payload/event/upload caps are 4/8/16 KiB; the source
frame cap is 64 KiB. These limits are distinct. Byte-budget refusal is a logical
quota; it does not prove that the host disk reached physical ENOSPC.

No pending, quarantined, business or deduplication record is automatically
deleted. The retry deadline is 24 hours from original acceptance; expiry
quarantines the original event without issuing a new ID. Backward-clock
uncertainty is observable and must be corrected, not bypassed by clearing state.
Unknown schema versions are refused; no automatic migration, downgrade or V1
state conversion is provided.

For a stable observation, reconcile gateway counters as
`accepted_total = acknowledged_total + pending + quarantined`. Cloud commits can
temporarily exceed gateway acknowledgements after a lost ACK; retransmission of
the same event/digest must close that gap without a second business row. Counts
alone do not replace event identity/content reconciliation after a fault.

On queue/disk refusal, preserve existing accepted events and inspect the fixed
reason metric. The gateway closes the source connection. The unchanged simulator
has no reading ACK or automatic reconnect: successful `sendall` is not durable
acceptance, and in-transit loss may have an unknown count. After capacity repair,
an operator must verify the source checkpoint/incarnation and explicitly restart
the simulated source. Do not clear checkpoints or replay already accepted
readings as new events. Authorized readings may buffer within quota while the
cloud policy/identity is expired; renewal must drain those same persisted IDs.

## Observe the owning service locally

Use loopback HTTP from the role container; keep bearer credentials private.
`GET /live` is public liveness. `/health`, `/ready` and `/readings` require
`Authorization: Bearer <the generated health credential>`; cloud `/readings`
returns up to 100 normalized rows, newest first. `/ready` returns 503 when degraded.

Read the fields separately: `live`, `ready`, `policy_valid`, `cloud_connected`,
`business_delivery`, `last_matching_ack_at`, `storage`, `metrics`, `state_bytes`
and `loss_count_unknown`. Connectivity is gateway TLS connectivity, not proof of
a durable business commit. Business state distinguishes no delivery, backlog,
delivered/reconciled work and exceptional quarantine. The cloud reports its
committed state separately. Durable acceptance/ACK/commit counters survive
restart; refusal/error counters are process-lifetime. Do not sum repeated health
snapshots or interpret `loss_count_unknown=true` as an exact dropped-sample count.

## Reproduce bounded verification

Run from the repository root in PowerShell with Docker Desktop's Linux engine
already running. Use the native CLI and fresh external directories. The runners
verify a local endpoint and cached immutable images; they do not pull/install or
repair Docker. The prepared target is Linux x86-64, Python 3.12.14,
OpenSSL 3.5 and cryptography 50.0.1. Image identities are recorded in the harness and
each run's evidence; an unavailable cached image is a stop condition.

```powershell
$phaseBDocker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$phaseBArtifacts = 'D:\Code\pqcbridge-phase-b-artifacts'
$phaseBRunId = [Guid]::NewGuid().ToString('N')
python scripts/phase_b/docker_probe.py --docker-cli $phaseBDocker --runtime-root "$phaseBArtifacts\normal-$phaseBRunId" --evidence "docs/phase-b/evidence/normal-$phaseBRunId.json"
python scripts/phase_b/fault_probe.py --docker-cli $phaseBDocker --runtime-root "$phaseBArtifacts\fault-$phaseBRunId" --evidence "docs/phase-b/evidence/fault-$phaseBRunId.json"
python scripts/phase_b/fault_probe.py --case before_gateway_send --docker-cli $phaseBDocker --runtime-root "$phaseBArtifacts\before-send-$phaseBRunId" --evidence "docs/phase-b/evidence/fault-before-send-$phaseBRunId.json"
python scripts/phase_b/runtime_probe.py --docker-cli $phaseBDocker --runtime-root "$phaseBArtifacts\runtime-$phaseBRunId" --evidence "docs/phase-b/evidence/runtime-$phaseBRunId.json"
```

Inspect each exit status/result before continuing; a failed or partial run is not
acceptance. Keep raw credentials, command output and logs in the external run
directory. Compare copied-source/harness hashes with the current checkout before
attributing a result to later edits. Rerun only the cases affected by new changes.

The normal runner uses unmodified service entry points. The fault runner
explicitly instruments public queue/commit/ACK API boundaries with bounded waits,
then SIGKILLs the real role and restarts the same owned volume; the before-send
slice pauses the persisted event before returning it to the sender. This is
controlled laboratory injection, not the normal application launcher. The runtime
runner uses real services with explicit synthetic policy/certificate fixtures.
Neither instrumentation nor shortened fixtures establish production lifecycle,
physical power-loss, ten-minute outage or 24-hour endurance guarantees.

All probe resources use fresh private owner labels, an internal network, no host
port publications and separate volumes; the selected per-service budget is
0.5 CPU/256 MiB with bounded logs. Cleanup verifies ownership before removal and
records remaining containers/networks/volumes. Investigate failed cleanup against
that exact owner only; do not prune Docker or remove unrelated resources. Unique
verification images may remain cached by the stated image policy.

Linux process-kill/reopen results cover the measured Docker/SQLite path. Windows
development tests, best-effort file permissions and API-level restart tests do
not establish Windows directory-fsync, host power-loss or physical-device
compatibility. Preserve these evidence boundaries in any completion report.
