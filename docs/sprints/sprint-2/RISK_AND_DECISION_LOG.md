# Sprint 2 risk and decision log

Baseline: **12 November 2026**. Authority: [Sprint goal](SPRINT_GOAL.md).
Current priority: respond to the largest customer's changed reporting and
migration requirements, as defined in the corrected Sprint goal and backlog.
The earlier credibility-first priority below is retained as planning history;
S2-D-10 supersedes it as the Sprint's product priority. Indicator credibility
remains supporting work. Earlier discussion, experiment and retrospective
records must be read against the corrected goal when selecting next work.

The user previously confirmed indicator credibility first as a group discussion decision;
the actual meeting date, attendance and detailed minutes are unspecified.
The group endorsed the review conclusions on 13 November 2026, as reported
by the user; scope, metric interpretation and keep/change/drop direction are
confirmed. Named commitments, human experiment results and PO acceptance
remain open. The planning batch prepared records and AI rehearsal evidence; the user
subsequently authorized development according to the Sprint goal.

## Initial risks

Likelihood and impact are provisional planning judgments. Owner roles are
unassigned proposals. All risks remain open pending the cited review evidence.

| ID | Risk and effect | Likelihood / impact | Mitigation and required evidence | Suggested owner role | Related story |
| --- | --- | --- | --- | --- | --- |
| S2-R-01 | Unknowns or filters change the denominator and inflate reported migration | Medium / High | Trace numerator/denominator to records; independently reconcile global counts and filtered rows | Metric reviewer, unassigned | S2-US-01, S2-US-02 |
| S2-R-02 | Stale or future information supports an apparent all-clear; investigation status hides uncertainty | Medium / High | Verify per-observation time and exact boundary; inspect simultaneous suspicion and poor-evidence explanations | Verification reviewer, unassigned | S2-US-01, S2-US-02 |
| S2-R-03 | Segment migration, fallback or HNDL explanations are interpreted as complete-path safety or confirmed attack | Medium / High | Mixed-path and expected/suspected examples; preserve assumptions; record actual first-response misunderstandings | Domain reviewer, unassigned | S2-US-01 through S2-US-03 |
| S2-R-04 | AI-generated expectations repeat implementation errors | Medium / High | State arithmetic and interpretation expectations independently; retain inputs and compare actual results; student review of rules | Verification reviewer, unassigned | S2-US-02 |
| S2-R-05 | AI technical rehearsal or proposed discussion conclusions are reported as observed human comprehension | Medium / High | Separate user-confirmed priority, AI findings, Group discussion draft and actual human responses; calculate human scores only from actual participant data | Experiment coordinator, unassigned | S2-US-03, S2-US-05 |
| S2-R-06 | Coaching, small samples or role-play create unsupported claims about user understanding | Medium / High | Keep unaided first responses, task order and sample denominator; report limits and assistance; distinguish role-play from professional users | Experiment coordinator, unassigned | S2-US-03 |
| S2-R-07 | Optional interface/backend work displaces indicator verification | Medium / High | Complete metric gate first; justify corrections with evidence; retain independent synthetic dashboard boundary | Sprint facilitator, unassigned | All stories |
| S2-R-08 | Local records imply Jira activity, accepted assignments or meetings that did not occur | Medium / High | Retain local IDs; add real issue keys and meeting facts only with verification; confirm owners and dates | Backlog coordinator, unassigned | All stories and process tasks |
| S2-R-09 | A wording/layout change improves one view but causes regression in another | Medium / Medium | Shared rule source; before/after examples; relevant model, browser, narrow-screen and keyboard checks | UI reviewer, unassigned | S2-US-04 |

Update mitigation results and residual risk after each batch. A prepared
protocol, successful model check or proposed owner does not close a risk.

## Decisions and proposals

