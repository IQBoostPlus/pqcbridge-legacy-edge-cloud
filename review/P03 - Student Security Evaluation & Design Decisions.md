# P03 — Student Security Evaluation & Design Decisions

> **AI-generated evaluation draft — decisions proposed, NOT made.**
> This document was produced by an AI assistant from
> `prompt/P03 - Student Evaluation & Security Design.md`. Every
> "decision" below is a **proposal** prepared for the student team's
> review; the students own the final decisions and must record them
> (ACCEPTED / MODIFIED / REJECTED) per the course documentation rules.
> **No project code was modified in P03.** The only file created is
> this document.
>
> Environment: Windows 11 (10.0.26200), Python 3.12.0,
> cryptography 50.0.1, pytest 9.1.1, Docker **not installed**,
> directory is **not a git repository**.

---

## 1. Executive Summary

The P02 review produced 15 findings, of which 11 are confirmed valid as
stated, 3 are partially valid (severity or scope needs recalibration),
and 1 is valid but deliberately deferred (F-12) because the demo scale
does not justify the complexity.

The P03 proposal makes these headline choices, all sized for a student
team in one project phase:

1. **F-01:** Adopt **ML-KEM public-key fingerprint pinning** at the
   gateway (the simplest mechanism that turns key establishment into
   *authenticated* key establishment for the gateway→cloud hop). The
   P02 alternatives (TLS, signature-bound keys) are evaluated and
   **rejected for this project** — see §16.
2. **F-02 + F-06:** Replace the single shared PSK with a small
   **per-device key table**, and **authenticate the capability hello**
   with an AEAD tag under the device's own key. Combined with an
   explicit fallback decision table (§8), this closes the downgrade
   path for the prototype.
3. **F-05:** **Monotonic per-device sequence numbers**, bound into the
   AEAD as AAD, enforced at the gateway and the cloud; the device
   persists its counter so restarts do not wedge the system. Replay
   windows were considered and rejected as unnecessary complexity
   (§16).
4. **F-03/F-04:** A uniform handshake validation policy — missing
   required fields raise `ProtocolError` and are handled like every
   other protocol violation (no more process crashes).
5. **F-07:** A simple five-state session lifecycle with reconnection,
   fresh session IDs, cloud-side session eviction, and a health
   endpoint that reports the real state.

Everything else is classified P2 (quality) or P3 (deferred), with
explicit justifications. Nothing proposed requires PKI, HSMs,
TLS infrastructure, or any production-grade machinery.

**Nothing in this document claims any vulnerability is fixed.** Fixes
happen only in P04, if the students approve this design.

---

## 2. Environment and Verification Scope

| Item | Value |
| --- | --- |
| OS | Windows 11 (10.0.26200) |
| Python | 3.12.0 |
| cryptography | 50.0.1 |
| pytest | 9.1.1 |
| Docker | **not installed** — compose not verified (inspection only) |
| Git | **not a repository** — CI workflow never executed |
| Test suite | 39/39 passed (re-run during P03, 0.07 s) |

**Verification performed in P03:**
- *Tested:* full pytest suite re-run (39/39).
- *Code inspection:* every file referenced by F-01..F-15 re-inspected;
  line references below were re-confirmed against the current tree.
- *Manually reproduced (in P02, evidence retained in the P02 report
  appendix):* replay acceptance (F-05), gateway crash on missing
  `public_key` (F-03), cloud thread crash on missing `ciphertext`
  (F-04). These were **not** re-run in P03; the code has not changed
  since P02 (no modifications are allowed in P02/P03).
- *Not verified:* Docker/compose, CI execution, Linux behavior,
  concurrency behavior.

---

## 3. P02 Findings Review — Overview

| ID | Finding | Validity | Proposed decision |
| --- | --- | --- | --- |
| F-01 | Unauthenticated ML-KEM key establishment | YES | MODIFIED — fingerprint pinning |
| F-02 | Capability spoofing / downgrade | YES | MODIFIED — authenticated hello + policy table |
| F-03 | Gateway crash on malformed handshake | YES | ACCEPTED — field validation fix |
| F-04 | Cloud thread crash on malformed encaps | YES | ACCEPTED — same fix, consistent policy |
| F-05 | Replay attack | YES | MODIFIED — monotonic sequence + AAD |
| F-06 | Static shared PSK | YES | MODIFIED — per-device key table |
| F-07 | Broken session lifecycle | YES | ACCEPTED — state machine + reconnect + eviction |
| F-08 | Metrics problems | YES | MODIFIED — metric table in §F-08 block |
| F-09 | Duplicated AEAD code | PARTIALLY (harm overstated at this size) | MODIFIED — minimal wrapper refactor |
| F-10 | Configuration duplication | YES (minor) | MODIFIED — documentation-only policy |
| F-11 | Key lifecycle | PARTIALLY (zeroization unrealistic in Python) | MODIFIED — eviction now, rest deferred |
| F-12 | Threads / timeouts / rate limiting | YES but out of scale | DEFERRED — justified |
| F-13 | Health endpoint semantics | YES | MODIFIED — simple status model |
| F-14 | Dependency drift | YES | ACCEPTED — pin versions |
| F-15 | Truncated message error text | YES (minor) | ACCEPTED — small fix |

Details and justifications follow in §4.

---

## 4. F-01 through F-15 Evaluation

### F-01 — Unauthenticated ML-KEM Key Establishment

```text
AI claim:
  The gateway accepts the cloud ML-KEM public key without authentication;
  an active attacker can substitute it; ML-KEM provides key establishment
  but not peer authentication.

Technical verification:
  CORRECT. gateway/cloud_channel.py:92 consumes reply["public_key"]
  over plain TCP with no verification step. ML-KEM is an IND-CCA KEM:
  it guarantees the shared secret is hidden from passive attackers and
  from anyone without the private key, but says nothing about WHO owns
  the public key. The gateway would happily encapsulate to an
  attacker-supplied key.

Is the finding valid?  YES

Student evaluation:
  The project prompt never states a threat model. For an educational
  migration simulation, the meaningful claim to demonstrate is: "the
  gateway establishes a session with the *real* cloud, protected even
  against an active network attacker." Without any authentication the
  demonstration only holds against passive eavesdropping. P02's HIGH
  severity is appropriate for the project's central claim.

AI recommendation (P02):
  Choose among signature-bound ML-KEM, public-key pinning, or TLS.

Alternative approaches:
  (a) TLS transport - authenticates the whole channel, but wraps the
      ML-KEM handshake inside TLS and largely hides the very
      mechanism the project must demonstrate. Also adds certificate
      management (the one production concern we were told to avoid).
  (b) Signature-bound ML-KEM public key - cryptographically the
      "right" answer, but requires a signing key + verification key
      distribution, i.e. a mini-PKI; more machinery than the demo
      needs.
  (c) Public-key pinning - the gateway knows the expected cloud public
      key (or its SHA-256 fingerprint) out of band and compares it
      before encapsulating.

Selected approach:
  (c) Pinning, implemented as SHA-256 fingerprint comparison
      (64 hex chars of config instead of a 2368-char raw key).
      secrets.compare_digest(fingerprint(received_key),
      CLOUD_PUBLIC_KEY_SHA256). On mismatch: ProtocolError + error
      metric + retry (the existing retry loop already handles
      ProtocolError).

Decision:  MODIFIED (P02 suggested "choose a mechanism"; we choose
           pinning and reject the TLS/signature options for this
           project - see §16)

Reason:
  Smallest change that converts key establishment into authenticated
  key establishment for the gateway->cloud hop, keeps the ML-KEM
  exchange fully visible (educational goal), zero new infrastructure.

Implementation scope:
  - config: CLOUD_PUBLIC_KEY_SHA256 env var (printed by the cloud at
    startup as a fingerprint so students can copy it).
  - cloud_channel._establish_once: fingerprint check before
    encapsulating.
  - ~15 lines total.

Verification method:
  - Unit test: fingerprint of a valid key passes; tampered key
    rejected.
  - Live: fake cloud with a DIFFERENT keypair -> gateway logs
    "public key fingerprint mismatch", retries, never establishes.
  - Live: real cloud -> session establishes as before.

Expected result:
  An attacker substituting the cloud key during handshake is detected
  and the session is not established.

Remaining risk:
  - The pin itself is distributed via config/env (trust anchor
    provisioning is out of scope - documented).
  - The cloud still does NOT authenticate the gateway (gateway_id is
    self-declared). Documented limitation until a future phase.
  - No TLS remains: metadata (types, device ids, session ids, timing)
    stays visible to passive observers.
```

