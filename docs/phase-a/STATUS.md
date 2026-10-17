# Phase A execution status

Updated: 2026-10-16 21:37 (Asia/Singapore).
State: **Phase A technical selection complete for the user-selected Docker
simulation scope. Phase B has not started.** Earlier pause instructions were
explicitly superseded by the user's continuation request.

## Scope and completed criteria

One Docker simulation site, one simulated device, one gateway and one cloud,
one-way telemetry. Only local owned services and synthetic credentials/data
were used. Physical-device/industrial-protocol compatibility is not claimed.

| Task | Result and boundary | Evidence |
| --- | --- | --- |
| A01 baseline | 136 existing tests passed; two separate harness checks; three-reading process smoke; later Docker smoke | [A01](A01_BASELINE.md) |
| A02 scenario | One device every five seconds; lab topology/trust boundaries and finite experimental budgets selected | [A02](A02_SCENARIO.md) |
| A03 risk mapping | 14 bounded observations reproduced open risks/controls; not security remediation | [A03](A03_RISK_EVIDENCE.md) |
| A04 transport feasibility | Windows OpenSSL 27/27; final target Linux Python adapter 22/22; direct TLS1.3/mTLS/mandatory X25519MLKEM768 selected | [A04](A04_TRANSPORT_VALIDATION.md) |
| A05 simulated compatibility and contract | Independent wire peer/readback; bounded measurements; lab-v1 design selected | [A05](A05_LEGACY_AND_DELIVERY.md), [contract](DELIVERY_CONTRACT.md) |
| Docker supplement | Three exact readings in pre-stop cloud snapshot, original images/source, isolated state, owned cleanup verified | [A06](A06_DOCKER_SIMULATION.md) |

Final Linux result: [linux-full-e3864eb459b7.json](evidence/transport/linux-full-e3864eb459b7.json).
It contains 3 positive transport cases, 11 actual TLS rejection cases and 8
configuration refusals. Both Python roles expose verified certificate identities
and exact bytes; actual group negotiation is evidenced, not inferred from a
cryptography import. One additional focused host cleanup-failure regression
passed; it is separate from the 22 TLS/policy cases.

Selected approach: direct Python ssl with a fixed OpenSSL configuration supplied
before process/library initialization, TLS1.3-only, required certificate checks,
mandatory hybrid group and no enabled early data/resumption. A04 records exact
versions, image identity, configuration, provenance, negative evidence and limits.
This adapter experiment is not integrated into the original application.

The selected lab-v1 design freezes event bytes/IDs/digest/ACK, source incarnation
and bounded sequence policy, atomic durable-state requirements, finite quotas,
explicit no-ACK-source admission refusal, expiry/retry, experimental recovery/
latency targets and packaging/upgrade boundaries. These are requirements for B-D,
not measured delivery/capacity guarantees.

## Review, preservation and earlier failures

Separate Standards and Spec agents completed final review with no remaining
actionable issue or technical selection gate in scope. The integration owner
reconciled reports and original-file preservation. See [review record](REVIEW.md).
These are automated reviews, not external human approval or production acceptance.

Latest original-manifest comparison: 70 files, none missing; only intentional
scope/status edits to docs/SHORT_TERM_PLAN.md changed. Original application,
configuration, keys, device state and user README/CLAUDE edits are preserved.
Work remains uncommitted; no commit/push or original-stack migration occurred.
Experiment containers/network/volumes were removed with ownership checks;
unique baseline images are retained. Earlier startup failures, WinError193,
certificate-provisioning and assertion-development failures remain historical
evidence and are not counted as successful checks. Historical pause handoffs
and their manifests are retained under handoffs/; they do not override this state.

## Automatic publication follow-up

The user subsequently authorized phase-completion GitHub publication. Active
thread task pqc-bridge-github checks every 15 minutes and includes completed A
in its first check. No verified publication is claimed by this setup record;
actual branch/SHA/remote verification is reported in the conversation. This
changes publication authorization, not Phase B implementation scope. See the
current policy in PROJECT_STATE.md.

## Next authorized boundary

Phase A is complete. Next planned work is B01: integrate the selected channel
and map verified gateway identities to permitted devices, followed by the lab-v1
durable queue/ACK/fault matrix. The present request did not start Phase B.
The original app's custom transport and A03 risks remain open; production/pilot
release, business authorization, durability, recovery, rotation/revocation,
resource-budget acceptance and 24-hour operation have not been accepted.

Recovery context: [PROJECT_STATE.md](../../PROJECT_STATE.md).
Future handoff prompt: [RESUME_PROMPT.md](RESUME_PROMPT.md).
