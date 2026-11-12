# Sprint 2 goal and delivery record

## Sprint goal

Deliver a working synthetic-data customer reporting increment that enables
Emma to explain the key customer's current HNDL exposure by data class, the
customer-related connections still requiring PQC key establishment by
**31 December 2027**, and the decisions needed to close the gap without hiding
uncertainty or service-continuity risks. Demonstrate a first customer report
structure at the next Sprint review, and document how the changed priorities
reshape the backlog, stakeholder trade-offs and the team's work.

This is the scope authority for the next development stage. Indicator
credibility supports this customer outcome. The previous credibility-first
goal is superseded; its implemented features remain reusable foundations.

## Current delivery state — 12 November 2026

The customer model, synthetic fixture, populated report, deadline gap and three
role workflows are implemented. Technical checks passed: 39/39 model tests
(17 legacy + 22 customer), 11/11 legacy scenario comparisons, production build
and scoped desktop/390px browser checks, including actual report downloads.
Default customer quantities reconcile to 6 = 2 exposed + 2 unresolved + 2
reported PQC; nine required segments include missing evidence and a 2028
replacement conflict. [VERIFICATION.md](VERIFICATION.md) records the evidence
and limitations; [BACKLOG.md](BACKLOG.md) separates technical state from acceptance.

Next work is actual team rule/role/estimate confirmation, Jira updates, customer
report demonstration with PO feedback, group-dynamics/retrospective observations
and course submission artifacts. These have no completion claim from the build.
R1-R4/R6 have technical evidence; R5/R7 have prepared local records and require
actual process evidence; R8 and formal team/PO acceptance remain pending.

## Authority, sources and dates

Corrected on **12 November 2026**, following the user's instruction to align
GOAL and backlog with the actual course requirements. This authorizes the
planning correction; formal teacher/Product Owner acceptance, team estimates,
assignment acknowledgement and Jira updates remain separate.

Authoritative supplied course sources:

- `PQC_Scrum_Project_Sprint2_pdf.pdf`, pp. 3-5: customer-first priority; revised
  deadline; HNDL by data class; initial report for the next review; keep/change/drop
  decisions; persona and group-dynamics impact.
- `Human_factors_persona_cards.pdf`, pp. 1-2: Sarah's exposure/investigation needs,
  Michael's 2028 replacement constraint and Emma's budget/continuity concerns.
- `Human_factors_project_instructions.pdf`, pp. 1-3: synthetic LLM-generated
  dashboard, evaluated LLM output, Scrum/Jira, reports and submission schedule.

Local source folder:
`D:\Code\SE\UniOulu\Professional Software Engineering Processes and Human Factors\Group Project`.
Business requirements come from these sources. The data contract below is an
implementation choice to make them measurable, not a teacher-specified schema.

| Date / milestone | Meaning |
| --- | --- |
| Next Sprint review, actual date to be recorded | Demonstrate the initial report structure and working increment; seek PO feedback |
| 18 November 2026, 23:59 Finnish time | Sprint 2 course submission deadline |
| 31 December 2027 | Proposed customer requirement: all connections carrying customer data use PQC key establishment; previously end of 2030 |
| 2028 certified replacements | Existing scenario constraint; where it affects customer data, it conflicts with the new target |

The Sprint delivers reporting and a response to change, not a claim that
production migration has occurred. Actual agreement to modified contract terms
is not inferred from the proposed customer requirement.

## Starting state and requirement coverage

Baseline: `e371940`. Traceability, clocks, JSON evidence export and path-context
explanations have technical evidence (17 model tests, 11 comparisons and scoped
browser checks) for the previous scope. Customer attribution, class aggregation,
deadline-gap analysis and a customer report are **not implemented at this baseline**.

| Requirement | Required outcome | Backlog / acceptance evidence |
| --- | --- | --- |
| R1: Customer-first scope | Identify the key customer and all reported data/required connections; expose missing attribution and unrelated data | S2-US-06/08; scoped fixture and visible report scope |
| R2: HNDL by data class | Quantify customer data with potential exposure, reported PQC and unresolved evidence; explain confidentiality assumptions | S2-US-06 and extended S2-US-01/02; reconciled class table and drill-down |
| R3: New deadline | Show 2027-12-31 for all customer connections, remaining gaps and the 2028 replacement conflict | S2-US-07; gap list and proposed actions |
| R4: Initial report | Demonstrate an understandable report structure at the next review from shared calculations | S2-US-08; rendered report, evidence bundle and review record |
| R5: Scrum change response | Record keep/change/drop rationale; update estimates, priorities and real Jira items | S2-T-01/06; decisions and verified Jira state |
| R6: Persona impact | Support Sarah, Michael and Emma's changed decisions and explicit continuity/deadline trade-off | S2-US-09; role tasks and scenario walkthrough |
| R7: Human factors and learning | Reflect actual group interaction and change response; maintain risks, retrospective follow-up and LLM evaluation | S2-US-05 and S2-T-02/03/04/06; attributable observations and decisions |
| R8: Submission | Approximately 500-word report, five-minute video and PDF of slides used; show Jira/dashboard evolution | S2-T-05; checked files and actual submission evidence |

