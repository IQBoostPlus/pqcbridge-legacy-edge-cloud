# Sprint 1 implementation prompt provenance

## User instruction

Exact user message in the current project chat:

> 根据goal，开始进行项目构建

Context: the accepted five-feature scope and the existing
[goal](SPRINT_GOAL.md), [backlog](BACKLOG.md) and project `CLAUDE.md`.

## Delegation references

The exact task messages are in this same chat's `collaboration.spawn_agent`
calls addressed to the following task names. The descriptions below are
summaries, not verbatim copies of those task messages.

| Task | Output ownership | Prompt summary |
| --- | --- | --- |
| dashboard_model | dashboard/model.mjs, fixtures/snapshot.json, tests/model.test.mjs | Implement dependency-free validation, shared calculations, filters and a fixed 8-segment fixture; test independently worked expectations and invalid/unknown/empty/stale/future cases. |
| dashboard_ui | dashboard/index.html, styles.css, app.mjs | Build an accessible responsive local dashboard using the shared model API; include three role views, filters/search, local fixture loading/reset, data errors and definitions; render dataset values as text. |
| build_records | BACKLOG.md, RISK_AND_DECISION_LOG.md, LLM_EVALUATION.md, RETROSPECTIVE_ACTIONS.md | Record actual decisions, AI provenance and progress during construction; wait for integrating-agent evidence before claiming test/UI success; preserve the human/Jira/PO states that were pending at the time of construction; see BACKLOG.md for the later Jira entry. |

The parent agent owns contract coordination, integration review, runtime/browser
verification, README/CLAUDE/goal updates and the final verification record.
Follow-up task messages in the same chat record corrections and evidence sent
back to the authors. Source changes remain in the working tree for student review.

## Contract supplied before implementation

- Data: schema version 1, explicitly synthetic, fixed snapshot time; individual
  connection segments with unique IDs, method/status/reason, observation time,
  fallback classification, blocker, confidentiality assumption, impact and action.
- Fixture expectation: eight segments, five PQC, two fallback (one expected,
  one suspected downgrade scenario), one unknown; PQC share 5/8 = 62.5%.
- Coverage includes unknown in its denominator and is unavailable for no records.
- Freshness threshold: 24 hours per observation; default clock pinned to the
  historical synthetic snapshot; current-clock inspection available separately.
- Status priority: suspected downgrade -> red; empty, unknown, stale or future
  evidence -> unknown; otherwise fallback -> amber; otherwise green for reported
  segment migration only. Explain the reason and residual limitations.
- Reject the complete invalid dataset visibly; never silently drop invalid rows
  from the denominator or keep a previous all-clear display after load failure.
- All three role views and the global overview use one snapshot/model. List
  filtering leaves the explicitly labelled global overview unchanged.

These are autonomous prototype implementation choices within the user's scope.
Student/PO approval of reporting rules and stakeholder usefulness remains pending.

See [LLM evaluation](LLM_EVALUATION.md) for findings, accepted changes, checks
and residual risks; [verification](VERIFICATION.md) for actual test/UI evidence.