| ID | Topic and alternatives | State and authority | Rationale / consequences | Evidence or next review |
| --- | --- | --- | --- | --- |
| S2-D-01 | Indicator credibility before comprehension evaluation and optional usability changes | User-confirmed group discussion decision, reported in project chat on 2026-11-12; actual meeting date/attendees unspecified | Establishes the first priority; detailed story acceptance and PO approval remain separate | SPRINT_GOAL.md and TEAM_REVIEW.md; approve detailed contract at planning |
| S2-D-02 | Traceable synthetic-data reporting contract rather than new risk score or live integration | Planning boundary carried into user-authorized Sprint 2 implementation | Builds on existing data and shared model; formula, time, uncertainty and assumptions can be checked directly | S2-US-01; verify fields/rules and obtain team review |
| S2-D-03 | Independent worked scenarios before interpreting human comprehension results | Proposed evidence gate | Arithmetic and classification errors could otherwise be mistaken for user misunderstanding; baseline checks alone do not approve the rules | S2-US-02 and VERIFICATION.md; resolve material discrepancies and review contract |
| S2-D-04 | AI rehearsal now, actual participant sessions recorded separately | Evidence classification for this batch | Allows scenario preparation and technical checks while preserving the boundary of actual human evidence | USER_UNDERSTANDING_EXPERIMENT.md; actual first responses pending |
| S2-D-05 | Prepare a Group discussion draft covering all five members' review areas | Proposed questions and conclusions for review; no actual member answers supplied | Supports the next discussion; attendance, individual opinions, user scores and group acceptance remain to be recorded | TEAM_REVIEW.md and experiment; append actual feedback with source attribution when available |
| S2-D-06 | Select product corrections from reproducible defects or actual comprehension evidence | Proposed follow-on rule | Keeps work bounded and makes before/after claims reviewable; discussion proposals identify questions for evaluation | S2-US-04; record actual finding, selected action and recheck |
| S2-D-07 | Keep local backlog and process proposals until real Jira/team actions occur | Current evidence boundary | Avoids invented issue keys, estimates, assignments, dates and acceptance | BACKLOG.md; verify future transfer and actual meeting outcomes |
| S2-D-08 | Extend the existing shared model with evidence membership/reasons and a reproducible JSON report | Implementation choice under the user's Sprint 2 development authorization | Preserves existing calculations while exposing the records, clock and rules behind conclusions; exported data remains synthetic | S2-US-01/02; final tests and report checks in VERIFICATION.md |
| S2-D-09 | Make denominator, reporting time, concurrent evidence concerns and segment context visible in the existing UI | Implementation choice addressing source-observed traceability gaps | Connects existing model rules to evidence a reader can inspect; no new scoring or protocol behavior | S2-US-01/04; verify actual rendered behavior before claiming completion |
| S2-D-10 | Correct the Sprint goal and backlog around the largest customer's changed requirements | User authorized this planning correction after comparison with the course Sprint 2 PDF, pages 3-5, on 2026-11-12; team/PO review remains pending | Customer scope, HNDL exposure by data class, the 2027-12-31 deadline, an initial report structure and documented response to change become the primary work; S2-D-01 remains historical supporting rationale | Corrected SPRINT_GOAL.md and BACKLOG.md; new S2-US-06 through S2-US-09 are not implemented by this documentation batch |

### Customer-build decisions — 12 November 2026

| ID | Decision / authority | Rationale / verification gate |
| --- | --- | --- |
| S2-D-11 | User authorized construction against the corrected goal and a GitHub push after verification | Implement customer-scoped class exposure, deadline gap, initial report and changed role decisions; product verification precedes push |
| S2-D-12 | Extend synthetic schema with explicit customer/item/path/plan metadata while retaining the legacy indicator input | Avoid inferring a customer from global segments; a legacy input without customer metadata must report customer scope unavailable; verify import/reset and invalid recovery |
| S2-D-13 | Use shared reporting calculations for the report, roles and exported evidence | Deduplicate item/path references, retain three reconciled categories and simultaneous quality flags, use one clock and versioned rules; independent expectations and browser checks required |
| S2-D-14 | Surface the 2027 deadline and relevant 2028 replacement as a decision conflict | Report proposed options and operational consequence without invented acceptance, budget or an exemption for fallback/telemetry; plan-date evidence is separate from observed current status |

### Group confirmation — 13 November 2026

