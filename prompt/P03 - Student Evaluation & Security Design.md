# P03 — Student Evaluation & Security Design

## 0. Role

You are an AI software-security assistant working on the university project:

**PQCBridge Legacy Edge-Cloud — Post-Quantum Security Migration Simulation**

The project is a small educational edge-cloud simulation involving:

* a legacy IoT device,
* an edge gateway,
* a cloud service,
* ChaCha20-Poly1305,
* ML-KEM-768,
* HKDF,
* legacy fallback,
* security migration from legacy devices toward post-quantum protection.

The project was initially generated as an AI-assisted baseline in **P01**.

A separate technical review was performed in **P02**.

The P02 review found 15 findings (F-01 to F-15), including:

* unauthenticated ML-KEM key establishment,
* downgrade/fallback weaknesses,
* malformed handshake crashes,
* replay attacks,
* static PSK,
* broken session lifecycle,
* metric inconsistencies,
* dependency drift,
* and several maintainability/operational issues.

The P02 review was explicitly marked as an **AI-generated review draft**.

The students must now evaluate those findings and make their own engineering decisions.

---

# 1. Most Important Rule

**DO NOT MODIFY PROJECT CODE IN P03.**

This phase is for:

1. understanding the P02 findings;
2. evaluating whether each finding is valid;
3. deciding which findings should be fixed;
4. deciding which findings should be deferred or rejected;
5. designing the proposed fixes;
6. identifying risks and trade-offs;
7. defining verification tests;
8. preparing the implementation plan for P04.

You may inspect the complete repository.

You may run existing tests.

You may reproduce existing P02 findings if useful.

You may create temporary test scripts outside the project source tree if required for evaluation.

You MUST NOT:

* edit existing project source files;
* modify tests;
* modify configuration;
* modify Docker files;
* modify CI;
* modify README;
* silently fix problems;
* commit code changes.

If a temporary experiment is required, clearly identify it as a temporary experiment and do not treat it as a project modification.

---

# 2. Project Documentation Requirement

This project is an AI-assisted university project.

The documentation must preserve the complete development chain:

> **Prompt → AI Output → Student Evaluation → Decision → Verification → Change → Remaining Risk**

P03 must therefore NOT pretend that AI recommendations are automatically correct.

For every finding:

* verify the technical claim;
* explain whether the finding is valid;
* evaluate the AI recommendation;
* identify possible alternative solutions;
* make a student-facing decision;
* explain why the decision was made;
* define how the decision will later be verified.

The final decision belongs to the student team, not the AI.

---

# 3. Required Inputs

Before beginning:

1. Read the current repository.
2. Read:

   * `README.md`
   * `CLAUDE.md`
   * P01 documentation
   * `review/P02 - Baseline Technical Review.md`
   * relevant source files
   * relevant existing tests
3. Inspect the actual implementation corresponding to every P02 finding.
4. Run the existing test suite if possible.

Record the environment:

* OS
* Python version
* cryptography version
* pytest version
* Docker availability
* Git repository status
* test result

Do not claim that something was tested if it was only inspected.

---

# 4. P02 Findings to Evaluate

Evaluate all findings F-01 through F-15.

Do not automatically accept the P02 severity or recommendation.

The student team must determine whether each finding is:

* **ACCEPTED**
* **MODIFIED**
* **REJECTED**
* **DEFERRED / OUT OF SCOPE**

Use the following findings as the starting point.

---

## F-01 — Unauthenticated ML-KEM Key Establishment

P02 claims:

* the gateway accepts the cloud ML-KEM public key without authentication;
* an active attacker may substitute a public key;
* ML-KEM provides key establishment but not peer authentication.

Evaluate:

1. Is this technically correct?
2. What threat model does the project actually target?
3. Is passive eavesdropping protection enough for this educational project?
4. Should the project implement authentication?
5. Compare:

   * public-key pinning;
   * signature-based authentication;
   * TLS;
   * another simple educational mechanism.
6. Recommend the simplest defensible solution appropriate for this project.
7. Explain implementation complexity and remaining risk.

Do not implement the solution yet.

---

## F-02 — Capability Spoofing / Downgrade

Evaluate:

