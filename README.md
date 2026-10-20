# PQC Bridge — Legacy Edge-Cloud

PQC Bridge explores verifiable post-quantum migration for legacy edge-to-cloud
telemetry: authenticated hybrid transport, durable delivery, bounded recovery,
and evidence of the policy actually in effect.

> **Engineering prototype with bounded lab acceptance.** Phase A transport
> selection, Phase B secure delivery, Phase C migration management and the amended
> Phase D pilot package are accepted for owned Docker services
> and simulated devices. Physical-device compatibility and production security
> have not been established. Passing tests does not prove a system secure.

## Current Engineering Status

- [Phase A](docs/phase-a/STATUS.md): target-runtime hybrid TLS feasibility and the
  simulation delivery contract were verified.
- [Phase B](docs/phase-b/STATUS.md): an opt-in TLS 1.3/mTLS path with mandatory
  hybrid key exchange, identity authorization, durable queues, cloud deduplication
  and acknowledgements, recovery, and resource limits was accepted in the lab.
- [Phase C](docs/phase-c/STATUS.md): local enrollment, versioned hybrid policy
  profiles, current-channel business proof, credential rotation/revocation, canary
  rollout and safe rollback were accepted in the Docker/simulated-device lab.
- C and its Linux test portability repair are published to `main` at
  [2cde91d](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/commit/2cde91dfabdf4435e298243b2b52bb1dcb48723c).
  [Main CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39260202385)
  passed all 247 tests and Docker checks. [CI follow-up](docs/phase-c/CI_FIX.md)
  preserves the earlier Linux failure and its test-only repair.
- [Phase D](docs/phase-d/COMPLETION.md): offline pilot packaging, coordinated cold
  recovery, same-schema upgrade/rollback and operator handover are accepted for
  the owned Docker/simulation scope. The explicitly human-amended30-minute run
  reconciled360 unique records, completed three rotations and verified backup/
  cleanup; durable ACK p950.475s. [Linux CI](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/actions/runs/39393876501) passed tests and Docker checks.
  [Evidence/review](docs/phase-d/FINAL_REVIEW.md), [pilot runbook](docs/phase-d/OPERATIONS.md).
  This establishes neither one-hour/24-hour stability nor production acceptance.
- [B engineering operations](docs/phase-b/OPERATIONS.md) documents the delivery path;
  [C management operations](docs/phase-c/OPERATIONS.md) covers managed deployment
  and migration recovery.
  The V1 commands and architecture below remain available as the initial baseline.

These are recorded phase outcomes, not tests rerun during this documentation
update. Consult each phase's evidence and limitations before making a claim.

## Roadmap and Development Records

- [Engineering and competition roadmap](docs/ENGINEERING_ROADMAP.md)
- [Short-term implementation plan](docs/SHORT_TERM_PLAN.md)
- [Initial Development Records: P01–P08](docs/development/initial/README.md)
- [Development documentation guide](docs/development/README.md)

The long-term aim is a reproducible cybersecurity and post-quantum migration
project with a clearly evaluated contribution. AI-assisted migration diagnostics
are a conditional research track, subject to measured benefit over rule-based
and manual baselines. These roadmap capabilities are not completion claims.

The following sections document the initial V1 path and its historical controls.
They do not replace the separate Phase B operational instructions or imply that
the opt-in engineering path has the same transport and persistence limitations.

## 1. Initial V1 Architecture

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
├── scripts/docker_bootstrap.py  fresh-clone Docker trust-anchor
│   │                  provisioning (F-01 pin, section 6)
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

CI (`.github/workflows/ci.yml`): GitHub Actions runs two jobs on
every push/PR:
1. `test` — Python 3.12 + pinned requirements + this pytest suite;
2. `docker` — `docker compose config --quiet` (compose validation),
   all three image builds, and the fresh-clone bootstrap smoke test
   (`scripts/docker_bootstrap.py`): cloud keypair generation →
   fingerprint provisioning → gateway ML-KEM-768 session → device
   readings reaching the cloud, all against empty CI volumes with no
   `.env`. CI verifies the repository as it exists in GitHub, never
   against local Docker volumes or local `.env` files.

