# Phase D — Human-Approved 30-Minute Scope Amendment

Date:2026-10-20. The latest explicit human instruction reduces sustained
testing to30minutes and resumes D. This prospective amendment supersedes the
original24-hour and later [one-hour amendment](history/ONE_HOUR_AMENDMENT.md),
as well as the earlier pause once a fresh safe quota Check passes. Root Check
2026-10-20T07:52:25Z was safe/exit0. Historical raw records remain unchanged.

Require one fresh continuous run of at least1,800 measured seconds, one reading
every5seconds, at least360 sent, no missed scheduled readings, existing service
resource limits,150-second lease renewal, resource samples and at least three
both-role credential rotations at450-second cadence. Reconcile all durable
gateway accepted/ACK/unique cloud-committed records, check durable ACK p95<=1s,
then take a verified private cold checkpoint before ownership-scoped cleanup.
The35-second diagnostic cannot qualify. Report full_30_minute_gate separately
from full_one_hour_gate and full_24_hour_gate; the latter two remain false.

No30-minute pass establishes one-hour/24-hour operation, long-term stability,
full24-hour retry-horizon coverage, physical-device compatibility or production
security. Retry TTL, dedup retention, credential bounds, mandatory hybrid policy,
100-sample formal checks and600-second outage gates are unchanged. This is a
human-directed scope reduction, not a measured conclusion that30minutes is
equivalent to longer testing.

The earlier one-hour attempt stopped updating after2050.603seconds and411records.
At resumption no supervisor, owned containers or final result existed, and its
state volumes remained. A final-state-vault directory exists, but this does not
establish a verified complete backup or final reconciliation/cleanup. Its exact
termination cause is unknown. Preserve it as inconclusive; do not retroactively
promote partial observations under this shorter requirement or add their time.

Final separate Standards/Spec reviews, risk disposition, synchronized current
documentation and exact-candidate GitHub Linux CI remain publication gates.
Publish only accepted scoped work by normal fast-forward direct main; no PR.
