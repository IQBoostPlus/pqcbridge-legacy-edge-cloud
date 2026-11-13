# Sprint 2 user-understanding experiment

## Group confirmation — 13 November 2026

The user reports that the group endorsed the review conclusions, including the
report's metric interpretation, limitations and review direction. This group
endorsement is confirmed. It is not a set of unaided task responses; participant
answers, assistance and comprehension scores below remain uncollected.

## Current customer-report validation protocol

The corrected [GOAL](SPRINT_GOAL.md) places the key customer's reporting change
first. The earlier technical rehearsal and credibility-focused prompts below
remain historical. They do not verify the new class aggregation or report, and
no human results are supplied by this protocol. Formal sessions are supporting
work after the required increment and technical checks; actual review feedback
and course human-factors reflection remain necessary.

Use the new synthetic customer fixture and a fixed historical reporting clock.
Record the tested revision, fixture, selected customer, clock, viewport,
facilitator and actual participants. Preserve unaided answers before showing
any answer key or explanation. Rotate Sarah/Michael/Emma roles where useful.

| Task | Prompt supplied without answer key | Reviewer criterion, shown only after first response |
| --- | --- | --- |
| CUS-01 / Emma | Explain how much customer data is potentially exposed, and the unit used. | Distinct logical items by class; three buckets reconcile; segment share and byte volume are different quantities |
| CUS-02 / Sarah | Trace one exposed item to the connection evidence and explain what remains unknown. | Any known required classical segment establishes potential exposure; concurrent quality flags remain; no confirmed attack claim |
| CUS-03 / Sarah | Explain an unresolved item and its confidentiality assumption. | Missing mapping, unknown/stale/future evidence or classification remains visible; short lifetime does not imply zero risk |
| CUS-04 / Michael | Explain the migration work remaining for the customer and the replacement constraint. | All required customer segments included; 2028 replacement conflicts with 2027-12-31; planned action is not completed migration |
| CUS-05 / Emma | Propose a next decision that preserves service and explains the customer position. | Identifies budget/continuity/deadline trade-off and options/escalation without claiming accepted waiver, funding or feasibility |
| CUS-06 / Emma | Explain what prevents a complete or current all-clear and where the report can be checked. | Unknown attribution/scope, evidence time and class totals are explicit; source IDs/shared exported calculations support traceability |

Score each explanation 0 (materially wrong/unsupported), 1 (partly correct,
missing relevant scope/reason/action), or 2 (correct and justified); maximum 12.
Keep missing responses missing, preserve assisted answers separately, and
publish no human success rate before actual collection. If a critical scope,
quantity or deadline misunderstanding occurs, record the observation, selected
change or no-change rationale, owner and comparable retest. A small internal
team exercise does not establish external-user comprehension.

| Actual customer session record | State |
| --- | --- |
| Date, facilitator, actual participants and revision | Pending actual session |
| Fixture, customer, clock and device | Pending actual session |
| Unaided answers, evidence locations and scores | Not collected |
| Assisted answers, disagreements and decisions | Not collected |
| Corrections, acknowledged owner/target and retest | Pending actual findings |

Independent technical expectations are supplied in
[customer-expectations.md](experiments/customer-expectations.md); observed checks
belong in [VERIFICATION.md](VERIFICATION.md), not in the human response fields. The
existing response sheet can be reused with the CUS-01 through CUS-06 prompts;
the old generated scenario kit remains a legacy-import/indicator regression
kit and must not be described as a customer-report fixture.

### Technical readiness for the customer tasks

The integrating agent reports 39/39 model tests, a 44-module build, 11/11 legacy
comparisons and scoped customer/role/import/export/keyboard checks passed. Final
production preview loaded the built JavaScript and showed six items split 2/2/2;
scoped error logs were empty and the 390 × 844 layout had no page horizontal
overflow. These checks make the protocol exercisable; actual first responses
and comprehension scores above remain uncollected. See
[VERIFICATION.md](VERIFICATION.md) for exact checks and evidence artifacts.

## Historical evidence status and purpose

Prepared on 12 November 2026. The group's confirmed priority is indicator
credibility first. This artifact contains an **executed AI technical rehearsal**,
a group discussion draft and the human experiment protocol. Technical results
are available below; participant measurements have not yet been collected.

Question: can a reader distinguish reported migration progress from evidence
quality and security assurance, and explain a justified next action for Sarah,
Michael and Emma? The metric contract in [SPRINT_GOAL.md](SPRINT_GOAL.md) is the
reference. An answer key available to the AI cannot validate human comprehension.

## Executed technical rehearsal

