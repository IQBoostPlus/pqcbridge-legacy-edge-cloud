# Sprint 2 LLM output evaluation

This register records AI-generated planning, implementation and review work.
Group endorsement of the review conclusions is confirmed by the user on
13 November 2026. Named individual evaluations and teacher/PO acceptance
retain their separate evidence states. Scope authority:
[Sprint goal](SPRINT_GOAL.md). Related records: [backlog](BACKLOG.md),
[risk and decision log](RISK_AND_DECISION_LOG.md),
[team review](TEAM_REVIEW.md) and [verification](VERIFICATION.md).

Current planning authority is the corrected Sprint goal: the largest customer's
reporting and migration changes come first. AI-S2-001 and AI-S2-002 remain
historical evidence for the earlier indicator-credibility increment; they do
not demonstrate fulfillment of the newly identified customer requirements.

## Significant interaction register

### AI-S2-001: credibility-first planning and comprehension rehearsal

| Field | Recorded evidence / state |
| --- | --- |
| Date | 12 November 2026 |
| Request and authority | User prioritized indicator credibility, confirmed this priority as a group decision and requested a user-understanding experiment and Sprint 2 records following Sprint 1 |
| Context | Project CLAUDE.md, README, Sprint 1 goal/backlog/process records, existing dashboard model, fixture and tests, and the current chat; the chat has not been exported as a standalone prompt archive |
| Author / evaluator | Integrating AI owns the goal, experiment and verification; sprint2_backlog AI owns backlog and risks; sprint2_process AI owns team review, retrospective and this register. Student evaluator unassigned |
| Output references | SPRINT_GOAL.md, BACKLOG.md, RISK_AND_DECISION_LOG.md, USER_UNDERSTANDING_EXPERIMENT.md, VERIFICATION.md, TEAM_REVIEW.md, RETROSPECTIVE_ACTIONS.md, this register and integrating-agent updates to project instructions |
| Scope | Local documentation and a source/model-based rehearsal; no product implementation in this batch |
| Review findings | Credibility checks must precede comprehension claims; a reported group priority does not establish meeting attendance; proposed member questions require actual responses before recording conclusions; existing implementation and new Sprint 2 acceptance must remain distinct |
| Decision | Retain the priority as a user-confirmed group decision. Prepare a group discussion draft with questions for all five members and a protocol for actual human evaluation |
| Technical evidence | Integrating agent reports 11/11 independent metric comparisons and 12/12 existing model tests passed; commands, source revision, scenario details and integration checks belong in VERIFICATION.md |
| Experiment evidence | AI/model-based answers are rehearsal artifacts. Group discussion questions are prepared for review. No actual participant answers, completion times, human success rates or change-effect measurements were collected |
| Student assessment | Pending a named student's review of the outputs, their actual findings and decisions |
| Remaining evidence | Actual human study, real group review details, estimates/owners/dates/Jira keys, any implementation and UI retest, and team/PO acceptance |

The technical counts above were supplied by the integrating agent and are not
an independent rerun by this document's author. The integrating agent reconciles
them with the final [verification record](VERIFICATION.md) and checks the
assembled documents before reporting completion.

### AI-S2-002: indicator traceability implementation

| Field | Recorded evidence / state |
| --- | --- |
| Date and authority | 12 November 2026; user requested Sprint 2 development according to the goal |
| Context | SPRINT_GOAL.md, prioritized backlog, existing model/fixture/Vue components and prior verification; pre-existing planning edits retained |
| Work and ownership | Integrating AI owns UI, integration, experiment assets and verification; s2_model AI owns dashboard/model.mjs and its model tests; s2_records_build AI owns backlog, risks, this register and retrospective records |
| Selected scope | Expose indicator evidence membership and concurrent reasons, reporting clocks, per-connection context, a JSON evidence report and reusable experiment scenarios; retain independent synthetic dashboard |
| Review basis | Existing calculations need a direct trace from displayed conclusion to records, selected clock and rule; source/model evidence does not establish actual human comprehension |
| Outputs | Shared reporting evidence and export API, interface integration and scenario assets; affected file list and exact observed behavior belong in VERIFICATION.md |
| Verification state | Integrating agent observed 17/17 model tests (12 existing + 5 new), 11/11 scenario comparisons, production build with 42 modules and scoped desktop/mobile browser checks; details in VERIFICATION.md |
| Evaluation state | Integrating AI reviews implementation and evidence; student evaluation and team/PO acceptance pending |
| Remaining evidence | Actual first-response human study data, discussion outcomes, assignment/date/Jira confirmation and any stakeholder acceptance |

