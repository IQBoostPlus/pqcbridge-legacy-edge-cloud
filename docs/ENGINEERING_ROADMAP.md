# PQC Bridge Engineering Roadmap

Updated: 2026-10-21. Status: A–D are accepted for their explicit Docker/simulation scopes. Physical deployment, Web/AI operations and further research remain planned. The historical estimates and decision gates below are preserved; current acceptance is recorded separately.

This roadmap reflects the accepted review of the proposed refactoring plan. It extends the project from a course demonstration toward an engineering system suitable for a controlled pilot. The [Initial Development Records](development/initial/README.md) retain P01–P08 technical findings, verification results, and historical decision states.

## 1. Objective and First Deliverable

The near-term deliverable is a deployable, recoverable, and auditable PQC migration gateway. Without modifying the firmware of the selected legacy devices, it will ingest telemetry through one existing protocol and upload it through an authenticated hybrid post-quantum channel. It will provide bounded buffering, acknowledged delivery and retry, credential management, and migration in small groups.

The long-term objective is a competition-ready cybersecurity and post-quantum software engineering project with a verifiable migration mechanism, reproducible experiments, and application evidence. Network security is the primary track; post-quantum migration is the technical focus; AI diagnostics are a conditional research extension. Engineering quality remains the foundation, while broad platform development depends on demonstrated demand.

The first release covers one organization, one site, one legacy protocol, one active gateway instance, one cloud receiver, and one-way telemetry. Preserve Python, the existing component boundaries, Docker, tests, and security review assets where practical. Industrial control commands, device firmware updates, multi-tenancy, and high-availability clusters are outside this release.

Execution details: [A–D implementation plan](SHORT_TERM_PLAN.md), [current project report](PROJECT_REPORT.md) and [planned real-device/Web/AI milestone](REAL_DEVICE_PLAN.md).

## 2. Current Baseline and Verification Boundaries

As of 2026-10-21, [A](phase-a/STATUS.md), [B](phase-b/STATUS.md),
[C](phase-c/COMPLETION.md) and amended [D](phase-d/COMPLETION.md) are accepted
for owned Docker services and simulated devices. D completion 87d33bf is present
in verified remote main history; its [main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39394824514)
passed test and Docker jobs. D's 30-minute run reconciled 360 unique records,
completed three both-role rotations and measured durable ACK p95 0.475430 seconds.
It establishes no one-hour/24-hour endurance or physical/production acceptance.

The following table retains the original V1 planning baseline. Its gaps are
historical motivation, not a claim that the accepted B–D path still lacks TLS,
durability or credential management. See the [project report](PROJECT_REPORT.md)
for delivered controls and remaining risks. No runtime checks were rerun for
this documentation synchronization.


The planning baseline is commit `681986b`. When planning began, the workspace already contained changes to `CLAUDE.md` and files under `docs/agents/`. Those existing changes were preserved.

| Area | Existing evidence | Engineering gaps |
| --- | --- | --- |
| Secure channel | Custom JSON/TCP; ML-KEM-768, HKDF, AEAD, and cloud public-key pinning | Complete authenticated handshake, forward secrecy, interoperability, and key lifecycle |
| Identity | Per-device keys, gateway authentication tags, and configuration-based credentials | Enrollment and revocation, handshake freshness, and device-to-gateway authorization |
| Replay protection | Persistent device sequence numbers; in-memory checks at the gateway and cloud | Restart recovery, retry and deduplication semantics, and abnormal sequence handling |
| Sessions | Five-state model, send-failure detection, and automatic reconnection | Keepalive, rotation, shutdown behavior, and bounded resources during failures |
| Data | In-memory storage without a durable acknowledgement queue | Durable acceptance, cloud acknowledgements, retries, and disk-full handling |
| Deployment and tests | README records 136 tests at P08 and previous Docker end-to-end verification | Current baseline revalidation, target-environment testing, and failure and capacity evidence |

These statements come from repository code and records. Tests, Docker verification, and attack reproductions were not rerun during planning. Historical passes do not establish current-environment verification or production security.

Primary references: [README](../README.md), [gateway sessions](../gateway/cloud_channel.py), [gateway forwarding](../gateway/gateway.py), [gateway authentication](../common/crypto.py), [cloud receiver](../cloud/cloud.py), and [replay state](../common/replay.py).

## 3. Accepted Direction and Open Decisions

### Accepted Engineering Direction

- Start with one real use case, deliver a minimal migration gateway, and expand platform capabilities in response to demonstrated demand.
- Preserve existing assets and evolve incrementally. Use the current baseline rather than rebuilding capabilities from the early 39-test version.
- Evaluate established TLS implementations first. Adding cryptographic algorithm APIs does not replace secure protocol design.
- Treat security, reliable delivery, operations, and migration recovery as core requirements. Begin deployment validation and benchmarking early.
- Require evidence for completion claims. A distributed configuration is not proof that a policy is effective.

