# P02 Baseline Technical Review

> **AI-generated review draft.** This review was produced by an AI
> assistant from `prompt/P02 - Baseline Testing & Technical Review.md`.
> The student team must verify every finding, make their own decisions,
> and record them (ACCEPTED / MODIFIED / REJECTED) in the project's
> technical documentation. **No project code was modified during this
> review.**
>
> Review environment: Windows 11, Python 3.12.0, cryptography 50.0.1,
> pytest 9.1.1. Review date: 2026-09-07.

---

## 1. Executive Summary

The P01 baseline is a **small, runnable, and mostly well-structured
university prototype**. The happy path works end-to-end: the legacy
device, gateway, and cloud interoperate, ML-KEM-768 sessions establish
correctly against the *installed* library API, and 39/39 pytest tests
pass.

However, passing tests prove almost nothing about security. The review
confirms — with live demonstrations, not just code reading — three
concrete problems:

1. **Replay is trivially possible.** A captured encrypted reading was
   re-transmitted and accepted/stored a second time by the cloud. The
   `sequence` field exists in the plaintext but is never checked.
2. **One malformed message can crash components.** A handshake message
   missing a required field crashed the *entire gateway process*
   (uncaught `KeyError`, exit code 1) and crashed a cloud handler
   thread with a raw traceback. Both paths are reachable by any
   network peer, because there is no TLS and no authentication.
3. **Key establishment is unauthenticated.** The gateway accepts the
   cloud's ML-KEM public key over an unauthenticated channel — the
   classic precondition for a man-in-the-middle attack on the KEM. The
   fallback path has the same disease: capability claims and
   device identity are self-declared.

These weaknesses were partially *documented* in the README, but
documentation does not mitigate them. The rest of the baseline
(protocol framing, library usage, logging hygiene, test structure,
metrics) is reasonable for its purpose, with a set of smaller
maintainability and operational findings listed below.

---

## 2. What Currently Works

### Tested (automated, verified during this review — 39/39 passed)

- Sensor reading generation (fields, ranges, deterministic timestamp).
- ChaCha20-Poly1305 round trip + wrong-key / tampered-ciphertext /
  malformed-envelope rejection.
- ML-KEM-768 encaps/decaps round trip, 32-byte shared secret, public
  key serialization round trip, garbage-key rejection.
- HKDF session-key derivation (determinism, variation with secret).
- JSON-lines protocol framing: round trip, invalid JSON, non-object,
  oversized message rejection, clean disconnect, multiple messages.
- Gateway/cloud message processing logic on both paths.
- Metrics counters and timing aggregation.

### Manually verified (live runs during P01 and this review)

- End-to-end smoke test: device → gateway → cloud, readings stored.
- ML-KEM-768 session establishment over real TCP sockets.
- Fallback activation for a legacy device (warning logged).
- Health endpoints (`/health` on gateway and cloud) return live
  metrics; cloud `/readings` shows stored data.
- No secret material in logs (grep scan in P01, repeated on current
  logs during this review).
- ML-KEM API matches the installed library: `cryptography 50.0.1`,
  module `cryptography.hazmat.primitives.asymmetric.mlkem`,
  `MLKEM768PrivateKey.generate()`, `encapsulate()`,
  `decapsulate()`, `public_bytes(Encoding.Raw, PublicFormat.Raw)`.

### Not verified

- **Docker / docker-compose: NOT verified.** Docker is not installed
  on the review machine. Nothing in this report claims compose works;
  section 9 lists inspection-only findings.
- **GitHub Actions CI: NOT verified.** The workflow was never
  executed (the directory is not a git repository / no push).
- Behavior on Linux (only Windows tested locally).
- Concurrent clients, partial-TCP-message handling, cloud-failure
  mid-run (code inspection only).
- Session expiry / rotation (not implemented at all).

---

## 3. Critical Findings

### F-01 — Unauthenticated ML-KEM key establishment (MITM)

- **ID:** F-01
- **Category:** Security — authentication
- **Severity:** HIGH
- **Location:** `gateway/cloud_channel.py:92` (`reply["public_key"]`),
  `cloud/cloud.py` `_establish_session()`
- **Problem:** The gateway requests the cloud's ML-KEM public key over
  plain TCP and uses it without any authentication. A network attacker
  can substitute their own public key, decapsulate the gateway's
  ciphertext, derive the same session key, and then relay traffic —
  impersonating the cloud in both directions.
- **Why it matters:** This is the difference between **key
  establishment** (two parties end up with a shared secret) and
  **authenticated key establishment** (they end up with a shared
  secret *and* knowledge of who holds the other side of it). ML-KEM
  protects against passive eavesdroppers; it says nothing about the
  identity of the key owner. The entire "modern/PQC path" currently
  provides confidentiality against a passive attacker only, not
  against an active one. This defeats the central purpose of the
  project.
