# [Phase / Milestone] — [Concrete Change or Evaluation]

Date: [YYYY-MM-DD]. Status: [Proposed / In progress / Awaiting verification / Accepted / Paused].

## 1. Background and Scope

Describe the problem, trigger, intended behavior, affected components, and explicit boundaries. Identify the baseline commit and relevant local changes. State whether this milestone changes implementation or only evaluates it.

## 2. Findings and Evidence

| ID | Preconditions and observed behavior | Impact | Evidence and confidence |
| --- | --- | --- | --- |
| [ID] | [Concrete observation] | [Bounded consequence] | [Artifact and method; observed or inferred] |

Separate inherited observations from this milestone's results. Preserve unsuccessful reproductions and environmental constraints.

## 3. Design Decisions

| Decision | Alternatives and trade-offs | Selected approach | Status and reason |
| --- | --- | --- | --- |
| [Decision] | [Practical alternatives] | [Approach] | [Proposed / Accepted / Deferred / Rejected, with rationale] |

Identify changed assumptions, security boundaries, compatibility, persistence, and rollback constraints. Link requirements and prior decisions.

## 4. Implementation

Explain the changed behavior, affected files or interfaces, and why the change resolves the finding. Include meaningful fail-first evidence where applicable. Record unexpected implementation or harness problems. For an evaluation-only phase, state that no implementation changes were made.

## 5. Verification Results

| Claim or requirement | Method and environment | Expected result | Observed result | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| [Claim] | [Static / unit / integration / live / fault test] | [Threshold] | [Measured result, or not run] | [Path] | [Pass / Partial / Fail / Not verified] |

Record revisions, dependencies, workload, commands, and redacted output needed to reproduce results. State whether tests exercise unchanged applications or instrumented fault harnesses. Report regressions and cleanup separately. Never substitute a configured value for an observed result.

## 6. Remaining Risks and Next Steps

List unresolved defects, accepted limitations, unverified environments, and the next bounded actions. Include deployment-blocking conditions and safe recovery steps. A planned follow-up is not a completed control.

## 7. Change and Review Record

List changed artifacts, reviewer/tool provenance where relevant, and outstanding review requirements. For authorized publication, record the direct-push destination and verified remote commit after publication. Do not claim publication from a local commit alone.
