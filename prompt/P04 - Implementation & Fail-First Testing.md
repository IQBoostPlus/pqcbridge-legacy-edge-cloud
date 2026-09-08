# P04 — Security Implementation & Fail-First Testing

## 0. Role

You are an AI software-engineering assistant working on the university project:

**PQCBridge Legacy Edge-Cloud — Post-Quantum Security Migration Simulation**

The project is an educational edge-cloud simulation involving:

* legacy IoT devices;
* an edge gateway;
* a cloud service;
* ML-KEM-768;
* HKDF;
* ChaCha20-Poly1305;
* legacy fallback;
* security migration;
* replay protection;
* session management.

P01 created the baseline.

P02 performed a technical security review.

P03 performed student evaluation of the P02 findings and selected the security design.

**P04 is the implementation phase.**

---

# 1. Critical Rule — Follow P03, Not Your Own Design

P03 is the approved design authority for this phase.

Before modifying anything:

1. Read P03 completely.
2. Read P02 completely.
3. Read the current repository.
4. Identify every P03 decision.
5. Build an implementation checklist from P03.

Do NOT introduce security mechanisms that were not approved in P03 unless they are strictly necessary to make an approved design work.

If you believe P03 contains a technical problem:

**STOP before changing the design.**

Document the problem and explain why the implementation cannot safely proceed.

Do not silently redesign the system.

---

# 2. Mandatory Evidence Chain

For every significant security change, preserve:

```text
P03 Decision
    ↓
Implementation Plan
    ↓
Fail-First Test
    ↓
Observed Baseline Failure
    ↓
Code Modification
    ↓
Test Pass
    ↓
Regression Test
    ↓
Security Verification
    ↓
Remaining Risk
```

The goal is NOT simply:

> "Make all tests pass."

The goal is:

> "Demonstrate that the selected security requirement was initially violated, implement the approved fix, and then demonstrate that the requirement is satisfied."

---

# 3. No Big-Bang Rewrite

Do NOT rewrite the project.

Do NOT replace the architecture.

Do NOT introduce a new framework.

Do NOT rewrite working modules without a clear reason.

Prefer:

* small changes;
* existing project structure;
* existing protocol;
* existing cryptographic libraries;
* minimal new dependencies;
* focused tests;
* readable student-level code.

The project must remain understandable to university students.

---

# 4. Implementation Order

Implement in the following order unless P03 explicitly states otherwise:

```text
P04.1 Dependency reproducibility
        ↓
P04.2 Protocol validation
        ↓
P04.3 AEAD/AAD support
        ↓
P04.4 Metrics correction
        ↓
P04.5 Per-device key model
        ↓
P04.6 Authenticated hello + fallback policy
        ↓
P04.7 Replay protection
        ↓
P04.8 Cloud ML-KEM key pinning
        ↓
P04.9 Session lifecycle
        ↓
P04.10 Full regression testing
        ↓
P04.11 Documentation
```

Do not skip directly to the final implementation.

---

# 5. P04.1 — Dependency Reproducibility

Review:

`requirements.txt`

The baseline currently uses a broad cryptography dependency.

P03 approved the dependency reproducibility improvement.

Implement an appropriate pinned or bounded version based on the verified environment.

The ML-KEM API must remain compatible with:

```python
from cryptography.hazmat.primitives.asymmetric import mlkem
```

and the verified ML-KEM-768 API.

After modification:

* install dependencies in the project environment;
* verify imports;
* run tests.

Record the exact installed versions.

Do not upgrade unrelated packages without justification.

---

# 6. P04.2 — Protocol Validation

Fix:

* F-03;
* F-04;
* relevant parts of F-15.

Required behavior:

## Gateway

Malformed ML-KEM handshake messages must NOT terminate the gateway process.

For example:

```json
{
  "type": "mlkem_pubkey",
  "cloud_id": "fake-cloud"
}
```

without `public_key` must result in controlled protocol handling.

## Cloud

Malformed encapsulation messages such as:

```json
{
  "type": "mlkem_encaps"
}
```

without `ciphertext` must NOT kill the handler thread unexpectedly.

Required principles:

* validate required fields;
* validate types;
* validate base64;
* validate expected lengths where appropriate;
* convert malformed input into controlled protocol errors;
* close or reject the connection according to the existing protocol design;
* log an appropriate safe error;
* increment error metrics where P03 specifies this.

Do NOT catch every exception with:

```python
except Exception:
```

unless there is a specific documented reason.

Do not hide programming errors.

---

# 7. P04.3 — AEAD / AAD Support