- **Evidence:** Code inspection (no signature, certificate, pin, or
  pre-shared trust anchor for the public key). README §8.2 documents
  the same limitation. Not demonstrated live (would require building
  an active relay), but it follows directly from the design.
- **Recommended action:** Student decision required (see §13, P0-1).
  Options to compare: ML-KEM signature binding (ML-KEM-PK / certificate
  chain), pre-shared public-key pinning for the prototype, or TLS as
  the transport. Do not implement a "full authentication system" yet —
  decide the approach first.

### F-02 — Unauthenticated capability claims → downgrade / spoofing

- **ID:** F-02
- **Category:** Security — fallback / downgrade
- **Severity:** HIGH
- **Location:** `gateway/processing.py` (`determine_path()`),
  `gateway/gateway.py` `_handle()`
- **Problem:** The gateway selects the legacy vs. modern path based on
  a plaintext, self-declared hello. (a) A MITM can strip `ml-kem-768`
  from a modern device's hello and force the weaker fallback path with
  no detection. (b) A device can claim any capabilities it likes; the
  gateway has no way to authenticate them. (c) A device claiming
  `ml-kem-768` gets its connection closed because the modern path is
  not implemented — a trivially triggerable denial of service for any
  device that declares that capability.
- **Why it matters:** Downgrade attacks make the PQC upgrade
  meaningless: an attacker who can force legacy crypto wins. The
  baseline *documents* the gap but ships no policy.
- **Evidence:** Code inspection; the baseline contains no modern
  device, so live stripping could not be demonstrated, but the
  decision logic is a single unauthenticated list check.
- **Recommended action:** This is exactly the fallback-policy work the
  prompt reserved for students (§13, P0-3): how capability is
  authenticated, when fallback is permitted, when devices are
  rejected, and how downgrade is detected.

### F-03 — One malformed handshake message crashes the whole gateway

- **ID:** F-03
- **Category:** Robustness — availability
- **Severity:** HIGH
- **Location:** `gateway/cloud_channel.py:92`
  (`protocol.b64d(reply["public_key"])`), retry loop at
  `cloud_channel.py:67`
- **Problem:** `_establish_once()` accesses `reply["public_key"]`
  without checking the field exists. A malformed `mlkem_pubkey` reply
  (missing `public_key`) raises `KeyError`, which is **not** in the
  retry loop's catch set (`OSError, ProtocolError, CryptoError`), so
  it escapes to `main()` and terminates the entire gateway process.
- **Why it matters:** With no TLS/authentication, *any* peer that can
  reach the gateway's cloud port can kill the gateway with one
  message. The gateway is the central component of the system. Severity
  is HIGH for this prototype precisely because the trigger is trivial
  and remote.
- **Evidence:** **Live demonstration during this review.** A fake
  cloud on port 5002 replied with
  `{"type": "mlkem_pubkey", "cloud_id": "fake-cloud"}` (no
  `public_key`). The gateway printed an uncaught `KeyError: 'public_key'`
  traceback and exited with code 1.
- **Recommended action:** Validate all required handshake fields
  before use and raise `ProtocolError` instead (small fix, see §13
  P0-2). Do not merely extend the catch set — fix the validation.

### F-04 — Malformed encaps crashes a cloud handler thread (unlogged)

- **ID:** F-04
- **Category:** Robustness — availability
- **Severity:** MEDIUM
- **Location:** `cloud/cloud.py:130` (`encaps["ciphertext"]`)
- **Problem:** Same class of bug on the cloud side:
  `_establish_session()` accesses `encaps["ciphertext"]` without
  validation. The resulting `KeyError` is not caught by `_handle()`,
  the connection thread dies with a raw traceback, and — unlike other
  failure paths — the `errors` metric is **not** incremented and no
  application log line is written. Only the thread dies (the process
  survives), hence MEDIUM rather than HIGH.
- **Evidence:** **Live demonstration during this review.** A client
  sent `mlkem_encaps` without `ciphertext`; the cloud's thread printed
  `KeyError: 'ciphertext'` and closed the connection with no log
  record beyond the traceback.
- **Recommended action:** Same as F-03: validate fields, raise
  `ProtocolError`. Also review why this path bypasses the `errors`
  counter (see F-08).

### F-05 — No replay protection (demonstrated)

- **ID:** F-05
- **Category:** Security — message freshness
- **Severity:** MEDIUM
- **Location:** Protocol as a whole (`gateway/processing.py`,
  `cloud/processing.py`, `common/protocol.py`)
- **Problem:** Nothing binds messages to freshness. Readings carry a
  `sequence` number in the plaintext, but neither the gateway nor the
  cloud validates monotonicity. Random per-message nonces prevent
  nonce reuse but do nothing against replaying a *captured, previously
  valid* message.
- **Why it matters:** An attacker who records traffic can re-inject
  old readings at will (e.g. re-report a safe temperature while the
  real sensor reports a dangerous one). On the protected path the
  replay succeeds until the (never-expiring) session ends; on the
  legacy path it succeeds indefinitely.
