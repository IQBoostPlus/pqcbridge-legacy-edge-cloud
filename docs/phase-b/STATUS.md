# Phase B execution status

Updated: 2026-10-17 (Asia/Singapore).
State: **COMPLETE and accepted for the Docker/simulated-device lab scope.**
Separate Standards and Spec re-reviews have no remaining blockers.
Publication uses the standing scoped phase-completion authorization; verify the
actual GitHub branch SHA rather than treating this document as push evidence.
Current branch: codex/phase-b-secure-path. C/D have not started.

## Implementation and acceptance

| Work | Result | Matching evidence |
| --- | --- | --- |
| B01 | Mandatory hybrid TLS1.3/mTLS bootstrap, verified certificate registry, no plaintext engineering receiver | transport-resume.json; docker-resume-current.json; runtime-final.json |
| B02 | Immutable lab-v1 event, atomic persistent queue/source state, bounded refusal/quarantine | Full regression; fault-resume-current.json; fault-before-send-current.json |
| B03 | Transactional cloud business/dedup storage, exact duplicate ACK, conflict rejection | Normal and fault matrices |
| B04 | Same-event retries, exponential application-failure backoff, restart/half-open/lease/certificate expiry | Fault and runtime matrices; boundary-delayed_commit-green.json |
| B05 | Frame/deadline, worker/row/byte limits; protected loopback management; bounded shutdown | Transport, fault, boundary-worker_limit-green.json, boundary-health_shutdown-green.json |
| B06 | Separate liveness/readiness/connectivity/business status, safe reason metrics and unknown loss | Normal and runtime matrices; exception reconciliation |

## Final verification

| Verification | Observed result |
| --- | --- |
| Complete existing/new host suite | 179 passed in 7.69s on final application source |
| Pinned Linux transport API | 9/9; Python3.12.14/OpenSSL3.5.7; required X25519MLKEM768 observed |
| Actual unmodified normal applications | 19/19; short outage10.641s, drain3.156s; coalesced source socket remains open |
| Controlled application fault matrix | 9/9; plus exact durable-before-first-send crash1/1 |
| Actual expiry/retry/identity/exception matrix | 7/7; actual short-lived certificate and active lease clipping |
| Final review boundary regressions | 3/3; expired ACK blocked, graceful HTTP-trickle shutdown0.687s/exit0, connection overload/recovery |

All final evidence is under [evidence/](evidence/). [FINAL_AUDIT.json](evidence/FINAL_AUDIT.json)
matches copied source/harness hashes to current files and records immutable app
images. Original nine protected inputs are unchanged; no Phase B owner containers,
networks or volumes remain. Unique verification images are retained by policy.
Transport reader trickle deadline observed0.200741s. Runtime lease-clipped TLS
frame closed in4.382s; application-failure retry intervals observed1.861/3.724/6.727s.

The main fault run ends accepted8=acknowledged8=committed8 with pending0/quarantine0.
The intentional authorization mismatch ends accepted4=acknowledged3+pending0+
quarantined1, cloudcommitted3 and readinessfalse. These are separate fresh labs.
Instrumentation pauses/delays real public storage methods, then uses actual
SIGKILL/restart or real network replies. It is disclosed separately from normal
unmodified service execution; it does not fake SQLite state or ACKs.

## Reviews, operation and limits

[REVIEW.md](REVIEW.md) records independent findings and fixes. Historical red,
engine-unavailable and pre-review-fix evidence is retained; it is not final
acceptance. October16 pause records are historical and superseded here.
[OPERATIONS.md](OPERATIONS.md) explains config, bootstrap, health, recovery and
verification. [.gitattributes](../../.gitattributes) preserves exact policy LF bytes.

Original V1/config/state and unrelated user edits are preserved. Logical byte
budget exhaustion is tested, not physical ENOSPC or host power loss. No 10-minute
outage, 24-hour endurance, Windows fsync, real-device compatibility, production
security or lifecycle-management acceptance is claimed. C/D remain future work.
