# Sprint 3 dashboard implementation and verification

Technical review performed on 20 November 2026. [Plan](PLAN.md) ·
[Run and walkthrough instructions](../../../dashboard/README.md) ·
[Dashboard evolution PDF](Sprint3_Dashboard_Evolution_Group22.pdf)

## What Sarah can conclude

The Vue dashboard reads synthetic data and its package manifest and lockfile
identify no ML-KEM implementation. The separate Gateway/Cloud prototype uses
ML-KEM-768 through the Python package in `requirements.txt`. A local isolated
installation of the pinned Windows wheel loaded `cryptography 50.0.1` and
reported `OpenSSL 4.0.2 25 Aug 2026`. The vendor changelog agrees with the
observed wheel version. Sarah's Sprint 3 course letter (p. 2) supplies no
advisory identifier, supplier or affected range. The reviewed changelog and
OpenSSL advisory index give no verified match for that course notice.
Applicability to the prototype and to any production installation remains
unresolved. [Browser dependencies](../../../dashboard/package.json) ·
[Python requirements](../../../requirements.txt) ·
[Vendor changelog](https://cryptography.io/en/latest/changelog/#v50-0-1) ·
[OpenSSL vulnerability index](https://openssl-library.org/news/vulnerabilities/)

For confirmed impact, identify the vendor-fixed version, plan the update and
long-term key rotation, coordinate the new gateway pin, and confirm reconnection
and monitoring before closure. Review historical exposure separately. The
proposed follow-up is to obtain the intended advisory and deployment inventory
for Sarah's review. The exercise completion labels refer to fictional records.

## Evidence checks

| Check | Observed result |
| --- | --- |
| Dashboard model suite and production build | `npm --prefix dashboard test` passed 41/41. `npm --prefix dashboard run build` passed. |
| Independent exercise expectations | An affected version triggers investigation. Missing or future inventory keeps applicability unresolved. An update without rotation stays pending. Rotation has to follow the upgrade evidence and the continuity check has to follow rotation. Tests exercised missing and out-of-order evidence. |
| Production browser walkthrough | Exercised four checkpoints, Sarah/Michael/Emma navigation, SEG-002 evidence and return to the same checkpoint. Verified all three simulated response steps were recorded before a verified status. No page exceptions occurred in the walkthrough. |
| Scope and downloaded JSON | Other customer and imported legacy snapshot showed no matching exercise connection. Reset restored the scenario. Downloaded Northfield evidence retained its 6-item split (2/2/2), historical clock and migration source data. The JSON contained no Sprint 3 incident records. |
| Narrow viewport | Chrome at 390 × 844 displayed the incident view without horizontal overflow. The incident panel client and scroll widths were both 345 px. |
| Version PDF | Chrome captured the Sprint 2 build from `6383183` (`index-Dqnu7a78.js`), the intermediate alert build (`index-BVTp1OTo.js`) and the final working-tree build (`index-sLw7e_OE.js`). The same Northfield snapshot anchors the comparison. Each page contains an actual screenshot with its version and a caption. |

## LLM-assisted implementation review

The implementation followed the request to deliver the runnable increment and
the separate evolution PDF against the plan. The LLM generated the response
assessment rules, role views and exercise data. A useful failure case is a
continuity record whose timestamp precedes the rotation. The expected status is
still pending even if all three record types exist. The model test and the
browser's upgrade-only checkpoint verify that closure requires ordered,
separate evidence. The browser export and the independent 2/2/2 fixture
expectation check the boundary between the new incident view and existing
reporting. These checks establish prototype behavior. Team review and PO
acceptance are still open.
