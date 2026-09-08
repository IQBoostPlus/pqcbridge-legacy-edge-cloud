# P04 — Security Implementation & Verification

> **AI-implemented phase — student verification required.** This
> document was produced by an AI assistant executing the P03-approved
> design (`prompt/P04`, `review/P03`). Every claim below is backed by
> a recorded test run or live demonstration; where a claim could not
> be verified, that is stated explicitly. Nothing here means the
> project is production-secure.
>
> Environment: Windows 11 (10.0.26200), Python 3.12.0,
> cryptography 50.0.1, pytest 9.1.1, Docker **not installed**,
> not a git repository.

---

## 1. Implementation Summary

P04 implemented every approved P03 decision, in the P04-prescribed
order, with fail-first tests written before the fixes:

1. **P04.1 (F-14):** pinned `cryptography==50.0.1`, `pytest==9.1.1`;
   verified the ML-KEM seed round trip (`private_bytes_raw()` /
   `from_seed_bytes()`) needed for cloud key persistence.
2. **P04.2 (F-03/F-04/F-15):** uniform handshake field validation
   (`protocol.require_str`/`require_int`, `parse_mlkem_pubkey_reply`,
   `parse_mlkem_request`, `parse_mlkem_encaps`,
   `parse_mlkem_established_reply`, length checks 1184/1088 bytes);
   split oversized vs. truncated messages in `read_message`.
3. **P04.3 (F-09):** single `_aead_encrypt`/`_aead_decrypt` core with
   AAD support; four thin public wrappers (behavior unchanged for old
   callers).
4. **P04.4 (F-08):** observations carry units (`s`/`bytes`), snapshot
   reports avg/min/max + unit; `forward_ms`→`forward_s`,
   `fallback_events`→`fallback_activations`, new `messages_rejected`;
   errors counted on every failure path incl. handshake retries.
5. **P04.5 (F-06/F-10):** per-device key registry
   (`DEVICE_KEYS_JSON`/`DEVICE_KEY_HEX`), unknown device ids rejected;
   config policy documented in both `common/config.py` and
   `docker-compose.yml`.
6. **P04.6 (F-02):** AEAD-tagged hellos (`build_hello`/
   `verify_hello_auth`) + the P03 §8 fallback decision table in
   `evaluate_hello`.
7. **P04.7 (F-05):** monotonic per-device sequences bound into the
   AEAD AAD (`legacy_message_aad`, `session_message_aad`),
   `ReplayGuard` at gateway and cloud, device counter persisted to
   `device_state/<id>.seq` (compose volume).
8. **P04.8 (F-01):** SHA-256 fingerprint pinning
   (`verify_cloud_public_key`, fail-closed when unconfigured); the
   cloud persists its ML-KEM keypair (`cloud_state/cloud.key`) and
   prints its fingerprint at startup so the pin survives restarts.
9. **P04.9 (F-07/F-13/F-11):** `CloudChannel` state machine
   (DISCONNECTED→CONNECTING→ESTABLISHING→ESTABLISHED→FAILED), new
   session id per attempt, send-failure invalidation + background
   reconnect, cloud session eviction on disconnect, health reports
   `status` + `cloud_state`.
10. **P04.10:** full regression (101 tests), attack re-tests, live
    integration and failure demos (section 8).
11. **P04.11:** README, compose, .gitignore updates.

## 2. P03 Decision Mapping