P03 approved binding security-relevant context to authenticated data.

Extend the existing ChaCha20-Poly1305 helper carefully.

AAD should be authenticated but not encrypted.

The design must ensure that replay/security-relevant context cannot be changed without causing authentication failure.

Possible authenticated context may include:

* device ID;
* session ID;
* message type;
* sequence number.

Use only the exact fields selected by P03.

Do NOT invent additional protocol semantics.

Maintain backward compatibility only where P03 explicitly requires it.

Add focused unit tests demonstrating:

1. correct AAD → decrypt succeeds;
2. modified AAD → decrypt fails;
3. modified ciphertext → decrypt fails;
4. modified nonce → decrypt fails.

---

# 8. P04.4 — Metrics Correction

Correct the P02/P03 metric issues.

Ensure:

* byte measurements are stored as bytes;
* time measurements are stored as milliseconds or seconds consistently;
* metric names match their units;
* fallback counters have clearly defined semantics;
* relevant protocol/security errors increment the appropriate error counter.

Do not create a large monitoring framework.

Keep the metrics simple.

Add tests for the important metric behavior.

---

# 9. P04.5 — Per-Device Key Model

Implement only the simple model approved in P03.

The project should no longer treat one global PSK as the authentication identity of every device if P03 explicitly requires per-device authentication.

Use a small static educational device-key registry if that is the selected P03 design.

For example, conceptually:

```text
dev-01 → device-specific secret
dev-02 → device-specific secret
```

Do NOT implement:

* a production provisioning server;
* a database;
* PKI;
* hardware security modules;
* key-management infrastructure.

Requirements:

* device ID must map to a specific configured key;
* unknown device IDs must be rejected;
* a device must not be able to claim another device's identity;
* keys must not be printed in logs;
* configuration must not accidentally expose secrets through health endpoints.

Add tests for:

* valid device;
* unknown device;
* wrong key;
* mismatched device ID/key;
* attempted device impersonation.

Document the prototype limitation:

> The key registry is a simulation of provisioning and is not a production provisioning system.

---

# 10. P04.6 — Authenticated Hello and Fallback Policy

Implement the P03 fallback decision.

The gateway must distinguish between:

* known legacy device;
* known modern-capable device;
* unknown device;
* malformed hello;
* unsupported capability combination.

Follow the exact P03 policy.

The core rule approved in P03 is:

> Legacy fallback is permitted only for known devices with an authenticated hello.

Do not allow an unauthenticated plaintext capability claim to determine security policy.

The gateway should reject cases that P03 marked as reject.

Add tests for:

1. valid legacy device;
2. modern-capable device;
3. both capabilities;
4. unknown device;
5. malformed capabilities;
6. modified capability claim;
7. unauthenticated hello;
8. authenticated legacy fallback.

Make the reason for every decision visible in logs without exposing secrets.

---

# 11. P04.7 — Replay Protection

Implement the P03-selected replay design:

> monotonic per-device sequence + AAD binding + device-side counter persistence

Do not replace this with a replay window unless P03 is explicitly changed.

The cloud/gateway must reject replayed or stale messages according to P03.

At minimum test:

```text
sequence 1 → ACCEPT
sequence 2 → ACCEPT
sequence 2 again → REJECT
sequence 1 again → REJECT
sequence 3 → ACCEPT
```

Also test:

* modified sequence number;
* sequence number with modified AAD;
* wrong device ID;
* reconnect behavior;
* device counter persistence.

The implementation must clearly define where the highest accepted sequence is stored.

Document the approved limitation:

> Gateway restart may lose replay state if this was accepted as a P03 limitation.

Do not silently solve this limitation by adding a database.

---

# 12. P04.8 — Cloud ML-KEM Key Pinning

Implement the P03-selected authentication strategy.

P03 selected fingerprint pinning rather than TLS or signature-based authentication.

Therefore:

1. compute/represent the cloud ML-KEM public-key fingerprint;
2. provision the expected fingerprint as a trust anchor;
3. verify the received public key against the expected fingerprint;
4. reject the handshake if the fingerprint does not match.

The fingerprint comparison must occur BEFORE using the received public key to establish the session.

Do not:

* accept any received public key;
* automatically update the pinned fingerprint;
* silently trust the first key;
* create a full PKI.

Add tests for:

* expected key → accepted;
* different key → rejected;
* malformed key → rejected;
* changed fingerprint → rejected.

Clearly document:

> Pinning protects against substitution only when the initial pinned fingerprint is provisioned through a trusted mechanism.

