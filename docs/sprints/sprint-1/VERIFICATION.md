# Sprint 1 build verification

Status: first increment implemented; integrating-AI model/browser checks passed
within the boundary below. Student/PO acceptance, Jira synchronization and an
confirmed review outcomes and an actual retrospective remain pending. The user
subsequently reported that the group review was held but its minutes were not
saved; see TEAM_REVIEW.md for the recovery record and prospective roles. Build record: 8 November
2026 (client project date).

## Workspace baseline

Branch: `main`; HEAD: `681986bc0119d51913140575f98720c90fb378ac`.
Pre-existing work: README/CLAUDE changes and five untracked Sprint documents
from the approved planning task. Tracked diff and initial process documents
were preserved as local snapshots inside `.git` before implementation. No
reset, cleanup, commit, push or protocol configuration change was performed.

## Automated checks observed by the integrating agent

Environment: Node.js v24.16.0, Python 3.12.0.

`node --test dashboard/tests/model.test.mjs`: **11 tests passed, 0 failed**.
Checks cover the 8/5/2/1 fixture and 62.5% calculation, unknown and zero
denominators, qualified green, expected-vs-suspected fallback, per-observation
24-hour boundary, future observations/snapshots, search/segment filters,
malformed schemas, duplicate IDs, missing fields, inconsistent crypto/status
classifications and valid UTC calendar timestamps. `node --check` passed for
both `dashboard/app.mjs` and `dashboard/model.mjs`.

The model author's first run exposed an incorrect test expectation: the search
term actually existed in a fixture value. The author changed the query to a
field-name-only term and re-ran successfully. This was a test correction, not
evidence of a product defect or a student review.

## HTTP and actual browser walkthrough

Started with `python -m http.server 8010 --bind 127.0.0.1 --directory dashboard`.
The root URL returned HTTP 200. The integrating agent used the in-app browser
against this local server, rather than inferring UI success from Node tests.

| Scenario | Expected | Observed |
| --- | --- | --- |
| Default fixture | Total 8; PQC 5/8; fallback 2; unknown 1 | 8, 62.5%, 2, 1; historical snapshot label/time visible |
| Sarah view | Explain non-PQC exposure and distinguish fallback contexts | Expected SEG-001, suspected SEG-007 and unknown SEG-008 shown with reasons, assumptions, impacts and actions |
| Status filters | Fallback IDs 001/007; Unknown 008; PQC five rows | Counts 2/8, 1/8 and 5/8; All restored 8/8 |
| Nonmatching search | Explicit empty result; global cards unchanged | Empty message shown; coverage stayed 62.5% |
| Michael view | Progress and actionable migration blockers | 5 of 8 migrated; three remaining segments with replacement, investigation and inventory blockers |
| Emma view | Explained status and at most three risks | RED / Investigate; three risks with business implications and next actions; no confirmed-attack claim |
| Historical/current clocks | Selected clock and freshness basis explicit | Both modes switched successfully; current-time assessment updated; demo reset restored snapshot clock |
| Definitions and context | Formula, time, HNDL and segment limits readable | Expanded definitions inspected; course and old prototype boundaries explicit |
| All-PQC local JSON | 100% reported migration, qualified green | 100.0%, GREEN / Reported segments migrated; security-guarantee caveat visible |
| Invalid JSON schema after green | Clear old all-clear and rows; visible error | Coverage became dash; role panel cleared; zero rows; schema error shown |
| Valid empty snapshot | Unavailable coverage and uncertain status | Unavailable; UNKNOWN / Insufficient evidence |
| Unknown-only snapshot | 0% coverage, uncertain status | 0.0%; UNKNOWN; one unknown segment |
| One old observation in otherwise PQC snapshot | 100% reported migration must not imply green | 100.0%; UNKNOWN; one stale segment and a data-quality warning |
| Malformed JSON text | Visible parse failure, cleared results | Error shown; coverage and previous assessment cleared |
| HTML-looking data string | Display as text | Literal `<img ...>` reason visible; zero image elements created in connection list |
| Reset after custom/error states | Default data restored | 62.5%, Showing 8 of 8 segments; historical clock restored |