All R1-R8 need evidence. Technical implementation, human process evidence and
PO decisions have separate completion states in [BACKLOG.md](BACKLOG.md).

## Data and metric contract for implementation

### Customer scope and counting unit

Use one named synthetic key customer for the first increment. Represent stable
customer IDs, logical data-item IDs, data classes, observation times,
confidentiality-lifetime assumptions, and the required connection-segment IDs
for each item. Record whether expected path mapping is complete. One item may
traverse several segments, and a segment may carry several items.

For this increment, **amount of data means distinct logical data-item counts
and proportions**, per customer and class. Define an item as a declared
scenario record representing a data stream or information asset, not a packet,
byte total or connection. Label this unit beside quantities. The course does
not prescribe the unit; this explicit modeling choice requires review.
Byte/traffic quantities are deferred until amounts, units and windows exist.

Each item has one primary class so class totals reconcile. Include short-lived
operational telemetry, long-lived configuration or maintenance information,
and an unknown-class case. Deduplicate by customer and data-item ID across
route segments. Retain missing classification as **Unknown class**. Show missing
customer attribution separately as unresolved scope; it prevents claims of a
complete customer inventory. Reject contradictory identifiers and malformed
mappings; never silently assign global records to the key customer.

### Exposure and evidence quality

Use three mutually exclusive categories for each in-scope item:

1. **Potential HNDL exposure:** any required segment is known to use classical
   key establishment. Preserve concurrent missing/stale/unknown evidence flags.
2. **Unresolved:** no known classical segment establishes category 1, but required
   mapping is incomplete or evidence is missing, unknown, stale or future-dated.
3. **Reported PQC:** all required segments are mapped and report PQC key
   establishment with usable evidence under the selected reporting clock.

Each class shows total, three category counts/proportions, confidentiality
assumptions and quality flags. Categories sum to the class total; quality flags
may overlap and are not additional category totals. Empty scope has unavailable
percentages. Unresolved in-scope items remain in the denominator. Filters must
state their scope; inventory filters cannot silently change customer totals.

Exposure describes potential future decryption under scenario assumptions,
not proof of harvesting or an attack. Short-lived telemetry is not automatically
zero-risk and is not exempt from the customer's deadline. Preserve expected
fallback versus suspected downgrade and per-observation freshness (older than
24 hours is stale; exactly 24 hours is current). High migration percentages
cannot conceal unresolved scope or unavailable evidence.

Keep **connection-segment coverage** separate from **customer data-item
exposure**. The old 5/8 = 62.5% cannot be reused as customer data coverage, and
its complement is not customer HNDL exposure. Version the new rules and trace
results to customer, class, item and segment IDs.

### Deadline-gap contract

Evaluate every distinct connection carrying customer data against 2027-12-31.
Show classical connections, unknown/unverified status, incomplete paths, planned
migration date if known, replacement blocker, business consequence and proposed
action. Missing plans are unresolved; a plan is not completed migration.
Stale/future/partial evidence cannot establish current compliance.

Flag relevant 2028 replacements as incompatible with the 2027 target. Present
options for investigation (earlier replacement, validated alternative or
escalation/contract discussion), their constraints and required decision.
Do not invent feasibility, funding, accepted exceptions or negotiated dates.
A local fallback approval does not waive the proposed customer requirement,
even for short-lived data. Keep reported migration separate from schedule risk.

## Customer report v1 and persona outcomes

The default entry or an unmistakable primary action must lead Emma to the
customer report. The runnable report contains:

1. Customer, synthetic scope/completeness, snapshot/reporting time, 2027 deadline
   and a plain-language status with its reasons.
2. Data-class HNDL table with the declared item-count unit, reconciled categories,
   confidentiality assumptions and unresolved information.
3. Remaining customer connections and plans, explicit 2028/2027 conflict,
   continuity consequences and proposed next decisions.
4. Up to three prioritized business risks/actions; owner and target where
   actually assigned, otherwise visibly unassigned/unknown.
5. Methodology and evidence: definitions, rule version, assumptions, limitations,
   input records and evaluation time.

Extend/reuse export to retain customer/class/item/segment associations and the
same calculations and clock. Existing generic JSON export alone does not
satisfy report v1. A bespoke customer-PDF exporter is not mandated by the brief;
prioritize a demonstrable report structure.

| Persona | Observable decision supported |
| --- | --- |
| Sarah | Identify exposed customer data classes and inspect the classical segment, lifetime assumption or suspected downgrade behind the result |
| Michael | Identify customer migration blockers, explain the 2028/2027 conflict and propose a next decision without claiming an approved solution |
| Emma | Explain current customer position, unresolved scope and top risks, and identify budget/continuity/deadline decisions to escalate |

Update role explanations and review tasks to this scenario. The prepared
understanding protocol supports validation; the course does not separately
mandate an external-user study. Preserve actual team walkthrough feedback and
assistance before claiming improved comprehension.

