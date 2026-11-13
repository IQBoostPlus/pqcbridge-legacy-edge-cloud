# Sprint 2 team review and group discussion record

Baseline: 12 November 2026. Scope: [Sprint goal](SPRINT_GOAL.md).
The earlier indicator-credibility decision is retained as history below.
The corrected goal now prioritizes customer reporting and the changed migration
target. **Group endorsement of the review conclusions is confirmed**, reported
by the user on 13 November 2026. Individual responses and teacher/PO feedback
retain their own evidence states.

## Confirmed group endorsement — 13 November 2026

The user reports that the group approved the cross-perspective review conclusions.
This confirms the group's endorsement of the customer-first priority, evidence
interpretation, keep/change/drop rationale and proposed follow-up direction.
The logical-item metric is accepted by the group as the current report basis,
including its limitations and the open PO question about whether volume is
required. The group also endorses reporting the 2028/2027 conflict and
investigating or escalating options without assuming funding or a waiver.

| Confirmation item | Current state |
| --- | --- |
| Cross-perspective review conclusions | Confirmed by group, reported by the user on 2026-11-13 |
| Customer-first scope and keep/change/drop rationale | Confirmed by group |
| Interpretation of six data items, nine required segments and seven missing plans | Confirmed by group; these remain distinct quantities |
| Current metric rules, limitations and presentation of report v1 | Confirmed by group; teacher/PO acceptance remains separate |
| Follow-up direction for the deadline conflict and review questions | Confirmed by group; execution and business authorization are not inferred |

This decision supersedes earlier pending group-endorsement wording for these
conclusions. It is a user-reported group decision. Meeting attendance, individual
statements, experiment scores, role/estimate values, Jira changes, procurement
decisions and teacher/PO approval have not been supplied by this confirmation.

## Membership and roles

The five-member roster is carried from the user-supplied
[Sprint 1 team register](../sprint-1/TEAM_REVIEW.md). Sprint 1 responsibilities
provide context for the discussion draft, not confirmed Sprint 2 assignments.
The proposal for Valerii Lebedev to act as Sprint 2 Scrum Master remains subject
to team confirmation. The teacher retains the Product Owner role.

## Cross-perspective review findings — 12 November 2026

This AI-assisted implementation review examined product commit `7f14cdd`
from security/evidence, migration/customer-reporting and Scrum/change
perspectives. It records analytical findings and proposed decisions, with
provenance in [LLM interaction AI-S2-005](LLM_EVALUATION.md). The review used
the goal, backlog, implementation, fixture and existing
[verification evidence](VERIFICATION.md); it did not conduct new participant
sessions or establish student agreement or teacher/PO acceptance.

### Findings and exchanged challenges

| Perspective | Finding | Challenge raised and resulting recommendation |
| --- | --- | --- |
| Security and evidence | The default six logical items reconcile to two potential HNDL, two unresolved and two reported PQC. Unknown ownership and missing SEG-009 prevent a complete-customer claim. Suspected downgrade requires investigation and does not establish an attack. | The process perspective asked what minimum explanation supports a review recommendation. The security response proposed a short demonstration of quantities, scope uncertainty, time and suspected-downgrade limits; it did not require an external study or score threshold. |
| Migration and customer reporting | SEG-001's 2028-06-30 replacement/migration timing conflicts with the proposed 2027-12-31 target. Loss of pump monitoring is a service-continuity consequence, not evidence that an alternative is feasible. | The process perspective asked whether the Sprint must solve procurement. The operations response supported showing the gap, consequences and investigation/escalation options now, with funding, feasibility and any customer exception unresolved. |
| Scrum and change response | The implemented increment and documented technical checks support presenting report v1. Bounded AI model/test/record ownership and observed corrections are workflow evidence; they do not establish student coordination outcomes or acceptance. | The reviewers converged on keeping the review bounded to the required customer outcome. Actual team decisions, Jira activity, retrospective observations and PO feedback remain necessary evidence for the corresponding process tasks. |

The quantity-unit question remains open for PO review: **do counts and
proportions of distinct logical data items adequately answer how much customer
data is exposed in the initial report?** These quantities describe a declared
inventory of streams/assets. They do not estimate byte volume, traffic share,
attack probability or financial loss. If a volume measure is requested, define
its unit, observation window and source data explicitly before changing the
backlog or reporting a value.

