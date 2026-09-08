# P08 – Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation

## 0. Role

You are acting as a senior software security engineer and software maintenance reviewer working on the existing university project:

**PQCBridge Legacy Edge-Cloud — Post-Quantum Security Migration Simulation**

Repository:

`D:\Code\pqcbridge-legacy-edge-cloud`

Remote repository:

`https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud`

This is **P08**, following the existing project phases:

* P01 – Baseline Generation
* P02 – Baseline Technical Review
* P03 – Student Evaluation & Security Design Decisions
* P04 – Security Implementation & Verification
* P05 – Independent Security Verification & Re-test
* P06 – NEW-1 Fix & Final Security Verification
* P07 – Final Project Evaluation & Evidence Consolidation
* **P08 – Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation**

P08 must preserve the existing engineering history. **Do not rewrite or silently alter P02–P07.**

---

# 1. Project Context

The project is a small educational legacy edge-cloud simulation:

```text
Legacy Device
      |
      v
   Gateway
      |
      v
    Cloud
```

The project uses:

* ML-KEM-768 for post-quantum key establishment
* HKDF for session-key derivation
* ChaCha20-Poly1305 for authenticated encryption
* authenticated device hellos
* per-device credentials
* sequence-based replay protection
* cloud public-key fingerprint pinning
* session lifecycle and reconnect handling
* health endpoints
* metrics and logging
* pytest-based verification
* GitHub Actions CI

Previous P07 final verdict was:

**PASS WITH DOCUMENTED RESIDUAL RISKS**

P08 is triggered because additional adversarial testing identified a new set of findings and, more importantly, demonstrated that several weaknesses can be chained into a more serious end-to-end attack.

The goal of P08 is NOT to make the system production-ready.

The goal is to:

1. independently reproduce and document the new findings;
2. distinguish root vulnerabilities from compound attack effects;
3. demonstrate realistic attack chains using evidence;
4. identify the actual root causes;
5. perform targeted remediation only where justified;
6. use fail-first and regression testing;
7. preserve previous security controls;
8. document residual risks honestly;
9. prepare the project for a later independent final verification phase.

---

# 2. Critical Rules

Follow these rules strictly.

## Rule 1 – Do not blindly trust previous AI-generated conclusions

Treat the current source code, tests, configuration, logs, and reproducible behavior as the source of truth.

Do not assume P02–P07 findings are still correct without checking the current code.

Do not assume the new BF findings are correct without reproducing them.

---

## Rule 2 – Do not modify P02–P07 reports

Do NOT rewrite, delete, or retroactively alter:

* P02
* P03
* P04
* P05
* P06
* P07

P08 must be an additive maintenance/evolution phase.

If P07 said something was true at the time of P07, preserve that historical record.

---

## Rule 3 – Do not expand the scope without explicit approval

The approved P08 remediation scope is initially:

### MUST investigate and, if reproducible, remediate

* BF-01 – Cloud does not authenticate Gateway
* BF-03A – insecure/hard-coded device credential management

### MUST investigate but do NOT automatically remediate

* BF-02 – connection flooding / one-thread-per-connection DoS
* BF-03B – unbounded sequence advancement / sequence-jump desynchronization
* BF-05 – unauthenticated `/health` and `/readings`

### MUST document as a negative result

* BF-04 – device ID timing side channel

### Compound findings to analyse and re-test

* BF-06 – targeted cloud-side data blindness through sequence-state poisoning
* BF-07 – plausible-data replacement / false data continuity

Do not introduce TLS, OAuth, JWT, a complete PKI, a new identity-management system, asynchronous networking, a full rate limiter, or other major architectural changes unless explicitly required by the user.

---

# 3. Initial Repository Inspection

Before changing any source code:

1. inspect the repository tree;
2. inspect `README.md`;
3. inspect `CLAUDE.md`;
4. inspect `requirements.txt`;
5. inspect `.gitignore`;
6. inspect `common/`;
7. inspect `device/`;
8. inspect `gateway/`;
9. inspect `cloud/`;
10. inspect `tests/`;
11. inspect `review/P02*` through `review/P07*`;
12. inspect existing CI configuration;
13. inspect current git status and commit;
14. verify that the working tree is clean or explicitly report any pre-existing changes.

