# Customer-report independent expectations

Prepared on 12 November 2026 for the corrected Sprint 2 goal. These worked
expectations are based on the declared synthetic paths and counting rules,
not on output captured from the implementation. The executable checks are in
`dashboard/tests/customer.test.mjs`. Technical checks establish reporting
behavior only; no human comprehension, contract agreement or PO acceptance is
implied.

## Counting example used by the tests

Customer A has five distinct logical items. The source snapshot remains the
historical eight-segment dataset; none of its segment percentages supplies the
customer-data denominator. Evaluate at `2026-11-08T04:00:00Z`.

| Item | Class | Required segments | Independent reasoning | Expected bucket |
| --- | --- | --- | --- | --- |
| T1 | Telemetry | SEG-001, SEG-002 | One required segment uses ECDH-P256, although the gateway segment uses ML-KEM | Potential HNDL exposure |
| T2 | Telemetry | SEG-003, SEG-004 | Both required segments report current ML-KEM | Reported PQC |
| C1 | Configuration | SEG-007 | Required segment uses ECDH-P256; suspected downgrade is unconfirmed | Potential HNDL exposure |
| C2 | Configuration | SEG-008 | Key establishment is unknown | Unresolved |
| U1 | Unknown class | SEG-005, SEG-006 | Classification is unknown; both known required segments report current ML-KEM | Reported PQC, with classification uncertainty visible |

The total is **5 items = 2 exposed + 1 unresolved + 2 reported PQC**. The
corresponding proportions are **40%, 20%, 40%**. Telemetry is 2 = 1 + 0 + 1;
Configuration is 2 = 1 + 1 + 0; Unknown class is 1 = 0 + 0 + 1. These sum to
the customer total. Item counts are not byte volumes, traffic shares or attack
probabilities. The old segment share, 5/8 = 62.5%, is a different quantity.

## Isolation, duplication and uncertainty

- Adding Customer B's item with the same item ID must leave A's quantities and
  required connections unchanged. Selecting B instead gives B's own scope.
- Reporting T1 twice with the same metadata, repeating SEG-001 in its path,
  and sharing its segments with another item cannot multiply T1's quantity.
  Contradictory class or identity metadata must fail validation.
- An unattributed item cannot be assigned to A because its path overlaps A's.
  It stays outside A's known-item denominator and makes inventory completeness
  unresolved. Its identifier must remain visible as a scope limitation.
- Missing SEG-999, incomplete mapping, an empty required path and unknown
  SEG-008 each leave an item unresolved unless known classical evidence already
  establishes potential exposure. In that case, simultaneous quality flags
  remain visible and the item is counted once in the exposed bucket.
- A three-day confidentiality assumption does not exempt classical telemetry
  from potential exposure or from the 2027 requirement. A five-year assumption
  does not establish that an attack occurred.
- Empty known-customer scope has zero counts and unavailable proportions.
  A legacy snapshot without customer metadata has an unavailable customer
  report, rather than an inferred customer or a healthy empty inventory.

## Time and deadline examples

Item observations and required-segment observations are both evaluated.
At `2026-11-08T04:00:00Z`, an observation at `2026-11-07T04:00:00Z` is exactly
24 hours old and still current. Advancing the reporting clock by one millisecond
makes it stale. Fresh segment evidence cannot compensate for a stale item's
observation. Future evaluation/snapshot evidence prevents reported current PQC.

| Planned migration date | Expected schedule interpretation | Current evidence interpretation |
| --- | --- | --- |
| 2027-12-30 | Before deadline | Still derived from observations; a plan cannot turn classical into PQC |
| 2027-12-31 | On deadline | Same evidence rule; includes the target day |
| 2028-01-01 | Conflict | Cannot satisfy the 2027 target as scheduled |
| Missing | Unplanned | Missing plan stays explicit, even when current evidence reports PQC |

A 2028 replacement must remain a scheduling conflict. Proposed actions must
preserve continuity considerations; missing owners and targets stay unassigned.
Impossible calendar dates must fail import validation instead of rolling into
the next month.

## Reproducibility and integration boundary

The evidence bundle's customer report must equal a direct calculation from
its nested snapshot at its exported reporting clock. JSON serialization and
re-import of that nested source snapshot must preserve the result. Subsequent
mutation of the source must not change the exported copy. UI checks, startup,
build results and actual test totals are recorded separately by the integrating
agent in [VERIFICATION.md](../VERIFICATION.md).

## Default customer demo cross-check

The demo fixture uses `CUS-NORTH` (Northfield Energy, synthetic). It declares
nine required segment IDs across six unique items. Eight have source connection
records; `SEG-009` is a missing reference, not an invented ninth observation.

| Class | Total logical items | Potential HNDL | Unresolved | Reported PQC |
| --- | --- | --- | --- | --- |
| Operational telemetry | 2 | 1 | 0 | 1 |
| Configuration | 2 | 1 | 1 | 0 |
| Maintenance | 1 | 0 | 0 | 1 |
| Unknown class | 1 | 0 | 1 | 0 |
| Total | 6 | 2 | 2 | 2 |

`DATA-T01` repeats in the input and repeats a segment ID, but counts once.
`DATA-T02` uses current PQC segments. `DATA-C01` uses classical `SEG-007`;
`DATA-C02` includes unknown `SEG-008`. `DATA-M01` uses current PQC segments;
`DATA-U01` has incomplete mapping to missing `SEG-009`. A separate customer's
item does not enter these six. An unattributed item stays outside the six but
prevents a complete inventory claim. Each bucket is 2/6 (33.3% rounded to one
decimal); the unrounded categories reconcile exactly.

The model checks also cover a current-PQC-only example with a late replacement
and one with no plan. They must retain PQC quantities but expose the planning
gap in the customer headline and risk list; current observed migration does
not establish an achievable customer commitment.

## Observed test result

On 12 November 2026, `node --test dashboard/tests/customer.test.mjs` passed
**22 tests, 0 failures** against the integrated customer-report model. The
worked five-item example and six-item demo table above match those test
assertions. This result includes the customer-headline guard for missing or
late plans, selected-customer export and independent current-versus-schedule
status. It does not supply browser, build or human-session evidence.
