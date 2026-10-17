# Phase B execution specification

Status: **COMPLETE for the Docker/simulation scope on 2026-10-17 Asia/Singapore.**
The prior pause handoff remains the historical recovery record.

Started: 2026-10-16 (Asia/Singapore). User explicitly approved direct B01-B06
implementation. Baseline A was pushed as commit
6e4a48ffc0ec465d6d5d1c29f2272314cff6a601 on codex/phase-a-validation.
Current integration branch: codex/phase-b-secure-path. Original user README,
CLAUDE and docs/agents changes are retained. Recovery snapshot:
tmp/phase-b-start-a2898e857bac498abe5b495c429a324c (ignored, local only).

## Scope and dependency graph

Retain the existing simulated device protocol and V1 comparison baseline. Add
explicit engineering service entry points that reuse its authenticated hello
and AEAD processing. The engineering cloud exposes only mandatory hybrid TLS
for ingestion; there is no plaintext forwarding backend. The old V1 services
remain comparison entry points and are never deployed alongside the engineering
receiver in its isolated project. No original .env, keys, state or Compose stack
is changed. All runtime validation uses fresh synthetic identities/data.

- B01 transport: exact startup policy, direct TLS1.3/mTLS, certificate identity
  to stable gateway/permitted devices; strict bounded framing.
- B02 acceptance: normalized immutable lab-v1 event, atomic bounded persistent
  queue and replay state, explicit refusal and quarantine.
- B03 after B02 contract: transactional cloud business+dedup commit, consistent
  ACK, identity/content conflict rejection.
- B04 after B01-B03: immutable retry, bounded backoff, connection recovery,
  policy/certificate expiry, clock uncertainty and owned shutdown.
- B05/B06 accompany each slice: finite connection/storage/message limits,
  protected loopback health/readback, readiness versus connectivity/delivery.
- Integrate public device -> gateway -> cloud path, restart/ACK-loss/outage/
  capacity/security fault cases, then separate Standards and Spec reviews.

## Approved public acceptance boundaries

Continue the already selected public CLI/process, device TCP protocol, TLS
socket and container HTTP readback boundaries. Persisted storage is exercised
through its public acceptance/pending/commit/ACK/reopen API and killed processes,
not private SQL assertions. Narrow red-before-green slices build each behavior.
Root owns application integration/shared config/health; transport and storage
workers own separate modules and tests; runtime worker owns copied Docker harness.
No independent worker completion counts as integration acceptance.

## Limits and completion

The source of truth is ../phase-a/DELIVERY_CONTRACT.md (lab-v1). Tests may lower
quotas/lease durations to trigger boundaries, never enlarge the security floor.
Normal-load/endurance/resource measurements and upgrade/lifecycle management
remain C/D as scoped by the roadmap; B must pass its minimum fault matrix.
No automatic source reconnect or source exactly-once sampling claim.

Only after the B fault/security matrix, required runtime evidence, original-state
preservation and independent reviews pass may B be marked complete and published
under the standing phase-completion authorization. No intermediate worker commit
or push. The A completion trailer must not be mistaken for B completion.
