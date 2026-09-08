# P06 — NEW-1 Fix and Final Security Verification

## 0. Role

You are the implementation and verification assistant for the university project:

**PQCBridge Legacy Edge-Cloud — Post-Quantum Security Migration Simulation**

Project phases completed:

* P01 — Baseline Generation
* P02 — Baseline Technical Review
* P03 — Student Security Evaluation & Design
* P04 — Security Implementation & Verification
* P05 — Independent Security Verification & Re-test

P05 independently verified all major P04 security claims but discovered one new defect:

> **NEW-1 — Invalid AEAD nonce length can cause an unhandled ValueError, uncontrolled traceback, handler-thread termination, and missing error-metric increment.**

P05 classified the overall result as:

> PARTIAL PASS

P06 exists specifically to address NEW-1.

---

# 1. P06 Scope

The ONLY mandatory implementation target is:

> **NEW-1 — AEAD nonce-length validation and controlled error handling**

Do NOT implement unrelated improvements.

Do NOT implement:

* TLS;
* PKI;
* gateway authentication;
* keepalive;
* heartbeat;
* NEW-2;
* NEW-3;
* replay windows;
* database persistence;
* production key management;
* rate limiting;
* thread pools;
* new cryptographic algorithms.

NEW-2 and NEW-3 remain documented limitations unless a separate future phase is explicitly approved.

---

# 2. Read Existing Evidence First

Before changing anything, read:

```text
README.md
CLAUDE.md

review/P02 - Baseline Technical Review.md
review/P03 - Student Security Evaluation & Design Decisions.md
review/P04 - Security Implementation & Verification.md
review/P05 - Independent Security Verification & Re-test.md
```

Inspect:

```text
common/crypto.py
common/protocol.py
common/metrics.py
gateway/
cloud/
device/
tests/
```

Find the exact implementation paths involved in NEW-1.

Do not assume the P05 description is correct without inspecting the code.

---

# 3. Preserve P05 Evidence

Do not modify or delete the P05 report.

The P05 finding must remain documented as:

```text
NEW-1
```

The project history must show:

```text
P04
  ↓
P05 independent testing
  ↓
NEW-1 discovered
  ↓
P06 fix
  ↓
P06 verification
```

Do NOT rewrite P05 to make it appear that NEW-1 never existed.

---

# 4. Record Baseline Before Modification

Before modifying source code:

Run:

```bash
pytest -q
```

Record:

* exact test count;
* passed;
* failed;
* skipped;
* duration.

Expected baseline from P05:

```text
101 passed
0 failed
0 skipped
```

If the result differs:

STOP and investigate.

Do not modify code simply to restore the expected number.

---

# 5. Fail-First Test — Mandatory

Before fixing NEW-1, create or run a test that demonstrates the current vulnerability.

The test must provide an invalid AEAD nonce length.

Example:

```text
valid encrypted message
+
8-byte nonce
```

The expected secure behavior is:

```text
invalid nonce length
→ controlled protocol/security error
→ connection rejected
→ handler remains stable
→ errors metric increments
→ service remains available
```

The current P05-observed behavior is:

```text
8-byte nonce
→ ValueError("Nonce must be 12 bytes")
→ unhandled exception
→ traceback
→ handler thread terminates
→ errors metric not incremented
```

The fail-first test MUST demonstrate the baseline defect before the fix.

Do not skip directly to a passing test.

Record the actual failure.

---

# 6. Root Cause Analysis

Determine exactly where NEW-1 originates.

The implementation must distinguish:

```text
malformed attacker-controlled input
```

from:

```text
unexpected programming failure
```

Do NOT solve this by adding:

```python
except Exception:
```

around large sections of code.

Instead validate attacker-controlled input at the appropriate boundary.

---

# 7. Nonce Validation

ChaCha20-Poly1305 in this project expects a 12-byte nonce.

Ensure attacker-controlled nonce data is validated before the AEAD operation is invoked.

The validation should reject:

* empty nonce;
* 8-byte nonce;
* 11-byte nonce;
* 13-byte nonce;
* excessively long nonce;
* malformed decoded nonce.

A valid 12-byte nonce must continue to work.

Do not change the cryptographic algorithm.

Do not replace ChaCha20-Poly1305.

Do not manually implement AEAD.

Use the existing `cryptography` implementation.

---

# 8. Error Handling

An invalid nonce is malformed protocol/security input.

It must NOT produce an uncontrolled traceback.

The selected error should integrate with the project's existing error-handling model.

Prefer the existing:

```text
ProtocolError
```

or the project's established controlled error type if the code structure requires another existing exception.

Do not introduce unnecessary exception classes.

Expected behavior:

```text
attacker input
    ↓
nonce validation
    ↓
controlled error
    ↓
safe log
    ↓
errors metric increment
    ↓
connection/request rejected
```

The service must remain operational.

---

# 9. Error Metric

