# P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation

> **AI-generated final report.** This document was produced by an AI
> assistant executing `prompt/P08 - Additional Adversarial Testing,
> Attack-Chain Analysis & Targeted Remediation.md`. P08 is an additive
> maintenance/evolution phase: P02–P07 were NOT rewritten, deleted, or
> retroactively altered. Its purpose is to reproduce the new BF
> findings, distinguish root vulnerabilities from compound attack
> effects, remediate only the approved scope (BF-01, BF-03A), and
> document the rest honestly. The central result is that the
> unauthenticated-fake-Gateway attack changed from **YES before P08** to
> **NO after P08**.
>
> Date: 2026-09-08. Environment: Windows 11 (10.0.26200), verification
> Python 3.12.10 (win_amd64), cryptography 50.0.1, pytest 9.1.1.

## 1. Purpose

P07 concluded `PASS WITH DOCUMENTED RESIDUAL RISKS`. P08 was triggered
by additional adversarial testing that identified a new finding set
(BF-01..BF-07) and, more importantly, showed that several weaknesses
chain into a serious end-to-end attack (BF-06/BF-07). The goal of P08
is NOT to make the system production-ready; it is to reproduce the new
findings, isolate root causes from compound effects, apply targeted
remediation only where justified, re-test the attack chain, and update
residual-risk documentation.

## 2. Scope and Environment

| Item | Value |
| --- | --- |
| Repository | `main` @ `2c041f5`, remote `origin` = `github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud` |
| Pre-existing changes | none (working tree was clean before P08) |
| Verification interpreter | Python 3.12.10 (win_amd64) — see section 16 for the environment note |
| cryptography | 50.0.1 (pinned, ML-KEM-768 verified via round trip) |
| pytest | 9.1.1 |
| Docker | NOT VERIFIED (Docker not executed) |
| CI (GitHub Actions) | NOT VERIFIED (not executed in this environment) |

Remediation scope is exactly the P08 section 3 decision matrix:
BF-01 and BF-03A were remediated; BF-02, BF-03B, BF-05 were analysed
and documented; BF-04 was recorded as a negative result; BF-06/BF-07
were re-tested as compound effects.

## 3. Pre-P08 Baseline

```text
pytest -q  ->  120 passed, 0 failed, 0 skipped
```

This matches the P07 end state. No test was deleted or weakened.

## 4. New Findings

### 4.1 BF-01 — Cloud does not authenticate Gateway

**Confirmed.** `cloud/cloud.py` accepted any `mlkem_request_pubkey`;
`gateway_id` was self-declared and never checked. Live reproduction:
an unauthenticated client completed the ML-KEM handshake and
established a session:

```text
session established with self-declared gateway_id=attacker-gw
active_sessions: 1   mlkem_sessions_established: 1
```

Security impact: HIGH. Any unauthenticated client could become a
cloud-accepted Gateway and inject readings. Classification: **root
vulnerability**. Decision: **REMEDIATE**.

### 4.2 BF-02 — Connection flooding / one-thread-per-connection

**Confirmed.** The cloud (and gateway) spawn one thread per accepted
connection with no bounded worker pool. Bounded reproduction:

```text
threads before: 3  after opening 150 connections: 153
```

Resource usage grows approximately linearly with the number of open
connections (one thread per connection). Classification:
**operational/resource risk**. Decision: **DEFER + DOCUMENT** (no
networking redesign in P08).

### 4.3 BF-03A — Hard-coded / insecure device credential management

**Confirmed.** The per-device keys and the device's own key were
embedded directly in `common/config.py` (and inline in
`docker-compose.yml`), so every simulated credential was visible to
anyone reading the source tree. Security impact: HIGH (credential
exposure -> device impersonation). Classification: **credential
management weakness**. Decision: **REMEDIATE**.

### 4.4 BF-03B — Unbounded sequence advancement

**Confirmed.** `ReplayGuard` accepts any `seq > last_seq` with no
maximum jump. Live reproduction:

```text
attacker seq=99999  ->  ACCEPTED (store_count 1)
legitimate seq=4    ->  REPLAY REJECTED (store_count still 1)
```