1. Can a plaintext capability claim be modified by an active attacker?
2. Can an attacker remove `ml-kem-768`?
3. What happens if a device falsely claims modern capabilities?
4. Should fallback always be permitted?
5. Should unknown capability combinations be rejected?
6. How should the project distinguish:

   * genuine legacy device;
   * modern device;
   * malicious/spoofed device?
7. What migration policy should the prototype demonstrate?

Produce a concrete fallback decision table.

Example structure:

| Device claim   | Gateway decision | Reason |
| -------------- | ---------------- | ------ |
| legacy only    | ...              | ...    |
| ML-KEM capable | ...              | ...    |
| both           | ...              | ...    |
| unknown        | ...              | ...    |
| malformed      | ...              | ...    |

---

## F-03 — Gateway Crash from Malformed Handshake

Evaluate:

1. Confirm whether missing `public_key` can cause `KeyError`.
2. Confirm whether the exception escapes the retry loop.
3. Determine the correct protocol-level behavior.
4. Decide whether malformed handshake messages should:

   * reject the message;
   * close the connection;
   * retry;
   * log an error;
   * increment metrics.

Propose the smallest safe fix.

---

## F-04 — Cloud Thread Crash from Malformed Encapsulation

Evaluate:

1. Confirm the missing `ciphertext` behavior.
2. Compare the cloud handling with gateway handling.
3. Determine why the exception bypasses normal error handling.
4. Define expected behavior for malformed handshake messages.
5. Decide whether errors should be counted.

The gateway and cloud should use a consistent protocol-validation policy unless there is a documented reason not to.

---

## F-05 — Replay Attack

P02 demonstrated:

> The same valid encrypted reading can be captured and transmitted again, and the cloud stores it twice.

Evaluate possible mechanisms:

### Option A — Monotonic sequence number

Reject:

`sequence <= last_sequence`

### Option B — Replay window

Allow limited out-of-order messages while rejecting old values.

### Option C — Session-bound counters

Bind freshness to a specific established session.

### Option D — Combination

Use sequence numbers plus session identity.

Compare the options.

Consider:

* legacy path;
* modern path;
* reconnects;
* device restarts;
* lost packets;
* duplicated packets;
* out-of-order messages;
* storage requirements;
* implementation complexity.

Select the mechanism most appropriate for this educational project.

Define expected behavior for:

* sequence 1;
* sequence 2;
* duplicate sequence 2;
* sequence 1 after sequence 2;
* very large sequence;
* device reconnect.

Do not implement yet.

---

## F-06 — Static Shared PSK

Evaluate:

1. Is one PSK shared by all legacy devices acceptable for the prototype?
2. Does `device_id` provide real authentication?
3. What happens if one device is compromised?
4. Compare:

   * keeping one simulation PSK;
   * per-device PSKs;
   * device-key mapping;
   * future provisioning system.

Decide whether this should be:

* fixed now;
* documented only;
* deferred as future work.

Do not over-engineer the prototype.

---

## F-07 — Broken Session Lifecycle

Evaluate:

1. What happens if the cloud dies after session establishment?
2. Does gateway state remain marked as established?
3. Should the gateway reconnect?
4. Should a failed session be cleared?
5. Should a new session ID be generated after reconnection?
6. What should `/health` report?
7. Should cloud sessions expire or be evicted?

Define a simple session lifecycle:

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
     ↓
