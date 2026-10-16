# A-02 Scenario and Boundary Record

Recorded: 2026-10-16. Status: Docker/simulation scenario and lab-v1 design
parameters selected; isolated Docker baseline verified. Transport acceptance
is recorded separately in A-04.

Scenario details were extracted from the project. The user then explicitly
selected Docker deployment with simulated devices and safe local defensive
validation. This supersedes the original plan's real-device selection
prerequisite for the current iteration. It does not authorize claims of
real-device or industrial-protocol compatibility.

## Existing scenario selected for baseline validation

- **System:** simulated temperature sensor -> one edge gateway -> one cloud
  receiver; one-way telemetry. P01, sections 1-4, explicitly defines a pure
  software simulation with no real IoT hardware, embedded hardware or production
  deployment. README section 1 confirms this architecture.
- **Legacy link:** custom newline-delimited JSON over TCP. `common/protocol.py`
  explicitly chooses this instead of HTTP/MQTT. Device payloads use
  ChaCha20-Poly1305 and a per-device key; the device does not perform ML-KEM.
  The authenticated hello selects the legacy capability. Sequence and device
  identity are included in the reading AAD.
- **Gateway/cloud link:** custom TCP handshake, pinned persistent ML-KEM-768
  cloud key, HKDF session key and ChaCha20-Poly1305. This is the existing
  baseline, not TLS and not a hybrid TLS channel.
- **Active workload:** `docker-compose.yml` starts one device, default
  `dev-01`, every 5 seconds (`common/config.py` also defaults to 5 seconds).
  Two provisioned demo device identities do not establish two active devices.
  README's 1-3 device demonstration scale is not a production capacity claim.
- **Data:** device ID, UTC timestamp, temperature in Celsius, unit and integer
  sequence (`device/sensor.py`). Temperature generation is 15-35 degrees C.
  Framing caps an encoded message at 64 KiB; this is a parser limit, not a
  measured normal payload size. A-05 measures sample wire sizes separately.
- **Deployment assets:** Docker Compose with `python:3.12-slim` images;
  GitHub Actions on Ubuntu with Python 3.12. Local Windows execution is also
  documented. An image tag alone does not freeze the underlying OpenSSL version.
  This run's Windows environment is a validation environment, not evidence of
  target Linux interoperability.

## Trust and failure boundaries

The gateway decrypts device telemetry and is a trusted termination point. The
new protected link is gateway -> cloud; there is no device-to-cloud end-to-end
PQC claim. Shared demo credentials are public educational material, not pilot
identities. Each experiment uses fresh test credentials.

Current provisioning consists of device/gateway key registries and a pinned
cloud public-key fingerprint. The cloud authenticates a gateway request but
does not implement a gateway-to-authorized-device mapping. A-03 revalidates
request freshness, transcript binding and related risks.

`device/device.py` has no reconnect/backoff and no reading acknowledgement. It
persists a sequence after `sendall`, which does not prove gateway acceptance or
cloud storage. Device-side buffering/backpressure is not implemented. A gateway
or cloud restart loses in-memory replay state. `cloud/store.py` retains only
the latest 1,000 readings in memory and silently evicts older ones; this is not
a time-based retention promise. There is no durable gateway queue or cloud ACK.

## Requirements boundary and selected experimental parameters

The roadmap deliberately leaves the first real device/protocol and primary
pilot environment to Phase A selection. It does not supply a manufacturer,
device model, external protocol specification or independent deployed endpoint.
The user has now selected Docker and simulation for this iteration; a future
real-device pilot would require its own source and compatibility evidence.

The following have no externally supplied physical-pilot requirements:

- For a future physical-device pilot only: protocol/device source, firmware
  constraints and operator/site; these are not current simulation blockers.
- Required peak device count, maximum business payload and network conditions.
- Tolerated outage, capacity budgets, time-based retention and data sensitivity.
- Handshake/delivery latency, throughput and reconnection acceptance thresholds.
- Maximum revocation enforcement delay and credential/offline lease duration.
- Deduplication retention, retry horizon, at-rest key storage and upgrade method.

For the current Docker simulation, [DELIVERY_CONTRACT.md](DELIVERY_CONTRACT.md)
now selects lab-v1 encoding, storage/durability settings, finite quotas, retry/
retention/expiry behavior and experimental performance/recovery targets. These
are deliberate test design choices, not measured results or claims of meeting
an unspecified physical-device need. It selects the 24-hour run and ten-minute
outage as future lab checks; neither has been executed as part of Phase A.

## Current decision

Use the existing one-device/5-second simulated scenario for the bounded A-01
and A-05 baseline. Preserve existing application code and default configuration.
Evaluate TLS separately, and describe compatibility results at their actual
scope. The selected lab topology is one simulated device, one logical gateway
and one cloud receiver in an isolated Docker project. The existing default
workload is one reading per five seconds. Target Linux baseline execution was
verified in A06. The selected resource/retention policies require implementation
and runtime acceptance in Phases B/D. Transport feasibility requires separate
Phase A target-runtime evidence.
Phase B is not started. The lack of physical hardware alone does not block
this revised lab scope.
