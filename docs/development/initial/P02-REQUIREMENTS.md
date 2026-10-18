# P02 Historical Requirements and Acceptance Criteria

Status: historical specification, not implementation evidence or instructions to resume work.

This companion to [P02](P02-Baseline-Technical-Review.md) preserves the technical requirements, constraints, test cases, and acceptance criteria from its initial task specification. Original section numbers and technical wording are retained for traceability. Role setup and response-format instructions are omitted; see the [coverage ledger](REQUIREMENTS_COVERAGE.md).

Imperative wording describes what the historical phase was asked to do, not what it achieved. References to student review remain historical ownership requirements, not proof that review occurred. Later engineering decisions may supersede these prototype constraints.

## 1. REVIEW OBJECTIVE

Perform a structured review of the current baseline.

The review must cover:

1. Functional correctness
2. Cryptographic integration
3. Protocol design
4. Security
5. Testing
6. Maintainability
7. Error handling
8. Performance measurement
9. Docker/deployment
10. CI/CD
11. Logging
12. Metrics
13. Health checks
14. Documentation
15. AI-generated design assumptions

Do NOT treat this as a production security audit.

This is a university prototype review.

## 2. IMPORTANT CRYPTOGRAPHIC REVIEW

Pay particular attention to:

* ML-KEM-768 API usage
* cryptography version compatibility
* ML-KEM key generation
* encapsulation
* decapsulation
* shared-secret handling
* HKDF usage
* AEAD usage
* nonce generation
* nonce uniqueness
* ciphertext handling
* key separation
* session lifecycle
* key storage
* key destruction/retention assumptions

Verify that the code uses the actual installed API.

The current environment reportedly uses:

cryptography 50.0.1

and:

cryptography.hazmat.primitives.asymmetric.mlkem

with:

MLKEM768PrivateKey.generate()

Do not assume these details are correct without inspecting the installed environment and source code.

IMPORTANT:

ML-KEM decapsulation follows the FIPS 203 implicit rejection behavior.

Review whether the application correctly handles this behavior.

Do not claim that a decapsulation result is automatically authenticated merely because it succeeds.

## 3. AUTHENTICATION REVIEW

Pay special attention to the current architecture's lack of strong authentication.

Review:

* gateway/cloud public-key exchange
* whether the ML-KEM public key is authenticated
* possibility of man-in-the-middle attacks
* device identity assumptions
* gateway identity assumptions
* cloud identity assumptions
* static PSK usage
* capability claims

Clearly explain the difference between:

KEY ESTABLISHMENT

and

AUTHENTICATED KEY ESTABLISHMENT.

If the current design establishes an encrypted session without authenticating the peer, identify the resulting security limitation.

Do NOT automatically implement a complete authentication system.

The purpose is to identify the limitation for student review.

## 4. DOWNGRADE / FALLBACK REVIEW

Inspect how the gateway decides:

* legacy
* modern
* unknown

Review whether a malicious device could simply claim to support or not support a capability.

Analyze:

* downgrade attacks
* capability spoofing
* fallback abuse
* legacy-device trust
* rejection policy
* migration policy

Do not pretend that the existing fallback policy is production-ready.

Identify concrete weaknesses.

## 5. REPLAY REVIEW

Inspect whether the protocol provides:

* message freshness
* sequence numbers
* timestamps
* nonces
* replay detection
* replay rejection

Determine whether an attacker could replay a previously valid encrypted message.

Do not add a complete replay-protection framework yet.

Instead identify what is missing and why it matters.

## 6. PROTOCOL REVIEW

Review:

* JSON-lines framing
* message validation
* message types
* required fields
* malformed messages
* unexpected message types
* invalid Base64
* missing fields
* oversized messages
* invalid ciphertext
* unexpected connection termination

Identify concrete failure scenarios.

## 7. TEST REVIEW

Inspect all 39 existing pytest tests.

Do NOT simply report:

"39 tests pass."