- **Evidence:** **Live demonstration during this review.** A fake
  device sent one valid encrypted reading (`sequence: 7`, temp 99.9),
  then re-transmitted the identical captured bytes on a fresh
  connection. The cloud stored the reading **twice** (confirmed via
  `/readings`).
- **Recommended action:** Student decision (P0-4): per-device
  monotonic sequence numbers checked by the gateway/cloud, replay
  windows, or session-bound counters. Identify what is missing first;
  do not rush a framework.

### F-06 — Static shared PSK for all legacy devices

- **ID:** F-06
- **Category:** Crypto — key management
- **Severity:** MEDIUM
- **Location:** `common/config.py` (`LEGACY_PSK_HEX`),
  `docker-compose.yml`
- **Problem:** One pre-shared key, fixed in an environment variable,
  protects every legacy device. There are no per-device keys, no
  provisioning, no rotation, no revocation. `device_id` is
  self-declared, so one compromised or malicious device can
  impersonate any other.
- **Why it matters:** The fallback path's confidentiality is only as
  strong as the weakest holder of the shared key; identity checks are
  cosmetic.
- **Evidence:** Code inspection; documented in README §8.4.
- **Recommended action:** P1-6: at minimum per-device keys (device_id
  → key table) for the prototype; record rotation/expiry as open
  design questions.

### F-07 — Broken cloud session leaves the gateway permanently wedged

- **ID:** F-07
- **Category:** Operations — failure handling
- **Severity:** MEDIUM
- **Location:** `gateway/cloud_channel.py` (`send_reading()`),
  `gateway/gateway.py` health provider
- **Problem:** If the cloud dies *after* establishment, `sendall`
  raises, `_sock` is never cleared, and `is_established()` keeps
  returning `True` — so the health endpoint reports
  `cloud_connected: true` forever while every device connection fails
  on forward. There is no reconnect (the retry loop only runs at
  startup). Related: `session_id` is generated once in `__init__` and
  reused across all retry attempts, and the cloud's `SessionRegistry`
  never evicts sessions (unbounded growth across gateway restarts).
- **Why it matters:** A transient cloud failure permanently degrades
  the system, and the health check lies about it.
- **Evidence:** Code inspection (not demonstrated live — would
  require killing the cloud mid-run; easy for students to reproduce).
- **Recommended action:** P1-5: clear session state on send failure,
  implement reconnection, and report the real state in `/health`.

### F-08 — Metrics semantics and consistency problems

- **ID:** F-08
- **Category:** Metrics / observability
- **Severity:** LOW
- **Location:** `common/metrics.py`, `gateway/gateway.py:114-116`,
  `gateway/cloud_channel.py`, `cloud/cloud.py`
- **Problem:** (a) `payload_bytes` is fed into the *timing* aggregate,
  so its snapshot fields are labeled `avg_s`/`min_s`/`max_s` while
  containing byte counts — units are wrong. (b) `forward_ms` records
  milliseconds into fields labeled `_s`. (c) `fallback_events` counts
  *connections* that activated fallback, not fallback events per
  message — the name overstates what it measures. (d) `errors` is not
  incremented on handshake failures (F-04) or when the gateway drops
  a connection due to protocol errors in `_handle`'s first branch.
  (e) The device exposes no metrics at all.
- **Why it matters:** Baseline measurements are the input for later
  evaluation; mislabeled units will silently corrupt any analysis.
- **Evidence:** Code inspection + health-endpoint output observed
  during this review (`payload_bytes` reported under `avg_s`).
- **Recommended action:** P2-9: split size observations from timing
  observations (or rename units), decide what `fallback_events`
  means, and count errors on every failure path.

### F-09 — Duplicated AEAD envelope code

- **ID:** F-09
- **Category:** Maintainability
- **Severity:** LOW
- **Location:** `common/crypto.py`
  (`encrypt_legacy_payload`/`encrypt_session_payload` +
  `decrypt_legacy_payload`/`decrypt_session_payload`)
- **Problem:** Two pairs of nearly identical functions differ only in
  exception type. Any future change (nonce length, AAD, envelope
  format) must be made twice.
- **Evidence:** Code inspection.
- **Recommended action:** P2-10: one generic pair parameterized by
  error class, or thin wrappers over a shared core.

### F-10 — Configuration duplicated across two sources of truth

- **ID:** F-10
- **Category:** Maintainability / deployment
- **Severity:** LOW
- **Location:** `common/config.py` vs `docker-compose.yml`
- **Problem:** Ports and the PSK hex value exist both in code defaults
  and in compose environment variables. They can silently diverge
  (e.g. compose maps 5002 while code defaults drift).
- **Evidence:** Code inspection.
- **Recommended action:** P2-11: document which side is authoritative,
  or generate one from the other.

### F-11 — Key material has no lifecycle or destruction policy