### F-02 — Capability Spoofing / Downgrade

```text
AI claim:
  Plaintext, self-declared capability claims let an attacker strip
  "ml-kem-768" (forced downgrade), forge claims, or force fallback
  resource use; the gateway cannot tell genuine legacy devices from
  spoofed ones.

Technical verification:
  CORRECT. The hello is plaintext (device/device.py send_hello);
  gateway/processing.py determine_path() trusts the list verbatim;
  a device claiming ml-kem gets closed because the modern path is
  unimplemented (self-DoS vector confirmed by inspection).

Is the finding valid?  YES

Student evaluation:
  Downgrade resistance is the point of the course topic. The baseline
  cannot distinguish "legacy device" from "modern device whose hello
  was tampered with" because hello claims are unauthenticated.

AI recommendation (P02):
  Authenticate capability claims; define the fallback policy
  (prompt section 3 questions).

Alternative approaches:
  (a) Keep plaintext hello, apply policy only - closes spoofing by
      devices but NOT stripping by a MITM.
  (b) Authenticate the hello with an AEAD tag under the device's key
      (requires per-device keys, F-06). A stripped/forged hello then
      fails verification and the connection is rejected.

Selected approach:
  (b) + explicit policy table (section 8):
    - hello carries device_id, capabilities, nonce, auth_tag =
      ChaCha20Poly1305(device_key, device_id || capabilities).
    - gateway looks up the device in the known-device table FIRST;
      unknown device_id -> reject (no key to verify with).
    - tag verified -> claims are trusted as the key holder's claims.
    - policy: legacy-only -> fallback; ml-kem or both -> reject
      (modern path not implemented); unknown/malformed -> reject.
    - rejections logged with device_id + metric incremented.

Decision:  MODIFIED (P02 only listed questions; we define the policy
           table and the authentication mechanism)

Reason:
  This is the minimum that makes downgrade *detectable* in the demo:
  a tampered hello cannot pass verification, and the rejection is
  visible (log + metric). It reuses existing AEAD machinery.

Implementation scope:
  - config: known-device table (F-06).
  - device: attach auth tag to hello (~5 lines).
  - gateway: lookup + verify + policy decision (~20 lines).
  - metrics: rejections counted under messages_rejected.

Verification method:
  - Unit: valid hello accepted; hello with stripped capability or
    forged claims rejected (tag fails).
  - Live: MITM-style script rewriting the hello in transit -> gateway
    rejects and logs; counter increments.

Expected result:
  Capability claims from known devices are authenticated; stripping or
  forging claims is detected and rejected.

Remaining risk:
  - No modern device exists, so "strip ml-kem from a modern device"
    remains theoretical; when a modern device is added, its hello must
    be authenticated the same way (documented requirement).
  - device_id enumeration: unknown ids are rejected before tag
    verification, revealing which ids exist (accepted - ids are not
    secret in this prototype).
  - Replayed hello: a captured valid hello re-sent re-triggers
    fallback activation; bounded by replay work in F-05 (same
    device_id + seq checks); flagged as known minor gap.
```

### F-03 — Gateway Crash from Malformed Handshake

```text
AI claim:
  A mlkem_pubkey reply missing "public_key" raises KeyError, which
  escapes the retry loop's catch set and terminates the gateway
  process.

Technical verification:
  CONFIRMED (manually reproduced in P02, evidence in P02 appendix D):
  reply["public_key"] (gateway/cloud_channel.py:92) -> KeyError;
  connect_and_establish catches only (OSError, ProtocolError,
  CryptoError) -> KeyError escapes to main() -> process exit code 1.

Is the finding valid?  YES

Student evaluation:
  A remote, unauthenticated, one-message kill of the central
  component. HIGH severity in P02 is justified.

AI recommendation (P02):
  Validate required fields, raise ProtocolError.

Alternative approaches:
  (a) Broaden the retry-loop catch set to Exception - treats all
      failures uniformly but hides programming errors; not preferred.
  (b) Validate fields explicitly and raise ProtocolError - failures
      become ordinary retryable protocol errors.

Selected approach:
  (b) Uniform handshake validation:
    - reply must be dict, type == mlkem_pubkey, public_key a non-empty
      str that is valid base64 of the correct length (1184 bytes);
      any violation -> ProtocolError.
    - Same pattern applied to every handshake message (see F-04).
    - Malformed reply -> log warning, increment errors, retry (the
      loop already waits 3 s).

Decision:  ACCEPTED (as P02 recommended)

Reason:
  Smallest safe fix; turns a crash into a logged, counted, retried
  protocol violation; consistent with how reading messages are
  already validated.

Implementation scope:
  - Add a pure parse helper (e.g. parse_mlkem_pubkey_reply(reply) ->
    bytes) in gateway/processing.py so the behavior is unit-testable.
  - ~10 lines + tests.

Verification method:
  - Unit: missing field / wrong type / bad base64 / wrong length all
    raise ProtocolError.
  - Live: re-run P02 demo D -> gateway logs, retries, and keeps
    running (process still alive after the attempt).

Expected result:
  Malformed handshake messages no longer terminate the gateway.

Remaining risk:
  - An attacker flooding malformed replies keeps the gateway in a
    retry loop (log spam); acceptable for the demo, noted in risks.
```

### F-04 — Cloud Thread Crash from Malformed Encapsulation