This is sequence-state poisoning / desynchronization. The P03 design
deliberately selected monotonic sequence with **no jump window**, so
the replay algorithm was NOT changed (a jump window can weaken replay
protection if done incorrectly). Classification: **sequence-state
poisoning**. Decision: **ANALYSE + DOCUMENT; no automatic algorithm
change**.

### 4.5 BF-04 — Device ID timing side channel

**Negative result.** Repeated measurements (40 samples each):

```text
unknown-device reject      mean 0.366 ms  stdev 0.064 ms
known-device bad-tag reject mean 0.408 ms  stdev 0.068 ms
```

The difference is microsecond-scale and noisy relative to the spread,
so device-id enumeration is not practically exploitable in the tested
environment. Decision: **NO FIX** (do not manufacture a fix to remove
the finding).

### 4.6 BF-05 — Unauthenticated `/health` and `/readings`

**Confirmed (code inspection).** `common/health.py` binds
`0.0.0.0` and requires no authentication; the cloud's extra route
`/readings` returns recent readings (device ids + temperatures).
`/health` exposes operational state/counters. Security impact: LOW
(information disclosure in the educational deployment). Decision:
**DOCUMENT** as a deployment limitation; no API-authentication
architecture was added. Application health must not be confused with
data authenticity.

## 5. Compound Findings

### 5.1 BF-06 — Targeted cloud-side data blindness

**Reproduced end-to-end before P08.** `BF-01 (fake Gateway)` +
`BF-03B (unbounded seq)` allowed an attacker to send
`device_id=dev-01, seq=99999`, poison the cloud replay state, and make
the real device's next reading (`seq=4`) be rejected:

```text
after attacker seq=99999: store_count = 1
after legitimate seq=4:   store_count = 1  (still 1 -> real reading rejected)
```

### 5.2 BF-07 — False data continuity / plausible replacement

**Reproduced before P08.** Continuing `seq=100000,100001,100002` was
accepted, replacing legitimate data with a plausible continuous
stream while application-level health remained normal:

```text
after attacker seq=100000..100002: store_count = 4
```

No alert is generated by the current application-level monitoring; the
health endpoint does not indicate that the data stream was compromised.

## 6. Attack Chains

### 6.1 Chain 1 — Data Blindness + Replacement

`BF-05 recon -> BF-01 fake Gateway -> ML-KEM session -> BF-06
sequence-state poisoning -> real device suppressed -> BF-07 plausible
data injected -> /readings appears normal`. This is the primary
security scenario and was the central P08 target.

### 6.2 Chain 2 — DoS + Data Replacement

`BF-02 connection flooding -> real path disrupted -> BF-01 fake
Gateway -> BF-07 attacker-controlled stream -> BF-05 health still
appears available`. Additional scenario; BF-02 remains deferred.

### 6.3 Chain 3 — Persistent Device Impersonation

`BF-03A credential exposure -> device impersonation -> trusted-looking
readings -> BF-03B/BF-06 sequence-state poisoning -> real device
suppressed`. This chain **requires credential exposure/compromise**; it
is NOT a zero-credential attack.

### 6.4 Chain 4 — Single-message Silent Blindness

`BF-01 fake Gateway -> one message (device_id=target, seq=99999) ->
real device data rejected`. Before P08 this required no legitimate
device key and only a small number of protocol interactions. After
P08 it is blocked at BF-01 (no session can be established).

## 7. Root Cause Analysis

Two major interacting root causes:

1. The cloud authenticates itself to the gateway (F-01 pinning) but
   does **not** authenticate the gateway identity.
2. Replay protection only checks monotonic increase (`seq > last`)
   without preventing extreme sequence-state advancement.

Additional independent weaknesses:

3. unbounded connection/thread handling (BF-02);
4. insecure credential storage/configuration (BF-03A);
5. unauthenticated monitoring/data endpoints (BF-05).

BF-06 and BF-07 are consequences of the interaction between (1) and
(2). BF-04 is a negative result.