Instead classify the tests into:

* functional tests
* cryptographic tests
* protocol tests
* error-handling tests
* integration tests
* security tests
* operational tests

Identify what is currently covered.

Then identify important missing tests.

At minimum consider:

* malformed JSON
* missing protocol fields
* invalid message type
* oversized input
* wrong ML-KEM ciphertext
* wrong key
* modified ciphertext
* replayed message
* downgrade attempt
* fake capability declaration
* cloud unavailable
* gateway unavailable
* connection timeout
* partial TCP message
* multiple messages over one connection
* empty message
* invalid Base64
* invalid nonce
* session expiration
* concurrent clients

Do not implement all missing tests automatically.

First provide the review findings.

## 8. MAINTAINABILITY REVIEW

Review:

* module boundaries
* duplicated logic
* naming
* configuration handling
* error handling
* logging
* comments
* TODO markers
* coupling
* testability
* dependency management

Identify code that is unnecessarily complicated.

Also identify code that is too simplistic and could cause maintenance problems.

## 9. DOCKER REVIEW

Inspect:

* Dockerfiles
* image base
* dependency installation
* ports
* service names
* networking
* environment variables
* startup commands
* health checks

Verify that:

docker compose up

actually works in the current environment if possible.

Do not claim Docker works unless you actually verify it.

Identify production limitations, but keep the review focused on this university prototype.

## 10. CI/CD REVIEW

Inspect:

.github/workflows/ci.yml

Verify:

* Python version
* dependency installation
* pytest execution
* failure behavior

Identify whether the CI environment is likely to reproduce the local ML-KEM environment.

This is particularly important because ML-KEM support may depend on:

* cryptography version
* OpenSSL version
* Python version

Identify any reproducibility risks.

## 11. LOGGING REVIEW

Inspect all logging statements.

Verify that logs do NOT expose:

* private keys
* shared secrets
* symmetric keys
* ciphertext unnecessarily
* sensitive plaintext unnecessarily

Check whether logs provide enough information for:

* startup
* connection
* message processing
* fallback
* errors
* ML-KEM session establishment

Identify excessive or insufficient logging.

## 12. METRICS REVIEW

Inspect the metrics implementation.

Determine whether:

* counters increment correctly
* counters represent meaningful events
* fallback counts are accurate
* errors are counted consistently
* latency measurements are meaningful

Identify whether the current metrics are sufficient for a simple baseline experiment.

## 13. PERFORMANCE REVIEW

Do not build a sophisticated benchmark framework.

Instead inspect the existing timing measurements.

Determine whether they are sufficient to support later evaluation of:

* ML-KEM establishment time
* message processing latency
* payload size
* successful messages
* fallback events

Identify measurement limitations such as:

* small sample size
* warm-up effects
* machine-specific results
* network variability
* lack of repeated trials

## 14. DOCUMENTATION REVIEW

Inspect README.md and CLAUDE.md.

Check whether the documentation clearly distinguishes:

AI-generated baseline

from

student-reviewed code.

Check whether the security limitations match the actual implementation.

Do not allow the README to claim stronger security than the implementation provides.

## 16. DO NOT MODIFY CODE YET

This is extremely important.

Do NOT automatically fix all findings.

Do NOT refactor the code yet.

Do NOT add a large number of features.

Do NOT implement a full authentication system.

Do NOT implement a sophisticated fallback policy.

Do NOT implement a production monitoring system.

The purpose of P02 is to produce evidence that the student team can use to decide what should be:

ACCEPTED
MODIFIED
REJECTED

in the next development stage.

## 18. FINAL WARNING

Passing 39/39 pytest tests does NOT prove:

* cryptographic correctness
* authentication
* resistance to MITM
* resistance to replay
* resistance to downgrade
* production security
* operational robustness

Explicitly preserve this distinction in the review.

Now inspect the existing project and produce the P02 Baseline Technical Review.

Do not modify files until the review is complete.
