# PQC Bridge — Legacy Edge-Cloud

> ⚠️ **AI-assisted project, student-owned.** The P01 baseline was
> AI-generated; P02 reviewed it; P03 defined the security design; P04
> implemented the approved fixes; P05 independently re-tested every
> security claim and discovered NEW-1; P06 fixed NEW-1; P07
> consolidated the evidence; P08 added adversarial testing, reproduced
> the BF-01..BF-07 findings, and remediated BF-01 (gateway
> authentication) and BF-03A (configuration-driven credentials). Every
> phase is documented in `prompt/` and `review/`. This is a university
> prototype — **not** production-grade secure software. Passing tests
> never means secure.

Project: **Legacy System Modernization for PQC & LLM-Assisted Development**
Course: Software Development, Maintenance & Operations

## 1. Architecture overview

Three components, pure software simulation, plain TCP with a tiny
JSON-lines protocol (no TLS — see section 7):

```
+------------------+      JSON/TCP      +-----------------------+      JSON/TCP      +------------------+
|  Legacy Device   |  ChaCha20-Poly1305 |      Edge Gateway     |  ML-KEM-768 +     |  Cloud Service   |
|  fake sensor,    |  per-device key +  |  (PQC-capable bridge) |  HKDF session key |  ML-KEM-768      |
|  NO ML-KEM       |  authenticated     |                       +------------------->+  decapsulation,  |
|                  |  hello + seq AAD   |                       |  fingerprint pin  |  in-memory store |
+------------------+------------------->+                       |  5002              +------------------+
                         5001
```

### Security controls implemented in P04 (P03-approved)

| Control | Mechanism | Finding |
| --- | --- | --- |
| Cloud authentication | Gateway pins the SHA-256 fingerprint of the cloud's ML-KEM public key (fails closed if unconfigured) | F-01 |
| Gateway authentication | Cloud verifies a per-gateway AEAD tag over the gateway's handshake request (unknown/invalid/tampered rejected) | BF-01 (P08) |
| Device authentication | Per-device keys (simulated provisioning registry) + AEAD-tagged hello | F-02, F-06 |
| Credential handling | Device/gateway keys are read from configuration (env or demo JSON), never from Python source | BF-03A (P08) |
| Fallback policy | Fallback ONLY for known devices with authenticated legacy-only hello; everything else rejected | F-02 |
| Replay protection | Monotonic per-device sequence bound into the AEAD AAD; enforced at gateway and cloud; device persists its counter | F-05 |
| Session lifecycle | 5-state machine, send-failure detection, automatic reconnect with a fresh session id, cloud-side eviction on disconnect | F-07 |
| Handshake hardening | Uniform field validation on all handshake messages (no more crashes on malformed input) | F-03, F-04 |
| Health truthfulness | Gateway `/health` reports `ok`/`degraded` + `cloud_state` | F-13 |
| Metrics | Units recorded per metric (s / bytes), `messages_rejected`, consistent error counting | F-08 |
| Reproducibility | `cryptography==50.0.1`, `pytest==9.1.1` pinned | F-14 |

### Fallback decision table (P03 section 8)

| Device claim | Gateway decision |
| --- | --- |
| legacy only + known device + valid hello tag | **FALLBACK** (logged warning; weaker posture) |
| `ml-kem-768` claimed | REJECT (modern path not implemented) |
| both capabilities | REJECT (never auto-downgrade) |
| unknown / no capabilities | REJECT |
| unknown device id | REJECT (no key to verify) |
| malformed hello / failed tag | REJECT + metric |

## 2. Project structure

```
├── common/            shared utilities
│   ├── config.py      hosts/ports, per-device + per-gateway key
│   │                  registries (F-06, BF-01), cloud key pin (F-01),
│   │                  state paths; credentials loaded from config
│   ├── demo_device_keys.json / demo_gateway_keys.json
│   │                  DEMO-ONLY credentials for the local run
│   │                  (real keys come from env/config — BF-03A)
│   ├── protocol.py    JSON-lines framing, field validation helpers,
│   │                  AAD construction (F-03/F-04/F-05/F-15)
│   ├── crypto.py      `cryptography` wrappers: AEAD with AAD, hello
│   │                  + gateway-auth tags, ML-KEM-768, HKDF,
│   │                  fingerprints, key persistence — NO from-scratch
│   │                  crypto
│   ├── replay.py      ReplayGuard: per-device monotonic sequences
│   ├── metrics.py     counters + unit-aware observations
│   ├── health.py      minimal HTTP /health endpoint
│   └── logging_setup.py
├── device/
│   ├── sensor.py      fake reading generation (pure, testable)
│   ├── state.py       persistent sequence counter (F-05)
│   └── device.py      TCP client; authenticated hello + readings
├── gateway/
│   ├── processing.py  pure logic: hello auth, fallback policy,
│   │                  handshake validation, pin verification
│   ├── cloud_channel.py  state machine, pinned ML-KEM-768
│   │                  establishment, reconnect (F-01/F-07)
│   └── gateway.py     device TCP server, replay guard, health
├── cloud/
│   ├── processing.py  pure logic: handshake validation, protected
│   │                  reading decryption
│   ├── store.py       bounded in-memory reading store
│   └── cloud.py       gateway TCP server, session registry with
│                      eviction, persisted ML-KEM keypair
├── tests/             136 pytest tests (P08)
├── .github/workflows/ci.yml
├── Dockerfile.device / Dockerfile.gateway / Dockerfile.cloud
├── docker-compose.yml
├── requirements.txt   pinned: cryptography==50.0.1, pytest==9.1.1
└── pytest.ini
```

