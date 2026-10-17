# PQC Bridge Short-Term Implementation Plan

Updated: 2026-10-17. Planning targets below are not measured results. Phases A and B are complete for the revised Docker/simulation scope; measured evidence and boundaries are recorded in the [Phase A status](phase-a/STATUS.md) and [Phase B status](phase-b/STATUS.md).

Execution scope clarification: the user selected Docker deployment with simulated devices for this iteration. This supersedes the physical-device/real-legacy prerequisite in A-02/A-05 for the current lab scope; simulator results must still never be presented as real-device compatibility. Actual target-runtime transport validation and delivery-contract gates remain required.

Objective: deliver an engineering gateway for one site, one legacy protocol, and one-way telemetry, producing a controlled-pilot candidate. Overall direction, long-term plans, and risk boundaries are defined in the [Engineering Roadmap](ENGINEERING_ROADMAP.md).

The provisional estimate is 6–10 effective working weeks for one primary developer, to be revised after Phase A. The implementation owner produces code and evidence; another suitably qualified person should review protocol, security, and phase acceptance. Confirm staffing and available effort at kickoff; these roles are not assumed to be staffed already.

## 1. Execution Order and Dependencies

`A: Use case, baseline, and transport validation → B: Secure and reliable data path → C: Minimal migration management → D: Pilot candidate package`

Pass the Phase A selection gate before committing to the main Phase B implementation. Use minimal registration and authorization contracts in B, then add their management lifecycle in C. Deployment checks, performance baselines, and observability begin in A/B rather than waiting for D.

Task IDs are planning identifiers within this document, not existing GitHub Issues. They were initially Not started; use the linked execution status for current progress. Phases A/B are accepted for the selected lab scope; C/D have not started.

## 2. Phase A: Define the Use Case and Validate the Technical Approach (1–2 Weeks)

| ID | Work | Deliverable | Dependencies and acceptance |
| --- | --- | --- | --- |
| A-01 | Record current HEAD, branch, changes, test environment, and deployment environment; preserve existing state | Baseline record, isolated execution procedure, and current test and smoke-test reports | Check test isolation first; do not reuse unidentified production state; distinguish historical from current results |
| A-02 | Select devices, protocol, deployment model, workload, and retention requirements | Scenario description, traffic and trust boundaries, and compatibility constraints | Identify whether firmware can change, device behavior during gateway failure, backpressure support, and business sequence numbers |
| A-03 | Map P02–P08 findings to current code; reassess authentication freshness and session binding | Risk/evidence matrix and reproduction/regression checklist | Assign new IDs to new findings; distinguish static inference from dynamic reproduction; historical fixes do not establish current engineering closure |
| A-04 | Validate TLS 1.3, mutual authentication, and hybrid key exchange in the target environment | Version matrix, handshake evidence, interoperability results, and negative-test report | Valid identities connect; invalid identities are rejected; peers without required hybrid support fail under a mandatory hybrid policy |
| A-05 | Validate one real legacy protocol, measure baseline performance, and freeze the delivery contract | Integration report, raw benchmark results, and message/state design | A-02; pass against an independent implementation or real device; simulator-only results must not be reported as completed real-device compatibility acceptance |

### Parameters to Freeze in Phase A

- Device count, reporting frequency, typical and maximum message size, network latency, and tolerated outage duration.
- Gateway CPU, memory, and disk budgets; cloud ingestion capacity and data retention.
- Handshake and delivery latency targets, reconnection recovery time, and maximum revocation enforcement delay.
- Message identifier source, handling of devices without sequence numbers, authorization scope, disconnection behavior, and expiry behavior.
- Supported operating systems, dependency versions, release packaging, and upgrade method for the first release.

### Technical Validation Constraints

Validate the TLS stack actually used at runtime. Importing ML-KEM through `cryptography` is not evidence of TLS support. Record negotiated groups, certificate-validation results, and how configuration takes effect. If a proxy terminates TLS, verify that the backend cannot be bypassed, propagated identities cannot be forged, and local connection boundaries are controlled.

Review the custom handshake for authentication-request replay, identity binding to subsequent KEM/session messages, key confirmation, and the impact of long-term KEM private-key compromise on recorded sessions. These remain validation items until reproduced; do not label them as attacks confirmed by this planning exercise.

**Exit criteria:** the use case and protection boundary are explicit; a deployable transport approach is selected; legacy integration evidence is available; Phase B message and persistent-state contracts are agreed.

**Stop conditions:** hybrid negotiation cannot be demonstrated in the target environment, no verifiable legacy protocol source is available, or first-release scope keeps expanding. Continue bounded compatibility work in that case; defer platform development and avoid using a new custom protocol to fill every gap.

## 3. Phase B: Secure and Reliable Data Path (2–3 Weeks)