Do not modify files during this inspection stage.

Report:

* current commit;
* current branch;
* current test count if discoverable;
* relevant security controls already implemented;
* existing limitations;
* files likely affected by P08.

---

# 4. Existing Baseline Must Be Re-established

Before implementing anything:

Run the existing test suite.

Expected previous baseline:

```text
120 passed
0 failed
0 skipped
```

Do not assume this number.

Record the actual result.

If the baseline is not green:

* stop remediation;
* diagnose the discrepancy;
* report whether it is environmental, test-related, or a regression.

Do not delete tests to make the suite green.

---

# 5. New BF Findings

Use the following findings as hypotheses to investigate.

## BF-01 – Cloud does not authenticate Gateway

### Description

The cloud verifies its own ML-KEM public-key identity through fingerprint pinning, but the cloud does not authenticate the identity of the connecting Gateway.

Potential impact:

**HIGH**

Potential attack:

```text
Attacker
   |
   | fake Gateway
   v
Cloud
   |
   | ML-KEM handshake accepted
   v
Session established
   |
   v
Attacker can inject readings
```

The critical claim to verify is:

> Can an unauthenticated attacker impersonate a Gateway, establish a cloud-accepted session, and inject readings without possessing a legitimate Gateway credential?

Do not assume this is true. Reproduce it.

Record:

* exact command or script used;
* relevant input;
* relevant protocol messages;
* gateway_id used;
* whether authentication was required;
* session establishment result;
* injected reading result;
* logs;
* timestamps where useful.

Do not log or expose real secret material.

---

# 6. BF-02 – Connection Flooding / Resource Exhaustion

### Description

The current design may use approximately:

```text
one connection -> one thread
```

with no effective connection rate limit or bounded worker pool.

Potential impact:

**MEDIUM-HIGH**

Known empirical evidence:

```text
Threads: approximately 6 -> 304
File handles: approximately 207 -> 2007
```

Reproduce safely.

Do not perform uncontrolled denial-of-service against the user's operating system.

Use a bounded test that demonstrates resource growth.

Measure:

* number of connections;
* thread count;
* file descriptors / handles if safely measurable;
* process memory if useful;
* response behavior.

Correct terminology:

Do NOT describe the growth as "exponential" unless actual measurements demonstrate exponential growth.

Prefer:

> resource usage increased rapidly and approximately linearly with the number of open connections.

P08 must document this finding.

**Do not implement a large networking redesign in P08.**

Treat this as a deferred/residual operational risk unless the user explicitly changes the scope.

---

# 7. BF-03 – Device Credential Management + Sequence Jump

BF-03 contains TWO different root issues.

Do not merge them into one technical mechanism.

## BF-03A – Hard-coded / insecure device credential management

Investigate whether device credentials are embedded directly in source code or otherwise exposed through tracked source/configuration.

Potential impact:

**HIGH**

Potential attack:

```text
credential exposure
      |
      v
device impersonation
      |
      v
trusted-looking readings
```

If reproducible, implement the smallest safe remediation:

* remove credential secrets from Python source;
* use environment/configuration injection;
* preserve the existing per-device identity model;
* ensure example/demo configuration contains only clearly documented demo material;
* ensure real secret files are excluded by `.gitignore`;
* do not commit real secrets.

Do NOT redesign the complete credential-management architecture.

Add regression tests where appropriate.

---

## BF-03B – Unbounded Sequence Advancement

Investigate:

```text
seq > last_seq
```

with no maximum jump or additional state validation.

Demonstrate safely:

```text
normal device:
seq = 1
seq = 2
seq = 3

attacker:
seq = 99999

real device:
seq = 4

result:
REPLAY REJECTED
```

This is a potential:

> sequence-state poisoning / desynchronization

problem.

Do NOT automatically add a jump window.

The existing P03 design explicitly selected:

> monotonic per-device sequence + no jump window

A jump window may weaken replay protection if implemented incorrectly.

Therefore:

* analyse the issue;
* reproduce it;
* document the impact;
* evaluate possible mitigations;
* do not change the replay algorithm unless explicitly approved.

