# Sprint 1 backlog: Jira-ready local draft

Baseline: 8 November 2026. Scope authority: [Sprint goal](SPRINT_GOAL.md).
All dashboard stories are **Implemented; AI checks passed; human acceptance
pending**. This file records local build progress, not completed Jira updates. Local IDs below are not Jira keys.
Prospective owners below are allocated under the user's delegation, with member
acknowledgement pending. Actual estimates and teacher/Product Owner acceptance
remain unconfirmed.

The user has supplied the five-person roster, recorded in
[TEAM_REVIEW.md](TEAM_REVIEW.md). Membership and prospective allocations are recorded; acknowledgement, actual
contributions and review sign-off still require the members' confirmation. The
user reports that a group review was held but its original record was not saved.
Date, actual attendees, feedback and acceptance decision remain unconfirmed.
The material review there supplies separately identified evidence for discussion,
not a reconstruction of missing member opinions.
The independent material reviewer reran 11/11 model tests and reconciled the
fixture and sampled screenshot captions; this refreshes technical evidence
without changing the pending human acceptance or remote Jira status.

The existing Device/Gateway/Cloud prototype provides background only. The
increment must run independently using synthetic data.

## Prioritized stories

Story points below are provisional relative-size suggestions (1, 2, 3, 5 scale),
not hours or team commitments. Confirm estimates and ordering in actual planning.
All five stories are required for the accepted Sprint 1 increment; the priority
column gives the suggested implementation order.

| Local ID | Summary | Priority/order | Proposed points | Dependencies | Status | Jira key | Prospective owner; acknowledgement pending |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1-US-01 | Load a fixed synthetic connection dataset | Must / 1 | 3, unconfirmed | Schema v1 build contract | Implemented; AI checks passed; human acceptance pending | Unassigned | Valerii Lebedev |
| S1-US-02 | Show reconciled connection coverage totals | Must / 2 | 2, unconfirmed | S1-US-01 | Implemented; AI checks passed; human acceptance pending | Unassigned | Valerii Lebedev |
| S1-US-03 | Inspect and filter connection segments | Must / 3 | 3, unconfirmed | S1-US-01 | Implemented; AI checks passed; human acceptance pending | Unassigned | Jinghao Lei |
| S1-US-04 | Present the same data for three stakeholder roles | Must / 4 | 5, unconfirmed | S1-US-02, S1-US-03, S1-US-05 rules | Implemented; AI checks passed; human acceptance pending | Unassigned | Jinghao Lei |
| S1-US-05 | Explain indicators and their interpretation limits | Must / rules before UI, finish with 4 | 3, unconfirmed | S1-US-01 contract; D-03/D-04 prototype rules | Implemented; AI checks passed; human acceptance pending | Unassigned | Cheng Peng |

### S1-US-01: Fixed synthetic connection dataset

As a dashboard user, I want a repeatable synthetic snapshot so that I can
understand and verify the demonstration without operating live services.

Acceptance criteria:

1. A local JSON fixture contains examples of PQC, expected classical fallback
   and unknown connection status. Repeated loads yield the same records.
2. Each record has a unique connection ID, device/asset identifier, connection
   segment (`device-to-gateway` or `gateway-to-cloud`), key-establishment method,
   status, classification reason and observation time. Applicable fallback
   reasons, migration blockers and confidentiality-lifetime assumptions are
   explicit; unknown values are represented explicitly rather than guessed.
3. The fixture distinguishes expected fallback from a suspected downgrade
   scenario; any suspicion is a synthetic scenario classification with a reason,
   not a conclusion derived merely from using classical cryptography.
4. The UI labels the dataset synthetic and displays its snapshot time. It loads
   without starting Device, Gateway or Cloud or using real credentials.
5. Missing, malformed or unsupported records produce a visible data-quality
   error/unknown indication, not an apparently healthy empty dashboard. Invalid
   input handling and any exclusions are explained and recorded.

Planned evidence: fixture path, schema/validation rules, hand-worked snapshot
counts and load/error walkthrough. Evidence: implementation and parent-observed AI checks recorded in [VERIFICATION.md](VERIFICATION.md); human acceptance pending.

### S1-US-02: Overview totals and coverage

As Michael, I want coverage numbers with a visible denominator so that I can
explain migration progress and its remaining uncertainty.

Acceptance criteria:

1. Overview shows total in-scope connection segments, PQC count and share,
   fallback count and unknown count using one shared snapshot.
2. For valid records, total = PQC + fallback + unknown. Coverage is PQC / total;
   unknown segments remain in the denominator. The UI states the segment unit,
   numerator, denominator and rounding convention.
3. Hand-worked fixture expectations match the displayed results. For example,
   a test snapshot with 3 PQC, 1 fallback and 1 unknown yields total 5 and 60%
   coverage. This is a calculation example, not a claim about an existing fixture.
4. Zero records yields unavailable coverage, not 100%; missing/invalid input is
   distinguished from a valid zero-record snapshot.
