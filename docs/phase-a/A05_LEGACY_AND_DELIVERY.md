# A-05: Simulated protocol compatibility and delivery baseline

Date: 2026-10-16. Source HEAD: `681986bc0119d51913140575f98720c90fb378ac`.
Status: bounded simulation compatibility measured; lab-v1 delivery design selected;
durable delivery and Phase B acceptance are not implemented.

## Authorized scope

The user selected **Docker deployment and simulated devices** during Phase A,
and requested safe cybersecurity boundaries. A real device is consequently not
a prerequisite for this iteration. This changes the scope of the original
plan's real-legacy selection gate; it does not turn simulation results into
real-device compatibility evidence. All observations below concern owned local
processes with fresh synthetic identities and data. No external target was used.

The existing protocol is newline-delimited JSON/TCP with ChaCha20-Poly1305 on
the device link. The independent peer in `scripts/phase_a/legacy_probe.py`
encodes JSON, framing, hello authentication and reading encryption directly.
It imports no application protocol, crypto, sensor or processing helpers.
It reuses only the baseline process-launch helper to run the real gateway and
cloud entry points in an isolated copied checkout. This is an independent
encoding of the repository's simulated protocol, not an independent vendor
implementation of an industrial protocol.

## Observed compatibility and measurements

The successful raw run is
`D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z\legacy-runtime-01`.
The sanitized result is [legacy-result.json](evidence/legacy/legacy-result.json).
Python was 3.12.0 with cryptography 50.0.1. The copied application source matches
the baseline source. A child-only loopback health-bind adapter is disclosed in
[A-01](A01_BASELINE.md); it excludes unmodified-deployment acceptance.

- One independent simulated device sent three readings at the existing
  five-second interval. All three exact payloads were returned by the real
  cloud HTTP readback endpoint.
- Each measured plaintext was 126 bytes; each encoded reading frame, including
  its newline, was 296 bytes. The authenticated hello was 151 bytes. These are
  sample sizes, not worst-case business payloads or size guarantees.
- Send-to-readback observation upper bounds were 89.1584, 80.3073 and 102.1313
  milliseconds. The nearest-rank sample p50 was 89.1584 ms and p95 was 102.1313
  ms. The same host's monotonic clock was used; HTTP work and 20 ms polling
  contribute to these values. Three samples do not establish an SLO, pure
  network latency or a useful tail-latency distribution.
- A separate 100-message burst completed in 0.0901255 seconds, an observed
  short-run rate of 1109.5639 messages/second. This includes encryption, sending
  and observation of the final cloud count; it is not sustained capacity.
  The cloud readback tail contained the expected sequences 95 through 104.
- Exact reading replay, unauthenticated outer-sequence tampering, wrong device
  key and an unknown device were rejected. A valid reading after sequence
  tampering was delivered. Malformed hello JSON closed the connection and
  increased the controlled error counter.

The pre-risk-probe cloud count was exactly 104: three nominal readings, one
valid control and 100 burst readings. The final count was 106 after the two
deliberate metadata-consistency observations below. Counts from these profiles
must not be combined into a claim of 106 normal benchmark samples.

## Open metadata-consistency finding

Using only its synthetic enrolled device credential, the peer encrypted a
payload naming another device while the authenticated outer metadata named
the enrolled device. The foreign inner identity was stored. It then supplied
outer sequence 106 with inner sequence 999999; the payload was stored, and the
next ordinary sequence 107 was rejected by the cloud's inner replay check.

This is A03-05 in the [risk report](A03_RISK_EVIDENCE.md). It establishes missing
inner/outer identity and sequence consistency for this path. It does not prove
that unauthenticated traffic can pass AEAD or establish every possible gateway
authorization attack. These synthetic observations are retained as defensive
regression requirements; no additional attack exercise is needed for acceptance.

## Delivery and persistent-state handoff

The existing device persists its sequence after `sendall`; the gateway advances
its in-memory replay check before cloud forwarding; the cloud retains only a
bounded in-memory deque. There is no durable gateway acceptance, transactional
cloud write, business acknowledgement, retry queue or deduplication transaction.
The observed delivery therefore cannot satisfy the Phase B fault matrix.

[DELIVERY_CONTRACT.md](DELIVERY_CONTRACT.md) specifies the selected lab-v1 state and
message contract for B-01 through B-04. Its invariant requirements follow the
accepted short-term plan. Encoding, storage settings, retention, retry horizon,
resource budgets and outage thresholds are selected engineering test choices
for the Docker simulation. Their implementation and runtime measurement remain
Phase B-D work; they are not agreed physical-pilot or production requirements.

The simulation profile is one active device and a five-second reporting
interval, with the current 64 KiB parser cap retained for baseline reproduction.
The accelerated A-01 smoke and 100-message burst are separate diagnostic
profiles. Target Docker observations are recorded separately in the Docker
report rather than attributed to this Windows subprocess run.

## Reproduction and boundaries

From the checkout root, choose a **new directory outside the checkout** in a
writable temporary location:

```powershell
.venv/Scripts/python.exe -B scripts/phase_a/legacy_probe.py --runtime "$env:TEMP/pqc-phase-a-legacy-new"
```

The command retains synthetic state and raw logs there and stops only its own
children on exit. It refuses a runtime inside the checkout or an existing
runtime. Do not reuse the successful evidence directory. The saved result
describes open findings rather than a security pass. Current validation has
not established WAN behavior, sustained load, durable recovery or any
real-device/standard-protocol interoperability.