Runtime state lives in `device_state/` (sequence counters) and
`cloud_state/` (cloud ML-KEM keypair) — both gitignored.

## 3. Install dependencies

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Run locally

The gateway verifies the cloud's ML-KEM public key against a pinned
fingerprint, so local runs need one extra step:

```bash
# 1. cloud service (persists its keypair on first start, prints the
#    SHA-256 fingerprint of its public key)
python -m cloud.cloud

# 2. copy the printed fingerprint into the environment, then start
#    the gateway (fails closed if the pin is missing/wrong)
CLOUD_PUBLIC_KEY_SHA256=<64-hex-fingerprint> python -m gateway.gateway

# 3. legacy device (dev-01 by default; key from DEVICE_KEY_HEX)
python -m device.device
```

Flags: `--device-id`, `--interval` (device); `--cloud-host`,
`--cloud-port` (gateway); `--health-port`, `--key-file` (cloud).
Useful env vars: `DEVICE_KEYS_JSON` (gateway-side registry),
`DEVICE_KEY_HEX` (device's own key), `DEVICE_STATE_DIR`,
`CLOUD_KEY_FILE`.

Watch for: `FALLBACK ACTIVATED: device dev-01 uses the legacy path ...`
(gateway), `ML-KEM-768 session <id> established with gateway ...`
(cloud), and `REPLAY REJECTED ...` if you replay a message.

Health endpoints: `GET http://127.0.0.1:8002/health` (cloud),
`GET http://127.0.0.1:8001/health` (gateway; reports
`ok`/`degraded` + `cloud_state`). The cloud serves recent readings at
`GET /readings`.

## 5. Run tests

```bash
pytest   # 136 passed at the end of P08 (120 at P06; 101 at P04; baseline 39)
```

Coverage: sensor generation, AEAD round trips + AAD binding (F-05),
hello authentication + full fallback policy (F-02), handshake field
validation (F-03/F-04), replay guard semantics, pin verification
(F-01), session lifecycle incl. failure/reconnect with a fake cloud
(F-07), per-device keys (F-06), protocol framing incl. truncated
messages (F-15), metrics units (F-08).

**Remaining test gaps (TODO):** concurrent clients, failure
injection at scale, Docker/CI tests. (Real-socket integration tests
were added in P04/P06: `tests/test_session.py`,
`tests/test_nonce_validation.py`.)

## 6. Run with Docker

```bash
# first start (one-time trust-anchor provisioning):
docker compose up cloud
#  read the printed "ML-KEM public key SHA-256 fingerprint" from the
#  logs, then create a .env file:
#    CLOUD_PUBLIC_KEY_SHA256=<fingerprint>
docker compose up --build
```

**Not verified:** Docker is not installed on the development machine;
the compose file is inspection-reviewed only. **Do not claim it works
until someone runs it.** The compose setup mirrors the local run:
cloud persists its keypair in a named volume (stable fingerprint),
the device keeps its sequence counter in a named volume.

## 7. Security limitations (final state, P08)

**Fixed in P04, P06 and P08 (evidence in `review/P04`, `review/P06`
and `review/P08`):**
- unauthenticated ML-KEM key establishment (now fingerprint-pinned),
- downgrade via unauthenticated capability claims (now AEAD-tagged
  hellos + explicit reject policy),
- gateway/cloud crashes on malformed handshake messages,
- replay acceptance (now monotonic sequences + AAD),
- wedged session state and lying health after cloud failure,
- metric unit inconsistencies,
- **NEW-1 (discovered in P05, fixed in P06):** wrong-length AEAD
  nonces crashed handler threads with uncontrolled tracebacks and
  bypassed the error metrics; nonce length is now validated before
  the AEAD call.
- **BF-01 (P08):** the cloud did not authenticate gateways; the
  gateway handshake request now carries a per-gateway AEAD tag,
  verified by the cloud before the session is accepted.
- **BF-03A (P08):** device/gateway credentials were embedded in source;
  they are now loaded from configuration (env or demo JSON files).

**Remaining limitations** (each with status):

| # | Limitation | Status | Reason / future improvement |
| --- | --- | --- | --- |
| 1 | No TLS; metadata (ids, sizes, timing) visible; transport-level tampering only *detected* where tags/pins apply | Deferred | Out of scope for the educational protocol demo; TLS would hide the ML-KEM handshake |
| 2 | Cloud does NOT authenticate gateways (gateway_id self-declared) | Deferred | Future phase: gateway credentials or signatures |
| 3 | Static demo keys; no rotation, revocation, or expiry timers | Deferred | P03 F-11 decision; pin must be updated when the cloud key rotates |
| 4 | Gateway/cloud restart loses replay state until devices send again | Accepted (P03) | Documented P03 limitation; do NOT silently add a database |
| 5 | No sequence jump window (an attacker with a device key can jump the counter and wedge the device stream until it catches up — observed live during P04) | Accepted (P03) | Future: bounded jump windows / incarnation counters |
| 6 | Hello replay re-triggers fallback activation (benign, observable) | Accepted | Future: hello anti-replay |
| 7 | Device has no reconnect logic; drops out during gateway-cloud outages | Deferred | P03 decision; future device retry/backoff |
| 8 | No rate limiting / thread caps (accepted at 1–3 device demo scale) | Deferred | P03 F-12 decision |
| 9 | Key material lives in Python bytes for the process lifetime (no zeroization) | Deferred | Python limitation; C-level secure memory out of scope |
| 10 | Pins and device keys are provisioned via env/config (simulated provisioning) | Accepted | The registry simulates provisioning; it is not a production provisioning system |
| 11 | In-memory storage/metrics only; health endpoint unauthenticated | Accepted | By design (prompt section 4/8) |
| 12 | Docker compose not yet verified in any environment | Deferred | Docker unavailable on the dev machine |
| 13 | Gateway `/health` is only available after the first successful cloud session; during the initial establishment retry loop there is no health endpoint (NEW-2, found in P05) | Deferred | Not required for the NEW-1 fix; P06 scope decision |
| 14 | No keepalive/heartbeat: a dead cloud connection is detected only when the next forwarding operation fails (NEW-3, found in P05) | Accepted | P03 send-failure-detection design; educational prototype |
| 15 | One-thread-per-connection resource growth (BF-02, P08) | Deferred | A bounded worker pool/rate limit was out of scope for P08 |
| 16 | No sequence jump window: replay state can be poisoned by a large accepted sequence number (BF-03B, P08) | Accepted | P03 design; a jump window may weaken replay protection |
| 17 | Unauthenticated `/health` and `/readings`, bound to `0.0.0.0` (BF-05, P08) | Accepted | Educational deployment; do not expose to an untrusted network |

## 8. Known TODOs

- Modern device path (direct device↔gateway ML-KEM) — rejected by
  policy until implemented (`gateway/processing.py`).
- Fallback policy extensions: credential expiry/rotation, migration
  management (`gateway/processing.py`, P03 questions).
- BF-02 (P08): bounded worker pool / connection rate limit to avoid
  one-thread-per-connection resource growth.
- BF-03B (P08): a bounded sequence jump window or incarnation counter
  to resist sequence-state poisoning (revisit P03 decision).
- BF-05 (P08): authentication/access control for `/health` and
  `/readings` if ever exposed to an untrusted network.
- Test gaps listed in section 5.
- CI improvements: linting, static analysis, Docker builds,
  integration tests (`.github/workflows/ci.yml`).

## 9. AI development chain (course documentation)

| Phase | Artifact |
| --- | --- |
| P01 | `prompt/P01`, baseline code (AI-generated) |
| P02 | `review/P02 - Baseline Technical Review.md` (15 findings, attack evidence) |
| P03 | `review/P03 - Student Security Evaluation & Design Decisions.md` (decisions are student-owned proposals) |
| P04 | `review/P04 - Security Implementation & Verification.md` (fail-first evidence, attack re-tests) |
| P05 | `review/P05 - Independent Security Verification & Re-test.md` (independent TCP attacks; NEW-1 discovered) |
| P06 | `review/P06 - NEW-1 Fix & Final Security Verification.md` (NEW-1 fail-first fix + re-verification) |
| P07 | `review/P07 - Final Project Evaluation & Evidence Consolidation.md` (final evidence matrix + verdict) |
| P08 | `review/P08 - Additional Adversarial Testing, Attack-Chain Analysis & Targeted Remediation.md` (BF-01..BF-07 reproduction; BF-01 + BF-03A remediation) |

Every significant AI interaction must be recorded by the student team
with the full chain: prompt → output → evaluation → decision →
verification → change → remaining risk. AI-generated content and
student-reviewed content must stay clearly separated.
