# Sprint 2 build and rehearsal verification

Current delivery: the corrected customer report, class quantities, deadline
gap and persona workflows are implemented and technically checked. See the
**Customer reporting increment** section below for current evidence; earlier
sections retain their historical scope. Actual human comprehension, Jira,
course submission and team/PO acceptance remain pending.

## Planning batch (historical baseline)

Date: 12 November 2026 (Asia/Singapore). Product baseline:
`main` at `7ce2898745e69a5e4943080e605db5b2f36dcd3b`. Initial tracked/untracked
status was clean. Existing ignored dashboard dependencies and build output were
present; they were not used as evidence of a fresh UI or production build.

## Checks observed in this batch

| Check | Actual result | Boundary |
| --- | --- | --- |
| `npm.cmd --prefix dashboard test` | 12 passed, 0 failed | Existing model suite; not human comprehension or browser verification |
| `node docs/sprints/sprint-2/experiments/run_experiment.mjs` | 11/11 expected/observed scenario comparisons passed | AI-authored technical rehearsal using existing model; actual output in experiments/results.json |
| Source review of fixture, model, shared state, overview, role and methodology components | Counts, global filter scope, role context and reporting explanations inspected | Source walkthrough only; no new interactive/browser/accessibility observation |

No dashboard implementation changed. No new build or browser session was
necessary to describe this documentation batch, and none is claimed. The
[Sprint 1 verification](../sprint-1/VERIFICATION.md) remains historical.

## Interpretation and open acceptance

The scenario comparisons establish the behavior of the existing synthetic
reporting model for the stated inputs. They do not prove correctness for all
inputs, actual cryptographic posture, live monitoring or user understanding.
The user confirmed the group priority decision. The five-member discussion
draft contains proposed questions and conclusions; participant data is pending.

S2-US-01/02 have initial contract and baseline technical evidence; human rule
review remains open. S2-US-03 has a protocol and AI rehearsal, with human data
not collected. S2-US-04 has candidates only. S2-US-05 awaits actual retrospective
agreement and follow-through. No story is marked Done or accepted by the PO.

## Document integration checks

Integration result: **passed**. The integrating agent checked 10 Markdown files,
60 local file links, eight required Sprint 2 records, all five local story IDs
in both goal/backlog, all 11 saved expected/actual results and trailing
whitespace. Four source-link paths were corrected after the first link check;
the final check passed. `git diff --check` also passed. These checks validate
the documentation package only. README and CLAUDE now point to Sprint 2 while
preserving Sprint 1 records. No commit, push or Jira update was performed.

## Development batch — 12 November 2026

The user authorized development against SPRINT_GOAL.md. Pre-existing README,
CLAUDE and untracked Sprint 2 records were preserved before implementation in
`.git/sprint2-baseline-20261112T043956Z/` (file archive, tracked patch, status,
branch/HEAD and ignored-file inventory). No reset, clean or automatic commit was
used. The product baseline remains `7ce2898`; checks apply to this modified
working tree, not to that commit alone. Runner output now retains source hashes.

### Implemented and observed changes

| Source gap before this batch | Resulting behavior / verification |
| --- | --- |
| No indicator audit or export UI | Indicators exposes formula, contributing IDs, all clocks, rule limits and coexisting reasons; actual JSON download matches the inputs and selected clock |
| Coverage formula hidden at narrow widths; filter footer omitted metric scope | Formula is visible on mobile; fallback selection shows 2 of 8 with unchanged global coverage 62.5% |
| Headline investigation omitted inline evidence-quality counts | Overview retains unknown/stale/future counts; audit retains all conditions and record IDs even when red wins precedence |
| Connection detail lacked same-device segment context | Path context shows SEG-001 fallback alongside SEG-002 PQC, with complete-path and inventory limits |
| Human protocol lacked loadable variants and blank response sheet | Six valid datasets plus deliberate invalid input and a participant sheet prepared; no participant response claimed |

These changes address observable source/reporting gaps, not measured human
misunderstandings. Existing coverage arithmetic and status precedence are retained.

### Technical verification

- `npm.cmd --prefix dashboard test`: **17 passed, 0 failed** (12 baseline plus
  five checks of provenance, simultaneous conditions, future/empty evidence,
  detached export snapshots and invalid export arguments).
- `npm.cmd --prefix dashboard run build`: **passed**, 42 modules transformed.
- `node docs/sprints/sprint-2/experiments/run_experiment.mjs`: **11/11 passed**;
  expected/actual results and source hashes in [results](experiments/results.json).
  Original planning results are retained separately.
- `node docs/sprints/sprint-2/experiments/prepare_sessions.mjs`: six valid
  datasets validated and written, plus one deliberately invalid file.
- Independent read-only source review found no actionable model/export/input
  handling regression within reviewed scope; it did not establish browser or
  human acceptance.

### Browser verification

Built output served by Vite preview at `http://127.0.0.1:4174/` with strict port
selection, separately from Device/Gateway/Cloud. The in-app browser walkthrough
used the default 887 × 902 viewport and a temporary 390 × 844 override; the
override was reset afterward.