## Keep, change and drop/defer

| Decision | Scope and rationale |
| --- | --- |
| Keep | Vue, independent synthetic operation, shared rules, validation, clocks, traceability, evidence export and useful tests/browser checks |
| Change | Goal/navigation, dataset, metrics, report, role tasks, risks and tests to reflect customer scope, data classes, 2027 deadline and 2028 conflict |
| Change | Customer reporting and change response precede more generic metric polish or an extended comprehension experiment |
| Drop from active plan | All-system segment coverage as the customer-exposure answer; generic evidence export as completion of the customer report |
| Defer | Optional redesign, complex scoring, unsupported byte-volume estimates, automatic customer-PDF generation and expanded usability research |
| Outside scope | Live ingestion, databases, authentication, automatic blocking and protocol/cryptographic redesign; preserve the separate communication prototype |

These are the user-authorized planning baseline. Record actual team/PO feedback
and changes in Jira and the decision log; this document establishes no meeting
attendance or consensus on detailed implementation rules.

## Execution sequence and completion gates

1. **Re-plan:** map R1-R8 to stories; record keep/change/drop and persona/group
   implications against the product vision and stakeholder analysis. Record
   actual estimates, dates, Scrum roles and Scrum Master rotation; enter/verify
   Jira stories and dependencies. Record unanswered PO questions explicitly.
2. **Data and rules:** implement S2-US-06 and extend S2-US-01/02. Independently
   work expected class totals and item paths. Gate: reconciliation, scope and
   uncertainty cases pass before report calculations are accepted.
3. **Report and decisions:** implement S2-US-07/08/09 from the shared rules.
   Gate: Emma can inspect the report and 2027/2028 gap; displayed/exported
   results and source records reconcile at the same reporting time.
4. **Verify:** test unrelated customer data, duplicate/multiple route segments,
   shared segments, multiple/unknown classes, missing attribution, incomplete
   paths, short/long lifetimes, expected/suspected fallback, stale/future/empty/
   invalid data and on/before/after-deadline plans. Recheck legacy import/reset
   or supply explicit schema migration/errors. Walk actual report/role flows
   in desktop/narrow layouts and check relevant keyboard controls. Old tests
   alone do not pass this gate.
5. **Review and reflect:** demonstrate report v1, record actual feedback and PO
   decisions, evaluate generated outputs, reassess risks and retrospective
   actions. Create or verify Jira actions with next-Sprint follow-up. Reflect
   actual changes in workload, disagreement, communication and
   emotional reactions, including no change if that is what members report.
6. **Submit:** check the approximately 500-word report, five-minute video and
   PDF of slides actually used. Cover goal/outcome, planned/completed work,
   Jira/dashboard evolution, product vision, stakeholders, decisions, changed
   risks, customer-change response,
   human factors, LLM evaluation and retrospective follow-up. Record actual
   submission separately from file readiness.

Definition of Done: product stories demonstrate R1-R4/R6 through verified data,
tests and browser evidence; process tasks supply R5/R7/R8 with actual Jira,
meeting, evaluation and artifact evidence. Keep unresolved business decisions
and scope uncertainty explicit. Record team/PO acceptance only when received.
Owners, estimates, Jira keys and review outcomes remain to be confirmed; the
product contract above is concrete enough for the next implementation stage.

## Supporting records and current status

Use [BACKLOG.md](BACKLOG.md) for ordered stories/dependencies;
[RISK_AND_DECISION_LOG.md](RISK_AND_DECISION_LOG.md) for change decisions;
[LLM_EVALUATION.md](LLM_EVALUATION.md) for generated-output evaluation;
[TEAM_REVIEW.md](TEAM_REVIEW.md) and
[RETROSPECTIVE_ACTIONS.md](RETROSPECTIVE_ACTIONS.md) for human evidence;
[VERIFICATION.md](VERIFICATION.md) for dated checks. Earlier experiment, review
and verification entries remain historical and need extension to this customer
scenario. They do not establish new-requirement coverage.

Preserve existing local story IDs and past evidence. New customer stories use
S2-US-06 through S2-US-09. Extend existing traceability/verification stories;
do not relabel prior work as new completion. During construction maintain the
backlog, risks, LLM and retrospective records through bounded delegated work
with exclusive ownership, integrate evidence, and update README/instructions.
Repository documentation is English.

| Date / event | Authority and resulting state |
| --- | --- |
| 2026-11-12 / earlier goal and development | Credibility work produced e371940; technical evidence retained as foundation; human acceptance pending |
| 2026-11-12 / course-source audit | Sprint 2 PDF revealed missing customer/class/deadline/change-response requirements; previous checks do not satisfy them |
| 2026-11-12 / correction | User requested comprehensive next-stage GOAL/backlog; R1-R8 and acceptance contract defined; customer features and formal process/submission evidence pending |
| 2026-11-12 / customer increment | User authorized build and GitHub push; R1-R4/R6 technically implemented and checked; actual process/submission and team/PO acceptance remain pending |