The preferred P08 conclusion is likely:

> Replay protection remains effective against replay, but the current monotonic state can be poisoned by a sufficiently large accepted sequence number, creating a denial/desynchronization condition.

---

# 8. BF-04 – Device ID Timing Side Channel

Test the hypothesis that device ID enumeration can be distinguished through response timing.

The currently reported measurement is approximately:

```text
0.1 ms
```

or more precisely approximately:

```text
0.097 ms
```

The test must:

1. use repeated measurements;
2. avoid relying on a single sample;
3. compare valid and invalid/unknown IDs;
4. report variability/noise;
5. avoid claiming exploitability from a tiny difference alone.

If the evidence supports the existing conclusion:

> not practically exploitable in the tested environment

record BF-04 as a:

**negative result**

Do not artificially create a fix just to eliminate the finding.

---

# 9. BF-05 – Unauthenticated `/health` and `/readings`

Investigate:

* endpoint binding;
* whether endpoints bind to `0.0.0.0`;
* whether authentication is required;
* whether `/readings` exposes device IDs or readings;
* whether `/health` exposes operational state/metrics.

Potential impact:

**LOW – information disclosure in the educational deployment**

Reproduce safely.

Do NOT introduce a large API authentication architecture unless explicitly approved.

The likely P08 treatment is:

> documented deployment limitation; these endpoints should not be directly exposed to an untrusted network in production.

If possible, clearly distinguish:

```text
application health
      ≠
data authenticity
```

---

# 10. BF-06 – Targeted Cloud Data Blindness

Treat BF-06 as a **compound attack effect**, not as an independent root vulnerability.

Hypothesis:

```text
BF-01
unauthenticated Gateway
        +
BF-03B
unbounded sequence advancement
        ↓
attacker sends:
device_id = real device
seq = 99999
        ↓
cloud replay state becomes 99999
        ↓
real device packets are rejected
        ↓
target device data disappears
```

Reproduce this end-to-end.

The test must demonstrate:

1. fake Gateway/session can be established;
2. target device ID is selected;
3. malicious high sequence number is accepted;
4. cloud replay state changes;
5. legitimate subsequent device messages are rejected;
6. the effect persists until the relevant state/session behavior changes.

Record exact evidence.

Do not overclaim.

---

# 11. BF-07 – False Data Continuity / Data Sovereignty Impact

Treat BF-07 as a **compound impact**, not necessarily a separate root vulnerability.

After BF-06, test whether the attacker can continue with:

```text
seq = 100000
seq = 100001
seq = 100002
...
```

and inject plausible readings.

The important security question is:

> Can the attacker suppress legitimate data and replace it with a continuous, plausible-looking data stream while the application-level health status still appears normal?

Demonstrate:

```text
real device data
      ↓
suppressed

attacker data
      ↓
accepted

/health
      ↓
still appears healthy
```

Do not claim "zero alert" unless the current monitoring system was explicitly tested and no alert was generated.

Prefer:

> No alert was generated by the current application-level monitoring during the test.

or:

> The current health endpoint did not indicate that the underlying data stream had been compromised.

---

# 12. Combined Attack Chains

P08 must analyse the findings as attack chains.

## Attack Chain 1 – Data Blindness + Replacement

```text
BF-05
Reconnaissance
   ↓
BF-01
Fake Gateway
   ↓
ML-KEM session accepted
   ↓
BF-06
Sequence-state poisoning
   ↓
Real device suppressed
   ↓
BF-07
Plausible data injected
   ↓
/readings appears normal
```

This should be treated as the primary security scenario.

---

## Attack Chain 2 – DoS + Data Replacement

```text
BF-02
Connection flooding
   ↓
Real path disrupted
   ↓
BF-01
Fake Gateway/session
   ↓
BF-07
Attacker-controlled data stream
   ↓
BF-05
Health endpoint still appears available
```

This is an additional attack scenario.

---

## Attack Chain 3 – Persistent Device Impersonation

```text
BF-03A
Credential exposure
   ↓
Device impersonation
   ↓
Trusted-looking readings
   ↓
BF-03B / BF-06
Sequence-state poisoning
   ↓
Real device suppressed
```

Clearly state that this chain requires credential exposure/compromise.