This remains an educational simulation, not a complete PKI.

---

# 13. P04.9 — Session Lifecycle

Implement the P03-approved session lifecycle.

The gateway must not remain permanently "established" after the cloud connection has failed.

At minimum:

```text
DISCONNECTED
    ↓
CONNECTING
    ↓
ESTABLISHING
    ↓
ESTABLISHED
    ↓
FAILED
    ↓
DISCONNECTED
```

Implement:

* session invalidation after connection failure;
* reconnect behavior;
* new session ID after a new session establishment;
* truthful health status;
* appropriate cloud-side session cleanup/eviction.

Do not build a complicated state-management framework.

Test:

1. normal establishment;
2. normal forwarding;
3. cloud failure;
4. failed send;
5. session invalidation;
6. reconnect;
7. new session ID;
8. health state after failure;
9. health state after reconnect.

---

# 14. P04.10 — Fail-First Tests

This section is mandatory.

Before implementing each major fix, create the corresponding regression/security test.

For selected findings, demonstrate that the baseline fails the security requirement.

At minimum produce evidence for:

### F-03

Baseline:

```text
Malformed handshake
→ gateway process crash
```

After fix:

```text
Malformed handshake
→ controlled rejection
→ gateway remains alive
```

### F-04

Baseline:

```text
Malformed encapsulation
→ handler thread failure
```

After fix:

```text
Malformed encapsulation
→ controlled protocol error
→ service continues
```

### F-05

Baseline:

```text
Valid message
→ ACCEPT

Same captured message
→ ACCEPT
```

After fix:

```text
Valid message
→ ACCEPT

Same captured message
→ REJECT
```

### F-01

Baseline:

```text
different ML-KEM public key
→ accepted
```

After fix:

```text
different ML-KEM public key
→ rejected
```

### F-02

Baseline:

```text
capability manipulation
→ possible fallback manipulation
```

After fix:

```text
unauthenticated/invalid capability
→ rejected
```

Only make claims that are actually demonstrated.

---

# 15. Preserve Baseline Evidence

Do not delete or overwrite the P02 evidence.

The repository must preserve:

* original P02 findings;
* original reproduction evidence;
* original baseline test count;
* original behavior before fixes.

If a test needs to change because the security design has changed, preserve the old rationale in documentation.

Do not rewrite history to make it appear that the baseline was already secure.

---

# 16. Regression Testing

After each major implementation step:

```bash
pytest -q
```

Record:

* number of tests;
* passed;
* failed;
* skipped;
* duration.

The original baseline had:

```text
39 passed
```

The final P04 test count may increase.

Do not remove existing tests simply because they conflict with the new implementation.

If an old test encodes behavior intentionally changed by P03:

1. explain why;
2. update the test;
3. document the design change;
4. verify all other relevant behavior.

---

# 17. Integration Testing

After unit tests pass, run end-to-end tests.

At minimum verify:

```text
Device
   ↓
Gateway
   ↓
ML-KEM-768 establishment
   ↓
Authenticated session
   ↓
Encrypted reading
   ↓
Cloud
   ↓
Stored reading
```

Also verify:

### Legacy path

```text
known legacy device
→ authenticated hello
→ approved fallback
→ protected forwarding
```

### Invalid device

```text
unknown device
→ rejected
```

### Replay

```text
valid message
→ accepted

same message
→ rejected
```

### Cloud failure

```text
established session
→ cloud failure
→ gateway detects failure
→ session invalidated
→ health becomes degraded/disconnected
→ reconnect
→ new session
```

---

# 18. Security Verification

Do not only rely on pytest.

Perform targeted demonstrations.

At minimum:

### Authentication / pinning

Try a substituted cloud public key.

Expected:

```text
REJECT
```

### Downgrade

Modify capability information.

Expected:

```text
REJECT
```

or the exact behavior defined in P03.

### Replay

Send an already accepted encrypted message again.

Expected:

```text
REJECT
```

### Malformed handshake

Send incomplete handshake data.

Expected:

```text
controlled error
```

and the service remains operational.

### Session failure

Terminate the cloud connection after establishment.

Expected:

```text
session no longer reported as healthy
```

---

# 19. Secret Handling

During implementation:

NEVER log:

* PSKs;
* ML-KEM private keys;
* shared secrets;
* raw session keys;
* authentication secrets.

If debugging requires identifying a key:

use:

```text
SHA-256 fingerprint
```

or another safe identifier rather than the key itself.

Run the project's secret-scan procedure if available.

If no secret scan exists, perform a targeted repository search before completion.

---

