# P05 — Independent Verification & Security Re-Test

## 0. Role

You are an independent security verification assistant for the university project:

**PQCBridge Legacy Edge-Cloud — Post-Quantum Security Migration Simulation**

The project has completed:

* P01 — Baseline Generation
* P02 — Baseline Technical Review
* P03 — Student Security Evaluation & Design Decisions
* P04 — Security Implementation & Verification

P04 reports that the approved security decisions have been implemented.

Your role in P05 is NOT to trust the P04 report.

Your role is to independently verify whether the implemented security controls actually work.

---

# 1. Critical Independence Rule

Treat the P04 report as a claim that must be tested.

Do NOT assume:

* 101 tests passing means all security properties are satisfied;
* an attack demonstration is correct merely because P04 says it worked;
* unit tests prove end-to-end behavior;
* a security log message proves an attack was blocked;
* a rejected connection proves the correct security reason;
* a passing test proves the system is secure.

Reproduce important claims independently.

If a P04 claim cannot be reproduced, report:

> NOT VERIFIED

Do not change the code merely to make P05 pass.

---

# 2. No Code Modification at the Beginning

For the first part of P05:

**DO NOT MODIFY SOURCE CODE.**

You may:

* inspect source code;
* inspect tests;
* run tests;
* create temporary external attack scripts;
* create temporary test harnesses;
* run integration experiments;
* inspect logs;
* inspect health endpoints;
* inspect stored readings.

Do not modify:

* `common/`
* `device/`
* `gateway/`
* `cloud/`
* `tests/`
* Docker files
* CI files
* README

until the independent verification is complete.

If a defect is discovered, record it first.

Do not immediately fix it.

---

# 3. Read Before Testing

Read:

```text
README.md
CLAUDE.md

review/P02 - Baseline Technical Review.md
review/P03 - Student Security Evaluation & Design Decisions.md
review/P04 - Security Implementation & Verification.md
```

Inspect the complete source tree.

Pay special attention to:

```text
common/
device/
gateway/
cloud/
tests/
```

Also inspect:

```text
requirements.txt
docker-compose.yml
```

Compare the actual implementation against the P03 design.

---

# 4. Environment Record

Record:

* OS;
* Python version;
* cryptography version;
* pytest version;
* Docker availability;
* Git status;
* current test count.

Do not claim Docker or CI verification if they cannot actually be executed.

---

# 5. Baseline Regression Check

Run:

```bash
pytest -q
```

Record exact results.

Expected current result according to P04:

```text
101 passed
0 failed
0 skipped
```

If the result differs:

* stop;
* investigate;
* document the difference;
* do not modify code just to restore the expected number.

---

# 6. Independent Security Verification

Perform the following security tests independently of the P04 demonstrations.

---

# 7. F-01 — ML-KEM Public-Key Substitution

Objective:

Determine whether a cloud ML-KEM public-key substitution is rejected.

Test procedure:

1. Establish the normal gateway-cloud handshake.
2. Capture or simulate the cloud public key.
3. Replace it with a different valid ML-KEM-768 public key.
4. Send the substituted key to the gateway.
5. Observe the gateway behavior.

Expected:

```text
Fingerprint mismatch
→ handshake rejected
→ no session established
→ gateway remains operational
```

Verify that:

* the substituted key is not accepted;
* no session is created using the attacker key;
* the gateway does not silently update its pin;
* the gateway does not crash.

Also test:

* malformed public key;
* invalid public-key length;
* invalid base64.

Record actual evidence.

---

# 8. F-02 — Downgrade / Capability Manipulation

Independently test the fallback policy.

Test at least:

### Case 1

Known authenticated legacy device.

Expected:

```text
legacy fallback accepted
```

### Case 2

Known device claiming modern capability.

Expected:

```text
REJECT
```

if this is the P03 policy.

### Case 3

Unknown device.

Expected:

```text
REJECT
```

### Case 4

Malformed capability list.

Expected:

```text
REJECT
```

### Case 5

Capability modification/tampering.

Expected:

```text
authentication failure / REJECT
```

Verify that a plaintext capability modification cannot silently force an insecure fallback.

Record:

* input;
* authentication state;
* gateway decision;
* logs;
* resulting connection state.

---

# 9. F-03 — Malformed Gateway Handshake

Independently reproduce the P02 crash case.

Send malformed handshake input such as:

```json
{
  "type": "mlkem_pubkey",
  "cloud_id": "fake-cloud"
}
```

without:

```text
public_key
```

Expected after P04:

```text
ProtocolError
connection controlled/rejected
gateway process remains alive
```

Verify process liveness independently.

Do NOT consider:

```text
"error was logged"
```

sufficient evidence.

The process must actually remain alive.

Also test:

* missing type;
* wrong type;
* malformed JSON;
* malformed base64;
* invalid key length.

---

# 10. F-04 — Malformed Cloud Encapsulation

Send malformed encapsulation input:

```json
{
  "type": "mlkem_encaps"
}
```

without:

```text
ciphertext
```

Expected:

```text
controlled protocol error
handler does not unexpectedly terminate service
```

Verify:

* cloud process remains alive;
* subsequent valid connections still work;
* no uncontrolled traceback is produced;
* error metric behavior is correct if P03 requires it.

This last check is important.

A handler thread may die while the overall process remains alive.

Therefore test both:

```text
process liveness
```

and:

```text
service availability after attack
```

---

# 11. F-05 — Replay Protection

This is one of the most important independent tests.

Perform:

```text
valid message
→ ACCEPT
```

Then replay the exact same message:

```text
same ciphertext
same nonce
same sequence
same authenticated data
```

Expected:

```text
REJECT
```

and:

```text
exactly one reading stored
```

Then test:

```text
sequence 1 → ACCEPT
sequence 2 → ACCEPT
sequence 2 → REJECT
sequence 1 → REJECT
sequence 3 → ACCEPT
```

Also test:

### Modified sequence

Take a valid encrypted message and change the sequence number.

Expected:

```text
authentication failure / REJECT
```

### Modified device ID

Change the device ID.

Expected:

```text
authentication failure / REJECT
```

### Modified session ID

If session ID is part of AAD, modify it.

Expected:

```text
authentication failure / REJECT
```

### Large jump

Test the documented no-jump-window behavior.

If:

```text
sequence 100
```

causes the device to become temporarily unable to communicate until its counter catches up, document this as a confirmed limitation.

Do NOT hide the limitation.

---

# 12. F-06 — Per-Device Key Isolation

Test:

### Valid device

```text
dev-01 + correct key
→ ACCEPT
```

### Wrong key

```text
dev-01 + dev-02 key
→ REJECT
```

### Impersonation

```text
dev-02 claims to be dev-01
→ REJECT
```

### Unknown device

```text
dev-999
→ REJECT
```

Verify that device identity and authentication credentials cannot be freely substituted.

Do not expose the actual secret values in the report.

---

# 13. F-07 — Session Failure and Reconnect

Independently reproduce cloud failure.

Procedure:

1. Establish a valid session.
2. Verify normal forwarding.
3. Terminate or interrupt the cloud connection.
4. Attempt another forwarding operation.
5. Observe gateway state.
6. Allow/retrigger reconnect.
7. Verify the new session.

Expected:

```text
ESTABLISHED
      ↓
cloud failure
      ↓
session invalidated
      ↓
health becomes degraded/disconnected
      ↓
reconnect
      ↓
new session
      ↓
health becomes OK
```

Verify:

* old session is not incorrectly reported as active;
* forwarding failure is detected;
* reconnect occurs;
* a new session ID is created;
* health state becomes truthful;
* cloud session cleanup works as designed.

---

# 14. F-08 — Metrics

Independently inspect several metrics.

Verify:

* payload size uses bytes;
* forwarding time uses the correct unit;
* fallback count has the documented meaning;
* errors increase when controlled protocol errors occur.

Do not only inspect variable names.

Trigger actual events and compare the metric before/after.

---

# 15. F-13 — Health

Test health under:

### Normal state

Expected:

```text
OK
```

### Cloud disconnected

Expected:

```text
degraded / disconnected
```

according to P03/P04.

### After reconnect

Expected:

```text
OK
```