RECONNECTING
```

Modify the diagram if a simpler lifecycle is more appropriate.

---

## F-08 — Metrics Problems

Evaluate:

* `payload_bytes` unit mismatch;
* `forward_ms` naming mismatch;
* `fallback_events` semantics;
* incomplete error counting;
* missing device metrics.

Define exactly what each metric should mean.

Do not add unnecessary metrics.

Create a small proposed metrics table:

| Metric | Type | Unit | Meaning |
| ------ | ---- | ---- | ------- |

---

## F-09 — Duplicated AEAD Code

Evaluate whether duplication is actually harmful at this project size.

Consider:

* readability;
* educational value;
* future changes;
* risk of introducing abstraction complexity.

Decide:

* ACCEPTED;
* MODIFIED;
* REJECTED;
* DEFERRED.

If modification is recommended, describe the smallest refactoring.

---

## F-10 — Configuration Duplication

Evaluate the two sources of configuration:

* `common/config.py`
* `docker-compose.yml`

Determine which should be authoritative.

Define a simple configuration policy.

Do not implement it yet.

---

## F-11 — Key Lifecycle

Evaluate:

* session retention;
* session eviction;
* static ML-KEM keypair lifetime;
* Python `bytes` zeroization limitations.

Do not propose unrealistic secure-memory requirements.

Define a practical prototype policy.

---

## F-12 — Threads / Timeouts / Rate Limiting

Evaluate whether this is important enough for the course project.

Consider:

* project scale;
* expected number of devices;
* demonstration environment;
* denial-of-service implications;
* implementation complexity.

A finding may reasonably be deferred if the decision is clearly justified.

---

## F-13 — Health Endpoint

Define what `"healthy"` means.

For the gateway, consider:

* device listener available;
* cloud connection available;
* usable session;
* degraded state.

For cloud, consider:

* server available;
* crypto state;
* storage state.

Propose a simple status model.

---

## F-14 — Dependency Drift

Evaluate:

`cryptography>=45.0`

versus a pinned or bounded version.

Consider:

* reproducibility;
* ML-KEM API stability;
* CI;
* educational environment.

Recommend an appropriate dependency policy.

---

## F-15 — Truncated Message Error

Evaluate the distinction between:

* oversized message;
* malformed message;
* truncated message;
* clean disconnect.

Recommend whether this should be fixed now or deferred.

---

# 5. Student Decision Framework

For every finding, use this structure:

```text
Finding:
F-XX

AI claim:
...

Technical verification:
...

Is the finding valid?
YES / PARTIALLY / NO

Student evaluation:
...

AI recommendation:
...

Alternative approaches:
...

Selected approach:
...

Decision:
ACCEPTED / MODIFIED / REJECTED / DEFERRED

Reason:
...

Implementation scope:
...

Verification method:
...

Expected result:
...

Remaining risk:
...
```

Do not leave the decision unexplained.

---

# 6. Priority Classification

After evaluating all findings, create four groups:

## P0 — Must Fix Before Further Development

Security or correctness issues that could invalidate the next phase.

## P1 — Important

Should be addressed if feasible and directly improves the system.

## P2 — Useful

Quality, maintainability, metrics, and documentation improvements.

## P3 — Deferred

Reasonable future work or outside the scope of this course prototype.

Explain why every finding belongs to its selected priority.

---

# 7. Security Design Decisions

Produce explicit decisions for at least:

### 7.1 Authentication

Answer:

> Who is authenticating whom?

### 7.2 Confidentiality

Answer:

> What traffic is protected, and from which attacker?

### 7.3 Integrity

Answer:

> How are modified messages detected?

### 7.4 Freshness

Answer:

> How are replayed messages detected?

### 7.5 Downgrade Resistance

Answer:

> How does the system prevent or detect forced legacy fallback?

### 7.6 Key Lifecycle

Answer:

> When are keys created, used, expired, and removed?

### 7.7 Legacy Compatibility

Answer:

> When is fallback allowed, and when must the gateway reject a device?

These decisions must be simple enough to implement and demonstrate within a university project.

---

# 8. Proposed Target Architecture

Based on the student decisions, describe the proposed architecture for P04.

Include:

```text
Legacy Device
      |
      | legacy protected message
      v
   Gateway
      |
      | authenticated ML-KEM session
      v
    Cloud
