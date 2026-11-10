# Sprint 1 LLM output evaluation

This is a traceability record for AI-generated work, not a completed student
assessment. The first dashboard increment is implemented with parent-observed
AI test and browser evidence; student/PO acceptance remains pending. Refer to the
[Sprint goal](SPRINT_GOAL.md), [backlog](BACKLOG.md) and
[risk/decision log](RISK_AND_DECISION_LOG.md).

## Significant interaction register

### AI-S1-001: approved scope and process-document drafts

| Field | Recorded evidence / state |
| --- | --- |
| Request | The user accepted the five-feature Sprint 1 proposal, requested a Sprint goal record, delegated preparation of Jira stories/acceptance criteria, initial risk/decision logs, LLM evaluation and retrospective actions, and ongoing README/project-instruction updates during construction |
| Prompt/context reference | Project chat containing that request, the preceding five-feature proposal and delegated task instructions; no external archive of the full chat has been created by this document |
| Context consulted | Existing CLAUDE.md and SPRINT_GOAL.md; course requirements previously read in the parent chat; current implementation state supplied by the integrating agent |
| Output references | SPRINT_GOAL.md, BACKLOG.md, RISK_AND_DECISION_LOG.md, LLM_EVALUATION.md, RETROSPECTIVE_ACTIONS.md and root README/CLAUDE updates; file/link existence checked during integration |
| Author / evaluator | Parent AI authored the goal and README/CLAUDE updates; sprint1_backlog subagent authored BACKLOG.md; sprint1_process subagent authored the three process logs. Parent AI completed integration review; student evaluator unassigned |
| Draft-review observations | User scope approval must stay distinct from teacher/PO approval; metric/color proposals require review; local story IDs must stay distinct from Jira keys; implementation and human meetings must remain pending |
| Decision | Retain as local planning drafts subject to integrating and student review; no claim of completed student evaluation |
| Verification | Parent AI read all five Sprint records and the README/CLAUDE changes, checked the five story IDs and scope/status consistency. A local check passed for seven documents, 23 relative file links, five required records, five story sections and trailing whitespace; git diff --check also passed. No product code or dashboard runtime was tested; student evaluation remains pending |
| Changes made in draft | Explicit pending states, provisional risk estimates/owners, unapproved status rules and synthetic-data interpretation boundaries added |
| Remaining risk | Source-chat trace is not a standalone prompt archive; student ownership, Jira mapping and PO acceptance were unconfirmed at this planning stage; wording review cannot establish dashboard behavior |

Integration review retained the explicit pending implementation/Jira/meeting
states and the proposed status/freshness rules. The parent updated provenance
and verification after checking the assembled records. A student's evaluation
must identify the student and their actual assessment separately.

### AI-S1-002: first dashboard implementation batch

| Field | Recorded evidence / state |
| --- | --- |
| Request | User instructed construction from the approved goal; exact original request and build delegation references are retained in [BUILD_PROMPTS.md](BUILD_PROMPTS.md) |
| Context | CLAUDE.md, SPRINT_GOAL.md, five backlog stories and initial process records; independently runnable fixed synthetic-data dashboard |
| Author / evaluator | dashboard_model AI subagent owns model, fixture and model tests; dashboard_ui AI subagent owns HTML/CSS/app; build_records AI subagent owns these four process records; parent AI integrates and verifies. Student evaluator unassigned |
| Output references | dashboard/model.mjs, dashboard/fixtures/snapshot.json, dashboard/tests/model.test.mjs, dashboard/index.html, dashboard/styles.css, dashboard/app.mjs; parent-owned startup/project docs and verification record |
| Build choices | D-03: all-segment coverage including unknown; D-04: historical demo clock, optional current time, 24-hour per-observation freshness and explicit status precedence; D-07: reject invalid snapshot rather than silently omit rows |
| Expected results | Fixed fixture: 8 total, 5 PQC, 2 fallback (1 expected / 1 suspected), 1 unknown; 62.5% coverage; suspected downgrade yields red while unknown remains separately visible |
| Review findings to address | Keep crypto assumptions separate from original symmetric-key prototype; pinned clock must be visibly historical; stale/unknown/invalid/empty data must not produce all-clear; generated text must remain text when rendered; role views must reconcile |
| Independent AI source review | build_records read model.mjs, fixture, app.mjs, index.html and dashboard README. No actionable metric/domain mismatch identified: unknown stays in denominator, fixture separates expected/suspected fallback and mixed segments, UI uses shared summary/textContent, and invalid input clears prior presentation. This source review does not establish browser success |
| Decision / authority | Build this bounded local prototype under the user's instruction; selected metric/status rules remain subject to human team/PO review. No human usability evaluation is claimed |
| Verification | Parent independently ran 11/11 passing model tests plus passing app/model syntax checks; local HTTP returned 200. Parent browser walkthrough observed default 8/5/2/1 and 62.5%, all roles, exact filters, empty search, both clocks, definitions, local data errors/reset, empty/unknown-only/stale/all-PQC scenarios and literal rendering of HTML-looking data. Detailed evidence: [VERIFICATION.md](VERIFICATION.md) |
| Remaining risk | Jira mapping and human acceptance were outstanding at the end of the build; fixture assumptions and AI-authored tests cannot establish real monitoring or cryptographic assurance |

