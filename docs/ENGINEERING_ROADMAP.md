# PQC Bridge Engineering Roadmap

Updated: 2026-10-16. Status: the engineering direction has been accepted. The milestones, effort estimates, and technology choices below are plans, not delivered capabilities.

This roadmap reflects the accepted review of the proposed refactoring plan. It extends the project from a course demonstration toward an engineering system suitable for a controlled pilot. The P01–P08 records remain intact as evidence of existing implementations, verification results, and scope decisions made at the time.

## 1. Objective and First Deliverable

The near-term deliverable is a deployable, recoverable, and auditable PQC migration gateway. Without modifying the firmware of the selected legacy devices, it will ingest telemetry through one existing protocol and upload it through an authenticated hybrid post-quantum channel. It will provide bounded buffering, acknowledged delivery and retry, credential management, and migration in small groups.

The long-term objective is a migration management product for legacy edge-to-cloud communication, developed after sufficient integration and operational experience. Its value will be measured through integration cost, data continuity, migration risk, and verifiable protection outcomes.

The first release covers one organization, one site, one legacy protocol, one active gateway instance, one cloud receiver, and one-way telemetry. Preserve Python, the existing component boundaries, Docker, tests, and security review assets where practical. Industrial control commands, device firmware updates, multi-tenancy, and high-availability clusters are outside this release.

Execution details: [Short-Term Implementation Plan](SHORT_TERM_PLAN.md).

## 2. Current Baseline and Verification Boundaries

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

### Technology Decisions Still Requiring Validation

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

## 5. Short-Term Roadmap: Controlled-Pilot Candidate

Planning assumption: one primary developer familiar with the repository, with access to the target device or an independent protocol implementation. Phases A–D provisionally require **6–10 effective working weeks**. This is an effort estimate, not a delivery commitment measured from this document's date. Hardware procurement, external security review, environment approval, and waiting time are additional. Re-estimate after Phase A using the resulting evidence.

| Phase | Estimate | Main outcome | Acceptance gate |
| --- | --- | --- | --- |
| A: Use case and technical baseline | 1–2 weeks | Scenario constraints, risk inventory, legacy integration evidence, and hybrid TLS interoperability results | Identify protected assets and links, and demonstrate target-environment feasibility |
| B: Secure and reliable data path | 2–3 weeks | Identity and authorization, durable queue, cloud acknowledgements and deduplication, recovery, and resource limits | No silent loss of durably accepted data after faults; negative tests and resource limits pass |
| C: Minimal migration management | 1–2 weeks | Minimal registry, versioned policies, credential rotation and revocation, and staged rollout and rollback | Verify effective policy and recover from failures without weakening the security floor |
| D: Controlled-pilot preparation | 2–3 weeks | Installation and upgrades, backup and recovery, metrics and alerts, benchmarks, and sustained-run report | Produce a reproducible pilot candidate package and known-limitations record |

Advance through dependency and acceptance gates, not calendar deadlines. Development may overlap, but shared contracts for ingestion, persistence, identity, and messaging must be defined before concurrent changes.

## 6. Long-Term Roadmap: Expansion Based on Pilot Evidence

The following windows assume completion of short-term milestones and sustained staffing. They are planning ranges rather than feature release dates.

| Window | Objective | Entry conditions | Deliverables and exit conditions |
| --- | --- | --- | --- |
| Approximately months 3–6 | Controlled pilot for one real use case | A–D accepted; site owner, data responsibilities, and incident response defined | Recommended observation period of at least 30 days; complete upgrade, rotation, and recovery exercises; establish integration cost, performance, and user feedback |
| Approximately months 6–12 | Repeatable migration product | First pilot demonstrates value; a second concrete integration need exists | Support a second protocol or device category; establish a compatibility matrix, bulk enrollment, grouped rollouts, audit exports, and version-support rules |
| Approximately month 12 onward | Platform capabilities driven by demand | Demonstrated multi-site, multi-team, or scale requirements and a maintenance budget | Selectively add multi-site control, role separation, automated credential management, high availability, or multi-tenancy; accept each capability separately |

Long-term priorities:

1. **Repeatable deployment:** installation, configuration diagnostics, backup, upgrades, rollback, and operational guides that reduce manual integration effort.
2. **Protocol coverage:** choose adapters for a specific next user and reuse stable ingestion and delivery contracts.
3. **Migration governance:** asset and cryptographic-use inventories, evidence of effective policy, time-limited exceptions, bulk rotation, and auditing.
4. **Capacity and availability:** use pilot bottlenecks to decide whether clustering is necessary. Resolve shared state, consistency, message ownership, and deduplication before promising high availability.
5. **Cryptographic evolution:** evaluate post-quantum authentication, algorithm retirement, and new configuration profiles against customer threat models and runtime support.

AI, a generic algorithm plugin marketplace, attack demonstration dashboards, and Kubernetes are not required deliverables. Add them only when there is a concrete need, measurable benefit, and a maintenance owner.

If the first pilot does not demonstrate reduced integration or migration cost, revisit the use case and delivery approach before expanding the platform. Where an established tunnel or proxy already meets the requirements, prioritize integration, deployment, and migration management instead of duplicating existing capabilities.

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

- The planning request covers documentation and README navigation. It does not authorize executing the entire roadmap, deployment, or pushing changes.
- Before implementation, record HEAD, branch, existing changes, and state data. Use isolated environments and preserve existing configurations, real credentials, and original data.
- Deliver small, reviewable changes. Define contracts before modifying shared interfaces, persistent formats, or security policies.
- Track phases as Not started / In progress / Awaiting verification / Accepted / Blocked. Completion requires evidence.
- Arrange independent security review of protocol and credential design. If review resources are unavailable, constrain deployment scope and security claims.
- Keep acceptance contracts and decision context in local documentation. Before creating GitHub Issues, follow `docs/agents/issue-tracker.md`; cross-reference task IDs to avoid maintaining conflicting status records.

## 9. External Technical References

These references inform technology selection but do not replace target-environment validation. Recheck version support and maintenance status during implementation.

- [OpenSSL 3.5 TLS groups](https://docs.openssl.org/3.5/man3/SSL_CTX_set1_curves/): hybrid key-exchange groups including X25519MLKEM768, and interfaces for inspecting negotiated results.
- [cryptography ML-DSA API](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/mldsa/): algorithm interfaces, which do not themselves establish a complete authentication protocol or TLS certificate support.
- [NIST definition of crypto agility](https://csrc.nist.gov/glossary/term/crypto_agility): replacing and adapting cryptographic mechanisms while preserving security and ongoing operations.

## 10. Planning Record

2026-10-16: The user accepted the engineering review direction and requested short- and long-term plans. This roadmap and the implementation task list were produced without code refactoring. Planning now uses the P08 baseline, actual channel evidence, and staged engineering acceptance instead of the early 39-test baseline, device-label migration counts, and late deployment validation.

2026-10-16: Both planning documents were rewritten in English at the user's request. All project documentation is to be written in English; communication with the user remains in Chinese. Scope, task IDs, estimates, and acceptance requirements were retained.
