# Phase C latest pause handoff — 2026-10-18

Explicit user request: pause all tasks and prepare next handoff. All C agents,
tests/labs and automatic phase publication are stopped. This replaces earlier
handoffs claiming the provider/catalog are still missing; those modules now exist.

## 1. Branch, baseline and preservation

Checkout D:\Code\pqcbridge-legacy-edge-cloud; codex/phase-c-management.
HEAD5c12f8644d35ae85422318bbad934379067affa1 includes user documentation organization
after B merge. B completion a6a083acac5afc06b81e82d4568e775069883ac1 is published.
No C commit/push. Preserve user CLAUDE.md diff, docs/agents and new unrelated
.codex-quota-checkpoints/ and Codex-Quota.ps1. Do not execute/stage those scripts.
Keep current README/docs organization, original .env/keys/device/cloud state,
Compose and V1. No reset/clean/stash discard or original-state migration.
Current protected12-file baseline: tmp\phase-c-resume-latest-a36aba08aafa4aa0bcf38a10fc586a2a.
Latest pre-handoff source/diff snapshot: tmp\phase-c-pause-latest-f618fbf63d354fbdbc52adffa7a72235.
Final checkpoint evidence/PAUSE_CHECKPOINT.json has hashes/drift and pause audit.
English project docs/Chinese user communication; milestone docs must follow
docs/development/README.md and RECORD_TEMPLATE.md.

## 2. Completed implementation and public APIs

common/credentials.py +test_credentials:20 focused passes. create_issuer and
issue_certificate/CLI, role EKU/SAN,24h leaf cap, exact key/certificate checks,
fresh no-overwrite external dirs and safe public descriptors. Linux tmpfs mode
checks actually passed in C Docker baseline; Windows bind ACLs remain distinct.

common/management.py +test_management:18 focused passes. ManagementStore supports
enroll_gateway/enroll_device/set_enabled/register_credential/revoke_credential,
create_version/begin_apply/observe/status/rollback/manifest/export/audit/close.
CLI: python -m common.management --state-dir ABS --request-file ABS; flat request
{operation,operator,...public args}; response {ok,result} or fixed error. export/
manifest optional operator argument preserves CLI audit actor. Rollback creates
new version from prior safe profile while retaining CURRENT valid nonrevoked
credentials. Effective requires fresh nonreused ACK after begin_apply; stale=>Unknown.
Safe management_failure_reason/failure_reason enum persists to proof/status/audit;
arbitrary diagnostics rejected without echo. Codes: tls_configuration_refused,
tls_identity_refused, channel_or_policy_refused, delivery_state_refused,
network_unavailable, delivery_unavailable, cloud_disconnected,
business_delivery_unverified. Success clears code.

common/managed_config.py +test_managed_config:13 focused passes. Public
ManagedConfiguration implements B interface plus dynamic_tls, close(),
operation_timeout(peer_fingerprint=None), channel_token(peer,*,local_fingerprint=None),
channel_current(peer,token),management_status(),source_allowed(id,spec). Strict
bounded manifest; persistent highest sequence/digest/immutable credential refs/
revocation tombstones in managed-config.sqlite3. Accepts revocation publications
without disabling unrelated group. Lease-only/global sequence updates do not
change unaffected per-peer tokens. New leaf maps to stable baseline gateway/
device/incarnation; no source/dedup reset. Reads only own role private references.
The optional expected local fingerprint is checked atomically under provider
lock when producing token, preventing rotation during handshake from rebinding
an old TLS context to new identity. Source may buffer when only cloud lease expired.

common/managed_bootstrap.py retains pre-import TLS gate, calls B service_main with
configuration_class=ManagedConfiguration. common/secure_runtime.py contains opt-in
dynamic TLS/token checks, own-context fingerprint capture, current source checks,
management desired/applied/version/time/reason and current-channel ACK evidence.
Every new managed TLS channel resets proof even if version unchanged. Stale ACK
returns Unknown. Matching ACK clears failure code. B default entry remains intact.

Root test fixture repair: tests/test_management.py observation helper waits one
bounded real wall-clock tick. It fixes Windows equal-timestamp flake without
weakening production strict ACK>apply. Do not restore old timing assumptions.

