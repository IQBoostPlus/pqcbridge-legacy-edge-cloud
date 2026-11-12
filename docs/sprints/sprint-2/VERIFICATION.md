# Sprint 2 build and rehearsal verification

Current delivery: indicator evidence UI and JSON export implemented; technical
checks below passed. Human comprehension and team/PO acceptance remain pending.

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