```

Show:

* authentication;
* capability negotiation;
* fallback;
* replay protection;
* session lifecycle;
* metrics;
* health state.

Clearly mark what remains intentionally insecure or simulated.

---

# 9. Test-First Planning

Before P04 implementation, define tests that should fail against the current baseline and pass after the selected modifications.

At minimum consider:

### Handshake

* missing `public_key`;
* missing `ciphertext`;
* malformed base64;
* invalid key length;
* unexpected message type.

### Replay

* duplicate sequence;
* older sequence;
* valid next sequence;
* reconnect behavior.

### Downgrade

* stripped `ml-kem-768`;
* forged capability;
* unsupported capability combination.

### Session

* cloud failure;
* reconnect;
* stale session;
* new session ID.

### Metrics

* correct units;
* correct error counters;
* correct fallback count.

Do not modify the tests during P03.

Only produce the test plan.

---

# 10. Verification Matrix

Create:

| Decision             | Current baseline | Proposed behavior | Test | Expected result |
| -------------------- | ---------------- | ----------------- | ---- | --------------- |
| Authentication       | unauthenticated  | ...               | ...  | ...             |
| Replay               | accepted         | ...               | ...  | ...             |
| Handshake validation | crash            | ...               | ...  | ...             |
| Downgrade            | possible         | ...               | ...  | ...             |
| Session failure      | wedged           | ...               | ...  | ...             |
| Metrics              | inconsistent     | ...               | ...  | ...             |

---

# 11. Risk and Scope Control

This is a university prototype, NOT a production IoT security platform.

Do not recommend unnecessary systems such as:

* full PKI infrastructure;
* hardware security modules;
* Kubernetes;
* enterprise identity management;
* complex service meshes;
* production certificate authorities;
* distributed databases.

Prefer small, understandable changes that demonstrate the security concept.

Every recommendation must answer:

> "Can a student team reasonably implement and test this in the next project phase?"

---

# 12. AI Recommendation Quality Review

Explicitly identify recommendations from P02 that should NOT be followed blindly.

For example:

* technically correct but too complex;
* valid for production but unnecessary for the course;
* requires infrastructure unavailable to the team;
* introduces more complexity than security benefit;
* should remain as documented future work.

This section is important because P03 demonstrates **student evaluation of AI output**, rather than simply following AI instructions.

---

# 13. Required Deliverable

Create:

`review/P03 - Student Security Evaluation & Design Decisions.md`

The document must contain:

1. Executive Summary
2. Environment and Verification Scope
3. P02 Findings Review
4. F-01 through F-15 Evaluation
5. Student Decision Table
6. P0/P1/P2/P3 Priorities
7. Security Design Decisions
8. Fallback Policy
9. Replay Protection Design
10. Session Lifecycle Design
11. Proposed Target Architecture
12. Test-First Plan
13. Verification Matrix
14. Remaining Risks
15. Deferred / Rejected Findings
16. AI Recommendation Quality Review
17. P04 Implementation Plan

---

# 14. Required Student Decision Table

Create a concise final table:

| ID   | Finding | Valid? | Student Decision | Priority | P04 Action |
| ---- | ------- | ------ | ---------------- | -------- | ---------- |
| F-01 | ...     | ...    | ...              | ...      | ...        |
| F-02 | ...     | ...    | ...              | ...      | ...        |
| F-03 | ...     | ...    | ...              | ...      | ...        |
| F-04 | ...     | ...    | ...              | ...      | ...        |
| F-05 | ...     | ...    | ...              | ...      | ...        |
| F-06 | ...     | ...    | ...              | ...      | ...        |
| F-07 | ...     | ...    | ...              | ...      | ...        |
| F-08 | ...     | ...    | ...              | ...      | ...        |
| F-09 | ...     | ...    | ...              | ...      | ...        |
| F-10 | ...     | ...    | ...              | ...      | ...        |
| F-11 | ...     | ...    | ...              | ...      | ...        |
| F-12 | ...     | ...    | ...              | ...      | ...        |
| F-13 | ...     | ...    | ...              | ...      | ...        |
| F-14 | ...     | ...    | ...              | ...      | ...        |
| F-15 | ...     | ...    | ...              | ...      | ...        |

---

# 15. P04 Boundary

Do NOT implement anything in P03.

P03 ends when:

* every P02 finding has been evaluated;
* every decision has been documented;
* the security design has been selected;
* the fallback policy is defined;
* the replay strategy is defined;
* the session lifecycle is defined;
* tests are planned;
* P04 implementation tasks are ready.

P04 will implement only the decisions explicitly approved in P03.

---

# 16. Final Output Rules

At the end of the task, report:

### Repository inspected

List important files inspected.

### Verification performed

Separate:

* tested;
* manually reproduced;
* code inspection;
* not verified.

### Student decisions required

Clearly identify decisions that still require human approval.

### Proposed P04 scope

List only approved/proposed implementation tasks.

### Files created

Only:

`review/P03 - Student Security Evaluation & Design Decisions.md`

No source code should be modified.

### Important

Never claim:

* a vulnerability is fixed;
* a test passes after a fix;
* authentication exists;
* replay protection exists;
* downgrade resistance exists;

unless this was actually implemented and verified in a later phase.

P03 is a **design and evaluation phase**, not an implementation phase.