- **ID:** F-11
- **Category:** Crypto — key lifecycle
- **Severity:** LOW (prototype; INFO for production)
- **Location:** whole system (`SessionRegistry`, `CloudChannel`,
  `config.legacy_psk()`)
- **Problem:** Keys and shared secrets live in immutable Python
  `bytes` for the lifetime of the process; nothing is zeroized or
  destroyed. Session keys persist in the cloud registry even after
  their gateway disconnects.
- **Evidence:** Code inspection.
- **Recommended action:** P3-14: document retention assumptions;
  evict sessions on disconnect; note that Python cannot guarantee
  zeroization (a C extension would be needed — out of scope).

### F-12 — Unbounded threads, long timeouts, no rate limiting

- **ID:** F-12
- **Category:** Operations
- **Severity:** LOW
- **Location:** `gateway/gateway.py`, `cloud/cloud.py`
  (`Thread(...).start()` per connection; `settimeout(60)`)
- **Problem:** Every connection spawns a thread with no cap, and
  connections can hold resources for 60 s without sending data. No
  rate limiting exists (README §8.9 partially notes this).
- **Evidence:** Code inspection.
- **Recommended action:** P3-13: thread pool or connection cap;
  shorter read timeouts; note rate limiting as a design question.

### F-13 — Health endpoint cannot express degraded states

- **ID:** F-13
- **Category:** Health checks
- **Severity:** LOW
- **Location:** `common/health.py`
- **Problem:** `/health` always returns `"status": "ok"` unless the
  provider itself raises. Combined with F-07, the health check can
  report healthy while the system cannot forward traffic. Also binds
  0.0.0.0 unauthenticated (documented).
- **Evidence:** Code inspection + observed responses.
- **Recommended action:** P2-12: derive status from real invariants
  (cloud session usable, device listener bound); leave auth questions
  as TODOs.

### F-14 — Dependency drift risk for ML-KEM

- **ID:** F-14
- **Category:** CI/CD — reproducibility
- **Severity:** LOW
- **Location:** `requirements.txt`, `.github/workflows/ci.yml`
- **Problem:** `cryptography>=45.0` is unpinned. The API surface for
  ML-KEM already shifted between versions during P01 (the P01 draft
  assumed module `ml_kem`; the installed 50.0.1 exposes `mlkem` with
  `MLKEM768PrivateKey.generate()`). A future major version could
  rename again, and CI installs whatever is latest — so CI may not
  reproduce the local environment over time. CI also only runs unit
  tests (no Docker build, no smoke test).
- **Evidence:** P01 correction history; `pip` resolves to 50.0.1
  today.
- **Recommended action:** P1-8: pin `cryptography==50.0.1` (or a
  narrow range) in `requirements.txt`; add a CI step that imports the
  ML-KEM classes to fail fast on API drift.

### F-15 — Misleading error text for truncated final messages

- **ID:** F-15
- **Category:** Protocol — error semantics
- **Severity:** LOW
- **Location:** `common/protocol.py` `read_message()`
- **Problem:** A peer that sends a partial message and closes the
  connection (no trailing newline) triggers
  `ProtocolError("message exceeds maximum allowed size")` — the
  message did not exceed the limit; it was truncated. The distinction
  matters for diagnostics and for distinguishing attack traffic from
  flaky devices.
- **Evidence:** Code inspection (the `len(line) > MAX` /
  `endswith(b"\n")` combined check).
- **Recommended action:** P2: split "truncated at EOF" from
  "exceeds size limit".

---

## 4. Cryptography Review

**ML-KEM API usage — verified against the installed library.**
The code uses `cryptography 50.0.1`'s `mlkem` module correctly:
`MLKEM768PrivateKey.generate()`, `public_key()`,
`public_bytes(Encoding.Raw, PublicFormat.Raw)` /
`MLKEM768PublicKey.from_public_bytes()`, `encapsulate()` returning
(32-byte shared secret, 1088-byte ciphertext), `decapsulate()`. All
unit tests pass and live sessions establish. The P01 assumption about
the `ml_kem` module name was wrong for the installed version; the
corrected code matches reality (see F-14 for the reproducibility
implication).

**Implicit rejection — handled correctly, by accident of design.**
FIPS 203 implicit rejection means decapsulating a *wrong but
correctly-sized* ciphertext does **not** raise — it returns a
pseudorandom rejection key. The review confirms the application does
not rely on decapsulation raising to authenticate anything: the
derived session key is used in ChaCha20-Poly1305, and a rejection key
makes every AEAD decryption fail. That is the correct pattern, and
`common/crypto.py` documents it. Only wrong-*length* ciphertexts raise
(`ValueError`), which is caught and wrapped.

**HKDF.** SHA-256, `salt=None`, domain-separating `info` string
(`pqc-bridge/gateway-cloud-session/v1`). Both sides derive identical
keys (round-trip tested). Reasonable for the prototype. Note: no
channel binding — the session_id is not authenticated as AAD, so
messages are bound to the session only via the key itself. Fine here
because keys are per-session; worth recording as a design note.

