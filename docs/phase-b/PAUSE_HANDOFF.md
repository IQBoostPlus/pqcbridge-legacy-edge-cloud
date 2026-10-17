# Phase B historical pause handoff

Historical October16 record, superseded by the explicit October17 resume and
completed acceptance in STATUS.md and REVIEW.md. Do not interpret the old pause
as the current instruction. Retained for recovery/audit provenance.

Pause: explicit user instruction, 2026-10-16 22:16 Asia/Singapore.
Read STATUS.md first. All implementation/probes/agents are stopped. Publication
heartbeat pqc-bridge-github was changed to PAUSED without changing its cadence
or prompt. A is already pushed; B must not be committed/pushed as complete.

## Files and ownership at interruption

- Transport: common/secure_transport.py, common/secure_bootstrap.py,
  deploy/phase_b/tls-policy.cnf, tests/test_secure_transport.py,
  scripts/phase_b/transport_probe.py.
- Storage: common/delivery.py, tests/test_delivery.py.
- Integration: common/secure_runtime.py, gateway/secure.py, cloud/secure.py,
  tests/test_secure_services.py. Root owns these shared application files.
- Runtime harness: scripts/phase_b/docker_probe.py, fault_probe.py,
  deploy/phase_b/Dockerfile, tests/test_secure_integration.py.
- Execution/status: docs/phase-b and PROJECT_STATE.md.

Original common/crypto.py, gateway/processing.py, device implementation and V1
services were reused, not rewritten. New services run only through
python -m common.secure_bootstrap gateway|cloud --config ABSOLUTE_JSON.
Bootstrap validates exact pre-initialization OpenSSL policy. Direct service
execution intentionally refuses. Keep TLS policy bytes LF-exact when copying.

## Runtime contract

Gateway config: gateway_id; devices mapping device ID -> {key_hex,
source_incarnation}; state_dir outside /app/checkout; cloud_host/cloud_port;
listen_host/listen_port/health_port; health_token >=32chars; policy_expires_at
UTC <=now+300sec; tls {ca_file,cert_file,key_file,server_hostname}.
Cloud config: gateway_peers mapping certificate DER SHA256 lowerhex ->
{gateway_id,devices:{deviceID:incarnationUUID}}; shared state/listen/health/
policy/tls fields. TLS certificate lifetime <=24h. Optional limits only lower
lab-v1 ceilings: queue_rows/cloud_rows/state_bytes/reserve_bytes. Configuration
may be multiline JSON; duplicate keys/nonfinite values are refused.

Only policy_expires_at can be renewed live; identity, budgets and credentials
cannot drift on renewal. Unauthorized cloud/device frames cannot change replay
state. Per-device one active source, per-gateway one active cloud connection,
global worker cap4. Health binds127.0.0.1, no host publications. /live public;
/health,/ready,/readings need Bearer health_token; /ready503 on degradation;
/readings returns normalized event list newest-first, max100.

Gateway storage public API: accept/pending/acknowledge/quarantine/expire/snapshot;
CloudStore commit/readings/snapshot. Call queue.expire regularly before pending,
also when idle. Durable counters accepted_total/acknowledged_total/committed_total;
known refusal counters process-lifetime. Source sampling has no reading ACK or
automatic reconnect. Controlled capacity refusal closes source connection;
unknown in-flight loss must remain disclosed. Spec/lab-v1 is unchanged.

## Recorded verification boundary

Delivery worker21 tests passed (1.21sec), including os._exit after public storage
transitions; logical byte-quota pressure, not physical ENOSPC or host powerloss.
Root batch36 passed before final integration fixes. Transport worker14 then16
focused host tests passed, with new TCP coalesced HELLO+2-frame and200ms total-
deadline/35ms trickle regressions. Do not sum duplicate runs.

Earlier transport-api.json: actual pinnedLinux7/7 at0.5CPU/256MiB, raw
D:\Code\pqcbridge-phase-b-artifacts\transport-6b1f25f3056440db830c2c7212905048.
It precedes SocketFrameReader and cannot validate the later edited probe/source.

Intermediate actual app Docker17/17:
docs/phase-b/evidence/docker-integration-third.json
Raw D:\Code\pqcbridge-phase-b-artifacts\docker-integration-f4953c3852814ff5820432741e650639.
Actual device->gateway->cloud exact fields, protected health, plaintext/
classical/no-cert/untrusted/trusted-but-unregistered rejection, duplicateACK/
conflict/unauthorized device, short outage/restarts/rowquota. Outage9.672sec,
drain3.156sec; NOT ten-minute/24h acceptance. Pending before gateway restart3
and after7 because source continued generating before stop. Cloud committed14
before capacity profile. Queuecap3 refused1 then recovery succeeded. Owned4
containers/network/3volumes removed. Original inputs preserved. Its copied
source hashes predate current fixes, so FINAL integration rerun is required.
Earlier failed runner/build/config records are retained; not app acceptance.