```text
AI claim:
  A mlkem_encaps missing "ciphertext" raises KeyError in the handler
  thread, bypassing the normal error handling, producing a raw
  traceback and no error metric.

Technical verification:
  CONFIRMED (manually reproduced in P02, evidence in P02 appendix C):
  cloud/cloud.py:130 uses encaps["ciphertext"] directly; _handle
  catches (ProtocolError, ProcessingError, CryptoError, OSError) -
  KeyError is not among them; thread dies with a traceback; errors
  metric not incremented.

Is the finding valid?  YES

Student evaluation:
  Same defect class as F-03, with asymmetric consequences (thread vs
  process). The asymmetry between gateway and cloud validation is
  itself the underlying issue: the two handshake sides must follow
  one policy.

AI recommendation (P02):
  Same fix as F-03 + count errors; consistent policy unless a
  documented reason exists.

Alternative approaches:
  (a) Fix only the KeyError - leaves other missing-field variants.
  (b) Full per-field validation on both sides, ProtocolError on any
      violation (chosen).

Selected approach:
  (b) Uniform handshake validation policy for BOTH components:
    - required fields: type, and per message the documented fields
      (public_key / ciphertext / session_id / gateway_id).
    - violation -> ProtocolError -> existing _handle path: log
      warning, increment errors, close the connection (handshake
      failures are connection-fatal; reading failures remain
      drop-and-continue - this split is documented).

Decision:  ACCEPTED (as P02 recommended)

Reason:
  One policy, both components; error paths become visible in logs and
  metrics; nothing silently dies.

Implementation scope:
  - Cloud: validate encaps fields before use (~10 lines).
  - Gateway: same for pubkey reply (F-03).
  - Errors metric incremented on this path (part of F-08).

Verification method:
  - Unit: missing ciphertext / bad base64 / wrong length -> ProtocolError.
  - Live: re-run P02 demo C -> cloud logs "closing gateway connection:
    ..." with NO traceback; errors counter incremented.

Expected result:
  Malformed encaps messages are rejected cleanly, counted, and the
  connection is closed without a traceback.

Remaining risk:
  None beyond normal DoS-by-flood (see F-12).
```

### F-05 — Replay Attack

```text
AI claim:
  A captured valid encrypted reading can be replayed and is accepted
  again; sequence numbers exist in plaintext but are never checked.

Technical verification:
  CONFIRMED (manually reproduced in P02, evidence in P02 appendix B):
  identical message accepted twice; cloud stored the duplicate.

Is the finding valid?  YES

Student evaluation:
  Replay defeats the freshness property of the whole data path. The
  demo in P02 is a ready-made regression test.

AI recommendation (P02):
  Choose a mechanism (monotonic sequence / window / session counters /
  combination) and write fail-first tests.

Alternative approaches (comparison):
  (A) Monotonic per-device sequence - simplest; breaks across device
      restarts unless the counter is persisted.
  (B) Replay window - tolerates reordering but needs sliding-window
      bookkeeping; overkill for a single-device demo.
  (C) Session-bound counters - protects the gateway->cloud hop but
      does nothing on the legacy path (no session there), and the
      P02 attack went over the legacy path.
  (D) Combination - sequence + session identity.

Selected approach:
  (A) with two additions that make it workable:
    1. AEAD AAD binding: legacy messages use aad = device_id || seq;
       protected messages use aad = session_id (channel binding).
       Tampering with seq or moving a message between sessions now
       fails the tag.
    2. Device persists its sequence counter to a state file
       (device_state/<device_id>.seq); docker-compose gets a named
       volume for it in P04. Restarts therefore do not rewind the
       counter.
    Gateway and cloud each keep an in-memory per-device last-seen
    sequence and reject seq <= last_seen (messages_rejected metric).
    The cloud check is defense-in-depth (a compromised or buggy
    gateway cannot replay into the cloud).

Expected behavior definition:
  - sequence 1                 -> accepted
  - sequence 2                 -> accepted
  - duplicate sequence 2       -> REJECTED (replay) + metric
  - sequence 1 after 2         -> REJECTED (stale) + metric
  - very large sequence        -> accepted (no jump window - see risk)
  - device reconnect (same run) -> state kept at gateway; counter
    continues -> accepted
  - device restart (persisted counter) -> continues -> accepted
  - gateway/cloud restart      -> in-memory state lost; replays of
    pre-restart messages accepted until the device sends again
    (documented limitation)

Decision:  MODIFIED (P02 offered options; we select A + AAD binding +
           persistence and reject the window)

Reason:
  Closes the demonstrated attack with ~25 lines total and demonstrates
  three concepts at once (freshness, AEAD binding, state management).
  Windows and session counters add complexity without helping the
  legacy path where the attack actually lives.

Implementation scope:
  - common/crypto: AAD support in the AEAD wrappers (pairs with F-09).
  - device: persist seq after each send (~8 lines).
  - gateway: per-device last_seq dict + check (~12 lines).
  - cloud: same (~10 lines).
  - compose: named volume for device_state (3 lines).

Verification method:
  - Fail-first: the P02 replay script (temp, outside the tree) must
    be rejected after the change; new pytest cases for duplicate/
    stale/next/reconnect per the table above.

Expected result:
  Replayed or out-of-order messages are rejected and counted on both
  paths; legitimate traffic including restarts keeps flowing.

Remaining risk:
  - No jump window: a device (or attacker holding its key) can jump
    the counter far ahead; harmless for the demo, documented.
  - Gateway/cloud restart amnesia (see above) - accepted, documented.
  - Counter state file is a new deployment artifact; losing it wedges
    the device until the gateway restarts - documented operationally.
```

### F-06 — Static Shared PSK

```text
AI claim:
  One PSK protects all legacy devices; device_id is self-declared; one
  compromised device can impersonate any other.

Technical verification:
  CORRECT. common/config.py:58-66 defines a single LEGACY_PSK_HEX used
  by every device and the gateway.

Is the finding valid?  YES

Student evaluation:
  Acceptable only as a P01 placeholder. The F-02 fix (authenticated
  hello) is meaningless with a shared key - any holder can tag any
  hello - so per-device keys are a DEPENDENCY of the downgrade fix,
  not an optional extra.

AI recommendation (P02):
  Per-device keys, rotation plan (P1).

Alternative approaches:
  (a) Keep one simulation PSK, document only - cheapest, but downgrade
      fix degrades to "proof of possession of the shared key".
  (b) Per-device key table in config (device_id -> hex key), device
      receives only its own key via env - the prototype analogue of
      provisioning (chosen).
  (c) Full provisioning system - out of scope (prompt: do not
      over-engineer).

Selected approach:
  (b) - a small JSON map in config (env DEVICE_KEYS_JSON with a
  two-device demo default). The device uses DEVICE_KEY_HEX. The
  gateway resolves the key by device_id from the hello and rejects
  unknown ids.

Decision:  MODIFIED (elevated from P02's P1 to a P04 dependency of
           F-02; still priority P1 in its own right)

Reason:
  Minimal change that gives the hello its meaning and kills
  cross-device impersonation within the known table.

Implementation scope:
  - config: key table parsing + demo defaults (~15 lines).
  - device: read own key from env (~3 lines).
  - gateway: lookup by device_id (~5 lines).
  - compose: per-device key env vars.

Verification method:
  - Unit: unknown device rejected; wrong key for known id rejected
    (hello tag fails); correct key accepted.
  - Live: two demo devices with distinct keys both work; swapping one
    device's key breaks only that device.

Expected result:
  Each legacy device authenticates with its own key; impersonation
  requires possession of that device's key.

Remaining risk:
  - Static keys, no rotation/revocation (documented, deferred).
  - Key distribution is via env/compose (simulated provisioning).
```

### F-07 — Broken Session Lifecycle