P05 specifically observed that NEW-1 bypassed the error metric.

After the fix, verify that the malformed nonce causes the appropriate error counter to increase exactly once for the relevant event.

Test:

```text
before = errors
send invalid nonce
after = errors
```

Expected:

```text
after = before + 1
```

If the existing architecture counts the error at a different layer, document that behavior rather than artificially incrementing it twice.

Avoid double-counting.

---

# 10. Gateway Verification

P05 found NEW-1 on gateway paths.

Independently verify the gateway.

Test at least:

### 8-byte nonce

Expected:

```text
REJECT
controlled error
no traceback
gateway remains alive
errors increment
```

### 11-byte nonce

Expected:

```text
REJECT
```

### 13-byte nonce

Expected:

```text
REJECT
```

### 12-byte nonce

Expected:

```text
normal behavior
```

Do not merely unit-test the helper.

At least one test must exercise the actual gateway message-processing path.

---

# 11. Cloud Verification

P05 found NEW-1 on a cloud path.

Repeat the same validation for the cloud.

Test:

```text
invalid nonce
→ controlled rejection
→ no traceback
→ cloud process remains alive
→ subsequent valid request works
```

Again, test the actual message-processing path, not only the crypto helper.

---

# 12. Regression Tests

Add focused regression tests.

At minimum:

### Unit-level

```text
12-byte nonce → accepted
wrong nonce length → rejected
```

### Gateway integration

```text
invalid nonce → controlled error
gateway remains alive
```

### Cloud integration

```text
invalid nonce → controlled error
cloud remains available
```

### Metrics

```text
invalid nonce → error counter changes correctly
```

Do not remove existing tests.

Do not weaken assertions simply to obtain green tests.

---

# 13. Regression Suite

After implementation:

```bash
pytest -q
```

All existing tests must pass.

The expected count should be greater than or equal to the P05 count if new tests were added.

Expected pattern:

```text
101 existing tests
+
NEW-1 regression tests
=
new total
```

Report the exact number.

Do not claim "all tests pass" without executing the test suite.

---

# 14. Independent TCP Re-test

After unit/integration tests pass, perform a fresh TCP-level attack.

Do NOT reuse only the P04 test.

Construct attacker-controlled input independently.

Test:

```text
attacker
  ↓
real TCP connection
  ↓
valid protocol envelope
  ↓
malicious nonce length
  ↓
gateway/cloud
```

Verify:

* no uncontrolled traceback;
* no handler termination;
* controlled rejection;
* error metric behavior;
* service remains available;
* a valid request immediately afterward succeeds.

This is required because P04 previously had a real integration bug that unit tests missed.

---

# 15. Regression After Attack

After all live attacks:

```bash
pytest -q
```

The attack harness must not leave persistent state that affects the tests.

Use temporary state directories and temporary ports where appropriate.

Do not modify production/test state merely to make the result pass.

---

# 16. Re-Test Previously Verified Security Controls

Because P06 modifies shared cryptographic/error-handling code, perform a lightweight regression of previously verified controls.

At minimum verify:

### F-01

Key substitution still rejected.

### F-02

Downgrade manipulation still rejected.

### F-05

Replay still rejected.

### F-06

Wrong-device key still rejected.

### F-07

Cloud failure/reconnect still works.

You do NOT need to repeat the entire P05 campaign unless a shared component has been substantially changed.

If a previous security property is affected by the NEW-1 change, perform the full relevant test.

---

# 17. Cryptographic Safety Check

Verify that the fix did not alter:

* ML-KEM-768;
* HKDF parameters;
* ChaCha20-Poly1305 algorithm;
* key sizes;
* nonce generation for valid messages;
* encryption/decryption semantics.

The fix should add input validation, not replace cryptographic primitives.

---

# 18. Secret Handling

Repeat the secret-handling check.

Ensure the new error-handling code does not log:

* nonce contents unnecessarily;
* keys;
* PSKs;
* shared secrets;
* private keys.

If logging the invalid nonce is useful for debugging, prefer:

```text
nonce_length=8
```

rather than logging the raw nonce.

---

# 19. NEW-2 — Health During Initial Retry

Do NOT fix NEW-2 in P06.

P05 observed:

> `/health` does not exist during the initial establishment retry loop.

Keep this as a documented operational limitation unless P03/P04 explicitly required otherwise.

The P06 report should state:

```text
NEW-2:
Not fixed.

Reason:
Outside mandatory P06 scope and not required to resolve the security defect NEW-1.
```

---

# 20. NEW-3 — No Cloud Keepalive

Do NOT fix NEW-3 in P06.

P05 observed:

> The gateway only discovers a dead cloud connection when the next forwarding operation fails.

Keep this design.

Document:

```text
No independent keepalive/heartbeat mechanism is implemented.

A dead cloud connection is detected when the next forwarding operation fails.
```

This is an accepted operational limitation for the educational prototype.

Do not add heartbeat infrastructure.

