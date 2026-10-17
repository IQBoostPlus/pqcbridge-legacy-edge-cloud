# Phase A review record

Date: 2026-10-16. Baseline HEAD: 681986bc0119d51913140575f98720c90fb378ac.
Review scope is the uncommitted Phase A scripts/reports plus the intentional
SHORT_TERM_PLAN status/scope clarification. Existing user README/CLAUDE edits
are preserved and excluded from attribution. No new commits were created.

These are separate automated subagent review axes, reconciled by the integration
owner. They are not external human approval, a dependency security audit or a
production release authorization. Original planning task IDs are not GitHub Issues.

## Standards and correctness

Earlier findings repaired and checked:

- Security raw-output destination must be new and outside the checkout; existing
  sentinel/protected paths were preserved by narrow refusal checks. Original
  dynamic evidence retains its observed pre-guard script provenance.
- Docker log-collection failure must not skip the independent owned cleanup attempt.
- Windows Docker resolution must select docker.exe, not the adjacent POSIX shim.
  Six public CLI contracts passed with fake programs explicitly selected.

Independent review reconciled the actual successful Docker smoke with 36 raw
command records, image IDs, source hashes, exact pre-stop readback, no published
ports/bind mounts, internal network, ownership labels and empty post-cleanup
container/network/volume queries. Three verified readings are a snapshot; device
logs contain six including stop grace. No remaining issue in that Docker review.

Final Linux adapter review found no remaining actionable issue. The final
22/22 result, observed probe/host copies and source hashes match; the raw-host
SHA matches the sanitized report's provenance field. All 11 transport rejection
cases had the specific expected TLS failure, no Python accepted result and no
timeout false positive. Exact Python/Python bytes and certificate DER identities
were independently reconciled. Final source/host hashes are recorded in the
[Linux result](evidence/transport/linux-full-e3864eb459b7.json).

A P2 host-cleanup exception path was repaired: timeouts/OSError in cleanup no
longer bypass report persistence, independent remaining-resource query or a
nonzero failure outcome. The narrow mocked timeout regression passed once;
[recorded output](evidence/transport/linux-host-contract-tests.txt). No real
daemon failure was induced. Raw report remains unchanged externally; public
certificate PEM is omitted from the repository copy with the raw SHA recorded.
Standards outcome: no remaining actionable findings in the reviewed additions.

## Specification

Revised scope is Docker plus simulated devices, not physical-device compatibility.
A05's independent wire encoding and actual baseline readback are bounded lab
compatibility evidence. Lab-v1 records explicit event/storage/expiry/capacity and
experimental recovery/performance choices; runtime behavior remains B/D work.

Review repaired the following design/report inconsistencies:

- Separate RSA certificate signatures from TLS CertificateVerify algorithms.
- Align A02/A05 and contract from draft to selected lab-v1 design.
- Avoid requiring future B authorization/ACK integration to start B; require
  actual A04 adapter feasibility and verified peer exposure before selection.
- Keep retry backoff below the selected 60-second first-recovery target and
  distinguish first ACK recovery from complete backlog drain.
- Select concrete no-ACK source capacity refusal and anomalous sequence behavior;
  recheck confirmed both choices are concrete and consistent.
- Versioned Compose/digests, staged upgrades, unknown-schema startup refusal and
  no automatic downgrade are selected design boundaries; D proves the procedures.

Final separate Spec review parsed the 22-case Linux result (3 positive, 11 TLS
rejections, 8 configuration refusals), verified both-role group/identity evidence
and confirmed the scenario/contract choices. It found no remaining technical
selection gate for the revised simulation. Standards and Spec conclusions remain
separate; neither is external human security/release approval.

Spec outcome: revised Phase A technical selection criteria met. B-D implementation,
fault acceptance, lifecycle, endurance and engineering release remain future work.
