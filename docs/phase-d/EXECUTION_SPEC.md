# Phase D — Controlled Docker Pilot Candidate

Date: 2026-10-20. Status: implementation started by explicit human instruction.
Baseline: caffc697e4975ab46266e9cb011542408b4bdfb8. Working branch:
codex/phase-d-pilot. Preserve unrelated CLAUDE/docs-agent/quota changes and V1.

## Scope and Deliverables

Follow SHORT_TERM_PLAN section 5 and the frozen A delivery contract. D01 adds a
versioned, offline-buildable Compose package, exact image/source/dependency
inventory, explicit synthetic provisioning and staged same-schema upgrade.
D02 adds cold, integrity-checked recovery into fresh isolated state, requiring
an independently retained current recovery receipt; stale backups must never
replace newer event/source/revocation state. D03 measures full handshakes,
durable delivery, overload, ten-minute outage recovery and real sustained load.
D04 consolidates evidence and separate AI Standards/Spec reviews. D05 adds an
operator CLI with fixed alerts and incident/recovery procedures.

The environment remains owned Linux x86-64 Docker and simulated one-way sensor
data. No production mode, external target, host port, arbitrary algorithm
selection or V1 data conversion is authorized. Reject a request to use this
package as a real deployment. Provision fresh synthetic secrets outside Git;
the administrator supplies the trust anchor through the provisioning artifact.

## Current Acceptance Gates

The explicit human 30-minute amendment on2026-10-20 supersedes the original
24-hour duration gate: [scope amendment](SCOPE_AMENDMENT.md). Other gates remain.

- One device, one reading per five seconds; 0.5 CPU/256 MiB per service; bounded
  logs and the existing 256 MiB state/10,000 pending/100,000 cloud row limits.
- At least 100 full, non-resumed TLS handshakes and 100 durable-ACK observations;
  p95 <= 1 second for each. Classical versus hybrid comparison is an isolated
  benchmark only; services retain mandatory X25519MLKEM768 and TLS 1.3/mTLS.
- An actual 600-second cloud outage; first authenticated matching durable ACK
  <= 60 seconds after verified availability with renewed policy. Reconcile the
  entire accepted backlog separately and report drain time.
- A continuous >=1,800-second real normal-load run with resource samples,
  accepted/ACK/committed reconciliation, bounded150-second lease renewal and
  both-role credential rotation every450seconds (at least three rotations).
  A shorter diagnostic run is never acceptance. This establishes no24-hour claim.
- Reproduce installation, same-schema upgrade/rollback, isolated current backup
  restore and refusal of wrong receipt, changed contents and unknown schemas.
- Keep earlier B/C fault/security evidence historical; rerun matching integration
  when D changes its boundary. Separate Standards/Spec review and exact-candidate
  Linux CI remain final publication gates. No Phase-Completion: D until all pass.

## Stop and Recovery Conditions

Retain failed/interrupted evidence. Stop on resource breach, lost reconciliation,
unknown schema, stale recovery authority, unavailable Docker or unsafe quota.
Never silently relax thresholds. The human-amended 30-minute job may run with progress
and a reproducible recovery prompt; elapsed time must be measured by the job.
Preserve original resources; remove only this run's verified ownership labels.