---

# 21. P06 Scope Control

At the end, verify that the implementation stayed within scope.

Expected source changes should be limited to:

```text
common/crypto.py
```

plus the necessary regression/integration tests and P06 documentation.

If other production files were changed:

Explain exactly:

1. file;
2. reason;
3. relationship to NEW-1;
4. verification.

Do not make unrelated cleanup changes.

---

# 22. P06 Report

Create:

```text
review/P06 - NEW-1 Fix & Final Security Verification.md
```

The report must contain:

## 1. Executive Summary

Explain:

* NEW-1 discovered in P05;
* why it mattered;
* how it was fixed;
* final verification result.

## 2. P05 Finding

Quote/paraphrase the relevant technical finding.

## 3. Root Cause

Explain the exact failure path.

## 4. Fail-First Evidence

Show:

```text
Before fix:
invalid nonce
→ unhandled ValueError
→ traceback
→ metric bypass
```

## 5. Implementation

Describe the minimal code change.

## 6. Regression Tests

List new tests.

## 7. Gateway Verification

Results.

## 8. Cloud Verification

Results.

## 9. Metrics Verification

Results.

## 10. Independent TCP Attack

Results.

## 11. Regression Suite

Exact pytest result.

## 12. Previously Verified Controls

Brief re-test results for F-01/F-02/F-05/F-06/F-07.

## 13. NEW-2 / NEW-3

Explicitly document why they remain unresolved.

## 14. Remaining Risks

Updated list.

## 15. Files Modified

Exact list.

## 16. Final Security Verdict

PASS / PARTIAL PASS / FAIL.

---

# 23. Required Before/After Table

Create:

| Test                  | P05 behavior    | P06 expected behavior | P06 result |
| --------------------- | --------------- | --------------------- | ---------- |
| 12-byte nonce         | valid           | ACCEPT                | ...        |
| 8-byte nonce          | traceback       | controlled REJECT     | ...        |
| 11-byte nonce         | traceback/error | controlled REJECT     | ...        |
| 13-byte nonce         | traceback/error | controlled REJECT     | ...        |
| gateway invalid nonce | handler failure | handler survives      | ...        |
| cloud invalid nonce   | handler failure | handler survives      | ...        |
| error metric          | not counted     | counted correctly     | ...        |

---

# 24. Final Security Status

If NEW-1 is completely fixed and independently verified, the overall project may be reported as:

> **PASS with documented residual risks**

Do NOT call the project:

> production secure

Do NOT claim:

> all security vulnerabilities are eliminated

The appropriate statement is:

> All security controls selected in P03 and implemented in P04 were independently verified in P05, and the additional NEW-1 robustness defect discovered during P05 was fixed and independently re-tested in P06. The project retains documented limitations that are outside the scope of this educational prototype.

If NEW-1 cannot be fully verified, use:

> PARTIAL PASS

Do not force a PASS.

---

# 25. Final Verification Matrix

Create:

| Finding | Status after P06    | Evidence |
| ------- | ------------------- | -------- |
| F-01    | ...                 | ...      |
| F-02    | ...                 | ...      |
| F-03    | ...                 | ...      |
| F-04    | ...                 | ...      |
| F-05    | ...                 | ...      |
| F-06    | ...                 | ...      |
| F-07    | ...                 | ...      |
| F-08    | ...                 | ...      |
| F-13    | ...                 | ...      |
| NEW-1   | ...                 | ...      |
| NEW-2   | Deferred            | ...      |
| NEW-3   | Accepted limitation | ...      |

---

# 26. Final Output Rules

At the end report:

### Implementation

What changed.

### Files modified

Exact list.

### Tests

Exact pytest result.

### Fail-first

Exact baseline failure.

### NEW-1 attack

Exact result.

### Previous security controls

Exact re-test result.

### Docker

Actual status.

If unavailable:

```text
NOT VERIFIED — Docker unavailable
```

### CI

Actual status.

If unavailable:

```text
NOT VERIFIED — CI environment unavailable
```

### Remaining risks

List all remaining limitations.

### Final verdict

PASS / PARTIAL PASS / FAIL.

### P06 scope compliance

Confirm whether unrelated code was modified.

---

# 27. Definition of Done

P06 is complete only when:

* NEW-1 fail-first behavior was demonstrated;
* root cause was identified;
* nonce validation was implemented;
* malformed nonce is handled safely;
* gateway remains alive;
* cloud remains alive;
* error metric is correct;
* valid 12-byte nonce still works;
* regression tests pass;
* independent TCP attack succeeds in demonstrating rejection;
* previously verified security controls still work;
* NEW-2 remains documented rather than silently fixed;
* NEW-3 remains documented rather than silently fixed;
* no secrets are exposed;
* Docker/CI status is honest;
* P06 report is created;
* final verdict is supported by evidence.

P06 is a focused corrective and final verification phase.

Do not expand the project scope.
