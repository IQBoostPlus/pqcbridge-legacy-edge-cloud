# Phase C — Verifiable Local Migration Management

Date: 2026-10-19. Status: Accepted for the owned Docker/simulated-device lab scope.

## 1. Background and Scope

The B engineering path delivered authenticated hybrid transport and durable,
idempotent telemetry, but its registry/policy configuration had no managed
lifecycle. C adds a bounded trusted local administrator, versioned publications,
credential rotation/revocation and evidence-based application status. A policy is
effective only after a current authenticated channel receives a real matching
business ACK; a desired version or historical delivery count is insufficient.

Baseline `5c12f8644d35ae85422318bbad934379067affa1` includes the user's documentation
organization after the B merge. B completion is
`a6a083acac5afc06b81e82d4568e775069883ac1`. C changes are on
`codex/phase-c-management`. This milestone is implementation plus laboratory
evaluation, with actual Docker services, simulated legacy sockets and synthetic
credentials. Physical devices and production acceptance are outside its scope.

## 2. Findings and Evidence

| ID | Preconditions and observed behavior | Consequence and decision | Evidence |
| --- | --- | --- | --- |
| C-OBS-01 | Prior ACK aged past 300 seconds while runtime still reported Applying | Stale observation must be Unknown; implemented | observation-red.json / observation-green.json; disclosed runtime clock fixture |
| C-OBS-02 | Cloud reconnect preserved a historical ACK for the same management version | Clear proof on every channel bind and require a fresh ACK | Actual cloud stop/start through protected health, red/green |
| C-DIAG-01 | Failed catalog observations lacked a useful safe failure reason | Persist bounded enum through runtime/status/audit; reject arbitrary diagnostics | Catalog tests and actual missing-key CLI failure in lifecycle matrix |
| C-OBS-03 | Disconnected runtime retained a fresh ACK and reported Applying | Disconnected objects report Unknown | observation-disconnect-red.json failed new check; final green passes |
| C-OBS-04 | An unobserved old ACK was newer than CLI apply but older than reconnect | Catalog also requires current-channel Effective state and ordered bind/ACK times | Four public API fail-first failures, 31 catalog tests, actual CLI old-proof refusal/new-proof acceptance |
| C-HARNESS-01 | Initial missing-key assertion expected policy_valid=false | Policy syntax validity and TLS key usability differ. Use actual desired/applied mismatch, disconnection, readiness and fixed error | docker-lifecycle-initial.json preserved; assertion repaired |
| C-TEST-01 | Windows adjacent wall-clock calls produced equal apply/ACK times | Positive test fixture waits one bounded real clock tick; strict production post-apply ordering retained | host-regression-first.json; later complete suites pass |
| C-ACCEPT-01 | First final runtime matrix rolled back to the same profile selected by the repaired failed apply | Strengthened live case restores the distinct conservative canary profile, retains current credential and obtains fresh ACK | docker-lifecycle-before-distinct-rollback.json preserved; final strengthened17 passes |

These are bounded observations, not attacks against external targets. The
October 18 user-interrupted final run is retained as interrupted, with verified
owned cleanup; it is not relabeled as either application failure or acceptance.

## 3. Design Decisions

| Decision | Selected approach and trade-off | Status |
| --- | --- | --- |
| Management boundary | Trusted local CLI, SQLite catalog/audit and atomic read-only manifest; avoids a network controller and per-message dependency | Implemented |
| Security floor | Two fixed hybrid profiles with 5s/3s operation caps, same TLS 1.3/mTLS/X25519MLKEM768/no-0RTT requirements | Implemented |
| Rollout unit | Per-gateway authorization/token; global lease renewal does not reconnect unaffected groups | Implemented |
| Identity continuity | Preserve baseline gateway/device/incarnation/event namespaces and B queue/dedup state | Implemented |
| Rotation/rollback | At most 60s retiring-leaf overlap; profile rollback creates a new version and keeps current valid credentials | Implemented |
| Offline controller | Last accepted lease at most 300s; after expiry, authorized source buffers within B quota, transport blocks | Implemented; no instantaneous offline revocation claim |
| Proof | Protected live health plus post-operator-apply, current-channel matching ACK, freshness and nonreuse checks | Implemented; local operator remains trusted |
| Storage limits | 3 gateways, 3 devices/group, 12 credentials, 100 versions, 1,000 audits, 32MiB catalog; refusal without automatic deletion | Implemented; limits are not scale measurements |

The issuer uses conventional RSA certificate signatures; hybrid key exchange does
not establish post-quantum authentication. Windows host ACLs and hostile local
administrators are outside the validated issuer/storage protection boundary.

## 4. Implementation

`common/credentials.py` creates a fresh offline issuer and role-specific leaves,
rejecting overwrite, malformed requests and unsupported/expired issuers with safe
codes. Private material is written outside the checkout. `common/management.py`
owns transactional enrollment, disable, versions, status, audit, export, rollback
and revocation. The catalog stores public metadata/references, not key bytes.