This entry records the development interaction separately from the planning
batch's historical 12/12 model tests and 11/11 comparisons. The final development
counts above were supplied by the integrating agent, not independently rerun by
this record author. Current comparison output retains source SHA-256 hashes;
the planning output is preserved as `experiments/results-planning-baseline.json`.

The integrating agent verified default 62.5% coverage and its 5/8 formula, all
audit reasons/IDs, red status with eight stale records under the current clock,
and an actual browser JSON download with matching inputs and clock. Local
empty, unknown, expected-fallback, mixed-path and stale-PQC scenarios rendered
their expected states; invalid input was visibly rejected, export disabled,
and reset recovered the workspace. Sarah's SEG-007 investigation, Michael's
SEG-001 blocker and Emma's suspected-downgrade risk were observed as role
workflow checks. These are AI browser observations, not human responses.

Mobile checks at 390 × 844 found no page/panel horizontal overflow; the footer
remained inside the viewport. Tab navigation moved from the reporting clock to
SEG-001 and scrolled the audit to reveal the link; SEG-008 navigation worked.
The scoped browser warning/error log was empty. A separate read-only reviewer
found no actionable source/model issue. Five screenshots and the downloaded
JSON are retained under `evidence/`. Six valid scenario files, one invalid
example and a response sheet support actual sessions; human results remain
uncollected.

### AI-S2-003: correction against the course Sprint 2 requirements

| Field | Recorded evidence / state |
| --- | --- |
| Date and authority | 12 November 2026; user requested that GOAL and backlog be corrected first, with a comprehensive goal usable for the next stage |
| Source context | Course `PQC_Scrum_Project_Sprint2_pdf.pdf`, pages 3-5; `Human_factors_persona_cards.pdf`; `Human_factors_project_instructions.pdf`; current goal, backlog and product baseline e371940 |
| Finding | The earlier goal prioritized generic credibility and comprehension work but omitted the largest customer's changed reporting scope, HNDL exposure by data class, the 2027-12-31 migration obligation and an initial customer report structure |
| Selected correction | Make the customer-facing requirement change the product priority; preserve traceability and verification as supporting foundations; specify keep/change/drop decisions, persona impacts, group dynamics, Jira evidence and course deliverables |
| Work and ownership | Integrating AI revises SPRINT_GOAL.md and reconciles entry-point references; backlog agent revises BACKLOG.md; record agent updates this register and RISK_AND_DECISION_LOG.md under exclusive ownership |
| Scope and outputs | Documentation correction only: corrected goal/backlog and affected references/process records. No new customer-report code, GitHub push, Jira update or stakeholder acceptance is established by this batch |
| Story continuity | Preserve S2-US-01 through S2-US-05 and their existing evidence. Introduce S2-US-06 customer data/class exposure, S2-US-07 deadline gap, S2-US-08 customer report and S2-US-09 revised persona decisions; new work remains to implement |
| Metric review requirement | Distinct logical customer data items must not be confused with segment counts or data volume. Keep unknown class, incomplete paths and evidence uncertainty visible and reconcile class totals |
| Deadline review requirement | All segments carrying customer data are in scope for 2027-12-31, including short-lived telemetry and approved fallback; the persona's 2028 replacement timing is an explicit conflict to resolve or escalate |
| Human-factors review requirement | Record actual changes to persona trade-offs and group communication, disagreement, decisions and retrospective actions. AI preparation does not supply member experiences or team/PO approval |
| Verification boundary | The earlier 17/17 model tests and 11/11 comparisons remain baseline evidence. Final document consistency, links and whitespace are checked by the integrating agent; no new product verification is claimed here |
| Integrated document checks | Passed on 2026-11-12: seven changed Markdown files only, 52 local links, R1-R8 coverage, retained US-01 through US-09 and T-01 through T-06 identifiers, key contract/deadline markers and git diff whitespace check. GOAL/backlog were read together to reconcile report/export, plan-date and legacy-import acceptance conditions; runtime tests were not rerun for this documentation-only batch |
| Student and PO evaluation | Pending named student review, actual findings and planning/PO confirmation of the corrected scope |

The course deadline is 18 November 2026 at 23:59 Finnish time. The general
instructions require a 500-word sprint report, five-minute video and PDF of the
slides used, alongside the working increment and Jira/process evidence. An
initial customer report structure is due at the next review; its actual meeting
date is not supplied. No extra customer PDF export format is inferred.

