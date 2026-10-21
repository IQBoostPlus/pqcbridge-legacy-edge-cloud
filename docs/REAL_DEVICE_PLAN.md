# Real-Device and Operations Product Plan

Date: 2026-10-21. Status: planned; no implementation or physical acceptance is
claimed. This English repository plan consolidates the user-provided 2026-10-20
PQC Bridge hardware/software implementation handbook and procurement checklist.
Those PDFs are local planning inputs outside this Git repository. Their proposed
interfaces, modules, costs and target metrics are not delivered capabilities.

## 1. Goal, Topology and Schedule

Deliver real reading -> durable protected delivery -> visible incident -> cited
AI investigation -> human-approved fixed action -> fresh-data recovery proof
and audit. Use one Orange Pi 3B 4GB/64GB eMMC gateway, two SEN0438 sensors on
separate isolated USB-RS485 links, and one AMD64 Linux cloud host. Sample each
sensor every ten seconds. Confirm actual hardware labels, serial parameters,
cloud access and Azure region/model permissions during implementation.

The handbook estimates 8–10 weeks with two contributors, plus about two weeks
of ARM/runtime/account contingency; a single contributor should allow 12–16
weeks. These are effort estimates from implementation readiness, not dates or
evidence of staffed roles. Progress follows gates rather than elapsed weeks.

## 2. Delivery Sequence and Gates

| Work | Planned output | Acceptance gate |
| --- | --- | --- |
| H01–H03: hardware/system | Inventory, board-matched ARM64 Linux/eMMC installation, separate 5V/12V supplies, fixed serial aliases and wiring records | Independent gateway boot; three restarts preserve device mapping |
| H04–H05: physical sampling | Independent read-only Modbus probe, confirmed registers/scaling, per-port workers and timeout/error status | Each sensor 30 minutes, then dual-channel two hours; disconnect either without disrupting the other |
| S01–S02: runtime/contracts | Explicit product modules and native ARM64/AMD64 immutable images | Actual board-to-cloud TLS 1.3/mTLS/X25519MLKEM768 and negative identity/policy checks |
| S03: durable real ingestion | Atomic sequence/event/checkpoint acceptance and unchanged-event retry | One hour of real dual-source data; restart/ACK-loss tests preserve IDs and unique commits |
| S04–S06: data/deployment | Incremental cloud commit cursor, product projection, identity/lease distribution, protected telemetry, backup and self-start | Interrupted projection catches up beyond 100 records; outage recovery, lease expiry, rotation and isolated restore pass |
| S07–S08: Web operations | FastAPI, separate product SQLite, Vue 3/TypeScript/ECharts, Entra identity and server-enforced roles | Real monitoring/history and seven pages; unauthenticated/unauthorized operations refused |
| S09–S10: read-only AI | Versioned runbook search and Foundry investigation through bounded tools | Real failure evidence and valid citations; missing context and unavailable AI handled explicitly |
| S11: approved actions | Fixed cloud-receiver restart and specified Modbus poller reopen | Single-use fresh approval; replay/target change/injection refused; new readings prove recovery |
| I01–I03: integrated evaluation | Fault matrix, comparative diagnosis, 48-hour run, restore and upgrade/rollback, evidence package | Complete accepted-event reconciliation, negative tests and versioned delivery records |

Proposed module names such as edge_modbus/, product_api/, web/, ops/ and
deploy/product/ are design locations, not existing entry points. Reuse the
accepted transport, delivery and management components through explicit opt-in
integration. The D simulation installer does not authorize a physical deployment.

## 3. Preserve the Security and Delivery Contracts

- Initialize the fixed TLS policy before application/framework/SDK imports.
  Record Python ssl's actual OpenSSL linkage separately from the CLI and
  cryptography binding; emulation is not native ARM performance evidence.
- Authenticate/authorize the gateway and cloud. A physical RS485 sensor lacks
  native cryptographic identity; a fabricated sensor PSK must not imply otherwise.
- Allocate accepted-source sequence, event ID, canonical bytes and source
  checkpoint in one queue transaction. Retries retain the original ID/digest.
- Report failed sampling separately; never fabricate zero, old or missed readings.
  Distinguish sampled, durably accepted, cloud committed and product projected.
- Isolate product/AI dependencies from the secure bootstrap. Keep private keys
  and tokens out of Git, browser responses, prompts and ordinary logs.
