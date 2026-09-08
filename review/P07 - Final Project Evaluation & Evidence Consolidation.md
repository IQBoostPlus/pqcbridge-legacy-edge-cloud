# P07 - Final Project Evaluation & Evidence Consolidation

> **AI-generated final evaluation report.** This document was
> produced by an AI assistant executing `prompt/P07 - Final Project
> Evaluation & Evidence Consolidation.md`. P07 is NOT an
> implementation phase: no security feature was added, no finding
> was re-fixed, and no defect was hidden. Its purpose is to verify
> the final project state against the P01–P06 evidence, consolidate
> that evidence, and prepare the project for the student team's
> final report and presentation. The only files changed in P07 are
> documentation (`README.md`, `CLAUDE.md`) and this report —
> disclosed in section 16.
>
> Date: 2026-09-08. Environment: Windows 11 (10.0.26200),
> Python 3.12.0, cryptography 50.0.1, pytest 9.1.1.

---

## 1. Executive Summary

The project is in a **consistent, verified final state**:

- The final source tree is byte-identical to the P06 end state
  (checksum-verified); the P06 NEW-1 fix is present in
  `common/crypto.py` exactly as documented and behaves as designed.
- Final test suite: **120 passed, 0 failed, 0 skipped** (~3.0 s).
- A final live end-to-end smoke test (device → gateway → cloud →
  reading stored → health → clean shutdown) passed in full.
- Every finding from P02 through P06 has a documented final status
  (section 5); no finding is left unaccounted.
- Documentation was audited against the final code and updated where
  stale (README test count, P05/P06 history, NEW-1/2/3 rows) —
  documentation-only changes, listed in section 16.
- Docker and CI remain honestly NOT VERIFIED (environment limits).
- No unsupported security claims exist anywhere in the project
  documentation (phrase scan, section 10).

**FINAL VERDICT: PASS WITH DOCUMENTED RESIDUAL RISKS** (section 15):
the selected security controls were implemented and independently
verified; NEW-1 was fixed and independently re-verified; the project
is explicitly not production-secure and retains documented
limitations.

## 2. Project Status

| Dimension | Status |
| --- | --- |
| Phases completed | P01 baseline → P02 review → P03 design → P04 implementation → P05 independent verification → P06 NEW-1 fix → **P07 final evaluation** |
| Source code | READY — final tree verified, no unreported changes |
| Tests | READY — 120 passed, 0 failed, 0 skipped, no skipped tests anywhere |
| Documentation | READY — README/CLAUDE.md audited and brought in line with the final code (P07) |
| Review evidence | READY — `review/P02`–`review/P06` present and internally consistent |
| Docker | NOT VERIFIED — Docker unavailable on this machine |
| CI | NOT VERIFIED — not a git repository |
| Student sign-off | PENDING — all P03 decisions were documented as proposals; the student team's formal ACCEPTED/MODIFIED/REJECTED record is still to be completed (course requirement) |

## 3. P01–P06 Development and Verification History

| Phase | What happened | Key artifact |
| --- | --- | --- |
| P01 | AI-generated baseline (39 tests) | `prompt/P01`, initial code |
| P02 | Technical review: 15 findings; live demos of replay acceptance, gateway/cloud crashes, unauthenticated key establishment | `review/P02` |
| P03 | Student-facing design proposals: fingerprint pinning (F-01), authenticated hello + fallback table (F-02/F-06), monotonic seq + AAD (F-05), handshake validation (F-03/F-04), session lifecycle (F-07), metric/health models; TLS/signatures/replay-windows explicitly rejected for scope | `review/P03` |
| P04 | Implementation with fail-first evidence (53 failed / 29 passed / 2 collection errors pre-fix); attack re-tests; 101 tests | `review/P04` |
| P05 | Independent verification: every P04 claim re-tested with external attacker tooling over real TCP — all PASS; **NEW-1 discovered** (wrong-length AEAD nonce → unhandled ValueError → thread crash + metric bypass); NEW-2/NEW-3 recorded; verdict PARTIAL PASS | `review/P05` |
| P06 | NEW-1 fixed with fail-first reproduction (18 of 19 new tests failed pre-fix); minimal nonce validation in `common/crypto.py`; 120 tests; independent TCP re-attack clean; all prior controls re-verified; verdict PASS with documented residual risks | `review/P06` |
| P07 | Final evaluation: state verified, documentation consolidated, evidence matrix produced (this report) | `review/P07` |

