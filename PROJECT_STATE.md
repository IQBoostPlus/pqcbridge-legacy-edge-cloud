# Current Project State: A–D Accepted in Simulation

Updated: 2026-10-21, Asia/Shanghai. Checkout: D:\PQC\pqcbridge-legacy-edge-cloud.
Current branch: main. D completion 87d33bfe5f6982cd743af5fa7ebafb30131fbb4b
was verified in origin/main history on this date. Its main CI run 39394824514
passed both test and Docker jobs. Later documentation commits may advance main;
never duplicate the existing Phase-Completion: D commit.

## 1. Current Authority

Read README.md, docs/PROJECT_REPORT.md, docs/SHORT_TERM_PLAN.md and
docs/ENGINEERING_ROADMAP.md for current summaries. Phase-specific authority is
each current STATUS/COMPLETION/REVIEW/OPERATIONS record; D additionally uses
SCOPE_AMENDMENT.md, RISKS.md and evidence/final-runtime-audit.json.
Historical pause handoffs and earlier pending records preserve provenance and
do not override accepted completion. Old D:\Code paths refer to historical
external runtime artifacts, whose presence is not assumed in this checkout.

## 2. Accepted Results

- A: simulated baseline, risk mapping, Linux hybrid TLS feasibility and lab-v1
  delivery contract. Target adapter 22/22; baseline 136 tests.
- B: mandatory TLS 1.3/mTLS/X25519MLKEM768, identity/device authorization,
  durable acceptance/queue, transactional cloud deduplication/ACK and bounded
  recovery/resources. Recorded regression 179; normal services 19/19.
- C: trusted local catalog/audit CLI, fixed versioned profiles, fresh
  current-channel business proof, rotation/revocation, canary and safe rollback.
  Recorded regression 247; observation 4/4; lifecycle 17/17. Completion and
  portability repair are published; see docs/phase-c/CI_FIX.md.
- D: offline simulation package, coordinated current-state cold recovery,
  strict receipt/schema refusal, same-schema upgrade/rollback and operator CLI.
  Recorded Windows/Linux regression 265 each; formal D 9/9; B 19/C 17.
  Real sustained run 1,800.000536 seconds: 360 sent/accepted/ACK/unique cloud,
  zero misses/pending/quarantine, three both-role rotations, ACK p95 0.475430s.
  Cold integrity and current-owner cleanup were verified.

These are recorded lab results; this documentation update reran no application
experiment. Do not repeat passed suites merely to reconstruct context.
No physical-device, ARM64, production, one-hour/24-hour endurance or current
vulnerability-clearance claim is established. The earlier interrupted/inconclusive
attempts remain historical; do not add their time to the accepted run.

## 3. Planned Next Milestone

docs/REAL_DEVICE_PLAN.md consolidates the 2026-10-20 local implementation
handbook and procurement plan: two real Modbus sensors, Orange Pi ARM64,
AMD64 cloud, product projection/Web/RBAC, cited read-only AI, human-approved
fixed actions and a new physical 48-hour evaluation. These are planned modules
and gates, not delivered capabilities or authority to start implementation.
Storage/deduplication and management-audit maintenance are long-run blockers.
The D installer remains simulation-only; do not relabel it as a physical release.

## 4. Preservation and Publication

Follow the current CLAUDE.md and development documentation guide. Preserve V1,
original configuration, source/cloud state, credentials, user edits and archived
evidence. Private issuer/state/raw logs/vaults remain outside Git. Never reset,
clean, discard a stash, force-push, clear guards or migrate original state to
recover context. Historical D records intentionally retain an older network
and four volumes; current-owner cleanup is not an assertion about today's host.

For authorized documentation updates, inspect actual remote main, use an
explicit reviewed file allowlist, validate links/evidence/whitespace, and preserve
all remote commits. Use a normal direct push and verify the exact remote SHA.
For the D completion release, exact-candidate CI was a gate and is now recorded
as passed. Further documentation publication must check its own CI; historical
runtime passes do not establish that a new commit's CI completed.

Historical publisher/receipt references are provenance. Inspect actual app state
before making automation claims; do not create, resume or alter an automation
as part of a documentation synchronization. Keep publication receipts outside
tracked documents to avoid self-referential SHA-only commits.
