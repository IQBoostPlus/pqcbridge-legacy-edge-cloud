# P05 — Independent Security Verification & Re-Test

> **AI-generated independent verification report.** This document was
> produced by an AI assistant executing `prompt/P05`. It does NOT
> trust the P04 report: every major P04 claim below was re-tested
> independently with external attack tooling (raw TCP sockets, direct
> `cryptography`-library message construction, subprocess supervision
> and log capture). **No project source, test, Docker, CI or README
> file was modified during this verification** (checksum-verified,
> section 18). One new defect was discovered and is recorded, not
> fixed (P05 section 25).
>
> Verification date: 2026-09-08. Environment: Windows 11
> (10.0.26200), Python 3.12.0, cryptography 50.0.1, pytest 9.1.1.

---

## 1. Executive Summary

The P04 security claims were **independently re-tested and verified**:

- All nine P02/P04 attack classes (F-01, F-02, F-03, F-04, F-05,
  F-06, F-07, F-08, F-13) behaved exactly as P04 claimed when
  re-tested with independently built attack messages over real TCP
  connections against live processes.
- Baseline regression matches P04 exactly: **101 passed, 0 failed,
  0 skipped**.
- **One NEW defect was discovered** that P04 did not report:
  a wrong-length AEAD nonce (8 bytes instead of 12) in a hello, a
  legacy reading, or a protected reading raises an unhandled
  `ValueError` and kills the handler **thread** with an uncontrolled
  traceback, without incrementing the `errors` metric (finding NEW-1,
  section 21). The processes survive and service resumes, so this is
  LOW-MEDIUM severity — but it contradicts the spirit of the P04
  hardening claim "no uncontrolled traceback".
- Docker and CI remain **NOT VERIFIED** (environmental: Docker is not
  installed; the directory is not a git repository). Nothing in this
  report claims they work.
- Overall verdict: **PARTIAL PASS** — every P04 security claim was
  reproduced, but the newly discovered defect and the unverifiable
  Docker/CI dimensions prevent an unqualified PASS (section 23).

## 2. Environment

| Item | Value |
| --- | --- |
| OS | Windows 11 Home China (10.0.26200) |
| Python | 3.12.0 |
| cryptography | 50.0.1 (matches pinned requirements.txt) |
| pytest | 9.1.1 (matches pinned requirements.txt) |
| Docker | **NOT installed** (`docker` command not found) — compose NOT executed |
| Git | **not a git repository** — CI workflow never executed |
| Test count | 101 (declared test functions verified per file, section 3) |