| P03 Decision | Implementation | Files | Status |
| --- | --- | --- | --- |
| F-01 fingerprint pinning (reject TLS/signatures) | `verify_cloud_public_key` (secrets.compare_digest), `CLOUD_PUBLIC_KEY_SHA256`, cloud prints fingerprint | gateway/processing.py, gateway/cloud_channel.py, common/config.py, cloud/cloud.py | ✅ implemented + tested + attack re-tested |
| F-02 authenticated hello + §8 policy table | `build_hello`/`verify_hello_auth`, `evaluate_hello` decision constants | common/crypto.py, gateway/processing.py, gateway/gateway.py, device/device.py | ✅ implemented + tested + attack re-tested |
| F-03/F-04 uniform handshake validation | require_str/require_int, parse helpers, length checks | common/protocol.py, gateway/processing.py, cloud/processing.py | ✅ implemented + tested + attack re-tested |
| F-05 monotonic seq + AAD + device persistence | ReplayGuard, AAD helpers, device/state.py | common/replay.py, common/protocol.py, device/state.py, device/device.py, gateway/gateway.py, cloud/cloud.py | ✅ implemented + tested + attack re-tested |
| F-06 per-device key registry | DEVICE_KEYS_JSON/DEVICE_KEY_HEX, unknown-id rejection | common/config.py, gateway/gateway.py, device/device.py | ✅ implemented + tested |
| F-07 5-state lifecycle + reconnect + eviction | State enum, _invalidate/_start_reconnect, registry.remove | gateway/cloud_channel.py, cloud/cloud.py | ✅ implemented + tested + live demo |
| F-08 metric table with units | Metrics.observe(unit), renames, messages_rejected | common/metrics.py, gateway/*, cloud/* | ✅ implemented + tested |
| F-09 minimal AEAD core refactor | _aead_encrypt/_aead_decrypt + wrappers | common/crypto.py | ✅ implemented (old tests unchanged) |
| F-10 config policy (documentation) | cross-referencing comments | common/config.py, docker-compose.yml, README | ✅ implemented (docs only) |
| F-11 eviction now, rest deferred | registry.remove + README key-lifecycle statement | cloud/cloud.py, README | ✅ eviction implemented; rotation/zeroization deferred |
| F-12 deferred | — | — | ✅ deferred as decided (README limitation #8) |
| F-13 health status model | status override + cloud_state | common/health.py (already supported), gateway/gateway.py, cloud/cloud.py | ✅ implemented + live demo |
| F-14 pin dependencies | cryptography==50.0.1, pytest==9.1.1 | requirements.txt | ✅ implemented + verified |
| F-15 split truncated/oversized | read_message branches + "mid-message" error | common/protocol.py | ✅ implemented + tested |

## 3. Fail-First Evidence

All baseline failures were reproduced in P04 **before** the fixes were
implemented (recorded 2026-09-07 ~22:01–22:02; preserved in the
session logs and `review/P02` appendix).

| Finding | Baseline behavior | Test | Initial result |
| --- | --- | --- | --- |
| F-03 | malformed handshake → gateway process crash | fake cloud sends `mlkem_pubkey` without `public_key` (P02 demo D re-run) | **CONFIRMED: `KeyError: 'public_key'`, gateway exit code 1** |
| F-04 | malformed encapsulation → handler thread failure | client sends `mlkem_encaps` without `ciphertext` (P02 demo C re-run) | **CONFIRMED: raw `KeyError` traceback in cloud thread** |
| F-05 | valid message → ACCEPT; same captured message → ACCEPT | P02 replay demo re-run | **CONFIRMED: duplicate 99.9 °C reading stored twice** |
| F-01 | different ML-KEM public key → accepted | code inspection (no verification step existed) | accepted by construction; no live MITM relay needed |
| F-02 | capability manipulation → possible fallback manipulation | code inspection (plaintext hello) | no authentication of claims |
| All | new fail-first test suite (82 tests) run against the baseline | `pytest --continue-on-collection-errors` | **53 failed, 29 passed, 2 collection errors** (missing `common.replay`, `State`; new APIs absent; assertions on new behavior failing) |

## 4. Implementation Details

### 4.1 Handshake validation (F-03/F-04/F-15)
- `protocol.require_str/require_int` raise `ProtocolError` for
  missing/ill-typed fields — every handshake message is validated
  through these helpers (never `msg["field"]`).
- Length checks: ML-KEM-768 public key 1184 bytes, ciphertext 1088
  bytes (`MLKEM768_PUBLIC_KEY_BYTES`, `MLKEM768_CIPHERTEXT_BYTES`,
  verified against cryptography 50.0.1).
- Behavior: malformed handshake → `ProtocolError` → gateway logs +
  counts + retries; cloud logs + counts + closes the connection.
  No `except Exception` catch-alls were added — programming errors
  still surface.
- `read_message` now reports "connection closed mid-message" for
  truncated input, distinct from "exceeds maximum allowed size".

### 4.2 AEAD with AAD (F-09/F-05)
- One core pair `_aead_encrypt/_aead_decrypt(key, data, aad,
  error_cls)`; the four public wrappers are one-liners (old call
  signatures still work — AAD optional).
- Bindings (exactly the P03-selected fields):
  - legacy readings: `aad = device_id || ":" || seq`
  - protected readings: `aad = session_id` (channel binding)
  - hellos: claims serialized canonically as AAD of an empty-message
    AEAD (MAC-only use)
- Tests prove: correct AAD decrypts; modified AAD / ciphertext /
  nonce all fail.

### 4.3 Hello authentication + fallback policy (F-02/F-06)
- `build_hello` (device) / `verify_hello_auth` (gateway) authenticate
  device_id + capabilities under the device's own key.
- `evaluate_hello(hello, device_key)` implements the P03 §8 table
  (see README section 1): `ALLOW_FALLBACK` only for known devices
  with a valid tag and legacy-only claims; `REJECT_UNKNOWN_DEVICE`,
  `REJECT_UNAUTHENTICATED`, `REJECT_MODERN`, `REJECT_AMBIGUOUS`,
  `REJECT_NO_CAPABILITIES` otherwise.
- The gateway looks the device up in the registry BEFORE verifying
  the tag; unknown ids are rejected without a key.

### 4.4 Replay protection (F-05)
- `ReplayGuard.check_and_update(device_id, seq)`: accepts
  `seq > last_seen`, otherwise rejects (thread-safe, per device).
- Enforced at the gateway (legacy path) and the cloud (protected
  path, defense in depth). State is in-memory per process —
  the accepted P03 limitation.
- The device persists its counter after every send
  (`device/state.py`); compose mounts `device_state:/app/device_state`.

### 4.5 Cloud key pinning (F-01)
- `verify_cloud_public_key(raw, expected)`: fails closed when
  `CLOUD_PUBLIC_KEY_SHA256` is empty; `secrets.compare_digest` on
  the SHA-256 fingerprint; runs BEFORE encapsulation.
- The cloud persists its keypair (`cloud_state/cloud.key`) and prints
  the fingerprint at every startup. **Deviation note (transparency,
  P04 §24):** P03 said "keypair per cloud process run"; persistence
  across restarts was required to make the approved pinning design
  operable — otherwise every cloud restart would invalidate the pin
  and break the F-07 reconnect demo. Documented, not silent.
- Pin provisioning remains manual (copy fingerprint into env) —
  the educational trust-anchor story.

### 4.6 Session lifecycle (F-07/F-13/F-11)
- `State` enum mirrors the P03 diagram. `connect_and_establish`
  retries with per-attempt session ids; `send_reading` failures call
  `_invalidate()` (clear socket+key, state=FAILED) and start a
  background reconnect (`auto_reconnect` flag allows tests to
  disable it).
- Health: `status: ok|degraded`, `cloud_connected`, `cloud_state`,
  session id (safe identifier only — never keys).
- Cloud: `registry.remove(session_id)` in `_handle`'s `finally`
  (eviction on disconnect).

### 4.7 Metrics (F-08)
- `observe(name, value, unit)`; snapshot aggregates carry `unit`.
- Semantics per P03 table: `messages_received/processed/forwarded/
  rejected`, `errors` (every failure path incl. handshake retries),
  `fallback_activations` (per authenticated hello), distinct
  `legacy_devices_detected`, `mlkem_sessions_established`,
  `mlkem_establish_s`, `mlkem_decapsulate_s`, `forward_s`,
  `payload_bytes` (bytes).

## 5. Security Tests

New/updated tests (final suite: **101 tests**, baseline was 39):

- `tests/test_handshake.py` (12) — missing fields, wrong types, bad
  base64, wrong lengths, valid round trips for all handshake
  messages.
- `tests/test_aad.py` (5) — correct/modified AAD, modified
  ciphertext/nonce, session-id channel binding.
- `tests/test_hello_policy.py` (9) — all eight P04 §10 cases plus
  impersonation.
- `tests/test_replay.py` (12) — guard semantics (duplicate/stale/
  next/independent devices), AAD sequence binding, seq required,
  tampered seq, counter persistence (round trip, missing, corrupt).
- `tests/test_pinning.py` (5) — expected key accepted, different key
  rejected, missing pin fails closed, changed fingerprint rejected,
  fingerprint format.
- `tests/test_session.py` (7) — establishment success, initial
  state, malformed handshake survival (F-03 regression), pin
  mismatch rejection, failed send invalidation, new session id per
  attempt (uses a scriptable fake cloud over real TCP).
- `tests/test_device_keys.py` (5) — registry mapping, default
  device key, unknown device, env overrides.
- `tests/test_processing.py` (updated) — hello parsing incl. auth
  fields, parse→evaluate chain regression, `determine_path` "both"
  case, seq/AAD/session-id updates.
- `tests/test_protocol.py` (updated) — truncated-message error,
  reading sequence required.
- `tests/test_metrics.py` (updated) — units, size observations.
- Unchanged: `test_sensor.py`, `test_crypto.py` (AEAD wrappers
  backward compatible).

## 6. Regression Tests

```text
$ pytest
101 passed in 0.53s
```

Repeated after every major step (P04.1: 39 passed on pinned deps;
post-implementation: 100 passed; after the live-integration fix +
regression test: 101 passed). No test was deleted to obtain a green
run; three test-harness bugs found during implementation were fixed
in the tests themselves (documented in section 13) and two tests
were intentionally updated for the P03-approved design change
(`determine_path` "both"; readings require `sequence`) — both
documented in `review/P03` and in the test files.

## 7. Integration Tests

Live end-to-end (device → gateway → cloud), P04 session:

```text
ML-KEM-768 establishment with pinned fingerprint        OK (session ad0467983dfceaf3)
authenticated hello → FALLBACK ACTIVATED                OK (dev-01)
encrypted readings seq 1..9 stored in the cloud         OK
health endpoints (gateway ok/established, cloud ok)     OK
metrics: forward_s avg 0.000112 s, payload_bytes 121 B (unit "bytes")
        mlkem_establish_s avg 0.008651 s
device restart with persisted counter                  OK (resumed at 106 after
                                                        an earlier crash; clean run
                                                        started at 1)
```

Cloud-failure sequence (P04 §17):

```text
established session
  → cloud killed
  → gateway detects send failure (session ... FAILED; will reconnect)
  → /health: status degraded, cloud_connected false, cloud_state connecting
  → cloud restarted (persisted keypair → same fingerprint → pin valid)
  → automatic reconnect with a NEW session id (b7967f9beb95717b)
  → /health: ok / established
  → readings resume after device restart
```

## 8. Security Attack Re-tests

| Attack | Expected per P03/P04 | Observed result |
| --- | --- | --- |
| Malformed handshake (`mlkem_pubkey` missing `public_key`) | controlled rejection, gateway stays alive | `cloud session attempt 1 failed (message missing required string field 'public_key')`; gateway kept retrying, health degraded, process alive ✅ |
| Malformed encapsulation (`mlkem_encaps` missing `ciphertext`) | controlled protocol error, service continues | `closing gateway connection ... message missing required string field 'ciphertext'` — no traceback ✅ |
| Replay (same captured message twice) | second transmission REJECTED | first stored, second → `REPLAY REJECTED for dev-01: sequence 100 is not newer...`; exactly ONE 42.0 °C reading in the cloud ✅ |
| Key substitution (evil cloud with different keypair) | handshake rejected | `cloud public key fingerprint mismatch - possible key substitution` (attempts 8–10), gateway alive ✅ |
| Downgrade (capabilities modified after tagging / unknown device / garbage tag) | rejected | `rejecting device dev-01: hello authentication FAILED (tampered claims or wrong key)` + `rejecting UNKNOWN device dev-999`; counted in messages_rejected ✅ |
| Session failure (cloud killed after establishment) | session no longer healthy | `status: degraded`, `cloud_connected: false`, `cloud_state: connecting`; recovery with new session id ✅ |

**Observed known-limitation behavior (honest evidence):** the replay
attack script used sequence 100; the running device (seq 64–67) was
subsequently rejected until its counter passed 101. This is the
accepted P03 "no jump window" limitation (README limitation #5),
now demonstrated live.

## 9. Metrics

Corrected semantics implemented; example values from the clean smoke
run:

```json
"counters": {"mlkem_sessions_established": 1, "device_connections": 1,
             "fallback_activations": 1, "legacy_devices_detected": 1,
             "messages_received": 9, "messages_processed": 9,
             "messages_forwarded": 9}
"timings": {"mlkem_establish_s": {"avg": 0.008651, "unit": "s"},
            "forward_s":         {"avg": 0.000112, "unit": "s"},
            "payload_bytes":     {"avg": 121.0,    "unit": "bytes"}}
```

During the attack re-tests the counters behaved as designed:
`messages_rejected` grew for every rejected hello/replay,
`fallback_activations` counted only authenticated hellos,
`errors` counted handshake retries.

## 10. Remaining Risks

**This is NOT complete security.** The unresolved risks (all
documented in README section 7 with status/deferred/reason):

1. No TLS — metadata exposure; tampering of unprotected fields is
   possible (detected only where tags/pins apply).
2. Cloud does not authenticate gateways.
3. Static demo keys; no rotation/revocation/session expiry.
4. Gateway/cloud restart amnesia for replay state (accepted P03
   limitation).
5. No sequence jump window (demonstrated live).
6. Hello replay re-triggers fallback activation.
7. Device has no reconnect logic.
8. No rate limiting / thread caps.
9. No key zeroization (Python limitation).
10. Simulated provisioning (env/config), manual pin provisioning.
11. Docker compose never executed (Docker unavailable).
12. CI never executed (not a git repository).

## 11. Deferred Findings

- **F-12** (threads/timeouts/rate limiting) — deferred per P03 with
  scale justification.
- **F-11 remainder** (key rotation, zeroization, session expiry
  timers) — deferred; eviction implemented.
- **F-08 remainder** (device-side metrics) — deferred; device logs
  suffice at demo scale.
- Device reconnect logic — deferred (adjacent to F-07).

## 12. Docker / CI Status

- **Docker: Not verified — Docker unavailable** on the development
  machine. The compose file was updated per P03 decisions (named
  volumes for cloud key + device state, per-device key env vars,
  `${CLOUD_PUBLIC_KEY_SHA256}` pin provisioning via `.env`) and is
  inspection-reviewed only. P04 §20 requires: do not claim Docker
  works without running it.
- **CI: Not executed.** The directory is not a git repository; the
  workflow file was inspected only (`python: "3.12"`, pip install,
  pytest — will fail on test failure by construction). Recorded as
  "CI execution not verified."

## 13. P04 Student/AI Development Record

For every major implementation (students must complete the review
column with their own verification):

| # | P03 decision → AI implementation → tests → verification → remaining risk | Student review |
| --- | --- | --- |
| 1 | F-01 pinning → `verify_cloud_public_key` + cloud key persistence → test_pinning (5) → unit + substitution attack rejected ✅ → pin provisioning is manual (trust anchor story) | pending |
| 2 | F-02 authenticated hello + policy → build/verify hello + evaluate_hello → test_hello_policy (9) + test_processing updates → downgrade attack rejected ✅ → hello replay still possible (benign) | pending |
| 3 | F-03/F-04 validation → require_* helpers + parse helpers → test_handshake (12) + test_session regression → both attacks now controlled errors, gateway alive ✅ → flood = retry-loop spam (no rate limit, F-12 deferred) | pending |
| 4 | F-05 replay → seq + AAD + ReplayGuard + device persistence → test_replay (12) + test_aad (5) → replay rejected, counter persistence live ✅ → jump-window + restart amnesia (accepted) | pending |
| 5 | F-06 per-device keys → registry + local_device_key → test_device_keys (5) → unknown device rejected live ✅ → static keys, simulated provisioning | pending |
| 6 | F-07 lifecycle → State machine + reconnect + eviction → test_session (7) → kill-cloud demo: degraded → reconnect → new session id ✅ → no session expiry timers | pending |
| 7 | F-08 metrics → unit-aware observe + renames → test_metrics (updated) → live /health shows correct units ✅ → device metrics deferred | pending |
| 8 | F-09 AEAD core → single core + wrappers → old crypto tests unchanged + new AAD tests ✅ | pending |
| 9 | F-14 pinning deps → requirements.txt → install + pytest on pinned versions ✅ | pending |
| 10 | F-15 error split → read_message branches → test_protocol updates ✅ | pending |

**Unexpected problems (never hidden, P04 §24):**
1. **Live-integration bug** found by the smoke test: `parse_hello`
   pruned the auth fields, so live hello verification always failed
   (unit tests missed it — they tested the functions in isolation).
   Fixed in `gateway/processing.py` + regression test
   `test_parse_then_evaluate_hello_allows_fallback` (101st test).
2. **Three test-harness bugs** fixed in the tests themselves:
   `test_device_keys` referenced a pre-refactor API name; the
   `test_pinning` tamper logic could reproduce the original
   fingerprint; `test_session` fake-cloud handlers crashed on
   expected client disconnects.
3. **Cloud key persistence** added beyond P03's literal wording —
   required by the approved pinning design (section 4.5).
4. **Windows demo tooling note:** `TaskStop` left orphaned python
   processes during the demo phase; they were cleaned with
   `taskkill` and the final verification was re-run clean. This is a
   demo-environment issue, not a project defect.

## 14. Final Verification Table

| Finding | P03 Decision | Implemented? | Baseline Tested? | Fix Tested? | Integration Tested? | Remaining Risk |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 | pinning (MODIFIED) | ✅ | ✅ (accepted by construction) | ✅ unit | ✅ substitution attack rejected | manual pin provisioning; no gateway auth |
| F-02 | authenticated hello + policy (MODIFIED) | ✅ | ✅ (plaintext claims) | ✅ unit | ✅ downgrade attack rejected | hello replay |
| F-03 | field validation (ACCEPTED) | ✅ | ✅ live crash exit 1 | ✅ unit + live | ✅ gateway survives | retry-loop flood (F-12) |
| F-04 | same policy on cloud (ACCEPTED) | ✅ | ✅ live traceback | ✅ unit + live | ✅ controlled error | — |
| F-05 | monotonic seq + AAD (MODIFIED) | ✅ | ✅ live duplicate stored | ✅ unit + live | ✅ replay rejected | jump window; restart amnesia |
| F-06 | per-device keys (MODIFIED) | ✅ | ✅ shared PSK | ✅ unit | ✅ unknown device rejected | static keys |
| F-07 | lifecycle + reconnect (ACCEPTED) | ✅ | ✅ wedged state | ✅ unit | ✅ kill-cloud demo | no expiry timers |
| F-08 | metric table (MODIFIED) | ✅ | ✅ wrong units | ✅ unit | ✅ live /health units | device metrics deferred |
| F-09 | minimal refactor (MODIFIED) | ✅ | ✅ duplication | ✅ old tests unchanged | ✅ | — |
| F-10 | docs policy (MODIFIED) | ✅ | ✅ two sources | ✅ manual review | — | comments can go stale |
| F-11 | eviction now, rest deferred (MODIFIED) | ✅ partial | ✅ no eviction | ✅ code inspection | ✅ session eviction in demos | rotation/zeroization deferred |
| F-12 | deferred | ✅ (as decided) | — | — | — | accepted at demo scale |
| F-13 | status model (MODIFIED) | ✅ | ✅ always "ok" | ✅ unit | ✅ degraded observed live | health endpoint unauthenticated |
| F-14 | pin versions (ACCEPTED) | ✅ | ✅ unpinned | ✅ install + pytest | ✅ | revisit per phase |
| F-15 | small fix (ACCEPTED) | ✅ | ✅ wrong error | ✅ unit | — | — |

---

## Final Output

**Files modified:** `requirements.txt`, `common/config.py`,
`common/protocol.py`, `common/crypto.py`, `common/metrics.py`,
`device/device.py`, `gateway/processing.py`,
`gateway/cloud_channel.py`, `gateway/gateway.py`,
`cloud/processing.py`, `cloud/cloud.py`, `tests/test_metrics.py`,
`tests/test_processing.py`, `tests/test_protocol.py`,
`docker-compose.yml`, `.gitignore`, `README.md`.

**Files created:** `common/replay.py`, `device/state.py`,
`tests/test_handshake.py`, `tests/test_aad.py`,
`tests/test_hello_policy.py`, `tests/test_replay.py`,
`tests/test_pinning.py`, `tests/test_session.py`,
`tests/test_device_keys.py`,
`review/P04 - Security Implementation & Verification.md`.

**Tests:** `pytest`: **101 passed, 0 failed, 0 skipped** (0.53 s).
Baseline before P04: 39 passed; fail-first run: 53 failed / 29
passed / 2 collection errors.

**Security demonstrations (exact results):**
- F-01: substituted key → `fingerprint mismatch` → REJECT, gateway
  alive.
- F-02: tampered/unknown/unauthenticated hellos → REJECT + metric.
- F-03: malformed pubkey reply → `ProtocolError`, gateway alive and
  retrying (baseline: exit code 1).
- F-04: malformed encaps → controlled log line, no traceback
  (baseline: raw KeyError traceback).
- F-05: replayed message → REJECTED, exactly one copy stored
  (baseline: duplicate stored).
- F-07: cloud killed → `degraded`/`connecting` → cloud restarted →
  new session id established → `ok`.

**Docker:** Not verified — Docker unavailable.

**CI:** CI execution not verified (not a git repository).

**Remaining risks:** section 10 (12 items, all documented in the
README with status and reasons).

**Unexpected problems:** section 13 (four items, none hidden).

The project remains an educational simulation; no claim of
production security is made or implied.
