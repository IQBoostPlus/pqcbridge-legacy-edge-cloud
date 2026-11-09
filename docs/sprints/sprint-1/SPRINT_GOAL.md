# Sprint 1 goal and delivery record

## Goal and authority

Deliver a runnable PQC Security Monitoring Dashboard using fixed synthetic data,
so that a security officer, migration manager and CIO can understand connection
protection, remaining exposure and migration blockers from the same dataset.

The user approved this scope in the project chat. This is a team planning
baseline; teacher/Product Owner acceptance and team estimates remain pending.
The course deadline recorded in the supplied instructions is **11 November 2026,
23:59 Finnish time**. Confirm any subsequent course announcement with the PO.

Current delivery state: **first increment implemented; AI model and browser
checks passed within the recorded boundary; human acceptance pending**. The
existing PQC Bridge communication prototype is background material. Actual checks
and runtime results are recorded in [VERIFICATION.md](VERIFICATION.md).
The user confirmed that the goal and ten work items are in [SCRUM Sprint 1](https://tacczy.atlassian.net/secure/GHGoToBoard.jspa?sprintId=1).
Five stories are In Review, and five process tasks are To Do. The Jira Sprint
has not started and has no dates entered. See [BACKLOG.md](BACKLOG.md) for the
issue mapping and confirmed dependency links. Student/PO acceptance and course
submission are tracked separately.

## Committed dashboard scope

| Local story | Increment | Observable acceptance |
| --- | --- | --- |
| S1-US-01 | Fixed synthetic dataset covering PQC, classical fallback and unknown connection states | Repeat loads produce the same data; the UI labels it synthetic and shows its snapshot time. Data identifies each connection segment, algorithm/key-establishment method, device, fallback reason, migration blocker and any confidentiality-lifetime assumption used in exposure explanations. |
| S1-US-02 | Overview showing total connections, PQC count/share, fallback count and unknown count | Summary and list reconcile. The denominator and units are visible. Unknown records remain in the total and never become protected records by default. |
| S1-US-03 | Connection list and status filter | Each row identifies the connection, device, segment (device-to-gateway or gateway-to-cloud), key-establishment method, status and reason. Filtering returns the matching records and supports an empty result. A PQC gateway-to-cloud segment does not label the whole device path PQC. |
| S1-US-04 | Basic Sarah / Michael / Emma views | Tabs or sections reuse the same dataset. Sarah can identify exposure and investigation candidates with reasons; Michael can see migration progress and blockers; Emma can see an explained overall status and up to three relevant risks. |
| S1-US-05 | Definitions and interpretation limits | Explain coverage, fallback, HNDL exposure, data time and classification assumptions. Expected fallback is distinguishable from a suspected downgrade. Exposure is not a detected HNDL attack; migration completion is not a security guarantee. Unknown or stale information cannot silently produce an all-clear status. |

The full stories and detailed acceptance criteria live in [BACKLOG.md](BACKLOG.md).
The local IDs map to SCRUM-5 through SCRUM-9 in the backlog.

## Implementation boundaries and metric proposal

Use a small, independently runnable dashboard module with local synthetic data.
The first increment must work without starting Device, Gateway or Cloud. Keep
the existing prototype available as a separate educational demonstration.
Live monitoring, automatic blocking, authentication, complex scoring, databases
and protocol/security redesign are outside this increment's agreed scope.

Implemented prototype calculation, pending team/PO review: coverage = PQC connection segments /
all in-scope connection segments, including unknown segments. Display the
numerator, denominator, snapshot time and segment unit alongside the percentage.
Zero records means coverage unavailable, not 100%. The 24-hour per-observation
freshness rule, historical/current clocks and overall-status precedence were
recorded before implementation in D-04 of the decision log. Empty,
missing, invalid or stale data must be visibly distinguishable from a healthy
known dataset. These rules describe reporting, not cryptographic assurance.

The existing device path uses preconfigured symmetric keys with
ChaCha20-Poly1305. Its `fallback` log message alone does not establish the
classical-key-exchange/HNDL assumptions in the course scenario. Synthetic data
must state those assumptions explicitly; see the decision log.

## Build sequence and evidence

1. Confirm data contract and worked examples; record assumptions and estimates.
2. Generate the dataset, overview and connection list using an LLM; retain the
   prompt/context and output references in the LLM evaluation record.
3. Add the three views and explanations. Use a single source of data and metric
   calculations so views reconcile.
4. Verify arithmetic against hand-worked expectations and exercise filtering,
   unknown, empty, missing/invalid and stale-data behavior as applicable.
5. Run the dashboard and walk through all three roles in the browser. Record
   commands, expected/observed behavior, evidence location and unresolved issues.
6. Update the story matrix and README with only verified behavior. Ask the team
   to assess the increment and obtain PO feedback during the actual review.

Acceptance demonstration: open the dashboard, explain the coverage denominator,
filter fallback records, inspect a reason and exposure assumption, then switch
to the migration and executive views to explain a blocker and required action.

Definition of Done: each story's criteria are met; generated changes have been
reviewed; appropriate checks pass; a runtime/UI walkthrough is recorded;
definitions and startup instructions match the implementation; remaining risks
and human acceptance status are explicit. Tests alone do not establish UI or
stakeholder acceptance. Only checks explicitly recorded in the verification
record establish this increment's observed behavior.

## Subagent workflow during construction

For each implementation batch, the integrating agent assigns bounded subagent
tasks with exclusive file ownership. Subagents maintain these artifacts using
the actual batch's changes and evidence:

| Artifact | Subagent responsibility | Update trigger |
| --- | --- | --- |
| [Backlog](BACKLOG.md) | Draft/refine Jira-ready stories, acceptance criteria and evidence links | Planning, scope change, implementation and verification results |
| [Risk and decision log](RISK_AND_DECISION_LOG.md) | Reassess risks; record alternatives, decisions, authority and residual risk | New assumption, requirement conflict, defect or PO feedback |
| [LLM evaluation](LLM_EVALUATION.md) | Trace prompt/output, review findings, decisions, fixes and verification | Every significant AI-generated code/document batch |
| [Retrospective actions](RETROSPECTIVE_ACTIONS.md) | Record actual retrospective findings and follow-up actions | Actual retrospective, then the next sprint's follow-up |

The integrating agent reconciles cross-file claims, reviews the final diff,
checks links and verifies the assembled increment. Subagent completion is not
integration completion. Update the root README and relevant component/project
instructions in the same batch whenever scope, startup, verification or known
limitations change. Use English for repository documentation.

Keep the local-to-Jira mapping current in BACKLOG.md when the team reports
verified changes. Preserve the distinction between local edits and remote Jira
updates. Student team
members supply actual membership, estimates, Scrum Master rotation, meeting
outcomes and acceptance decisions; AI draft authorship does not supply them.

## Sprint submission checklist

- [x] Five student names supplied by the user and recorded in TEAM_REVIEW.md and submission covers.
- [x] Record the current Sprint 1 work allocation in [TEAM_REVIEW.md](TEAM_REVIEW.md).
- [ ] Confirm the Scrum Master proposal, rotation and working agreement with the team; record past contributions separately.
- [ ] Product vision and stakeholder needs/conflicts reviewed by the team.
- [x] Sprint Goal, five stories and five process tasks saved in Jira; six dependencies verified by the user.
- [ ] Confirm priorities, formal estimates and assignees; enter actual Sprint dates and agree the Jira Sprint start.
- [x] Working dashboard increment exercised with model tests and browser evidence; group review reported held, with outcomes and acceptance pending.
- [x] Planned versus implemented scope documented in the report draft.
- [x] Initial risk, decision and LLM evaluation records prepared with technical checks.
- [ ] Add the team's conclusions on risk changes, decisions and LLM output quality.
- [ ] Recover the reported review's date, attendance, feedback and acceptance; record an actual retrospective and track agreed actions for Sprint 2.
- [x] Report draft and gallery with six dashboard screenshots prepared locally.
- [ ] Review and export the approximately 500-word report and export the dashboard images as one PDF.
- [ ] Prepare slides, record the video (at most five minutes), export the slides used as PDF and submit all four items.

## Change record

| Event | Authority/evidence | Result at that stage |
| --- | --- | --- |
| Initial scope recorded | User accepted the five-feature Sprint 1 proposal in chat | Goal, Jira-ready backlog and initial process records created; implementation, team review, Jira transfer and course submissions pending |
| First build integrated | User instructed construction; model/UI subagents and process-record subagent worked under exclusive ownership | Five features implemented; 11 model tests and browser scenarios observed; see verification. Human acceptance, Jira transfer, actual review/retrospective and course submissions pending |
| Submission Markdown drafted | User requested screenshots and editable report/gallery before their own PDF export | Six fresh screenshots and two Markdown sources prepared; human review and export pending |
| Team register and review prepared | User supplied five member names and requested review/completion | Membership confirmed; technical/material review and student walkthrough questions prepared in TEAM_REVIEW.md; actual student feedback, roles and acceptance await evidence |
| Review occurrence clarified and roles allocated | User confirmed a prior review without saved minutes and delegated allocation | Prior review recorded as user-reported; prospective owners/SM rotation and discussion candidates prepared; actual meeting details and member acknowledgement pending |
| Jira entry confirmed | User confirmed saved goal and checked all ten records, order, statuses and six dependency links in the [Group 22 Backlog](https://tacczy.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog) | SCRUM-5 through SCRUM-9 In Review; SCRUM-10 through SCRUM-14 To Do; Sprint unstarted and undated; estimates, assignees and acceptance pending |
| Work allocation updated | User supplied the revised five-person split | TEAM_REVIEW.md records current responsibilities; individual Jira assignees and Scrum Master confirmation remain separate |
