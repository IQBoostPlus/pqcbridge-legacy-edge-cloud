# Phase C execution status

Updated: 2026-10-19 (Asia/Singapore).
State: **COMPLETE and accepted for the owned Docker/simulated-device lab scope.**
Separate Standards/Spec re-reviews have no remaining blocker. Branch:
codex/phase-c-management; baseline5c12f8644d35ae85422318bbad934379067affa1.
C completion and its test-only repair are verified published to main at
2cde91dfabdf4435e298243b2b52bb1dcb48723c. Main CI39260202385 passed tests and
Docker checks. Later documentation commits may advance main. The human started
[Phase D](../phase-d/STATUS.md) on2026-10-20; D acceptance is tracked separately.

## 1. Implementation and Acceptance

| Work | Result | Matching evidence |
| --- | --- | --- |
| C01 | Bounded gateway/device enrollment, disabling, immutable binding and credential references, transactional audit | Full regression; real device/gateway disable cases |
| C02 | Fixed hybrid profiles, desired/applied/effective versions, safe failure reasons, Unknown for stale/disconnected proof | Lifecycle canary/failure/rollback; observation4; catalog tests |
| C03 | Synthetic issuer, role-isolated leaves, bounded overlap/retirement, failed rotation recovery and emergency revocation | Lifecycle issuer/rotation/revocation/expiry |
| C04 | Per-gateway rollout, unaffected group TCP/business continuity, safe new-version rollback retaining current credentials | Two-group actual lifecycle matrix |
| C05 | Local CLI, no per-message controller call, expiring lease/cache, exact-event buffered recovery and credential expiry | Actual5s offline lease/45s leaf; observation proof |

## 2. Final Verification

| Verification | Observed result |
| --- | --- |
| Original C native Windows suite (4b70e0d) | 247 passed in14.46s; historical source record |
| After test portability repair: Windows / offline Linux | 247 passed12.71s /247 passed9.51s |
| GitHub Linux CI for repair2cde91d | 247 passed8.42s; test and Docker jobs successful before and after main push |
| Actual unmodified B applications on final shared runtime | 19/19, cleanup verified |
| Real TLS/ACK/protected HTTP and catalog proof regressions | 4/4, cleanup verified |
| Actual unmodified two-group C managed lifecycle | 17/17, cleanup verified |
| Source/harness reconciliation and preservation | Zero drift; all12 protected inputs unchanged |
| Final owner-resource/process audit | No C/B owner containers/networks/volumes or matching validation runner |

Final records under evidence/: full-regression.json, b-compatibility.json,
observation-green.json, docker-lifecycle-final.json and FINAL_AUDIT.json. Runtime:
Python3.12.14/OpenSSL3.5.7/cryptography50.0.1 on local Docker desktop-linux.
Lifecycle image:sha256:28c86865a9e9feb9011c1db7d61af573b801328e9c3cb3f23869f23e11487cc2.

Active revocation verification completed0.984s after publication returned; an
existing device source closed0.905s after manifest issuance. These single lab
measurements are not production delay guarantees. Offline authorization lasts
at most the last300s lease plus scheduling. Short fixtures:24s overlap,5s lease,
45s leaf. The separate stale-proof scenario offsets runtime clock301s, not elapsed
endurance; actual TLS/storage/business ACKs are retained.

## 3. Reviews, History and Limits

[REVIEW.md](REVIEW.md) records independent AI findings and repairs;
[COMPLETION.md](COMPLETION.md) is the milestone record and
[OPERATIONS.md](OPERATIONS.md) covers setup, CLI proof and recovery. Historical
red, pre-fix, harness-defect and interrupted reports keep their original outcomes.
October18 pause/next-step instructions are superseded. [CI_FIX.md](CI_FIX.md)
records the later Linux fixture failure, test-only repair and verified main CI.
Original source hashes and audit outcomes remain historical and unchanged.

Secrets/raw state are excluded; unrelated user work and original config/state
are preserved. Catalog observations trust the local operator; status is a bounded
last observation, not an online fleet monitor. No production security, physical
devices, host-compromise protection, Windows ACL verification, power-loss,
endurance, upgrade/restore or D acceptance is claimed. Unique images stay cached.