| ID | Decision / authority | Result and boundary |
| --- | --- | --- |
| S2-D-15 | Group endorsement of cross-perspective review conclusions, reported by the user on 2026-11-13 | Customer-first direction, current metric interpretation and keep/change/drop rationale confirmed internally. Present report v1 and retain the PO quantity-unit question; investigate/escalate the 2028/2027 gap. Risk occurrence, mitigation execution, funding/waivers and PO approval are not inferred |

Historical planning entries below describe their state at the time; S2-D-15
supersedes pending group-endorsement wording for the endorsed conclusions.

Existing coverage, 24-hour freshness and overall-precedence rules are inherited
prototype behavior for review. Recording them does not establish a new team or
PO approval of their details. The group priority confirmation is narrower than
acceptance of these detailed rules.

## Change record and mitigation evidence

| Date / event | Change and source | Evidence boundary and remaining work |
| --- | --- | --- |
| 2026-11-12 / planning request | User prioritized indicator credibility and requested Sprint 2 records following Sprint 1 | Local documentation work authorized; no new product implementation or Jira action claimed |
| 2026-11-12 / discussion scope | Indicator credibility first recorded as a user-confirmed group decision; Group discussion draft prepared for five review areas | Priority is confirmed; discussion questions and conclusions await review; actual participant responses remain pending |
| 2026-11-12 / delegated record preparation | Ordered stories, acceptance criteria, risks and decision boundaries drafted under exclusive file ownership | Parent integration and verification recorded in LLM_EVALUATION.md and VERIFICATION.md; actual participant and PO evidence remains separate |
| 2026-11-12 / implementation authorized | User requested development against the Sprint goal; D-08/D-09 document bounded implementation choices | Existing dirty planning records retained; scope limited to synthetic dashboard traceability and experiment support |
| 2026-11-12 / integrated technical verification | Integrating agent observed 17/17 model tests, 11/11 comparisons, production build (42 modules), desktop/mobile walkthrough and browser JSON export | Technical readiness recorded; actual human comprehension, contract approval and PO acceptance remain open |
| 2026-11-12 / course requirement correction | Source review found that the earlier goal omitted the customer's changed requirements; user requested corrected GOAL and backlog | Planning correction only; baseline tests and technical evidence do not establish delivery of the new customer requirements |

## Risks introduced by the customer requirement change

The source is `PQC_Scrum_Project_Sprint2_pdf.pdf`, pages 3-5, supplemented by
the persona cards and general project instructions. These risks take priority
when planning the corrected increment. Owners and estimates require actual
team assignment; no risk is closed by rewriting the plan.

| ID | Risk and effect | Likelihood / impact | Mitigation and required evidence | Related work |
| --- | --- | --- | --- | --- |
| S2-R-10 | Unscoped global connection totals are presented as the largest customer's exposure | High / High | Identify the synthetic customer and map each customer data item to all required connection segments; demonstrate that unrelated customer records do not affect the report | S2-US-06, S2-US-08 |
| S2-R-11 | Counting segments or repeated paths double-counts data and misstates how much is exposed | High / High | Use the goal's distinct logical data-item unit and customer/class denominator; reconcile unique items and show exposed, reported-PQC and unresolved buckets separately | S2-US-01/02, S2-US-06 |
| S2-R-12 | Missing class, path or observation evidence is excluded or silently treated as protected | Medium / High | Keep Unknown class and unresolved items visible, retain uncertainty alongside known exposure, and test missing/incomplete/stale/future evidence explicitly | S2-US-02, S2-US-06, S2-US-08 |
| S2-R-13 | A 2028 legacy replacement plan appears compatible with the new 2027-12-31 obligation | High / High | Flag the scheduling conflict for every affected customer-carrying segment, including short-lived telemetry and approved exceptions; record options, business consequences and decisions without claiming completed production migration | S2-US-07, S2-US-09 |
| S2-R-14 | Existing technical checks or AI role walkthroughs are taken as acceptance of the revised customer report and human-factors requirements | Medium / High | Retain 17/17 tests and 11/11 comparisons as baseline evidence for e371940 only; add customer/class/deadline/report checks and obtain attributable team/PO feedback and actual group reflection | S2-US-02, S2-US-08/09 and process tasks |
| S2-R-15 | Technical work displaces reprioritization, Jira evidence and required course deliverables | Medium / High | Record keep/change/drop rationale and actual planning/role/retrospective decisions; prepare the 500-word report, five-minute video and slides-used PDF against the 2026-11-18 23:59 Finnish-time submission deadline | Process tasks and corrected completion checklist |

