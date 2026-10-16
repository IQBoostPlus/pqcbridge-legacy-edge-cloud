# Phase B simulation message and persistent-state contract

Date: 2026-10-16. Contract version: **lab-v1, selected for implementation**.
Status: design handoff selected for this bounded simulation; not implemented
or accepted as runtime behavior. Independent review is recorded in STATUS.md.
Scope: one Docker simulation site, one active logical gateway, simulated
one-way telemetry. Source: SHORT_TERM_PLAN sections 2 and 3 and current A-05
observations. This document makes the required behavior concrete without
claiming that the baseline already provides it.

## Identity and message boundary

1. The selected transport must expose the verified peer identity. A registry
   maps that identity to a stable logical gateway ID and an explicit permitted
   device set. A submitted ID cannot override that mapping. Certificate
   renewal must not create a new message namespace or authorize other devices.
2. On validated ingestion, normalize one event containing `schema_version`,
   `gateway_id`, `event_id`, `device_id`, `accepted_at`, optional source timestamp
   and sequence, and a bounded typed payload. Validate inner device/sequence
   against authenticated source metadata before any replay-state update.
3. The gateway generates an unpredictable event ID once for the durably
   accepted event. The cloud idempotency key is `(gateway_id, event_id)`.
   Persist the event ID and payload together before counting acceptance.
   Retries, restarts and credential rotation preserve this key and payload.
4. Where a source has no reliable sequence, this ID covers gateway retries
   only. It cannot identify separate duplicate submissions from the device.
   Device reset/replacement must have a defined enrollment/incarnation policy;
   it must not silently reset business deduplication or accept an arbitrary
   large sequence as a recovery mechanism.
   For lab-v1, a present sequence is an integer in `1..2^63-1`, excluding
   Booleans. Provision the initial last-accepted value as zero for the fresh
   simulator incarnation and persist subsequent values atomically with events.
   Values at or below that value are rejected without advancing state. A forward
   increment up to 1,024 is admissible after full authentication/metadata
   validation. Increment the source-gap metric only when the increment exceeds
   one, recording the inferred missing count as increment minus one; this
   does not prove missing samples were
   delivered. A larger forward jump is refused, counted and leaves state
   unchanged. Recovery requires an explicit operator-reviewed source checkpoint
   or new incarnation enrollment, never automatic sequence-state clearing.
   This finite lab window is not a complete replay/authorization solution.
5. Use the deterministic encoding/digest selected below. An ACK must identify
   the same gateway/event and digest.
   Reusing a key with different content is an explicit conflict, never a
   successful duplicate. Transport-level identity checks and business-level
   deduplication remain separate checks.

## Durable state transitions

- **Before acceptance:** validate source authorization, schema, size and
  capacity. A failed transaction or full queue is not acceptance. If the source
  protocol supports acknowledgement, return success only after durable commit.
  The existing simulated source protocol has no reading ACK; it cannot tell
  its sender that durable acceptance occurred without an explicit extension.
- **Pending:** atomically commit event ID, immutable normalized payload and
  required retry metadata in bounded local storage. Pending work survives a
  process or host restart under the selected storage's documented guarantees.
- **In flight:** sending does not remove the pending row. This state may be
  transient; after a crash, unacknowledged work returns to pending with the
  original identifier. Bound connection attempts and exponential backoff.
- **Cloud commit:** authorize the gateway/device, validate content and write
  business data plus the idempotency record in one transaction. A matching
  duplicate returns the committed result. No success ACK precedes commit.
- **Acknowledged:** only a valid matching ACK permits a durable gateway state
  update/removal. A crash after cloud commit or ACK receipt may retransmit the
  same event, but must not create another business record.
- **Exceptional:** expired, conflicting or otherwise nonretryable work is
  explicitly quarantined/rejected according to a recorded policy, with counts
  and reason. Queue/disk exhaustion applies compatible backpressure or visible
  drops; no unbounded buffering or silent accepted-data deletion is allowed.
  For the current simulator specifically, choose **connection close on admission
  refusal**, not a claim of supported source backpressure. On row/disk quota or
  failed durable commit, count the known refused reading with a reason, do not
  mark it accepted, and close that source connection. Preserve already pending
  events. Buffered/in-transit readings may be lost with an unknown count; expose
  that uncertainty rather than inventing an exact drop total. The unchanged
  source has no reading ACK or automatic reconnect: `sendall` success is not
  gateway acceptance. After the operator resolves capacity/storage and verifies
  the source checkpoint/incarnation, explicitly restart the simulated source;
  do not promise automatic source replay. B must verify this refusal/recovery
  behavior and the accepted/pending/committed reconciliation separately.