### Original Selection Gates and Remaining Field Validation

The table records the selection gates used to plan A–D. The lab selected direct
Python/OpenSSL hybrid TLS, SQLite transactions, local credential management and
per-gateway rollout; their acceptance is in the phase records. Physical protocol
interoperability, native ARM64 operation and deployment-specific custody,
capacity and durability still require the [real-device gates](REAL_DEVICE_PLAN.md).

| Decision | Preferred direction to evaluate | Decision gate |
| --- | --- | --- |
| Legacy protocol | Select from the first target device or existing system | Interoperate with a real device or independent implementation; document what can be modified |
| Gateway-to-cloud channel | TLS 1.3, mutual authentication, and hybrid key exchange | Enforce policy and demonstrate the actual negotiated result in the target environment |
| TLS integration | Use a compatible stack directly; evaluate an established proxy if necessary | Manageable operations, trustworthy identity propagation, and no bypassable backend entry point |
| Local persistent state | Evaluate an embedded database first | Pass transaction, crash recovery, disk capacity, and backup tests |
| Cloud storage | Select based on idempotent writes and acknowledgement transaction requirements | Commit data and deduplication state atomically; preserve results after recovery |
| Credentials | Certificate issuance, renewal, and revocation manageable at small scale | Verify identity mapping, expiry, and revocation behavior |
| Migration unit | Initially group by gateway or independent channel | Match actual connection isolation; avoid overstating protection through device labels |

If the preferred approach is infeasible in the target environment, document compatibility problems and alternatives. Do not automatically return to an incompletely reviewed custom security protocol. Conventional TLS may support engineering validation, but it must not be reported as delivered hybrid post-quantum protection.

## 4. Security and Business Boundaries

1. **Protection scope.** The default improvement covers the gateway-to-cloud link. The device-to-gateway link remains subject to its existing protocol and local network conditions. The gateway is a trusted termination point with plaintext access; the design does not claim device-to-cloud end-to-end PQC.
2. **Identity and authorization.** An authenticated gateway is not automatically authorized to represent every device. The cloud must enforce device-to-gateway authorization. If a legacy device lacks a cryptographic identity, record its actual source of trust; a device identifier is not authentication.
3. **Algorithm claims.** Record hybrid key exchange and post-quantum signatures separately. Conventional certificate signatures do not provide post-quantum authentication. Hybrid deployment may be a long-term choice; a pure-PQC configuration is not a mandatory destination.
4. **Reliable delivery.** The first release targets at-least-once transmission and idempotent cloud processing from the point of durable gateway acceptance. In-memory receipt or a successful socket send does not establish durable acceptance or successful cloud storage.
5. **Legacy limitations.** Recovery of data that never reached the gateway depends on device-side buffering. For protocols without backpressure or acknowledgements, specify overflow drops and alerts explicitly.
6. **Downgrade and rollback.** Network failure must not trigger unauthorized algorithm downgrades. Rollback must preserve the security floor and must not restore revoked credentials, stale replay state, or incompatible data formats.
7. **Controller disconnection.** The data path may use the last valid policy, subject to credential validity and constraints such as offline leases. Define blocking or buffering behavior after expiry before release.
8. **Deployment boundaries.** Separate management, health, and reading interfaces by purpose; avoid unnecessary public exposure. Implement access controls, connection limits, and input limits before a pilot.

The P03 decisions accepting non-persistent state, static demo credentials, and limited scale for the course prototype do not automatically exempt the engineering version from these requirements. Record revised design decisions, data migration methods, and rollback conditions during implementation. Preserve the historical review conclusions.

## 5. A–D Roadmap and Recorded Acceptance

The original planning assumption was one primary developer and **6–10 effective
working weeks** for A–D, excluding procurement and external waiting time. This
historical estimate is not remaining work or a measured project duration. A–D
have since passed their amended simulation gates; the original plan below
retains its intended outcomes. The next physical/product milestone has separate
[estimates and gates](REAL_DEVICE_PLAN.md), including 48-hour real operation.

| Phase | Estimate | Main outcome | Acceptance gate |
| --- | --- | --- | --- |
| A: Use case and technical baseline | 1–2 weeks | Scenario constraints, risk inventory, legacy integration evidence, and hybrid TLS interoperability results | Identify protected assets and links, and demonstrate target-environment feasibility |
| B: Secure and reliable data path | 2–3 weeks | Identity and authorization, durable queue, cloud acknowledgements and deduplication, recovery, and resource limits | No silent loss of durably accepted data after faults; negative tests and resource limits pass |
| C: Minimal migration management | 1–2 weeks | Minimal registry, versioned policies, credential rotation and revocation, and staged rollout and rollback | Verify effective policy and recover from failures without weakening the security floor |
| D: Controlled-pilot preparation | 2–3 weeks | Installation and upgrades, backup and recovery, metrics and alerts, benchmarks, and sustained-run report | Produce a reproducible pilot candidate package and known-limitations record |

