# P06 — NEW-1 Fix & Final Security Verification

> **AI-implemented corrective phase — student verification required.**
> This document was produced by an AI assistant executing
> `prompt/P06 - NEW-1 Fix and Final Security Verification.md`. P06
> fixes exactly one defect — NEW-1 from the P05 independent
> verification (`review/P05`) — and re-verifies the previously
> verified controls. The P05 report is preserved unchanged: NEW-1
> remains documented there as discovered.
>
> Environment: Windows 11 (10.0.26200), Python 3.12.0,
> cryptography 50.0.1, pytest 9.1.1, Docker **not installed**,
> not a git repository. Date: 2026-09-08.

---

## 1. Executive Summary

P05 (independent verification) verified every P04 security claim but
discovered one new robustness defect:

> **NEW-1:** an AEAD envelope whose `nonce` field is valid base64 of
> the wrong length (e.g. 8 bytes instead of 12) reached
> `ChaCha20Poly1305.decrypt()`, which raised
> `ValueError("Nonce must be 12 bytes")`. No handler catches
> `ValueError`, so the handler **thread died** with an uncontrolled
> traceback, the `errors` metric was **not incremented**, and (as
> P06 investigation showed) the TCP connection was left half-open
> until garbage collection. A remote, unauthenticated attacker could
> trigger this on three paths: gateway hello verification, gateway
> legacy-reading decryption, and cloud protected-reading decryption.

P06 fixed NEW-1 with a minimal input-validation change in
`common/crypto.py` only: the decoded nonce length is now checked
**before** the AEAD call and a wrong length raises the project's
established controlled error types (`ProtocolError` on reading
envelopes; `AuthenticationError` via the existing hello-auth
conversion).

Final verification result:

- Fail-first: 19 new regression tests written first, **18 failed**
  against the unfixed code (ValueError tracebacks, metric bypass,
  hung connections) — exactly the P05-observed defect.
- After the fix: **120/120 pytest tests pass** (101 existing + 19
  new; no test was removed or weakened).
- Independent TCP re-attack against real processes: all three
  attacker paths now produce a controlled close with **0
  tracebacks**, exactly one counter increment per event in the
  layer that owns it, and full service availability afterwards.
- Re-test of previously verified controls (F-01/F-02/F-03/F-04/
  F-05/F-06/F-07/F-08/F-13 + robustness + crypto): all unchanged.
- Scope compliance: only `common/crypto.py`, the new test file, and
  this report were changed (checksum-verified).

## 2. P05 Finding

From `review/P05 - Independent Security Verification & Re-test.md`,
section 21 (NEW-1), condensed:

> A hello (`auth_nonce`), legacy reading, or protected reading whose
> nonce field is valid base64 of the WRONG length (8 bytes instead
> of 12) reaches `ChaCha20Poly1305.decrypt()`, which raises
> `ValueError("Nonce must be 12 bytes")`. ValueError is not in any
> handler catch set, so the handler THREAD dies with an uncontrolled
> traceback and the connection closes. Observed live: gateway
> thread tracebacks ×2, cloud thread traceback ×1, `errors` metric
> delta 0 for all three, processes survived, a subsequent valid flow
> worked (thread-level impact only). Severity: LOW-MEDIUM.

P05's overall verdict was PARTIAL PASS because of this defect and
the unverifiable Docker/CI dimensions.

## 3. Root Cause

Two code paths in `common/crypto.py` consumed attacker-controlled
nonce data without validating its length before the AEAD library
call:

1. `_aead_decrypt()` (used by both `decrypt_legacy_payload` and
   `decrypt_session_payload`): after base64 decoding, the nonce was
   passed straight to `ChaCha20Poly1305.decrypt()`. The
   `cryptography` library raises `ValueError("Nonce must be 12
   bytes")` for any non-12-byte nonce. The surrounding `try` only
   catches `InvalidTag` (and parsing errors), so `ValueError`
   escaped `_aead_decrypt`, escaped the drop-and-continue handlers
   (`gateway._serve_legacy` catches `ProcessingError` /
   `LegacyDecryptionError`; `cloud._receive_readings` catches
   `ProcessingError` / `CryptoError`), escaped the connection
   handlers (`_handle` catches `ProtocolError` / `ProcessingError` /
   `CryptoError` / `OSError`), and terminated the handler thread.
