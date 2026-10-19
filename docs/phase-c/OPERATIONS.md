# Phase C — Local Migration Management Runbook

Date: 2026-10-19. Scope: owned Docker laboratory with simulated devices and
synthetic identities. Acceptance status is maintained in [STATUS.md](STATUS.md).

## 1. Deployment Boundary

The opt-in managed entry point adds a trusted local catalog and a read-only
manifest to the B delivery path. It is a local operator tool, without a network
management API. The controller has no per-message role in delivery. The initial
V1 entry points and the B engineering bootstrap remain available separately.

Use the validated Python 3.12 / OpenSSL 3.5 hybrid-capable container environment.
Managed startup initializes the mandatory TLS policy before importing application
modules. Required transport remains TLS 1.3, mutual certificate authentication,
X25519MLKEM768 and no 0-RTT. Certificates use synthetic RSA signatures; hybrid key
exchange does not imply post-quantum certificate signatures.

Keep issuer keys, source keys, health tokens, request files and raw runtime data
outside the checkout. Only the offline administrator receives the issuer private
key. Each service mounts its own leaf/key plus public certificates and the
read-only control directory. Do not share another service's private key. Linux
mode checks do not verify Windows host ACLs. Protect host directories explicitly.
Bind protected health endpoints to the intended local namespace; do not publish
laboratory ports to the host or an external network.

## 2. Reproduce the Laboratory Checks

The self-contained C lifecycle harness builds from the existing cached B image,
creates a fresh external fixture directory, enrolls two gateway/device groups,
exercises actual services, then removes only its ownership-labelled containers,
network and volumes. It refuses an existing runtime directory. It does not pull
images, install dependencies, reuse original state or expose host ports.

```powershell
$runtime = 'D:\Code\pqcbridge-phase-c-artifacts\lifecycle-' + [guid]::NewGuid().ToString('N')
python -B scripts/phase_c/docker_probe.py --runtime-root $runtime `
  --docker-cli 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' `
  --evidence "$runtime\published-result.json"