```text
AI claim:
  If the cloud dies after establishment, the gateway keeps stale
  session state, /health reports connected=true forever, there is no
  reconnect, session ids are reused across retries, and the cloud
  registry never evicts sessions.

Technical verification:
  CORRECT by inspection. gateway/cloud_channel.py:50 generates
  session_id once in __init__; _sock/session_key are only cleared by
  object destruction; send failures propagate without state cleanup
  (gateway/cloud_channel.py:119 sets _sock only on success);
  is_established() checks only the two fields; cloud registry has add
  and get but no remove.

Is the finding valid?  YES

Student evaluation:
  A transient cloud failure permanently degrades the demo and the
  health endpoint lies - exactly the operational failure students
  should learn to design for.

AI recommendation (P02):
  Clear state on failure, reconnect, new session ids, truthful
  health.

Alternative approaches:
  (a) Minimal: clear state on send failure only - no reconnect (device
      connections keep dying until gateway restart).
  (b) Full: state machine + reconnect + eviction + health reporting
      (chosen).

Selected approach:
  (b) Simple five-state machine in CloudChannel:
      DISCONNECTED -> CONNECTING -> ESTABLISHING -> ESTABLISHED
      -> FAILED -> DISCONNECTED (loop)
    - A new session_id is generated per establishment attempt
      (move token generation into _establish_once).
    - Any send/read failure transitions to FAILED: clear _sock and
      session_key, then re-enter the connect loop (existing 3 s
      retry pacing).
    - Health reports cloud_state (string) + cloud_connected
      (ESTABLISHED only); gateway status is "degraded" while not
      established.
    - Cloud: registry.remove(session_id) when the gateway connection
      closes (finally block in _handle); stale sessions do not
      accumulate.
    - Session expiry timers: DEFERRED (disconnect-eviction is enough
      for the demo).

Decision:  ACCEPTED (as P02 recommended, with the lifecycle diagram
           from the prompt adopted as-is - it matches the design)

Reason:
  The diagram in the prompt is already the right model; implementing
  it is ~40 lines and makes failure behavior demonstrable.

Implementation scope:
  - cloud_channel: state field, per-attempt session_id, failure
    transitions, reconnect loop.
  - cloud: registry.remove + eviction on disconnect.
  - health provider: state reporting (pairs with F-13).

Verification method:
  - Live: establish, kill the cloud, observe /health -> degraded,
    restart the cloud, observe automatic reconnection with a NEW
    session id and resumption of forwarding.
  - Unit: state transitions (extract the machine into a testable
    form if practical).

Expected result:
  Cloud failure -> degraded health -> automatic recovery with fresh
  session; no stale "connected" state.

Remaining risk:
  - Device connections are closed while the gateway cannot forward
    (no buffering) and the device has no reconnect logic - accepted
    for the demo, noted as future work.
  - No session expiry timers.
```

### F-08 — Metrics Problems

```text
AI claim:
  payload_bytes is recorded in a seconds-labeled timing aggregate;
  forward_ms records milliseconds under _s keys; fallback_events
  actually counts per-connection activations; errors are undercounted
  (handshake failures bypass them); the device has no metrics.

Technical verification:
  CORRECT by inspection: gateway/gateway.py:114-116 observe()s
  forward_ms (ms) and payload_bytes (bytes) into a single timing
  aggregate whose snapshot keys are avg_s/min_s/max_s
  (common/metrics.py:53); cloud/gateway error increments exist but
  the F-03/F-04 paths never reach them; device.py has no Metrics
  object.

Is the finding valid?  YES

Student evaluation:
  These numbers feed the course's baseline analysis; mislabeled units
  silently corrupt it.

AI recommendation (P02):
  Fix units, define fallback semantics, count every error path.

Alternative approaches:
  (a) Rename only - cosmetic, still conflates seconds and bytes.
  (b) Add a unit tag to observations and split counters from stats
      (chosen).

Selected approach:
  (b) Proposed metric table (units recorded in the snapshot):

  | Metric | Type | Unit | Meaning |
  | --- | --- | --- | --- |
  | messages_received | counter | count | messages read from the wire |
  | messages_processed | counter | count | messages accepted after full validation/decrypt |
  | messages_forwarded | counter | count | gateway: readings sent to cloud |
  | messages_rejected | counter | count | NEW: drops for policy/protocol reasons (replay, bad MAC, unknown device, malformed) |
  | errors | counter | count | unexpected failures (exceptions, connection faults) - every path |
  | fallback_activations | counter | count | RENAMED from fallback_events: hellos that successfully authenticated and activated fallback |
  | legacy_devices_detected | counter | count | distinct known device_ids that activated fallback |
  | mlkem_sessions_established | counter | count | successful ML-KEM establishments |
  | mlkem_establish_s | timing | seconds | gateway: request -> established duration |
  | mlkem_decapsulate_s | timing | seconds | cloud: decapsulate + HKDF duration |
  | forward_s | timing | seconds | RENAMED from forward_ms: one reading send |
  | payload_bytes | size | bytes | reading plaintext size (min/avg/max) |

  - Metrics.observe(name, value, unit) records the unit; snapshot
    reports avg/min/max with the unit, no forced _s suffix.
  - errors incremented on ALL handler failure paths including
    handshake validation failures.
  - Device metrics: DEFERRED - the device has no health endpoint and
    its logs suffice at demo scale (documented).

Decision:  MODIFIED (P02 said "fix units" generally; we define the
           exact table)

Reason:
  A concrete, testable definition avoids a second round of
  inconsistencies and keeps the metric set small.

Implementation scope:
  - common/metrics.py: unit support (~10 lines).
  - Renames + increments across gateway/cloud (~15 lines).
  - tests updated accordingly (P04 may modify tests).

Verification method:
  - Unit: snapshot reports units correctly; error counters increment
    on the F-03/F-04 regression tests; fallback_activations counts
    hellos, not messages.

Expected result:
  Every metric has one unambiguous meaning and unit; analysis-ready.

Remaining risk:
  None material; metrics remain in-memory only (as designed).
```

### F-09 — Duplicated AEAD Code

```text
AI claim:
  encrypt/decrypt_legacy_payload and encrypt/decrypt_session_payload
  are near-identical; changes must be made twice.

Technical verification:
  CORRECT. Four functions in common/crypto.py differ only in the
  exception type raised.

Is the finding valid?  PARTIALLY - the duplication is real, but at
                     this scale the two explicit functions also serve
                     readability ("two paths" narrative), so the harm
                     is low.

Student evaluation:
  The F-05 AAD change must touch both pairs; that is the moment
  duplication starts to cost. A minimal refactor now is cheaper than
  two divergent edits.

AI recommendation (P02):
  Unify into one generic pair or thin wrappers.

Selected approach:
  Keep the public API but implement over one private core:
    _aead_encrypt(key, plaintext, aad) -> envelope
    _aead_decrypt(key, envelope, aad, error_cls) -> bytes
  The four public functions become 2-3 line wrappers. No behavior
  change.

Decision:  MODIFIED (smallest possible refactor)

Reason:
  One edit point for AAD changes; public names/behavior unchanged;
  educational two-path structure preserved.

Implementation scope:
  ~15 lines in common/crypto.py + unchanged test suite (P02 tests
  already cover both pairs).

Verification method:
  Existing 39 tests must still pass unchanged after the refactor.

Expected result:
  Single core, four thin wrappers, no behavior change.

Remaining risk:
  None.
```

### F-10 — Configuration Duplication