The chain the course requires is fully preserved:
AI-generated baseline → AI review → student-visible design
proposals → implementation → independent verification → correction →
final evaluation. The student team's own evaluation record (their
ACCEPTED/MODIFIED/REJECTED decisions) remains to be written by the
students themselves — nothing in this chain presents AI output as
automatically correct.

## 4. Final Test Results

```text
$ .venv/Scripts/python.exe -m pytest -q
120 passed in 3.00s        (0 failed, 0 skipped)
```

Test inventory across phases (actual recorded results):

| Phase | Test Result | Purpose |
| --- | --- | --- |
| P01 | 39 passed | Baseline |
| P02 re-run | 39 passed (0.07 s) | Baseline confirmed during review |
| P04 fail-first | 53 failed / 29 passed / 2 collection errors | Security tests BEFORE implementation |
| P04 final | 101 passed (0.53 s) | Post-implementation |
| P05 | 101 passed (0.88 s baseline / 0.58 s after attacks) | Independent verification |
| P06 fail-first | 18 failed / 1 passed (of the 19 new NEW-1 tests) | NEW-1 reproduction before fix |
| P06 final | 120 passed (3.04 s) | NEW-1 remediation |
| P07 final | **120 passed (3.00 s)** | Final verification |

The count grew 39 → 101 → 120 because regression tests were added in
P04 (handshake, AAD, hello policy, replay, pinning, session,
device keys) and P06 (nonce validation). A higher test count does
NOT mean the project became "safer" — it means more behavior is
asserted. No test was deleted or weakened to obtain a green run at
any phase (verified per-phase; no `@pytest.mark.skip` anywhere).

## 5. Final Security Finding Matrix

| ID | Original Finding | Final Status | Evidence | Remaining Risk |
| --- | --- | --- | --- | --- |
| F-01 | Unauthenticated ML-KEM key establishment (MITM) | Fixed and Verified | Unit tests (test_pinning); P05 live key-substitution attack: substituted valid key rejected 6/6, no session, no encaps; P06 re-test unchanged | Security depends on trusted pre-provisioned fingerprint (env); no full PKI; cloud does not authenticate gateways |
| F-02 | Capability spoofing / downgrade | Fixed and Verified | Unit tests (test_hello_policy); P05 live: all 8 manipulation variants rejected, exactly 1 fallback for 1 valid hello; P06 re-test unchanged | Hello replay re-triggers fallback (observable, benign); no universal downgrade protection claimed |
| F-03 | Gateway crash on malformed handshake | Fixed and Verified | Unit tests (test_handshake, test_session); P05 live: 10 malformed handshakes (8 classes) → controlled errors, gateway alive, 0 tracebacks; P06 re-test unchanged | Retry-loop log spam under flood (F-12 deferred) |
| F-04 | Cloud thread crash on malformed encaps | Fixed and Verified | Unit tests; P05 live: 5 variants → controlled close, 0 tracebacks, errors +5, service available after; P06 re-test unchanged | — (beyond normal flood DoS, F-12) |
| F-05 | Replay attack | Fixed and Verified | Unit tests (test_replay, test_aad); P05 live: exact replay rejected on BOTH hops, one copy stored, seq/device/session/AAD/ciphertext tampering all rejected; device counter persistence demonstrated; P06 re-test unchanged | Gateway/cloud restart amnesia (accepted, P03); no jump window (demonstrated); NOT perfect replay protection |
| F-06 | Static shared PSK / impersonation | Fixed and Verified | Unit tests (test_device_keys); P05 live: 6/6 accept/reject probes correct; P06 re-test unchanged | Educational registry model, not production provisioning; static keys, no rotation/revocation |
| F-07 | Wedged session after cloud failure | Fixed and Verified | Unit tests (test_session); P05 live: degraded after failed forward → auto reconnect with NEW session id → forwarding resumed → cloud evicts dead sessions; P06 re-test unchanged | No session expiry timers; device has no reconnect logic (deferred) |
| F-08 | Metrics units/semantics | Fixed and Verified | Unit tests (test_metrics); P05 live counter deltas + units (`bytes`/`s`); P06 re-test unchanged | Device-side metrics deferred; metrics in-memory only |
| F-09 | Duplicated AEAD code | Fixed and Verified | P04 refactor to `_aead_encrypt`/`_aead_decrypt` core; old crypto tests unchanged; P05 crypto scenario 19/19 | None |
| F-10 | Config duplication | Fixed and Verified (documentation policy) | Cross-reference comments in `common/config.py` + `docker-compose.yml` (inspected P04–P07) | Comments can go stale (discipline-dependent) |
| F-11 | Key lifecycle | Partially Addressed | Eviction implemented and verified (P05: cloud active_sessions 1→0 on gateway death); rotation/zeroization deferred by P03 decision | Static keys; no zeroization (Python limitation); no expiry timers |
| F-12 | Threads / timeouts / rate limiting | Deferred | P03 decision (scale justification) — no code change | A determined local attacker can hold threads at demo scale |
| F-13 | Health endpoint semantics | Fixed and Verified | P05 live: ok → degraded/connecting → ok tracks state machine; cloud /health reports sessions/readings | Unauthenticated endpoint; no perfect real-time liveness (see NEW-3) |
| F-14 | Dependency drift | Fixed and Verified | `requirements.txt` pins cryptography==50.0.1, pytest==9.1.1; installed versions verified P05/P07 | Pinning ages over time; no guarantee about future cryptography versions |
| F-15 | Truncated-message error text | Fixed and Verified | Unit tests (test_protocol); P05 robustness battery: "connection closed mid-message" logged correctly | None |
| NEW-1 | Wrong-length AEAD nonce → unhandled ValueError, thread crash, metric bypass | **Fixed and Independently Verified** | P05 discovery (3 live tracebacks, metric delta 0); P06 fail-first (18/19 new tests failed); fix in `common/crypto.py`; 19 regression tests; 120/120 suite; independent TCP attack: controlled close, 0 tracebacks, errors +1 / messages_rejected +1, valid traffic after | None (input validation added at protocol boundary) |
| NEW-2 | `/health` absent during initial establishment retry loop | Deferred / Accepted Limitation | P05 observation; P06 scope decision — NOT fixed; README limitation #13 | Observability gap during startup outage |
| NEW-3 | No keepalive; dead cloud detected only on next forward failure | Accepted Operational Limitation | P05 observation; P06 scope decision — design kept; README limitation #14 | Health can lag reality for an idle interval |

