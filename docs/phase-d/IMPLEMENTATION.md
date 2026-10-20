# Phase D — Package and Recovery Implementation, Endurance Pending

Date: 2026-10-20. Status:30-minute runtime and separate final evidence reviews passed; exact-candidate Linux CI pending.
Baseline caffc69; current branch codex/phase-d-pilot. D is not accepted/published.

## Concrete Result

The new opt-in package builds offline from the validated immutable image and
generates new synthetic trust/source provisions in an external directory. An
exported controller works without the original checkout; image archives have
recorded checksums and exact image verification. Services retain the mandatory
hybrid floor and use Linux named volumes rather than Windows bind SQLite state.
The original V1 and user config/state remain separate and unchanged.

Cold recovery carries the coordinated delivery/source/dedup/catalog/guard/trust
and private issuer cohort. It requires an independently held current receipt and
an empty isolated destination. Streaming hashes and strict structural checks
bound memory and reject unsupported state. A failed backup now retains stopped
state instead of deleting the only copy. The local CLI reports actionable fixed
alerts and credential expiry without echoing tokens or payloads.

The sustained test exposed an existing shared-connection metric read outside its
lock. The observed durable counters stayed intact while concurrent reads could
return0 or raise TypeError. The fix serializes metric reads and captures expiry
time inside the acceptance lock, preserving genuine clock-rollback refusal.
The independent review and red/green provenance are in [REVIEW.md](REVIEW.md).

The latest30-minute run completed1800.000536seconds with360 unique cloud records,
zero missed readings, three rotations and durable ACK p950.475430seconds.
The cold receipt/all-payload hash audit and current owned cleanup passed.
See [candidate](CANDIDATE.md) and [final review](FINAL_REVIEW.md).

## Current Evidence Boundary

- Current Windows regression:265 passed21.07s. Offline Linux:265 passed13.93s.
  Linux is a local no-network container check, not GitHub CI.
- After the shared delivery fix, actual B compatibility19/19 and actual C
  lifecycle17/17 passed, with ownership cleanup verified.
- A224MiB valid-schema unused-metadata fixture completed cold backup and restore
  with peak RSS21,604KiB under the256MiB admin cap. This exercises recovery memory,
  not sensor payload or business throughput capacity.
- Offline image export/import via the external controller passed with a
  56,434,688-byte archive. The image contains source, not runtime private keys.
- The initial formal D run failed during workload execution; preserve it as
  failed. A later pre-delivery-fix full matrix passed, but is historical for the
  repaired shared source. Matching formal-20261020-03 passed all nine cases;
  see evidence/formal-current.json. The exact source reconstruction in
  evidence/one-hour-resume-proof.json confirms that its later runner delta only
  changes initial/error status reporting; all application source hashes match.
- The35-second supervisor diagnostic passed with seven reconciled records and
  a final cold checkpoint. It satisfies neither the 30-minute nor24-hour gate.
- The real24-hour run at endurance-20261020-main was safely stopped by human
  request after925.665 seconds. It is interrupted, not accepted; private cold
  checkpoint and verified owned cleanup completed. A fresh full-duration run
  was originally required. The later explicit [human amendment](SCOPE_AMENDMENT.md)
  instead requires one fresh continuous hour; the old partial result is unchanged.

The current complete phase status and evidence pointers are in [STATUS.md](STATUS.md).
Final risk disposition, independent runtime-evidence review and exact-candidate
GitHub Linux CI remain publication gates. No main push or PR was performed for D.
