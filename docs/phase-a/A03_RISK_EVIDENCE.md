# A-03: Risk mapping and current handshake reproductions

Date: 2026-10-16 (Asia/Singapore). Source HEAD: `681986bc0119d51913140575f98720c90fb378ac`;
execution branch: `codex/phase-a-validation`. Existing application source is unchanged.
Status: risk/evidence mapping and bounded reproductions completed; the current
custom transport fails the engineering security selection gate. This is a
validation result, not remediation, release acceptance, or independent human review.

## Current evidence and reproduction

The observations below were completed before the output-directory guard fix.
Do not rerun them merely to reconstruct context. If explicitly needed for a
later defensive regression, use a fresh process and a **new external directory**:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/security_probe.py --raw-dir "$env:TEMP/pqc-phase-a-security-new"
```

Runtime: Python 3.12.0, cryptography 50.0.1. The completed run exited 0 and all
14 observation assertions were true. **Exit 0 means the documented weaknesses
and their negative controls reproduced; it does not mean security passed.**

After cross-review, the raw-output guard was strengthened to resolve the path
and reject an existing directory or any directory inside the checkout before
writing. Targeted CLI rejection checks passed without rerunning the security
observations: an in-checkout target stayed absent and an existing external
directory's sentinel and entries were unchanged. The original evidence's
`source_sha256` refers to the observed pre-guard script, preserved externally
as `security-runtime/security_probe.observed.py` with that same hash. The
current script differs by this output-safety fix; the stored dynamic result
was not overwritten or relabelled as a run of the changed script.

- Sanitized machine-readable observations: [security-result.json](evidence/security/security-result.json).
- Probe: [security_probe.py](../../scripts/phase_a/security_probe.py).
- Complete observation JSON and cloud warning log: external preserved artifact
  directory `D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z\security-runtime`.
  These are raw runtime observations, not a packet capture. No private key,
  PSK, shared secret, or traffic key is logged.
- [A-01 current baseline evidence](evidence/baseline/result.json) records 136
  existing tests passing and three real device-CLI readings through the cloud.
  This is separate evidence; those tests are not counted as new A-03 probes.

The probe owns three ephemeral loopback listeners: one bounded cloud handler
worker and two fake-cloud controls. It sends seven sequential cloud connections,
five protected readings, and uses fresh synthetic identities and in-memory keys.
It changes only its own child-process environment. It does not read existing
cloud/device state, demo credentials, or contact a remote service. The cloud
worker replaces the unlimited accept/thread loop with seven serial accepts;
the original `CloudServer._handle`, authentication, handshake, replay guard,
metrics and store execute unchanged. This harness cannot establish production
listener/thread-limit safety. Worker cleanup kills only its owned process.

## New findings

### A03-01 — Replayed gateway authentication permits a fresh attacker session

**High impact; dynamically reproduced over loopback TCP.** The attacker receives
one previously generated legitimate `mlkem_request_pubkey` request and no PSK.
It reuses the identical bytes, then independently encapsulates to the public
cloud ML-KEM key with a new session identifier. The cloud accepts it and stores
attacker-chosen telemetry. Random auth nonces authenticate the message but are
not freshness checks when the receiver neither challenges nor remembers them.

Observed sequence: a valid control stores sequence 1 (store count 1); a replayed
request with a new KEM/session stores 99999 (count 2); a legitimate sequence 2
is rejected (count remains 2); another replayed request stores 100000 (count 3).
The last two steps reproduce the BF-06/BF-07 suppression/replacement mechanism
through a newly demonstrated prerequisite. This does not assert the historical
P08 no-auth request test was false: missing credentials still fail.

Negative controls: an invalid tag and unknown gateway identity are each rejected
before any cloud public-key reply. Each increments `messages_rejected` once.
The registry is empty after every one of the seven connections closes.

Current references: `common/crypto.py:179`, `common/crypto.py:197`,
`common/protocol.py:139`, `cloud/cloud.py:128`, `common/replay.py:23`.
Impact requires observing one valid authentication request and reaching the
cloud listener; the current plaintext TCP carries that request in the clear.
No interception against another process or network was performed.

### A03-02 — Gateway proof does not bind the following KEM/session transcript

**High impact; dynamically reproduced in the A03-01 chain, not counted as a
second independent exploit.** The authenticated claim contains only
`gateway_id` and a domain-separation scope. It does not bind session ID, cloud
identity/key, KEM ciphertext or a fresh server challenge. The replay client
chooses each session and KEM ciphertext and deliberately sends a different
`gateway_id` in `mlkem_encaps`; the cloud accepts and attributes the connection
to the identity from the first request. `parse_mlkem_encaps` ignores that later
gateway ID. Checking that redundant field alone would not repair transcript
binding or freshness.

Current references: `common/protocol.py:139`, `cloud/processing.py:46`,
`cloud/cloud.py:150`, `cloud/cloud.py:162`, `gateway/cloud_channel.py:99`.
This is distinct from application-payload session-ID AAD: that existing AAD
still rejects moving an encrypted payload to a different session key/context.

### A03-03 — Established state precedes any cryptographic key confirmation

**Medium-to-high availability/readiness risk; dynamically reproduced on both
sides.** A fake cloud with only the correctly pinned public key, without its
private key and without performing decapsulation, sends a structurally valid
plaintext `mlkem_established` reply. The unchanged gateway reports established
and sends a protected payload. An incorrect session ID in the same reply is
rejected in the negative control. This demonstrates that pinning a public key
does not prove the responding peer possesses its private key.

Separately, a correct-length substituted KEM ciphertext causes the actual cloud
to derive a different secret but still increment `mlkem_sessions_established`
and send an established reply. The following protected message fails AEAD and
is rejected; store count stays 3. Thus payload authentication still protects
that ciphertext, but established/readiness does not prove keys agree.

Current references: `gateway/processing.py:123`, `gateway/cloud_channel.py:136`,
`cloud/cloud.py:153`, `cloud/cloud.py:161`, `cloud/cloud.py:166`.
The fake responder receives ciphertext, not plaintext. This result alone does
not demonstrate confidentiality loss. No forged protected plaintext was accepted
using a wrong session key.

### A03-04 — Static cloud ML-KEM private-key disclosure decrypts old transcripts

**High confidentiality impact conditional on later private-key disclosure;
dynamically reproduced with current crypto wrappers on synthetic transcripts.**
Two independently encapsulated sessions are archived as KEM ciphertext,
session ID and AEAD envelope. Once the same long-lived cloud private key is
available, decapsulation + the current HKDF recovers both messages (2/2).
An unrelated private key fails AEAD on both (2/2). The experiment uses only
fresh keys in memory and does not read, disclose, or attack the existing
`cloud_state/cloud.key`. It is a recorded-transcript cryptographic experiment,
not a live packet capture or a demonstrated key-extraction attack.

Current references: `cloud/cloud.py:206` persists/reuses the key;
`common/crypto.py:225`, `common/crypto.py:274`, `common/crypto.py:291`;
`common/protocol.py:124`. Evicting session keys does not stop re-derivation
from recorded KEM ciphertexts and that static private key. This identifies a
protocol property, not a failure of ML-KEM's underlying computational security.

### A03-05 — Authenticated device metadata does not bind inner reading identity/sequence

**High impact; dynamically reproduced independently by the A-05 device peer.**
The peer knows one enrolled device credential, not a gateway credential. After
104 ordinary readings are stored, it sends authenticated outer device metadata
for that enrolled device with sequence 105, but encrypts a reading for an
unassigned inner device with inner sequence 1. That reading is stored (count
105). An outer sequence 106 carrying the enrolled device's inner sequence
999999 is then stored (count 106). The following ordinary outer/inner sequence
107 is forwarded by the gateway but rejected by the cloud (count remains 106).
This is a separate device-credential attack path from A03-01 gateway-auth replay.

Evidence: [A-05 independent results](evidence/legacy/legacy-result.json),
`scripts/phase_a/legacy_probe.py:193`; raw observations at
`D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z\legacy-runtime-01\legacy-results.json`.
The peer independently constructs wire JSON and AEAD rather than reusing the
application message-building functions. Its wrong-key, unknown-device, exact
replay and outer-sequence-tampering controls are rejected. This makes the
inner/outer inconsistency materially different from simply altering an
authenticated outer sequence without its key.

Current application references: `gateway/processing.py:156` authenticates the
outer device ID and sequence but does not compare them with the inner fields;
`common/protocol.py:149` checks field presence rather than strict schema;
`gateway/gateway.py:138` tracks the outer sequence while `cloud/cloud.py:190`
tracks the inner identity and sequence. The independent A-05 run supplies the
dynamic proof; the A-03 probe does not claim to have rerun it.

### A03-06 — Gateway identities have no device-authorization scope

**High impact for compromised/overprivileged gateways; static assessment.**
The cloud stores the gateway ID with the session but `_receive_readings` accepts
the device ID supplied inside any valid session payload without checking an
authorized-device set. The A03-01 probe stores a synthetic device without any
authorization registration; there is no implemented authorization policy against
which a separate allow/deny control can be run. An engineering authorization
claim remains unverified until Phase B defines and enforces that policy.

Current references: `cloud/cloud.py:47`, `cloud/cloud.py:162`,
`cloud/cloud.py:173`, `cloud/processing.py:59`. A03-05 separately proves a
device-side metadata inconsistency; it does not prove a nonexistent
gateway-to-device authorization policy passes its own allow/deny controls.

## P02–P08 finding/evidence matrix

Each entry states the historical disposition, current mechanism, and the
boundary of this run. Historical “fixed/verified” labels below describe the
specified historical check, not blanket engineering closure. Review sources:
[P02](../development/initial/P02-Baseline-Technical-Review.md),
[P03](../development/initial/P03-Security-Evaluation-and-Design-Decisions.md),
[P04](../development/initial/P04-Security-Implementation-and-Verification.md),
[P05](../development/initial/P05-Independent-Security-Verification.md),
[P06](../development/initial/P06-Nonce-Validation-and-Security-Verification.md),
[P07](../development/initial/P07-Evaluation-and-Evidence-Consolidation.md),
[P08](../development/initial/P08-Adversarial-Testing-and-Remediation.md).

- **F-01, unauthenticated ML-KEM key establishment:** P03 chose fingerprint
  pinning; P04 implemented; P05/P06 independently rejected key substitution;
  P07 consolidated. Current `gateway/processing.py:134` fails closed on a
  missing/wrong pin. Existing `tests/test_pinning.py` retains those controls.
  A03-03 dynamically proves no private-key possession/key confirmation despite
  a matching pin. Pin provisioning, TLS authentication and deployment closure
  are not established by the historical substitution test.
- **F-02, capability spoof/downgrade:** P03 policy and P04 authenticated hello
  verified P05/P06; current `gateway/processing.py:77`, `common/crypto.py:136`;
  `tests/test_hello_policy.py`. Hello replay remains possible; no new dynamic
  capability/downgrade battery in A-03. The configured modern-device path still
  rejects rather than pretending to support it.
- **F-03, malformed cloud reply crashes gateway:** P04 validators verified
  P05/P06; current `gateway/processing.py:107`, `:123`,
  `gateway/cloud_channel.py:74`; `tests/test_handshake.py`, `test_session.py`.
  This run dynamically rejects the wrong-session reply; other malformed
  variants remain existing-test/historical evidence.
- **F-04, malformed encaps crashes cloud handler:** P04 field/length checks
  verified P05/P06; `cloud/processing.py:46`, `common/protocol.py:59`;
  `tests/test_handshake.py`. This run uses a correctly sized substituted
  ciphertext: controlled AEAD rejection but premature established state
  (A03-03). It does not repeat the full malformed-field battery.
- **F-05, reading replay:** P04 monotonic sequence + AAD, P05/P06 verified
  exact replay and field tampering; `common/replay.py:23`,
  `gateway/gateway.py:138`, `cloud/cloud.py:190`, `tests/test_replay.py`,
  `test_aad.py`. Current dynamic poisoning/suppression repeats BF-03B semantics
  and bypasses handshake freshness through A03-01. Restart state remains
  volatile; transport replay protection and business deduplication are separate.
- **F-06, shared device PSK:** P04 per-device keys verified P05/P06;
  `common/config.py:100`, `:106`, `gateway/gateway.py:75`,
  `tests/test_device_keys.py`. P08 moved production credentials to config;
  committed demo keys still require an explicit deployment prohibition. No
  fresh multi-device key-isolation battery is claimed here.
- **F-07, wedged cloud session:** P04 state machine/reconnect/eviction verified
  P05/P06; `gateway/cloud_channel.py:74`, `:170`, `:181`,
  `cloud/cloud.py:121`, `tests/test_session.py`. Current probe verifies all
  seven cloud disconnects leave zero active sessions. No crash/reconnect,
  durable delivery, expiry or heartbeat acceptance was performed here.
- **F-08, metrics semantics/units:** P04 unit-tagged aggregates/counters,
  P05/P06 verification; `common/metrics.py`, `tests/test_metrics.py`.
  Current snapshots show intended rejection/processing deltas and seconds
  units. A03-03 shows established count is not proof of key confirmation;
  socket send/forward count is not durable delivery.
- **F-09, duplicated AEAD code:** P04 shared core verified P05 crypto checks;
  `common/crypto.py:73`, `:86`, thin wrappers at `:114`–`:129`,
  `tests/test_crypto.py`. Current crypto experiment exercises those wrappers;
  no additional refactor is needed for this finding.
- **F-10, config duplication:** P03/P04 selected an authority-comment policy;
  `common/config.py:1`, `docker-compose.yml`. Historical documentation-level
  closure is not a generated single source or deployment drift test. Current
  state: static documentation mechanism; no deployment drift verification.
- **F-11, key lifecycle:** P04 disconnect eviction (verified P05/P06), remainder
  deferred; `cloud/cloud.py:56`, `:121`, `common/crypto.py:225`.
  Current dynamic eviction passes; A03-04 demonstrates no forward secrecy
  under static KEM private-key disclosure. Rotation, expiry, revocation,
  permissions, zeroization and backup secrecy remain outside current closure.
- **F-12, resource exhaustion:** P03 deferred; P08 BF-02 measured thread growth;
  current `cloud/cloud.py:82`, `:93`, `:99`, `gateway/gateway.py:45`, `:56`,
  `:61`. One thread per connection and 60-second timeout remain. Static
  mechanism confirmed; no flood is rerun. The bounded probe harness avoids
  this risk and therefore is not its remediation.
- **F-13, health semantics:** P04 derived state verified P05/P06;
  `gateway/gateway.py:179`, `common/health.py:16`, `tests/test_metrics.py`.
  NEW-2/NEW-3 and unauthenticated endpoints remain. A03-03 dynamically proves
  an established predicate alone can be misleading. No health endpoint is
  opened by the A-03 harness.
- **F-14, dependency drift:** P04 pinned requirements; P05/P07 checked installed
  versions; current `requirements.txt` pins cryptography 50.0.1 and pytest
  9.1.1. Probe records Python 3.12.0 and cryptography 50.0.1. This is current
  local runtime evidence, not current dependency vulnerability review,
  container-build or Linux TLS support evidence.
- **F-15, truncation message:** P04 split oversized/truncated errors, verified
  P05 robustness; current `common/protocol.py:89`, `tests/test_protocol.py`.
  Static branch present; no new truncation probe in A-03.
- **NEW-1, wrong AEAD nonce length crash:** discovered P05; P06 fail-first
  18/19 failures then 19/19 regression tests; consolidated P07. Current
  `common/crypto.py:86`, `:156`, `:197`, `tests/test_nonce_validation.py`.
  Static validation remains; A03 uses valid-size nonces and makes no new
  exhaustive nonce-length runtime claim.
- **NEW-2, no health during startup reconnect:** accepted P06/P07;
  `gateway/gateway.py:176` blocks before health initialization at `:179`.
  Static limitation remains; not dynamically retested here.
- **NEW-3, no proactive cloud failure detection:** accepted P06/P07;
  `gateway/cloud_channel.py:69`, `:151` detects a later write failure.
  Static limitation remains; idle half-open behavior not retested here.
- **BF-01, cloud lacks gateway auth:** P08 added request MAC and verified
  missing/unknown/bad credentials; current `cloud/cloud.py:128`,
  `common/crypto.py:179`, `tests/test_gateway_auth.py`. Current bad-tag/unknown
  negative controls pass, but A03-01/A03-02 show the implemented mechanism
  does not establish fresh session-authentication closure.
- **BF-02, connection flood:** P08 deferred after bounded 150-connection
  historical reproduction; current static F-12 mechanism unchanged. Not
  re-flooded; deployment blocker until bounded resources are enforced.
- **BF-03A, credentials embedded in source:** P08 moved keys into config and
  marked demo material; current `common/config.py:75`, `:87`, `:124`, `:136`,
  demo JSON files and compose demo configuration; `tests/test_credential_config.py`.
  Probe uses fresh environment credentials rather than committed examples.
  Default demo enablement/provisioning/rotation are not engineering closure.
- **BF-03B, unlimited sequence advancement:** P08 analysed/deferred;
  `common/replay.py:23`. Current live seq=99999 acceptance followed by seq=2
  rejection reproduces it. A jump window alone would not solve authorization,
  resets, legitimate retries or durable business deduplication.
- **BF-04, device-ID timing side channel:** P08 negative/noisy timing result;
  current unknown-key vs bad-tag branches `gateway/gateway.py:75` and
  `gateway/processing.py:77`. Not reproduced in A-03, neither upgraded to a
  vulnerability nor asserted impossible in every environment.
- **BF-05, unauthenticated health/readings:** P08 documented;
  `common/health.py:28`, `:58`, `cloud/cloud.py:265`. Static wildcard bind,
  no authentication and readings route remain. No information-disclosure
  runtime probe was run because the harness does not expose that interface.
- **BF-06, targeted data blindness:** P08 historical no-auth chain blocked at
  BF-01 for its exact request. Current A03-01 uses captured valid auth, accepts
  99999, then suppresses sequence 2. **Current chain reproduced**, not fixed.
- **BF-07, false replacement continuity:** historical chain blocked at P08
  BF-01 for its exact request. Current replay chain accepts replacement
  sequence 100000. **Current injection/replacement mechanism reproduced**;
  no claim of a complete deceptive dashboard or measured human deception.

## Regression checklist and Phase B handoff

1. Preserve exact bad-tag, unknown-identity, missing/wrong pin, tampered payload,
   malformed fields, AEAD nonce-size, valid legacy fallback and disconnect
   eviction regressions. Their existing narrower expectations remain useful.
2. Replace the custom engineering transport through A-04 selection; require
   actual TLS 1.3 mutual authentication, transcript-bound key confirmation,
   mandatory hybrid failure behavior, and trusted credential provisioning.
   TLS selection alone does not fix device authorization or delivery semantics.
3. Add future transport regressions that reject replayed authentication and
   substituted session/key-exchange context. The current probe intentionally
   observes vulnerable behavior; update its explicit expectations when the
   transport changes rather than counting vulnerability reproduction as a fix.
4. In B-01 define and enforce gateway-to-device authorization. Validate inner
   device/sequence schema and authenticated metadata consistency at ingestion.
5. In B-02/B-03 separate authenticated transport, replay state and transactional
   business deduplication. A send counter or established session cannot count
   as durable acceptance; use A-05's agreed delivery/persistence contract.
6. Before engineering acceptance, rerun real target-runtime TLS/deployment
   evidence, restart/fault matrix, credential lifecycle, resource bounds and
   independent security review. None is established by this local harness.

## Cryptographic interpretation sources

The attack outcomes above are local experiment results. Their interpretation
does not invent new cryptographic primitives: [NIST FIPS 203, Section 3.3](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.pdf)
defines decapsulation from a decapsulation key and ciphertext. That operation
explains A03-04 given a reused disclosed key; the probe demonstrates the
project-specific consequences. [RFC 8446, Sections 2 and 4.4.4](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.4)
describes TLS Finished as authenticating the handshake transcript and confirming
key agreement. [RFC 8446, Appendix E.1](https://www.rfc-editor.org/rfc/rfc8446.html#appendix-E.1)
states forward-secrecy properties and their assumptions. These are design
references for A-04, not evidence that the current Python ML-KEM wrappers use
TLS or that a selected TLS deployment already satisfies them.
