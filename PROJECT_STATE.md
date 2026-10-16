# Project state: Phase A technical selection complete

Updated: 2026-10-16 21:37, Asia/Singapore.
Current authority: user explicitly resumed after the earlier pause. Phase A is
now complete within the Docker/simulated-device technical-selection scope.
Phase B has NOT started. Current results: docs/phase-a/STATUS.md.
Future handoff: docs/phase-a/RESUME_PROMPT.md.
Historical pause handoffs/manifests are superseded, preserved under
 docs/phase-a/handoffs/.

## Stage-completion GitHub publication authorization

On 2026-10-16 the user explicitly requested automatic GitHub publication after
each completed major phase A/B/C/D. Active thread task: `pqc-bridge-github`,
checking every 15 minutes. This supersedes older no-auto-commit/no-push wording
only for scoped, verified phase-completion commits and ordinary pushes to
origin IQBoostPlus/pqcbridge-legacy-edge-cloud. Current completed A is eligible
for its first check; creation of the task is not proof of an actual Git push.

Do not start the next implementation phase as part of publication. Require
phase acceptance evidence and Standards/Spec reviews, preserve unrelated dirty/
staged work, stage only reviewed explicit phase paths/hunks, exclude credentials
and raw state, and push a codex/ branch without force or automatic merging.
For current A, preserve pre-existing README.md/CLAUDE.md and unrelated docs
changes. Use a Phase-Completion trailer for idempotence and verify the exact
commit SHA against the remote branch. Keep failed local commits for retry;
report genuine publication failures without discarding or rewriting user work.
A later explicit pause/cancellation overrides this standing authorization.
Publication SHA/results are recorded in the conversation to avoid timestamp-only
commit loops. The completion snapshot below predates automatic publication.

## Scope and preservation

The user authorized Phase A with subagents, Docker deployment and simulated
devices. All probes used owned local services and synthetic identities/data.
No physical-device or industrial-protocol compatibility claim. No original
application/config/key/state edits, original Compose deployment, commits/pushes,
reset/clean/stash cleanup or state migrations. Do not discard untracked files.

Repository: D:\Code\pqcbridge-legacy-edge-cloud
Branch: codex/phase-a-validation
HEAD: 681986bc0119d51913140575f98720c90fb378ac
Pre-existing modified CLAUDE.md/README.md and untracked docs/ are preserved.
Phase A scripts/reports and this file remain uncommitted.
Original 70-file snapshot, manifest and initial diff:
D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z
Final comparison: none missing; only intentional docs/SHORT_TERM_PLAN.md
status/scope edits differ. Original .env, keys and device sequence state preserved.

## Completed evidence: do not rerun merely for context

- Existing suite136 passed; two separate baseline contracts; real subprocess
  device/gateway/cloud smoke. Child-only loopback health adaptation is disclosed.
- A03 fourteen observation assertions reproduced open risks, not fixes.
  Output-destination guard fixed narrowly; observed pre-guard provenance retained.
- Windows OpenSSL3.5.3/3.5.2 three9-case suites:27/27. Python Windows ssl3.0.11
  did not carry these sessions. RSA certificate/CertificateVerify distinction fixed.
- Independent simulated peer: three readings/5sec, measured upper-bound
  p50/p95 89.1584/102.1313ms,296-byte frames; separate burst100/0.0901255sec
  is not sustained capacity. Risk controls changed counts104->106 deliberately.
- Original three Dockerfiles actually built/run separately; exact first3 readings
  matched cloud snapshot; total device generation6 includes stop grace. Fresh
  internal network/volumes/credentials, no host ports or original bind mounts.
  Thirty application/config/state inputs unchanged; owned resources removed.
- Six Docker CLI contract checks passed, including native Windows executable
  resolution. Old WinError193 occurred before Docker execution, not daemon proof.
- Final Linux Python adapter22/22:3 positive/11 TLS rejection/8 config refusal.
  Verified both peer certificates/DER identities, exact bytes, TLS1.3 and actual
  X25519MLKEM768 negotiation. One additional focused cleanup-timeout regression
  passed; no daemon failure was induced.

## Selected adapter and exact recovery pointers