Observed default 5/8 = 62.5%, audit source records/reasons, historical/current
clock switching, red coexisting with eight stale observations, fallback filter
2/8 with unchanged global coverage, and mixed-path connection context. Imported
empty, unknown, expected-fallback, mixed-path, stale-pqc and default variants
showed their expected results. The stale-pqc case reports 100% and insufficient
evidence, not all-clear. Invalid input was visibly rejected; export was disabled,
the audit reported unavailable evidence, and Reset demo recovered the fixture.

All three roles were exercised: Sarah SEG-007, Michael SEG-001 and Emma's
suspected-downgrade business risk. These are role-based application checks,
not real participant results. Browser warning/error log collection was empty.

The actual browser download is retained as [browser-export.json](evidence/browser-export.json).
It was parsed independently: eight original records, exact five numerator IDs,
coverage 62.5% and historical clock `2026-11-08T04:00:00.000Z` matched.

At 390px, no page or indicator-panel horizontal overflow was observed. The
filtered inventory footer stayed inside the viewport (right 375.3px, bottom
773.3px). Tab from the reporting-clock selector focused the first source record
and scrolled the audit to expose it; the last source-record link also opened
its connection detail. This is scoped keyboard coverage, not a full accessibility
audit. Physical devices and other browser engines were not tested.

| Evidence | Screenshot |
| --- | --- |
| Stale 100% with insufficient evidence | [Desktop overview](evidence/01-stale-coverage.png) |
| Indicator formula, clock and source explanation | [Desktop indicators](evidence/02-indicator-evidence.png) |
| Responsive evidence page | [Mobile indicators](evidence/03-mobile-indicators.png) |
| Filtered list retains global metric | [Mobile filter](evidence/04-mobile-filter.png) |
| Formula and evidence limits visible | [Mobile overview](evidence/05-mobile-overview.png) |

The first automated scenario-text comparison used an AX diff and incorrectly
treated unchanged text as missing. A full current tree showed the correct UI;
the checker was corrected and all five comparison cases passed. A screenshot
taken immediately after viewport resizing showed an older frame; the final
mobile indicator screenshot was recaptured after a fresh observation. Neither
verification artifact issue is reported as a product defect.

### Remaining acceptance

S2-US-01/02: implementation and technical evidence ready for team rule review.
S2-US-03: participant kit and application rehearsal ready; real sessions pending.
S2-US-04: source-supported reporting fixes technically verified; any later human
findings need their own correction/retest. S2-US-05: evidence maintenance observed,
actual retrospective agreement/effectiveness pending. Jira and PO acceptance
remain separate from these checks.

Final integration checks passed for 12 Markdown files, 77 local file links,
trailing whitespace, all 11 saved scenario results and their current model,
fixture and runner SHA-256 hashes. The archived pre-change model matches the
starting HEAD. `git diff --check` passed. Existing planning records were
extended in place; no commit, push or Jira mutation was performed. The local
preview remains available on port 4174 for review.

## Customer reporting increment — 12 November 2026

### Scope, source and reproducibility

The user authorized construction against the corrected goal and a GitHub push
after verification. Starting HEAD: `e371940c1916aa00cedd42d72a932cc99ff519f5`;
the seven documentation corrections from the preceding batch were already
present and retained. No unrelated product or protocol work was changed.

Implemented R1-R4/R6: declared customer attribution; distinct logical-item
quantities by class; complete required-segment evaluation; explicit unknown
ownership, mapping and evidence limits; 2027 target and 2028 replacement gap;
populated first report; shared persona workflows and selected-customer export.
Local process records support R5/R7; actual Jira/group/PO evidence and R8 course
submission remain pending. No technical check supplies those missing outcomes.

Working-tree SHA-256 at verification:

| Source | SHA-256 |
| --- | --- |
| dashboard/model.mjs | 1596620d19d7ab70346cf87c95e241ddd8d4dc007a44c91cfebd52fe3ea5199f |
| dashboard/fixtures/customer-snapshot.json | c494e1179b891a095ae034f6209a1b12fabe15403873bee475cefabdb644a05a |
| dashboard/tests/customer.test.mjs | ac49e35db215d9167ed8fb9b3d0cbaf9afe3fc198192a4460b8aa280f48e1150 |
| dashboard/src/components/CustomerReport.vue | 3e5c99170363e458531ee8ec6e0ce986b0cc1b19e7cac5b0cabfc1488bf3aa91 |
| dashboard/src/customer.css | c8ff2d2ab5709a8247f5ca5d0f8f80e9e49594712c7274a9cf47a27ba395ae2e |

### Automated checks and independent expectations

- `npm.cmd --prefix dashboard test`: **39/39 passed**, 0 failed: 17 retained
  model tests plus 22 customer cases. Cases cover customer isolation, deduplication
  across repeated route records/shared segments, contradictory metadata, unknown
  class/ownership, missing/incomplete paths, short/long lifetimes, expected and
  suspected fallback, stale/future/item/segment evidence, exact 24-hour boundary,
  empty/invalid scope, plan dates before/on/after 2027-12-31, replacement conflicts,
  selected-customer export and round-trip source snapshot consistency.