Coverage: sensor generation, AEAD round trips + AAD binding (F-05),
hello authentication + full fallback policy (F-02), handshake field
validation (F-03/F-04), replay guard semantics, pin verification
(F-01), session lifecycle incl. failure/reconnect with a fake cloud
(F-07), per-device keys (F-06), protocol framing incl. truncated
messages (F-15), metrics units (F-08).

**Remaining test gaps (TODO):** concurrent clients, failure
injection at scale. (Real-socket integration tests were added in
P04/P06: `tests/test_session.py`,
`tests/test_nonce_validation.py`.)

## 6. Run with Docker

Fresh clone, first start (trust-anchor provisioning is automatic):

```bash
python scripts/docker_bootstrap.py
```

Every later start (the cloud keypair persists in the `cloud_state`
volume and `.env` is already provisioned):

```bash
docker compose up -d
```

**How the cloud fingerprint is provisioned**
(`scripts/docker_bootstrap.py`, Python standard library only):

1. starts only the cloud, which generates its ML-KEM-768 keypair on
   first start and persists it in the `cloud_state` volume
   (`CLOUD_KEY_FILE=/app/cloud_state/cloud.key`);
2. waits for the cloud health endpoint, then reads the cloud's
   ML-KEM public key SHA-256 fingerprint from the cloud logs (public
   material — the private key never leaves the container);
3. writes `CLOUD_PUBLIC_KEY_SHA256=<fingerprint>` to the gitignored
   `.env` file;
4. starts the gateway + device and waits until the gateway's
   ML-KEM-768 session is established and the cloud has stored at
   least one device reading.

The gateway **fails closed** when the pin is absent or incorrect:
with a missing/empty `CLOUD_PUBLIC_KEY_SHA256` or a fingerprint that
does not match the cloud's actual public key, no session is ever
established — the gateway logs the rejection and keeps retrying. The
fingerprint is deliberately NOT hardcoded in the compose file, so a
fresh clone with a fresh `cloud_state` volume provisions its own
pin. Re-run the bootstrap whenever the `cloud_state` volume is
recreated (e.g. `docker compose down -v`); re-running against the
persisted keypair simply provisions the same fingerprint again.

**Local Docker verification:** `docker compose config --quiet`
(compose syntax/consistency) and the bootstrap smoke test above
(fresh-clone provisioning + ML-KEM session + end-to-end readings).

**Verification status (2026-09-21): Docker runtime VERIFIED.**

Docker Desktop 29.8.0 was used to run the complete edge-cloud
simulation with Docker Compose. All three services started
successfully. Cloud and Gateway were healthy, and the Device was
running successfully.

The Gateway established an ML-KEM-768 session with the Cloud. The
Device successfully connected to the Gateway and continuously sent
sensor readings; the Cloud received and stored them (seq=11–19
during the final verification run). The Device used the intended
legacy ChaCha20-Poly1305 fallback path.

The verification also confirmed state persistence. After Docker
Desktop was restarted, the Cloud loaded its existing ML-KEM keypair,
and the Device resumed its sequence number from the previous state.

Therefore, the Docker runtime and the complete Device → Gateway →
Cloud communication path were successfully verified.

