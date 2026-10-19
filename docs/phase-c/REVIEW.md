# Phase C — Final Standards and Spec Review

Date: 2026-10-19. Source baseline:
`5c12f8644d35ae85422318bbad934379067affa1`, with the explicit C working-tree
allowlist. Source review passed after repairs. Final evidence review additionally
required a distinct live rollback profile; the strengthened17-case run passed.
Spec independently verified the profile change, fresh ACK and unchanged group.
Whole-phase runtime acceptance is
recorded separately in [STATUS.md](STATUS.md) and [COMPLETION.md](COMPLETION.md).

## 1. Method and Provenance

Root coordinated two independent AI reviewers, `c_final_standards` and
`c_final_spec`, using the code-review skill. They read the untracked C modules,
tests, probes and shared runtime diff directly, rather than treating an empty
committed diff as absence of changes. Reviewers did not modify implementation or
run Docker. A separate bounded worker repaired catalog proof validation; root
integrated runtime and public observation adapters. This is AI-assisted review,
not a human security assessment or production certification.

Standards sources: `CLAUDE.md`, domain guidance, the development record guide and
template, existing B conventions, and the skill's heuristic smell baseline. Spec
sources: C01–C05 in the short-term plan, the roadmap's evidence rules and
[EXECUTION_SPEC.md](EXECUTION_SPEC.md). Root verifies runtime evidence and cleanup.

## 2. Standards

Final follow-up verdict: **Pass, no blocking finding.** Review found the opt-in
TLS bootstrap, preserved B defaults, immutable source namespaces, role-specific
credential mounts, bounded state, safe diagnostics, channel proof and owned
cleanup consistent with repository requirements. Rejected observations preserve
status/audit; successful channel state/time survives status, audit and reopen.

Optional maintenance observation: fixed profile names occur in both
`common/management.py` and `common/managed_config.py`. They match; consolidation
could reduce future drift, but is not required for C acceptance. This judgement
call is not a documented-standard breach or a deployment blocker.

## 3. Spec Findings and Resolution

| ID | Observed defect and consequence | Repair and verification boundary | Final source verdict |
| --- | --- | --- | --- |
| C-OBS-01 | A stale prior ACK returned Applying rather than Unknown | Runtime freshness branch repaired; actual protected-health red/green uses disclosed runtime clock offset | Closed |
| C-OBS-02 | A same-version reconnect retained old-channel effectiveness | Every authenticated channel bind clears proof and refreshes applied time; actual cloud stop/start requires a new business ACK | Closed |
| C-DIAG-01 | Failed catalog proof omitted a useful safe reason | Fixed-code runtime/catalog diagnostics persisted to status/evidence/audit; arbitrary text refused; actual missing-key lifecycle checks require the code | Closed |
| C-OBS-03 | A newly disconnected gateway with fresh historical ACK returned Applying | Runtime reports Unknown on disconnection; actual cloud stop red failed that assertion, final observation probe checks it | Closed |
| C-OBS-04 | A previously unobserved old-channel ACK could be accepted by the catalog after reconnect | Require runtime Effective and channel applied time <= ACK <= observation, plus strict post-operator-apply and ACK nonreuse. Four fail-first public API cases exposed the gap; 31 catalog tests pass. Actual CLI rejects old proof and accepts fresh ACK | Closed |
| C-ACCEPT-01 | The first final lifecycle rollback created a new version but restored the same profile as the repaired failed migration | Strengthen the live harness to restore the earlier canary's different conservative profile, retain current credentials and require fresh business ACK | Closed; final17 passes |

Final Spec follow-up found no remaining confirmed implementation blocker. It
explicitly reserved whole-phase acceptance for matching completed lifecycle,
observation, B compatibility and full regression checks, source reconciliation and
owned cleanup. An earlier intermediate 17-case pass or interrupted final run is
not evidence of acceptance for the changed source.

## 4. Reviewed Source Identity

| Artifact | SHA-256 |
| --- | --- |
| common/secure_runtime.py | b6b150fa2e561ab3e8b5cafb39546a1ef292da8e50f075145ea8793d4f95635d |
| common/management.py | b0bf372714d36e10f8fbc7ad1bfdf06e857231d86d0d6f3901dba6ba19270c55 |
| scripts/phase_c/docker_probe.py | 0d1284a6c9a1a197ffc6bd20f3e7b97b1aaf0a10dccf1ff90137395f811ff54a |
| scripts/phase_c/observation_probe.py | 127e6e1b52beca09afad87c463f1ea8df17eeb90604e42da57723b756f17b0cb |
| tests/test_management.py | f0148fdbdeb1c43bcaa4affd7d34916cc68e02de69a501b6eba051aca01acef2 |

## 5. Acceptance Boundary

The local administrator remains trusted to obtain authentic protected health.
Catalog observations are not signed fleet attestations, and catalog status is a
bounded-age last observation rather than a live monitor. No physical-device,
production-security, endurance, host power-loss, Windows ACL or D acceptance is
derived from this review. [OPERATIONS.md](OPERATIONS.md) documents those limits and
safe failure/recovery procedures.