# 20. Docker and CI

If Docker is unavailable, do not pretend it was tested.

If Docker becomes available:

1. build images;
2. start compose;
3. check health;
4. run the end-to-end flow;
5. test restart/failure behavior.

For CI:

* inspect the workflow;
* run locally where possible;
* do not claim remote CI passed unless it actually ran.

If the project is not a Git repository, record:

```text
CI execution not verified.
```

---

# 21. Documentation Updates

After implementation, update:

## README.md

Add:

* implemented security controls;
* authentication model;
* fallback policy;
* replay protection;
* session lifecycle;
* dependency version;
* tests;
* known limitations.

Do not remove the original limitations unless they are genuinely fixed.

For every remaining limitation, state:

```text
Status:
Deferred / Out of Scope

Reason:
...

Future improvement:
...
```

---

# 22. Create P04 Report

Create:

`review/P04 - Security Implementation & Verification.md`

The report must contain:

## 1. Implementation Summary

What was changed and why.

## 2. P03 Decision Mapping

| P03 Decision | Implementation | Files | Status |
| ------------ | -------------- | ----- | ------ |

## 3. Fail-First Evidence

| Finding | Baseline behavior | Test | Initial result |
| ------- | ----------------- | ---- | -------------- |

## 4. Implementation Details

For each major security control.

## 5. Security Tests

List all new tests.

## 6. Regression Tests

Report the complete pytest result.

## 7. Integration Tests

Report end-to-end results.

## 8. Security Attack Re-tests

Include:

* malformed handshake;
* replay;
* key substitution;
* downgrade;
* session failure.

## 9. Metrics

Report corrected metric semantics and example results.

## 10. Remaining Risks

Do NOT claim complete security.

Explicitly list unresolved risks.

## 11. Deferred Findings

List findings intentionally not implemented.

## 12. Docker / CI Status

Clearly distinguish:

* tested;
* not tested;
* unavailable.

## 13. P04 Student/AI Development Record

For every major implementation:

```text
P03 decision
→ AI implementation approach
→ student review
→ code change
→ test
→ verification
→ remaining risk
```

---

# 23. Final Verification Table

Create:

| Finding | P03 Decision | Implemented? | Baseline Tested? | Fix Tested? | Integration Tested? | Remaining Risk |
| ------- | ------------ | -----------: | ---------------: | ----------: | ------------------: | -------------- |
| F-01    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-02    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-03    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-04    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-05    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-06    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-07    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-08    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-09    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-10    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-11    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-12    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-13    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-14    | ...          |          ... |              ... |         ... |                 ... | ...            |
| F-15    | ...          |          ... |              ... |         ... |                 ... | ...            |

---

# 24. Required Final Output

At the end of the task report:

### Files modified

List every modified source/config/test/documentation file.

### Files created

At minimum:

```text
review/P04 - Security Implementation & Verification.md
```

### Tests

Report exact results.

Example:

```text
pytest:
XX passed
X failed
X skipped
```

### Security demonstrations

Report exact results for:

* F-01;
* F-02;
* F-03;
* F-04;
* F-05;
* F-07.

### Docker

State:

```text
Verified
```

or:

```text
Not verified — Docker unavailable
```

### CI

State actual status.

### Remaining risks

List unresolved security limitations.

### Unexpected problems

If implementation deviated from P03, explain:

1. what changed;
2. why;
3. who/what caused the change;
4. how it was verified.

Never hide deviations.

---

# 25. Absolute Prohibitions

Do NOT:

* claim a fix without a test;
* claim an attack is prevented without reproducing the attack;
* claim Docker works without running Docker;
* claim CI passes without CI execution;
* remove failing tests just to obtain green status;
* silently change P03 decisions;
* expose secrets in logs;
* replace ML-KEM with another cryptographic algorithm;
* implement homemade cryptography;
* introduce unnecessary infrastructure;
* rewrite the entire project;
* declare the project "production secure."

The final project remains an educational simulation.

The objective is:

> **small, understandable, demonstrable security improvements supported by evidence.**

---

# 26. Definition of Done

P04 is complete only when:

* all approved P03 implementation decisions are addressed;
* fail-first tests exist for major security findings;
* baseline failures are documented where reproducible;
* fixes are implemented;
* new tests pass;
* original regression tests pass;
* end-to-end flow works;
* security attacks are re-tested;
* remaining risks are documented;
* deferred findings are documented;
* README is updated;
* P04 report is created;
* no unsupported security claims are made.

The project should be ready for a later **P05 independent verification / security re-test phase**.