Keep the three reporting quantities distinct:

- **Customer data:** six unique attributed items = 2 exposed + 2 unresolved +
  2 reported PQC. DATA-UNATTR remains outside attributed totals and limits
  inventory completeness.
- **Required connections:** nine unique segment references = 2 classical gaps +
  5 reported current PQC + 2 unresolved (unknown SEG-008 and missing SEG-009)
  under the historical reporting clock.
- **Planning:** seven of those connections have no recorded migration plan.
  SEG-001 has a late plan and replacement; SEG-007 has an on-deadline plan.
  Missing plans are not seven classical connections, and a plan is not migration
  completion.

### Confirmed direction and follow-up actions

Keep shared rules, source traceability, clocks, validation and evidence export.
Keep customer reporting and the 2027 gap ahead of generic polish. Change any
claim that uses global segment share as customer-data exposure. Drop generic
JSON export as sufficient evidence of a completed customer report. Defer a
bespoke PDF exporter, broad redesign and expanded comprehension research unless
actual review findings justify them. The group endorsed this direction on
13 November 2026. These recommendations preserve the
corrected backlog scope and add no new course or release requirement.

| Follow-up action | Completion evidence | Owner / status |
| --- | --- | --- |
| Present report v1 for PO consideration | Demonstrated class quantities, unknown scope, evidence trace and deadline conflict; actual PO response recorded | Direction confirmed by group; execution owner unassigned |
| Confirm the quantity unit | PO response accepting logical-item quantities, or a clarified volume/unit/window requirement entered in the backlog | Unassigned; pending decision |
| Investigate or escalate the 2028/2027 gap | Alternatives, continuity/budget constraints and actual authorized decision; unknown feasibility or funding stays explicit | Direction confirmed by group; execution owner unassigned |
| Confirm keep/change/drop and Scrum planning | Actual team/PO decisions, roles/rotation, estimates and assignments linked to verified Jira items | Group keep/change/drop confirmed; fifteen Jira items and ten dependencies verified 2026-11-13 in JIRA_UPLOAD.md; roles and estimates remain pending |
| Follow through retrospective actions | Actual observations, adopted actions, completion criteria and next-Sprint follow-up recorded | Unassigned; pending actual review |
| Complete existing course submission tasks | Checked report, video, slides-used PDF and actual submission evidence as required by the goal | Unassigned; pending delivery |

The group has confirmed the recommendation to demonstrate the technically
checked increment and seek PO decisions on scope, metric unit and migration
trade-offs. The original AI findings establish no member attendance, personal
response, comprehension score or PO acceptance. Subsequent group endorsement
comes from the user's report above. Remaining actual-review fields have their
own evidence states.

## Current customer-change review agenda

The corrected [goal](SPRINT_GOAL.md) supersedes the earlier credibility-first
ordering below. The customer report, class-level HNDL quantities and all-customer-
connection target of 31 December 2027 now lead. Traceable indicators remain a
foundation. This is the next review agenda, not a record of a completed meeting.

| Member invited to review | Customer-focused question | Evidence / decision to record |
| --- | --- | --- |
| Changzhengyuan Chu | Does the report answer the key customer's question, using a clear unit and complete scope? | Class counts versus segment share; product vision link; unanswered PO questions |
| Valerii Lebedev | How should the team plan the changed priorities and rotate facilitation? | Actual Scrum Master rotation, estimates, workload distribution and Jira changes |
| Jinghao Lei | Can Emma reach the report and trace an exposed class to its required segments? | Actual first response, navigation issue and any adopted correction |
| Cheng Peng | What can Sarah conclude about known classical exposure, unknown evidence and suspected downgrade? | Lifetime assumptions, concurrent quality flags and justified investigation |
| Zhizhou Zhao | What should Michael and Emma do about certified replacements in 2028 against the 2027 target? | Continuity/budget trade-offs, alternative or escalation proposal, accepted decision if any |

Persona trade-offs for discussion: Sarah needs exposure and downgrade evidence;
Michael must preserve service while planning constrained replacements; Emma
must explain customer readiness without inventing budget, agreement or a safe
waiver. Short-lived telemetry and approved fallback still carry the deadline.