5. Overview counts reconcile with the full connection list. If list filtering
   leaves global cards unchanged, label them as all connections and show the
   filtered row count separately. Any alternate filter behavior must be explicit.

Planned evidence: arithmetic checks including unknown and zero denominators,
reconciliation results, browser capture. Evidence: implementation and parent-observed AI checks recorded in [VERIFICATION.md](VERIFICATION.md); human acceptance pending.

### S1-US-03: Connection list and status filter

As Sarah, I want to inspect the connections behind each count so that I can
identify exposure and determine which records require investigation.

Acceptance criteria:

1. The list displays connection ID, device/asset, segment, key-establishment
   method, status, reason and observation time; relevant fallback/exposure
   context is accessible in the row or its details.
2. A status filter provides All, PQC, Fallback and Unknown. Each selection shows
   exactly the matching records and a matching row count. Returning to All
   restores the complete valid snapshot.
3. A filter with no matching records shows an explicit empty-result message.
4. A PQC gateway-to-cloud segment does not label the corresponding
   device-to-gateway segment or complete device path PQC.
5. Status and reasons are readable as text, not only conveyed by color.

Planned evidence: expected record IDs for every filter, empty-result exercise,
segment distinction and UI walkthrough. Evidence: implementation and parent-observed AI checks recorded in [VERIFICATION.md](VERIFICATION.md); human acceptance pending.

### S1-US-04: Three basic stakeholder views

As a security officer, migration manager or CIO, I want a view supporting my
decisions while keeping the underlying facts consistent across roles.

Acceptance criteria:

1. Tabs or sections provide Sarah (security), Michael (migration) and Emma
   (executive) views, all derived from the same dataset and calculations.
2. Sarah can locate non-PQC/unknown connections, inspect exposure assumptions
   and reasons, and distinguish expected fallback from synthetic investigation
   candidates. This increment proposes investigation, not automated blocking.
3. Michael can see coverage/progress, remaining connections and migration
   blockers with explanations. Unknown blockers remain visibly unknown.
4. Emma can see an overall status with its rule/reason and up to three relevant
   risks with business implications. The status rule is recorded before coding
   and unknown/stale data cannot silently yield an all-clear state.
5. Switching roles preserves agreement on totals and connection facts. A
   basic walkthrough can explain a fallback reason, migration blocker and
   management concern without relying on specialist cryptography knowledge.

Planned evidence: all three views exercised in a running browser; expected and
observed answers for the role walkthrough; human feedback separately recorded.
Evidence: parent-observed role walkthrough in [VERIFICATION.md](VERIFICATION.md). Human acceptance: pending.

### S1-US-05: Definitions, time and interpretation limits

As a dashboard user, I want understandable indicator definitions and limits so
that I can use the prototype without mistaking progress for security assurance.

Acceptance criteria:

1. Accessible explanations define coverage, fallback, HNDL exposure, unknown
   status, snapshot time and the classification assumptions used by this fixture.
2. HNDL is described as potential exposure under stated assumptions, not a
   detected attack count. Classical fallback alone is not proof of a downgrade
   attack; expected fallback and suspected downgrade are differentiated.
3. Migration/coverage measures are not presented as guarantees of system
   security, and a protected segment is not presented as an end-to-end guarantee.
4. A documented freshness threshold/rule is selected for the prototype before
   implementation and submitted for team/PO review (D-04). Data that is unknown, missing, invalid or stale is visibly
   distinguishable from current known data; an all-clear requires sufficient
   evidence under the stated rule. A fixed historical demo is labelled accordingly.
5. The course's synthetic classical-key-exchange scenario is distinguished
   from the existing prototype's preconfigured symmetric-key device path.

Planned evidence: wording review, stale/unknown examples, documented status and
freshness rules, browser verification. Evidence: implementation and parent-observed AI checks recorded in [VERIFICATION.md](VERIFICATION.md); human acceptance pending.

## Process tasks accompanying the stories

These local task IDs may be transferred to Jira alongside stories. Process-log
maintenance and AI output evaluation are in progress; actual planning evidence, review minutes/decisions,
retrospective and submission remain pending. No task has a remote issue key. The user-delegated prospective allocation is
recorded in TEAM_REVIEW.md; it does not document past contributions or member
acknowledgement.

| Local task | Proposed work | Completion evidence |
| --- | --- | --- |
| S1-T-01 | Team planning: confirm roles, working agreement, estimates and Sprint goal | Actual attendees/date, decisions and assigned work; team/PO feedback recorded |
| S1-T-02 | Maintain [risks and decisions](RISK_AND_DECISION_LOG.md) | Dated updates identifying authority, rationale, residual risks and follow-up |
| S1-T-03 | Evaluate significant LLM outputs in [LLM evaluation](LLM_EVALUATION.md) | Prompt/output references, findings, decisions, fixes, checks and remaining risks |
| S1-T-04 | Review integrated increment and conduct actual retrospective | Runtime demonstration and team/PO feedback; [retrospective actions](RETROSPECTIVE_ACTIONS.md) with owners and follow-up |
| S1-T-05 | Prepare Sprint submission from actual evidence | 500-word report, 5-minute video and the slides used in the video as PDF; working increment reference |