**AEAD.** ChaCha20-Poly1305 with 12-byte random nonces
(`os.urandom`). Correct API usage; tamper/wrong-key cases tested.
Nonce collision probability is negligible at demo rates, but there is
no nonce-misuse-resistance and no nonce-management policy — a future
multi-key-era system needs explicit rules. `AAD=None` everywhere.

**Key separation.** Legacy PSK (device↔gateway) and the HKDF-derived
session key (gateway↔cloud) are independent; the info string prevents
cross-context reuse. The legacy PSK is used directly as an AEAD key
(no KDF) — acceptable for the simulation, but it means the PSK's
entropy directly caps the fallback path's strength.

**Session lifecycle / key storage / destruction.** Static ML-KEM
keypair; sessions never expire; registry never evicts; keys live in
immutable bytes for process lifetime (F-11). The cloud stores derived
session keys per session — required to decrypt — but with no TTL or
cleanup. All of this is documented but not mitigated.

**Authentication.** See F-01/F-02. The system performs **key
establishment, not authenticated key establishment**. The resulting
confidentiality property is: protection against passive eavesdropping
(after key agreement) and against tampering of in-transit ciphertext
— but **no protection against an active attacker who can position
themselves in the path**, because neither end ever verifies the
identity of the other. This must be stated plainly in any report the
students produce.

---

## 5. Protocol Review

**What is solid:**
- JSON-lines framing is simple and enforceable; the 64 KiB per-message
  cap is actually enforced in `read_message()` and tested.
- Malformed JSON, non-object top level, invalid base64, oversized
  messages, and clean disconnects all produce typed errors
  (`ProtocolError` / `ConnectionClosedError`) with tests.
- Multiple messages per connection work (tested).
- Unexpected message types on established paths are handled
  (drop-and-continue on device/reading paths, close on handshake
  paths).

**Concrete failure scenarios identified:**
1. Missing required fields in *handshake* messages → uncaught
   `KeyError` → gateway process death (F-03) / cloud thread death
   (F-04). The asymmetric validation (reading envelopes validate
   defensively; handshake messages do not) is the core inconsistency.
2. Truncated final message mislabeled as oversized (F-15).
3. No protocol version field — any evolution of the wire format will
   be ambiguous across versions.
4. No freshness/channel binding (F-05) — covered above.
5. A peer that connects and sends nothing holds a thread for 60 s
   (F-12).
6. Device side never reads replies: if the gateway rejects a device
   (e.g. unknown capabilities), the device keeps sending into a closed
   socket until an error surfaces — acceptable minimalism, but the
   hello handshake is one-way, so the device cannot distinguish
   "rejected" from "accepted".

---

## 6. Fallback / Downgrade Review

The gateway's decision table is:

| Claimed capabilities | Decision | Notes |
|---|---|---|
| contains `ml-kem-768` | "modern" | connection closed — path not implemented (self-DoS possible) |
| contains `chacha20-poly1305` only | "legacy" | fallback activated, weaker posture logged |
| neither / unknown | reject | conservative and sensible default |

Concrete weaknesses:

1. **Capability spoofing enables forced downgrade.** Claims are
   plaintext and unauthenticated; a MITM can strip `ml-kem-768` from a
   modern device's hello and the gateway silently activates the weaker
   path (F-02). Conversely a malicious device can claim
   `chacha20-poly1305` and force fallback resource use.
2. **Fallback trust is all-or-nothing.** One shared PSK; no concept
   of trusted vs untrusted legacy devices, no per-device posture, no
   rejection policy beyond "no capabilities claimed" (F-06).
3. **No downgrade detection.** The system cannot distinguish "legacy
   device" from "modern device whose hello was tampered with".
   Detection would require authenticating capability claims (F-02) or
   out-of-band knowledge of device types.
4. **No migration signals.** Nothing in the protocol lets a device
   announce a pending upgrade, version of firmware, or migration
   schedule — the prompt's migration question is entirely unaddressed
   (TODO markers exist, correctly, per P01 §3).
5. **Fallback activation is connection-scoped.** A device
   reconnecting re-triggers fallback logging and metrics each time
   (F-08c) — noisy and easy to spoof into the metrics.

The baseline is honest about this (warnings, TODOs, README), which is
appropriate for a review artifact. Nothing here is "solved", and the
review confirms it should not be presented as such.

---

## 7. Testing Gap Analysis