Verification tooling: an external attack harness was created
**outside the project tree** at `D:\Code\Claude\p05-verify\`
(P05 section 2 permits temporary external attack scripts). The
harness:

- runs cloud/gateway/device only as subprocesses with non-default
  ports (15001/15002/18001/18002) and temp state dirs, so the
  project's `device_state/` and `cloud_state/` were never touched
  (mtimes unchanged, section 18);
- builds attack messages with the `cryptography` library directly
  (never through project encoder functions), reproducing the
  documented wire format the way an attacker would;
- captures every process log and every health/readings response as
  evidence.

## 3. Baseline Regression Result

```text
$ .venv/Scripts/python.exe -m pytest -q
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 0.88s
```

Matches the P04 claim (101 passed, 0 failed, 0 skipped). Wall-clock
differs trivially from P04's 0.53 s (machine load); final re-run at
the end of P05: `101 passed in 0.58s` (section 18).

## 4. P04 Claims Under Verification

P04 claims (review/P04): fingerprint-pinned ML-KEM establishment
(F-01); authenticated hellos + reject-based fallback policy (F-02);
uniform handshake validation ending the process/thread crashes
(F-03/F-04); monotonic per-device sequences bound into AEAD AAD with
device counter persistence (F-05); per-device key registry (F-06);
5-state session lifecycle with reconnect and cloud-side eviction
(F-07); unit-correct metrics (F-08); truthful health (F-13); 101
tests; Docker/CI honestly unverified. Each is addressed below.

## 5. Independent Test Method

Per claim, the method was: (1) reproduce the P02/P04 attack against
the **current** code with independently constructed inputs over real
TCP; (2) observe gateway/cloud/device behavior through their own
logs, `/health`, and `/readings`; (3) verify process liveness with
`proc.poll()` (never "error was logged" alone); (4) verify
availability after the attack with a fresh valid flow. Where P04
claimed a metric moved, the counter was read before and after the
triggered event and compared.

## 6. F-01 Verification — ML-KEM Public-Key Substitution: PASS

**Method:** a fake "evil cloud" served a *different, valid*
ML-KEM-768 keypair to the gateway; the gateway was provisioned with
the real cloud's fingerprint (64-hex SHA-256 computed independently
from the key file, cross-checked against the fingerprint the cloud
prints at startup).

**Result:**

- 6 consecutive establishment attempts, each rejected:
  `cloud public key fingerprint mismatch - possible key substitution`
- gateway process **alive** after all attempts (verified via
  `proc.poll()`);
- **no** `ML-KEM-768 session ... established` line in the gateway
  log;
- the gateway **never sent an encaps** to the evil cloud (verified
  on the evil cloud's side — the connection was closed by the
  gateway immediately after the pin check);
- the gateway does not write any pin anywhere (source inspection:
  `CLOUD_PUBLIC_KEY_SHA256` is read-only via `config.cloud_public_key_sha256()`);
- additionally tested the "wrong-length public key" and "malformed
  base64 public key" substitutions (section 8, variants V5/V6) —
  both rejected as ProtocolErrors.

**Honest nuance (finding NEW-2):** while the gateway is stuck in the
initial establishment retry loop, its `/health` endpoint does **not
exist yet** (`gateway/gateway.py: main()` starts the health server
only after `connect_and_establish()` returns). P04's wording "health
degraded" for the F-03/F-01 retry-loop attacks cannot be reproduced
via `/health` in that scenario; process liveness is the correct
evidence there. In the F-07 scenario (established → cloud killed)
degraded health IS correctly reported (section 12).

## 7. F-02 Verification — Downgrade / Capability Manipulation: PASS

Live tests against a real gateway (each case = one TCP connection,
`closed` = the gateway closed the connection):

| Case | Input | Expected | Observed |
| --- | --- | --- | --- |
| 1 | known dev-01, legacy-only, valid tag | ACCEPT (fallback) | connection open; exactly 1 `FALLBACK ACTIVATED` log line |
| 2 | dev-01 claims `ml-kem-768`, valid tag | REJECT | closed; `claims the modern path` logged |
| 2b | dev-01 claims BOTH capabilities | REJECT | closed; `ambiguous capability claims` logged |
| 3 | unknown dev-999 | REJECT | closed; `rejecting UNKNOWN device` logged |
| 4 | capabilities = string (not list) | REJECT | closed (ProtocolError) |
| 4b | capabilities missing | REJECT | closed (ProtocolError) |
| 5 | valid modern hello, `ml-kem-768` **stripped** after tagging | REJECT | closed; `hello authentication FAILED` (tag breaks) |
| 5b | valid legacy hello, modern claim **forged** after tagging | REJECT | closed; `hello authentication FAILED` |

Metrics cross-check: `messages_rejected` delta = 5 (cases 2, 2b, 3,
5, 5b — the malformed cases 4/4b correctly count as `errors`, not
`messages_rejected`); `fallback_activations` delta = 1. A plaintext
capability modification **cannot** silently force an insecure
fallback — the AEAD tag breaks first.

## 8. F-03 Verification — Malformed Gateway Handshake: PASS

The P02 crash payload (`{"type": "mlkem_pubkey", "cloud_id":
"fake-cloud"}`, no `public_key`) plus 7 further variants were served
by a scriptable fake cloud; the gateway retried every 3 s and
received **10 malformed handshakes total**:

| Variant | Gateway log evidence (controlled error) |
| --- | --- |
| V1 missing `public_key` (P02 demo D) | `message missing required string field 'public_key'` |
| V2 missing `type` | `expected mlkem_pubkey` |
| V3 wrong `type` (`mlkem_established`) | `expected mlkem_pubkey` |
| V4 malformed JSON | `message is not valid JSON` |
| V5 invalid base64 `public_key` | `invalid base64 field` |
| V6 wrong public-key length (32 B) | `ML-KEM public key has invalid length` |
| V7 empty `public_key` | `message missing required string field 'public_key'` |
| V8 empty object `{}` | `expected mlkem_pubkey` |

**Result:** gateway process **alive** after all 10 (`proc.poll()`);
10 retry attempts logged; **0 tracebacks**; no session ever
established. The P02 crash is fixed.

## 9. F-04 Verification — Malformed Cloud Encapsulation: PASS

Against a live cloud, five malformed encaps variants were sent
(P02 demo C payload `{"type": "mlkem_encaps"}` + bad base64 +
wrong length + empty ciphertext + empty session_id):

- all five: connection closed by the cloud with a controlled
  `closing gateway connection ...` log line;
- **0 tracebacks** in the cloud log;
- cloud process **alive**;
- cloud `errors` counter: **+5** (each failure counted — the P02
  version of this path counted zero);
- **service availability after attack** (process liveness alone is
  not enough — a handler thread could have died): the pre-existing
  gateway session still reported `ok`; a brand-new valid ML-KEM
  handshake established; a protected reading through it was stored;
  a new legacy-device flow through the gateway forwarded end-to-end.
  All verified.

## 10. F-05 Verification — Replay Protection: PASS

Live, with independently constructed messages:

| Test | Expected | Observed |
| --- | --- | --- |
| seq 1 valid | ACCEPT | stored exactly once |
| exact byte-for-byte replay of seq 1 | REJECT | rejected; still exactly one copy (`/readings`) |
| seq 2 → ACCEPT; seq 2 again → REJECT; seq 1 again → REJECT; seq 3 → ACCEPT | per pattern | stored `[1,2,3]`, each once; 4 `REPLAY REJECTED` log lines |
| valid seq-4 message, plaintext `seq` field changed to 5 | REJECT | `dropping message ... authentication failed` (AAD binds seq) |
| valid message, `device_id` field changed to dev-02 | REJECT | `dropping message ... device_id mismatch` |
| seq 100 (large jump) | accepted — **no jump window** (documented limitation) | ACCEPTED; stored |
| seq 6 after seq 100 | rejected as stale (limitation consequence) | REJECTED — limitation **confirmed live**, not hidden |
| same hello bytes replayed twice | fallback re-activates (documented limitation #6) | `fallback_activations` +2 — limitation confirmed |

**Protected path (independent fake gateway, library-level ML-KEM +
HKDF):**

- protected reading (AAD = session_id) → ACCEPT, stored;
- exact replay of the same protected bytes → **REJECTED BY THE CLOUD**
  (`REPLAY REJECTED` in the cloud log) — the cloud-side
  defense-in-depth works independently of the gateway;
- same ciphertext with `session_id` field rewritten → rejected
  (`session_id mismatch`);
- same ciphertext encrypted under AAD `evil-session` but sent as the
  real session → rejected (AAD binding holds);
- ciphertext with one flipped byte → rejected (AEAD detects
  modification).

Exactly one copy of each accepted reading was stored; the
`messages_rejected` counter increased for every rejection.

## 11. F-06 Verification — Per-Device Key Isolation: PASS

| Probe | Expected | Observed |
| --- | --- | --- |
| dev-01 + dev-01 key | ACCEPT | connection open; fallback activated |
| dev-01 + dev-02 key | REJECT | `hello authentication FAILED` |
| dev-02's hello with `device_id` rewritten to dev-01 | REJECT | `hello authentication FAILED` (impersonation blocked) |
| dev-999 | REJECT | `rejecting UNKNOWN device` |
| dev-02 + dev-02 key | ACCEPT | connection open |
| dev-02 + dev-01 key | REJECT | `hello authentication FAILED` |

`legacy_devices_detected` = 2 (distinct device ids), 2 fallback
activations, 4 rejections counted. Device identity and credentials
cannot be freely substituted. (Actual key values are intentionally
not reproduced in this report.)

**Device counter persistence (part of the F-05 claim) — verified:**
a real device process persisted its counter (10 after run 1), a
restart logged `sequence resumes at 10` and continued at 11; the
cloud stored a strictly increasing sequence across the restart with
no gaps or duplicates (17 readings stored; `/readings` shows the
last 10 by design). Killing the gateway made the connected device
exit with `device terminating due to connection error` —
documented limitation #7 confirmed as described.

## 12. F-07 Verification — Session Failure and Reconnect: PASS

Live sequence (cloud killed with `proc.kill()` mid-run):

```text
established: status=ok cloud_state=established session=4437cd3f228eda0a
  → reading forwarded to cloud: True
  → cloud killed
  → health BEFORE any post-kill forward attempt: still ok/established
  → forward attempt: device connection closed on failure
  → health: degraded | cloud_connected: false | cloud_state: connecting
  → cloud restarted (same key file → same fingerprint → pin valid)
  → automatic reconnect: status=ok, NEW session id 045fbdecbfdb5ff2
    (differs from old: True)
  → forwarding resumed: True
  → cloud evicted the dead gateway's session after the gateway was
    killed: active_sessions 1 → 0