The local QA snapshots were derived from the fixed fixture in
`.git/sprint1-ui-cases/` (not served or tracked). To reproduce: retain only PQC
rows for green, only unknown rows for uncertainty, use an empty array for zero
data, move one PQC observation to `2026-11-06T04:00:00Z` for stale data, omit
required fields for invalid schema, or use malformed JSON. Load them using
the UI's local JSON chooser. This does not modify the shipped fixture.

The final browser console check returned no captured error/warning entries.
The temporary local QA server is stopped after verification; use the documented
command to reopen the dashboard.

## Layout and screenshot evidence

Desktop viewport visually inspected: summary cards, controls, labels and role
switch are readable without overlapping content. Saved
[desktop screenshot](evidence/dashboard.png).

A temporary 390px viewport check found no document-level horizontal overflow
(reported document width 375px), while the table's 850px content remained inside
a 341px horizontal scroll region. Role buttons and status control were visible.
The browser's mobile full-page screenshot attempt failed; a complete mobile
visual review is **not** claimed. The temporary viewport override was reset and
the default desktop page reloaded before saving final evidence.

## Review, documentation and remaining acceptance

The parent inspected generated model, fixture, tests, HTML and application code.
The process-record subagent independently reviewed domain/metric wording and UI
logic, finding no actionable mismatch against the agreed scope. Dynamic input
uses text nodes; loading/reset paths guard asynchronous results. This is AI
review, not student evaluation or proof of production security.

README, dashboard instructions, CLAUDE, goal and the four subagent-maintained
process records are updated together. Final integration checks passed for local
Markdown links, referenced HTML assets, duplicate HTML IDs and trailing whitespace;
`git diff --check` also passed. Existing protocol/backend code and
dependencies were not changed; its historical tests/runtime are not reused as
dashboard evidence, and its suite was not rerun for this isolated frontend.

Outstanding: student walkthrough/evaluation, teacher/PO review of reporting
rules and usefulness, full mobile/cross-browser/accessibility assessment, actual
Jira mapping, team roles/estimates, Sprint review and retrospective, report,
video and slides. These remain separate from the implemented increment.

## Supplementary screenshot and submission-source preparation

This follow-up prepares additional actual dashboard captures and Markdown report
and image-gallery drafts. It does not change dashboard code or rerun product
tests. The test and browser results above remain the historical first-build
evidence; new captures do not establish teacher or stakeholder acceptance.

Existing `evidence/dashboard.png`, `evidence/01-overview.png` and
`evidence/02-security.png` are preserved. The parent captured six additional
JPEGs from the actual running dashboard using native browser screenshots and
DOM-bounding-box clips, without image editing. All use the historical synthetic
snapshot clock. The parent observed the page states and visually inspected the
captures; this does not establish a human usability review or a new mobile check.

| Screenshot | Parent-observed content |
| --- | --- |
| Overview | Eight segments, 62.5% PQC coverage, two fallback and one unknown; synthetic snapshot and clock labels |
| Security view | Sarah's full panel distinguishes expected fallback, synthetic suspected downgrade and unknown protection |
| Migration view | Michael's full panel shows five of eight migrated segments and the three remaining blocker contexts |
| Executive view | Emma's full panel shows RED / Investigate and three risks with actions |
| Fallback inventory | Fallback filter shows two of eight segments; SEG-001 context expanded and SEG-007 marked suspected |
| Definitions | Four expanded explanation panels covering coverage, exposure, time/status and model boundaries |

The report source, dashboard gallery and six JPEGs are kept locally in
`submission/`. The gallery references all six captures with captions and export
page-break hints. The record-maintenance subagent independently checked the
draft's word count, image-file existence and JPEG signatures. These Markdown
sources are prepared for student review; they are
not completed Moodle PDF submissions. Absolute image paths are specific to this
checkout and must remain resolvable when previewing/exporting the gallery.

The parent also verified that all six JPEGs decode, at 1265px wide and respective
heights of 712, 597, 517, 593, 761 and 377px. The screenshot server was stopped
after capture and no listener remained on port 8010. Local checks of these two
updated evidence records passed for 16 relative links and trailing whitespace;
`git diff --check` passed as well.

PDF export and rendered-PDF validation are outside this Markdown-only batch and
remain pending, as do human content review, real Jira mapping and actual team
review/retrospective records. The earlier outstanding report item now has a
Markdown draft; final report review and export are still required. No video or
slides are claimed by these source files.
