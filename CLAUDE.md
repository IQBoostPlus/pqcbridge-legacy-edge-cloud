# CLAUDE.md

This repository contains an **AI-generated baseline** for the course
project "Legacy System Modernization for PQC & LLM-Assisted
Development" (Software Development, Maintenance & Operations).

- The generating prompt is `prompt/P01 - Initial Baseline Generation.md`.
- All code is AI-assisted output awaiting final student review; it
  has been through the P02 review, P04 implementation, P05
  independent verification, P06 remediation, P07 consolidation and
  P08 adversarial testing/remediation, but must NOT be presented as
  secure or production-ready (see README.md §7 limitations and the
  `review/P02`–`review/P08` reports).
- Every significant AI interaction must be documented by the student
  team (README.md §9).

## Sprint 2 dashboard work

Before planning, implementing or reviewing Sprint 2 dashboard work, read
`docs/sprints/sprint-2/SPRINT_GOAL.md` for the credibility-first priority,
metric evidence gate and current delivery state. Read
`docs/sprints/sprint-2/USER_UNDERSTANDING_EXPERIMENT.md` when conducting or
reporting comprehension evaluation, and `docs/sprints/sprint-2/TEAM_REVIEW.md`
when recording group decisions. Attribute discussion drafts, actual participant
responses, technical checks and team/PO acceptance to their respective evidence.
Maintain the Sprint 2 backlog, risks, LLM evaluation and retrospective records
through bounded delegated work with exclusive file ownership during build
batches. Integrate evidence before updating completion claims, README or
affected instructions. Repository documentation is English.

The implemented indicator audit uses `summarize().evidence` and
`createEvidenceReport()` in `dashboard/model.mjs`; keep reporting rules shared
with role views. Read `docs/sprints/sprint-2/VERIFICATION.md` before reporting
current delivery evidence. Use the participant kit in the experiment record for
actual understanding sessions; source checks and browser role walks establish
technical behavior only.

## Sprint 1 dashboard work

Before planning, implementing or reviewing the course dashboard, read
`docs/sprints/sprint-1/SPRINT_GOAL.md` for the approved scope, acceptance
boundaries and current delivery state. During each build batch, delegate
bounded subagent work for the backlog, risk/decision log, LLM evaluation and
retrospective actions listed there; integrate and verify their evidence before
updating completion claims. Update README and affected project instructions
in the same batch. Repository documentation is written in English.

The Sprint 1 dashboard uses synthetic data independently of the existing
Device/Gateway/Cloud prototype. Use the local-to-Jira mapping in
`docs/sprints/sprint-1/BACKLOG.md` for SCRUM Sprint 1. Record verified Jira
changes and actual meetings and PO decisions as separate events.

For dashboard startup, reporting rules and test commands, read
`dashboard/README.md`. Recorded runtime/check results and their limits live in
`docs/sprints/sprint-1/VERIFICATION.md`. Run the dashboard separately from the
prototype. The interface uses Vue and Vite, and its model tests use Node's
built-in runner without crypto/backend services.

## Prototype commands

- Install: `pip install -r requirements.txt`
- Test: `pytest` (from the project root; `pytest.ini` sets the pythonpath;
  136 passed at the end of P08)
- Run (3 terminals, in this order):
  1. `python -m cloud.cloud`   (port 5002, health 8002)
  2. `python -m gateway.gateway` (devices 5001, health 8001)
  3. `python -m device.device`
- Docker: `docker compose up --build`

Gateway-to-cloud authentication (P08 BF-01) and config-driven
credentials (P08 BF-03A) are enabled by default using the committed
`common/demo_*_keys.json` demo material; supply real keys via
`GATEWAY_KEYS_FILE` / `GATEWAY_KEYS_JSON`, `GATEWAY_KEY_HEX`,
`DEVICE_KEYS_FILE` / `DEVICE_KEYS_JSON` and `DEVICE_KEY_HEX`.

## Architecture

Legacy device (ChaCha20-Poly1305, no ML-KEM) → Edge gateway
(ML-KEM-768 + fallback) → Cloud (ML-KEM-768 decapsulation, in-memory
store). Plain TCP, JSON-lines protocol, no TLS. See README.md for
details and known limitations.