The parent supplied actual check results for this entry. The initial model-test
run exposed an incorrect search expectation; that expectation was corrected and
the parent independently reran all 11 tests successfully. This was a test-oracle
correction, not an implementation defect. No actionable source-review domain
mismatch was identified by the build-records AI. Browser error/warning logs were
empty. A desktop screenshot was saved; narrow-screen geometry showed no page
overflow and a scrollable table, but mobile full-page screenshot capture failed.
Complete mobile visual validation and human acceptance remain open. Significant
prompts and follow-up instructions belong in the build prompt record, rather
than being replaced by an outcome summary. The parent stopped the QA server
after testing. HTTP 200 refers to the dashboard page; an incidental favicon 404
was observed and does not imply every requested resource returned success.

Final assembled documentation/source checks passed: local Markdown links,
referenced HTML assets, duplicate HTML IDs, trailing whitespace and
`git diff --check`. These are consistency checks, separate from the browser
and model evidence above.

### AI-S1-003: supplementary screenshots and submission-source drafts

| Field | Recorded evidence / state |
| --- | --- |
| Request / prompt reference | The current project chat contains the user's screenshot-supplement and report/dashboard-images preparation request, followed by the current Markdown-only artifact direction. Exact user/task messages remain in that chat; the descriptions here summarize their scope |
| Context | Existing goal, backlog, risk/decision log, LLM evaluation, retrospective record and historical build verification; no new dashboard features requested |
| Author / evaluator | sprint_report AI subagent drafts the report; parent AI captures the running dashboard and composes the screenshot gallery; submission_records AI subagent maintains this entry and verification record. Student evaluator unassigned |
| Outputs | Local report draft and gallery (`submission/Sprint1_Report.md`, `submission/Sprint1_Dashboard_Images.md`) and six JPEG captures under `submission/images/`; existing PNG evidence preserved |
| Evaluation criteria | Approximately 500 report words; statements grounded in existing records; distinguish local Jira-ready stories from remote Jira activity; preserve pending human evaluation, PO approval, review and retrospective; match gallery captions to visible screenshots |
| Decision | Prepare reviewable Markdown sources and supplementary screenshots in this batch. PDF export and human review remain pending; no PDF rendering or completion claim is made |
| Verification | Parent observed and captured overview, security, migration, executive, fallback-inventory and definitions views in the running browser, and visually inspected the captures. This records agent evidence rather than student acceptance. The report body contains 501 whitespace-delimited words excluding headings; six gallery image targets exist. Supplementary details are in VERIFICATION.md. Historical model/browser checks in AI-S1-002 are not new tests for this artifact-preparation batch |
| Remaining risk | The report can reflect confirmed Jira entry and still requires evidence for earlier Scrum participation. Exported layout, course-process completeness and human acceptance require separate work |

No dashboard code change or new product test result is asserted by this entry.
The earlier build evidence remains historical and unchanged. The parent supplied
actual screenshot observations; the record-maintenance subagent independently
checked the report word count and the gallery image file references. The six
new image files have JPEG signatures. Gallery captions distinguish synthetic
scenarios from real attacks, and the draft at that stage preserved the pending Jira and meeting
states. Human content evaluation and PDF export/layout validation remain pending.
The parent confirmed all six JPEGs decode and the temporary capture server was
stopped. The two updated evidence records passed local link/whitespace checks
and `git diff --check`.

