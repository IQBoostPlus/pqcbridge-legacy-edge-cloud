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
Student/PO acceptance and course submissions remain separate from implementation.

## Committed dashboard scope

| Local story | Increment | Observable acceptance |
| --- | --- | --- |
| S1-US-01 | Fixed synthetic dataset covering PQC, classical fallback and unknown connection states | Repeat loads produce the same data; the UI labels it synthetic and shows its snapshot time. Data identifies each connection segment, algorithm/key-establishment method, device, fallback reason, migration blocker and any confidentiality-lifetime assumption used in exposure explanations. |
| S1-US-02 | Overview showing total connections, PQC count/share, fallback count and unknown count | Summary and list reconcile. The denominator and units are visible. Unknown records remain in the total and never become protected records by default. |
| S1-US-03 | Connection list and status filter | Each row identifies the connection, device, segment (device-to-gateway or gateway-to-cloud), key-establishment method, status and reason. Filtering returns the matching records and supports an empty result. A PQC gateway-to-cloud segment does not label the whole device path PQC. |
| S1-US-04 | Basic Sarah / Michael / Emma views | Tabs or sections reuse the same dataset. Sarah can identify exposure and investigation candidates with reasons; Michael can see migration progress and blockers; Emma can see an explained overall status and up to three relevant risks. |
| S1-US-05 | Definitions and interpretation limits | Explain coverage, fallback, HNDL exposure, data time and classification assumptions. Expected fallback is distinguishable from a suspected downgrade. Exposure is not a detected HNDL attack; migration completion is not a security guarantee. Unknown or stale information cannot silently produce an all-clear status. |

The full stories and detailed acceptance criteria live in [BACKLOG.md](BACKLOG.md).
These IDs are local identifiers, not Jira issue keys.

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

Jira-ready drafts are local until a real Jira project/issue mapping is available.
Record actual issue keys and synchronization state when transferred. Preserve
the distinction between local edits and remote Jira updates. Student team
members supply actual membership, estimates, Scrum Master rotation, meeting
outcomes and acceptance decisions; AI draft authorship does not supply them.

## Sprint submission checklist

- [x] Five student names supplied by the user and recorded in TEAM_REVIEW.md and submission covers.
- [ ] Confirm the prospective Scrum roles/rotation and working agreement in TEAM_REVIEW.md; record past contributions separately.
- [ ] Product vision and stakeholder needs/conflicts reviewed by the team.
- [ ] Stories estimated/prioritized by the team and tracked in Jira.
- [x] Working dashboard increment exercised by integrating AI with runtime evidence (actual Sprint review/team acceptance pending).
- [ ] Planned versus completed scope and changes explained.
- [ ] Risks, decisions and significant LLM outputs evaluated.
- [ ] Recover the reported review's date, attendance, feedback and acceptance; record an actual retrospective and track agreed actions for Sprint 2.
- [ ] Report draft prepared from evidence in `submission/Sprint1_Report.md`; student review and PDF export pending.
- [ ] Six dashboard images assembled in `submission/Sprint1_Dashboard_Images.md`; student review and PDF export pending.
- [ ] 5-minute video and the slides used in it exported as PDF.

## Change record

| Event | Authority/evidence | Result |
| --- | --- | --- |
| Initial scope recorded | User accepted the five-feature Sprint 1 proposal in chat | Goal, Jira-ready backlog and initial process records created; implementation, team review, Jira transfer and course submissions pending |
| First build integrated | User instructed construction; model/UI subagents and process-record subagent worked under exclusive ownership | Five features implemented; 11 model tests and browser scenarios observed; see verification. Human acceptance, Jira transfer, actual review/retrospective and course submissions pending |
| Submission Markdown drafted | User requested screenshots and editable report/gallery before their own PDF export | Six fresh screenshots and two Markdown sources prepared; human review and export pending |
| Team register and review prepared | User supplied five member names and requested review/completion | Membership confirmed; technical/material review and student walkthrough questions prepared in TEAM_REVIEW.md; actual student feedback, roles and acceptance await evidence |
| Review occurrence clarified and roles allocated | User confirmed a prior review without saved minutes and delegated allocation | Prior review recorded as user-reported; prospective owners/SM rotation and discussion candidates prepared; actual meeting details and member acknowledgement pending |