```text
AI claim:
  Ports and the PSK exist in both common/config.py defaults and
  docker-compose.yml and can drift.

Technical verification:
  CORRECT by inspection (e.g. 5001/5002/8001/8002 and LEGACY_PSK_HEX
  appear in both).

Is the finding valid?  YES (minor)

Student evaluation:
  Drift risk is real but small; a generator would be over-engineering.

AI recommendation (P02):
  Single source of truth / document which side is authoritative.

Selected approach:
  Policy (documentation only): common/config.py defaults are the
  single source of truth for DEFAULT values; docker-compose.yml may
  override per deployment and must name the same env vars. Add
  cross-reference comments in both files in P04. No code generation.

Decision:  MODIFIED (documentation-only)

Reason:
  Zero runtime risk; prevents the most likely drift (renaming a var
  in one place).

Implementation scope:
  Comments only + README note (~10 lines).

Verification method:
  Manual review: compose env names match config.py _env names.

Expected result:
  Obvious, documented authority for each setting.

Remaining risk:
  Discipline-dependent (comments can go stale); accepted.
```

### F-11 — Key Lifecycle

```text
AI claim:
  No session eviction, static ML-KEM keypair, keys live in immutable
  Python bytes with no zeroization.

Technical verification:
  CORRECT by inspection (registry has no remove; keypair generated
  once in cloud main(); Python bytes cannot be zeroized).

Is the finding valid?  PARTIALLY - eviction and keypair lifetime are
                     real design gaps; zeroization is a language
                     limitation that cannot be meaningfully fixed in
                     pure Python and should not be pretended.

Student evaluation:
  A practical prototype policy is enough; secure-memory machinery is
  explicitly out of scope (prompt section 11).

Selected approach (practical prototype policy):
  - Sessions: evicted when the owning gateway connection closes
    (implemented with F-07).
  - ML-KEM keypair: one demo keypair per cloud process run; rotation
    DEFERRED and documented (pinning in F-01 interacts: rotating the
    key requires updating the pin - documented as the intended
    operational story).
  - Device keys: static config for the demo; rotation deferred.
  - Zeroization: not feasible; policy statement: keys live for the
    process lifetime; documented in README. A C-extension-based
    secure buffer is out of scope.

Decision:  MODIFIED (eviction now, everything else deferred with
           documentation)

Reason:
  Fixes the unbounded-growth defect; everything else is honest
  deferred scope, not pretend-security.

Implementation scope:
  registry.remove + call site (part of F-07) + README key-lifecycle
  statement.

Verification method:
  Live: reconnect a gateway N times -> registry.count() stays at 1;
  disconnect -> count 0.

Expected result:
  No orphaned session keys accumulate.

Remaining risk:
  Static keys and no rotation remain; documented.
```

### F-12 — Threads / Timeouts / Rate Limiting

```text
AI claim:
  Unbounded per-connection threads, 60 s timeouts, no rate limiting.

Technical verification:
  CORRECT by inspection.

Is the finding valid?  YES, but the severity does not match the
                     project scale.

Student evaluation:
  The demo runs 1-3 devices on localhost. A thread per connection is
  the *simplest correct* model and is exactly what a student should
  read first. Rate limiting has no adversary at demo scale except the
  F-03/F-04 floods, which the validation fix already logs and counts.

AI recommendation (P02):
  Thread pool / connection caps / shorter timeouts (P3).

Selected approach:
  DEFER the whole finding. Note as a one-line optional tweak: reduce
  the 60 s socket timeout to 10 s if idle connections become annoying
  during demos (not required).

Decision:  DEFERRED (with justification)

Reason:
  Complexity without a demonstrated problem at this scale; the prompt
  explicitly allows deferring findings that are clearly justified.

Implementation scope:
  None in P04.

Verification method:
  N/A (revisit if the demo grows past ~10 devices).

Expected result:
  N/A.

Remaining risk:
  A determined local attacker can hold ~dozens of idle threads; no
  impact on the course goals. Recorded.
```

### F-13 — Health Endpoint

```text
AI claim:
  /health always returns "ok" and cannot express degraded states
  (combined with F-07 it can lie).

Technical verification:
  CORRECT by inspection (common/health.py returns "ok" unless the
  provider raises).

Is the finding valid?  YES

Student evaluation:
  "Healthy" must mean something operational, or the endpoint is a
  demo prop.

Selected approach (simple status model):
  - Gateway: status "ok" iff the device listener is bound AND
    cloud_state == ESTABLISHED; otherwise "degraded" with
    cloud_state included ("connecting", "establishing", "failed").
  - Cloud: status "ok" iff the server is serving (implied by
    answering) AND mlkem_ready (keypair present) is true; storage
    failure would surface as an exception -> "degraded". Reports
    stored_readings and active_sessions counts.
  - Both endpoints stay unauthenticated and bound to 0.0.0.0
    (documented; needed for compose healthchecks and host demo
    access).

Decision:  MODIFIED

Reason:
  ~15 lines total; makes the F-07 recovery observable in the demo.

Implementation scope:
  - Health providers compute status from real state.
  - Gateway exposes cloud_state (pairs with F-07).

Verification method:
  Live: kill cloud -> gateway /health shows degraded/connecting;
  restart -> ok. Unit: provider logic as pure functions.

Expected result:
  /health reflects the operational truth.

Remaining risk:
  Health endpoint remains unauthenticated (documented).
```

### F-14 — Dependency Drift

```text
AI claim:
  cryptography>=45.0 is unpinned; the ML-KEM API already shifted
  between versions during P01 (assumed ml_kem; actual mlkem), so CI
  may drift from the reviewed environment.

Technical verification:
  CORRECT. requirements.txt declares cryptography>=45.0; pip resolves
  50.0.1 today; the P01 correction history is recorded in the P02
  report (§12).

Is the finding valid?  YES

Student evaluation:
  Reproducibility matters for grading and for the ML-KEM environment
  (wheel-bundled OpenSSL; the API, not the OS, is the drift risk).

Selected approach:
  Pin exact versions in requirements.txt:
    cryptography==50.0.1
    pytest==9.1.1
  with a comment explaining why (ML-KEM API stability).

Decision:  ACCEPTED

Reason:
  Two-line change; eliminates the largest reproducibility variable.

Implementation scope:
  requirements.txt edit + README note.

Verification method:
  Fresh venv install from the pinned file -> pytest 39/39 on the
  pinned versions (already true locally).

Expected result:
  Every environment installs the reviewed versions.

Remaining risk:
  Pinning ages over time; revisit per phase (documented).
```

### F-15 — Truncated Message Error Text

```text
AI claim:
  A peer that sends a partial message and closes (no trailing newline)
  triggers "message exceeds maximum allowed size" - wrong diagnosis.

Technical verification:
  CORRECT. common/protocol.py:75 combines the two conditions; a
  truncated-at-EOF message without newline hits the same branch as an
  oversized message.

Is the finding valid?  YES (minor)

Student evaluation:
  Cheap fix, better diagnostics for the students' own debugging.

Selected approach:
  Split the branches: content-without-newline at EOF ->
  ProtocolError("connection closed mid-message"); no content ->
  ConnectionClosedError (unchanged); len > MAX -> oversized error
  (unchanged).

Decision:  ACCEPTED

Reason:
  ~5 lines + 2 tests; removes a misleading message.

Implementation scope:
  common/protocol.py read_message() split + tests.

Verification method:
  Unit: partial line + close -> "mid-message" error; oversize ->
  size error; empty close -> ConnectionClosedError.

Expected result:
  Accurate error classification for three distinct conditions.

Remaining risk:
  None.
```