## Review findings and saved repairs

Standards P1s:
1. Source makefile read-ahead + select(kernel) could strand complete queued
   readings. Transport added SocketFrameReader with its own buffer and
   wait_readable checking that buffer/TLS pending before kernel readiness.
2. Per-recv timeout did not bound entire frame or lease/certificate expiry.
   Reader now set_deadline(seconds<=5) once per frame, monotonic budget across
   fragmented recv. Root clips every TLS read budget to remaining lease/peer
   certificate; idle wait rechecks expiry. Final integration not yet verified.

Spec findings, root repairs saved:
3. Backoff reset only after matching ACK and durable queue cleanup, not a TLS
   handshake. Repeated application refusals should now exponentially back off.
4. Fixed safe source_refused_<reason> metrics distinguish row/disk quota,
   sequence/clock/storage from generic invalid reading.
5. Health now exposes business_delivery and last_matching_ack_at; quarantine
   makes ready false even if cloud is connected. Counts still authoritative.

Other root fixes saved: strict multiline config parsing (original first green
failed pretty JSON), limit defaults copied instead of mutating live config,
only a successfully claimed source releases active identity, source idle wait
supports5sec normal reporting while each in-progress frame stays bounded.
No final post-fix Standards/Spec review or application matrix has run.

## Incomplete fault harness: inspect, then run after fixes

scripts/phase_b/fault_probe.py is a DRAFT, not successful evidence. Approved
instrumentation wraps real public GatewayQueue.accept/acknowledge and
CloudStore.commit with marker+bounded25sec wait. Host SIGKILLs the actual role,
disarms marker, restarts same owned volume; all real SQLite/TLS/authorization
still run. It uses public HTTP/API readback, no private SQL acceptance and no
fake ACKs/database. Disclose this controlled injection boundary separately
from normal unmodified service execution.

Draft stages: before_gateway_accept; before_cloud_commit; after_cloud_commit
(before ACK send); before_gateway_acknowledge (root has already validated exact
ACK before calling public cleanup API). Also drafts paused-cloud half-open,
shortened lease and operator renewal. It was interrupted before a successful run.

KNOWN HARNESS CONTRACT ERROR: its expired-policy case currently expects gateway
accepted_total not to increase on source6. Contract explicitly permits authorized
source buffering during cloud policy expiry, and actual gateway does that.
Correct expected behavior: liveness true, ready false, cloud_connected false,
zero new cloud commits; authorized source6 may become pending, then SAME event
must drain after trusted lease renewal. Do not resend source6 as a new source
reading after it was already durably accepted; that is a replay. Do not change
application to prohibit allowed buffering just to satisfy the draft assertion.

Still needed beyond draft: actual service disk-byte quota/failure preservation,
invalid cloud identity, credential expiry (active channel as well as new
handshake), source coalesced-frame and TLS slow-fragment/lease-expiry regression,
repeated application-failure backoff, observable refusal/business status. Ensure
all required B minimum-fault-matrix rows have evidence, not just API tests.
C rotation/revocation management, D24h/upgrade/full performance remain future.

## Resume procedure after explicit request

1. Preserve dirty state and read this/STATUS/PROJECT_STATE. A HEAD is
   6e4a48ffc0ec465d6d5d1c29f2272314cff6a601 on B branch. No B commit exists.
2. Restart bounded exclusive workers if useful; update main/status to resumed.
   On an explicit whole-task resume, re-enable existing paused pqc-bridge-github
   with existing settings; never duplicate it. It must defer during active work
   and publish only a complete verified major B, never this partial snapshot.
3. Inspect fault/probe drafts and fix known harness expectation above. Confirm
   final source hashes and what has actually been verified. Run focused changed
   regressions; loopback tests require reviewed host access to avoid sandbox
   socketpair stall. Don't rerun passed A suites merely for context.
4. Run actual Docker normal matrix and fault matrix on current source copies;
   all private credentials/raw stdout go to NEW external runtime. Validate exact
   current hashes, no original-state mounts, owned cleanup even on exceptions.
5. Full existing+new suite, separate final Standards/Spec reviews, fix/retest
   only justified failures, final preservation and cleanup. Mark B complete and
   auto-publish only after matching acceptance. Otherwise record precise gaps.

Native Docker CLI C:\Program Files\Docker\Docker\resources\bin\docker.exe.
Pinned local base python image SHA2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9.
Runtime runner uses verified temporary local base tag for cached A gateway image
SHAb23cfa27684e7af4be489c0d3683e184c72e3440bc45a408bbcbd5762b42b0f4;
BuildKit FROM sha256:<imageID> is not a valid local-image FROM. Do not pull/install
or repair Docker. Container volumes are new owned resources; preserve originals.

Local before-B dirty snapshot:
tmp/phase-b-start-a2898e857bac498abe5b495c429a324c.
Local pre-handoff pause snapshot:
tmp/phase-b-pause-70079b04be4a48ca9ee051d8cd200144.
