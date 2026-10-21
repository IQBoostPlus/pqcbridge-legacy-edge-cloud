# Phase D — Accepted30-Minute Controlled Docker Pilot

Date:2026-10-20. Status:accepted for the explicit owned Docker/simulated-device
scope after matching runtime, independent Standards/Spec reviews and Linux CI.
The human prospectively reduced the original24-hour target, first to one hour,
then to30minutes. [Scope amendment](SCOPE_AMENDMENT.md). Historical interrupted
or inconclusive attempts remain unchanged and were not retroactively accepted.

## Concrete Delivered Behavior

The opt-in package now supports reproducible offline installation/export/import,
fresh synthetic trust, current-cohort cold backup and isolated restore, strict
receipt/schema refusal, same-schema upgrade/rollback, fixed operator alerts and
incident handover. Source/event/revocation progress is retained during recovery.
Private issuer material stays with the sensitive external recovery cohort.
The shared SQLite metric-read repair serializes the existing connection and
samples expiry clocks under the acceptance lock, preserving delivery/TLS policy.
Original V1/configuration/user CLAUDE/docs-agent/quota changes remain separate.

## Matching Evidence

- Real30-minute run:1800.000536seconds,360 scheduled readings, zero missed;
  accepted=ACK=uniquecloud360, zero backlog/quarantine; durable ACK p950.475430s.
- Three both-role rotations at460.610/921.719/1384.141s;17manifest operations,
  6old-leaf revocations,8catalog credentials/two active roles. Fifty-two resource
  samples: peak17.77%of256MiB,5PIDs,335,872state bytes. CPU/memory/PID/no-host-port/
  no-OOM/no-restart constraints were asserted by the matched supervisor.
- Current cold manifest and every payload hash matched, followed by verified
  current-owner cleanup. [Runtime/source/cold audit](evidence/final-runtime-audit.json).
- Formal D9/9:100-sample handshakes and normal delivery, actual600-second outage/
  complete drain, overload refusal, offline install, current recovery/upgrade,
  restored-issuer rotation and rollback retaining new data. Normal p950.6954s.
- After the shared repair: B19/C17 actual compatibility, Windows265/offlineLinux265
  regression. Current supervisor negative/refusal tests5/5; older19result is historical.
- Recovery-memory fixture224MiB:21,604KiB peak RSS,54.316s checkpoint+restore,
  valid-schema unused metadata only, not business capacity. External controller/
  fixed-image archive roundtrip passed on the same owned engine.
- Separate AI [Standards/Spec final reviews](FINAL_REVIEW.md) passed with no
  unresolved blocker. [Amendment review](AMENDMENT_REVIEW.md) and exact formal
  runner status-only reconstruction remain recorded.
- GitHub Linux validation candidate:4a9431d23b8af834eceae1a85a9fd4a261034612; [CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39393876501)
  completed successfully with both required test and Docker jobs.
  [Machine-readable CI record](evidence/github-validation-ci.json).

## Acceptance and Publication Boundaries

This accepts a single owned synthetic lab candidate, not a production deployment,
physical-device compatibility, one-hour/24-hour stability or a live vulnerability
clearance. RetryTTL/security policy were not shortened. Recovery receipts prove
selected checkpoint integrity, not global freshness. Real source in-flight loss
may be unknown; all broader blockers in [RISKS.md](RISKS.md) still apply.

D completion 87d33bfe5f6982cd743af5fa7ebafb30131fbb4b is verified in remote
main history. Its [main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39394824514)
passed both test and Docker jobs; those facts were checked on 2026-10-21.
This records publication of the existing completion, not another D completion.
Future documentation updates require their own exact-commit CI/publication
verification and a normal fast-forward preserving remote history. Keep their
receipts in the conversation/local artifacts; do not chase a document's own SHA.
Old inconclusive project network/state volumes remain deliberately retained;
current-run cleanup never claims every historical Docker resource was removed.