### AI-S2-004: customer-reporting implementation against the corrected GOAL

| Field | Recorded evidence / state |
| --- | --- |
| Date and authority | 12 November 2026; user requested Sprint 2 construction against GOAL and GitHub push after completion |
| Context | Corrected SPRINT_GOAL.md/BACKLOG.md, supplied course-source requirements, existing Vue dashboard/model/tests and pre-existing planning edits |
| Work and exclusive ownership | Integrating AI owns UI, assembled verification and entry-point documentation; customer-model AI owns model and new customer fixture; test AI owns new customer tests and independent expectations; record AI owns backlog, risk/decisions, this register, retrospective, team agenda and comprehension protocol |
| Selected scope | Explicit customer/item/class/path metadata; reconciled potential-exposure/unresolved/reported-PQC quantities; all-customer-connection 2027 gap and 2028 conflict; initial report and shared role/export evidence |
| Evaluation checks required | Customer isolation and unknown ownership; repeated/shared paths without double counting; invalid/incomplete data; class reconciliation; lifetime/expected-versus-suspected fallback; freshness/future/empty cases; plan dates on either side of the deadline; legacy import/reset; same-clock report/export and role workflows |
| Current technical state | Integrating agent reports 39/39 tests (17 legacy + 22 new), 44-module production build and 11/11 legacy scenario comparisons passed; scoped browser checks verified six-item 2/2/2 totals, unchanged filtered denominators, current-clock 2/4/0, separate customer selection/export, legacy unavailable state, invalid rejection/reset and three role workflows. Exact evidence belongs in VERIFICATION.md |
| Process preparation | Customer-focused review questions, role tasks and retrospective follow-up prepared; US-01/02/06-09 technically implemented/verified; actual Jira/estimates/assignments and human feedback remain pending |
| Student evaluation and acceptance | Pending named student review and actual findings; technical AI review cannot establish student evaluation or teacher/PO acceptance |
| GitHub delivery | Product commit `7f14cddc35f0ed555fd86ab58ed3ce07b8abed99` pushed to `origin/main` on 12 November 2026. A subsequent `git ls-remote --heads origin main` returned that exact commit. This receipt is a documentation-only follow-up; product verification remains tied to the implementation above |

AI review and corrections in this build: the scoped 390 × 844 browser check
found report-width overflow; grid-column changes were checked, including
keyboard horizontal-table access and Enter to open details. Required segment
IDs were presented as a set instead of implying unrecorded route order with
arrows. At 1440 × 900 the customer/role flows were checked. These are observed
technical behaviors, not measured human comprehension or a broad accessibility
claim. A downloaded CUS-OTHER evidence bundle retained only that selected
customer's report, the same clock and SEG-006 association. Legacy input retained
62.5% all-system segment share while explicitly lacking customer report scope.

Final production-preview confirmation supplied by the integrating agent: the
44-module build loaded `assets/index-Dqnu7a78.js` and rendered the same six-item
2/2/2 customer totals. Scoped browser error logs were empty. At 390 × 844, body
width was 390px and the report's scroll/client widths were both 345px, with no
page horizontal overflow observed. Production desktop/mobile screenshots and
actual Northfield/other-customer browser JSON downloads are retained under
`evidence/`; VERIFICATION.md identifies their provenance and limits. This does
not close actual student review, Jira, human feedback or PO acceptance.

### AI-S2-005: cross-perspective review and discussion record

| Field | Recorded evidence / state |
| --- | --- |
| Date and task | 12 November 2026; prepare a subagent discussion and review record for the current Sprint 2 increment |
| Reviewed product | Implementation commit `7f14cddc35f0ed555fd86ab58ed3ce07b8abed99`; documentation receipt at `4cf3e9e9b5371bd881ada382a5519682b17d621b` |
| Review method | Three AI subagents reviewed security/evidence, operations/customer needs and Scrum/change response. They exchanged challenges on quantity units and the minimum review outcome; the process reviewer recorded the synthesis under exclusive TEAM_REVIEW.md ownership |
| Sources evaluated | Corrected GOAL/backlog, model, customer fixture/tests, CustomerReport.vue, existing verification, team and retrospective records |
| Security evaluation | Six equal-weight logical items reconcile as 2 exposed + 2 unresolved + 2 reported PQC; unknown ownership and missing paths prevent complete-customer claims; stale evidence and suspected downgrade require qualifications |
| Operations evaluation | Nine required connections are 2 classical + 5 reported current PQC + 2 unresolved; seven absent migration plans are a separate measure. The 2028/2027 conflict requires investigation/escalation, not assumed funding, feasibility or a waiver |
| Process evaluation | Recommend a populated report for PO consideration; preserve keep/change/drop rationale and actual process follow-up. A formal external-user study or a solved procurement programme is not added as a Sprint review prerequisite |
| Converged recommendation | Present the declared inventory position with limitations; ask the PO whether item counts suffice for the initial report or whether volume, unit, reporting window and source must be specified |
| Outputs | Cross-perspective findings, proposed decisions, unresolved PO questions and evidence-based follow-up in TEAM_REVIEW.md |
| Verification performed | Read-only source and record review; the earlier 39/39 tests, build and browser checks were inspected as recorded evidence, not rerun or relabeled as new human results. Final document checks are performed at integration |
| Evaluation boundary | Findings are AI-assisted analytical recommendations. Actual group responses, accepted assignments, Jira actions, user-understanding measurements and teacher/PO approval retain their existing evidence states |

