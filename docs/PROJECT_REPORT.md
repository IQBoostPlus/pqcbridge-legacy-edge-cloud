# PQC Bridge — Project Report and User Stories

Date: 2026-10-21. Status: documentation consolidation of recorded results.
Baseline: main at 87d33bfe5f6982cd743af5fa7ebafb30131fbb4b.
No runtime experiment was rerun for this report. Acceptance records and raw
evidence retain their original revisions, environments and outcomes.

## 1. Problem and Intended Users

Legacy telemetry equipment may be costly or impractical to replace or reflash.
PQC Bridge places a trusted gateway between those sources and the cloud, adding
authenticated hybrid transport, durable delivery and controlled migration.
The initial scope is one organization/site, one protocol, one active gateway
and one cloud receiver carrying one-way telemetry.

| User | User story | Current evidence or dependency |
| --- | --- | --- |
| Site owner | Preserve existing equipment while improving the cloud link without changing device firmware | Simulated source preserved; real compatibility pending |
| Security administrator | Bind authenticated gateways to permitted devices and reject unauthorized identities or algorithm downgrade | B authorization/TLS checks; C fixed hybrid profiles |
| Data consumer | Receive durably accepted data after retry/restart without duplicate business records | B atomic acceptance, immutable event retries, cloud commit/dedup and matching ACK |
| Migration operator | Apply a policy to one group, prove it effective and roll back safely | C two-group lifecycle; fresh current-channel business ACK required |
| Credential operator | Rotate/revoke identity without resetting event, source or revocation progress | C lifecycle; D coordinated recovery and restored-issuer rotation |
| Operations staff | Identify missing sampling, backlog, expired credentials and unknown security evidence | Local protected health/CLI delivered; authenticated Web product planned |
| Incident responder | Ask AI to explain evidence, approve a fixed recovery action and verify new readings | Agent/search/approval/executor product work pending |
| Reviewer | Reproduce success and failure, tracing each claim to a version and result | P01–P08 records, A–D probes, sanitized evidence and CI |

## 2. Architecture and Business Semantics

The accepted engineering path is simulated authenticated source -> gateway
SQLite acceptance -> TLS 1.3/mTLS/X25519MLKEM768 -> transactional cloud store
and deduplication -> matching durable ACK -> durable gateway queue cleanup.
Local management supplies bounded versions, authorization, credentials and leases;
the data path has no per-message controller dependency.

The business invariant at a stable observation is:

`accepted_total = acknowledged_total + pending + quarantined`

Reconcile event IDs and digests as well as counters after faults. A lost ACK may
cause retransmission of the same event; its cloud business record remains unique.
This guarantee starts at durable gateway acceptance. The unchanged simulator
does not ACK readings or automatically replay source-side loss.

The gateway sees plaintext. Protection of the gateway/cloud key exchange does
not establish sensor-to-cloud end-to-end PQC or post-quantum certificate
authentication; the accepted issuer uses conventional RSA signatures.

## 3. Initial Development: P01–P08

| Phase | Work and recorded outcome |
| --- | --- |
| [P01](development/initial/P01-Baseline-Design.md) | Three-component software simulation, library-backed cryptography and 39-test inherited baseline |
| [P02](development/initial/P02-Baseline-Technical-Review.md) | F-01–F-15 review; replay and malformed-message failures reproduced |
| [P03](development/initial/P03-Security-Evaluation-and-Design-Decisions.md) | Proposed pinning, authenticated hello, per-device keys, sequence/AAD and session lifecycle decisions; proposal status preserved |
| [P04](development/initial/P04-Security-Implementation-and-Verification.md) | Selected security controls implemented with fail-first evidence; 101 tests passed |
| [P05](development/initial/P05-Independent-Security-Verification.md) | Independent TCP-level verification; wrong-length nonce defect NEW-1 found; partial pass |
| [P06](development/initial/P06-Nonce-Validation-and-Security-Verification.md) | Targeted nonce validation and independent re-test; 120 tests passed |
| [P07](development/initial/P07-Evaluation-and-Evidence-Consolidation.md) | Evidence/finding consolidation; pass with documented residual risks |
| [P08](development/initial/P08-Adversarial-Testing-and-Remediation.md) | Gateway authentication and configuration-based credentials; scoped compound attack re-test; 136 tests passed |

These are historical prototype results. A later reproduced authentication replay,
missing transcript binding/key confirmation and metadata-consistency gaps in
[A03](phase-a/A03_RISK_EVIDENCE.md) motivated the separate engineering path.
The P08 result is not blanket closure of the custom protocol's engineering risks.
AI assistance and pending human review remain attributed in the original records.

## 4. Accepted Engineering Milestones