## 8. Remediation Decision Matrix

| Finding | Classification | Decision |
| --- | --- | --- |
| BF-01 | Root vulnerability | REMEDIATE |
| BF-02 | Operational/resource risk | DEFER + DOCUMENT |
| BF-03A | Credential management weakness | REMEDIATE |
| BF-03B | Sequence-state poisoning | ANALYSE + DOCUMENT; no algorithm change |
| BF-04 | Negative result | NO FIX |
| BF-05 | Low-risk deployment limitation | DOCUMENT |
| BF-06 | Compound attack effect | Re-test after BF-01 remediation |
| BF-07 | Compound impact | Re-test after remediation |

## 9. BF-01 Remediation

A minimal Gateway-to-Cloud authentication mechanism was added, reusing
the existing per-device hello mechanism (F-02) rather than introducing
TLS/PKI/JWT:

- `common/protocol.py`: `gateway_auth_claims_bytes(gateway_id)` — a
  canonical identity claim with a `scope` field for domain separation.
- `common/crypto.py`: `build_gateway_auth()` /
  `verify_gateway_auth()` — a MAC-only ChaCha20-Poly1305 AEAD tag over
  the claim (library call; no from-scratch crypto).
- `common/config.py`: per-gateway key registry
  (`gateway_keys()` / `gateway_key()` / `local_gateway_key()`), loaded
  from configuration like the device registry.
- `cloud/processing.py`: `parse_mlkem_request()` now requires
  `auth_nonce` + `auth_tag`; `verify_gateway_request_auth()` verifies
  the tag.
- `cloud/cloud.py`: the gateway is authenticated **before** the cloud
  sends its public key / accepts the session. Unknown gateway ids and
  failed/tampered authentication raise `crypto.AuthenticationError`,
  counted as `messages_rejected` (a policy rejection, distinct from
  malformed-input `errors`).
- `gateway/cloud_channel.py`: the gateway signs its request with its
  own credential.

The ML-KEM handshake and cloud public-key pinning (F-01) are unchanged.

## 10. BF-03A Credential Remediation

Credential secrets were removed from Python source:

- `common/config.py` no longer contains any key material; the
  device/gateway registries load from `DEVICE_KEYS_JSON` /
  `DEVICE_KEYS_FILE` and `GATEWAY_KEYS_JSON` / `GATEWAY_KEYS_FILE`,
  falling back to clearly-labelled demo files.
- `common/demo_device_keys.json` and
  `common/demo_gateway_keys.json` contain DEMO-ONLY material so the
  educational local run still works out of the box.
- `.gitignore` now excludes real `device_keys.json` /
  `gateway_keys.json` files while keeping the demo files committed.
- `docker-compose.yml` keeps the demo values inline with explicit
  "demo only" comments and adds the gateway credential.

The per-device identity model and per-device isolation are preserved.

## 11. Fail-First Verification

The new regression tests were written first and run against the
unfixed code:

```text
15 new BF-01/BF-03A tests -> 12 failed, 3 passed
```

Representative pre-fix failures: `test_unauthenticated_gateway_cannot_
inject_reading` (fake gateway established a session),
`test_config_source_has_no_embedded_device_key_secrets` (secrets were
present in source), `test_device_keys_file_override` (file-based config
unsupported). After remediation the same tests pass (section 12).

## 12. Regression Verification

```text
pytest -q  ->  136 passed, 0 failed, 0 skipped
```

The count grew 120 -> 136 because 16 regression tests were added
(BF-01 gateway authentication, BF-03A credential config, plus a
handshake validation test). All previous F-01..F-15 and NEW-1 tests
remain and pass. A higher count does not mean "safer"; it means more
behaviour is asserted.

## 13. Compound Attack Re-test

After remediation the central attack chain was re-run over real TCP:

```text
[1] unauthenticated fake gateway -> pubkey reply? False
    active_sessions: 0  errors: 1  (rejected at BF-01)
[2] store_count: 0 (no seq=99999 poisoning possible)
[3] valid gateway (gw-01 + credential) -> established, active_sessions: 1
[4] device -> gateway -> cloud -> reading stored (store_count: 1)
```