## Retention, recovery and operational requirements

Deduplication retention must cover the maximum retry horizon. Define what
happens after that horizon before enabling cleanup. A storage restore must not
roll back message identifiers, credential revocations or relevant replay state.
Before an incompatible upgrade, prove read compatibility or an explicit
migration/recovery route. The preserved V1 remains a comparison baseline, not
an unconditional data-format rollback target.

Select at-rest protection, permissions, key location and deletion based on the
simulation's data handling requirements. Transport TLS does not protect queue
files. Keep synthetic credentials out of source-controlled artifacts.

Report liveness, readiness, authenticated cloud connectivity and business
delivery separately. Provide accepted, committed/acknowledged, pending and
exception counts with a reconciliation rule; a socket-send counter or healthy
connection cannot substitute for cloud business commit evidence.

## Selected lab-v1 encoding and storage

These are engineering choices for the user-selected simulation, not externally
supplied device requirements or measured product guarantees. A change to them
requires an explicit new contract version and corresponding regression changes.

- Persist exactly one UTF-8 JSON event with sorted object keys, compact
  separators, `ensure_ascii=False` and `allow_nan=False`. Fields are exactly
  `schema_version` (integer 1), `gateway_id`, UUIDv4 `event_id`, `device_id`,
  `source_incarnation`, `accepted_at`, `source_timestamp`, `source_sequence`
  and `payload`. Unknown fields are rejected in v1. Timestamps are UTC strings
  with a `Z` suffix and six fractional digits; a source timestamp may be null.
  Source sequence is a positive integer or null, never a Boolean. Payload has
  exactly finite `temperature_c` and `unit="celsius"`; no physical-range claim
  is inferred from an authenticated reading. Validate types before serialization.
- Calculate SHA-256 over those persisted event bytes, excluding any transport
  frame/newline. Send the stored bytes unchanged on every retry; never parse
  and reserialize a retry to invent a new digest. The upload carries type
  `event`, that event as strict base64, and its hexadecimal digest. ACK fields
  are `type="ack"`, schema version 1, gateway/event IDs, matching digest and
  `status="committed"`. Initial writes and exact duplicates return the same
  committed ACK. An ID/content conflict returns an explicit error, no ACK.
- The initial registry contains one stable gateway and one simulated device,
  with a UUID source incarnation provisioned in trusted configuration. Enforce
  one active connection per device. Source state reset/replacement requires
  explicit enrollment of a new incarnation; never infer a reset from a lower
  sequence or clear cloud deduplication. The incarnation is gateway-bound
  configuration for this simulator, not an asserted new wire capability.
- Use SQLite in separate gateway/cloud Docker volumes, transactions and
  uniqueness constraints; select `journal_mode=WAL` and `synchronous=FULL`.
  Gateway acceptance atomically stores pending event bytes and the accepted
  source sequence/incarnation. Cloud commit atomically writes business data
  and `(gateway_id,event_id,digest,result)` deduplication state. Verify actual
  storage/fsync/crash behavior in Phase B; selecting settings is not proof.

## Selected lab-v1 limits and expiry

- Normal workload: one simulated device, one reading every five seconds;
  original source frame cap 64 KiB. Normalized payload cap is **4 KiB**, event
  bytes cap **8 KiB**, and encoded upload frame cap **16 KiB**, including its
  newline. All limits are byte counts, checked before durable acceptance.
  These distinct limits do not reinterpret the original parser limit.
- Gateway pending **plus quarantined** rows are capped at 10,000 combined.
  Both gateway and cloud state directories have a 256 MiB lab budget each,
  including database/WAL/SHM and quarantined data. Stop new acceptance before
  the budget, reserving 16 MiB for bounded metadata/checkpoint/error handling.
  Cloud business rows/dedup keys are additionally capped at 100,000. Whichever
  bound is reached first controls admission. Already committed exact duplicates
  may still receive their stored ACK. Quarantine is not an unbounded disk escape.