Verify that health reflects the actual session state rather than merely whether a socket object exists.

---

# 16. Protocol Robustness

Perform a small malformed-input test set.

Include:

* empty message;
* invalid JSON;
* JSON array;
* JSON string;
* missing fields;
* wrong field types;
* invalid base64;
* truncated message;
* oversized message;
* unexpected message type.

The service must not crash.

Record whether each input results in:

* ACCEPT;
* REJECT;
* controlled error;
* connection close.

---

# 17. Cryptographic Verification

Do NOT implement cryptography yourself.

Verify the existing implementation uses:

```text
ML-KEM-768
HKDF
ChaCha20-Poly1305
```

Verify:

* ML-KEM shared secrets match between encapsulation and decapsulation;
* incorrect ciphertext does not result in successful message decryption;
* AEAD detects modified ciphertext;
* AEAD detects modified authenticated data;
* nonce length is correct;
* keys have expected sizes;
* ML-KEM private keys are not logged.

Do not attempt to prove the mathematical security of ML-KEM itself.

The goal is to verify correct API usage and protocol integration.

---

# 18. Secret Leakage Verification

Search source code, logs, and generated output for:

* private keys;
* shared secrets;
* PSKs;
* raw session keys;
* sensitive authentication material.

Expected:

```text
No secrets exposed in normal logs or health endpoints.
```

Fingerprints and identifiers are acceptable if they do not reveal key material.

---

# 19. Regression After Security Tests

After independent security testing:

```bash
pytest -q
```

The security experiments must not leave the project in a broken state.

If the project uses temporary state files:

* reset them;
* explain the reset;
* rerun tests.

---

# 20. Docker

Check whether Docker is available.

If Docker is available:

1. build the images;
2. start compose;
3. verify health;
4. execute the normal end-to-end flow;
5. perform at least one failure/reconnect test.

If Docker is unavailable:

```text
Docker verification: NOT AVAILABLE
```

Do not simulate Docker results.

---

# 21. CI

Check the repository status.

If CI can be executed locally, do so.

If the project is still not connected to a remote Git repository:

```text
Remote CI: NOT VERIFIED
```

Do not claim CI success.

---

# 22. Independent Attack Matrix

Create:

| Attack                   | P02 Baseline   | P04 Claim  | P05 Independent Result | Status    |
| ------------------------ | -------------- | ---------- | ---------------------- | --------- |
| F-01 key substitution    | accepted       | rejected   | ...                    | PASS/FAIL |
| F-02 downgrade           | possible       | rejected   | ...                    | PASS/FAIL |
| F-03 malformed handshake | crash          | controlled | ...                    | PASS/FAIL |
| F-04 malformed encaps    | thread failure | controlled | ...                    | PASS/FAIL |
| F-05 replay              | accepted       | rejected   | ...                    | PASS/FAIL |
| F-06 impersonation       | possible       | rejected   | ...                    | PASS/FAIL |
| F-07 cloud failure       | wedged         | reconnect  | ...                    | PASS/FAIL |
| F-08 metric errors       | inconsistent   | corrected  | ...                    | PASS/FAIL |
| F-13 health              | misleading     | truthful   | ...                    | PASS/FAIL |

Do not mark PASS unless independently verified.

---

# 23. Evidence Classification

For every important claim classify the evidence as:

### PASS

Independently reproduced and expected behavior observed.

### PARTIAL

Some aspects work, but the complete security property was not demonstrated.

### FAIL

The P04 claim could not be reproduced or the vulnerability remains.

### NOT VERIFIED

The required environment/test could not be executed.

This distinction is mandatory.

---

# 24. Residual Risk Verification

P04 documented remaining risks.

Independently check that they are still honestly described.

Important examples include:

* no TLS;
* no full PKI;
* no gateway authentication if deferred;
* simulated provisioning;
* static configured keys;
* gateway restart replay-state loss;
* no replay jump window;
* no device reconnect;
* Docker/CI limitations.

Do not call a documented limitation a vulnerability if it was intentionally accepted as project scope.

Instead classify it as:

```text
Accepted limitation
```

or:

```text
Deferred security improvement
```