| ID | Work | Deliverable | Dependencies and acceptance |
| --- | --- | --- | --- |
| B-01 | Integrate the selected secure channel and map authenticated gateway identities to authorized device sets | Transport implementation, minimal registry configuration, and authorization tests | Phase A accepted; reject invalid gateways, unauthorized devices, and invalid cloud identities |
| B-02 | Implement the durable gateway queue and message-state transitions | Bounded queue, storage format, and capacity policy | A-05; report acceptance only after durable commit; recover pending data after a crash |
| B-03 | Implement transactional cloud writes, idempotent deduplication, and durable acknowledgements | Receiver storage, acknowledgement protocol, and duplicate-processing tests | B-02 message contract; repeated requests return consistent results without duplicate business records |
| B-04 | Implement retries, backoff, connection recovery, and session/credential expiry handling | Recovery logic and stop/shutdown paths | B-01–03; recover according to contract after acknowledgement loss, half-open connections, and restarts |
| B-05 | Bound connections, handshakes, messages, queues, and disk usage; isolate management interfaces | Resource configuration, access controls, and limit-exceeded metrics | Do not rely on a tiny device population; overload produces predictable behavior |
| B-06 | Separate liveness, readiness, cloud connectivity, and business delivery status | Structured logs, metrics, and health checks | Observable from startup; outages do not report normal delivery; secret material is not logged |

### Message and Persistent-State Contract

1. Count data as accepted by the gateway only after validation and durable commit. Where the legacy protocol supports acknowledgement, send success only after that point.
2. Reuse the same message identifier for retries. The cloud stores the business record and deduplication state in one transaction and acknowledges only after commit.
3. Finalize gateway queue state after receiving a matching acknowledgement. A lost acknowledgement may cause retransmission but must not duplicate the business record.
4. Where devices lack reliable sequence numbers, the gateway assigns identifiers to durably accepted events. These identify gateway retries; they do not guarantee detection of duplicate sampling or submissions originating at the device.
5. Replay state, device sequence numbers, and business deduplication have distinct responsibilities. Unauthenticated messages must not advance sequence state; legitimate retries must not be rejected solely for carrying an older sequence number.
6. If sequence checks remain, define behavior for device reset/replacement, unusually large sequence numbers, concurrent connections, and service restarts. A sequence-jump window alone does not resolve all these cases.
7. Deduplication retention must cover the maximum retry period. Beyond that period, explicitly quarantine, reject, or manually recover data; state cleanup must not silently enable repeated business side effects.
8. Transport encryption does not encrypt the local queue. Select protection at rest, file permissions, retention, and deletion based on data sensitivity, and document key storage.

### Minimum Fault Matrix

| Failure point | Required outcome |
| --- | --- |
| Gateway exits before durable commit | No false acceptance; protocols with acknowledgements permit sender retry |
| Gateway exits after commit but before sending | Pending records survive restart |
| Connection drops before cloud commit | Gateway retries; cloud ultimately creates at most one business record |
| Connection drops after cloud commit but before acknowledgement | Retry receives a consistent acknowledgement without duplicate records |
| Gateway exits after acknowledgement but before cleanup | Retransmission after recovery does not duplicate cloud writes |
| Cloud outage or half-open network connection | Bounded retry behavior and resources; observable state |
| Queue or disk fills | No false acceptance; apply protocol-compatible backpressure or explicit drops with alerts |
| Invalid identity, unauthorized device, or incompatible policy | Reject the operation or buffer authorized data as policy permits; do not automatically weaken security |

**Exit criteria:** the fault matrix passes; durably accepted, acknowledged, pending, and explicitly handled exceptional data can be reconciled. The implementation does not hide failure by relying on unlimited memory, disk, or threads.

**Rollback boundary:** retain an isolated V1 baseline for comparison, not as an unconditional rollback target for engineering data. Verify read compatibility and recovery steps before upgrades that change storage formats. Restoring an old database snapshot must not roll back message or revocation state.

## 4. Phase C: Minimal Migration Management (1–2 Weeks)

| ID | Work | Deliverable | Dependencies and acceptance |
| --- | --- | --- | --- |
| C-01 | Establish minimal device/gateway registration lifecycle | Enrollment, disabling, binding, and audited operations | B-01; separate identities, asset information, and credential references; no plaintext secrets in the registry |
| C-02 | Implement a small set of versioned policy profiles | Desired/effective versions, application outcomes, and failure reasons | B; reject unknown profiles and configurations below the security floor; disallow arbitrary algorithm combinations |
| C-03 | Implement credential issuance, renewal, rotation, and revocation | Procedures, bounded overlap windows, and emergency-revocation exercise | C-01; specify when existing connections terminate and how quickly revocation takes effect offline |
| C-04 | Implement staged policy rollout and constrained rollback | Prechecks, canary group, outcome observation, and rollback record | C-02–03; failures do not affect unmigrated groups or restore invalid credentials |
| C-05 | Handle controller disconnection and provide minimal management access | CLI or limited API, valid-policy cache, and status queries | No per-message controller dependency; test policy expiry, credential expiry, and extended disconnection |