```

The cached application base is
`sha256:b23cfa27684e7af4be489c0d3683e184c72e3440bc45a408bbcbd5762b42b0f4`.
A missing image or stopped engine is an environmental blocker, not a passed
transport check. Retain raw logs externally; only sanitized evidence belongs in
Git. Check `status`, every case's result, source/harness hashes and
`cleanup.verified` in the generated report. An interrupted process has no complete
acceptance result. Do not remove resources whose ownership labels do not match.
Unique verification images are retained; the cached base remains unchanged.

`observation_probe.py` separately checks protected health and catalog proof on
disconnect/reconnect. Its stale-evidence scenario offsets only the gateway
runtime wall clock by 301 seconds; TLS, storage and business ACKs are real, while
the provider/controller clocks stay unchanged. This is not an endurance test.

## 3. Provision and Start Managed Services

Create a fresh external issuer directory and fresh leaf directories. The CLI
prints public descriptors/references only; it writes private material locally.
Issuer validity is seven days; leaf validity is at most 24 hours. Example commands
below use Linux container paths, all outside `/app`:

```text
python -m common.credentials issuer --directory /lab/issuer
python -m common.credentials issue --issuer-dir /lab/issuer --output-dir /lab/issued/gw-new --role gateway --subject-id gw-lab
python -m common.credentials issue --issuer-dir /lab/issuer --output-dir /lab/issued/cloud-new --role cloud --subject-id cloud --hostname cloud
```

Copy each leaf/key into its own role's credential directory. Adapt descriptor
references to absolute paths visible to that role, before registration. Register
the DER SHA-256 fingerprint and public descriptor once. References and identity
metadata remain immutable for that fingerprint. Do not overwrite an existing
credential directory or repurpose a fingerprint.

The B private configuration retains source keys/incarnations, gateway identity,
endpoints, health token, TLS trust and storage budgets. Add:

```json
{"management":{"manifest_file":"/run/lab/control/manifest.json"}}
```

Start with `python -m common.managed_bootstrap gateway --config /run/lab/gateway.json`
and the corresponding `cloud` role. The managed provider never expands the
immutable baseline gateway/device/incarnation provisions. Preserve pending data,
source sequence state, cloud deduplication and `managed-config.sqlite3` across
restarts. Do not edit the baseline configuration while running.

## 4. Operator Lifecycle and Evidence

Submit one bounded UTF-8 JSON request file to:

```text
python -m common.management --state-dir /lab/catalog --request-file /lab/request.json
```

Every request names `operation` and a bounded `operator` identifier. Responses are
`{"ok":true,"result":...}` or a fixed refusal code with exit status 2. Enrollment,
version changes, publication and accepted observations have transactional audit
records. Read-only status/audit queries do not append audit entries.

1. Enroll gateway and device using `enroll_gateway` and `enroll_device`. Device
   registration includes its existing incarnation and a key reference, never key
   bytes. Register leaf descriptors through `register_credential`.
2. Use `create_version` with `gateway_id`, a fixed `profile` and
   `active_credential`. Only `hybrid-standard-v1` (5-second operations) and
   `hybrid-conservative-v1` (3-second operations) are allowed. Neither weakens TLS.
3. Call `begin_apply` for the desired version. `export` atomically publishes the
   manifest using `path`, `cloud_credential` and optional `lease_seconds` (1–300).
   Mount the directory read-only so atomic file replacement is visible.
4. Obtain authenticated `/health` from the actual gateway. Observe the applied
   version, desired version, `management_state`, `management_applied_at`, cloud
   connectivity, business delivery and last matching ACK. A new authenticated
   channel is `Applying` until it receives its own matching business ACK;
   disconnection or stale proof is `Unknown`.
5. Send `observe` using the actual health fields and a fresh UTC `observed_at`.
   Successful evidence includes `gateway_id`, `management_version`,
   `management_state`, `management_applied_at`, `cloud_connected`,
   `business_delivery` and `last_matching_ack_at`. It must be current-channel
   `Effective` proof, with an ACK after the operator apply boundary and at or after
   channel application. Reusing a previous accepted ACK is refused. Recording
   desired policy, a live process or aggregate historical delivery is insufficient.

The CLI trusts its local operator to retrieve real health; evidence is not a
cryptographically attested remote claim. The catalog's status is the last accepted
operator observation, aging to `Unknown` after 300 seconds; it is not an online
fleet monitor. Query live health again when making operational decisions.

For a failed apply, record a clearly unsuccessful observation of the requested
version, preserving actual cloud/business state and the fixed
`management_failure_reason`. Its version denotes the failed desired apply, not a
claim that this version ran. `Failed` status/audit retains the safe reason. Never
insert raw exception text, tokens or private keys. See the enum in
`common/management.py`. A later actual matching ACK clears the reason.

## 5. Rotation, Revocation and Recovery

Stage the new leaf/key in the correct role, register its descriptor, create a new
version and publish. `accepted_credentials` maps the active fingerprint to null
and any retiring fingerprint to an absolute UTC deadline no more than 60 seconds
away and before its expiry. Verify a fresh business ACK on the new channel,
retirement refusal and continued traffic for the unchanged group. Do not extend
an overlap by restoring old control files.

For a missing key, health can have valid policy while TLS application fails. Check
desired versus applied version, connection/readiness and
`tls_configuration_refused`. Installing the matching already-issued key may
recover the requested version. If a credential cannot safely be recovered, issue
and publish a fresh valid one. Profile `rollback` creates a new version selecting
the earlier profile while retaining current valid credentials; it will not revive
revoked or retired keys. Call `begin_apply`, export and verify again after rollback.

`revoke_credential` followed by export closes active access and refuses new access
when the publication is seen. `set_enabled` can disable a gateway or device;
device disabling closes an existing source socket and refuses new messages.
Each role persists sequence/digest and revocation tombstones, refusing older
snapshots after restart. Do not delete guard/state files to bypass a refusal.

Renew the lease before expiry while keeping unchanged group tokens stable. If the
controller is offline, authorization lasts at most the last accepted 300-second
lease plus bounded service scheduling. There is no instantaneous offline
revocation or online OCSP/CRL. After lease expiry, an otherwise authorized source
may buffer within B quotas; renewed authorization drains the same accepted event
IDs. Expired/invalid credentials still block transport. At quota exhaustion,
preserve state and stop new mutations; this release has no automatic history
deletion or unbounded credential rollover.

## 6. Operating Limits and Next Boundary

Catalog limits: 3 gateways, 3 devices per gateway, 12 credentials, 100 policy
versions, 1,000 audit operations and 32 MiB. Manifests are at most 65,535 bytes;
role guards are bounded independently and included in service state accounting.
These are refusal limits, not demonstrated scale or capacity promises.

The C laboratory validates one canary and one unchanged gateway group. D owns
endurance, upgrades, backup/restore, broader deployment packaging and final pilot
acceptance. Physical devices, host compromise, filesystem power-loss guarantees,
production issuer custody and Windows ACL hardening remain outside this result.