Advance through dependency and acceptance gates, not calendar deadlines. Development may overlap, but shared contracts for ingestion, persistence, identity, and messaging must be defined before concurrent changes.

## 6. Long-Term Roadmap: Engineering Evidence for Competitions

Use milestone gates and the selected event deadline to plan delivery. The former broad platform timeline is replaced by the sequence below. No specific event, eligibility, award outcome, or submission date is assumed.

| Milestone | Contribution | Required evidence | Gate |
| --- | --- | --- | --- |
| Engineering foundation — accepted in simulation | Secure, recoverable gateway with controlled migration | A–D evidence, explicit lab/field boundaries, recovery and credential tests | Preserve accepted controls; field use still requires separate verification |
| Physical and operations product — planned | Two real sensors, ARM64 gateway, authenticated Web operations and approved recovery | [Real-device plan](REAL_DEVICE_PLAN.md), compatibility/fault results, fresh-data action proof and 48-hour report | Native transport, capacity maintenance and identity gates precede broader use |
| Research validation | A testable method for migration without silent downgrade or data loss after durable acceptance | Defined research question, comparison baselines, automated experiments, raw results, and limitations | Identify what the project contributes beyond its TLS and storage dependencies |
| Competition release | Stable demonstration of the contribution | Reproducible package, English technical report, architecture diagram, short demonstration, video, and claim-to-evidence matrix | Select event and deadline; freeze features before submission and rehearse the complete demonstration |
| Conditional AI study | Evidence-grounded migration diagnosis and recommendations | Held-out cases, rule/manual baselines, ablation results, safety tests, latency, and cost | Add AI to the core contribution only when it demonstrates a measurable benefit |
| Pilot and further iteration | Real integration and operational feedback | Compatibility results, operator feedback, integration effort, and maintenance cost | Expand protocols or platform functions only in response to demonstrated requirements |

### Research Question and Core Contributions

Evaluate how legacy telemetry can migrate to an authenticated hybrid channel while preserving firmware compatibility, durable delivery, credential lifecycle control, and a security floor during failure and rollback. Separate three contributions: compatibility integration, controlled migration, and reproducible verification tooling.

Using ML-KEM or TLS is an enabling dependency, not a claim of a new cryptographic algorithm. Compare with existing solutions and state the project's original mechanism or integration contribution precisely.

### Track Positioning

- Cybersecurity: emphasize threat models, identity authorization, adversarial testing, recovery, and security-preserving migration.
- Post-quantum security/software engineering: emphasize compatibility, hybrid interoperability, migration overhead, and reproducible engineering evidence.
- AI: require a substantive, evaluated diagnostic capability; code written with AI assistance is not itself an AI product feature.
- Quantum computing: PQC runs on classical computers. Check whether the event accepts post-quantum security; do not imply quantum circuits, quantum hardware execution, or a real quantum attack.

### AI Diagnostic Experiment

The proposed assistant reads redacted capabilities, configuration, handshake outcomes, and failure logs; explains policy mismatches with cited evidence; and produces structured migration or repair suggestions. It must distinguish missing evidence from a valid diagnosis.

AI recommendations pass through deterministic constraint checks and administrator approval before changes. The model receives no private keys and cannot independently change device authorization or lower cryptographic requirements. AI availability must not be required for telemetry delivery.

Compare fixed rules, manual log analysis, and AI with deterministic validation. Measure diagnosis accuracy, evidence-reference accuracy, unsafe recommendation rate, abstention behavior, time, and cost. Split evaluation by scenario or device family to avoid template leakage between development and held-out cases. Include malicious log instructions, missing context, contradictory evidence, and out-of-scope inputs. Report failures as well as improvements; omit AI from the core contribution if benefits are not demonstrated.

### Reproducible Security and Failure Experiments

Automate identity/authorization rejection, replay and tamper cases, policy downgrade attempts, rotation/revocation/expiry, controller disconnection, process exits, lost acknowledgements, queue limits, and disk limits. Distinguish logical storage quotas from physical disk exhaustion and laboratory attacks from real-world deployment evidence.

Each run records configuration, versions, expectations, observed results, and redacted evidence. A dashboard may control and visualize these real runs; it must not display scripted success as a measured result. An offline demonstration recording must be labeled as a recording.

### Comparison and Attribution

Use V1 as a historical baseline, an established conventional TLS configuration, an established hybrid TLS configuration or equivalent transport setup, and the complete PQC Bridge path. Keep hardware, authentication, workload, network, and measurement methods comparable. Use component-removal experiments to distinguish benefits from the transport, delivery mechanism, migration controls, and AI assistant.