Record the change response with keep/change/drop rationale from the backlog.
Ask each member how the new scope affected their work, coordination,
disagreements and emotional reactions; record no effect if that is their
actual response. Record how a disagreement was handled and which decision was
adopted, rather than treating a prepared agenda as consensus. Link accepted
changes to real Jira items and next-Sprint retrospective follow-up.

| Current review field | Evidence / state |
| --- | --- |
| Corrected scope and implementation authority | User requested comprehensive GOAL/backlog correction, then development and GitHub push |
| Meeting date, channel, actual participants and facilitator | Pending actual review |
| Product vision/stakeholder analysis reviewed | Pending actual review and reference |
| Keep/change/drop decisions and rationale | Confirmed by group on 2026-11-13, as reported by the user; PO response separate |
| Changed workload, communication, disagreements and emotions | Pending attributable member observations |
| Actual first answers and assistance | Pending; use the customer protocol in USER_UNDERSTANDING_EXPERIMENT.md |
| Scrum Master rotation, acknowledged assignments and estimates | Pending actual planning |
| Technical evidence available for review | Integrating agent reports 39/39 tests, build/scenarios and scoped desktop/mobile/keyboard/import/export/role checks, plus final built-asset preview with 2/2/2 totals and empty error logs; see VERIFICATION.md |
| Teacher/PO feedback and acceptance | Pending actual review |

## Earlier group discussion record

The following material belongs to the earlier indicator-focused increment.
It does not establish acceptance of the corrected customer-reporting scope.

## Historical group discussion results

### User-confirmed group priority

Indicator credibility comes first: establish and independently check the
coverage denominator, segment unit, unknown handling, freshness and status
interpretation before testing how users understand them. User understanding
then informs focused usability changes. This priority is confirmed through the
user's report of the group decision on 12 November 2026; no individual vote or
quotation is inferred.

### Group discussion draft

The following questions and follow-ups are proposed for member review.
They are not recorded member statements or findings from a completed meeting.
Detailed scenarios and the proposed human study are in the
[user-understanding experiment](USER_UNDERSTANDING_EXPERIMENT.md).

| Member invited to review | Proposed discussion question | Proposed follow-up |
| --- | --- | --- |
| Changzhengyuan Chu | Does the coverage explanation keep its numerator, denominator and evidence limits clear enough to avoid treating progress as a security guarantee? | Make the metric contract and its evidence links the first planning gate; keep acceptance separate from test results |
| Valerii Lebedev | Does the stale-100% example explain why high reported coverage can coexist with insufficient current evidence? | Demonstrate the stale-100% scenario and explain reporting time before presenting the percentage |
| Jinghao Lei | Can users distinguish a filtered inventory from the global coverage denominator? | Keep global scope and filtered inventory scope distinguishable; propose a wording change only after the human task confirms a problem |
| Cheng Peng | Can users distinguish expected fallback from an unconfirmed suspected downgrade? | Check the classification reasons and use separate expected and suspected examples; preserve the unconfirmed-attack qualification |
| Zhizhou Zhao | Can users identify the remaining classical segment when the gateway-to-cloud segment reports PQC? | Present the two segments together in the explanation and ask users to identify the remaining classical segment |

This draft identifies hypotheses for discussion. It reports
no measured misunderstanding rate, real consensus on the proposed fixes or
teacher/PO acceptance.

## Actual human review and acceptance

| Field | Current evidence / next entry |
| --- | --- |
| Priority decision | User reports group agreement to place indicator credibility first |
| Meeting date, channel, attendees and facilitator | Not supplied |
| Human experiment sessions and unaided answers | Not collected in this batch |
| Member feedback, disagreements and adopted changes | Group endorsement of review conclusions confirmed on 2026-11-13; individual comments and disagreements not supplied |
| Sprint 2 owners, estimates, dates and Jira keys | Jira entry verified 2026-11-13: SCRUM-15 through SCRUM-29; see JIRA_UPLOAD.md. Owners, estimates and formal dates remain pending |
| Team acceptance and conditions | Confirmed for the cross-perspective review conclusions on 2026-11-13; see the current endorsement record |
| Teacher/PO feedback and acceptance | Pending |

For a real review, record each participant's task, unaided response, explanation
after prompting, resulting decision and source evidence. Keep initial and
assisted answers separate. Append actual group conclusions with their date and
participants; retain these questions as the planning baseline.