Baseline product revision: `7ce2898745e69a5e4943080e605db5b2f36dcd3b`.
The development rerun uses the Sprint 2 working tree; source SHA-256 hashes are
retained in results.json. The original planning result is preserved in
[results-planning-baseline.json](experiments/results-planning-baseline.json).
Inputs: existing synthetic fixture and cloned variants, no backend data. The
reporting clock is fixed at `2026-11-08T04:00:00Z` unless changed explicitly.

Reproduce from the repository root:

```powershell
node docs/sprints/sprint-2/experiments/run_experiment.mjs
```

The [rehearsal script](experiments/run_experiment.mjs) compares predeclared
expectations with actual model results and retains both in
[results.json](experiments/results.json). It reuses the reporting model, so
this is a separate expectation comparison, not an independently implemented
reporting engine. These checks overlap baseline tests intentionally to provide
named discussion scenarios. Result this batch: **11/11 comparisons passed**.

| Case | Independently stated expectation / observed result | Interpretation for discussion |
| --- | --- | --- |
| C01 | 8 total = 5 PQC + 2 fallback + 1 unknown; 62.5%; red | Unknown remains in the denominator; suspected downgrade drives investigation |
| C02 | Fallback filter returns SEG-001 and SEG-007; global coverage remains 62.5% | Inventory selection does not redefine the global metric |
| C03 | Empty coverage is null; overall unknown | No records cannot establish 100% migration |
| C04 | One unknown yields 0% reported PQC and unknown overall | 0% reported PQC is not proof that every segment is classical |
| C05 | Five PQC segments after 48 hours: 100% coverage, 5 stale, overall unknown | Past migration and current evidence quality are different |
| C06 | Pump station A: SEG-001 fallback and SEG-002 PQC; 50% for this two-segment scenario | Gateway PQC does not cover the complete device path |
| C07 | Expected fallback only: amber, no suspected case | Approved synthetic exception is not an attack finding |
| C08 | Default fixture after 48 hours: red, 8 stale, 1 suspected, 3 risks | Investigation takes priority while stale evidence still needs attention |
| C09 | Exactly 24 hours: 0 stale; 1 millisecond later: 1 stale | Freshness boundary is strict greater-than, per observation |
| C10 | Reporting clock before the PQC observations/snapshot: unknown | Future-dated evidence cannot establish all-clear |
| C11 | Unsupported status rejected | Invalid data cannot silently become healthy or empty data |

## Three-role source walkthrough

The initial AI walkthrough inspected model, fixture and Vue source. A subsequent
Sprint 2 browser walkthrough exercised the implemented increment as recorded
below. Existing Sprint 1 screenshots remain historical evidence.

| Role / task | Actual source evidence inspected | AI rehearsal conclusion |
| --- | --- | --- |
| Sarah: distinguish expected fallback from a suspected downgrade and select an investigation | SEG-001/007 reasons and confidentiality fields; RolePanel sorts suspected cases first and exposes reason/confidentiality/impact/action | SEG-007 merits investigation; SEG-001 requires exception review. Neither is proof of a confirmed HNDL attack. |
| Michael: explain Pump station A's remaining migration work | SEG-001/002 segment identities, replacement blocker and business impact; migration role excludes PQC rows and shows remaining blockers | Retain segment-level scope; review the legacy exception and replacement plan while accounting for lost pump monitoring. |
| Emma: explain 100% reported migration with stale evidence | C05 model output; CoverageOverview separates coverage, status and evidence freshness; MethodologyView explains clock and status | Request refreshed evidence before a current all-clear. The source contains the needed explanation, but real users' ability to find it remains unmeasured. |

Source links: [model](../../../dashboard/model.mjs),
[role view](../../../dashboard/src/components/RolePanel.vue),
[overview](../../../dashboard/src/components/CoverageOverview.vue),
[definitions](../../../dashboard/src/components/MethodologyView.vue).

## Group discussion draft

Confirmed group decision: indicator credibility comes first. The following
discussion points are proposed for member review; they do not record measured
participant responses or establish attendance.

| Member / discussion task | Question for review | Proposed clarification and conclusion |
| --- | --- | --- |
| Changzhengyuan Chu / explain 62.5% and apply the fallback filter | Should the overview become 0% when only fallback rows are shown? | Filtering changes the inventory, while coverage remains global at 5/8. Keep scope and units beside the metric. |
| Valerii Lebedev / brief Emma using C05 | Can a report claim current safety when coverage is 100% but evidence is stale? | Reported segments were migrated in the snapshot, but current assurance is unavailable. Show the selected clock and evidence time in the demonstration. |
| Jinghao Lei / guide Michael through Pump station A | Does the PQC gateway link mean the complete pump path is migrated? | The two segments differ and a legacy exception remains. Consider a visible path-scope reminder, subject to user testing. |
| Cheng Peng / guide Sarah through SEG-001 and SEG-007 | Why does red persist when the observations become stale? | Investigation takes priority alongside stale evidence; neither label confirms an attack. Explain both reasons rather than relying on the headline color. |
| Zhizhou Zhao / prepare an executive explanation of empty and unknown data | Does unknown-only 0% mean every connection is definitely classical? | No segments are reported PQC, but unknown evidence remains unresolved. Report numerator, denominator and uncertainty together. |