---

## 5. Student Decision Table

| ID | Finding | Valid? | Student Decision (proposed) | Priority | P04 Action |
| --- | --- | --- | --- | --- | --- |
| F-01 | Unauthenticated ML-KEM key establishment | YES | MODIFIED — fingerprint pinning | P0 | Pin cloud key fingerprint at gateway |
| F-02 | Capability spoofing / downgrade | YES | MODIFIED — authenticated hello + policy table | P0 | Hello AEAD tag + fallback policy |
| F-03 | Gateway crash on malformed handshake | YES | ACCEPTED | P0 | Handshake field validation |
| F-04 | Cloud thread crash on malformed encaps | YES | ACCEPTED | P0 | Same validation policy on cloud |
| F-05 | Replay attack | YES | MODIFIED — monotonic seq + AAD + persistence | P0 | Seq enforcement both hops |
| F-06 | Static shared PSK | YES | MODIFIED — per-device key table | P1 | Known-device table (F-02 dependency) |
| F-07 | Broken session lifecycle | YES | ACCEPTED | P1 | State machine + reconnect + eviction |
| F-08 | Metrics problems | YES | MODIFIED — defined metric table | P2 | Units + renames + error counts |
| F-09 | Duplicated AEAD code | PARTIALLY | MODIFIED — minimal core refactor | P2 | _aead_encrypt/_aead_decrypt core |
| F-10 | Configuration duplication | YES | MODIFIED — documentation-only policy | P2 | Cross-reference comments |
| F-11 | Key lifecycle | PARTIALLY | MODIFIED — eviction now, rest deferred | P3 | Session eviction (with F-07) |
| F-12 | Threads / timeouts / rate limiting | YES | DEFERRED — scale does not justify | P3 | None |
| F-13 | Health endpoint semantics | YES | MODIFIED — status model | P2 | Derived status + cloud_state |
| F-14 | Dependency drift | YES | ACCEPTED — pin versions | P1 | Pin cryptography==50.0.1, pytest==9.1.1 |
| F-15 | Truncated message error | YES | ACCEPTED — small fix | P2 | Split error branches |

All decisions above are proposals awaiting student confirmation.

---

## 6. P0 / P1 / P2 / P3 Priorities

**P0 — must fix before further development:**
- F-01 (authentication of key establishment) — without it the PQC
  path's central claim is not demonstrable.
- F-03, F-04 (crash-class bugs) — they can terminate components
  during any subsequent testing.
- F-05 (replay) — demonstrated attack against the data path.
- F-02 (downgrade) — the course topic; needs F-06 as dependency.

**P1 — important:**
- F-06 (per-device keys) — enables the F-02 fix; small.
- F-07 (session lifecycle) — operational truthfulness.
- F-14 (pin dependencies) — reproducibility for grading.

**P2 — useful:**
- F-08 (metrics), F-09 (AEAD dedup), F-10 (config policy),
  F-13 (health semantics), F-15 (error text).

**P3 — deferred:**
- F-11 (partial: eviction done in P1/F-07; rotation/zeroization
  deferred), F-12 (threads/rate limiting).

---

## 7. Security Design Decisions

### 7.1 Authentication — who authenticates whom?
- **Gateway authenticates Cloud:** by ML-KEM public-key SHA-256
  fingerprint pinning (config `CLOUD_PUBLIC_KEY_SHA256`; the cloud
  prints its fingerprint at startup so students can copy it).
- **Gateway authenticates legacy Devices:** by per-device key
  (F-06): device_id resolves to a key; the hello's AEAD tag proves
  possession; the data path's AEAD under the same key extends the
  proof to every message.
- **Cloud does NOT authenticate the gateway** in P04 (documented
  gap; gateway_id is informational).
- Modern devices: none exist; policy for their future hello auth is
  documented in §8.

### 7.2 Confidentiality — what is protected, from whom?
- Reading payloads: ChaCha20-Poly1305 end-to-end on both hops
  (device→gateway under the device key; gateway→cloud under the
  ML-KEM-derived session key). Protects payload contents from passive
  network eavesdroppers.
- Metadata (message types, device_ids, session_ids, sizes, timing):
  NOT protected (no TLS) — documented as a known limitation.
- Protection against active attackers: tampering with protected
  payloads is detected (AEAD); the key-establishment hop resists key
  substitution via pinning; hello tampering is detected via the tag.

### 7.3 Integrity — how are modified messages detected?
- AEAD tags on every protected payload; tag verification before any
  processing.
- AAD binding (F-05): legacy aad = device_id || seq; protected
  aad = session_id. Re-binding a captured message to another device,
  session, or sequence fails the tag.
- Hello integrity via its AEAD tag over device_id || capabilities.
- Public-key integrity at establishment via the fingerprint check.
- All failures → reject + messages_rejected/errors metric + log.

### 7.4 Freshness — how are replays detected?
- Per-device monotonic sequence numbers, generated and persisted by
  the device, verified by the gateway (legacy path) and the cloud
  (protected path, defense-in-depth): accept iff seq > last_seen.
- See §9 for the full behavior table and limitations (gateway/cloud
  restart amnesia; no jump window).

### 7.5 Downgrade resistance — how is forced fallback prevented/detected?
- Capability claims are authenticated (hello tag under the device
  key), so a MITM cannot strip `ml-kem-768` without breaking the
  tag → rejection + log + metric.
- Policy never auto-downgrades: modern/ambiguous/unknown/malformed
  claims are rejected; fallback is granted only to known devices
  whose authenticated hello claims legacy-only.
- Fallback activation is explicitly logged as a warning and counted
  (fallback_activations), making downgrade events visible.

### 7.6 Key lifecycle — when are keys created, used, expired, removed?
- ML-KEM keypair: created once per cloud process; used for all
  sessions; never expires in P04 (rotation deferred; rotating
  requires updating the pin — documented operational story).
- Session keys: derived per establishment (HKDF); used for that
  session's traffic; removed when the gateway connection closes
  (eviction with F-07).
- Device keys: static config; used per message; no expiry
  (deferred).
- Zeroization: not feasible in pure Python; keys live for the
  process lifetime (documented; C-level secure memory out of scope).

### 7.7 Legacy compatibility — when is fallback allowed?
- Fallback is allowed ONLY for devices present in the known-device
  table whose authenticated hello claims legacy-only capabilities.
- The gateway REJECTS: unknown device_ids, modern claims, ambiguous
  (both) claims, malformed hellos, failed hello tags.