It must NOT be described as a zero-credential attack.

---

## Attack Chain 4 – Single-message Silent Blindness

Demonstrate the minimum attack:

```text
BF-01
fake Gateway/session
      ↓
one malicious message
      ↓
device_id = target
seq = 99999
      ↓
real device data rejected
```

If evidence supports it, record that the attack requires no legitimate device key and only a very small number of protocol interactions.

If claiming "one round trip", provide evidence from logs or packet/message timing.

---

# 13. Root Cause Analysis

Do not claim that all findings have exactly two root causes.

The analysis should distinguish:

### Major interacting root causes

1. **Cloud authenticates itself to Gateway but does not authenticate Gateway identity.**
2. **Replay protection only checks monotonic increase (`seq > last`) without preventing extreme sequence-state advancement.**

### Additional independent weaknesses

3. unbounded connection/thread handling;
4. insecure credential storage/configuration;
5. unauthenticated monitoring/data endpoints.

BF-06 and BF-07 are mainly consequences of the interaction between the first two major causes.

BF-04 is a negative result.

---

# 14. Remediation Decision Matrix

Before modifying code, create and record this decision matrix:

| Finding | Classification                 | Decision                                          |
| ------- | ------------------------------ | ------------------------------------------------- |
| BF-01   | Root vulnerability             | REMEDIATE                                         |
| BF-02   | Operational/resource risk      | DEFER + DOCUMENT                                  |
| BF-03A  | Credential management weakness | REMEDIATE                                         |
| BF-03B  | Sequence-state poisoning       | ANALYSE + DOCUMENT; no automatic algorithm change |
| BF-04   | Negative result                | NO FIX                                            |
| BF-05   | Low-risk deployment limitation | DOCUMENT                                          |
| BF-06   | Compound attack effect         | Re-test after BF-01/BF-03 remediation             |
| BF-07   | Compound impact                | Re-test after remediation                         |

Do not change this matrix merely to make the test suite or project appear more secure.

If evidence requires a different decision, explain why before changing it.

---

# 15. BF-01 Remediation

Implement a minimal Gateway-to-Cloud authentication mechanism compatible with the existing architecture.

Preferred properties:

* explicit Gateway identity;
* per-Gateway credential or equivalent authenticated proof;
* authentication before accepting a Gateway session;
* reject unknown Gateway identities;
* reject invalid credentials;
* reject modified authentication data;
* do not expose secrets in logs;
* do not replace ML-KEM;
* do not remove existing cloud public-key fingerprint pinning.

The resulting flow should be conceptually:

```text
Gateway
   |
   | Gateway identity + authentication proof
   v
Cloud
   |
   +-- invalid -> reject
   |
   +-- valid
         ↓
     ML-KEM session
         ↓
     encrypted traffic
```

Do not use a cryptographic mechanism incorrectly just to satisfy the finding.

If the existing code already contains a suitable authentication primitive, reuse it.

---

# 16. BF-03A Remediation

Move device credentials out of source code.

Use:

* environment variables;
* configuration injection;
* or another minimal deployment configuration already compatible with the project.

Requirements:

* no real secrets committed;
* `.gitignore` updated if needed;
* demo credentials clearly labelled;
* existing tests continue to work;
* per-device isolation remains intact.

Do not break the educational local-run workflow.

---

# 17. Fail-First Testing

For every remediation:

1. write or add the regression test;
2. run the test against the unfixed code;
3. record the failure;
4. implement the fix;
5. rerun the same test;
6. confirm it passes.

Do not write tests only after the fix and call them fail-first.

For BF-01, include at minimum:

```text
test_valid_gateway_authentication
test_unknown_gateway_rejected
test_wrong_gateway_credential_rejected
test_tampered_gateway_authentication_rejected
test_unauthenticated_gateway_cannot_inject_reading
```

For BF-03A, include appropriate tests proving configuration-based credentials work and unauthorized/wrong credentials remain rejected.

Do not delete existing tests.

---

# 18. Regression Testing

After remediation:

Run:

```text
pytest -q
```

The final suite must have:

* 0 failures;
* 0 skipped;
* all previous security tests retained;
* all new regression tests passing.

