# PQC Bridge | Sprint 2 dashboard

The corrected [Sprint 2 goal](../docs/sprints/sprint-2/SPRINT_GOAL.md) prioritizes
the key customer's data-class HNDL report and 2027 migration gap, including the
2028 replacement conflict. These features are implemented; human review and
team/PO acceptance remain pending.

The default **Customer** page reports six distinct logical items for Northfield
Energy: 2 potentially exposed, 2 unresolved and 2 reported PQC, across telemetry,
configuration, maintenance and Unknown class. It lists nine required segments,
including missing SEG-009; unknown ownership prevents a complete-inventory
claim. Repeated routes are deduplicated. The proposed 2027 deadline covers all
customer-data connections, with the 2028 replacement conflict shown explicitly.
Select another declared customer, inspect item/connection evidence or export the
selected report with its shared clock and source snapshot. Sarah, Michael and
Emma use this same report with role-specific decision guidance.

The existing increment adds an **Indicators** evidence page: inspect the coverage numerator and
denominator, linked source records, snapshot/reporting/observation times and all
coexisting investigation or data-quality reasons. Export evidence JSON from
the customer report, Indicators or Dataset. It contains the source snapshot,
evaluation clock, rules, global summary and selected customer report; it is an
audit artifact, not an importable snapshot (the nested
`snapshot` retains that input). Downloads are initiated explicitly and contain
the loaded synthetic data. Current-time mode re-evaluates observations without
fetching live data.

The overview shows the coverage formula and simultaneous evidence limits;
inventory filters keep global coverage explicit. Connection evidence includes
the other reported segments for the same device under **Path context**.

Technical verification: 39 model tests (17 legacy + 22 customer), production
build and 11 legacy scenario comparisons passed; desktop and 390px browser
workflows are recorded in the
[Sprint 2 verification](../docs/sprints/sprint-2/VERIFICATION.md).
The [Sprint 2 goal](../docs/sprints/sprint-2/SPRINT_GOAL.md) is the current scope
authority. Human comprehension results and team/PO acceptance remain pending.

For customer-focused group sessions, reset the demo or load
`dashboard/fixtures/customer-snapshot.json` and use the CUS tasks in the
[experiment record](../docs/sprints/sprint-2/USER_UNDERSTANDING_EXPERIMENT.md).
Historical generic scenarios remain available from
`docs/sprints/sprint-2/experiments/scenarios/` via Dataset. The participant
response sheet and scenario preparation instructions are linked in the
[experiment record](../docs/sprints/sprint-2/USER_UNDERSTANDING_EXPERIMENT.md).

## Sprint 1 interface baseline

A Vue 3, Vue Router and Vite rebuild of the Sprint 1 dashboard at `e3c366b` supplies the interface foundation. The legacy fixture remains at `fixtures/snapshot.json`: 8 connection segments, 5 PQC (62.5%), 2 fallback and 1 unknown. Sprint 2's default customer fixture extends those connection records with customer metadata; the separate segment totals remain unchanged.

Integrated from [zerphy799/pqc-dashboard-vue at f95f684](https://github.com/zerphy799/pqc-dashboard-vue/commit/f95f684d3f81abd7aff7a8423dd6978c143b098c).
Run the commands below from this `dashboard/` directory. In PowerShell, use
`npm.cmd` if `npm` resolves to a restricted script.

## Preview the production build

Build the dashboard and serve it with Vite preview. Open the local URL that
Vite prints. The compiled dashboard needs no external network services.

```sh
npm ci
npm run build
npm run preview
```

## Develop

Requires Node.js 22.12+ or 24.

```sh
npm ci
npm run dev
```

Open the URL printed by Vite. Run `npm test` for the model suite and `npm run build` to build the static site into `dist/`. Run `npm run preview` to serve the production build locally. Serve the site over HTTP.

## Data and UI

- `fixtures/customer-snapshot.json` is the default. Optional `customerReporting` metadata extends schema version 1 with declared customers, `keyCustomerId`, `inventoryComplete`, `dataItems` and segment `plans`. Each item declares its customer (or null), ID, primary class (or null), confidentiality assumption, observation time, required segment IDs and mapping-complete flag. See the fixture for the complete import shape.
- Duplicate route records merge by customer and data-item ID; contradictory stable metadata is rejected. Missing segment references remain unresolved. Unknown ownership is shown separately and prevents complete-scope claims. Item counts/proportions do not represent bytes, traffic share or attack probabilities.
- Migration plans accept calendar dates as `YYYY-MM-DD` or null. Current observed PQC, missing plans and late replacement/migration dates remain separate. Owners and action targets stay unassigned/unknown until supplied.
- A legacy snapshot without customer metadata still imports. The Customer page explicitly reports unavailable attribution; all-system views remain usable. Reset demo restores the customer-aware fixture and historical clock.
- Historical mode compares observations with the snapshot time. Current-time mode compares the same observations with the browser clock. The reporting threshold is 24 hours.
- Local JSON import stays in the browser. Reset demo restores the bundled fixture. Search checks supported text fields; filters only change the inventory.
- The default `#/` route is the customer report; `#/overview` is the separate all-system overview. Other routes cover Sarah, Michael, Emma, inventory, individual evidence, the dataset, the interpretation guide and indicator audit. Customer/class totals stay fixed when filtering the item list or connection inventory.
- `model.mjs` owns validation and reporting. `src/dashboard.js` owns the shared snapshot and filters. `src/router.js` defines the routes. Hash navigation supports opening a route directly from a plain static server.
- This dashboard uses synthetic data independently of Device/Gateway/Cloud. Reported migration, fallback, and suspected downgrade scenarios have the limits documented in the interface.
- This frontend is the working dashboard increment. Scrum records, team evaluation and Moodle submissions are tracked separately.

See the [Sprint goal](../docs/sprints/sprint-2/SPRINT_GOAL.md) for scope,
the [backlog](../docs/sprints/sprint-2/BACKLOG.md) for Jira and acceptance
criteria, and [verification](../docs/sprints/sprint-2/VERIFICATION.md) for
checks and remaining UI validation.