| Area | Existing Coverage | Missing Tests | Priority |
| ---- | ----------------- | ------------- | -------- |
| Sensor generation | 4 functional tests (fields, range, timestamps) | boundary values, bad device_id | LOW |
| AEAD (ChaCha20-Poly1305) | round trip, wrong key, tamper, malformed envelope | nonce length checks, AAD cases, large payloads | MEDIUM |
| ML-KEM | round trip, shared-secret length, key serialization, garbage key | wrong-*length* ciphertext rejection, wrong-but-valid-length (implicit rejection) behavior | MEDIUM |
| HKDF | determinism, variation, length | info-string misuse, salt handling | LOW |
| Protocol framing | 10 tests (invalid JSON, non-object, oversized, disconnect, multi-message, b64) | partial/truncated TCP message, empty line, missing newline at EOF, unicode edge cases | HIGH |
| Hello parsing / path decision | valid/missing fields, path mapping | fake capability declaration (downgrade attempt), both capabilities claimed, hello replay | HIGH |
| Legacy path processing | round trip, wrong PSK, device_id mismatch, bad plaintext | replayed message (demonstrated broken in F-05 — no test exists), spoofed device_id with valid PSK | HIGH |
| Protected path processing | round trip, wrong key, wrong type | replayed protected message, session_id mismatch | HIGH |
| Handshake field validation | **none** | missing `ciphertext` / `public_key` / `session_id` (F-03, F-04) | HIGH |
| Cloud/gateway unavailable | **none** | connect-refused retry loop, cloud death mid-run (F-07) | HIGH |
| Connection timeout / partial messages | **none** | silent peer, 60 s timeout behavior | MEDIUM |
| Concurrency | **none** | multiple simultaneous devices, concurrent gateway sessions | MEDIUM |
| ReadingStore / health endpoints | **none** (store only exercised indirectly) | store bounds/eviction, `/health` and `/readings` responses | MEDIUM |
| Integration (real sockets) | **none** (all unit-level) | device→gateway→cloud end-to-end, replay/downgrade attacks as automated tests | HIGH |
| Metrics accuracy | 3 unit tests | error counters on every failure path (F-08d), fallback semantics | LOW |
| Docker / CI | **none** | compose health gating, CI run (never executed) | MEDIUM |

The 39 tests are reasonable *unit* tests for the happy path and basic
crypto misuse, but the highest-risk code (handshake parsing, replay
behavior, availability under failure) is exactly what is untested.

---

## 8. Maintainability Review

**Good:**
- Clear module boundaries: pure processing logic (`*_processing.py`)
  is separated from socket/thread code and is directly testable.
- Consistent exception taxonomy (`ProtocolError`,
  `ConnectionClosedError`, `CryptoError`, `ProcessingError`).
- Honest TODO markers that name the open questions rather than hiding
  them — well suited to the course's review methodology.
- Logging discipline is consistent (see §11).
- No dead framework weight; stdlib + one crypto library.

**Concerns:**
- Duplicated AEAD envelope code (F-09).
- Config duplicated between code and compose (F-10).
- `session_id` generation in `CloudChannel.__init__` couples session
  identity to object lifetime (F-07).
- Partial type hints; docstrings good overall.
- The two "drop bad message, keep connection" loops (gateway
  `_serve_legacy`, cloud `_receive_readings`) duplicate policy that
  will likely need to diverge later — a shared decision record or
  comment would prevent silent drift.
- Handshake logic mixes protocol parsing with crypto calls; the
  missing-field crashes (F-03/F-04) are a direct symptom of parsing
  not being centralized and validated up front.

---

## 9. Docker / Operations Review

**NOT VERIFIED:** Docker is not installed on the review machine, so
`docker compose up` was **not** executed. The following is
inspection-only.

- Dockerfiles: `python:3.12-slim` (unpinned minor), `pip install` of
  `requirements.txt`, selective `COPY` of `common/` + one service
  package each — clean and minimal. Because `cryptography` ships
  manylinux wheels with a bundled OpenSSL ≥ 3.5, ML-KEM should work in
  the container without system OpenSSL — plausible but unverified
  here.
- Compose: sensible service ordering via `depends_on:
  condition: service_healthy` with python-urllib healthchecks;
  gateway correctly depends on cloud health before starting. The
  device inherits `LEGACY_PSK_HEX` and gateway address from
  environment.
- Concerns (prototype level): the PSK sits in plaintext in
  `docker-compose.yml` (matches F-06); no `restart:` policies, so the
  F-03 crash takes the gateway down permanently in compose too; no
  resource limits; ports are exposed to the host; healthchecks poll
  every 5 s.
- One ordering note: the gateway refuses to serve devices until a
  cloud session exists (retry loop at startup). This couples device
  availability to cloud availability — worth a conscious decision by
  the students.

---

## 10. CI/CD Review

`.github/workflows/ci.yml` does the minimum correctly: checkout →
`setup-python@v5` with 3.12 → `pip install -r requirements.txt` →
`pytest` (fails the build on failure).

- **Reproducibility risk (F-14):** `cryptography>=45.0` is unpinned.
  CI installs the newest version, which may not match the reviewed
  environment (50.0.1) or the code's API assumptions in the future.
  ML-KEM support depends on the cryptography wheel's bundled OpenSSL,
  so the container's OpenSSL is not a variable — but the Python API
  surface is.
- CI does not build Docker images, run a compose smoke test, or
  exercise any socket-level integration — the layers where this
  review found the real defects.