2. `verify_hello_auth()` (hello tag): same defect class — a
   wrong-length `auth_nonce` raised `ValueError` inside the AEAD
   call; `evaluate_hello` catches only `AuthenticationError`, so the
   gateway handler thread died the same way.

Consequence chain (all empirically confirmed in P05 and in the P06
fail-first run): attacker input → unhandled `ValueError` →
uncontrolled traceback → handler-thread termination → `errors`
metric bypassed. A P06 investigation additionally showed that when
the crashed thread's traceback is retained (which pytest does, and
which CPython's traceback cycle can do transiently in production),
the server-side socket's `makefile` reference keeps the TCP
connection half-open: the connection is not closed until the frame
is garbage-collected. This made the fail-first tests hang waiting
for EOF — the defect's practical impact is slightly worse than
"thread dies": the connection can linger until GC.

Classification per P06 section 6: the nonce is **malformed
attacker-controlled input**, not an unexpected programming failure —
so the fix is input validation at the protocol boundary, not a
broad `except Exception`.

## 4. Fail-First Evidence

New tests (`tests/test_nonce_validation.py`, 19 tests) were written
and run **before** the fix (baseline: `pytest -q` → 101 passed):

```text
$ pytest tests/test_nonce_validation.py -q
18 failed, 1 passed in 25.52s
```

Representative failures against the unfixed code:

- Unit level: `ValueError: Nonce must be 12 bytes` raised at
  `common/crypto.py:97` (`_aead_decrypt`) for nonce lengths
  0/1/8/11/13/64 — the test expected a controlled `ProtocolError`.
- Gateway integration (real TCP, real handler thread):
  `Exception in thread Thread-3 (_handle) ... ValueError: Nonce must
  be 12 bytes` at `common/crypto.py:155` (`verify_hello_auth`);
  `errors` counter delta 0 (metric bypass).
- Cloud integration: same class; the connection was never closed
  (test timed out waiting for EOF) — see the root-cause note above.

The single passing test was `test_valid_12_byte_nonce_still_works`
(unchanged valid behavior). The fail-first run demonstrates the
defect on every affected path; the failure list is preserved in
this report rather than in the test suite (the tests now pass).

## 5. Implementation

Minimal change, `common/crypto.py` only (diff summary):

1. `_aead_decrypt()` — after decoding, before the AEAD call:

```python
    if len(nonce) != NONCE_LENGTH:
        raise protocol.ProtocolError(
            f"invalid nonce length ({len(nonce)})")
```

`ProtocolError` is the project's established "malformed wire input"
type (P06 section 8 preference). On both reading paths it is caught
by the connection handlers (`gateway._handle` /
`cloud._handle`), which log a controlled close line and increment
`errors` exactly once — the same treatment an invalid-base64 nonce
field already received. Only the length is logged, never the nonce
bytes.

2. `verify_hello_auth()` — same validation inside the existing
auth-field parsing block, so the existing conversion maps it to
`AuthenticationError("malformed hello auth fields")`, which routes
to the established hello-rejection path
(`REJECT_UNAUTHENTICATED` + `messages_rejected` — the counter every
other hello rejection uses):

```python
        if len(nonce) != NONCE_LENGTH:
            raise protocol.ProtocolError("invalid nonce length")
```

No new exception classes; no `except Exception`; no algorithm
change; valid nonce generation (`os.urandom(12)`) untouched.

Error-metric design note (P06 section 9): the architecture counts
malformed messages at different layers by design. Reading-envelope
violations that are connection-fatal (like this one and like
invalid base64) count under `errors`; hello rejections count under
`messages_rejected`. Each event increments exactly one counter,
exactly once — verified in sections 7–9. No double counting was
introduced.

## 6. Regression Tests

New file `tests/test_nonce_validation.py` (19 tests, none of the
101 existing tests modified or removed):

