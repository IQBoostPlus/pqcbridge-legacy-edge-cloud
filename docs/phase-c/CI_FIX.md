# Phase C Follow-up — Portable Old-ACK Regression Fixture

Date: 2026-10-19. Status: Verified published to main after successful GitHub Linux CI.
Accepted repair:2cde91dfabdf4435e298243b2b52bb1dcb48723c; application code unchanged.

## 1. Background and Scope

C completion4b70e0d4d6f2e71be9cd592e777b4936663314a5 passed247 native Windows
tests and the recorded managed Docker checks, then failed the GitHub Linux test
job. Both push run39257392131 and pull_request run39257794324 reported the same
failure:246passed/1failed in tests/test_management.py. Their Docker jobs passed.
This follow-up changes only one test fixture; all application code is unchanged.

## 2. Finding C-CI-01

The regression constructed an observation before begin_apply but expected only
ack_not_post_apply_or_reused. Linux correctly rejected the earlier observation
first with observation_not_applying. Windows clock granularity could give the
two actions equal timestamps, allowing execution to reach the later ACK guard.
Both guards reject the input; the test selected its expected error using an
uncontrolled cross-platform timing assumption.

An offline, unchanged committed-source Linux reproduction failed identically in
0.24s, without a PR merge or network dependency. This rules out the PR merge and
the GitHub Python patch version as necessary causes of the failure.

## 3. Repair

After begin_apply, refresh only the observation timestamp while retaining the old
ACK and channel timestamps. This models a fresh observation containing an old
ACK and reaches the specific post-apply/nonreuse guard the test is meant to check.
The expected error, wrong-target rejection, accepted fresh proof, reused-ACK
rejection, status and audit assertions remain intact. No production guard or
security floor is changed; no test is skipped or assertion broadened.

## 4. Verification

| Check | Observed outcome | Boundary |
| --- | --- | --- |
| Unchanged Linux reproduction | Same expected/actual-error mismatch,1failed0.24s | Exact committed source; cached image; selected regression |
| Complete Windows suite after repair | 247passed12.71s | Native host; fresh external temporary data |
| Complete offline Linux suite after repair | 247passed9.51s; owned container removed | Python3.12.14/pytest9.1.1/OpenSSL3.5.7, cached image, no network |
| GitHub Linux CI before main | 247passed8.42s; test and Docker jobs pass, run39259917002 | Exact repair2cde91d; Ubuntu/Python3.12.15 |
| Main CI after ordinary fast-forward push | Successful, run39260202385 | Same repair SHA; remote main ref independently verified |

Local evidence: [ci-fixture-fix.json](evidence/ci-fixture-fix.json). Frozen source
copies, raw stdout/stderr and result files remain outside the checkout under the
recorded runtime roots. The first complete local Linux attempt omitted the tracked
.gitignore from its exported test copy, causing an unrelated fixture failure;
that harness omission was corrected and its original result retained externally.

Historical C evidence keeps its original bytes and outcomes. The original full
suite/source audit describes4b70e0d; this record describes the later test-only
repair. Application source is unchanged, so the already passed C17/B19/observation4
service matrices are not rerun for this test-only change. No endurance, production
security or physical-device acceptance is added.

## 5. Review and Publication

Root reviewed the three-line test diff against the actual Linux failure and
verified that only observation age is advanced. Existing independent C application
reviews remain applicable; this follow-up does not claim a new independent review.
User-authored CLAUDE/docs-agent/quota work and protected original inputs remain
excluded from the fix commit. No next-phase implementation is included.

The latest explicit user instruction requires no PR and direct main publication
after successful Linux CI. The repair passed
[pre-main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39259917002),
then the same commit was normally fast-forwarded to main and verified by its
exact remote SHA. [Main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39260202385)
also passed. No PR was created or merged. Keep these verified outcomes as history
when later documentation commits advance main; do not generate commits solely
to refresh a publication timestamp or self-referential documentation SHA.
