# Project state: Phase A resumed

Updated: 2026-10-16, Asia/Singapore.
Status: **RESUMED by explicit user instruction on 2026-10-16.**
Current execution status is maintained in `docs/phase-a/STATUS.md`.
The sections below retain the pause handoff as historical recovery context;
their pending notes are superseded by the current execution status as work
is completed. The earlier pause is no longer an instruction to stop.

## Current authority and scope

The user authorized Phase A with subagents, then clarified:

- Deployment is Docker.
- Devices may remain simulated for this iteration. Do not require physical
  hardware or claim real-device/industrial-protocol compatibility.
- Keep cybersecurity work within safe local defensive validation using owned
  services and synthetic credentials/data. Do not broaden probing.
- Historical pause instruction: stop and save completed work. The user has
  now explicitly requested continuation from that point.

The original subagents were interrupted at pause. On resumption, new agents
`docker_validation`, `standards_review` and `spec_review` were assigned bounded,
exclusive work. No successful earlier suite is being rerun just for context.

## Repository and preservation

- Checkout: `D:\Code\pqcbridge-legacy-edge-cloud`.
- Branch: `codex/phase-a-validation`.
- HEAD: `681986bc0119d51913140575f98720c90fb378ac`.
- Pre-existing changes: modified `CLAUDE.md`, modified `README.md`, untracked
  `docs/`. These have been preserved.
- Phase A additions are saved but **untracked/uncommitted** under
  `scripts/phase_a/` and `docs/phase-a/`, plus this state file.
- No application-source changes, commits, pushes or original-state migrations
  were performed. Do not reset, clean or discard untracked files.
- Original 70-file preservation snapshot, manifest and initial diff:
  `D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z`.
  The successful baseline run verified all 70 original file hashes unchanged.
  Original `.env`, device sequence state, cloud key and existing configuration
  were not used as experiment state.

## Completed and saved work

### A-01: Current simulation baseline

Report: `docs/phase-a/A01_BASELINE.md`.
Tools: `scripts/phase_a/baseline.py`, `baseline_child.py`,
`baseline_contract_test.py`.
Evidence: `docs/phase-a/evidence/baseline/result.json`.

- Existing pytest suite: **136 passed**, zero failures/errors/skips; 8.27 s
  reported by pytest. This is current observed evidence, not the historical
  README count reused as a new run.
- Real Device/Gateway/Cloud subprocess smoke: **3 cloud readings**, sequences
  1-3. Fresh synthetic credentials and a copied runtime were used.
- Two additional harness contract checks passed separately from those 136.
- Health binding was adapted only in child processes to loopback; this does
  not validate the original wildcard-bind deployment or access controls.
- Smoke children stopped; recorded binds were loopback. A deliberate device
  shutdown produced one gateway reset/error metric, disclosed in the report.
- Isolated Compose config validation passed. Container runtime was unavailable
  at that check; no image build or container acceptance was claimed.

### A-02: Scenario extraction

Report: `docs/phase-a/A02_SCENARIO.md`.

The repository scenario is a one-device temperature simulation, default
five-second interval, custom JSON-lines TCP protocol. It is not MQTT/Modbus
or a real industrial-device integration. The user's later Docker/simulation
decision is authoritative and overrides older real-device prerequisite wording.
Business budgets, retention and recovery/SLO thresholds are not frozen.

### A-03: Risk/evidence mapping

Report: `docs/phase-a/A03_RISK_EVIDENCE.md`.
Tool: `scripts/phase_a/security_probe.py`.
Evidence: `docs/phase-a/evidence/security/security-result.json`.

- 14 defensive observation assertions reproduced the documented weaknesses
  and controls. Exit 0 means reproduction succeeded, **not security passed**.
- Current findings include authentication-request replay/session substitution,
  missing effective key confirmation, recovery of synthetic historical sessions
  after disclosure of a reused synthetic KEM private key, and metadata/sequence
  consistency failures. Gateway/device authorization gaps are separately
  distinguished as static inference where appropriate.
- No remediation of application transport or release-security acceptance is
  claimed. No additional vulnerability probes should be run while paused.
- Cross-review fixed output safety in `security_probe.py`: resolve/reject a
  raw directory inside the checkout or one that already exists before writing.
  Targeted CLI refusals passed; existing sentinel bytes and protected targets
  were unchanged. No exploit rerun or full-suite rerun was needed for that fix.
- Existing dynamic evidence records the **pre-guard** script hash. The exact
  observed script is preserved externally as
  `security-runtime/security_probe.observed.py`; its hash matches the evidence.
  Current script changed only its output-directory guard. A report note about
  this provenance change is still pending.

### A-04: Local transport feasibility

Report: `docs/phase-a/A04_TRANSPORT_VALIDATION.md`.
Tool: `scripts/phase_a/tls_probe.py`.
Evidence: three JSON files under `docs/phase-a/evidence/transport/`.

- **27/27** checks passed across OpenSSL 3.5.3/3.5.2 in both endpoint directions.
- Actual TLS 1.3/X25519MLKEM768, mutual certificate validation and an encrypted
  message round trip were observed. Certificate/policy rejection cases include
  missing/untrusted/expired identities, wrong server hostname, TLS 1.2 and a
  conventional-only peer under mandatory-hybrid policy.