## Definition of Done and current evidence

A story is ready for team acceptance only when every acceptance criterion has
evidence, generated changes have been reviewed, appropriate checks pass and the
integrated dashboard has been exercised in a browser. Verify arithmetic,
unknown/empty/invalid inputs and relevant status/freshness behavior against known
expectations. Record the launch steps, expected and observed UI behavior and
remaining limitations. README/startup instructions and related process records
must match the implementation.

Subagent completion and automated tests do not establish integrated UI success
or stakeholder acceptance. Record team/teacher acceptance separately with actual
feedback. All five stories have implementation and parent-observed AI check evidence in
[VERIFICATION.md](VERIFICATION.md); **human acceptance is pending**. This does
not mark stories Done in Jira or establish student/PO acceptance.

## Transfer to Jira and ongoing maintenance

1. Obtain the actual course Jira project key and board from the student team.
   No remote Jira connection or synchronization has been performed for this file.
2. Copy each story's summary, role/need, acceptance criteria, dependencies and
   local ID into a Jira story. Keep estimates provisional until team planning;
   assign real team members through the team's normal process.
3. If using Jira import, map fields against that project's actual import schema;
   this Markdown file is a copy-ready draft, not a validated CSV import payload.
4. Record the returned issue key against the local ID, link dependencies and add
   the actual Sprint assignment. Preserve local IDs for traceability.
5. During each build batch, a bounded backlog subagent updates verified evidence
   and proposed changes here. The integrating agent reconciles these with the
   [goal](SPRINT_GOAL.md), logs and README before changing completion claims.
6. After an actual remote update, record the issue URL/key, date and resulting
   state. Keep Planned, Implemented, Verified and Accepted distinct; do not mark
   a Jira issue done solely because this document or a subagent task is finished.

## First implementation batch: implemented, awaiting human acceptance

The user instructed construction from the approved goal. The integrating agent
delegated model/fixture/tests to `dashboard_model`, UI to `dashboard_ui`, and
these process records to `build_records`, with exclusive file ownership. See
[build prompts](BUILD_PROMPTS.md) for request and delegation provenance.

- Implemented model and fixture: `dashboard/model.mjs`,
  `dashboard/fixtures/snapshot.json`; schema v1 and the recorded D-03/D-04 rules.
- Implemented UI: `dashboard/index.html`, `dashboard/styles.css`,
  `dashboard/app.mjs`; one shared snapshot, role views, filtering, local JSON
  loading and explicit historical/current-time clock choice.
- Parent independently ran `node --test dashboard/tests/model.test.mjs`: 11/11
  passed; model/app syntax checks passed. Local HTTP returned 200 and the
  parent performed the running-browser checks summarized below.
- Known fixture expectation: eight segments = five PQC + two fallback
  (one expected, one suspected) + one unknown; coverage 62.5%. Parent observed
  these values in the running UI; fixture counts and calculations were checked
  separately.

The user subsequently reported a group review was held; no retained minutes or
confirmed date/attendees/decisions are available. This implementation batch does
not supply those missing facts or imply a remote Jira operation.

### Parent-observed AI verification by story

| Story | Observed checks | Remaining acceptance boundary |
| --- | --- | --- |
| S1-US-01 | Fixed fixture loads over local HTTP; malformed JSON and invalid schema rejected; invalid input after a green dataset clears old metrics, role content and rows; reset restores default | Synthetic scenarios only; student/PO review pending || Valerii Lebedev |
| S1-US-02 | Default 8 = 5 + 2 + 1 and 62.5%; empty means unavailable; unknown-only gives 0%; all-PQC gives 100%; filters leave global summary unchanged | Coverage is segment migration, not security assurance || Valerii Lebedev |
| S1-US-03 | Fallback returns SEG-001/SEG-007 (2/8), unknown SEG-008 (1/8), PQC 5/8, All 8/8; nonexistent search gives explicit empty result; context and segment labels inspected | No live monitoring or automatic blocking || Jinghao Lei |
| S1-US-04 | Sarah expected/suspected/unknown context, Michael 5-of-8 with blockers, Emma RED Investigate with exactly three risks including business impact/actions | AI browser walkthrough is not student usability evaluation || Jinghao Lei |
| S1-US-05 | Definitions and both clocks inspected; one stale PQC row can display 100% coverage while overall is UNKNOWN; all-PQC green is qualified; HTML-looking reason displays literally without creating images | Rules remain prototype choices awaiting team/PO review || Cheng Peng |

No browser error/warning logs were observed. At a 390-pixel viewport, measured
page width had no page overflow and the table scrolled horizontally with controls
visible. The mobile full-page screenshot capture failed; complete mobile visual
validation is not claimed. Desktop screenshot and detailed checks are referenced
in [VERIFICATION.md](VERIFICATION.md).
