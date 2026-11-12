# Sprint 2 LLM output evaluation

This register records AI-generated planning and rehearsal work. Student
evaluation and teacher/PO acceptance remain pending. Scope authority:
[Sprint goal](SPRINT_GOAL.md). Related records: [backlog](BACKLOG.md),
[risk and decision log](RISK_AND_DECISION_LOG.md),
[team review](TEAM_REVIEW.md) and [verification](VERIFICATION.md).

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