- 54 endpoint-log hashes matched saved results during independent read-only
  reconciliation. This is local Windows OpenSSL evidence, not application TLS
  integration, post-quantum certificate authentication or Docker acceptance.
- Windows Python's `ssl` links OpenSSL 3.0.11; the tested sessions used the
  separate OpenSSL executables. This distinction remains material.
- A review wording correction is pending: generated certificate signatures
  are RSA-2048/SHA-256 (PKCS#1 v1.5); TLS CertificateVerify used RSA-PSS/SHA-256.
  The current report conflates these in one sentence.

### A-05: Independent simulated peer and contract draft

Tool: `scripts/phase_a/legacy_probe.py`.
Report: `docs/phase-a/A05_LEGACY_AND_DELIVERY.md`.
Contract: `docs/phase-a/DELIVERY_CONTRACT.md` (**proposed, not frozen**).
Evidence: `docs/phase-a/evidence/legacy/legacy-result.json`.

- Independent encoding of the repository's simulated wire protocol reached
  the real gateway/cloud subprocesses. It does not import application protocol,
  crypto or sensor encoders, but shares the isolated launch helper.
- Three readings at five-second intervals matched cloud readback. Sample
  observation upper-bound p50/p95: 89.1584/102.1313 ms; 296 bytes per measured
  reading frame. HTTP/polling overhead is included; three samples are not an SLO.
- Separate 100-message burst: 0.0901255 s, observed 1109.5639 messages/s.
  This is a short diagnostic, not sustainable-capacity evidence.
- Five invalid/replay controls behaved as documented. Pre-risk-probe count was
  104. Two intentionally inconsistent inner metadata payloads were stored,
  final count 106, then ordinary sequence 107 was rejected. This supports
  A03-05; it must not be counted as 106 normal benchmark messages.
- Raw completed result was copied into the repository while saving this pause.
- The delivery document records candidate identity, event ID, transaction,
  ACK, pending/retry and quarantine semantics. No durable queue/ACK/cloud
  deduplication implementation has been added.

## Docker follow-up interrupted before delivery

The user selected Docker as the deployment environment. The last completed
read-only daemon check returned `Server=null` and a missing
`dockerDesktopLinuxEngine` pipe. Docker Desktop is installed.

The parent requested a hidden launch of the installed Docker Desktop app.
The launch command returned successfully, but engine readiness was **not
subsequently established**. Do not equate the launch request with a running
Docker engine or successful deployment.

The transport agent was preparing an isolated Docker runner/report under
`scripts/phase_a/docker_probe.py` and
`docs/phase-a/A06_DOCKER_SIMULATION.md`. Neither file existed at the final
pause inventory. No Docker execution result, container image/version proof,
Linux hybrid-TLS run or application adapter was delivered.

On resume, Docker work must use a unique project/network/volume namespace,
fresh synthetic state in a new writable temporary directory, no published
host ports where unnecessary, and explicit owned-resource cleanup. Preserve
the original Compose project, root `.env`, volumes, keys and device state.
Do not run the original bootstrap, which writes root `.env`.

## Review and execution state at pause

Two independent review axes ran over uncommitted additions: standards/
correctness and Phase A requirements. Review is not final acceptance.

- Output-directory safety finding was fixed and narrowly checked.
- Certificate-signature wording correction remains pending.
- A02 and EXECUTION_SPEC still contain real-device gate wording predating the
  user's simulation decision; update that wording on resume without claiming
  real-world compatibility. SHORT_TERM_PLAN still says all tasks Not started:
  it is a preserved planning snapshot, not the current execution status.
- New A05/contract documents have not received final cross-review.
- Before the Docker follow-up, a read-only audit found no listeners on the
  35 recorded experiment ports and no Phase A Python/OpenSSL processes.
- A final pause-time CIM process query was unavailable in the restricted
  environment (`cannot access CIM resources`). Therefore the earlier cleanup
  evidence is retained, but no new OS-wide process-cleanliness claim is made.
  No destructive or broad process termination was attempted.

## Resume order (only after user instruction)

1. Read this file and `docs/phase-a/EXECUTION_SPEC.md`; check repository status
   and preserve all existing additions. Do not repeat successful suites merely
   to reconstruct context.
2. Reconcile simulation scope/status in A02, EXECUTION_SPEC and the plan's
   current-status navigation; apply the two report provenance/wording fixes.
3. Complete final review of A05/contract and retain open decisions as such.
4. Establish actual Docker availability. Implement the isolated simulation
   runner, demonstrate real container readback and record actual image/library
   versions. If unavailable, record the exact blocker rather than a pass.
5. Validate hybrid mTLS using the actual selected Linux runtime and application
   integration boundary before closing the transport selection gate. Keep
   mandatory hybrid policy and fatal identity verification; no silent fallback.
6. Freeze the remaining simulation delivery/resource parameters with evidence;
   reconcile Phase A status. Phase B has **not started** and remains gated.

Private keys and credential values remain outside source-controlled reports.
Project documents are English; communicate with the user in Chinese.