## Customer build risk follow-up

S2-R-10 through S2-R-14 now have customer-scoped technical mitigation evidence:
the integrating agent reports 39/39 tests, a 44-module build and 11/11 legacy
comparisons, plus desktop/mobile/keyboard, import/reset, role and export checks.
Six known customer items reconcile as 2 exposed + 2 unresolved + 2 reported PQC;
filtering did not alter totals, and the unrelated customer's selection/export
remained separate. Current-clock evidence gave 2 exposed + 4 unresolved + 0
reported PQC. Legacy metadata absence stayed unavailable; invalid input was
rejected. A 390 × 844 width-overflow defect was corrected and checked; unordered
required segment IDs no longer imply an observed route order. Exact evidence
belong in VERIFICATION.md. Final production preview loaded the built asset,
retained the same 2/2/2 totals and had empty scoped error logs; 390px production
layout had equal report scroll/client widths and no page horizontal overflow. Scope completeness, rule
acceptance, data-quantity unit review and actual persona comprehension remain limitations after technical
checks. S2-R-15 remains open until actual Jira/process evidence and course
artifacts/submission are complete.

## Earlier implementation findings and residual risks

The integrating agent identified source-level presentation gaps: the coverage
formula was hidden on mobile, the headline did not show simultaneous unknown
or stale evidence inline, inventory scope lacked an explicit unchanged global
denominator, connection evidence lacked sibling-segment context, and no
dedicated trace/export interface existed. These are source observations, not
claims about member feedback. The implemented formula, evidence conditions,
scope text, sibling context and indicator audit/export address those gaps.

S2-R-01 through S2-R-04 now have model/scenario and rendered evidence. The
downloaded report preserves the 5/8 calculation, eight input records, exact
clock and numerator IDs. S2-R-09 has desktop and 390 × 844 mobile checks,
including no observed page/panel horizontal overflow, an in-viewport footer,
keyboard scrolling to the first evidence link and navigation to SEG-008. The
browser warning/error log was empty in the scoped walkthrough; a read-only
source/model reviewer reported no actionable issue.

These checks mitigate the stated technical risks within their observed scope.
S2-R-05/06 remain open because no actual human comprehension measurements were
collected; S2-R-08 remains open for real Jira/team facts. Other risks retain
their residual review requirements, and none is closed by this batch alone.

Technical results belong in [VERIFICATION.md](VERIFICATION.md); AI technical
rehearsal results and the human protocol belong in the
[experiment](USER_UNDERSTANDING_EXPERIMENT.md). Record actual group decisions
in [TEAM_REVIEW.md](TEAM_REVIEW.md), generated-output evaluation in
[LLM_EVALUATION.md](LLM_EVALUATION.md) and carry-over outcomes in
[RETROSPECTIVE_ACTIONS.md](RETROSPECTIVE_ACTIONS.md). Do not infer risk closure
or human acceptance from the existence of these artifacts.

## Jira evidence update - 13 November 2026

The user authorized Sprint 2 upload and final checks. Fifteen real items
SCRUM-15 through SCRUM-29 are in Sprint 2 ID 3; final states are 8 In Review,
4 In Progress and 3 To Do. Ten directed dependencies were saved and read back.
Five malformed implementation hrefs were corrected. See the exact mapping and
UI evidence in [JIRA_UPLOAD.md](JIRA_UPLOAD.md).

This supplies the actual Jira-transfer part of S2-R-08 and S2-R-15. Both retain
residual process risk: assignments, estimates, dates, individual observations,
teacher/PO decisions and course delivery require their own evidence. No risk
is closed solely by uploading its tracking item.