Report the exact result.

Do not invent a test count.

---

# 19. Regression Security Checks

After BF-01/BF-03A remediation, re-test all important existing controls from P05/P06/P07:

### F-01

Cloud key substitution remains rejected.

### F-02

Downgrade/capability manipulation remains rejected.

### F-03

Malformed handshake remains controlled.

### F-04

Malformed encaps remains controlled.

### F-05

Replay remains rejected.

### F-06

Per-device credential isolation remains intact.

### F-07

Cloud session recovery remains functional.

### F-08

Metrics remain correct.

### F-13

Health remains truthful with respect to service/session state.

### NEW-1

Wrong-length nonce remains controlled.

Do not claim a previous finding remains fixed without testing it where practical.

---

# 20. Re-test the Compound Attack

This is a critical P08 requirement.

After remediation, attempt the previously successful attack:

```text
fake Gateway
    ↓
cloud session
    ↓
seq = 99999
    ↓
real device suppression
    ↓
fake continuous data
```

The goal is NOT merely:

```text
unit tests pass
```

The goal is:

> demonstrate that the real end-to-end attack chain is broken.

Record:

* attack step;
* expected result;
* actual result;
* relevant log evidence;
* whether the attacker is rejected at BF-01 authentication;
* whether sequence poisoning is still possible if BF-01 is bypassed in a controlled test;
* whether legitimate device data remains protected.

Do not claim that BF-06/BF-07 are fixed unless the actual attack is re-tested.

---

# 21. Security Logging Requirements

Logs may be used as evidence, but:

DO NOT log:

* ML-KEM private keys;
* shared secrets;
* device credentials;
* authentication secrets;
* plaintext secrets.

Safe evidence includes:

* rejected Gateway identity;
* authentication failure;
* device ID;
* sequence number if non-sensitive;
* protocol error;
* state transition;
* error counter;
* session ID where appropriate.

If sequence numbers are used in evidence, ensure the evidence does not expose secrets.

---

# 22. Scope and Safety

All attack tests must target only the local educational project environment.

Do not:

* attack external systems;
* perform uncontrolled network flooding;
* scan unrelated hosts;
* expose credentials;
* publish secrets;
* create persistence outside the project;
* modify unrelated repositories.

For BF-02 use bounded local testing only.

---

# 23. Documentation Requirements

Create:

`review/P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation.md`

The report must follow the same style and evidence-oriented structure as P02–P07.

Suggested structure:

```text
# P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation

## 1. Purpose

## 2. Scope and Environment

## 3. Pre-P08 Baseline

## 4. New Findings

### 4.1 BF-01
### 4.2 BF-02
### 4.3 BF-03A
### 4.4 BF-03B
### 4.5 BF-04
### 4.6 BF-05

## 5. Compound Findings

### 5.1 BF-06
### 5.2 BF-07

## 6. Attack Chains

### 6.1 Chain 1 – Data Blindness + Replacement
### 6.2 Chain 2 – DoS + Data Replacement
### 6.3 Chain 3 – Persistent Device Impersonation
### 6.4 Chain 4 – Single-message Silent Blindness

## 7. Root Cause Analysis

## 8. Remediation Decision Matrix

## 9. BF-01 Remediation

## 10. BF-03A Credential Remediation

## 11. Fail-First Verification

## 12. Regression Verification

## 13. Compound Attack Re-test

## 14. Evidence Summary

## 15. Residual Risks

## 16. Deviations / Limitations

## 17. Final P08 Assessment

## 18. Files Changed

## 19. Test Inventory
```

---

# 24. Evidence Standard

For every significant finding provide:

```text
Finding
↓
Attack input
↓
Expected behavior
↓
Observed behavior
↓
Security impact
↓
Evidence
↓
Decision
```

Evidence may include:

* command output;
* pytest output;
* logs;
* measured resource counts;
* before/after behavior;
* attack scripts;
* test names;
* file references;
* relevant source locations.

Do not fabricate evidence.

If a test cannot be reproduced, explicitly state:

> Not reproduced in the current environment.

Do not convert a hypothesis into a confirmed vulnerability.

---

# 25. Before/After Security Matrix

P08 must include a concise matrix:

| Finding | Before P08                   | P08 Action                    | After P08            | Status     |
| ------- | ---------------------------- | ----------------------------- | -------------------- | ---------- |
| BF-01   | Gateway unauthenticated      | targeted authentication       | verify               | ...        |
| BF-02   | resource exhaustion possible | deferred                      | unchanged            | residual   |
| BF-03A  | credentials exposed/insecure | configuration remediation     | verify               | ...        |
| BF-03B  | sequence can jump            | no automatic algorithm change | unchanged/documented | residual   |
| BF-04   | 0.097 ms difference          | no fix                        | unchanged            | negative   |
| BF-05   | unauthenticated endpoints    | no architecture change        | unchanged            | limitation |
| BF-06   | targeted blindness           | re-test after remediation     | verify               | ...        |
| BF-07   | plausible replacement        | re-test after remediation     | verify               | ...        |

Use actual evidence, not assumptions.

---

# 26. Final Verdict

Do NOT automatically use "PASS".

The P08 verdict must reflect evidence.

Possible verdicts:

* **PASS**
* **PASS WITH DOCUMENTED RESIDUAL RISKS**
* **PARTIAL PASS**
* **FAIL**

If BF-01 is fixed and the main compound attack chain is broken while BF-02/BF-03B/BF-05 remain documented limitations, the expected direction is:

**PASS WITH DOCUMENTED RESIDUAL RISKS**

But this is only acceptable if the actual verification evidence supports it.

---

# 27. README / CLAUDE Updates

If P08 is successfully completed:

Update `README.md` only where necessary to reflect:

* current test count;
* current security controls;
* P08 history;
* BF findings if appropriate;
* remaining limitations;
* final known risks.

Update `CLAUDE.md` with the P08 phase status.

Do not rewrite unrelated documentation.

Do not claim production security.

Do not claim that all vulnerabilities have been eliminated.

---

# 28. Git Safety

Before finishing:

1. inspect `git status`;
2. inspect changed files;
3. inspect diff;
4. confirm no secrets;
5. confirm no P05 external harness has been copied into the repository;
6. confirm no `.venv`, `.pytest_cache`, runtime state, private keys, `.env`, or logs were accidentally added;
7. confirm only intended files changed.

Do NOT commit or push unless explicitly instructed.

---

# 29. Final P08 Output

At the end, provide a concise engineering summary containing:

### Repository state

* branch;
* commit;
* clean/dirty state;
* files changed.

### Findings

* BF-01 result;
* BF-02 result;
* BF-03A result;
* BF-03B result;
* BF-04 result;
* BF-05 result;
* BF-06 result;
* BF-07 result.

### Remediation

* exact source files changed;
* exact security behavior changed;
* tests added;
* tests modified, if any;
* tests not removed.

### Verification

* fail-first result;
* final pytest result;
* live attack re-test result;
* regression security result;
* compound attack result.

### Residual risks

Clearly list what remains unresolved.

### P08 verdict

Use an evidence-based verdict.

---

# 30. Important Engineering Principle

The purpose of P08 is not to make the report look perfect.

The purpose is to demonstrate:

```text
Additional testing
      ↓
Finding
      ↓
Reproduction
      ↓
Root-cause analysis
      ↓
Risk prioritisation
      ↓
Student-approved remediation
      ↓
Fail-first test
      ↓
Implementation
      ↓
Regression test
      ↓
End-to-end attack re-test
      ↓
Residual-risk documentation
```

The final report must clearly distinguish:

**fixed**

from

**mitigated**

from

**deferred**

from

**not exploitable**

from

**compound impact**

from

**not tested / not reproduced**.

Never claim stronger security than the evidence supports.

---

# 31. Do Not Stop at Unit Tests

A successful P08 is NOT:

```text
pytest passes
```

A successful P08 must demonstrate that the important real-world attack path has been re-tested.

The most important final question is:

> Can an unauthenticated fake Gateway still establish a cloud-accepted session and poison the target device's sequence state so that legitimate data is suppressed and replaced by attacker-controlled plausible readings?

If the answer changes from **YES before remediation** to **NO after remediation**, provide the evidence.

That is the central security result of P08.