### AI-S1-004: supplied roster and material review for the team

| Field | Recorded evidence / state |
| --- | --- |
| Request / source | In the current project chat, the user supplied Changzhengyuan Chu, Valerii Lebedev, Jinghao Lei, Cheng Peng and Zhizhou Zhao as the team roster and requested review, missing material completion and remaining supplements |
| Subsequent clarification | The user reports that group review occurred but its original record was not saved, and delegates allocation of members and preparation of discussion opinions. Forward roles and confirmation-ready discussion candidates are recorded separately; no missing historical opinion, attendee or acceptance decision is invented |
| Context | Existing Sprint goal, implemented dashboard, verification record, report/image Markdown sources and process records; membership is user-supplied, not inferred from code or AI activity |
| Author / evaluator | Parent AI integrates TEAM_REVIEW.md and project-material updates; material_review AI subagent performed independent assessment; build_records AI subagent updates the four process records. Actual human evaluator identity, attendance and opinions remain unconfirmed |
| Outputs | [TEAM_REVIEW.md](TEAM_REVIEW.md) is the roster and evidence-based material review for team consideration; backlog, risk/decision log, this evaluation and retrospective action states are updated |
| Evaluation criteria | Record the known roster; preserve unknown roles, contributions, meeting facts and sign-off; distinguish AI assessment from student/PO acceptance; reconcile missing-material claims with actual artifacts; retain original build evidence as historical |
| Decision | Prepare reviewable team material and prospectively allocate responsibilities under the user's explicit delegation. D-09 distinguishes those assignments from unverified past contributions. R-09/D-08 preserve the boundary between supplied membership, reported review occurrence and missing review evidence; discussion candidates await member confirmation |
| Verification | material_review independently reran 11/11 passing model tests in this batch and checked fixture totals 8 = 5 + 2 + 1, six gallery image targets and executive/fallback screenshot-caption agreement. No actionable defect within the synthetic scope was identified. Parent integrated the roster, prospective roles, confirmation-ready discussion candidates and review outcome in TEAM_REVIEW.md, and checked Markdown links/names/whitespace. No new browser walkthrough, human finding or remote Jira result is asserted |
| Remaining work | Prospective role acknowledgement, actual contributions, review date/attendees/opinions, acceptance decisions and the course submission/export gaps require real information; Jira mapping was confirmed in the subsequent handoff. The reported review does not establish a retrospective; final scope follows the parent-integrated material review |

The earlier browser walkthrough remains historical; the independent 11/11 model
test rerun above is new evidence in this material-review batch. The reviewer
checked the report before the parent's subsequent review-context wording update;
the integrating parent checks the final report body separately. The
roster has been linked from the backlog, risk log and retrospective record;
pending role acknowledgement and human action agreement remain intact. RA-S1-01
through RA-S1-03 now display the implementation/AI evidence already recorded,
instead of obsolete "execution/dashboard pending" states. RA-S1-04 still
requires actual student participation.

build_records read the team's review record and submission cover roster for
consistency at that review stage. The roster and initial responsibility
proposals were available, while past contributions, meeting particulars and
member opinions were unconfirmed. See TEAM_REVIEW.md for the current allocation. The per-member discussion candidates in TEAM_REVIEW.md are prepared
for confirmation, not attributed historical quotations or accepted decisions.
The current review retains the known mobile/process/PO validation limits and
does not close related risks. No product code was changed by these record edits.

## AI-S1-005: Jira handoff and repository reconciliation