- Migration demonstration: the device table carries each device's
  path; upgrading a device = updating its table entry (documented as
  the prototype's migration story). See §8.

---

## 8. Fallback Policy

| Device claim | Gateway decision | Reason |
| --- | --- | --- |
| legacy only (`chacha20-poly1305`), known device, valid tag | FALLBACK path (logged warning + metric) | Genuine legacy device during migration |
| `ml-kem-768` claimed | REJECT (modern path not implemented) | Honest rejection; prevents spoofing the unimplemented path |
| both capabilities | REJECT | Ambiguous; never auto-downgrade when modern is claimed |
| unknown / no capabilities | REJECT | Conservative; no silent downgrade |
| unknown device_id | REJECT (no key to verify) | Untrusted device |
| malformed hello / failed tag | REJECT + metric | Protocol violation or tampering (possible downgrade attempt) |

Policy invariants:
1. Capability claims are trusted only after tag verification under
   the device's own key.
2. Fallback never activates without an authenticated hello.
3. Every fallback activation is observable (log + metric).
4. Rejection reasons are logged with the device_id but never expose
   key material.

Known limitation: hello replay (a captured valid hello re-sent)
re-triggers fallback activation; harmless and observable in the
prototype, noted as future work.

---

## 9. Replay Protection Design

Mechanism: per-device monotonic sequence + AEAD AAD binding +
device-side counter persistence + enforcement at gateway and cloud.

| Event | Expected behavior |
| --- | --- |
| sequence 1 | accepted |
| sequence 2 | accepted |
| duplicate sequence 2 | REJECTED (replay) + messages_rejected metric |
| sequence 1 after 2 | REJECTED (stale) + metric |
| very large sequence | accepted (no jump window — documented) |
| device reconnect (same gateway run) | accepted; gateway keeps per-device state |
| device restart (persisted counter) | accepted; counter continues from file |
| gateway or cloud restart | in-memory seq state lost; replays of pre-restart messages accepted until the device sends again (documented) |

Implementation notes:
- Legacy messages: aad = device_id || seq; seq also carried as a
  plaintext envelope field for early rejection.
- Protected messages: aad = session_id (channel binding); the inner
  reading's device_id + seq are checked by the cloud per device.
- Device persists its counter to `device_state/<device_id>.seq` after
  each send; docker-compose mounts a named volume for that directory
  (P04).
- Rejected messages are counted and logged; connections stay open
  (reading-level policy), matching existing drop-and-continue
  behavior.

Future extension (documented, not in P04): incarnation counters to
survive state-file loss and gateway restarts without amnesia.

---

## 10. Session Lifecycle Design

Adopted from the prompt's diagram:

```text
DISCONNECTED
     ↓
CONNECTING
     ↓
ESTABLISHING
     ↓
ESTABLISHED
     ↓
FAILED          (any send/read failure, or failed handshake attempt)
     ↓
DISCONNECTED    (state cleared: _sock=None, session_key=None)
     ↓
CONNECTING      (retry loop, 3 s pacing, NEW session_id per attempt)
```

Rules:
- `session_id` is generated per establishment attempt, never reused.
- Health: `cloud_state` mirrors the state machine; `cloud_connected`
  is true only in ESTABLISHED; gateway `/health` reports "degraded"
  while not established (F-13).
- Cloud: the session registry entry is removed when the owning
  gateway connection closes (eviction, F-11 partial).
- Session expiry timers: deferred (documented).
- While FAILED/DISCONNECTED, device connections that need forwarding
  are closed (no buffering); the device has no reconnect logic —
  accepted, documented.

---

## 11. Proposed Target Architecture

```text
Legacy Device                          Gateway                        Cloud
(per-device key K_d,       hello: {device_id, capabilities,      (ML-KEM keypair;
 persisted seq counter)      nonce, auth_tag=AEAD(K_d, claims)}    prints SHA-256 fingerprint
      |                              |                               of public key at startup)
      |                              | mlkem_request_pubkey          |
      |                              |------------------------------>|
      |                              | mlkem_pubkey                  |
      |                              |<------------------------------|
      |                              | verify SHA-256 fingerprint    |
      |                              | against pinned value          |
      |                              | mlkem_encaps {ciphertext}     |
      |                              |------------------------------>|
      |                              | mlkem_established             |
      |                              |<------------------------------|
      |                              | session_key = HKDF(shared)    |  (cloud: decapsulate+HKDF)
      |                              |                               |
      | legacy_reading:              |                               |
      |  AEAD(K_d, reading,          | decrypt, seq check,           |
      |  aad=dev_id||seq)            | re-encrypt:                   |
      |----------------------------->|  AEAD(session_key, reading,  |
      |                              |  aad=session_id)              |
      |                              |------------------------------>|
      |                              |                               |  decrypt, seq check,
      |                              |                               |  store, metrics
```

Secured by the P04 design:
- authentication: cloud→gateway via pinning; device→gateway via
  per-device key + hello tag;
- capability negotiation: authenticated hello + §8 policy table;
- fallback: only for known legacy devices with valid tags;
- replay protection: §9;
- session lifecycle: §10 with health state and eviction;
- metrics: §F-08 table; health: §F-13 model.

**Intentionally insecure or simulated (must stay visible in docs):**
- plain TCP, no TLS (metadata exposure);
- cloud does not authenticate gateways;
- static demo keys, no rotation;
- gateway/cloud restart amnesia for replay state;
- no rate limiting / thread caps;
- in-memory storage and metrics;
- key material lives for the process lifetime (no zeroization).

---

## 12. Test-First Plan

Tests that should FAIL against the current baseline and PASS after
the P04 changes (to be added in P04; nothing is modified now):

**Handshake**
- `mlkem_pubkey` missing `public_key` → gateway logs, retries, stays
  alive (currently: process crash).
- `mlkem_encaps` missing `ciphertext` → cloud closes cleanly with log
  + metric, no traceback (currently: thread crash).
- malformed base64 public key / ciphertext → ProtocolError path.
- public key of wrong length → rejected.
- unexpected first message type → rejected, counted.
- public key whose fingerprint does not match the pin → establishment
  refused (F-01).

**Replay**
- duplicate sequence → rejected + metric (currently: accepted).
- older sequence after newer → rejected.
- valid next sequence → accepted.
- reconnect with continued sequence → accepted.
- replay across connection boundary → rejected.
- device restart with persisted counter → accepted.

**Downgrade**
- hello with stripped `ml-kem-768` → tag fails → rejected
  (currently: silently treated as legacy-only).
- forged capabilities under a different device's key → rejected.
- unknown device_id → rejected.
- modern claim → rejected (policy).
- malformed hello → rejected + counted.

**Session**
- cloud killed after establishment → gateway `/health` degraded;
  reconnect with NEW session_id; forwarding resumes (currently:
  wedged).
- stale session_id protected message → rejected.
- gateway reconnect → cloud registry count does not grow (eviction).

**Metrics**
- payload_bytes reported with unit bytes (not seconds).
- errors incremented on handshake failures.
- fallback_activations counts hellos, not messages.

---

## 13. Verification Matrix

| Decision | Current baseline | Proposed behavior | Test | Expected result |
| --- | --- | --- | --- | --- |
| Authentication (F-01) | unauthenticated key acceptance | fingerprint-pinned ML-KEM establishment | fake cloud with wrong key / wrong fingerprint | establishment refused + retried; real cloud succeeds |
| Replay (F-05) | accepted | monotonic seq + AAD, both hops | duplicate/stale seq cases (§12) | rejected + counted; fresh seq accepted |
| Handshake validation (F-03/F-04) | crash / traceback | ProtocolError handling | malformed handshake cases (§12) | logged, counted, no crash; gateway survives |
| Downgrade (F-02) | possible | authenticated hello + policy table | stripped/forged hello cases (§12) | rejected + counted |
| Session failure (F-07) | wedged, health lies | state machine + reconnect + eviction | kill-cloud scenario | degraded → reconnect with new id → resume |
| Metrics (F-08) | inconsistent units, undercounted errors | defined table with units | unit + counter assertions (§12) | exact semantics hold |

---

## 14. Remaining Risks

After the proposed P04 changes, these risks remain (all documented in
the README):
1. No TLS: metadata (ids, sizes, timing) visible; active tampering of
   unprotected fields possible (but detected where tags/pins apply).
2. Cloud does not authenticate gateways.
3. Static keys; no rotation, revocation, or expiry timers.
4. Gateway/cloud restart amnesia for replay state.
5. No jump window on sequence numbers.
6. Hello replay re-triggers fallback activation (observable, benign).
7. Device has no reconnect logic; device connections drop during
   gateway-cloud outages.
8. No rate limiting / thread caps (accepted at demo scale).
9. Key material not zeroized (Python limitation).
10. Pin and device keys distributed via config/env (simulated
    provisioning).
11. Docker compose not yet verified in any environment (Docker
    unavailable on the review machine).

---

## 15. Deferred / Rejected Findings

**Deferred (documented future work):**
- F-12 entirely (threads/timeouts/rate limiting) — scale
  justification in §4.
- F-11 partial: key rotation, zeroization, session expiry timers.
- F-08 partial: device-side metrics.
- Device reconnect logic (adjacent to F-07, not demanded by the
  finding).
- Incarnation counters for replay-state durability (§9 future
  extension).

**Rejected as proposed (replaced by a simpler design):**
- F-01 via TLS or signature-bound keys — replaced by pinning (§16).
- F-05 via replay windows — replaced by monotonic sequence (§16).
- F-10 via config generation tooling — documentation policy instead.

Nothing else was rejected outright; the remaining findings were
modified in scope or severity as recorded in §4/§5.

---

## 16. AI Recommendation Quality Review

P02 recommendations that should NOT be followed blindly:

1. **"TLS" as an F-01 option — REJECT for this project.** Correct
   engineering in production, but it would wrap and hide the ML-KEM
   handshake the course must demonstrate, and adds certificate
   management to a project told to avoid production machinery.
   Pinning achieves the educational goal with ~15 lines.
2. **"Signature-bound ML-KEM public key" — DEFER.** The right answer
   at scale (rotating keys need signatures, pins break), but it
   implies a signing key + verification-key distribution, i.e. a
   mini-PKI. The prototype has static keys, so pinning is strictly
   simpler and equally effective *here*.
3. **"Replay windows" — REJECT for this project.** Window management
   (bitmaps, out-of-order tolerance) adds statefulness the demo does
   not need; a single-device stream is naturally ordered. Monotonic
   sequence + persisted counter is simpler and closes the actual
   attack.
4. **"Thread pool / connection caps" (F-12) — DEFER.** Valid for
   production; irrelevant at 1–3 localhost devices. Blindly applying
   it would add code the students must then understand for no
   observable benefit.
5. **"Per-device keys" (F-06) — ELEVATED, not followed as P2's P1
   suggestion implies.** P02 listed it as an important improvement;
   P03 shows it is actually a *dependency* of the downgrade fix
   (shared keys make hello authentication meaningless). This is an
   example of a correct-but-underweighted AI recommendation.
6. **"CI API-drift check step" (F-14) — KEEP, but simplified.** A
   dedicated CI import-check step is redundant once versions are
   pinned; pinning alone addresses the drift risk. The extra CI step
   is optional polish, not a requirement.
7. P02's severity calibration held up under re-verification (nothing
   needed downgrading); the adjustments above are scope/simplicity
   decisions, not corrections of factual errors.