```

Verified: old session not reported active after failure
(`cloud_connected: false`); forwarding failure detected; reconnect
with a fresh session id; health becomes truthful; cloud-side session
cleanup (eviction) works. Cloud `/health` (`mlkem_ready: true`,
`stored_readings`, `active_sessions`) and gateway `/health` (normal
`ok`, `cloud_state` mirroring the state machine) both match the
P03/F-13 design.

**Honest nuance (finding NEW-3):** with an idle system the gateway
does not notice a dead cloud until the next forward attempt — there
is no keepalive; detection is send-failure-driven, exactly as the
P03 design states. After the first failed send, health is truthful.
This is a design characteristic, not a defect, but it means
"cloud_connected" can lag reality for the duration of an idle
interval.

## 13. F-08 Verification — Metrics: PASS

Counter deltas around real triggered events (before → after):

| Event | Metric | Delta |
| --- | --- | --- |
| 3 valid fallback hellos | `fallback_activations` | 0 → 3 (per authenticated hello — documented meaning) |
| 3 valid fallback hellos, one device | `legacy_devices_detected` | 0 → 1 (distinct ids) |
| 1 reading + its replay | `messages_received` | 0 → 2 (wire reads) |
| 1 reading + its replay | `messages_processed` | 0 → 1 (replay decrypted but NOT processed) |
| 1 reading | `messages_forwarded` | 0 → 1 |
| unknown device + replay | `messages_rejected` | 0 → 2 |
| malformed hello | gateway `errors` | 0 → 1 |
| malformed encaps | cloud `errors` | 0 → 1 |

Units: `payload_bytes` reports `"unit": "bytes"` (avg 113.0),
`forward_s` `"unit": "s"` (avg 0.000092), `mlkem_establish_s`
`"unit": "s"` (avg 0.008659) — the P02 mislabeling is gone. Every
semantic was checked by triggering the event and comparing before/
after snapshots, not by reading variable names.

## 14. F-13 Verification — Health: PASS

- Normal state: gateway `/health` `status: ok`, `cloud_state:
  established`, `cloud_connected: true`; cloud `/health` `ok`.
- Cloud disconnected: after a failed forward,
  `status: degraded, cloud_connected: false, cloud_state: connecting`
  (section 12).
- After reconnect: `ok` / `established` with the new session id.
- Health derives from the state machine + socket + key
  (`is_established()`), not merely from a socket object existing —
  after invalidation the endpoint immediately reported the failed
  state. (Two honesty notes: NEW-2 and NEW-3 in sections 6/12.)

## 15. Protocol Robustness (P05 section 16): PASS

Malformed-input battery against both services (one connection per
input; service liveness + valid flow re-verified after):

| Input | Gateway result | Cloud result |
| --- | --- | --- |
| empty message | controlled close | controlled close |
| invalid JSON | controlled close | controlled close |
| JSON array | controlled close | controlled close |
| JSON string | controlled close | controlled close |
| missing fields | controlled close | controlled close |
| wrong field types | controlled close | controlled close |
| invalid base64 | controlled close | — |
| truncated mid-message | waits for data (60 s timeout, F-12 deferred); client close → `connection closed mid-message` logged (F-15 fix verified) | same |
| oversized line (>64 KiB) | controlled close, `message exceeds maximum allowed size` | same |
| unexpected message type | controlled close | controlled close |

**Result:** 0 tracebacks anywhere, both processes alive, both
`/health` endpoints `ok` afterwards, and a valid end-to-end flow
(seq 600 stored in the cloud) worked after the battery.

## 16. Cryptographic Integration Verification: PASS (18/19 checks)

Library + project-wrapper checks (the only scenario that imports
project code — it verifies the wrappers, implements no crypto):

- ML-KEM-768 sizes: public key 1184 B, ciphertext 1088 B, shared
  secret 32 B — match the project constants;
- encaps/decaps shared secrets identical (round trip through the
  project wrappers);
- wrong-**length** ciphertext → `MLKEMDecapsulationError`;
- wrong-but-valid-length ciphertext → **no exception** (FIPS 203
  implicit rejection), the derived key differs, and AEAD rejects all
  traffic under the rejection-derived key — the application's
  protection is the AEAD, correctly;
- HKDF-SHA256 deterministic, 32-byte output, varies with the secret;
- AEAD detects modified ciphertext, modified AAD, and modified
  nonce (all → `LegacyDecryptionError`);
- hello tag round trip; modified claims → `AuthenticationError`;
- fingerprints are 64-hex SHA-256.

**The one FAIL is the discovered defect:** a wrong-length nonce
(8 B) in an envelope raises an unhandled `ValueError` instead of a
controlled `CryptoError` — see NEW-1 (section 21), confirmed live in
section 17's probe.

## 17. Secret Leakage Verification: PASS

- **Source:** the only key-adjacent log statements print file paths
  and the public-key **fingerprint** (a safe identifier). No private
  key, shared secret, PSK, or session key is logged anywhere.
- **Runtime logs (all scenario runs):** zero hex runs ≥ 96
  characters (the private seed would be 128 hex chars); the only
  64-hex values present are cloud startup **fingerprints**; the demo
  device-key hex values never appear in logs.
- **Health endpoints:** gateway and cloud `/health` responses
  contain only status, session id, counters, and timings — no key
  material. `/readings` contains only reading data. (Full JSON
  dumps captured as evidence.)
- **By design (not leakage, documented):** `cloud_state/cloud.key`
  is the 64-byte ML-KEM private seed persisted across restarts
  (required for pinning stability); file permissions are not
  hardened — already an accepted README limitation. Demo device
  keys live in config/compose as documented demo values (simulated
  provisioning).

## 18. Regression Testing After Security Tests

```text
$ .venv/Scripts/python.exe -m pytest -q
101 passed in 0.58s
```

- The security experiments left the project in its original state:
  all runs used temp state dirs and non-default ports;
  `device_state/` and `cloud_state/` mtimes are unchanged (2026-09-07,
  i.e. P04); a checksum comparison of **all 84 project files**
  (excluding `.venv/`, `.pytest_cache/`, and the two state dirs)
  before vs. after P05 shows **zero differences**;
- no listener remains on any harness port (verified with netstat).

## 19. Docker / CI

- **Docker verification: NOT AVAILABLE.** `docker` is not installed
  on this machine; the compose file was **not** executed. P04's
  honest wording is confirmed — nothing here simulates a Docker
  result.
- **Remote CI: NOT VERIFIED.** The directory is not a git
  repository, so the workflow has never run. `.github/workflows/
  ci.yml` was inspected: checkout → setup-python 3.12 → `pip install
  -r requirements.txt` (pinned) → `pytest` — it fails the build on
  test failure by construction, and it does not build Docker images
  or run integration tests (a gap the workflow's own TODO list
  acknowledges). CI success is not claimed.

## 20. Independent Attack Matrix

| Attack | P02 Baseline | P04 Claim | P05 Independent Result | Status |
| --- | --- | --- | --- | --- |
| F-01 key substitution | accepted | rejected | substituted valid key rejected 6/6 attempts, no session, no encaps sent, gateway alive | **PASS** |
| F-02 downgrade | possible | rejected | all 8 manipulation variants rejected; exactly 1 fallback for 1 valid legacy hello; tampered claims break the tag | **PASS** |
| F-03 malformed handshake | crash | controlled | 10 malformed handshakes, 8 variant classes → controlled ProtocolErrors, process alive, 0 tracebacks | **PASS** |
| F-04 malformed encaps | thread failure | controlled | 5 variants → controlled close, 0 tracebacks, errors +5, service fully available after | **PASS** |
| F-05 replay | accepted | rejected | exact replay rejected (both hops), exactly one copy stored, AAD/seq/device/session tampering all rejected; jump-window limitation confirmed live | **PASS** |
| F-06 impersonation | possible | rejected | wrong-key, rewritten-device-id and unknown-device all rejected; correct keys accepted | **PASS** |
| F-07 cloud failure | wedged | reconnect | degraded after failed forward → auto reconnect with NEW session id → forwarding resumed; cloud evicts dead sessions | **PASS** |
| F-08 metric errors | inconsistent | corrected | every counter moved exactly per its documented meaning; units bytes/s correct | **PASS** |
| F-13 health | misleading | truthful | ok → degraded/connecting → ok tracks the real state machine; two honesty nuances recorded (NEW-2/NEW-3) | **PASS** |

No cell above is marked PASS without independent reproduction.

## 21. Failed or Partially Verified Claims — and New Findings

Nothing P04 claimed **failed** to reproduce. However:

**NEW-1 — Wrong-length AEAD nonce → uncontrolled handler-thread
traceback (LOW-MEDIUM, newly discovered in P05).**

```text
Finding:
  A hello (auth_nonce), legacy reading, or protected reading whose
  nonce field is valid base64 of the WRONG length (8 bytes instead
  of 12) reaches ChaCha20Poly1305.decrypt(), which raises
  ValueError("Nonce must be 12 bytes"). ValueError is not in any
  handler catch set, so the handler THREAD dies with an
  uncontrolled traceback and the connection closes.