- `npm.cmd --prefix dashboard run build`: **passed**, 44 modules. Final output:
  `index-Dqnu7a78.js` and `index-XkeXQdJD.css`.
- `node docs/sprints/sprint-2/experiments/run_experiment.mjs`: **11/11 passed**.
  This is a regression check of the earlier generic scenarios, not new customer
  or human evidence. [results.json](experiments/results.json) contains the current
  model hash, independently checked against the source.
- [Independent worked expectations](experiments/customer-expectations.md)
  explain a separate five-item 2/1/2 example and the default six-item 2/2/2
  fixture before interpreting implementation output. Default classes reconcile:
  telemetry 2 = 1 exposed + 0 unresolved + 1 PQC; configuration 2 = 1 + 1 + 0;
  maintenance 1 = 0 + 0 + 1; Unknown class 1 = 0 + 1 + 0.
- Read-only integration review found one presentation issue: a union of required
  segment IDs was shown with an ordered-path arrow. It now says **Required
  segments** with comma-separated IDs. The schema does not establish traversal
  order. Review did not establish human understanding or PO acceptance.

### Observed browser behavior

The in-app browser exercised the development server at `http://127.0.0.1:5173/`.
It was then replaced by Vite production preview on the same port. Reload showed
`./assets/index-Dqnu7a78.js`, establishing that final checks used built output.
Production desktop (1440 x 900) and narrow (390 x 844) checks passed; temporary
viewport overrides were restored. Production error-log collection was empty.

Observed flows:

1. Default Customer route and initial report: 6 distinct attributed items =
   2 potential HNDL + 2 unresolved + 2 reported PQC (33.3% each). Nine unique
   required connections include missing SEG-009. DATA-UNATTR remains outside
   attributed totals and prevents complete-inventory claims; one other-customer
   item is excluded. Global 5/8 segment coverage is separately labeled.
2. Filter Configuration plus potential exposure: **1 of 6** items shown while
   class/customer totals remain unchanged. Customer switching resets item
   filters. Selecting the other customer yields **1 reported-PQC item** and
   SEG-006 only; unknown ownership still limits scope completeness.
3. Current reporting clock: **2 exposed, 4 unresolved, 0 reported PQC**. Historical
   mode restores 2/2/2. Old classical evidence remains potential exposure with
   quality flags, rather than becoming a second unresolved count.
4. Actual browser downloads were parsed independently. The
   [Northfield export](evidence/customer-browser-export.json) has 6 = 2/2/2 and
   nine connections; the [other-customer export](evidence/customer-other-browser-export.json)
   has one item and SEG-006 only. Both customer report and enclosing evidence
   share `2026-11-08T04:00:00.000Z`; the nested input retains all associations.
5. Sarah: open DATA-C01, inspect the five-year assumption and suspected-downgrade
   reason, follow SEG-007, and select **Customer data context**. Michael: open
   SEG-001 and inspect 2028-06-30 replacement/migration, continuity consequence
   and pending alternatives. Emma: inspect the same report and top decisions.
   These are application role walkthroughs, not participant sessions.
6. Legacy `fixtures/snapshot.json` imports successfully; the Customer page says
   unavailable attribution while all-system overview retains 62.5%. Actual
   `experiments/scenarios/invalid.json` is rejected with the title validation
   message and export disabled. Customer fixture import and Reset demo restore
   6 = 2/2/2. A mistaken nonexistent file selection also produced a visible
   file-read error and recovered on Reset; it is not the invalid-schema result.
7. A narrow-screen overflow was reproduced during development and corrected by
   constraining the workspace grid column. Final production dimensions: viewport
   and body 390px; report client/scroll widths both 345px. The class table has
   its own labeled horizontal-scroll region. Arrow-key focus/scroll on that
   region and Enter to expand a connection detail were observed. Physical devices,
   other browser engines and a full accessibility audit were not tested.

| Evidence | Artifact |
| --- | --- |
| Final production desktop report | [Desktop](evidence/customer-desktop.jpg) |
| Class quantities and uncertainty | [Class table](evidence/customer-classes.jpg) |
| Replacement/continuity conflict | [Deadline gap](evidence/customer-deadline-gap.jpg) |
| Final production narrow report | [Mobile](evidence/customer-mobile.jpg) |

The class and gap screenshots were captured from development preview of the
same final source; desktop/mobile screenshots were captured from built output.

### Delivery and remaining work

The working increment is technically ready for group/PO review. Customer
stories and extended verification have technical evidence; actual member
responses, rule approval, Scrum roles/estimates, Jira history, retrospective
outcomes, teacher acceptance, report/video/slides and course submission are
not established. Prepared discussion/tasks must not substitute for those facts.
GitHub publication is verified against the remote branch after commit; the
resulting revision is reported in the delivery message and Git history.

Final integration checks passed for all 34 changed/new files: 98 local Markdown
links, Markdown whitespace, screenshot dimensions, saved browser-export clocks
and the legacy-runner model hash. `git diff --check` passed. The first document
checker used the host's default text encoding for an export JSON file; switching
that checker to explicit UTF-8 resolved the checker error without changing data.