The answer to the central P08 question changed from **YES before
remediation** to **NO after remediation**: an unauthenticated fake
Gateway can no longer establish a cloud-accepted session and therefore
cannot poison the target device's sequence state.

## 14. Evidence Summary

| Finding | Evidence | Status |
| --- | --- | --- |
| BF-01 | Live: attacker session established (before); rejected with `errors`+1 (after) | Fixed and Verified |
| BF-02 | Live: threads 3 -> 153 for 150 connections | Deferred (residual) |
| BF-03A | Source grep: 0 embedded secrets after fix; demo files + `.gitignore` | Fixed and Verified |
| BF-03B | Live: seq=99999 accepted, seq=4 rejected | Documented (no algorithm change) |
| BF-04 | 40-sample timing: ~0.04 ms mean difference, noisy | Negative result |
| BF-05 | Code inspection: 0.0.0.0 bind, no auth, `/readings` | Documented limitation |
| BF-06 | Live: blindness reproduced (before); blocked at BF-01 (after) | Blocked (compound) |
| BF-07 | Live: plausible replacement reproduced (before); blocked (after) | Blocked (compound) |

## 15. Residual Risks

- BF-02: one-thread-per-connection resource exhaustion remains (deferred).
- BF-03B: replay state can still be poisoned by a sufficiently large
  accepted sequence number; replay protection remains effective against
  replay but not against desynchronization (no jump window, per P03).
- BF-05: `/health` and `/readings` remain unauthenticated and bind
  0.0.0.0 (deployment limitation).
- No TLS; gateway metadata visible; cloud does not authenticate
  gateways beyond the added credential check (no PKI).
- Gateway credentials are static demo keys with no rotation/revocation;
  the registry simulates provisioning and is not a production
  provisioning system.
- Docker and CI remain NOT VERIFIED in this environment.
- Gateway/cloud restart replay-state amnesia (P03 accepted) remains.

## 16. Deviations / Limitations

- The system's default interpreter (`C:\msys64\ucrt64\bin\python.exe`,
  a mingw-UCRT build) is ABI-incompatible with the project's
  `win_amd64` extension wheels (cffi/cryptography), so verification used
  a local official Python 3.12.10 (win_amd64) with the exact pinned
  cryptography 50.0.1 / pytest 9.1.1. This is an environment concern,
  not a project-code change.
- `docker-compose.yml` and the Dockerfiles were updated for consistency
  (F-10) but were NOT executed (Docker unavailable).
- Remote CI was NOT executed.

## 17. Final P08 Assessment

**PASS WITH DOCUMENTED RESIDUAL RISKS**

BF-01 and BF-03A were fixed and verified with fail-first + regression
evidence; the primary compound attack chain (BF-06/BF-07) is broken;
the legitimate device-to-cloud path still works end-to-end. BF-02,
BF-03B and BF-05 remain documented limitations, and BF-04 is a
negative result. The project remains an educational simulation, not a
production security system.

## 18. Files Changed

Modified:

```text
.gitignore
cloud/cloud.py
cloud/processing.py
common/config.py
common/crypto.py
common/protocol.py
docker-compose.yml
gateway/cloud_channel.py
tests/test_handshake.py
tests/test_nonce_validation.py
```

Created:

```text
prompt/P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation.md
review/P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation.md
common/demo_device_keys.json
common/demo_gateway_keys.json
tests/test_gateway_auth.py
tests/test_credential_config.py
```

No tests were removed. No secrets were committed. Temporary attack
harnesses were kept outside the repository tree (`work/`).

## 19. Test Inventory

| Phase | Result | Purpose |
| --- | --- | --- |
| P07 final | 120 passed | Pre-P08 baseline (re-established) |
| P08 fail-first | 12 failed / 3 passed | BF-01 + BF-03A tests before remediation |
| P08 final | **136 passed** | Post-remediation full regression |

The count increased because 16 regression tests were added in P08
(gateway authentication, credential configuration, handshake auth
validation).
