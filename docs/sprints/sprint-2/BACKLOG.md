# Sprint 2 backlog and Jira mapping

Baseline: **12 November 2026**. Scope authority: [Sprint goal](SPRINT_GOAL.md).
The user confirmed that indicator credibility first is a group discussion
decision. The meeting date, attendance and detailed minutes have not been
supplied. The ordering below records that confirmed priority. The user has
authorized implementation according to the goal; formal team/PO review and
acceptance of the increment remain separate.

The planning batch established records and an AI rehearsal against the existing
synthetic dashboard. The user then authorized Sprint 2 development according to
the goal. The implementation batch adds metric traceability, evidence export and
scenario support; final technical verification is recorded separately below.
Existing Sprint 1 behavior remains baseline evidence. No Sprint 2 Jira transfer,
estimates, assignees, Sprint dates or teacher/Product Owner acceptance are
established here.

## Prioritized stories

Complete and review the indicator evidence gate before evaluating actual human
comprehension. P1 means the first planning priority; P2 follows that gate.

| Local ID | Summary | Priority / order | Dependencies | Current local state | Jira key / status |
| --- | --- | --- | --- | --- | --- |
| S2-US-01 | Establish a traceable indicator contract | P1 / 1 | Sprint 1 schema and reporting rules | Model/UI traceability and export implemented; technical checks passed; team rule review pending | Not transferred / unknown |
| S2-US-02 | Independently verify indicator calculations and edge cases | P1 / 2 | S2-US-01 | 17/17 model tests, 11/11 comparisons, build and scoped browser checks passed; human acceptance pending | Not transferred / unknown |
| S2-US-03 | Evaluate comprehension across three stakeholder roles | P2 / 3 | S2-US-01 and S2-US-02 metric gate | Three-role AI browser walkthrough, scenarios and response sheet prepared; human results pending | Not transferred / unknown |
| S2-US-04 | Correct evidence-supported usability problems | P2 / 4, conditional | Findings from S2-US-02 or S2-US-03 | Source-observed traceability gaps corrected; desktop/mobile checks passed; human effect unmeasured | Not transferred / unknown |
| S2-US-05 | Verify process improvements carried from Sprint 1 | P2 / 5; records maintained throughout | Actual team decisions on carry-over actions | Build records maintained; human retrospective outcomes pending | Not transferred / unknown |

Estimates and ownership are left for actual team planning. S2-US-05 record
maintenance runs throughout the Sprint; its final review follows the product
and experiment evidence.

### S2-US-01: Traceable indicator contract

As a dashboard user, I want every indicator to expose its inputs, rule and
limits so that I can justify my interpretation.

Acceptance criteria:

1. Record coverage numerator, denominator, segment unit, source fields and
   one-decimal display rounding. Unknown segments remain in the total; zero
   records produce unavailable coverage.
2. Record observation time, snapshot time and reporting clock separately,
   including historical/current modes and the exactly-24-hour boundary.
3. Record classification and overall-status precedence, including overlapping
   suspected-downgrade and missing/stale evidence. Suspicion must not suppress
   the availability of data-quality explanations.
4. Trace each conclusion to identifiable connection records and a reporting
   rule. Filters must not silently change the global coverage denominator.
5. Explain segment versus complete-path protection, expected versus suspected
   fallback, synthetic HNDL assumptions and the limits of migration indicators.
6. Retain actual team questions and decisions on the contract, including any
   unresolved disagreement; technical checks alone do not approve the rules.

Planned evidence: contract in [SPRINT_GOAL.md](SPRINT_GOAL.md), source/field
references and worked examples in [VERIFICATION.md](VERIFICATION.md), and actual
rule-review decisions in [TEAM_REVIEW.md](TEAM_REVIEW.md).

### S2-US-02: Independent indicator evidence

As the verification reviewer, I want expected results stated independently of
the implementation so that a consistent calculation error can be detected.

Acceptance criteria:

1. Preserve the tested revision, inputs, selected reporting clock, expectations,
   observed results and evidence locations.
2. Reconcile default counts and coverage: 8 segments = 5 PQC + 2 fallback + 1
   unknown; 5/8 = 62.5%. Check filtered rows against the unchanged global totals.
3. Exercise empty, unknown-only, stale all-PQC, exact freshness boundary,
   future-dated evidence and invalid input. Invalid input must remain distinct
   from a valid empty snapshot.
4. Exercise mixed device paths and expected/suspected fallback. A result must
   not imply end-to-end PQC or a confirmed attack from those labels alone.
5. Record discrepancies and residual gaps. Source/model checks establish only
   their observed scope; changed presentation behavior requires fresh browser
   checks and the metric contract requires human review.

Evidence authority: [VERIFICATION.md](VERIFICATION.md). Existing Sprint 1 tests
and newly executed model scenarios must be dated separately from historical UI
evidence. Resolve material discrepancies before passing the metric gate.

### S2-US-03: Three-role comprehension evaluation

As the team, we want to observe how users interpret the indicators so that
changes address actual misunderstandings.

Acceptance criteria:

1. Follow [USER_UNDERSTANDING_EXPERIMENT.md](USER_UNDERSTANDING_EXPERIMENT.md)
   after the metric gate. Record actual participant IDs, roles, session date,
   dashboard revision, task order and consent to recording responses.
2. Cover Sarah's investigation decision, Michael's migration interpretation and
   Emma's executive action, including denominator, stale-data, mixed-path and
   fallback questions. Keep first responses before showing expected answers.
3. Preserve responses, evidence locations, incorrect interpretations and
   confidence/assistance observations under the protocol's scoring rules.
4. Record actual group discussion results and decisions separately from the
   user-confirmed priority. The Group discussion draft contains proposed
   questions and conclusions for review; it supplies no participant responses.
   Keep the AI technical rehearsal separate from human success rates.
5. Report denominators, limitations and unresolved misunderstandings. Participant
   agreement does not establish cryptographic assurance or PO acceptance.

Current boundary: the AI rehearsal, human protocol and development scenario
support prepare the experiment; no real participant comprehension result is
established.

### S2-US-04: Evidence-supported usability corrections

As a stakeholder, I want explanations and controls corrected when evidence
shows they cause a material misunderstanding.

Acceptance criteria:

1. Link every proposed correction to a reproducible defect or an actual study
   observation, and record priority, rationale and scope.
2. Record before/after examples; maintain the shared metric contract and explicit
   uncertainty when changing placement, wording or interaction.
3. Verify affected model behavior and browser workflows, including relevant
   narrow-screen and keyboard use, and repeat the affected comprehension task.
4. If evidence supports no change, record that outcome and its limits. Proposed
   discussion conclusions alone do not establish improved human comprehension.

Evidence: [VERIFICATION.md](VERIFICATION.md) and experiment findings. The
implementation batch addresses source-observed evidence visibility and
traceability gaps; final UI checks and actual comprehension evaluation remain
separate.

### S2-US-05: Follow-through on process improvements

As the team, we want to check whether agreed Sprint 1 improvements were carried
out and helped Sprint 2.

Acceptance criteria:

1. Discuss the four Sprint 1 proposed retrospective actions; record each
   accepted, revised, rejected or deferred decision with a reason.
2. Give accepted actions actual owners, target dates, completion criteria and
   verified Jira keys when entered; do not infer ownership from the roster.
3. Review outcome evidence during Sprint 2, distinguishing an action performed
   from evidence that it improved the process.
4. Keep meeting participation, AI contributions, team review and PO acceptance
   attributable to their actual sources.

Evidence: [RETROSPECTIVE_ACTIONS.md](RETROSPECTIVE_ACTIONS.md),
[TEAM_REVIEW.md](TEAM_REVIEW.md) and [LLM_EVALUATION.md](LLM_EVALUATION.md).

## Process tasks accompanying the stories

| Local task | Work | Completion evidence | Jira mapping |
| --- | --- | --- | --- |
| S2-T-01 | Confirm detailed scope, estimates, roles and Sprint dates | Actual planning decisions and assignment acknowledgements | Not transferred |
| S2-T-02 | Maintain risk and decision records | Dated authority, alternatives, mitigation evidence and residual risks | Not transferred |
| S2-T-03 | Evaluate significant LLM outputs | Provenance, review findings, corrections and verification boundaries | Not transferred |
| S2-T-04 | Record review and retrospective follow-through | Actual discussion outcomes, accepted actions and team/PO decisions | Not transferred |
| S2-T-05 | Confirm Sprint 2 submission requirements | Course/PO requirements and checked deliverables when supplied | Not transferred |

## Definition of Done and ongoing maintenance

A story needs evidence for all its accepted criteria, review of generated work,
appropriate technical checks and browser evidence for changed UI behavior.
Human comprehension claims require actual participant data. Maintain README
and project instructions with scope/startup changes; record remaining risks
and team/PO decisions explicitly.

Local records do not establish Jira history. Add real Sprint 2 issue keys and
verified resulting statuses only after transfer, preserving these local IDs.
No story is marked Done or human-accepted by these records alone. The
user-confirmed group priority does not establish acceptance of detailed stories,
the Group discussion draft or the increment.

## Implementation batch record

| Date / event | Authorized scope and evidence | State |
| --- | --- | --- |
| 2026-11-12 / development authorization | User requested Sprint 2 development according to SPRINT_GOAL.md | Credibility-first implementation authorized; no Jira or human acceptance inferred |
| 2026-11-12 / metric traceability and experiment support | Model evidence IDs/reasons, reporting clocks, connection context, JSON evidence export and scenario assets | Implemented; 17/17 model tests, 11/11 comparisons, production build and scoped browser checks passed; technical evidence in VERIFICATION.md |

Observed technical evidence supplied by the integrating agent: the browser
export reconciled 5/8 coverage, eight source records, exact reporting clock and
numerator IDs. Desktop and 390 × 844 mobile checks exercised local scenario
loading, empty/unknown/expected fallback/mixed-path/stale-PQC states, invalid
data rejection, reset recovery and all three role views. Screenshots and the
downloaded JSON are retained under `evidence/`. These observations establish
technical readiness for team review, not human comprehension or PO acceptance.

The full observation boundaries and commands are recorded in VERIFICATION.md.