## 3. Actual verification and source boundaries

Latest full-regression.json234passed13.51s, native Windows, complete existing/new
suite. b-compatibility.json19/19 real B Docker cases on latest source; cleanuptrue.
observation-green.json2/2 real managed TLS+business ACK+protected HTTP regressions:
same-version reconnect needs new proof, stale prior ACK reports Unknown. Red
counterparts preserved in observation-red.json. Staleness uses a gateway-runtime
wall-clock offset301s only (provider/controller clock remains real); not endurance.

docker-lifecycle-second.json17/17 INTERMEDIATE source, before final observation/
failure-code changes. It demonstrated two live gateways and exact payload/ACK,
canary/unaffected kernel TCP tuple, actual unknown/classical CLI refusal,
missing-key apply failure/recovery, safe rollback,24s overlap/old retirement,
active/new revocation, antirollback after role restart, device EOF/new admission
refusal, gateway disable,5s offline lease buffer/exact-event drain and45s managed
leaf expiry. No claim that it covers later changed source. Cleanup verified.

The final matching rerun was active when user paused. Its last agent message
reported baseline/canary/actual failure_reason/repair/rollback passed and overlap
underway; there is NO complete report. Do not infer final17 pass from progress.
Runtime D:\Code\pqcbridge-phase-c-artifacts\lifecycle-final-0556dd3c4e844909be1848df6ad3a60e,
project pqc-c-93954e99588545b4. Verified host runner30156 and recorded Docker CLI
children stopped. Root captured logs then used existing label-verifying cleanup:
removed3containers+1network+3volumes, empty remaining. Interrupted record is
docker-lifecycle-final-interrupted.json and raw pause-cleanup.json. This is a
user interruption, not an app failure. Fresh next run required; don't reuse volumes.

scripts/phase_c/docker_probe.py is normal unmodified managed service matrix with
real issuer/catalog CLI/public TLS/health/ACK and explicit operator fixture changes.
Its17case matrix strictly asserts actual tls_configuration_refused in missing-key
Failed status AND audit. scripts/phase_c/observation_probe.py is the separate
disclosed external-clock fixture; no fake TLS/database/ACK. Harness contracts3
pass and are part of full234, not a separate assurance total.

## 4. Review and current acceptance gaps

See REVIEW_PROGRESS.md: preliminary Standards had no confirmed blocker but noted
old proof reuse; preliminary Spec identified stale Unknown and missing safe failure
codes. Root reproduced/repaired proof/stale issues; catalog safe diagnostic fix
and unit/CLI tests completed. Final independent Standards/Spec re-reviews after
latest changes and matching final17matrix still required. No C acceptance/push.

After explicit resume: inspect source/hash drift, then run ONLY the outstanding
final17case matrix on fresh external runtime:
python -B scripts/phase_c/docker_probe.py --runtime-root NEW_EXTERNAL_DIRECTORY
 --docker-cli "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
 --evidence docs/phase-c/evidence/docker-lifecycle-final.json
Do not rerun already current full234/B19/observation2 merely for context. If code
changes or source drift require it, rerun matching affected checks and full suite
as justified. Complete independent reviews, final source/evidence reconciliation,
preservation/owned cleanup, milestone/runbook records and scoped secret/diff checks.
Only then mark whole C complete and publish under standing authorization. D future.

## 5. Automation and environment

Existing pqc-bridge-github heartbeat changed to PAUSED with unchanged prompt/
15-minute cadence. On explicit whole-task resume restore same task, no duplicate;
defer during active edits and publish only accepted major phase, never partialC.
A/B already published. Native Docker desktop-linux local engine remains intact.
Final read-only audit found no matching validation processes and no C owner
containers/networks/volumes or B compatibility owner containers. This is not an
OS-wide guarantee. No tests after pause; only read/save/interruption/owned cleanup.
Keep raw synthetic credentials/logs outside checkout. Unique verification images
retained by policy. No host ports, pulls, old mounts or external probes.
GitHub direct failed previously; existing Windows127.0.0.1:7897 proxy per command
worked for B. Do not change persistent proxy/Git config. No C publication whilepaused.