| Phase | Delivered result | Recorded verification | Boundary |
| --- | --- | --- | --- |
| [A](phase-a/STATUS.md) | Isolated baseline, risk mapping, simulated protocol compatibility, hybrid TLS selection and delivery contract | 136 baseline tests; Windows 27/27 and target Linux adapter 22/22 | Technical feasibility and simulated compatibility |
| [B](phase-b/STATUS.md) | Mandatory hybrid TLS/mTLS, gateway/device authorization, durable queue/source state, cloud commit/dedup/ACK, recovery and limits | 179 tests; normal applications 19/19; fault 9 plus before-send 1; runtime 7 and review boundaries 3 | Owned Docker/synthetic telemetry; logical quotas, not physical ENOSPC or power-loss proof |
| [C](phase-c/COMPLETION.md) | Local catalog/audit, fixed versioned profiles, live proof, credential lifecycle, canary and safe rollback | 247 tests; B 19/19; observation 4/4; lifecycle 17/17; Linux CI | Trusted local operator; catalog is a bounded-age observation, not continuous fleet monitoring |
| [D](phase-d/COMPLETION.md) | Offline bundle, coordinated cold recovery, strict receipt/schema checks, same-schema upgrade/rollback and operations handover | Windows/Linux 265 tests each; formal D 9/9; B 19/C 17; 30-minute run and Linux CI | Single owned Linux/amd64 simulation candidate |

Counts overlap across phases and suites; do not sum them into a reliability or
security score. Process-kill recovery does not establish host power-loss safety.
The D repair serialized shared SQLite metric reads and expiry clock sampling
under the existing lock; its red/green evidence remains in the D review.

## 5. Measured D Results and Publication

| Measurement | Recorded result | Source |
| --- | --- | --- |
| Continuous workload | 1,800.000536 seconds; one source every five seconds | [Endurance](phase-d/evidence/endurance-30min-final.json) |
| Delivery reconciliation | 360 sent = accepted = ACK = unique cloud; zero missed schedule/pending/quarantine | Same endurance record |
| Durable ACK p95 | 0.475430 seconds across 360 samples | Same endurance record |
| Credential lifecycle | Three both-role rotations; 17 manifests; six old-leaf revocations | [Final audit](phase-d/evidence/final-runtime-audit.json) |
| Resource observations | 52 samples; peak memory 17.77% of 256 MiB, five PIDs, 335,872 state bytes | Same final audit; this workload only |
| Separate formal normal delivery | 100 observations; durable ACK p95 0.695436 seconds | [Formal matrix](phase-d/evidence/formal-current.json) |
| Separate actual cloud outage | 601.609 seconds; complete backlog drain 27.016 seconds | Same formal matrix |
| Cold checkpoint | Current manifest and all payload hashes checked; current-owner cleanup verified | Final audit |

The [prospective human scope amendment](phase-d/SCOPE_AMENDMENT.md) reduced the
original 24-hour gate, via a one-hour plan, to a fresh 30-minute run. Older
interrupted/inconclusive attempts remain unchanged; their time is not added.
One-hour and 24-hour acceptance flags remain false.

D implementation candidate 4a9431d passed
[validation CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39393876501).
D completion 87d33bf is present in verified remote main history and its
[main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39394824514)
passed both test and Docker jobs. These remote facts were checked on 2026-10-21.
They describe the historical D release; later documentation commits require
their own publication verification.

## 6. Next Product Milestone and Long-Term Direction

The [real-device plan](REAL_DEVICE_PLAN.md) carries forward the 2026-10-20
implementation handbook: two SEN0438 sensors -> Orange Pi 3B ARM64 -> AMD64
cloud receiver -> separate product database/API -> authenticated Web operations
-> cited AI advice -> human-approved fixed action -> new-data recovery proof.
The handbook describes purchased-configuration planning; it supplies no
physical commissioning, account availability or performance acceptance result.

Real Modbus collection, dual-architecture reproducible images, product projection,
Web/RBAC, Foundry/AI Search, action approval/execution and the 48-hour physical
evaluation remain unimplemented or unverified in this checkout. No new phase
was started by this documentation update.

The [long-term roadmap](ENGINEERING_ROADMAP.md) prioritizes a reproducible
cybersecurity/post-quantum migration contribution. Compare the complete system
with V1, conventional TLS and hybrid TLS baselines under comparable conditions;
use component-removal experiments to attribute effects. Compare AI with rules
and manual diagnosis before claiming benefit. Deliver a technical report,
architecture, versioned reproduction package, live demonstration/video and
claim-to-evidence matrix after choosing an event and checking its current rules.

## 7. Remaining Deployment Boundaries

- Physical compatibility and native ARM64 performance require actual hardware.
- Web, AI, remote control distribution and approved recovery actions require
  new implementation, authorization tests and recorded acceptance.
- Queue/storage/catalog quotas require safe maintenance before long operation;
  pending or revoked state must not be cleared to make a run pass.
- D accepts same-schema package changes, not arbitrary storage migrations.
- Offline revocation is bounded by the current lease and service scheduling;
  no instantaneous offline revocation is established.
- The local administrator/recovery authority remains trusted. Queue encryption,
  host-compromise protection, physical power-loss guarantees, live advisory
  clearance and production certification have not been established.

Use the [D risk register](phase-d/RISKS.md), phase operations records and actual
acceptance evidence when defining any broader deployment.
