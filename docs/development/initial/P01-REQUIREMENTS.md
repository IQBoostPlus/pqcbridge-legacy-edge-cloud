# P01 Historical Requirements and Acceptance Criteria

Status: historical specification, not implementation evidence or instructions to resume work.

This companion to [P01](P01-Baseline-Design.md) preserves the technical requirements, constraints, test cases, and acceptance criteria from its initial task specification. Original section numbers and technical wording are retained for traceability. Role setup and response-format instructions are omitted; see the [coverage ledger](REQUIREMENTS_COVERAGE.md).

Imperative wording describes what the historical phase was asked to do, not what it achieved. References to student review remain historical ownership requirements, not proof that review occurred. Later engineering decisions may supersede these prototype constraints.

## 1. PROJECT CONTEXT

The project is about:

"Legacy System Modernization for PQC & LLM-Assisted Development"

The goal is to modernize a small simulated legacy edge-cloud system
and investigate the integration of post-quantum cryptography (PQC),
specifically ML-KEM, while preserving compatibility with legacy devices
where appropriate.

The system is a pure software simulation.

There is NO real IoT hardware, embedded hardware, or production
deployment.

The system contains three components:

1. Legacy Device
2. Edge Gateway
3. Cloud Service

The project should remain small and manageable. Do NOT unnecessarily
turn this into a production-grade distributed system.

## 2. LEGACY DEVICE

Implement a simulated legacy IoT sensor.

Requirements:

- Generate periodic fake sensor readings.
- Example readings may include:
  - temperature
  - timestamp
  - device ID
- Send readings to the Edge Gateway.
- The device represents a legacy device with limited cryptographic
  capabilities.
- It MUST NOT implement or execute ML-KEM.
- Use an existing standard Python cryptographic library for symmetric
  encryption.
- Use ChaCha20-Poly1305 or AES-GCM for payload protection.
- Do not implement cryptographic algorithms from scratch.

The legacy device should be intentionally simple.

Assume that legacy devices may continue to exist during a migration
period.

## 3. EDGE GATEWAY

The Edge Gateway is the central component of the system.

It should:

- Receive messages from the Legacy Device.
- Identify or determine whether a device supports the modern PQC path.
- Support two conceptual communication paths:

  A. Modern/PQC path
  B. Legacy fallback path

Modern/PQC path:

- Establish a shared secret with the Cloud Service using ML-KEM.
- Use an existing Python cryptographic library.
- Do NOT implement ML-KEM/Kyber from scratch.
- The implementation should use ML-KEM-768 unless there is a clear
  technical reason to choose another supported ML-KEM parameter set.
- Use the resulting shared secret as the basis for a protected
  gateway-to-cloud session.
- If a key derivation function is required, use an existing standard
  library rather than implementing one manually.

Legacy fallback path:

- Detect or identify devices that cannot use ML-KEM.
- Activate a fallback mechanism for those devices.
- Preserve compatibility with the legacy device where appropriate.
- Clearly document that fallback provides a weaker security posture
  than the modern PQC path.

IMPORTANT:
Do NOT fully implement sophisticated fallback policy.

Leave clear TODO markers for the student team to review and implement.

The TODO areas should include questions such as:

- How should device capability be authenticated?
- How should trusted vs. untrusted legacy devices be determined?
- When should fallback be permitted?
- When should a legacy device be rejected?
- How can downgrade attacks be detected or prevented?
- Should legacy credentials/keys expire or rotate?
- How should migration from legacy cryptography to PQC be managed?

Do not pretend that the fallback design is production-ready.

## 4. CLOUD SERVICE

Implement a simulated Cloud Service.

The Cloud Service should:

- Accept communication from the Edge Gateway.
- Participate in the ML-KEM key-establishment process.
- Establish the same shared secret as the Edge Gateway.
- Receive protected sensor data from the gateway.
- Decrypt data when the prototype protocol requires it.
- Store the received sensor data in simple in-memory storage or print
  non-sensitive application data for demonstration.

IMPORTANT:

Do not print or log cryptographic secret keys.

Do not expose:

- ML-KEM private keys
- ML-KEM shared secrets
- symmetric encryption keys
- other sensitive key material

## 5. COMMUNICATION

Use a simple communication mechanism such as:

- Python TCP sockets

or

- a minimal HTTP interface.

Keep the protocol simple and easy for university students to understand.

Use JSON for simple application-level messages where appropriate.

Clearly separate:

- protocol/application data
- cryptographic material
- logging/metrics information

Do not build a complicated message broker or microservice architecture.

## 6. CRYPTOGRAPHY REQUIREMENTS

