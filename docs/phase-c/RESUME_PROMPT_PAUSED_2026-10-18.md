# Next recovery prompt — Phase C paused2026-10-18

Copy this when ready to explicitly resume:

---

Resume Phase C in D:\Code\pqcbridge-legacy-edge-cloud from the latest pause.
Read PROJECT_STATE.md, docs/phase-c/STATUS.md, PAUSE_HANDOFF.md, REVIEW_PROGRESS.md
and EXECUTION_SPEC.md. Keep codex/phase-c-management/HEAD5c12f8644d35ae85422318bbad934379067affa1
unless newer user changes exist; never reset them. A/B are already published.
C code is local/uncommitted and NOT accepted. Restore EXISTING paused
pqc-bridge-github unchanged only because of this explicit continuation; no duplicate,
no publication while active/unaccepted, no recommit of A/B, no automatic D work.

Preserve CLAUDE/docsagents, quota scripts/checkpoints, current README/docs layout,
original .env/keys/state/Compose/V1. No reset/clean/stash discard or state migration.
Use current12-file protected-input manifest in handoff. Docs English/user Chinese;
follow docs/development guide/template. Keep private/raw artifacts outside checkout.

Implementation is now present: issuer, catalog lifecycle/rollback/CLI, managed
configuration/bootstrap and shared runtime hooks. Do NOT redo missing-module work
from old handoffs. Latest full regression234passes13.51s, B compatibility19 and
observation2 actual Docker cases passed. Intermediate C17case lifecycle passed
before last review fixes; final matching17rerun was explicitly interrupted, has
NO complete result and its owned resources have been cleaned. Do not mark C done.

Prioritize fresh final17case run via scripts/phase_c/docker_probe.py, new external
runtime, native Docker/local cached image/no pulls/host ports/old volumes. Include
actual missing-key failure code in status/audit, unaffected second gateway TCP,
safe rollback/current credentials, overlap/retirement, active/new revocation,
restart antirollback, device/gateway disable, offline lease exact-event recovery
and managed certificate expiry. Preserve B immutable event/source/dedup state.

Then independent Standards/Spec FINAL re-reviews of current source and evidence.
Already repaired: atomic local certificate/token binding; new channel clears old
ACK even same version; stale proof=>Unknown; fixed safe failure reasons retained
and arbitrary diagnostic text rejected. observation_probe uses a disclosed external
wall-clock fixture, not elapsed endurance. Do not fake business proof or add
overlapping check counts. Do not rerun matching passed suites only for context;
rerun affected/full checks if new source changes or findings justify it.

Finish source/harness/evidence hash reconciliation, original-input/owned cleanup,
development record/runbook and reviewed explicit staging allowlist excluding user
work/secrets/raw state. Only after full C acceptance use Phase-Completion:C commit
and ordinary push to codex/phase-c-management, verify exact remote SHA. No PR unless
user changes current direct-push preference. D/prod/physical-device/endurance
acceptance remain future. Keep recovery records current.

---