Proposed conclusions for group review: retain the credibility-first priority,
keep denominator and segment scope visible, explain coverage separately from
freshness, and preserve both investigation and uncertainty reasons. These are
**candidate changes**, not measured defects, implemented fixes or actual group
acceptance. See [TEAM_REVIEW.md](TEAM_REVIEW.md) for the discussion summary.

## Human experiment protocol for actual validation

Prerequisite: team reviews the metric contract and expected/observed comparisons
under S2-US-01/02. Invite the five roster members; record who actually participates,
the facilitator and consent to storing their responses. Proposed roles rotate so
each participant attempts Sarah, Michael and Emma tasks. Do not treat names in
the discussion table as actual recruitment or consent.

1. Record date, product revision, device/viewport and reporting clock. Use the
   default fixture and C03/C05/C06 variants generated from the same source.
2. Give task prompts without the answer key or discussion notes. Preserve the
   unprompted first answer and where the participant looked. Ask for a reason
   and next action, not only the color or percentage.
3. Ask each participant to explain: the 5/8 denominator and filtered scope;
   expected versus suspected fallback; the mixed pump path; stale 100%; empty
   versus unknown evidence; and the action Emma should take.
4. Score each explanation using the predeclared rubric: 0 = materially wrong or
   unsupported; 1 = partly correct but missing scope/evidence/uncertainty;
   2 = correct interpretation with the relevant reason and action. Preserve
   missing responses as missing. Maximum 12 per participant; do not publish a
   success rate before collecting data.
5. Discuss errors only after first responses. Record actual comments and
   agreement/disagreement separately. A post-explanation correct answer is an
   assisted answer, not proof of an improved interface.
6. Proposed release criterion, for team approval: each participant correctly
   explains the denominator, stale-100% limitation and mixed-path limitation
   without assistance. Any critical misunderstanding triggers review and a
   comparable follow-up task; log remaining problems before acceptance.

| Actual session field | Value |
| --- | --- |
| Date, facilitator, actual participants and consent | Pending human session |
| Revision, scenario, clock and device | Pending human session |
| First answers, evidence locations and rubric scores | Not collected |
| Assisted answers and actual discussion results | Not collected |
| Selected changes, owner, due date and retest evidence | Pending actual feedback and planning |

The sample is a small internal team exercise with prior product familiarity,
not a representative study of external users. Report that limitation alongside
any future human results. Record collected responses separately from the
discussion questions when preparing reports or slides.

## Development batch: ready-to-use session kit

From the repository root, run:

```powershell
node docs/sprints/sprint-2/experiments/prepare_sessions.mjs
```

Six valid JSON datasets are supplied under [scenarios](experiments/scenarios/default.json):
default, empty, unknown, expected-fallback, mixed-path and stale-pqc. A seventh
file deliberately contains invalid input for recovery checks. The stale-pqc
variant has five observations older than 24 hours even under the historical
clock. Select **Historical snapshot** to reproduce the prepared expectations.
Use Dataset -> Load local JSON, then return to Overview, Indicators or a role
view. Reset demo restores the original fixture and historical mode.

The [participant response sheet](experiments/RESPONSE_SHEET.md) contains prompts
and blank first-response, assistance and scoring fields. Do not give participants
the answer-key sections above before collecting their first responses.

Actual technical walkthrough results in this development batch:

- Sarah's view identifies SEG-007 for investigation; Michael's view shows the
  SEG-001 legacy exception; Emma's view shows the suspected-downgrade risk.
- The six valid datasets load and show the expected metrics. The stale-pqc
  variant shows 100% reported coverage and insufficient evidence with five
  stale observations. The invalid file is rejected; export is disabled until
  a valid snapshot is restored.
- Indicator evidence exposes contributing IDs and coexisting reasons. In
  current-time mode the default snapshot shows both investigation and all eight
  stale segments. The global percentage remains 62.5% with fallback filtered.
- Path context shows both SEG-001 fallback and SEG-002 PQC for Pump station A.
- An actual downloaded report was checked against the eight source records,
  five numerator IDs and selected historical clock.

These are observed application behaviors. Human answers and comprehension
scores have not been collected. Screenshots, commands, limitations and source
review are in [VERIFICATION.md](VERIFICATION.md).