Statuses are used per P07 section 7: "Fixed and Verified" only
where test or independent-verification evidence exists (P04–P06).

## 6. Security Evidence Classification

### A. Code inspection
Crypto API usage (ML-KEM-768/HKDF/ChaCha20-Poly1305 via
`cryptography` only), pin/registry configuration, protocol
structure, session lifecycle, F-09/F-10/F-11 remainder, F-12,
NEW-2/NEW-3 mechanisms, secret-handling policy (no key material in
logs or endpoints).

### B. Automated tests
120 pytest tests: crypto, protocol, hello policy, replay, AAD,
handshake, pinning, session (real TCP vs fake cloud), device keys,
metrics, sensor, and NEW-1 nonce validation (unit + real-TCP
gateway/cloud integration).

### C. Independent live verification
P05 external attack harness (`D:\Code\Claude\p05-verify\`, outside
the project tree): F-01…F-13 attack scenarios, robustness battery,
crypto checks, secret-leakage scans — all against real processes
with attacker-constructed inputs. P06 independent nonce re-attack.
P07 final end-to-end smoke test.

### D. Environment-limited verification
Docker compose: NOT VERIFIED (Docker not installed). GitHub Actions
CI: NOT VERIFIED (not a git repository). Both documented in every
report from P02 onward and never simulated.

## 7. Student Security Decisions

Recorded from `review/P03` (all decisions are documented as
**proposals prepared for the student team**; formal student
confirmation is still pending — see section 2):

| Decision | Alternatives Considered | Selected Design | Reason |
| --- | --- | --- | --- |
| F-01 authentication | TLS / signature-bound keys / fingerprint pinning | ML-KEM public-key SHA-256 fingerprint pinning (fail-closed) | Smallest mechanism that makes the ML-KEM exchange authenticatable while keeping it visible for the course demo |
| F-02 fallback policy | unrestricted fallback / strict policy | Authenticated hello + explicit reject table: fallback ONLY for known devices with valid legacy-only tags | Prevents silent downgrade; downgrade attempts are observable |
| F-03/F-04 validation | broaden catches / field validation | Uniform handshake field validation → ProtocolError | Controlled errors instead of crashes; one policy on both sides |
| F-05 replay | replay window / session counters / monotonic sequence | Monotonic per-device sequence + AEAD AAD binding + device-side counter persistence | Simplest mechanism that closes the demonstrated attack and demonstrates AAD binding |
| F-06 keys | shared PSK / per-device keys / provisioning system | Per-device key registry (simulated provisioning) | Enables hello authentication; kills cross-device impersonation |
| F-07 session | minimal state clearing / full lifecycle | 5-state machine, per-attempt session ids, reconnect, cloud-side eviction | Makes failure behavior demonstrable and health truthful |
| F-08/F-13 | renames only / defined semantics | Unit-tagged metrics table; derived health status | Analysis-ready numbers; health reflects the state machine |
| NEW-1 | broad `except Exception` / input validation | Nonce-length validation before the AEAD call (ProtocolError / AuthenticationError) | Minimal targeted fix; no masking of programming errors |

These are explicitly **not** production-grade architectural
decisions: they were selected for the project's scope and
educational objectives, and the alternatives rejected are documented
in `review/P03` (§4/§16).

## 8. Final Architecture Verification

Inspected against the final code (P07), matching the P03 target
architecture:

- **Device** (`device/`): generates simulated readings; claims the
  legacy `chacha20-poly1305` capability only; builds AEAD-tagged
  hellos and seq-bound encrypted readings; persists its sequence
  counter (`device/state.py`); performs NO ML-KEM and no from-scratch
  crypto. ✓
- **Gateway** (`gateway/`): accepts device TCP connections;
  validates and authenticates hellos (per-device registry lookup
  first, then tag verification); applies the P03 fallback decision
  table; enforces per-device replay via `ReplayGuard`; establishes
  the ML-KEM-768 session with fingerprint-pinned cloud key
  (`cloud_channel.py` 5-state machine); re-encrypts and forwards
  readings with session-id AAD; invalidates + reconnects on send
  failure; reports truthful health. ✓
- **Cloud** (`cloud/`): ML-KEM-768 decapsulation; session registry
  with disconnect eviction; protected-reading decryption with
  session-id AAD; its own per-device replay guard (defense in
  depth); bounded in-memory store; `/health` and `/readings`. ✓
- **Shared** (`common/`): JSON-lines protocol with validation
  helpers, AEAD/HKDF/ML-KEM wrappers over `cryptography` only,
  unit-aware metrics, ReplayGuard, health server, logging with a
  no-secrets policy. ✓

No architecture drift found; no presentation rewrite performed.

## 9. P06 NEW-1 Final Verification

`common/crypto.py` (final code, re-read in P07):

- `_aead_decrypt`: decoded nonce length checked against
  `NONCE_LENGTH` **before** `ChaCha20Poly1305.decrypt()`; wrong
  length → `ProtocolError("invalid nonce length (N)")` — length
  only, no nonce bytes. ✓
- `verify_hello_auth`: same check inside the existing auth-field
  validation block → converted to `AuthenticationError` by the
  existing mechanism → the established hello-rejection path. ✓
- Confirmed: no broad `except Exception` added; no new cryptographic
  primitive; no algorithm change; no secret logging; no raw nonce
  logging; no unrelated source changes (tree checksum-identical to
  P06 except the P07 documentation updates, section 16). ✓
- Behavior evidence: 19/19 new tests; 120/120 suite; P06 independent
  TCP attack (0 tracebacks, exact counter deltas, valid traffic
  after). ✓

## 10. README and Documentation Audit

P07 audit of `README.md` against the final code:

- **Architecture:** matches the actual three-component system. ✓
- **Security controls:** match the final code; the P04 control table
  now notes P05 verification and the NEW-1 fix. ✓ (updated)
- **Limitations:** all present — no TLS, limited authentication
  model, educational per-device key registry, replay-state restart
  limitation, no keepalive, NEW-2, NEW-3, Docker/CI, and the other
  P03/P04 accepted limitations (now 14 rows). ✓ (updated)
- **Testing:** reported 101 → corrected to the final **120 passed**
  (P06). ✓ (updated)
- **P06:** NEW-1 resolution now mentioned in the fixed-list and the
  AI-development chain table (P05/P06 rows added). ✓ (updated)
- **Security claims:** phrase scan across README, CLAUDE.md and all
  review reports found **no** unsupported wording ("fully secure",
  "production ready", "immune", "perfect replay protection" — the
  only "production-ready" hit is in the required negative sentence
  "must NOT be presented as secure or production-ready"). ✓
- **Test gaps:** corrected — real-socket integration tests now exist
  (P04/P06); remaining gaps honestly listed. ✓ (updated)

`CLAUDE.md`: updated to reflect the phase history (P02–P06 complete,
student review still pending) while keeping the "not secure /
not production-ready" warning. `requirements.txt` was checked and
**not** changed: it pins `cryptography==50.0.1` and `pytest==9.1.1`
with a comment on ML-KEM API stability, and the installed versions
match. The README does not claim compatibility with future
`cryptography` versions.

All P07 documentation changes are listed in section 16 and were
documentation-only (no code, test, Docker, CI changes).

## 11. AI-Assisted Development Evidence

The project documentation clearly separates AI-generated proposals
from student-owned decisions and shows the full critical-use chain:

- **P01:** the initial ML-KEM API assumption (`ml_kem`) was wrong
  for the installed library and was corrected after live testing
  (`mlkem`, cryptography 50.0.1) — recorded in `review/P02` §12.
- **P02:** the AI review's findings were validated by live
  demonstrations (replay accepted, crashes reproduced) — appendix
  evidence preserved.
- **P03:** alternatives were evaluated and specific designs selected
  as proposals; several P02 recommendations were explicitly rejected
  for scope (TLS, replay windows, thread pools) — §16.
- **P04:** fail-first testing exposed real implementation and
  test-harness bugs before fixes (the 101st regression test came
  from a live-integration bug unit tests missed) — §13.
- **P05:** independent verification (not trusting P04) discovered
  NEW-1 and two documented limitations (NEW-2/NEW-3).
- **P06:** NEW-1 was reproduced fail-first before the minimal fix.
- **P07:** final audit re-verified the state from code, not from
  prior reports.

Nothing in the project presents AI output as automatically correct;
the student team's own decision record remains to be filled in
(course requirement, flagged in section 2).

## 12. Docker and CI Status

```text
Docker:  NOT VERIFIED — Docker unavailable on this machine
         (docker command not installed; compose never executed;
          inspection-reviewed only since P02)

CI:      NOT VERIFIED — CI environment unavailable / project is not
         a git repository (workflow inspected only; it runs pip
         install + pytest on Python 3.12 and fails the build on test
         failure by construction)
```

No claim that Docker/compose/CI work is made anywhere in the
project. These statuses are consistent across P02–P07.

## 13. Remaining Risks and Limitations

Final, verified list (README section 7, 14 rows):

1. No TLS — metadata visible; tampering detected only where
   tags/pins apply (Accepted).
2. Cloud does not authenticate gateways (Deferred).
3. Static demo keys; no rotation/revocation/expiry (Accepted).
4. Gateway/cloud restart loses replay state until devices re-send
   (Accepted, P03).
5. No sequence jump window — demonstrated live (Accepted).
6. Hello replay re-triggers fallback activation (Accepted).
7. Device has no reconnect logic (Deferred).
8. No rate limiting / thread caps (Accepted at demo scale).
9. No key zeroization — Python limitation (Accepted).
10. Simulated provisioning; manual pin provisioning (Accepted).
11. Docker compose never executed (NOT VERIFIED).
12. CI never executed (NOT VERIFIED).
13. NEW-2: `/health` absent during initial establishment retry loop
    (Deferred — P06 scope decision).
14. NEW-3: no keepalive; dead-cloud detection is
    send-failure-driven (Accepted operational limitation).

Plus: the student team's formal decision confirmation is pending;
the project is an educational simulation, not a production system.

## 14. Final Security Claims

> The project demonstrates a tested migration simulation for
> selected post-quantum security controls in a legacy edge-cloud
> environment. The selected controls were implemented and
> independently verified through automated tests and live TCP-level
> testing. Several production-grade security mechanisms remain
> outside the project scope.

Explicitly NOT claimed: "the system is secure", "production ready",
"all vulnerabilities fixed". The verdict below is the only final
claim made, and it carries its limitations inline.

## 15. Final Verdict

```text
FINAL VERDICT: PASS WITH DOCUMENTED RESIDUAL RISKS

PASS:
Selected security controls (F-01, F-02, F-03/F-04, F-05, F-06,
F-07, F-08, F-13, plus F-09/F-10/F-14/F-15) were implemented and
independently verified. NEW-1 was fixed and independently
re-verified. No critical inconsistency was found between the
final code, the tests, and the documentation.

RESIDUAL RISKS:
The project is not production secure. The accepted P03/P04
limitations remain (section 13).

ENVIRONMENT LIMITATIONS:
Docker and CI were not verified.

KNOWN LIMITATIONS:
NEW-2 and NEW-3 remain documented. The P03/P04 accepted
limitations remain. Student formal sign-off remains pending.
```

## 16. Submission Readiness

| Item | Status |
| --- | --- |
| Source code | **READY** |
| Tests | **READY** (120 passed, 0 failed, 0 skipped) |
| README | **READY** (audited and updated in P07) |
| Review evidence | **READY** (`review/P02`–`review/P07`) |
| Docker | **NOT VERIFIED** |
| CI | **NOT VERIFIED** |
| Final report | **READY** (this document; the student team writes their own submission report) |
| Presentation/demo | **NEEDS PREPARATION** (demo script in README §4; live smoke procedure verified in P07) |

### P07 file changes (disclosure, P07 section 25)

- `README.md` — documentation-only: final test count (120), P05/P06
  history, NEW-1 in the fixed-list, limitation rows 13/14 (NEW-2/
  NEW-3), corrected test-gap list, AI-chain table extended.
- `CLAUDE.md` — documentation-only: phase-history sentence updated;
  "not secure / not production-ready" warning preserved.
- `review/P07 - Final Project Evaluation & Evidence Consolidation.md`
  — created (this report).
- **No source code, test, Docker, CI, or requirements changes.**
- No hidden changes: tree checksums confirm the source is otherwise
  byte-identical to the P06 end state; `review/P05` is intact and
  unaltered; no security test was deleted; no test is skipped; no
  unsupported claim was added; no unrelated feature was added.

## 17. Recommended Final Deliverables

**Required submission files:**

```text
common/            device/            gateway/            cloud/
tests/             README.md          CLAUDE.md           requirements.txt
pytest.ini         .gitignore
Dockerfile.device  Dockerfile.gateway Dockerfile.cloud    docker-compose.yml
.github/workflows/ci.yml
review/P02 - Baseline Technical Review.md
review/P03 - Student Security Evaluation & Design Decisions.md
review/P04 - Security Implementation & Verification.md
review/P05 - Independent Security Verification & Re-test.md
review/P06 - NEW-1 Fix & Final Security Verification.md
review/P07 - Final Project Evaluation & Evidence Consolidation.md
prompt/            (the course's phase prompts — the assignment chain)
```

**Evidence / archive files (optional, if the course requires the
full AI-interaction record):**

```text
review/            (already listed above — the primary evidence)
p05-verify/        (external attack harness outside the tree,
                    D:\Code\Claude\p05-verify\ - not part of the
                    repository; include only if the course asks for
                    the raw attack tooling)
```

**Temporary verification files (do NOT submit unless required):**

```text
device_state/      cloud_state/      .pytest_cache/     .venv/
(D:\Code\Claude\p05-verify\logs and evidence are harness
workspace files outside the repository.)
```

Runtime state and caches are gitignored by design; the external
attack harness lives outside the project directory and is not a
repository file.

---

## Final output (P07)

- **Final pytest:** 120 passed, 0 failed, 0 skipped (~3.0 s).
- **Final smoke test:** startup + ML-KEM session → device
  hello/reading → reading stored in cloud → health ok/established
  (units correct) → clean shutdown — all verified live in P07.
- **Final security regression:** F-01/F-02/F-03/F-04/F-05/F-06/F-07/
  NEW-1 — **previously independently verified** (P05/P06, real TCP,
  external harness); source tree unchanged since P06
  (checksum-verified), so per P07 §18 that evidence is relied on;
  the happy path was **re-tested during P07** (smoke test above).
- **Finding matrix:** section 5 (F-01–F-15, NEW-1/2/3, all with
  evidence and remaining risk).
- **Docker:** NOT VERIFIED — Docker unavailable. **CI:** NOT
  VERIFIED — not a git repository.
- **Files changed in P07:** README.md and CLAUDE.md
  (documentation-only) + this report; nothing else.
- **Final verdict:** PASS WITH DOCUMENTED RESIDUAL RISKS.
