# Current project state: Phase B complete

Updated: 2026-10-17, Asia/Singapore.
Phase B is accepted for the bounded owned Docker/simulated-device lab.
Independent Standards and Spec re-reviews found no remaining blockers.
Phase C/D have not started. No production or physical-device acceptance.

## Recovery authority

- Checkout: D:\Code\pqcbridge-legacy-edge-cloud.
- Branch: codex/phase-b-secure-path; published A baseline was
  6e4a48ffc0ec465d6d5d1c29f2272314cff6a601.
- Current acceptance: docs/phase-b/STATUS.md and REVIEW.md.
- Runbook: docs/phase-b/OPERATIONS.md; next prompt: RESUME_PROMPT.md there.
- PAUSE_HANDOFF.md and PAUSE_CHECKPOINT.json are historical October 16 records,
  superseded by this explicit October 17 resume and final acceptance.

## Completed B01-B06

Opt-in direct mandatory hybrid TLS1.3/mTLS services, certificate-to-gateway/device
authorization, immutable lab-v1 events, durable bounded gateway queue and cloud
deduplication/ACK, retry/backoff and expiry, protected loopback health and
separate delivery/readiness/exception status. Original V1 entry points retained.
New service command: python -m common.secure_bootstrap gateway|cloud --config ABSOLUTE_JSON.

Final verification: 179 complete host regression tests; 9 pinned Linux transport
checks; 19 actual normal application cases; 9 fault cases plus 1 exact before-send
crash; 7 runtime expiry/retry/identity/exception cases; 3 focused review regressions.
Do not sum overlapping API/application evidence into a reliability guarantee.
FINAL_AUDIT.json verifies current source/harness hashes, preserved inputs and
owned-resource cleanup. The two additional review defects were reproduced before
fixes and verified after: expired ACK transmission and health-request shutdown.

## Preservation and scope

Original README.md/CLAUDE.md edits and untracked docs/agents remain user-owned.
Original .env, keys, device/cloud state, Compose and V1 implementation retained.
No reset/clean/stash discard, old-state migration or original-stack deployment.
Private synthetic credentials/raw logs are outside checkout under
D:\Code\pqcbridge-phase-b-artifacts; never stage them.
Recovery snapshots: tmp/phase-b-start-a2898e857bac498abe5b495c429a324c and
tmp/phase-b-pause-70079b04be4a48ca9ee051d8cd200144 (ignored local only).

Logical byte-quota refusal and process kills are proven within the lab; physical
ENOSPC, host power loss, 10-minute outage, 24-hour endurance, upgrades and lifecycle
rotation/revocation remain unproven/future as scoped in C/D. At-rest encryption is
not added. The unchanged source has no reading ACK or automatic reconnect.

## Authorized publication and next work

The existing pqc-bridge-github heartbeat is ACTIVE, unchanged 15-minute cadence.
It must defer while files/publication are active and publish only completed major
phases. A is already published; B qualifies after this final acceptance. Use a
scoped English commit with Phase-Completion: B, ordinary push on the B codex/
branch, and verify exact remote SHA. A local status file is not proof of push.
Check git log/remote ref and the delivery response for the resulting commit.
Never absorb the original user edits or publish secrets/state.
Wait for explicit user direction before starting C; do not auto-implement it.