The static review cross-checked the compose file against the code:
service names and Compose DNS hosts (`cloud`, `gateway`), ports
(cloud 5002/8002, gateway 5001/8001), all environment variable names
against `common/config.py`, the simulated provisioning registries
(`GATEWAY_KEYS_JSON` ↔ `GATEWAY_KEY_HEX`, `DEVICE_KEYS_JSON` ↔
`DEVICE_KEY_HEX`; demo keys only), the named volumes for cloud
ML-KEM key persistence (`cloud_state`) and device sequence
persistence (`device_state`), and the healthchecks (stdlib urllib
against each service's own `/health` endpoint). No defects were found
in static review. The runtime behavior (build, health checks,
end-to-end Device → Gateway → Cloud, pin enforcement, restart
behavior) was verified on 2026-09-21 with Docker Desktop 29.8.0 —
see the verification status above.

## 7. Initial V1 Security Limitations (P08)

**Fixed in P04, P06 and P08 (evidence in `docs/development/initial/P04`, `docs/development/initial/P06`
and `docs/development/initial/P08`):**
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
- **BF-06/BF-07 (P08):** the zero-credential compound attack chain
  (fake Gateway → seq=99999 poisoning → data blindness / plausible
  fake stream) is blocked at BF-01. A credential-bearing attacker
  (anyone with the committed demo gateway key) can still poison
  sequence state and inject plausible readings — see the BF-03B and
  static-demo-key limitation rows below. This residual is
  intentional: demo keys are public by design in this educational
  repo, and a real deployment must supply its own keys.

**Remaining limitations** (each with status):

| # | Limitation | Status | Reason / future improvement |
| --- | --- | --- | --- |
| 1 | No TLS; metadata (ids, sizes, timing) visible; transport-level tampering only *detected* where tags/pins apply | Deferred | Out of scope for the educational protocol demo; TLS would hide the ML-KEM handshake |
| 2 | Static demo keys; no rotation, revocation, or expiry timers | Deferred | P03 F-11 decision; pin must be updated when the cloud key rotates |
| 3 | Gateway/cloud restart loses replay state until devices send again | Accepted (P03) | Documented P03 limitation; do NOT silently add a database |
| 4 | No sequence jump window (an attacker with a device key can jump the counter and wedge the device stream until it catches up — observed live during P04) | Accepted (P03) | Future: bounded jump windows / incarnation counters |
| 5 | Hello replay re-triggers fallback activation (benign, observable) | Accepted | Future: hello anti-replay |
| 6 | Device has no reconnect logic; drops out during gateway-cloud outages | Deferred | P03 decision; future device retry/backoff |
| 7 | No rate limiting / thread caps (accepted at 1–3 device demo scale) | Deferred | P03 F-12 decision |
| 8 | Key material lives in Python bytes for the process lifetime (no zeroization) | Deferred | Python limitation; C-level secure memory out of scope |
| 9 | Pins and device keys are provisioned via env/config (simulated provisioning) | Accepted | The registry simulates provisioning; it is not a production provisioning system |
| 10 | In-memory storage/metrics only; health endpoint unauthenticated | Accepted | By design (P01 historical requirements sections 4/8) |
| 11 | Docker compose runtime deployment | Resolved (2026-09-21) | Previously unverifiable on the dev machine (no Docker Engine); now verified end-to-end with Docker Desktop 29.8.0 — see section 6 |
| 12 | Gateway `/health` is only available after the first successful cloud session; during the initial establishment retry loop there is no health endpoint (NEW-2, found in P05) | Deferred | Not required for the NEW-1 fix; P06 scope decision |
| 13 | No keepalive/heartbeat: a dead cloud connection is detected only when the next forwarding operation fails (NEW-3, found in P05) | Accepted | P03 send-failure-detection design; educational prototype |
| 14 | One-thread-per-connection resource growth (BF-02, P08) | Deferred | A bounded worker pool/rate limit was out of scope for P08 |
| 15 | No sequence jump window: replay state can be poisoned by a large accepted sequence number (BF-03B, P08) | Accepted | P03 design; a jump window may weaken replay protection |
| 16 | Unauthenticated `/health` and `/readings`, bound to `0.0.0.0` (BF-05, P08) | Accepted | Educational deployment; do not expose to an untrusted network |

## 8. Historical V1 Follow-ups

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
- CI improvements: linting, static analysis, security scanning
  (`.github/workflows/ci.yml`).

## 9. Development History and Continuing Records

The [Initial Development Records](docs/development/initial/README.md) cover
baseline design (P01), technical review (P02), proposed security decisions (P03),
implementation (P04), independent verification (P05), targeted correction (P06),
evidence consolidation (P07), and additional adversarial testing (P08).

Technical requirements formerly held separately are retained beside each record.
Historical findings, test outcomes, proposal status, and residual risks remain
attached to their original phases. Later progress does not retroactively change
those results.

New milestones follow the [development record template](docs/development/RECORD_TEMPLATE.md):
background and scope, findings and evidence, design decisions, implementation,
verification results, and remaining risks. All project documents are in English.
