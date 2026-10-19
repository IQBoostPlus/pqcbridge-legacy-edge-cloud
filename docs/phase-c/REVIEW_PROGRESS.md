# Phase C review progress

Updated2026-10-19. Status: complete; final independent re-reviews passed.
This chronological record preserves earlier pending states. REVIEW.md, STATUS.md
and FINAL_AUDIT.json record final acceptance and supersede those interim states.
AI subagents reviewed Standards and Spec separately against C01-C05/lab contract;
their preliminary conclusions are not human review or production certification.

Final outcome: C-OBS-03/04 repairs passed247 complete regression,31 overlapping
catalog checks,4 actual observation/CLI cases,19 B compatibility cases and17 C
lifecycle cases on matching source. Both independent reviewers re-read the fixes
and found no implementation blocker. Root verified zero source/harness drift,
all12 protected inputs unchanged, owned cleanup and no matching validation runner.

## October 19 final review follow-up

Independent Standards review found no blocking violation; optional duplication
of fixed profile names does not justify a C refactor. Independent Spec review
identified two additional proof/status defects before acceptance:

C-OBS-03: a disconnected runtime with still-fresh historical ACK returned
Applying rather than Unknown. The extended actual observation probe reproduced
this in observation-disconnect-red.json (the two prior checks passed, the new
disconnect check failed; owned cleanup verified). Runtime now includes current
disconnection in the Unknown condition; final green verification is pending.

C-OBS-04: catalog observations omitted the runtime channel bind time/state and
could accept a never-observed old-channel ACK after same-version reconnect.
Catalog success must require current-channel Effective proof and ACK at or after
management_applied_at. A bounded public-API fail-first regression reproduced four
refusal gaps. Repair, matching actual CLI proof checks and final re-review are
pending. Final lifecycle evidence will be rerun on these fixes; old matching
234/B19/observation2 results are now historical for the changed source.

## October 18 preliminary review and repairs (historical)

## Standards

No confirmed blocker in the preliminary catalog/issuer/provider/runtime review.
Atomic expected-local-fingerprint binding was verified by public provider tests.
Reviewer observed same-version channel replacement could reuse an old channel ACK.
Root reproduced it through actual protected health, then changed every successful
new channel binding to clear ACK proof and refresh applied_at. Green regression
passes. Final-source standards re-review has NOT been performed since these fixes.

## Spec

C-OBS-01: stale ACK evidence returned Applying instead of required Unknown.
Actual external-clock health red reproduced it; runtime now returns Unknown and
green passes. Offset is a controlled external clock fixture, not elapsed endurance.
C-OBS-02: a fresh same-version connection reused the previous connection's ACK.
Actual cloud stop/start red returned Effective without a new event. Now Applying
until current-channel real ACK; separate green passes.
C-DIAG-01: catalog Failed proof omitted failure reason required by C02. Runtime
now exposes fixed safe management_failure_reason and catalog retains approved
failure_reason in status/evidence/audit. Arbitrary diagnostic/secret text refused.
Catalog focused18 passes; actual final matrix prefix reportedly passed the real
missing-key code/audit check, but complete final result was interrupted and must
be rerun before acceptance. Preliminary Spec reviewer requested matching evidence
and final re-review; neither is complete for the whole phase.

Windows test fixture wall-clock resolution caused one positive ACK timestamp to
equal apply_at in the first full batch (229pass/1fail). Bounded external clock
advance fixed the fixture; production strict ACK>apply was retained. Latest full
suite234 passed13.51s. Preserve historical failed/harness records, do not relabel
them as final acceptance. No further code changes should be inferred from pause.

C-ACCEPT-01 final evidence follow-up: the first final17 run selected the same
profile on rollback. Its report/audit are preserved under before-distinct-rollback
names. The strengthened final17 run actually restores standard to conservative,
retains current credential and verifies fresh ACK/unaffected group. Standards
reviewed the harness and Spec independently verified the new evidence; closed.
No application code changed; matching247/B19 remain valid and observation4 was
refreshed for exact shared-harness identity. FINAL_AUDIT was rebuilt afterward.
