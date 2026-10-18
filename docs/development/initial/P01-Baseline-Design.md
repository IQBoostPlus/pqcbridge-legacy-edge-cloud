# P01 — Initial Baseline Design and Requirements

> Initial Development Record. Reconstructed on 2026-10-18 from the original specification and the baseline observations reported in P02.
> This is a historical design record, not a new execution or security verification report.

[Record index](README.md) · [Historical requirements](P01-REQUIREMENTS.md)

## 1. Background and Scope

The initial objective was to explore post-quantum cryptographic integration in a small legacy edge-to-cloud software simulation. The system comprised a simulated legacy sensor, an edge gateway, and a cloud receiver. It did not involve physical IoT equipment or a production deployment.

The original baseline was AI-assisted. That provenance does not establish correctness, and this editorial reconstruction does not attribute unverified implementation or review work to a human author. Subsequent records distinguish proposals, implementation, independent testing, and residual risks.

## 2. Component and Protocol Design

| Component | Initial responsibility | Boundary |
| --- | --- | --- |
| Legacy device | Generate periodic sensor readings with identity, timestamp, and temperature; protect the payload with an existing symmetric cryptographic library | No ML-KEM execution on the device |
| Edge gateway | Receive device traffic, identify the legacy path, establish an ML-KEM-768 shared secret with the cloud, and forward protected readings | Capability authentication and fallback policy initially required further design |
| Cloud service | Participate in key establishment, decrypt protected readings, and retain demonstration data in memory | No production persistence or identity-management claim |
| Shared utilities | JSON framing, library-backed AEAD/KDF operations, configuration, logs, health, and metrics | No cryptographic primitives implemented from scratch |

The implemented baseline used JSON-lines over TCP, ChaCha20-Poly1305, ML-KEM-768, and HKDF. Establishing a shared secret did not by itself authenticate the peer. Legacy compatibility was a constrained demonstration, not a completed migration policy.

## 3. Requirements and Deferred Decisions

The [requirements companion](P01-REQUIREMENTS.md) preserves the original numbered technical sections. They cover component responsibilities, communication, cryptographic libraries, safe logging, health, metrics, testing, Docker, CI, structure, measurements, and scope limits.

Deferred questions included authenticating capabilities, distinguishing trusted legacy devices, authorizing fallback, rejecting unknown devices, resisting downgrade and replay, and managing expiry, rotation, and migration. In-memory storage and simple deployment were deliberate initial scope choices, not permanent engineering requirements.

## 4. Initial Deliverable Inventory

- Device, gateway, and cloud Python components and shared cryptographic/protocol utilities.
- Dependency declarations and a baseline pytest suite.
- A Dockerfile for each component and a minimal Compose topology.
- A minimal GitHub Actions workflow that installs dependencies and runs tests.
- Installation, local execution, testing, deployment, limitations, and follow-up documentation.
- Review questions covering authentication, fallback, malformed input, replay, failure recovery, key lifecycle, and operational limits.

The specification requested optional baseline measurements for establishment time, message processing, payload size, successful messages, and fallback events. A requested metric or deployment artifact is not evidence that it was measured or executed.

## 5. Historical Baseline Evidence

The P02 task context reported 39/39 tests passing, a working end-to-end path, ML-KEM session establishment, legacy fallback, working health endpoints, 12 stored readings during a smoke run, and no cryptographic secrets found in that run's logs. These are inherited reports, not fresh measurements from this documentation update.

[P02](P02-Baseline-Technical-Review.md) contains the review's own verification, attack demonstrations, and limitations. It also records correction of an initial API assumption: the installed library used `cryptography.hazmat.primitives.asymmetric.mlkem`, rather than the initially assumed `ml_kem` module spelling.

## 6. Verification Boundaries and Remaining Risks

Passing functional tests did not demonstrate authentication, replay resistance, downgrade resistance, robust failure handling, or production security. Docker configuration and CI workflow existence did not establish successful execution in every environment. No physical-device compatibility was established.

The next phase was a technical review before broad remediation. P02 identified findings; P03 evaluated designs; P04 implemented selected changes. Later phases must be read in sequence rather than applying their results retroactively to P01.