The first release groups rollouts by gateway or independent channel. Devices sharing one secure connection cannot be reported as using different key-exchange modes. Device-level protection statistics require actual channel routing that supports the distinction.

Policy states must distinguish Pending, Applying, Effective, Failed, Rolled back, and Unknown. Effective requires live connection evidence and business-path verification. Expired evidence changes the status to Unknown.

Exercise bounded overlap of old and new credentials, retirement of old credentials, failed-rotation recovery, and emergency revocation. If online revocation checks are initially omitted, specify the combination of short-lived credentials, active disconnection, and offline leases, including the maximum enforcement delay. A generic claim of revocation support is insufficient.

**Exit criteria:** one group of active channels completes migration; one failed migration completes a safe rollback; credential rotation and revocation exercises pass; management records identify the operator and version involved.

## 5. Phase D: Pilot Candidate Package and Acceptance (2–3 Weeks)

| ID | Work | Deliverable | Acceptance |
| --- | --- | --- | --- |
| D-01 | Standardize installation, initial trust establishment, configuration, and upgrades | Versioned deployment package, configuration examples, and installation/upgrade/rollback instructions | Reproducible in a clean environment; real deployments reject demo credentials; trust anchors are not obtained from untrusted logs |
| D-02 | Establish backup/recovery, permissions, and dependency maintenance | Recovery guide, permission settings, dependency inventory, and vulnerability-handling process | Restore successfully in isolation; keep secrets out of the repository, logs, and ordinary reports |
| D-03 | Run fault, sustained-operation, and capacity tests | Raw results, environment description, and performance report | Meet frozen thresholds and include target-load and overload results |
| D-04 | Consolidate security regression and independent review | Risk register, review findings, and pilot boundaries | Unresolved high-impact risks have explicit deployment-blocking conditions; passing tests alone does not authorize release |
| D-05 | Complete operational visibility and handover | Simple status page or CLI, metrics/alerts, and support/incident procedures | Operators can identify backlog, disconnection, credential expiry, policy mismatch, and capacity problems |

### Proposed Acceptance Scenarios

These are initial candidate values to freeze against the use case in Phase A. Without supporting business requirements, they must not be presented as suitable for arbitrary devices or production scale.

- Run for at least 24 hours at the agreed load without unhandled exceptions; keep memory, connections, and disk within agreed limits.
- Recover from a 10-minute network outage within designed buffering capacity. All data durably accepted by the gateway eventually receives cloud acknowledgement, with unique business-record counts reconciled.
- Complete exit/restart tests at all Phase B failure points, plus queue-full and disk-full tests.
- Reject invalid identities, unauthorized devices, applicable replay cases, and unauthorized downgrades as expected; legitimate traffic remains recoverable.
- Complete at least one version upgrade, credential rotation, emergency revocation, and backup-restore exercise.
- Compare conventional and hybrid TLS using equivalent authentication, hardware, message sizes, network, and load. Separate full handshakes from session resumption; record sample counts, latency percentiles, throughput, and resource peaks.
- Keep TLS 0-RTT disabled in the first release. Reassess replay and business side effects before any later adoption.
- Freeze handshake latency, delivery latency, recovery time, and throughput thresholds in Phase A. Do not invent absolute performance guarantees in advance.

**Exit criteria:** implementers and reviewers can reproduce the report's results; deployment package, operational instructions, remaining risks, and pilot scope agree. The accepted output is a controlled-pilot candidate, not an automatically production-secure product.

## 6. Scope and Effort Control

The short-term release excludes a generic cryptographic algorithm configurator, a multi-tenant platform, multi-site high availability, arbitrary protocol adapters, control-command delivery, AI anomaly detection, an attack-button dashboard, and a Kubernetes cluster.

If effort exceeds estimates, reduce management UI scope and protocol coverage first. Preserve authentication, durable delivery, resource limits, and fault acceptance. Prefer a small, maintainable dependency set. Any service split must address a concrete requirement the current components cannot meet.

## 7. First Work After Implementation Starts

1. Complete A-01 to establish a reproducible current baseline while preserving existing user work.
2. Complete A-02 to identify the device/protocol and primary environment. If hardware is unavailable, document the limits of independent-implementation verification.
3. Carry out A-03 and A-04 in isolation to resolve handshake risks and hybrid transport feasibility first.
4. Complete A-05, freeze message-delivery and persistent-state contracts, and re-estimate Phases B–D.

This task list is the entry point for a future implementation request. Producing or translating these documents does not initiate development, external deployment, or Git pushes.