Expected:
  Controlled rejection like every other malformed-input class:
  a crypto/protocol error, a log line, an errors/metrics increment,
  no traceback (the P04 hardening standard).

Actual:
  gateway <- hello with 8-byte nonce:         thread traceback
  gateway <- reading with 8-byte nonce:       thread traceback
  cloud   <- protected reading, 8-byte nonce: thread traceback
  errors metric delta: 0 (all three failures unaccounted)
  processes stay alive; a subsequent valid flow works (thread-level
  impact only).

Security impact:
  Remote attacker-controlled input kills handler threads with raw
  tracebacks and bypasses the error counters. Process-level DoS is
  NOT achieved (daemon threads; the accept loop survives), so the
  severity is LOW-MEDIUM. It also contradicts the P04 statement
  that malformed input produces "no uncontrolled traceback".

Reproduction:
  Send any of the three messages above with "nonce" set to
  base64 of 8 bytes (live probe recorded; wrapper-level check:
  common/crypto.py _aead_decrypt and verify_hello_auth raise
  ValueError for wrong-length nonces).

Affected component:
  common/crypto.py (_aead_decrypt line ~97, verify_hello_auth line
  ~155); gateway/gateway.py _handle/_serve_legacy; cloud/cloud.py
  _receive_readings.

Recommended action (for P06, not performed in P05):
  Validate the decoded nonce length before decrypt (12 bytes), or
  fold ValueError into the existing error taxonomy in
  _aead_decrypt/verify_hello_auth, plus regression tests on all
  three paths and error-counter assertions.
