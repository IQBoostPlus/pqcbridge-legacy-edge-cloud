# Phase A Execution Specification

Started and completed: 2026-10-16 (Asia/Singapore).
Status: **revised Docker/simulation Phase A technical selection complete**.
Current status and evidence: [STATUS.md](STATUS.md). Phase B has not started.

Source requirements: [short-term plan](../SHORT_TERM_PLAN.md), A-01 through
A-05, and [engineering roadmap](../ENGINEERING_ROADMAP.md). The user authorized
implementation with subagents. This execution covers Phase A validation and
supporting tools; Phase B implementation is outside this execution.

Scope clarification and resumption, 2026-10-16: the user selected Docker with
simulated devices, requested safe local defensive validation, and subsequently
resumed the paused work. Real-device/industrial-protocol compatibility is not
a prerequisite for this iteration and must not be claimed. Complete the
Docker simulation evidence and record transport/contract gates honestly.

## Preserved starting point

- HEAD: `681986bc0119d51913140575f98720c90fb378ac`.
- Starting branch: `main`; execution branch: `codex/phase-a-validation`.
- Pre-existing work: modified `CLAUDE.md` and `README.md`; untracked `docs/`.
- Byte-for-byte backup of 70 existing source/document/state files, manifest,
  and starting diff: `D:\Code\pqcbridge-phase-a-artifacts\20261016T065351Z`.
- Existing virtual environment, credentials, cloud key and device sequence
  state are preserved. Runtime evidence and generated credentials stay outside
  the repository. No commits, pushes, external deployments or changes to the
  original Compose stack are part of this execution. An isolated, uniquely
  named Docker validation project is authorized by the revised scope.

## Work graph and ownership

1. **A-01 / baseline subagent:** audit test side effects before execution;
   copy source into an isolated runtime; run the existing suite and a bounded
   Device -> Gateway -> Cloud smoke test. Own `baseline*` tools and A01 evidence.
2. **A-02 / integration owner:** extract the scenario from project primary
   sources. Distinguish documented defaults, measured values and missing pilot
   decisions. Do not choose a different legacy protocol without evidence.
3. **A-03 / security subagent:** map P02-P08 to current code and reproduce
   handshake risks with negative controls and fresh local credentials. Own
   `security*` tools and A03 evidence. Historical fixes are not new acceptance.
4. **A-04 / transport subagent:** demonstrate actual TLS 1.3 mTLS and hybrid
   negotiation, plus certificate/policy rejection, using an isolated installed
   stack. Own `tls*` tools and A04 evidence. Local success is not Linux deployment
   acceptance or application integration.
5. **A-05 / integration owner:** after A-01 launch isolation is available,
   implement an independent peer for the existing wire protocol; measure a
   bounded baseline and document the delivery/state contract. The user selected
   simulation for this iteration; independently encoded simulated peers are
   admissible lab evidence, never real-device compatibility evidence.
6. **Review:** independently review implementation standards and Phase A
   requirements, repair actionable findings, and reconcile the final evidence.

## Authorized validation boundaries

- Subprocess CLI: isolated runtime paths, environment, bounded execution,
  owned-process cleanup, and preservation of original files.
- Existing public device/gateway/cloud socket protocols and HTTP readback:
  valid data, invalid identity, replay, malformed input and readback results.
- Installed TLS implementation: real loopback TLS handshakes, application
  payload and negative authentication/mandatory-hybrid tests.
- Recorded-session cryptographic experiment: only freshly generated test
  keys and locally captured messages; no live deployment targets.

No permanent application interfaces, storage formats or security policy are
changed during these experiments. A child-only loopback health bind adaptation,
if needed because the baseline hardcodes wildcard health listeners, must be
reported explicitly and excludes unmodified-deployment acceptance.

## Completion and stop rules

Each report identifies source version, runtime, commands, observed results,
raw/sanitized evidence and limitations. Failed or unavailable checks remain
visible. Security weaknesses reproduced by a probe are open findings, not fixes.
All new documentation is English; user communication is Chinese.

The selected simulation scenario, actual isolated Docker baseline, target Linux
transport feasibility and lab-v1 delivery/persistence design now meet the revised
technical selection criteria; final Standards/Spec reviews are recorded in
REVIEW.md. Physical-device compatibility is deferred by user choice. This closes
Phase A only: B-D implementation/runtime acceptance and engineering release are
not implied, and Phase B has not started.
