# Sprint 2 backlog and Jira mapping

Corrected baseline: **12 November 2026**. Scope authority:
[Sprint goal](SPRINT_GOAL.md), including its course-source references, data
contract and requirements R1-R8. The key customer's report now drives delivery
order; indicator credibility remains essential to make that report defensible.

Revision `e371940` provides generic indicator traceability, reporting clocks,
connection context, scenario support and JSON evidence export. Its recorded
technical checks cover that foundation only. Customer identification, data-class
HNDL quantities, the 2027 gap and the first customer report are **not implemented**
by that revision. Existing story IDs retain links to historical evidence.

**Group endorsement confirmed on 13 November 2026:** the user reports approval
of the review conclusions, customer-first scope, current metric interpretation
and keep/change/drop rationale. Earlier pending group-review statements are
superseded for these conclusions; teacher/PO approval remains separate. See
[TEAM_REVIEW.md](TEAM_REVIEW.md) for the dated confirmation.

Sprint 2 Jira transfer was completed and checked on **13 November 2026**:
15 items in SCRUM Sprint 2 (ID 3), 8 In Review / 4 In Progress / 3 To Do, with
ten directed dependency links. Actual keys and statuses are recorded below;
see [JIRA_UPLOAD.md](JIRA_UPLOAD.md) for the verified mapping and evidence.
Estimates, assignment acknowledgements, formal Sprint dates and teacher/Product
Owner acceptance remain pending. The course deadline
is **18 November 2026, 23:59 Finnish time**, separate from the customer's
**31 December 2027** PQC target.

## Customer build batch — 12 November 2026

The user authorized implementation of the corrected GOAL and a GitHub push
once verified. Customer model, fixture, report and role integration are
implemented and technically checked in this batch: 39/39 tests (17 legacy + 22 customer), a
44-module production build, 11/11 legacy scenario comparisons and scoped
desktop/mobile/keyboard/import/export/role browser checks passed. The final
production preview loaded the built asset, retained 2/2/2 totals and had empty
scoped error logs; the 390px layout had no page horizontal overflow. The actual
pushed revision and final delivery evidence belong in
[VERIFICATION.md](VERIFICATION.md).
That build did not establish Jira activity or acceptance. The dated Jira
transfer above and the group confirmation are later events; teacher/PO
acceptance, actual session results and course submission remain separate.

## Prioritized stories

Start the S2-US-08 report outline alongside scope definition. Populating and
accepting it requires the customer-data and deadline work. Verification runs
with each increment. P1 covers required product outcomes; P2 covers supporting
evaluation and conditional improvements.