```

**NEW-2 — Gateway `/health` does not exist during the initial
establishment retry loop (observation).** `main()` starts the health
server only after `connect_and_establish()` succeeds, so a gateway
that cannot reach/authenticate the cloud at startup has no health
signal at all. P04's "health degraded" wording for the F-01/F-03
retry-loop attacks is therefore not reproducible via `/health` in
that scenario (verified). Not a security defect; an observability
gap worth recording (P06 candidate).

**NEW-3 — No proactive cloud-failure detection (observation,
matches design).** Health stays `ok/established` after a cloud kill
until the next forward attempt fails (no keepalive). This is the
P03-approved send-failure-detection design; recorded so the
limitation is understood, not treated as a lie in `/health`.

**Partial/unverifiable items:** Docker (NOT AVAILABLE) and CI (NOT
VERIFIED) — environmental, honestly reported in section 19.

## 22. Remaining Risks (verified against the actual code)

Every README section-7 limitation was re-checked against the code
and/or live behavior:

| # | Limitation | P05 check | Classification |
| --- | --- | --- | --- |
| 1 | No TLS; metadata visible; tampering only detected where tags/pins apply | plain TCP everywhere; detection paths verified live | Accepted limitation |
| 2 | Cloud does NOT authenticate gateways (self-declared `gateway_id`) | cloud only requires a non-empty string | Deferred security improvement |
| 3 | Static demo keys; no rotation/revocation/expiry | static config/env; pin manual | Accepted limitation |
| 4 | Gateway/cloud restart loses replay state until devices re-send | `ReplayGuard` is per-process memory (code inspection) | Accepted limitation |
| 5 | No sequence jump window | **demonstrated live** (seq 100 accepted; seq 6 then stale) | Accepted limitation (confirmed) |
| 6 | Hello replay re-triggers fallback activation | **demonstrated live** (+2 activations) | Accepted limitation (confirmed) |
| 7 | Device has no reconnect logic | **demonstrated live** (device exits on gateway death) | Deferred security improvement |
| 8 | No rate limiting / thread caps | thread-per-connection, 60 s timeout (code) | Accepted limitation |
| 9 | No key zeroization (Python) | immutable bytes (code) | Accepted limitation |
| 10 | Simulated provisioning; manual pin provisioning | env/config registry; pin copy (verified flow) | Accepted limitation |
| 11 | Docker compose never executed | Docker not installed here | NOT VERIFIED (environment) |
| 12 | CI never executed | not a git repository | NOT VERIFIED (environment) |

Plus the three new findings from section 21. Nothing here is
reclassified as a vulnerability that was already accepted in P03
scope.

## 23. P05 Overall Verdict

```text
P05 Overall Verdict:

PARTIAL PASS

Reason:
  Every P04 security claim was independently reproduced with
  attacker-constructed inputs over real sockets: all nine attack
  classes now behave as P04 claimed (attack matrix section 20),
  the baseline and final regression both show 101 passed, and
  secret-leakage checks came back clean. The verdict is PARTIAL
  rather than PASS because (a) the independent verification
  discovered a NEW robustness defect (NEW-1: wrong-length AEAD
  nonce -> unhandled ValueError -> handler-thread traceback,
  errors uncounted) that the P04 "no uncontrolled traceback"
  standard does not yet cover, and (b) Docker and CI remain
  verifiably unexecuted in this environment.

Security controls independently verified:
  F-01 fingerprint pinning, F-02 authenticated hello + fallback
  policy, F-03/F-04 handshake validation (no more crashes),
  F-05 replay protection on both hops + AAD binding + device
  counter persistence, F-06 per-device key isolation, F-07
  session lifecycle with reconnect and eviction, F-08 metric
  semantics/units, F-13 truthful health, protocol robustness
  battery, crypto integration (18/19 wrapper checks), secret
  leakage.

Security controls only partially verified:
  None of the P04 controls. (Health truthfulness carries two
  recorded nuances: NEW-2, NEW-3.)

Security controls not verified:
  Docker compose (Docker NOT AVAILABLE on this machine);
  CI execution (directory is not a git repository).