- The workflow was never executed (not a git repository at review
  time); "CI works" must not be claimed until a push happens.

---

## 11. Metrics / Performance Review

**What exists:** counters (`messages_received/processed/forwarded`,
`errors`, `fallback_events`, `legacy_devices_detected`,
`mlkem_sessions_established`, connection counts) plus timing
observations (`mlkem_establish_s` at gateway,
`mlkem_decapsulate_s` at cloud, `forward_ms`, `payload_bytes`),
exposed via `/health`.

**Accuracy problems (F-08):** unit mislabeling (`payload_bytes` in a
seconds-labeled aggregate; `forward_ms` in ms under `_s` keys),
`fallback_events` actually counting activations per connection,
`errors` undercounted (handshake failures bypass it), device-side
metrics absent.

**Measurement limitations (§13 of the prompt, confirmed):**
- n = 1 for ML-KEM establishment (single session per run); no warm-up;
  gateway's `mlkem_establish_s` includes 2 network round trips while
  the cloud's `mlkem_decapsulate_s` measures decapsulation+HKDF only —
  the two numbers measure different things and must not be compared
  directly.
- All measurements were taken on localhost; network variability is
  zero, so latency numbers will not transfer to real deployments.
- No repeated trials, no percentile reporting, no payload-size
  breakdown (the observed ~120–121 B readings are one fixed shape).

**Verdict:** sufficient as *placeholders* for the baseline experiment,
not sufficient as *measurements*. Any analysis using them must first
fix F-08 and define the comparison protocol.

---

## 12. Documentation Review

- **README.md** is accurate overall. All ten security limitations
  (§8) match the actual implementation — verified by inspection and
  the demos in this review. In particular, the replay claim in
  §11.3 ("cloud accepts it") is now **empirically confirmed** by this
  review's replay demonstration.
- The AI-generated vs student-reviewed distinction is present (top
  banner, §12) and correctly states that everything is currently
  AI-generated.
- **CLAUDE.md** is brief and correct (commands verified during this
  review).
- **Gaps:** (1) The P01 API correction history (assumed `ml_kem`,
  actual `mlkem`) is not recorded anywhere in the repository — it is
  exactly the kind of AI-assist evidence the course requires and
  should be written into the technical documentation. (2) No record
  yet of the P02 review or its demonstrations (this document provides
  the material). (3) README does not mention the F-03/F-04 crash
  behavior or the confirmed replay result; §11 can now cite real
  evidence instead of predictions.

---

## 13. Recommended Student Actions

### P0 — Must review before modifying anything

1. **Authentication strategy for key establishment (F-01).** Decide
   the threat model and the mechanism (signature-bound ML-KEM key,
   public-key pinning, TLS transport) before building on the current
   handshake. Everything else is cosmetic until this is decided.
2. **Fix handshake input validation (F-03, F-04).** Minimal, high
   value: validate required fields, raise `ProtocolError`. Optionally
   add the missing regression tests at the same time.
3. **Fallback policy (F-02).** Answer the prompt's questions (trusted
   devices, permitted fallback, rejection, downgrade detection,
   credential expiry, migration) and implement the agreed policy.
4. **Replay protection approach (F-05).** Choose the mechanism
   (sequence checks, windows, session binding) and write tests that
   fail first — the replay demo in the appendix is a ready-made test
   case.

### P1 — Important improvement

5. Session lifecycle: reconnect, stale-state cleanup, truthful health
   (F-07).
6. Per-device keys / PSK management plan (F-06).
7. Add the missing HIGH-priority tests from §7 (handshake fields,
   replay, downgrade spoofing, availability, integration).
8. Pin `cryptography` and add a CI API-drift check (F-14).

### P2 — Useful improvement

9. Fix metrics units/semantics and error-count coverage (F-08).
10. Deduplicate AEAD envelope code (F-09).
11. Single source of truth for configuration (F-10).
12. Health status semantics + truncated-message error text (F-13,
    F-15).

### P3 — Future enhancement

13. Connection/thread limits, rate limiting (F-12).
14. Key destruction/eviction policy (F-11).
15. Docker hardening, CI Docker build + smoke test, wider test matrix.

---

## 14. Appendix: Review Evidence

### A. Test suite (re-run during review)

```
$ .venv/Scripts/python.exe -m pytest
tests\test_crypto.py ..........    [ 25%]
tests\test_metrics.py ...          [ 33%]
tests\test_processing.py ......... [ 64%]
tests\test_protocol.py ..........  [ 89%]
tests\test_sensor.py ....          [100%]
39 passed in 0.07s
```

### B. Replay demonstration (F-05) — CONFIRMED

Fake device sent one encrypted reading (`sequence: 7`, 99.9 °C), then
re-transmitted the identical captured bytes. Cloud `/readings`
afterwards:

```json
[{"device_id": "replay-dev", "timestamp": "2026-09-07T00:00:00+00:00",
  "temperature_c": 99.9, "unit": "celsius", "sequence": 7},
 {"device_id": "replay-dev", "timestamp": "2026-09-07T00:00:00+00:00",
  "temperature_c": 99.9, "unit": "celsius", "sequence": 7}]
```

Both transmissions accepted; no freshness check anywhere in the path.

### C. Malformed encaps → cloud thread crash (F-04) — CONFIRMED

Sent `mlkem_encaps` without `ciphertext`. Cloud output:

```
Exception in thread Thread-3 (_handle):
  File "cloud\cloud.py", line 130, in _establish_session
    self._private_key, protocol.b64d(encaps["ciphertext"]))
KeyError: 'ciphertext'
```

No application log line, no `errors` metric increment.

### D. Malformed pubkey reply → gateway process crash (F-03) — CONFIRMED

Fake cloud replied with `mlkem_pubkey` missing `public_key`. Gateway
output (exit code 1):

```
Traceback (most recent call last):
  File "gateway\gateway.py", line 141, in main
    cloud_channel.connect_and_establish()
  File "gateway\cloud_channel.py", line 67, in connect_and_establish
    self._establish_once()
  File "gateway\cloud_channel.py", line 92, in _establish_once
    protocol.b64d(reply["public_key"]))
KeyError: 'public_key'
GATEWAY EXIT CODE: 1
```

The retry loop's catch set `(OSError, ProtocolError, CryptoError)`
does not include `KeyError`, so the whole gateway terminates.

### E. Environment facts

- `docker`: not installed → compose **not** verified.
- `cryptography 50.0.1`; ML-KEM module
  `cryptography.hazmat.primitives.asymmetric.mlkem`; API verified by
  live session establishment and unit tests.
- FIPS 203 implicit rejection confirmed by code inspection: valid-
  length wrong ciphertexts do not raise; application relies on AEAD
  failure (correct pattern).

### F. What passing 39/39 tests does NOT prove

Cryptographic correctness, authentication, MITM resistance, replay
resistance, downgrade resistance, production security, or operational
robustness. The tests pass while the replay attack succeeds and while
single malformed messages crash components — this distinction must be
preserved in all documentation.

---

# Suggested Student Evaluation Record

The students must make all final decisions. This table suggests the
documentation entries; nothing below has been decided by the AI.

| Finding | AI-generated recommendation | Student evaluation required | Possible decision | Verification method | Student change | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 MITM on key establishment | Add authentication of the ML-KEM public key (signature binding, pinning, or TLS) | Threat model + mechanism choice | ACCEPTED / MODIFIED / REJECTED | Active MITM relay experiment; code review | (students fill in) | (students fill in) |
| F-02 Downgrade via capability spoofing | Authenticate capability claims; define fallback policy | Policy decisions from prompt §3 | MODIFIED expected | Spoofed-hello test (strip/forge capabilities) | | |
| F-03 Gateway crash on malformed handshake | Validate fields, raise ProtocolError; add regression test | Correctness of the fix | MODIFIED expected | Re-run demo D until gateway survives | | |
| F-04 Cloud thread crash on malformed encaps | Same fix + count errors | Whether to also close sessions on such failures | MODIFIED expected | Re-run demo C | | |
| F-05 Replay | Add freshness checks (sequence/anti-replay) after choosing approach | Mechanism choice + scope (both paths?) | MODIFIED expected | Re-run demo B → must be rejected | | |
| F-06 Shared static PSK | Per-device keys, rotation plan | Scope for prototype vs. design doc | MODIFIED or REJECTED (document-only) | Compromised-device simulation | | |
| F-07 Wedged gateway after cloud failure | Clear session state, reconnect, truthful health | Reconnection semantics | MODIFIED expected | Kill cloud mid-run experiment | | |
| F-08 Metrics issues | Fix units, define fallback_events, cover all error paths | What the baseline analysis needs | MODIFIED expected | Unit tests + /health inspection | | |
| F-09 Duplicated AEAD code | Unify | Whether divergence is actually planned | ACCEPTED or MODIFIED | Review + tests | | |
| F-10 Duplicated config | Single source of truth | Which side is authoritative | MODIFIED or REJECTED | Config drift test | | |
| F-11 Key lifecycle | Evict sessions; document retention | Policy + retention rules | MODIFIED expected | Registry inspection after disconnects | | |
| F-12 Thread/rate limits | Thread pool, caps | Needed for the demo? | REJECTED or deferred | Load test | | |
| F-13 Health semantics | Real status derivation | What "healthy" must mean | MODIFIED expected | Kill components, watch /health | | |
| F-14 Pin dependencies | Pin cryptography; CI drift check | Version policy | MODIFIED expected | CI run | | |
| F-15 Truncation error text | Separate error paths | Trivial | ACCEPTED or MODIFIED | Protocol tests | | |

Each row, once decided, must be recorded with the full chain required
by the course documentation (prompt → output → evaluation → decision
→ verification → changes → remaining risks).