- Distribute short-lived manifests through authenticated control access, checking
  target, sequence, digest and expiry. Never extend an expired local lease.

## 4. Storage, Projection and Long-Run Blockers

Keep separate gateway, cloud-delivery, management and product databases with
designated writers. SQLite files stay local to their owning host. Add a stable,
generation-aware incremental commit cursor and idempotent projection; the current
latest-100 readings endpoint is insufficient for history synchronization.

| Existing bound | At two readings per ten seconds | Work required |
| --- | --- | --- |
| 10,000 pending plus quarantined gateway rows | About 13.9 hours at ideal sampling, before byte limits | Explicit admission/alerts; preserve accepted events; 24-hour TTL is not 24-hour capacity |
| 100,000 cloud rows | About 5.8 days | Reviewed versioned archival/storage migration before cumulative load approaches the limit |
| 256 MiB per-role state with 16 MiB reserve | DB/WAL/index/metadata may reach quota first | Measure actual bytes and alarm before refusal |
| 1,000 management audit entries; 12 credentials; 100 versions | About 720 manifest publications in 48 hours at a proposed 240-second interval, plus other actions | Safe audit/credential/version maintenance retaining replay/revocation guards |

Plan verified archive batches, integrity checks and recovery watermarks before
deleting hot business details. Deduplication and source/revocation progress must
survive archival. The handbook's candidate three-day hot history and private
object-storage archive need schema, budget and replay tests. Never clear state
or merely enlarge defaults to bypass a gate. Check actual credential notAfter
and renewals before scheduling 48 hours.

## 5. Web, AI and Action Boundaries

Plan seven pages: monitoring, devices, incidents/AI operations, security/PQC,
automation/audit, experiments/evidence, and history/export. Enforce Observer,
Operator and Admin authorization in the backend/executor; a hidden button is
not access control. Show timestamps, real/simulated provenance, data gaps,
staleness, unknown policy evidence and partial failures.

Azure AI Search supplies version-filtered runbook passages and citations.
Foundry Agent Service may request only bounded read-only incident evidence,
gateway health, delivery summaries and runbook search. Validate evidence IDs
and citations against the current snapshot. Model/SDK choices and account
permissions require verification; procurement candidates are not guaranteed.

Only restart_cloud_receiver and reopen_modbus_poller are proposed write actions.
Bind an explicit human approval to the fixed target, action, evidence/policy
hashes, expiry and one-use authorization. No arbitrary shell, SQL, file path,
root access or Docker socket is granted to AI. Reject stale/replayed/modified
authorizations. Enter verifying after execution; require three fresh samples
per sensor with unique cloud commits and matching ACKs before marking recovery.
Hardware reconnection remains a human task. Ordinary deterministic reconnection
after network repair is not an AI-executed action.

## 6. Experiments and Final Delivery

Exercise normal temperature changes, single-sensor disconnect, gateway restart,
ten-minute outage, cloud stop, commit/ACK loss, queue/storage refusal, invalid
TLS/identity, lease expiry/rotation, unavailable AI/search, unauthorized/injected
actions, and projection/recovery interruption. Record a unique run ID, version,
preconditions, expected/actual outcomes and reversal/cleanup for each case.

Freeze targets before runs. Handbook candidate targets include sampling success
at least 99%, online delivery p95 at most five seconds, search Recall@5 at least
90%, principal diagnosis accuracy at least 80% and AI investigation p95 at most
60 seconds. These are proposed acceptance values, not measurements. Report
sampling coverage separately from delivery completeness after durable acceptance.

Compare manual runbook diagnosis with AI-assisted diagnosis across five fault
classes, at least five independent resets per class/condition (50 runs). Block
by class and randomize order; retain failures/timeouts and avoid treating many
messages from one incident as independent experiments. Evaluate citation quality,
unsafe recommendations, latency and cost, as well as diagnosis correctness.

The physical 48-hour run targets about 34,560 scheduled samples, with actual
attempts/successes recorded separately. Include planned restart/outage and an
approved recovery, reconcile accepted event sets after drain, verify backup/
restore and compatible upgrade/rollback, then deliver hardware records, pinned
images/configuration, migrations, raw metrics/failures, runbooks and a real demo.
This new gate does not extend the accepted D simulation's 30-minute result.

Broader field deployment, additional protocols, multi-tenancy and high
availability remain demand-driven work. Research/competition evidence and AI
contribution rules are defined in the [engineering roadmap](ENGINEERING_ROADMAP.md).