`common/managed_config.py` retains B private provisions, validates bounded public
manifests, persists sequence/digest/revocation guard state, and refreshes per-peer
authorization. It atomically checks the actual TLS context's captured leaf when
issuing channel tokens. Only the local role's private references are read.
`common/managed_bootstrap.py` enforces mandatory TLS before application import.
Shared runtime changes are opt-in; B bootstrap behavior remains separate.

Runtime health separates desired and applied version, application time, actual
connectivity, business delivery and safe failure code. Reconnection clears proof;
disconnection/expiry/staleness cannot preserve current effectiveness. Successful
catalog observations must carry that current channel boundary. A failed desired
apply can be recorded explicitly without pretending its channel was established.

The two C probes use fresh external directories, pinned cached Docker images,
separate role mounts, internal networking, resource limits and exact ownership
labels. The lifecycle probe runs unmodified services; operator fixture changes
are explicit. The separate observation probe discloses its runtime-only clock
offset. Neither manufactures ACKs or queries private SQL for acceptance.

## 5. Verification Results

Final source identity is the baseline plus C's allowlist, reconciled by
`evidence/FINAL_AUDIT.json` after all runs finished. Docker Desktop engine 29.8.0
uses local `desktop-linux`; runtime Python 3.12.14, OpenSSL 3.5.7 and cryptography
50.0.1 are captured by each report. Source and harness hashes bind evidence to
the reviewed implementation. Runtime roots are in evidence; reproduction commands
are in OPERATIONS.md and the full regression record.

| Claim | Method and workload | Observed result | Evidence | Verdict |
| --- | --- | --- | --- | --- |
| Complete existing/new regression | Native Windows full pytest suite | 247 passed in 14.46s | full-regression.json | Pass |
| B path preserved | Actual unmodified B Docker bootstrap/services, negative identities, outage/restart, capacity and coalesced frames | 19/19; owned cleanup verified | b-compatibility.json | Pass |
| Channel proof and stale/disconnected observation | Actual TLS/storage/ACK/protected HTTP and CLI; stale-only runtime clock offset 301s | 4/4; old unobserved ACK refused, new channel ACK accepted; cleanup verified | observation-green.json | Pass |
| C01–C05 lifecycle | Two live gateway groups with real simulated source data and matching cloud ACKs | 17/17; owned cleanup verified | docker-lifecycle-final.json | Pass |
| Independent source review | Separate Standards and Spec AI reviewers, follow-up after bounded repairs | No remaining confirmed implementation blocker | REVIEW.md | Pass for source |
| Preservation and cleanup | Protected input hashes and exact owner-resource/process audit | Zero source/harness drift; all12 protected inputs unchanged; no owner resources or validation runner | FINAL_AUDIT.json | Pass |

The final lifecycle matrix covers issuance/role mounts, real source-to-cloud
delivery and application proof, canary/unaffected TCP connection, unknown/classical
profile refusal, missing-key failure/recovery, safe profile rollback, stale catalog
proof, 24s leaf overlap/retirement, active/new revocation, old-manifest refusal after
role restart, fresh credential recovery, existing/new device/gateway disabling,
5s offline lease buffering/exact-event drain, and actual 45s leaf expiry.

The old intermediate 17-case pass predates later source repairs. Earlier full234,
B19 and observation2 records are retained with explicit historical filenames.
Focused issuer/provider/catalog tests overlap the full suite; totals are not
summed into a stronger assurance claim. The 24s overlap, 5s lease and 45s leaf are
short laboratory fixtures, not 24-hour endurance or production timing guarantees.

## 6. Remaining Risks and Next Steps

No management web platform, remote unauthenticated administration, physical-device
integration or production issuer custody is added. Host compromise, Windows ACL
verification, physical ENOSPC, host power loss, sustained load, upgrades and
backup/restore remain unverified here. D owns pilot packaging, performance and
sustained operation, subject to a later user instruction; D is not started by C.

Catalog status is the last privileged observation with a 300s age bound, not a
continuous fleet monitor. Offline revocation is constrained by the last lease and
bounded service scheduling. State/credential/audit limits refuse new mutations;
there is no automatic lifecycle-history cleanup. Follow [OPERATIONS.md](OPERATIONS.md)
for recovery; preserve queues, source/dedup state and persistent control guards.

## 7. Change and Review Record

The C allowlist comprises four new common modules, the opt-in shared runtime
integration, five test files, two C probes, phase records and the necessary current
project/short-term status. User CLAUDE/docs-agent/quota changes, original `.env`,
keys, device/cloud state, Compose, V1 and documentation reorganization are
preserved. [REVIEW.md](REVIEW.md) names the AI review method, findings and hashes.

The user authorized ordinary scoped publication at completed major-phase gates.
Publication will use an English `Phase-Completion: C` commit on
`codex/phase-c-management`, normal push to origin
`https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud.git`, and exact remote
SHA verification. No PR or D implementation is included. A local commit alone is
not publication; the verified result belongs in the conversation after pushing.
