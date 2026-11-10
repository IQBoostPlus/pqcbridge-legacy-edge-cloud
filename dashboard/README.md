# PQC Bridge | Sprint 1 dashboard

A Vue 3, Vue Router and Vite rebuild of the Sprint 1 dashboard at `e3c366b`. It uses the same schema, default fixture and reporting rules. The default load shows 8 connection segments, 5 PQC (62.5%), 2 fallback and 1 unknown. The three perspectives use the same snapshot.

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

- Historical mode compares observations with the snapshot time. Current-time mode compares the same observations with the browser clock. The reporting threshold is 24 hours.
- Local JSON import stays in the browser. Reset demo restores the bundled fixture. Search checks supported text fields; filters only change the inventory.
- Routes cover the overview, Sarah's security review, Michael's migration planning, Emma's executive briefing, connection inventory, individual evidence, the dataset and the interpretation guide. Inventory records, role cases, and long evidence text use paging within the viewport. Evidence stays on the selected connection and field while the clock updates.
- `model.mjs` owns validation and reporting. `src/dashboard.js` owns the shared snapshot and filters. `src/router.js` defines the routes. Hash navigation supports opening a route directly from a plain static server.
- This dashboard uses synthetic data independently of Device/Gateway/Cloud. Reported migration, fallback, and suspected downgrade scenarios have the limits documented in the interface.
- This frontend is the working dashboard increment. Scrum records, team evaluation and Moodle submissions are tracked separately.

See the [Sprint goal](../docs/sprints/sprint-1/SPRINT_GOAL.md) for scope,
the [backlog](../docs/sprints/sprint-1/BACKLOG.md) for Jira and acceptance
criteria, and [verification](../docs/sprints/sprint-1/VERIFICATION.md) for
checks and remaining UI validation.
