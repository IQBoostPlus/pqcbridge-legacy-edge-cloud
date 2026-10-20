# Phase D — Human Pause Handoff

Saved: 2026-10-20, Asia/Singapore. Authority: the human explicitly requested
"pause all work and write the handoff prompt". **D is paused, incomplete and
unpublished.** No implementation, experiment, review, commit or publication may
resume without a new human instruction. [Resume prompt](RESUME_PROMPT.md).

## Preserved Checkout

- Workspace: D:\Code\pqcbridge-legacy-edge-cloud.
- Branch: codex/phase-d-pilot. HEAD: caffc697e4975ab46266e9cb011542408b4bdfb8.
- Origin: https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud.git.
  Last actual remote-main observation during this work matched that SHA; no new
  remote fetch or publication was done for the pause. Recheck before later push.
- Working files are saved, with no staged changes and no D commit. Baseline:
  tmp/phase-d-baseline-be4eff8f72a54f9388f01082a39d576c (patches, status, protected hashes).
  Pause snapshot: tmp/phase-d-human-pause-20261020 (tracked patch, file inventory
  and exact hashes). Untracked D files remain in the checkout; do not clean them.
- Preserve pre-existing CLAUDE.md, docs/agents, Codex-Quota.ps1 and
  .codex-quota-checkpoints. They are not D publication candidates. Original V1,
  Compose, .env, demo keys and original data remain protected.

## Completed Implementation and Checks

New package/recovery/operations code: common/pilot_ops.py, deploy/phase_d,
scripts/phase_d and pilot/concurrency regression tests. The package is opt-in,
offline-exportable, synthetic-only, uses bounded Linux state volumes, preserves
the mandatory hybrid floor and has no published host ports. Cold recovery carries
coordinated delivery, source, dedup, catalog, guard, trust and private issuer
state; restores require an independent current receipt and fresh destination.

The scoped common/delivery.py repair serializes shared SQLite metric reads and
captures expiry clocks inside the existing acceptance lock. Observed pre-fix
read corruption did not change persisted counters. Real backward-clock refusal,
ACK semantics, retry deadlines and event identity are preserved.

- Windows: 265 passed in 21.07s; tmp/d-full-regression-final.xml.
- Offline no-network Linux: 265 passed in 13.93s; sanitized
  [report](evidence/linux-regression-final.json). This is not GitHub CI.
- Repaired-source B compatibility 19/19 and C lifecycle 17/17 passed with owned
  cleanup: b-compat-20261020-01 and c-compat-20261020-01 under the external root.
- formal-20261020-03: 9/9 passed; finished 2026-10-20T03:48:24Z. Includes actual
  100-record normal load (durable ACK p95 0.6954s), 600-second cloud outage/drain,
  fresh offline install, isolated classical/hybrid handshake comparisons, overload
  refusal, current-state recovery/upgrade, restored-issuer rotation and rollback.
  Three current cold vaults retained; three owned projects cleaned successfully.
  [Formal report](evidence/formal-current.json).
- Recovery-memory proof: valid-schema 224MiB unused-metadata fixture, checkpoint
  plus restore 54.3155s, peak RSS21,604KiB under256MiB admin. Not business capacity.
- External controller/image archive export/checksum/import passed (56,434,688 bytes).
- Independent d_standards/d_spec static re-reviews completed without remaining
  implementation blocker. Final evidence reviews have not happened.

Formal-run application hashes match the current candidate. Its recorded runner
hash is ea706f4ab497403276e4b7ff77257b25bc69547940502f8d376fefa9be4e82f0;
acceptance.py subsequently changed the initial report status to running and sets
failed in the exception handler. This reporting-only delta needs explicit final
review, not a false zero-drift statement. No workload assertion was changed.
Current delivery SHA256:361bffe0cfcbd4b65112e5f2fb9f5d9221f11daebfe2d6865bba974d64a4816f.
Current pilot_ops SHA256:93652aab98df7596da34dbe1693755a7ae0d6779172c70fa87f6330078bb07af.

## Stopped Work and Retained Private Artifacts

External root: D:\Code\pqcbridge-phase-d-artifacts. It contains generated
credentials, private issuer keys, logs, state, receipts and cold vaults. Never
stage it or print its private contents. Keep failed and diagnostic records.

The real 24-hour run endurance-20261020-main was stopped through its STOP file.
Former supervisor PID27520 exited; result status is interrupted, not passed.
Workload began 2026-10-20T03:34:42Z and ran 925.665 seconds. Latest observation:
186 sent/accepted/ACK, pending0, 27 resource samples, no six-hour rotation yet.
There is no final-success cloud reconciliation claim. At 2026-10-20T03:50:59Z,
the supervisor retained final-state-vault/snapshot and verified removal of its
owned containers/network/state volumes. Preserve the vault and the independently
held current receipt; recovery authority is not proof of global freshness.

Pause inventory found no D containers, networks or acceptance/endurance Python
runners. Two older diagnostic-owned volumes remain retained, deliberately not
deleted: pqc-d-f7e3c5e57232e19c_cloud_state and
pqc-d-f7e3c5e57232e19c_gateway_state. Their contents were not inspected during
pause. Do not claim all historical volumes were cleaned or delete unknown state.
The current D review agents are completed and no new review was dispatched.

The recurring publisher pqc-bridge-github is verified PAUSED; its existing
15-minute cadence and prompt were preserved. It must not publish during this
pause. This does not claim unrelated user processes or chats were stopped.

## Next Safe Steps After Explicit Resumption

1. Read the authority documents and run a fresh safe quota Check. Inspect Git,
   candidate hashes, existing evidence, Docker availability and actual runners.
   Preserve the dirty workspace; do not rerun passed suites just for context.
2. Start one fresh, uniquely rooted full 86,400-second experiment only when
   authorized to resume and the host can stay awake. The interrupted duration
   cannot be continued or summed. Do not restore expired credentials to bypass
   current trust checks. Keep old STOP/result files immutable.
3. Review actual full-duration renewals/rotations, resource bounds, final durable
   accepted/ACK/committed reconciliation, checkpoint and owned cleanup. Match
   source/harness hashes; retain unresolved gates if a run fails or drifts.
4. Complete final separate Standards/Spec evidence reviews and exact-candidate
   GitHub Linux CI. Reconcile current documentation and risks before acceptance.
5. Only then use standing scoped commit/main publication authority, with an
   explicit allowlist excluding user changes, secrets and raw artifacts. Validate
   on the existing branch, ordinary fast-forward origin/main and verify SHA.
   Never create or merge a PR. No D completion trailer is appropriate yet.

The 24-hour gate, final independent evidence review and exact-candidate GitHub
Linux CI remain open. Existing A/B/C acceptance/publication remains valid; do not
duplicate earlier commits. [Risk register](RISKS.md), [review](REVIEW.md),
[runbook](OPERATIONS.md) and [execution contract](EXECUTION_SPEC.md) define scope.
