# Phase D — Independent Review and Finding Record

Date: 2026-10-20. **Independent static/final evidence reviews and matching GitHub Linux CI passed; accepted bounded scope.**
Baseline caffc697e4975ab46266e9cb011542408b4bdfb8, plus the explicit D working
allowlist including untracked D files. Current scope is defined in EXECUTION_SPEC.

## Review Provenance

Root used code-review with two independent AI reviewers, d_standards and d_spec.
They inspected the actual untracked files as well as the baseline diff. Reviewers
did not implement fixes, run Docker, publish or claim human security review.
Repeated scoped re-reviews kept Standards and Spec independent. Their latest
static pass found no remaining implementation blocker in the delivery-lock,
recovery-preservation and worker-readiness changes. Runtime/endurance and CI gates
remain separate, open requirements. This is not production certification.

## Findings and Disposition

- D-PKG-01: exported controller depended on the original checkout/B test helper.
  It now locates bundled source/common and carries its own fixed packaging logic;
  the exported-entry subprocess test runs outside the original checkout.
- D-REC-01: whole-file hashing could allocate near the admin memory ceiling.
  Recovery and source inventories now stream hashes. The224MiB valid-schema
  synthetic metadata fixture completed cold backup/restore with21,604KiB peak
  RSS under the256MiB cap; this does not establish business-capacity performance.
- D-REC-02: schema checks covered table names only. Checks now include column
  types/nullability/primary keys, control-body version, control SQL version and
  unexpected triggers. Deliberately wrong versions/columns are refused.
- D-REC-03: recovery omitted offline issuer material. Issuer/issued files are now
  in the private coordinated cohort. Recovery/rotation tests preserve authority,
  issue fresh roles and revoke their old leaves. Backups are explicitly sensitive.
- D-OPS-01: row-capacity causes were missing. Fixed row/refusal alerts now
  complement byte limits, expiry/mismatch and unavailable-health reporting.
- D-REC-04: automatic harness cleanup could delete the only state after a failed
  checkpoint. Both finalizers now retain stopped resources and report failure;
  two injected unavailable-backup regressions assert cleanup is not called.
- D-RUN-01: detached worker result could be read before creation. The endurance
  supervisor now uses a bounded first-result wait. Missing/failed results cannot
  be relabelled as endurance success.
- D-DATA-01: expiry's metric read after its transaction did not own the shared
  SQLite connection lock. Real health briefly reported accepted0/ACK71. The tight
  GatewayQueue probe also reported accepted0 with persisted17, or a read TypeError.
  A cache-off diagnostic control passed; the production fix keeps the default
  cache and serializes all metric reads with the existing RLock. Expiry now also
  acquires that lock before sampling clocks, avoiding a stale pre-lock sample
  being compared with a newer accepted timestamp. Regression tests preserve
  default-cache concurrency and the clock/acceptance boundary. Existing strict
  retry deadlines, rollback refusal and event IDs remain unchanged.
- D-MEAS-01: Windows bind state produced a1.07s two-sample diagnostic latency.
  The package now uses Linux named state volumes, as frozen in A. This short
  result was a failed diagnostic, never a basis for lowering the1s threshold.

The analogous upstream Python concurrency report is background, not a substitute
for the observed local red/green loop:
[CPython issue118172](https://github.com/python/cpython/issues/118172).
See evidence/sqlite-race-*.json. The pre-fix race is nondeterministic: a short
regression invocation also passed before repair, while repeated pressure runs
failed. Preserve that limitation rather than claiming a deterministic red test.

See [independent amendment review](AMENDMENT_REVIEW.md) for separate Standards
and Spec reports: zero unresolved static findings, with final runtime and matching CI subsequently passed in COMPLETION.md.

## Final Evidence Review

Separate Standards/Spec final runtime reviews passed with no unresolved blocker:
[FINAL_REVIEW.md](FINAL_REVIEW.md). The human-amended30-minute result passed all
recorded gates. The earlier24-hour/one-hour failures or inconclusive records remain
unchanged. Matching GitHub Linux CI subsequently passed; see COMPLETION.md. Any final
publication commit must pass its own exact CI before a verified normal main push.
