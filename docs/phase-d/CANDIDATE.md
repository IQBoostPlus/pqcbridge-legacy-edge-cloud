# Phase D — Runtime-Reviewed Controlled Pilot Candidate

Date:2026-10-20. Runtime and independent evidence review passed for the latest
human-amended30-minute scope. Exact-candidate GitHub Linux CI and main publication
remain pending. This is not a Phase-Completion record yet.

The engineering path previously lacked a self-contained offline pilot package,
coordinated current-state recovery and operational handover. D adds these opt-in
controls without converting V1 state or changing the mandatory hybrid policy.
The sustained run also exposed a shared SQLite metric-read race; the scoped lock
repair preserves real clock-rollback refusal, retry deadlines and event identity.

Verified matching application checks: Windows265/offline Linux265; B19/C17;
formal D9/9 including actual600-second outage/drain,100-sample normal load,
offline install, current recovery, same-schema upgrade, restored-issuer rotation
and rollback retaining newer business state. Formal durable ACK p950.6954s.
New supervisor refusal tests5/5 passed. Earlier19-targeted result is historical.

Latest sustained run: 1800.001 real seconds; 360 sent/accepted/ACK/unique cloud records; durable ACK p95 0.4754s. At least three both-role
rotations, real manifest renewals, resource bounds and zero missed readings were
verified. The private current cold checkpoint's manifest and every payload hash
matched, then owned cleanup was verified. See [runtime audit](evidence/final-runtime-audit.json)
and [experiment report](evidence/endurance-30min-final.json).

A224MiB valid-schema unused-metadata recovery fixture completed with21,604KiB
peak RSS under256MiB admin. This is recovery-memory evidence, not business
capacity. The offline controller/image archive roundtrip also passed on the
same owned engine. Prior interrupted/inconclusive runs remain historical.

Separate AI Standards and Spec final reviews passed; [final review](FINAL_REVIEW.md).
No human security certification, physical-device compatibility, production
acceptance, one-hour or24-hour stability claim is established. Dependency records
do not constitute a current vulnerability clearance. Scope/risk/runbook remain
authoritative. Publish only after exact-candidate Linux CI passes, via normal
fast-forward direct main and exact remote SHA verification; never PR.