No product code or course-submission artifact was changed by this review batch.

### AI-S2-006: group endorsement recorded

| Field | Current evidence / state |
| --- | --- |
| Date and source | 13 November 2026; the user reports that the group approved the review conclusions |
| Confirmed scope | Customer-first priority, report/evidence interpretation, current logical-item metric with stated limitations, keep/change/drop rationale and follow-up direction |
| Record update | TEAM_REVIEW, GOAL, backlog, risks, retrospective, experiment/verification status and README references now distinguish confirmed group endorsement from independent unfinished work |
| Provenance | AI-S2-005 remains the analytical source; the user's report supplies subsequent group endorsement. No member quotations, attendance or scores are inferred |
| Outstanding evidence | Actual teacher/PO response, named role/estimate values, Jira mutations, session measurements, individual process observations and course submission |
| Checks | Documentation consistency, links and whitespace only; no product or participant tests performed in this update |

### AI-S2-007: Jira upload, repair and final checks

| Field | Recorded evidence / state |
| --- | --- |
| Date and authority | 13 November 2026; user authorized Jira upload/retry and final status, link and dependency checks, then writing actual keys back to project records |
| Inputs | Corrected GOAL/backlog, implementation evidence, confirmed group endorsement and fifteen prepared source records |
| Method | Connected Edge Jira UI; first four items through Create, eleven through in-product Rovo preview/create; no direct hidden API or browser security-setting changes |
| Creation evaluation | Rovo callback reported an invocation-format error after the creation success. Creation was not repeated; reloaded board verified fifteen unique items in existing Sprint 2 ID 3, preventing duplicate creation |
| Corrections | Five implementation hrefs contained encoded line-break/Records text; original descriptions were restored and read back with one local-ID/criteria marker and the correct commit href. A rich-editor append was detected and replaced before saving |
| Workflow and dependencies | Actual states individually checked and reconciled in the final task list: 8 In Review, 4 In Progress, 3 To Do; ten directed blocks links saved and read back, including reciprocal prerequisite checks on SCRUM-17 |
| UI recovery | A dropdown intercepted the first Link click and selected an unwanted target; the editor was corrected/cancelled, then the proper link set was saved and verified. A Sprint 1 date dialog was cancelled without changes |
| Output | SCRUM-15 through SCRUM-29 mapped to local IDs in BACKLOG.md and JIRA_UPLOAD.md, with screenshot and dependency list |
| Verification boundary | Jira UI/documentation verification only; no new runtime tests, participant data, individual experiences, teacher/PO approval or course submission inferred. Owners, estimates and dates remain blank |
| Student evaluation | Upload/repair evidence is available for group review; AI execution does not by itself establish student evaluation or teacher/PO acceptance |

The earlier entries preserve their dated scope. Their pending Jira-transfer
statements are superseded by this verified upload event, not by creation
attempts or AI assertions alone.

## Evaluation criteria and follow-up

- Check every metric conclusion against the contract and independently worked
  expected values, including unknown, empty, stale and mixed-path cases.
- Check whether outputs preserve the distinction between migration progress,
  evidence quality and security assurance.
- Check attribution: user-confirmed group priority is reportable; proposed
  member questions remain separate from actual member responses.
- Review the human-study prompts for leading cues; retain unaided answers before
  giving explanations and report both separately.
- For each adopted change, link the actual observation, decision, implementation
  and verification. Record rejected AI suggestions and their reasons as well.

Append future significant interactions with their actual request, context,
outputs, evaluator, defects found, decisions, fixes and verification. Do not
mark student evaluation complete from an AI review alone.