- Unit (14): wrong nonce lengths 0/1/8/11/13/64 rejected with
  `ProtocolError` for both AEAD wrappers (12 cases);
  wrong-length `auth_nonce` rejected with `AuthenticationError`;
  valid 12-byte nonce round trips (legacy + session + hello).
- Gateway integration (4, real TCP through `DeviceServer`'s actual
  handler thread): wrong nonce lengths 8/11/13 in a legacy reading
  → exactly one `errors` increment, reading never forwarded,
  no traceback, service still available (fresh valid flow
  forwarded); wrong-length `auth_nonce` in a hello → connection
  closed, exactly one `messages_rejected` increment, no traceback.
- Cloud integration (1, real TCP through `CloudServer`'s actual
  handler thread incl. a real ML-KEM handshake): 8-byte nonce in a
  protected reading → exactly one `errors` increment, reading not
  stored, no traceback, session evicted (registry count 0), and a
  brand-new valid session stores a reading afterwards (service
  availability).

Test-environment note: the integration tests assert rejection via
metric/forward/store/availability; the eventual TCP close is
asserted in the live TCP attack against real processes (section
10), because pytest's traceback retention defers the OS-level
socket close in-process (documented in the test file).

## 7. Gateway Verification

Unit + real-TCP gateway integration (section 6) plus live-process
attack (section 10). Summary:

| Nonce length | Result |
| --- | --- |
| 12 bytes (valid) | accepted, reading forwarded (normal behavior) |
| 8 bytes | REJECT, `ProtocolError` → controlled close, errors +1 |
| 11 bytes | REJECT, controlled close, errors +1 |
| 13 bytes | REJECT, controlled close, errors +1 |
| hello `auth_nonce` 8 bytes | REJECT (`REJECT_UNAUTHENTICATED`), messages_rejected +1 |

Gateway process alive in every case; no tracebacks.

## 8. Cloud Verification

Real-TCP cloud integration + live-process attack (section 10):

- 8-byte nonce in a protected reading → controlled rejection
  (`closing gateway connection ... invalid nonce length (8)`),
  errors +1, no traceback, session evicted, cloud process alive.
- A subsequent valid ML-KEM handshake and reading worked
  immediately afterwards.

## 9. Metrics Verification

Live-process attack (before → after):

| Event | Counter | Delta |
| --- | --- | --- |
| gateway hello, 8-byte nonce | `messages_rejected` | +1 |
| gateway reading, 8-byte nonce | `errors` | +1 |
| cloud protected reading, 8-byte nonce | `errors` | +1 |

Exactly one increment per event, in the layer that owns the
rejection (section 5 design note). Pre-fix, all three deltas were 0.

## 10. Independent TCP Attack

Re-ran the P05 external harness's nonce probe against the fixed code
(real subprocesses, non-default ports, temp state, independently
constructed messages):

```text
gateway <- hello with 8-byte nonce:            closed = True
gateway <- reading with 8-byte nonce:          closed = True
cloud   <- protected reading with 8-byte nonce: closed = True
tracebacks in gateway log: 0
tracebacks in cloud log: 0
gateway alive: True | cloud alive: True
gateway errors delta: 1
gateway messages_rejected delta: 1
cloud errors delta: 1
controlled close lines (gateway): 1   (cloud): 1
invalid nonce length logged (gateway): 1  (cloud): 1
valid flow still works after probes: True
```

Pre-fix, the same probe produced 3 tracebacks and 0 metric
increments (P05 section 21). The full malformed-input robustness
battery was also re-run: 0 tracebacks anywhere, both services alive
and serving a valid end-to-end flow afterwards.

## 11. Regression Suite

```text
$ pytest -q
120 passed in 3.04s
```

(101 existing tests, unchanged, + 19 new NEW-1 regression tests.
Re-run after all live attacks: still 120 passed in 3.04s. No test
deleted, no assertion weakened.)

## 12. Previously Verified Controls

Because `common/crypto.py` is shared by every security path, the
previously verified controls were re-tested live (external harness,
real processes) after the fix:

| Control | Re-test result |
| --- | --- |
| F-01 key substitution | substituted valid key rejected 6/6 attempts (`fingerprint mismatch`), no session, no encaps, gateway alive |
| F-02 downgrade | all 8 manipulation variants rejected; exactly 1 fallback for 1 valid legacy hello; `messages_rejected` +5, `fallback_activations` +1 |
| F-03 malformed handshake | 10 malformed handshakes (8 classes) → controlled ProtocolErrors, gateway alive, 0 tracebacks |
| F-04 malformed encaps | 5 variants → controlled close, 0 tracebacks, errors +5, service available after |
| F-05 replay | exact replay rejected (both hops), exactly one copy stored; tampered seq/device_id/session_id/AAD/ciphertext all rejected; jump-window limitation still as documented |
| F-06 per-device keys | all 6 accept/reject probes as expected; 2 fallbacks, 4 rejections counted |
| F-07 cloud failure | degraded after failed forward → auto reconnect with NEW session id → forwarding resumed; cloud evicts dead sessions |
| F-08 metrics | counter deltas and units (`bytes`/`s`) unchanged from P05 |
| F-13 health | ok → degraded/connecting → ok transitions unchanged |
| Robustness battery | 0 tracebacks; both services alive and serving after |
| Crypto integration | **19/19 checks pass** (P05 had 18/19 — the failing check is now the passing NEW-1 check) |

No previously verified property was affected by the change.

## 13. NEW-2 / NEW-3

```text
NEW-2 (gateway /health does not exist during the initial
establishment retry loop):
Not fixed.

Reason:
Outside mandatory P06 scope and not required to resolve the
security defect NEW-1. Kept as a documented operational
limitation (P05 section 21 / P06 section 19).

NEW-3 (no independent cloud keepalive/heartbeat):
Not fixed - kept by design.

No independent keepalive/heartbeat mechanism is implemented.
A dead cloud connection is detected when the next forwarding
operation fails. This is an accepted operational limitation for
the educational prototype (P06 section 20). No heartbeat
infrastructure was added.
```

## 14. Remaining Risks

Unchanged from P05 (each re-checked), plus NEW-1 resolved:

1. No TLS — metadata exposure; tampering detected only where
   tags/pins apply (Accepted limitation).
2. Cloud does not authenticate gateways (Deferred).
3. Static demo keys; no rotation/revocation/expiry (Accepted).
4. Gateway/cloud restart loses replay state until devices re-send
   (Accepted, P03).
5. No sequence jump window (Accepted, demonstrated).
6. Hello replay re-triggers fallback activation (Accepted).
7. Device has no reconnect logic (Deferred).
8. No rate limiting / thread caps (Accepted at demo scale).
9. No key zeroization (Python limitation).
10. Simulated provisioning; manual pin provisioning (Accepted).
11. Docker compose never executed (Docker unavailable).
12. CI never executed (not a git repository).
13. NEW-2 — /health absent during initial retry loop (documented
    limitation, not fixed in P06).
14. NEW-3 — no keepalive; dead-cloud detection is
    send-failure-driven (documented limitation, not fixed in P06).

## 15. Files Modified

- `common/crypto.py` — NEW-1 fix: nonce-length validation in
  `_aead_decrypt` and `verify_hello_auth` (the only production file
  changed).
- `tests/test_nonce_validation.py` — NEW (19 regression tests).
- `review/P06 - NEW-1 Fix & Final Security Verification.md` — NEW
  (this report).
- Regenerated bytecode: `common/__pycache__/crypto.*.pyc`,
  `tests/__pycache__/test_nonce_validation.*.pyc` (build artifacts).

Scope compliance (P06 section 21): checksum comparison of the whole
tree before vs. after shows exactly the files above and nothing
else. `gateway/`, `cloud/`, `device/`, `common/protocol.py`,
`common/metrics.py`, Docker files, CI files, README, and the P05
report are all byte-identical to the P05 end state. No unrelated
cleanup was performed; NEW-2 and NEW-3 were not touched.

## 16. Final Security Verdict

```text
PASS with documented residual risks

All security controls selected in P03 and implemented in P04 were
independently verified in P05, and the additional NEW-1 robustness
defect discovered during P05 was fixed and independently re-tested
in P06. The project retains documented limitations that are
outside the scope of this educational prototype.

This is NOT a claim of production security and NOT a claim that
all security vulnerabilities are eliminated.
```