The browser GPT received a prompt with the Sprint Goal, five user stories, five
process tasks, acceptance criteria and instructions to preserve existing entries.
The user confirmed that it saved the goal in SCRUM Sprint 1, then verified the
ten new items and six dependency links in the [Group 22 Backlog](https://tacczy.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
Earlier entries describe the state at the time of their respective batches.
The current mappings and statuses are in [BACKLOG.md](BACKLOG.md).

The handoff distinguishes reported technical verification (stories In Review)
from outstanding process work (tasks To Do). Formal estimates and assignees,
actual Jira Sprint dates, team/PO acceptance and retrospective outcomes remain
open. [SCRUM-12](https://tacczy.atlassian.net/browse/SCRUM-12) tracks the team's evaluation of significant LLM outputs.
The documentation reconciliation uses the user's confirmed browser results.
It adds no new product test or direct Jira inspection.

### AI-S1-006: Vue dashboard replacement

| Field | Recorded evidence / state |
| --- | --- |
| Request and source | The user authorized the interface replacement from [zerphy799/pqc-dashboard-vue at f95f684](https://github.com/zerphy799/pqc-dashboard-vue/commit/f95f684d3f81abd7aff7a8423dd6978c143b098c). The request is recorded in the current project chat |
| Work and ownership | The parent agent integrates the Vue source into `dashboard/`. The build_records subagent maintains the four Sprint process records. D-11 records the selection and R-10 tracks regression risk |
| Evaluation scope | Check the integrated build against S1-US-01 through S1-US-05, including the fixture totals and unknown denominator, connection filters, role views, freshness and invalid-input behavior, and the interpretation of fallback and HNDL exposure |
| Verification | Dependency install, production build and 12 model tests passed. A later isolated Chromium walkthrough exercised routes, filters, local JSON and reset. A Windows preview MIME mismatch and narrow-screen filter alignment issue were resolved. See [VERIFICATION.md](VERIFICATION.md) for screenshots and the verification boundary |

## Evaluation checklist for each implementation batch

The earlier report revision counted 486 whitespace-delimited words. The
current count is kept in the local report's reviewer notes. Prepared discussion
candidates remain outside the report's factual account until confirmed.

Before merging a generated batch into the increment, record its local story IDs,
prompt/context location, generated output paths, evaluator and findings. Preserve
the prompt or an accessible exact transcript reference in addition to a summary.

The evidence below covers the first interface. AI-S1-006 tracks the Vue
replacement separately.

| Evaluation area | Expected evidence | Current state |
| --- | --- | --- |
| Scope and provenance | Generated files map to accepted stories; source/prompt and author are traceable | Five stories implemented; BUILD_PROMPTS.md holds provenance |
| Domain interpretation | HNDL exposure is not an attack count; expected fallback differs from suspected downgrade; connection segments remain explicit | Separate AI source review and parent browser wording inspection performed; student review pending |
| Metric correctness | Independent worked expectations for normal, unknown-only and zero-record datasets; summary/list reconciliation | 11/11 model checks and parent browser normal/edge/filter observations recorded |
| Robustness | Observed behavior for missing/invalid/stale data and empty filter results, matching prototype rules | Parent observed invalid/malformed, empty, unknown-only, stale, reset and empty-filter cases; model validates missing/unsupported fields |
| UI behavior | Start command, browser walkthrough of Sarah/Michael/Emma views and filters, actual results/evidence | Parent performed running-browser walkthrough; VERIFICATION.md records scope and screenshot limit |
| Generated-code quality | Reviewer findings on data validation, safe rendering, accessibility and avoidable dependency growth as relevant | Shared model and textContent reviewed; parent observed literal HTML-looking input and no created image elements; no third-party dependencies |
| Human-factor clarity | Student role walkthrough records misunderstandings and changes; simulated roles identified as simulated | Pending student participation |
| Decisions and residual risk | Accepted/rejected suggestions, rationale, changes, rechecks and remaining limitations | D-03/D-04/D-07 implemented and AI-checked; risks stay open pending human review and real-use evidence |

## Entry format for subsequent outputs

Use the next AI-S1 identifier and retain the following fields for each significant
code or document batch:

1. Trigger and linked local/Jira story IDs.
2. Exact prompt/context reference and output file/change reference.
3. AI authorship and actual evaluator identity/type (AI or student).
4. Findings, including incorrect or misleading output and its consequences.
5. Accepted/rejected suggestions and decision authority/rationale.
6. Changes made, checks performed, expected/observed results and evidence paths.
7. Unperformed checks, residual risk and required follow-up.

Update this record after generation, review, fixes and re-verification. Do not
reuse P01-P08 prototype testing as evidence that a new dashboard story passed.