### Competition Deliverables and Scope Control

Maintain an English technical report covering the problem, related work, design, method, results, and limitations; a versioned reproducible package; architecture diagrams; a short live demonstration; a complete video; and a contribution inventory separating standards, third-party components, team implementation, and material AI assistance.

After selecting an event, verify eligibility, scoring, permitted prior work, open-source requirements, data licenses, AI-use disclosures, and repeat-submission rules against that event's current rules. Do not claim novelty or compliance solely from this roadmap.

A 30-day field pilot remains useful evidence but is not a universal prerequisite for a competition release. If field access is unavailable, submit an honestly bounded laboratory evaluation where event rules allow it. Second protocols, multi-site operation, multi-tenancy, high availability, generic algorithm plugins, and Kubernetes remain demand-driven extensions. Prefer deeper validation of one protocol over unsupported breadth.

## 7. Success Metrics and Evidence Rules

| Dimension | Metrics to record | Interpretation constraints |
| --- | --- | --- |
| Integration value | Configuration effort per device/site, firmware changes required, and compatibility pass rate | Simulated device counts are not real integration counts |
| Security | Actual key-exchange group, authentication type, authorization denials, and revocation enforcement time | Enabled configuration does not prove successful negotiation; unit tests do not prove protocol security |
| Reliability | Durably accepted, cloud-acknowledged, pending, and explicitly dropped messages; recovery time | Separate successful transmission from successful cloud storage |
| Performance | Handshake P50/P95, delivery P95/P99, throughput, CPU, memory, and peak queue/disk usage | Compare equivalent hardware, load, network, authentication, and sampling methods |
| Migration | Desired/effective policy versions, active channels meeting target policy, failures, and rollbacks | Disconnected objects or expired evidence become unknown rather than retaining a historical success status |
| Operations | Upgrade and recovery duration, rotation failure rate, and manual interventions | One successful demonstration does not replace sustained operation and fault exercises |

Each phase report must identify the commit, dependency and image versions, environment, workload, commands, redacted logs, expected and observed outcomes, and remaining risks. For latency across machines, document clock synchronization or the measurement method. Set numerical targets in Phase A against device requirements; do not change thresholds retrospectively to make results pass.

## 8. Delivery and Change Governance

- This roadmap does not authorize execution or publication by itself. When publication is explicitly authorized, use a scoped English commit and direct non-forced push; do not create a pull request unless the user requests a change to that preference.
- Before implementation, record HEAD, branch, existing changes, and state data. Use isolated environments and preserve existing configurations, real credentials, and original data.
- Deliver small, reviewable changes. Define contracts before modifying shared interfaces, persistent formats, or security policies.
- Track phases as Not started / In progress / Awaiting verification / Accepted / Blocked. Completion requires evidence.
- Arrange independent security review of protocol and credential design. If review resources are unavailable, constrain deployment scope and security claims.
- Keep acceptance contracts and decision context in repository documentation. Planning task IDs are not GitHub Issues; cross-reference any later issue IDs to avoid conflicting status records.

## 9. External Technical References

These references inform technology selection but do not replace target-environment validation. Recheck version support and maintenance status during implementation.

- [OpenSSL 3.5 TLS groups](https://docs.openssl.org/3.5/man3/SSL_CTX_set1_curves/): hybrid key-exchange groups including X25519MLKEM768, and interfaces for inspecting negotiated results.
- [cryptography ML-DSA API](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/mldsa/): algorithm interfaces, which do not themselves establish a complete authentication protocol or TLS certificate support.
- [NIST definition of crypto agility](https://csrc.nist.gov/glossary/term/crypto_agility): replacing and adapting cryptographic mechanisms while preserving security and ongoing operations.

## 10. Planning Record

2026-10-16: The user accepted the engineering review direction and requested short- and long-term plans. This roadmap and the implementation task list were produced without code refactoring. Planning now uses the P08 baseline, actual channel evidence, and staged engineering acceptance instead of the early 39-test baseline, device-label migration counts, and late deployment validation.

2026-10-16: Both planning documents were rewritten in English at the user's request. All project documentation is to be written in English; communication with the user remains in Chinese. Scope, task IDs, estimates, and acceptance requirements were retained.

2026-10-18: The accepted competition direction was incorporated: cybersecurity as the primary track, verifiable post-quantum migration as the focus, and an evidence-gated AI diagnostic study. Initial development records were reorganized, and direct GitHub pushes became the publication preference. No paused Phase C implementation was resumed by this documentation update.

2026-10-21: Synchronized A–D acceptance and verified D main/CI history, added current user-story/report navigation and the separate planned real-device/Web/AI milestone. Historical estimates, failures and raw evidence remain unchanged. No new runtime implementation was started.
