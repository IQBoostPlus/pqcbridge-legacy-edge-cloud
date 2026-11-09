# PQC Bridge dashboard - Sprint 1

A static, LLM-assisted educational dashboard for the Human Factors Scrum
project. Uses synthetic connection segments independently of the existing
Device/Gateway/Cloud protocol prototype. No third-party runtime dependencies,
real credentials, network monitoring or automatic security actions are needed.

## Run locally

From the repository root, with Python 3 installed:

```powershell
python -m http.server 8010 --bind 127.0.0.1 --directory dashboard
```

Open **http://127.0.0.1:8010/** in a modern browser. Use another free port if
8010 is occupied. Stop the server with Ctrl+C when finished. Opening the HTML
directly as a file is unsupported because ES modules and JSON use HTTP loading.
The server serves this dashboard directory only, on loopback.

Run the model checks with Node.js 24 (no install step):

```powershell
node --test dashboard/tests/model.test.mjs
```

See [verification](../docs/sprints/sprint-1/VERIFICATION.md) for observed results
and the validation boundary, rather than inferring success from these commands.

## Demonstrate the increment

1. Load the default fixture. The global overview should show eight connection
   segments, five PQC (62.5%), two fallback and one unknown.
2. In Sarah's security view, distinguish the expected legacy exception from the
   synthetic suspected downgrade; inspect reasons and confidentiality assumptions.
3. Filter Fallback, then Unknown. Search for a nonexistent connection to see the
   empty-result message; clear the search and restore All.
4. Switch to Michael's migration view to inspect blockers, then Emma's executive
   view for an explained overall status and up to three risks/actions.
5. Compare the historical snapshot clock with current time to see data freshness.
6. Load a local JSON snapshot for additional scenarios. Invalid input should show
   an error and clear the previous data presentation. Reset to restore the demo.

The file chooser reads local JSON in the browser; it does not upload it to an
external service or persist the selection. Only synthetic data is supported.

## Data and reporting rules

The fixed [snapshot](fixtures/snapshot.json) declares `schemaVersion: 1`,
`synthetic: true`, a title, UTC `snapshotAt` and a `connections` array. Each
connection supplies string values for `id`, `device`, `segment`,
`keyEstablishment`, `status`, `reason`, `observedAt`, `fallbackKind`, `blocker`,
`confidentiality`, `impact` and `action`.

Segments are `device-to-gateway` or `gateway-to-cloud`. Status is `pqc`,
`fallback` or `unknown`. PQC requires `ML-KEM-768` and fallback kind `none`;
the synthetic fallback scenario uses `ECDH-P256` and kind `expected` or
`suspected`; unknown uses method and kind `unknown`. IDs are unique. Observation
times cannot be later than the snapshot. The model rejects an invalid snapshot
as a whole; it does not quietly discard records and alter coverage.

Coverage is PQC segments divided by all segments, including unknown. Displayed
percentages round to one decimal place. A valid empty snapshot has unavailable
coverage. Filters affect the list, while global summary cards retain all records.
A PQC gateway-to-cloud segment does not establish end-to-end device protection.

The default demonstration clock is pinned to the fixture's historical snapshot
time, keeping results reproducible. It is explicitly labelled as historical
synthetic data. The current-time mode compares observations to the actual clock.
Observations older than 24 hours are stale; future observations relative to the
selected clock are also uncertain. Freshness concerns can coexist with red alerts.

Overall reporting priority is:

1. Red if any synthetic suspected downgrade exists (investigation needed).
2. Unknown for no records, unknown status, stale data or future observations.
3. Amber for remaining expected classical fallback.
4. Green only when all reported segments are PQC and current under these rules.

Green describes the reported segment migration state, not a security guarantee.
The default fixture is red because one scenario calls for investigation; fallback
alone is not proof of attack. HNDL information describes potential exposure under
stated classical-key-exchange and confidentiality assumptions, not detected
harvesting or successful future decryption. The old prototype's preconfigured
ChaCha20-Poly1305 path is a different model from this course scenario.

The rules are prototype decisions under the accepted scope, awaiting student
and Product Owner review. This is a small demonstrator with synthetic scenarios,
not a production monitoring or compliance system.

## Project records

[Sprint goal](../docs/sprints/sprint-1/SPRINT_GOAL.md),
[backlog and Jira mapping](../docs/sprints/sprint-1/BACKLOG.md),
[risks and decisions](../docs/sprints/sprint-1/RISK_AND_DECISION_LOG.md),
[LLM evaluation](../docs/sprints/sprint-1/LLM_EVALUATION.md) and
[retrospective actions](../docs/sprints/sprint-1/RETROSPECTIVE_ACTIONS.md)
track this increment separately from the earlier protocol work.