Use direct Python ssl linked to OpenSSL3.5 with fixed official OPENSSL_CONF
system_default policy before process/library initialization. Python's public
set_ecdh_curve does NOT accept X25519MLKEM768 on this runtime; the proven route
is configuration with exact-byte startup guard, TLS1.3-only, CERT_REQUIRED,
hostname checks, no enabled early data and num_tickets0. Do not substitute
cryptography ML-KEM imports or default hybrid preference as policy evidence.
No proxy/plaintext backend or propagated identity header exists in this proof.
Python exposes verified identity but no public negotiated-group getter here;
CLI traces corroborate actual group, including ServerHello NamedGroup4588.

Host entry: scripts/phase_a/linux_tls_host.py
Inner probe: scripts/phase_a/linux_tls_probe.py
Focused regression: scripts/phase_a/linux_tls_host_test.py
Final evidence: docs/phase-a/evidence/transport/linux-full-e3864eb459b7.json
Final raw: D:\Code\pqcbridge-phase-a-artifacts\linux-tls-e3864eb459b74570ac90b3d0b4ddacd0
Pinned image:
sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
Python3.12.14; Python ssl/CLI OpenSSL3.5.7; Linuxx86_64/WSLkernel6.18.54.1.
Probe SHA459781ad12597fbd5a273a0bb96d15deaeeec3841d7e91613a676ab0ad1da201
Host SHA5ffa2737652222008a07571a45dde9bd960f02597c0f5ea3fe6f5ea1e6c6bec0
Raw report SHAdc19e778a6fdb00ce6a9dde6c71e5c7d517ad8ef4f2688b983e5a14fb462f597
Observed source bytes are saved externally. Repo evidence is a sanitized copy
omitting public certificate PEM; raw remains unchanged and its hash is recorded.
Generated private keys only existed in container tmpfs and were destroyed.
All actual runs reported cleanup_verified=true. Do not sum repeated suites.

Successful baseline Docker evidence:
docs/phase-a/evidence/docker/docker-result-native-cli.json
Raw: D:\Code\pqcbridge-phase-a-artifacts\docker-ad91c651551244cd81f91f150719c24c
Project pqc-a-f464a7c89a57ba9a; Desktop4.91.0/Engine29.8.0 at that run;
Python3.12.14/cryptography50.0.1; Python OpenSSL3.5.7 vs crypto OpenSSL4.0.2.
Its earlier WSLkernel6.6.87.2 is a separate snapshot. Unique image tags retained;
containers/network/volumes removed. No Docker repair/reset/config change performed.
Native CLI: C:\Program Files\Docker\Docker\resources\bin\docker.exe
Sandbox pipe access required reviewed elevated execution. Do not auto-repair
Docker or pull new images. Future raw runtimes must be fresh external directories.

## Design and review outcome

DELIVERY_CONTRACT.md selects lab-v1 exact encoding/IDs/digest/ACK, SQLite atomic
WAL/FULL writes, incarnation/reset and 64-bit positive source-sequence policy
(initial0, maxforwardincrement1024, outliers refused without state advance),
finite row/disk quotas, explicit source connection close on admission refusal,
unknown in-flight-loss disclosure, fixed24h retry, <=30sec backoff, expiry,
experimental performance/recovery budgets, and packaging/upgrade boundaries.
These are B-D requirements, NOT current queue/ACK/durability/recovery capability.

Separate Standards and Spec agents reviewed final22-case evidence, current source
and raw hashes, rejection semantics/identity, cleanup, contract choices and scope.
No remaining actionable issue or technical selection gate. The cleanup-exception
P2 was fixed and narrowly tested; unknownCA/expired/hostname are verified via
specific codes20/10/62. Intermediate client CONNECTION ESTABLISHED does not mean
server accepted client cert; rejected Python endpoint never consumed application.
REVIEW.md records separate axes. These are automated reviews, not external human
security approval. Original A03 risks remain open until future remediation.

## Next work requires Phase B instruction

Start with B01 integration of the selected channel, startup policy/readonly
configuration and verified gateway->allowed-devices mapping; remove alternative
plaintext ingestion. Then B02/B03 durable queue/cloud transaction/ACK and B04-B06
retry, quotas, health and full fault matrix. C handles enrollment/lifecycle/
rotation/revocation. D handles packaged upgrade/recovery, budgets/endurance and
engineering release. No production/pilot security,24h run, durable delivery or
real-device acceptance has been claimed. Do not silently start B from this state.