- Do not automatically delete pending, quarantined, business or dedup records
  in this lab iteration. Retention is the bounded experiment lifetime; reaching
  quota stops acceptance with an explicit metric/reason. Any later export or
  cleanup is a separate reviewed operation after reconciliation. This avoids
  a dedup-retention gap without claiming unlimited storage or retention.
- Retry expires **24 hours from original durable acceptance**, with that UTC
  deadline persisted once. Attempts and restarts never extend it. Use monotonic
  elapsed time within a process and persist the last observed UTC progress;
  on a detected backward wall-clock step, fail closed into an observable
  clock-uncertain state until corrected. Expired pending work is quarantined
  within the same quota, never silently deleted or automatically re-IDed.
- Connect and individual network-operation timeouts are five seconds. Retry
  backoff starts at one second, doubles to at most 30 seconds and uses bounded
  jitter without exceeding that maximum. Cap concurrent cloud delivery at one
  connection; resource/connection-limit rejection must remain observable.
- Synthetic identities are scoped to this lab. Select certificate validity
  at most 24 hours and a renewable five-minute policy/offline lease. Expired
  identity/lease stops new transmission and closes an active channel; authorized
  events may buffer within quota. The planned revocation bound is five minutes
  including active disconnection. Rotation/revocation implementation and
  enforcement exercises remain Phase C work, not existing capability.
- Store only synthetic sensor data. Restrict state/credential mounts to the
  owning service account, mount trust/credential inputs read-only, keep private
  material outside the checkout, and disable payload/secret logging. This lab
  does not add application-level queue encryption or claim host-compromise
  confidentiality; confidential real data requires a new at-rest decision.

## Experimental acceptance targets, not measured guarantees

Select 0.5 CPU and 256 MiB memory limits for each gateway/cloud container and
bounded logs (two 8 MiB files per service). These are test budgets; measure
the actual runtime before accepting them. At the normal one-device workload,
candidate future checks are full-handshake p95 <= 1 second and durable-ACK
delivery p95 <= 1 second over at least 100 observations, with full handshakes
separated from resumption and all clocks/measurement methods recorded.

The selected fault scenario is a ten-minute cloud outage with recovery/retry
within 60 seconds of verified service availability and valid renewed policy.
Recovery here means the first authenticated post-outage delivery with matching
durable ACK, allowing connection/handshake time beyond the bounded backoff.
Reconcile all durably accepted backlog afterward and record its drain time
separately; do not equate first recovery with an already empty backlog.
A 24-hour normal-load run is the selected
sustained-operation scenario. These thresholds are explicit experimental
targets fixed before the future tests; no current three-sample/burst result
establishes they pass. If they fail, report failure and investigate rather
than retroactively changing thresholds to fit the result.

The B implementation must exercise every failure point in SHORT_TERM_PLAN's
minimum fault matrix, including crashes around commits/ACKs, full queue/disk,
invalid identity and outage. The selected lab-v1 targets above provide the
bounded test profile; durability, recovery and capacity acceptance remain
future implementation/test work.
There is no exactly-once device sampling guarantee and no production acceptance
in this contract.

## Selected packaging and upgrade boundary

The measured target is Linux x86-64 containers on this host's Docker Desktop /
WSL2 engine; the Windows Python environment is a secondary development baseline.
Use Python 3.12.14 and the recorded immutable base-image identity in A-06 for
the next simulation build, with cryptography 50.0.1. Pin the TLS configuration
and actually loaded library together with the selected adapter evidence in
A-04. This is the measured candidate, not a dependency support/vulnerability
audit or a promise that a floating image tag remains equivalent.

The planned D package is a versioned Compose bundle plus immutable image
references and a source/dependency manifest. Stage upgrades in a separate
simulation project with separate state first. Refuse unknown storage schema
versions at startup; no automatic in-place schema conversion or downgrade is
selected for lab-v1. A later upgrade that changes persistent state requires a
separately tested migration and recovery procedure that preserves event IDs,
deduplication, source-incarnation and credential/revocation progress. Packaging,
backup/restore and upgrade exercises remain D deliverables. These design choices
do not change the existing Compose stack or make the V1 baseline a data rollback
target.