---

## Before/After Table (P06 section 23)

| Test | P05 behavior | P06 expected behavior | P06 result |
| --- | --- | --- | --- |
| 12-byte nonce | valid | ACCEPT | ACCEPT (round trips; live flow forwarded) |
| 8-byte nonce | traceback | controlled REJECT | REJECT, `ProtocolError`, controlled close, errors +1 |
| 11-byte nonce | traceback/error | controlled REJECT | REJECT, controlled close, errors +1 |
| 13-byte nonce | traceback/error | controlled REJECT | REJECT, controlled close, errors +1 |
| gateway invalid nonce | handler failure | handler survives | handler survives; process alive; 0 tracebacks |
| cloud invalid nonce | handler failure | handler survives | handler survives; process alive; 0 tracebacks |
| error metric | not counted | counted correctly | +1 exactly once per event in the owning layer (hello path: `messages_rejected` +1 — documented design note, section 5) |

## Final Verification Matrix (P06 section 25)

| Finding | Status after P06 | Evidence |
| --- | --- | --- |
| F-01 | PASS | live key-substitution re-test: 6/6 rejections, no session, no encaps |
| F-02 | PASS | live downgrade re-test: all variants rejected, counters exact |
| F-03 | PASS | live malformed-handshake re-test: 10 attacks, gateway alive, 0 tracebacks |
| F-04 | PASS | live malformed-encaps re-test: 5 variants, cloud alive, errors +5 |
| F-05 | PASS | live replay re-test: both hops reject, one copy stored, AAD binding holds |
| F-06 | PASS | live key-isolation re-test: 6/6 probes as expected |
| F-07 | PASS | live failure/reconnect re-test: degraded → new session → resumed → eviction |
| F-08 | PASS | live metric deltas and units unchanged and correct |
| F-13 | PASS | live health transitions unchanged and truthful |
| NEW-1 | **FIXED** | fail-first 18 failures → fix → 19/19 new tests, 120/120 suite, independent TCP attack: 0 tracebacks, correct counters |
| NEW-2 | Deferred | documented (section 13) |
| NEW-3 | Accepted limitation | documented (section 13) |

---

## Final Output

- **Implementation:** nonce-length validation before the AEAD call
  in `common/crypto.py` (`_aead_decrypt` → `ProtocolError`;
  `verify_hello_auth` → `AuthenticationError` via existing
  conversion). No algorithm change, no new exception classes, no
  broad catches.
- **Files modified:** `common/crypto.py`; created
  `tests/test_nonce_validation.py` and this report (plus
  bytecode artifacts). Nothing else (checksum-verified).
- **Tests:** `pytest -q` → **120 passed, 0 failed, 0 skipped**
  (baseline 101; +19 NEW-1 regression tests; no test removed or
  weakened; re-run after live attacks with the same result).
- **Fail-first:** 18 of the 19 new tests failed against the
  unfixed code (`ValueError: Nonce must be 12 bytes`, thread
  tracebacks, `errors` delta 0, hung connections) — the exact P05
  defect, recorded before the fix.
- **NEW-1 attack (independent, real processes):** all three paths
  controlled-closed, 0 tracebacks, `errors` +1 (reading paths) /
  `messages_rejected` +1 (hello path), services alive, valid flow
  succeeds immediately after.
- **Previous security controls:** F-01/F-02/F-03/F-04/F-05/F-06/
  F-07/F-08/F-13 + robustness battery + crypto checks (19/19) all
  re-tested live and unchanged.
- **Docker:** NOT VERIFIED — Docker unavailable on this machine.
- **CI:** NOT VERIFIED — CI environment unavailable (not a git
  repository).
- **Remaining risks:** section 14 (NEW-1 resolved; NEW-2 deferred;
  NEW-3 accepted; the P03/P04 accepted limitations unchanged).
- **Final verdict:** **PASS with documented residual risks**
  (section 16; NOT production security).
- **P06 scope compliance:** confirmed — no unrelated code was
  modified; NEW-2 and NEW-3 were left untouched and documented.