---

## 17. P04 Implementation Plan

Proposed task order (each item is a small, testable change; P04
implements ONLY what the students approve from this document):

1. **Pin dependencies** [F-14]: `cryptography==50.0.1`,
   `pytest==9.1.1` + comment.
2. **Protocol hardening** [F-03, F-04, F-15]: handshake field
   validation helpers (parse_mlkem_pubkey_reply, encaps field
   checks) raising ProtocolError; split truncated/oversized error
   branches.
3. **AEAD core refactor with AAD** [F-09 + F-05 prep]:
   `_aead_encrypt/_aead_decrypt(key, data, aad, error_cls)` core;
   four public wrappers unchanged in behavior.
4. **Metrics refactor** [F-08]: units on observations; renames
   (fallback_activations, forward_s); messages_rejected counter;
   error increments on all failure paths.
5. **Per-device keys** [F-06, F-10]: device key table in config,
   device reads its own key, gateway lookup + unknown-id rejection;
   config-policy comments (F-10).
6. **Authenticated hello + fallback policy** [F-02]: hello tag on
   device; gateway verification + §8 decision table implementation.
7. **Replay protection** [F-05]: seq in legacy envelope + AAD
   (device_id||seq); session_id as AAD on protected path; per-device
   seq state at gateway and cloud; device counter persistence +
   compose volume.
8. **Cloud key pinning** [F-01]: fingerprint print at cloud startup;
   pin check in gateway establishment.
9. **Session lifecycle** [F-07, F-13]: CloudChannel state machine,
   per-attempt session ids, failure→reconnect, registry eviction on
   disconnect, health state reporting and degraded status.
10. **Tests**: add the §12 fail-first suite; update tests touched by
    renames (test_metrics etc.); re-run the P02 replay/attack demo
    scripts (kept outside the tree) and confirm they now fail
    safely.
11. **Deployment/docs**: compose named volume + per-device key envs;
    README updates (new limitations, removed/solved items, decision
    records pointing to this document).

Each task's acceptance criterion is its row in §13.

---

## Final output notes

- **Repository inspected:** README.md, CLAUDE.md,
  prompt/P01+P02+P03, review/P02, common/* (config, protocol,
  crypto, metrics, health, logging_setup), device/*, gateway/*
  (gateway, processing, cloud_channel), cloud/* (cloud, processing,
  store), tests/*, Dockerfile.*, docker-compose.yml,
  .github/workflows/ci.yml, requirements.txt, pytest.ini.
- **Verification performed:** tested (pytest 39/39 re-run); manually
  reproduced (F-03/F-04/F-05 in P02, evidence in the P02 appendix —
  not re-run in P03, code unchanged); code inspection (all other
  findings, line references re-confirmed); not verified (Docker, CI,
  Linux).
- **Student decisions required:** ALL decisions in §5 are proposals;
  the team must explicitly confirm or change: (1) threat-model
  statement and pinning choice for F-01, (2) fallback policy table
  (F-02), (3) replay design incl. its documented limitations (F-05),
  (4) per-device key model (F-06), (5) session lifecycle scope
  (F-07), (6) whether deferred items (F-11 remainder, F-12, device
  reconnect) stay deferred.
- **Proposed P04 scope:** the 11 tasks in §17, only as approved.
- **Files created:** `review/P03 - Student Security Evaluation &
  Design Decisions.md` only. No source code, tests, config, Docker,
  CI, or README files were modified.
- **No claims of fixes:** nothing in P03 fixes, tests-after-fix, or
  guarantees authentication, replay protection, or downgrade
  resistance. Those properties exist only if P04 implements and
  verifies them.