---

# 25. Do Not Fix Problems in P05

If an independent test discovers a defect:

STOP.

Record:

```text
Finding:
...

Expected:
...

Actual:
...

Security impact:
...

Reproduction:
...

Affected component:
...

Recommended action:
...
```

Do NOT modify the code during the initial P05 verification.

Only after the complete verification report has been produced should a separate corrective phase be considered.

---

# 26. P05 Report

Create:

`review/P05 - Independent Security Verification & Re-test.md`

The report must contain:

## 1. Executive Summary

State whether the P04 security claims were independently verified.

## 2. Environment

Exact versions and available tools.

## 3. Baseline Regression Result

Exact pytest result.

## 4. P04 Claims Under Verification

Summarize what P04 claimed.

## 5. Independent Test Method

Explain how each security property was tested.

## 6. F-01 Verification

Key substitution.

## 7. F-02 Verification

Downgrade/capability manipulation.

## 8. F-03 Verification

Malformed gateway handshake.

## 9. F-04 Verification

Malformed cloud encapsulation.

## 10. F-05 Verification

Replay.

## 11. F-06 Verification

Per-device authentication/isolation.

## 12. F-07 Verification

Session failure/reconnect.

## 13. F-08 Verification

Metrics.

## 14. F-13 Verification

Health.

## 15. Protocol Robustness

Malformed-input results.

## 16. Cryptographic Integration Verification

ML-KEM/HKDF/AEAD behavior.

## 17. Secret Leakage Verification

Logs and repository inspection.

## 18. Regression Testing

Final pytest result.

## 19. Docker / CI

Actual status.

## 20. Independent Attack Matrix

Complete table.

## 21. Failed or Partially Verified Claims

Do not hide failures.

## 22. Remaining Risks

Updated based on actual evidence.

## 23. Recommendations for P06

Only if further work is necessary.

---

# 27. Required Final Verdict

At the end of the report provide:

```text
P05 Overall Verdict:

[PASS / PARTIAL PASS / FAIL]

Reason:
...

Security controls independently verified:
...

Security controls only partially verified:
...

Security controls not verified:
...

New defects discovered:
...

Remaining accepted risks:
...

Recommended next phase:
...
```

Use **PARTIAL PASS** if some important controls pass but others cannot be fully verified.

Do not force a PASS.

---

# 28. Important Reporting Principle

The purpose of P05 is not to prove:

> "The project is secure."

The purpose is to determine:

> "Which security claims made by P04 are supported by independent evidence?"

Therefore, an honest result such as:

```text
F-01 PASS
F-02 PASS
F-03 PASS
F-04 PASS
F-05 PASS
F-06 PASS
F-07 PASS
Docker NOT VERIFIED
CI NOT VERIFIED
Gateway authentication NOT IMPLEMENTED
Replay state lost after gateway restart
```

is a strong result.

Do not hide limitations to make the project appear stronger.

---

# 29. Final Output Rules

At the end of execution report:

### Tests

Exact pytest result.

### Independent attacks

Exact result for every attack.

### Security verdict

PASS / PARTIAL PASS / FAIL.

### Files created

At minimum:

```text
review/P05 - Independent Security Verification & Re-test.md
```

### Files modified

During the initial P05 verification:

```text
Expected: none
```

If any file was modified accidentally or necessarily, disclose it explicitly.

### Docker

Actual status.

### CI

Actual status.

### New findings

List every new defect.

### Remaining risks

List unresolved limitations.

### P06 recommendation

Explain whether another implementation phase is required.

---

# 30. Definition of Done

P05 is complete only when:

* P04 claims were independently tested;
* major attacks were reproduced independently;
* replay protection was independently verified;
* key substitution was independently verified;
* downgrade protection was independently verified;
* malformed-input resilience was independently verified;
* session failure was independently verified;
* regression tests were executed;
* secret leakage was checked;
* Docker/CI status was honestly reported;
* PASS/PARTIAL/FAIL/NOT VERIFIED distinctions were used;
* no defects were hidden;
* no unsupported production-security claims were made;
* P05 report was created.

P05 is an **independent verification phase**, not another implementation phase.