New defects discovered:
  NEW-1 wrong-length AEAD nonce -> uncontrolled handler-thread
  traceback, errors metric bypassed (LOW-MEDIUM, recorded, NOT
  fixed per P05 section 25).
  NEW-2 /health unavailable during initial establishment retry
  loop (observability gap).
  NEW-3 no proactive cloud-failure detection (matches design;
  recorded for honesty).

Remaining accepted risks:
  README section 7 limitations 1-10 (each re-verified, section
  22), plus Docker/CI unverified, plus NEW-1 pending fix.

Recommended next phase:
  P06: (1) fix NEW-1 (nonce length validation in the AEAD
  wrappers + regression tests + error-counter assertions);
  (2) optionally start the gateway health server before the
  establishment loop (NEW-2); (3) keep Docker/CI verification
  pending until an environment with Docker and a git remote
  exists. All other P04 controls require no further work.
```

---

## Final Output

- **Tests:** `pytest -q` → **101 passed** (baseline 0.88 s; final
  re-run after all attacks 0.58 s; 0 failed, 0 skipped).
- **Independent attacks:** exact results in sections 6–16 and the
  matrix in section 20; every cell independently reproduced.
- **Security verdict:** **PARTIAL PASS** (section 23).
- **Files created:** `review/P05 - Independent Security Verification
  & Re-test.md` (this report). External temporary attack harness
  outside the project tree: `D:\Code\Claude\p05-verify\`
  (p05lib.py, p05_attacks.py, evidence/, logs/, state/) — permitted
  by P05 section 2 as temporary external tooling; it is not part of
  the project.
- **Files modified:** **none.** Checksum comparison of all 84
  project files (excluding `.venv/`, `.pytest_cache/`, state dirs)
  before vs. after P05: zero differences. `device_state/` and
  `cloud_state/` untouched (mtimes 2026-09-07). No test was changed
  to obtain the green run.
- **Docker:** NOT AVAILABLE (not installed; compose not executed).
- **CI:** NOT VERIFIED (not a git repository; workflow inspected
  only).
- **New findings:** NEW-1 (wrong-length nonce → thread traceback,
  uncounted error), NEW-2 (health absent during initial retry
  loop), NEW-3 (idle gateway unaware of dead cloud) — details and
  evidence in section 21. Recorded, **not** fixed, per P05
  section 25.
- **Remaining risks:** section 22.
- **P06 recommendation:** required — fix NEW-1 first; NEW-2/NEW-3
  are optional observability improvements; Docker/CI stay
  unverifiable in this environment.