| Local ID | Summary | Priority / order | Dependencies | Current local state | Jira key / status |
| --- | --- | --- | --- | --- | --- |
| S2-US-06 | Define key-customer scope and quantify HNDL exposure by class | P1 / 1 | Customer contract and synthetic fixtures | Implemented; technical checks passed; group review conclusions confirmed 2026-11-13; PO acceptance pending | [SCRUM-15](https://tacczy.atlassian.net/browse/SCRUM-15) / In Review |
| S2-US-01 | Extend the traceable indicator contract to customer reporting | P1 / 1, alongside US-06 | Existing foundation; rules agreed before acceptance | Customer extension implemented; technical checks passed; group rule conclusions confirmed 2026-11-13; PO acceptance pending | [SCRUM-16](https://tacczy.atlassian.net/browse/SCRUM-16) / In Review |
| S2-US-07 | Show the 2027 migration gap and 2028 replacement conflict | P1 / 2 | US-06 scope and US-01 rules | Implemented; technical checks passed; group review conclusions confirmed 2026-11-13; PO acceptance pending | [SCRUM-17](https://tacczy.atlassian.net/browse/SCRUM-17) / In Review |
| S2-US-08 | Deliver first customer report structure and populated review example | P1 / outline starts immediately; populated report 3 | US-06, US-07 and US-02 checks | Implemented; technical checks passed; group review conclusions confirmed 2026-11-13; PO acceptance pending | [SCRUM-18](https://tacczy.atlassian.net/browse/SCRUM-18) / In Review |
| S2-US-09 | Update stakeholder views for changed customer decisions | P1 / 3, alongside report | US-06 and US-07 | Implemented; technical checks passed; group review conclusions confirmed 2026-11-13; PO acceptance pending | [SCRUM-19](https://tacczy.atlassian.net/browse/SCRUM-19) / In Review |
| S2-US-02 | Independently verify quantities, deadline and report | P1 / each increment; final gate 4 | Agreed contract and changed features | 39/39 tests; build/scenarios/browser checks passed; group evidence conclusions confirmed; PO acceptance pending | [SCRUM-20](https://tacczy.atlassian.net/browse/SCRUM-20) / In Review |
| S2-US-03 | Evaluate comprehension across stakeholder roles | P2 / after verified report | Relevant US-02 checks | Protocol and AI rehearsal prepared; human results pending | [SCRUM-21](https://tacczy.atlassian.net/browse/SCRUM-21) / To Do |
| S2-US-04 | Correct evidence-supported usability problems | P2 / conditional | Reproducible defects or actual review findings | Mobile report overflow corrected and checked; human effect unmeasured | [SCRUM-22](https://tacczy.atlassian.net/browse/SCRUM-22) / In Review |
| S2-US-05 | Verify process improvements carried from Sprint 1 | Throughout; close at retrospective | Actual team decisions and outcomes | Review conclusions and follow-up direction confirmed by group; execution and observed retrospective outcomes pending | [SCRUM-23](https://tacczy.atlassian.net/browse/SCRUM-23) / In Progress |

### S2-US-06: Customer scope and HNDL quantities by class

As Emma, I want the key customer's potential HNDL exposure by data class so
that I can explain its current position and prioritize action.

Acceptance criteria:

1. Name a synthetic key customer and represent `customerId`, `dataItemId`,
   `dataClass`, confidentiality assumptions, observation times and each item's
   mapping to **all required connection segments**, with an explicit mapping
   completeness indicator. Identify shared segments and customer ownership.
2. Use **distinct logical data items** as the quantity unit: one item counts once
   per customer/class even when routes repeat or cross several segments. Show
   counts and proportions with denominators. Segment counts, segment PQC share
   and bytes must not be presented as quantities of customer data.
3. Assign each item to exactly one bucket in this order: potential HNDL exposure
   when any required known segment uses classical key establishment; otherwise
   unresolved when mapping/evidence is missing, unknown, incomplete, stale or
   future-dated; otherwise reported PQC when the complete required path has
   valid, current PQC evidence. Preserve concurrent uncertainty flags even when
   known classical exposure takes precedence.
4. Reconcile bucket counts to every class total and the customer's total. Keep
   absent classification visible as `Unknown class`; reject or surface
   inconsistent/invalid records. Uncertain customer ownership must remain a
   visible scope-completeness limitation; do not silently exclude it and claim
   the selected customer's inventory is complete.
5. Show per-class confidentiality assumptions and limits. Short lifetime does
   not imply zero HNDL risk. Reported PQC is an evidence-based classification,
   not proof of future security, an attack observation or attack probability.
6. Provide reproducible synthetic fixtures covering several classes, repeated
   routes/items, shared segments, unknown class/ownership and uncertain evidence;
   retain fixture provenance and the reporting clock.

Evidence: contract in [SPRINT_GOAL.md](SPRINT_GOAL.md), fixtures and independent
worked expectations in [VERIFICATION.md](VERIFICATION.md), and reconciled
customer/class views. Covers R1-R2.

### S2-US-01: Traceable indicator contract, extended

As a dashboard user, I want each conclusion to expose its inputs, rule and
limits so that I can justify my interpretation of the customer report.

Acceptance criteria:

1. Retain existing segment coverage, source traceability, rounding and explicit
   unknowns. Label segment PQC share separately from logical-item HNDL
   quantities and class/customer denominators.
2. Document customer scope, quantity unit, deduplication, path completeness,
   bucket precedence and concurrent uncertainty from US-06. Provide independently
   calculable examples and state inventory-completeness limitations.
3. Expose report as-of clock, snapshot/observation times, freshness threshold and
   boundary rules. Missing or future-dated evidence cannot become current
   protection merely because a status says PQC.
4. Trace class totals, unresolved items and deadline gaps to item and segment
   IDs. Show changed denominators when filtering; distinguish filtered subtotals
   from whole-customer totals.
5. Explain expected versus suspected fallback without implying a confirmed
   attack. Approved fallback and short-life telemetry remain in the 2027 target
   when carrying customer data. Show quality reasons alongside exposure.
6. Record actual team rule-review questions and decisions. Technical checks
   alone do not establish comprehension or Product Owner acceptance.

State: generic traceability/export implemented at `e371940`; customer extension
implemented and technically checked; group rule conclusions confirmed on 2026-11-13; PO acceptance pending. Evidence: [VERIFICATION.md](VERIFICATION.md) and
[TEAM_REVIEW.md](TEAM_REVIEW.md). Supports R1-R4.

### S2-US-07: 2027 target and 2028 conflict

As Emma and Michael, we want customer-data connections that cannot yet meet
the revised target identified so that we can discuss a feasible response.

Acceptance criteria:

1. State **all connections carrying customer data use PQC key establishment by
   31 December 2027**, replacing end-of-2030. Derive scope from all required
   customer-data segments, including approved fallback and short-life telemetry.
2. Distinguish reported current PQC, known classical gaps and unresolved readiness
   or evidence. Unknown/incomplete scope cannot be reported as fully compliant.
   Keep connection quantities separate from logical-item quantities.
3. Show the 2028 certified-replacement constraint as an explicit conflict wherever
   affected segments carry customer data. Do not silently move either date or
   exempt affected connections.
4. For gaps and unresolved dependencies, show affected segments/classes, reason,
   proposed action or decision, dependencies, owner and target date. Mark
   unagreed actions/owners/dates pending; do not imply approval of options.
5. Explain budget/continuity implications and Michael's operational constraints.
   Deliver a working synthetic planning/reporting view; this 2026 Sprint does
   not require a real production migration by 2027.
6. Show planned migration dates separately from reported current status. Missing
   dates remain unresolved; a plan is not completion. Classify plans before, on
   and after the deadline consistently, retaining schedule risk and missing
   evidence even where reported PQC status is present.

Evidence: working gap view and decision register in
[RISK_AND_DECISION_LOG.md](RISK_AND_DECISION_LOG.md). Covers R3; supports R4/R6.

### S2-US-08: First customer report

As Emma, I want an initial report at the next review so that the customer's
current position and required decisions can be discussed together.

Acceptance criteria:

1. Prepare the outline immediately and populate a reproducible first version
   from the verified dashboard for the next Sprint review. Record its actual
   agreed date. An outline alone is not a working populated report.
2. Include named customer/scope, synthetic-data context, as-of clock, class/item
   totals and exposure buckets, quantity method/denominators, unknowns, scope
   limitations and per-class confidentiality assumptions.
3. Include the 2027 target, connection gap, explicit 2028 conflict and proposed
   actions/decisions, with unagreed owners and targets pending. Link material
   conclusions to underlying item/segment evidence.
4. Reconcile report quantities, clocks and qualifications with the dashboard.
   Clearly distinguish known exposure, unresolved evidence and reported PQC.
5. Demonstrate the structure and populated example in the working dashboard;
   retain actual feedback and resulting decisions. A separate customer PDF
   export is optional, not a stated course requirement.
6. Make the report the default entry or an unmistakable primary action. Include
   up to three prioritized business risks/actions with actual owners/targets or
   explicit unassigned/unknown values.
7. Extend the evidence export with customer/class/item/segment associations,
   versioned rules and the same reporting clock and calculations. Generic
   evidence JSON alone does not complete the customer report.

Evidence: working report, reproducible example/screenshots and
[TEAM_REVIEW.md](TEAM_REVIEW.md). Covers R1/R4; supports R2-R3.

### S2-US-09: Changed stakeholder decisions

As Sarah, Michael and Emma, we want role-appropriate evidence for the key
customer so that we can act on the revised priorities.

Acceptance criteria:

1. Sarah can inspect exposed classes/items, required segments and simultaneous
   uncertainty, distinguishing approved fallback from suspected downgrade
   without a claim that an attack occurred.
2. Michael can inspect customer paths, fallback, migration dependencies,
   continuity constraints and the 2027/2028 conflict.
3. Emma can obtain the initial report, explain class exposure/deadline gaps and
   identify decisions with budget and continuity consequences.
4. All views use the same customer scope, clock and calculation rules. Preserve
   useful existing context while prioritizing the changed customer outcome.
5. Verify changed desktop/narrow-screen and keyboard workflows; retain actual
   review feedback. Record persona trade-offs through S2-T-06.

Evidence: persona-to-feature mapping, browser checks and review. Covers R6;
supports R1-R4.

### S2-US-02: Independent evidence, extended

As the verification reviewer, I want independent expected results so that a
consistent calculation error can be detected.

Acceptance criteria:

1. Preserve tested revision, fixtures, clock, expectations, observations and
   evidence locations. The existing 17 model tests and 11 comparisons remain
   dated foundation evidence, not verification of new customer features.
2. Verify isolation, shared segments, duplicate/repeated routes and items,
   multiple classes, unknown class and uncertain customer ownership. Reconcile
   class/customer totals and filtered denominators; check separate segment share.
3. Verify all buckets, including known classical plus uncertainty, incomplete
   mapping, unknown segments, stale all-PQC, future evidence and exact freshness
   boundary. Distinguish valid empty scope, missing scope and invalid input.
4. Verify all-required-segment interpretation and no lifetime exemptions.
   Telemetry/approved fallback carrying customer data stay in the 2027 scope;
   2028 dependencies remain conflicts.
5. Reconcile report and dashboard at identical scope/clock; check evidence links
   and all three role workflows in the browser. Record residual gaps and resolve
   material calculation/reporting errors before accepting the report.
6. Exercise missing plans and dates before, on and after 2027-12-31. Verify
   customer report/export consistency and legacy import/reset behavior, or
   explicit schema migration/errors, without silently changing customer scope.

Evidence authority: [VERIFICATION.md](VERIFICATION.md). Supports R1-R4/R6.

### S2-US-03: Supporting comprehension evaluation

Acceptance criteria:

1. Adapt [USER_UNDERSTANDING_EXPERIMENT.md](USER_UNDERSTANDING_EXPERIMENT.md)
   to the verified report and changed persona decisions. A formal comprehension
   study is supporting work, not an extra mandatory course deliverable.
2. If sessions occur, record actual participant IDs/roles, date, revision, task
   order and first responses before answers. Cover item/segment quantities,
   uncertainty, required paths and the deadline conflict.
3. Preserve responses/assistance and report denominators/limitations. Keep AI
   rehearsal and proposed discussion material distinct from actual human
   results. Agreement does not establish cryptographic assurance or PO acceptance.
4. If time is constrained, retain an honest pending state and prioritize the
   required customer increment, verification and course review/submission.

### S2-US-04: Evidence-supported usability corrections

Acceptance criteria:

1. Link each correction to a reproducible defect or actual review/session
   observation, with priority, rationale and before/after behavior.
2. Preserve customer scope, shared rules, uncertainty and traceability.
3. Verify affected calculations and browser workflows; repeat the affected task
   if an actual session supplied the finding.
4. Record no-change decisions when justified. Earlier foundation fixes do not
   establish improved customer-report comprehension.

### S2-US-05: Process improvements from Sprint 1

Acceptance criteria:

1. Review the four proposed Sprint 1 retrospective actions; record each actual
   accepted, revised, rejected or deferred decision and reason.
2. Give accepted actions acknowledged owners, targets, completion criteria and
   real Jira keys after entry; do not infer ownership from the roster.
3. Review outcomes, distinguishing action performed from improvement shown.
   Record observed effects of the priority change on coordination, or no impact
   if actual evidence supports that conclusion.
4. Attribute participation, LLM contributions, team review and PO acceptance to
   their actual sources.

Evidence: [RETROSPECTIVE_ACTIONS.md](RETROSPECTIVE_ACTIONS.md),
[TEAM_REVIEW.md](TEAM_REVIEW.md) and [LLM_EVALUATION.md](LLM_EVALUATION.md).
Supports R7.

## Keep, change and defer decisions

The group confirmed this planning direction on 13 November 2026, as reported
by the user. Record subsequent changes in S2-T-06; detailed assignments and
authorized business decisions remain to be supplied.

| Disposition | Work | Corrected direction |
| --- | --- | --- |
| Keep | Traceability, clocks, unknown/stale evidence, scenarios, shared model and JSON export | Reuse as defensible customer-report foundations |
| Change | US-01/US-02 generic indicator contract and verification | Customer/class quantities, complete paths, deadline and report reconciliation |
| Change | Generic persona views and credibility-first order | Customer report first, followed by changed role decisions |
| Defer if necessary | US-03 formal sessions and broad polish | Supporting work after required increment/verification; pending status stays visible |
| Conditional | US-04 corrections | Act on evidence relevant to customer reporting |
| Drop as acceptance evidence | Global segment share as customer exposure; generic JSON export as a finished customer report | Require scoped class quantities and a populated customer report |
| Drop from required scope | Separate customer PDF export and unrelated features | No course requirement makes these mandatory |
| Outside this increment | Real customer data collection and production migration | Functioning synthetic dashboard and actionable report |

## Process tasks accompanying the stories

| Local task | Work | Completion evidence | Jira mapping |
| --- | --- | --- | --- |
| S2-T-01 | Plan corrected scope/order, estimates, roles and dates; record Scrum Master rotation and other actual roles; relate priorities to existing product vision and stakeholder analysis; update Jira with preserved local IDs | Actual decisions, role rotation, acknowledged owners/estimates, vision/stakeholder references, real keys and verified statuses | [SCRUM-24](https://tacczy.atlassian.net/browse/SCRUM-24) / In Progress |
| S2-T-02 | Maintain risks/decisions: assumptions, uncertainty, 2027/2028 conflict, budget and continuity | Dated alternatives, authority, dependencies, mitigation and residual risks | [SCRUM-25](https://tacczy.atlassian.net/browse/SCRUM-25) / In Progress |
| S2-T-03 | Evaluate significant LLM outputs: fixtures, code, report and planning correction | Provenance, actual review findings, corrections and verification limits in LLM_EVALUATION.md | [SCRUM-26](https://tacczy.atlassian.net/browse/SCRUM-26) / In Review |
| S2-T-04 | Review increment and retrospective; check Sprint 1 follow-through; enter agreed improvement actions in Jira for next-Sprint follow-up | Actual discussion/feedback, team/PO decisions, process outcomes, real action keys and next-Sprint follow-up plan | [SCRUM-27](https://tacczy.atlassian.net/browse/SCRUM-27) / To Do |
| S2-T-05 | Assemble/check course submission by 18 November 2026, 23:59 Finnish time; reference product vision and stakeholder analysis in the report | Approximately 500-word report with those references, 5-minute video, PDF of slides actually used, working dashboard, Jira evidence and actual submission record | [SCRUM-28](https://tacczy.atlassian.net/browse/SCRUM-28) / To Do |
| S2-T-06 | Analyze keep/change/drop, persona impacts and group dynamics | Rationale linked to backlog changes; Sarah/Michael/Emma trade-offs; observed coordination impact or evidenced no-impact conclusion | [SCRUM-29](https://tacczy.atlassian.net/browse/SCRUM-29) / In Progress |

The required PDF contains presentation slides actually used; it does not
require customer-report PDF export. Submission content must reflect implemented
scope and actual process evidence, including limitations.

## Definition of Done and delivery checkpoints

1. **Contract and outline:** agree customer scope/classes, item unit, complete-path
   and uncertainty rules; prepare report outline and Jira planning records.
2. **Working increment:** implement customer/class HNDL, deadline/conflict, report
   and role views; pass independent calculations, reconciliation and browser
   checks for changed workflows.
3. **Review/process:** demonstrate the populated initial report; record actual
   feedback/acceptance or pending decisions, keep/change/drop, persona/group
   impact, risks, retrospective and evaluated LLM outputs.
4. **Submission:** check required report, video, slides PDF, dashboard and Jira
   evidence against the course deadline; record actual delivery status.

A story is Done only with evidence for accepted criteria and reviewed generated
work. Verified Jira history is recorded in [JIRA_UPLOAD.md](JIRA_UPLOAD.md);
upload completion does not establish human acceptance. Keep
unresolved owners/dates/decisions pending. Maintain README/project instructions
when scope/startup changes. Prior generic checks cannot complete new stories.

## Requirement coverage

| Requirement | Main stories / tasks | Acceptance evidence |
| --- | --- | --- |
| R1 Customer scope/report priority | US-06, US-08, US-01; T-01 | Selected customer, required scope and report-led delivery |
| R2 HNDL by data class | US-06, US-01, US-02 | Item counts/proportions, reconciliation and uncertainty cases |
| R3 Revised deadline | US-07, US-02; T-02 | All customer-data segments, 2028 conflict and decision/action register |
| R4 Initial report | US-08, US-02; T-04 | Populated working report and actual review feedback |
| R5 Keep/change/drop and Jira | T-01, T-06 | Rationale, acknowledged owners/estimates and actual Jira changes |
| R6 Persona impact | US-09; T-06 | Role workflows and documented trade-offs |
| R7 Group dynamics, retrospective, LLM evaluation | US-05; T-03, T-04, T-06 | Actual observations, reviewed outputs and action outcomes |
| R8 Course submission | T-05 | Required artifacts, functioning dashboard/Jira access and submission record |

Table abbreviations US-xx and T-xx refer to the full S2-US-xx and S2-T-xx IDs.

## Implementation and correction history

| Date / event | Evidence boundary | State |
| --- | --- | --- |
| 2026-11-12 / earlier development, e371940 | Metric evidence IDs/reasons, reporting clocks, connection context, JSON export and scenarios; 17/17 tests, 11/11 comparisons, build and scoped browser checks in VERIFICATION.md | Reusable foundation; human/PO acceptance pending |
| 2026-11-12 / course-PDF audit and planning correction | Earlier goal omitted customer scope, class HNDL, revised deadline, report and change-impact requirements | Goal/backlog corrected; new customer work entered as To Do at that point |
| 2026-11-12 / customer build and integrated checks | Six customer items reconcile as 2 exposed + 2 unresolved + 2 reported PQC; 39/39 tests, build, 11/11 legacy comparisons and scoped browser checks passed; details in VERIFICATION.md | US-01/02/06-09 technically implemented/verified; team rule review and human/PO acceptance pending; process/submission tasks retain pending evidence |
| 2026-11-13 / Jira transfer and final checks | SCRUM-15 through SCRUM-29 in Sprint 2 ID 3; descriptions/source hrefs, actual statuses and ten directed dependencies checked in Jira; mapping in JIRA_UPLOAD.md | 8 In Review, 4 In Progress, 3 To Do; no Done claims; assignments, estimates, dates and teacher/PO acceptance remain separate |

Historical browser/export observations remain in
[VERIFICATION.md](VERIFICATION.md) with their original scope. They do not
establish completion of the corrected Sprint goal.
