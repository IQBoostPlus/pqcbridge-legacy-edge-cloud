# Phase D — Risk Register and Deployment Gates

Date: 2026-10-20. D is accepted for the explicit30-minute amended simulation scope. No production release is authorized.

## Accepted Gate Disposition

- D-GATE-01 closed: actual amended30-minute run, at least three both-role rotations,
  renewals, limits, durable reconciliation, p95, private cold hashes and owned cleanup
  verified in evidence/final-runtime-audit.json. No longer duration is established.
- D-GATE-02 closed: formal D9/9 and source/runner mapping independently reviewed;
  all37 application hashes match and the two runner status-only edits are proven.
- D-GATE-03 closed: separate final Standards/Spec reviews and matching GitHub Linux
  CI passed. Every final publication candidate still requires its own exact CI.
- D-GATE-04 closed for this simulation: package/recovery/permissions/alerts and
  dependency maintenance records reconciled against matching evidence. No current
  advisory clearance or production deployment approval is implied.

## Bounded Simulation Limitations

- D-RISK-01: trusted local recovery authority. A receipt verifies a selected
  checkpoint's integrity, not its global freshness. Lost latest authority or an
  unreconciled post-checkpoint gap blocks promotion; an old backup plus matching
  old receipt is insufficient. Never run two recovered copies as one site.
- D-RISK-02: host and administrator trust. Named volumes and restrictive host
  permissions reduce accidental access; there is no host-compromise protection,
  application queue encryption or physical power-loss guarantee. Real sensitive
  data and production issuer custody require a separate decision/verification.
- D-RISK-03: unchanged simulated source has no reading ACK, automatic replay or
  assured backpressure. Refused/in-flight loss may be unknown. Reconcile durable
  accepted data independently; do not equate sendall with durable acceptance.
- D-RISK-04: credential/authentication boundary. Hybrid TLS key exchange does not
  make RSA certificate signatures post-quantum. Offline revocation remains bounded
  by the current lease and scheduler; no instantaneous offline revocation claim.
- D-RISK-05: measurement scope. A single owned host, synthetic sensor and local
  network cannot establish physical-device compatibility, arbitrary scale or
  business performance suitability. The classical TLS comparison is an isolated
  benchmark; the services never permit a classical downgrade.
- D-RISK-06: release compatibility. v1→v1.1 exercises same-schema packaging,
  not an incompatible application/data migration. Unknown storage is refused;
  rollback always carries the newest state. V1 is not a data rollback target.
- D-RISK-07: advisory coverage. Dependency inventory and maintenance procedure
  do not establish a current vulnerability clearance. An applicable unresolved
  high-impact advisory blocks deployment beyond this isolated experiment.

These limits may be acceptable for the explicitly owned simulation after its
gates pass. They must not be silently relabelled as production acceptance.
