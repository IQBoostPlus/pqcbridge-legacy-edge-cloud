# Phase D — Human-Approved One-Hour Scope Amendment

Date: 2026-10-20. The human explicitly instructed: reduce the24-hour experiment
to one hour, then resume D from the handoff. This prospective change supersedes
the old D duration gate and the earlier human pause. It does not turn the old
interrupted run into a pass. Preserve PAUSE_HANDOFF.md and old raw results.

The revised controlled Docker/simulation acceptance is one fresh continuous
normal-load run of at least3,600 measured seconds (one record per5seconds,
at least720 sent, no missed scheduled readings). Keep existing service limits,
lease renewal every150seconds, resource observations, final accepted/ACK/unique
cloud-committed reconciliation, durable ACK p95<=1second, cold checkpoint and
ownership-scoped cleanup. Rotate both roles every900seconds, at least three
times within the run, so the shorter experiment still covers rotation.

The experiment proves at most one-hour operation in this owned lab. No24-hour
operation, six-hour rotation interval, production stability, physical-device
compatibility or full24-hour retry-horizon exercise is established. The24-hour
retry TTL, certificate bounds, deduplication retention and all security contracts
are unchanged. Existing100-sample formal tests and600-second outage gates remain.
Historical Phase A planning and pause records remain evidence of earlier scope;
this explicit amendment controls the current D duration acceptance.

Implementation default is3,600seconds; --diagnostic remains35seconds and cannot
satisfy acceptance. Evidence records acceptance_profile, acceptance_seconds,
rotation_interval_seconds, full_one_hour_gate and full_24_hour_gate separately.
Never infer completion from progress, configured duration or elapsed host time.
Final independent Standards/Spec evidence reviews and exact-candidate GitHub
Linux CI remain mandatory before the authorized direct-main publication. No PR.