Use existing, reputable Python cryptographic libraries.

Preferred library:

cryptography

Use library implementations for:

- ML-KEM
- AES-GCM
- ChaCha20-Poly1305
- KDFs if required

DO NOT:

- implement ML-KEM/Kyber mathematically
- implement AES manually
- implement ChaCha20 manually
- implement cryptographic primitives from scratch

The purpose of the project is the safe integration and evaluation of
existing cryptographic functionality into a legacy software system.

Clearly comment where cryptographic library APIs are being used.

## 7. LOGGING

Add basic application logging.

Logs should help demonstrate:

- service startup
- connection attempts
- successful message processing
- fallback activation
- errors
- basic ML-KEM session establishment

IMPORTANT:

NEVER log secret keys or shared secrets.

Avoid logging sensitive plaintext unnecessarily.

Use safe placeholders or identifiers instead of secret values.

## 8. HEALTH CHECKS

Add simple health-check functionality.

The health check should provide basic information such as:

- service status
- whether the service is running
- basic communication status if easy to implement

Do NOT create a complicated monitoring system.

Leave TODO comments for improvements that the student team may consider.

## 9. METRICS

Add simple metrics counters/placeholders.

At minimum consider:

- messages received
- messages successfully processed
- messages forwarded
- errors
- fallback events
- number of legacy devices detected

The metrics are intended for later baseline analysis and evaluation.

Do not create a full observability platform.

## 10. TESTING

Provide a minimal pytest test suite.

Tests should cover basic functionality such as:

- sensor reading generation
- encryption/decryption round trip
- ML-KEM encapsulation/decapsulation round trip
- basic protocol serialization/deserialization
- basic message processing

The tests are only a baseline.

Clearly indicate areas where the student team should add:

- negative tests
- invalid-message tests
- authentication tests
- replay/downgrade tests
- failure handling
- security-related tests
- integration tests

Use TODO markers where appropriate.

## 11. DOCKER / DEPLOYMENT

Provide simple Dockerfiles for:

- Legacy Device
- Edge Gateway
- Cloud Service

Also provide a minimal docker-compose.yml for running the three
components together in a test environment.

The deployment should be suitable for a university test environment.

Do NOT claim that the Docker configuration is production-ready.

## 12. CI/CD BASELINE

Provide a minimal CI configuration, preferably GitHub Actions.

The CI pipeline should at least:

- install Python dependencies
- run pytest
- fail when tests fail

Keep the CI configuration simple.

Do not build a complex enterprise CI/CD system.

Leave TODO markers for possible future improvements such as:

- linting
- static analysis
- security scanning
- Docker image building
- integration tests

## 13. PROJECT STRUCTURE

Provide a clean and understandable project structure.

For example:

legacy-edge-cloud-pqc/
│
├── common/
├── device/
├── gateway/
├── cloud/
├── tests/
├── .github/
│   └── workflows/
├── requirements.txt
├── docker-compose.yml
└── README.md

You may modify this structure if there is a clear reason.

Explain the purpose of each major module.

## 14. BASELINE MEASUREMENTS

Provide simple placeholders or basic measurements that can later be
used by the student team for baseline analysis.

Potential measurements include:

- ML-KEM key establishment time
- message processing latency
- number of successful messages
- number of failed messages
- fallback activation count
- basic payload size

Do NOT create a sophisticated benchmarking framework.

The purpose is to give the students a starting point for later
performance and operational evaluation.

## 15. SECURITY AND LIMITATIONS

This is a university prototype.

Do NOT present the system as production-grade secure software.

Explicitly identify important limitations, including where applicable:

- no full production authentication
- no TLS unless explicitly implemented
- simplified device identity
- simplified key management
- simplified fallback policy
- possible downgrade risks
- simplified error handling
- limited replay protection
- limited key rotation
- limited monitoring
- limited deployment security

However, do not simply list generic security warnings.

Identify limitations that are actually relevant to the generated
architecture and implementation.

## 18. IMPORTANT SCOPE LIMIT

Keep the implementation minimal.

This is the INITIAL BASELINE generated by an LLM.

Do NOT:

- implement a large production architecture
- add unnecessary frameworks
- implement ML-KEM from scratch
- create a complex database
- create Kubernetes deployment
- create a sophisticated monitoring stack
- implement a full identity-management system
- pretend that fallback security is solved
- pretend that the generated code is production-ready

The purpose of this first artifact is to give the student team a
small runnable baseline that can subsequently be:

- tested
- reviewed
- criticized
- corrected
- refactored
- improved
- measured
- deployed
- documented

The student team must remain responsible for all final technical and
security decisions.
