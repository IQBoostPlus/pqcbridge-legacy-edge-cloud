import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateSnapshot, createCustomerReport, createEvidenceReport, filterConnections } from '../model.mjs';

const legacy = JSON.parse(await readFile(new URL('../fixtures/snapshot.json', import.meta.url), 'utf8'));
const clock = Date.parse(legacy.snapshotAt);
const item = (id, segments, extra = {}) => ({
  customerId: 'CUSTOMER-A', dataItemId: id, dataClass: 'Telemetry',
  confidentiality: 'Synthetic operating information assumed sensitive for 3 days.',
  observedAt: legacy.snapshotAt, requiredSegmentIds: segments, mappingComplete: true, ...extra,
});
const plan = (id, date = null, extra = {}) => ({
  segmentId: id, plannedMigrationDate: date, replacementDate: null,
  blocker: 'Synthetic procurement decision pending.', consequence: 'Monitoring continuity must be preserved.',
  action: 'Review alternatives with security and operations.', owner: null, targetDate: null, ...extra,
});
function input(items = [], plans = []) {
  return { ...structuredClone(legacy), customerReporting: {
    keyCustomerId: 'CUSTOMER-A', inventoryComplete: true,
    customers: [{ id: 'CUSTOMER-A', name: 'Synthetic key customer' }, { id: 'CUSTOMER-B', name: 'Other synthetic customer' }],
    dataItems: structuredClone(items), plans: structuredClone(plans),
  } };
}
const report = data => createCustomerReport(data, 'CUSTOMER-A', clock);
const counts = result => [result.totals.total, result.totals.exposed, result.totals.unresolved, result.totals.pqc];
const findItem = (result, id) => result.items.find(row => row.dataItemId === id);
const connection = (result, id) => result.connections.find(row => row.segmentId === id);

test('legacy imports remain valid but cannot imply an identified customer inventory', () => {
  assert.equal(validateSnapshot(legacy), legacy);
  const result = report(legacy);
  assert.equal(result.available, false);
  assert.match(result.reason, /customer|scope/i);
});

test('logical items reconcile across classes, independently of eight-segment coverage', () => {
  const data = input([
    item('T1', ['SEG-001', 'SEG-002']),
    item('T2', ['SEG-003', 'SEG-004']),
    item('C1', ['SEG-007'], { dataClass: 'Configuration', confidentiality: 'Synthetic configuration assumed sensitive for 5 years.' }),
    item('C2', ['SEG-008'], { dataClass: 'Configuration' }),
    item('U1', ['SEG-005', 'SEG-006'], { dataClass: null }),
  ]);
  const result = report(data);
  assert.equal(result.available, true);
  assert.deepEqual(counts(result), [5, 2, 1, 2]);
  assert.equal(result.totals.exposedPercent, 40);
  assert.equal(result.totals.unresolvedPercent, 20);
  assert.equal(result.totals.pqcPercent, 40);
  assert.match(result.unit, /item/i);
  const telemetry = result.classes.find(row => row.dataClass === 'Telemetry');
  const configuration = result.classes.find(row => row.dataClass === 'Configuration');
  const unknown = result.classes.find(row => row.dataClass === 'Unknown class');
  assert.deepEqual([telemetry.total, telemetry.exposed, telemetry.unresolved, telemetry.pqc], [2, 1, 0, 1]);
  assert.deepEqual([configuration.total, configuration.exposed, configuration.unresolved, configuration.pqc], [2, 1, 1, 0]);
  assert.equal(unknown.total, 1);
  for (const row of result.classes) assert.equal(row.exposed + row.unresolved + row.pqc, row.total);
  assert.equal(result.classes.reduce((sum, row) => sum + row.total, 0), 5);
  filterConnections(data, 'pqc', 'valve');
  assert.deepEqual(counts(report(data)), [5, 2, 1, 2]);
});

test('unrelated customer items do not change selected-customer quantities or paths', () => {
  const data = input([item('T1', ['SEG-003', 'SEG-004'])]);
  const expected = counts(report(data));
  data.customerReporting.dataItems.push(item('T1', ['SEG-007'], { customerId: 'CUSTOMER-B' }));
  const result = report(data);
  assert.deepEqual(counts(result), expected);
  assert.equal(result.scope.unrelatedItemCount, 1);
  assert.deepEqual(result.connections.map(row => row.segmentId).sort(), ['SEG-003', 'SEG-004']);
  assert.deepEqual(counts(createCustomerReport(data, 'CUSTOMER-B', clock)), [1, 1, 0, 0]);
});

test('repeated item records, route IDs and shared segments do not multiply logical quantities', () => {
  const shared = item('T1', ['SEG-001', 'SEG-002', 'SEG-001']);
  const result = report(input([shared, structuredClone(shared), item('T2', ['SEG-001', 'SEG-002'])]));
  assert.deepEqual(counts(result), [2, 2, 0, 0]);
  assert.deepEqual(result.connections.map(row => row.segmentId).sort(), ['SEG-001', 'SEG-002']);
  assert.equal(findItem(result, 'T1').requiredSegmentIds.length, 2);
});

test('contradictory identities and malformed metadata are rejected rather than silently merged', () => {
  const data = input([item('T1', ['SEG-001']), item('T1', ['SEG-001'], { dataClass: 'Configuration' })]);
  assert.throws(() => validateSnapshot(data));
  for (const change of [
    raw => { raw.customerReporting.keyCustomerId = 'NOT-REGISTERED'; },
    raw => { raw.customerReporting.dataItems[0].customerId = 'NOT-REGISTERED'; },
    raw => { raw.customerReporting.dataItems[0].requiredSegmentIds = 'SEG-003'; },
    raw => { raw.customerReporting.dataItems[0].mappingComplete = 'yes'; },
    raw => { raw.customerReporting.customers.push({ id: 'CUSTOMER-A', name: 'Contradictory customer' }); },
  ]) {
    const invalid = input([item('T1', ['SEG-003'])]); change(invalid);
    assert.throws(() => validateSnapshot(invalid));
  }
});

test('unknown customer attribution remains a separate scope limitation, never inferred from shared paths', () => {
  const result = report(input([
    item('T1', ['SEG-003']), item('UNATTRIBUTED', ['SEG-003'], { customerId: null }),
  ]));
  assert.deepEqual(counts(result), [1, 0, 0, 1]);
  assert.equal(result.scope.inventoryComplete, false);
  assert.ok(result.scope.unattributedItemIds.includes('UNATTRIBUTED'));
  assert.ok(result.scope.limitations.length > 0);
});

test('missing references, incomplete paths, unknown segments and empty paths stay unresolved', () => {
  const result = report(input([
    item('MISSING', ['SEG-999']), item('INCOMPLETE', ['SEG-003'], { mappingComplete: false }),
    item('UNKNOWN', ['SEG-008']), item('EMPTY', []),
  ]));
  assert.deepEqual(counts(result), [4, 0, 4, 0]);
  assert.ok(connection(result, 'SEG-999'));
  for (const row of result.items) {
    assert.equal(row.bucket, 'unresolved');
    assert.ok(row.qualityFlags.length > 0);
  }
});

test('known classical exposure preserves simultaneous missing, stale and unverified evidence', () => {
  const data = input([item('T1', ['SEG-001', 'SEG-008', 'SEG-999'], { mappingComplete: false })]);
  data.connections[0].observedAt = '2026-11-06T04:00:00Z';
  const result = report(data);
  assert.deepEqual(counts(result), [1, 1, 0, 0]);
  const exposed = findItem(result, 'T1');
  assert.ok(exposed.qualityFlags.length >= 3);
  assert.ok(exposed.reasons.length > 0);
});

test('expected fallback and suspected downgrade expose short- and long-life data without deadline exemptions', () => {
  const result = report(input([
    item('SHORT', ['SEG-001']),
    item('LONG', ['SEG-007'], { dataClass: 'Configuration', confidentiality: 'Synthetic confidentiality lifetime: 5 years.' }),
  ]));
  assert.deepEqual(counts(result), [2, 2, 0, 0]);
  assert.deepEqual(result.connections.map(row => row.segmentId).sort(), ['SEG-001', 'SEG-007']);
  assert.equal(result.deadline, '2027-12-31');
  assert.match(findItem(result, 'SHORT').confidentiality, /3 days/);
});

test('freshness boundary applies to both item and segment observations', () => {
  const data = input([item('T1', ['SEG-003'], { observedAt: '2026-11-07T04:00:00Z' })]);
  data.connections.find(row => row.id === 'SEG-003').observedAt = '2026-11-07T04:00:00Z';
  assert.deepEqual(counts(report(data)), [1, 0, 0, 1]);
  assert.deepEqual(counts(createCustomerReport(data, 'CUSTOMER-A', clock + 1)), [1, 0, 1, 0]);
  const staleItem = input([item('T1', ['SEG-003'], { observedAt: '2026-11-06T04:00:00Z' })]);
  assert.deepEqual(counts(report(staleItem)), [1, 0, 1, 0]);
});

test('future evaluation and snapshot clocks cannot manufacture current all-PQC evidence', () => {
  const data = input([item('T1', ['SEG-003'])]);
  assert.deepEqual(counts(createCustomerReport(data, 'CUSTOMER-A', clock - 3600000)), [1, 0, 1, 0]);
  assert.deepEqual(counts(createCustomerReport(data, 'CUSTOMER-A', clock + 48 * 3600000)), [1, 0, 1, 0]);
  assert.throws(() => createCustomerReport(data, 'CUSTOMER-A', NaN), /clock/i);
  assert.throws(() => createCustomerReport(data, 'CUSTOMER-A', 1e20));
});

test('valid empty customer scope yields unavailable proportions, not 100 percent', () => {
  const result = report(input());
  assert.deepEqual(counts(result), [0, 0, 0, 0]);
  assert.equal(result.totals.exposedPercent, null);
  assert.equal(result.totals.unresolvedPercent, null);
  assert.equal(result.totals.pqcPercent, null);
  assert.deepEqual(result.connections, []);
});

test('2028 replacement and missing plans remain visible independently of current status', () => {
  const data = input([item('T1', ['SEG-001', 'SEG-003'])], [
    plan('SEG-001', '2028-01-01', { replacementDate: '2028-01-01' }),
  ]);
  const result = report(data);
  const late = connection(result, 'SEG-001');
  assert.equal(late.replacementDate, '2028-01-01');
  assert.equal(late.plannedMigrationDate, '2028-01-01');
  assert.ok(late.action);
  assert.ok(late.consequence);
  assert.equal(late.owner, null);
  const missing = connection(result, 'SEG-003');
  assert.equal(missing.plannedMigrationDate, null);
  assert.notEqual(missing.scheduleStatus, late.scheduleStatus);
});

test('migration plans before and on deadline differ from late and missing plans; plans never change exposure', () => {
  const data = input([item('A', ['SEG-001']), item('B', ['SEG-007']), item('C', ['SEG-008']), item('D', ['SEG-003'])], [
    plan('SEG-001', '2027-12-30'), plan('SEG-007', '2027-12-31'), plan('SEG-008', '2028-01-01'),
  ]);
  const result = report(data);
  assert.deepEqual(counts(result), [4, 2, 1, 1]);
  assert.equal(connection(result, 'SEG-001').scheduleStatus, 'before-deadline');
  assert.equal(connection(result, 'SEG-007').scheduleStatus, 'on-deadline');
  assert.equal(connection(result, 'SEG-008').scheduleStatus, 'conflict');
  assert.equal(connection(result, 'SEG-003').scheduleStatus, 'unplanned');
  assert.notEqual(connection(result, 'SEG-001').scheduleStatus, connection(result, 'SEG-008').scheduleStatus);
  assert.notEqual(connection(result, 'SEG-003').scheduleStatus, connection(result, 'SEG-008').scheduleStatus);
});

test('invalid calendar plan dates and item observations fail import validation', () => {
  for (const date of ['2027-02-30', 'tomorrow', '2027-12-31T00:00:00Z']) {
    const data = input([item('T1', ['SEG-001'])], [plan('SEG-001', date)]);
    assert.throws(() => validateSnapshot(data));
  }
  const data = input([item('T1', ['SEG-001'], { observedAt: '2026-11-08T04:00:01Z' })]);
  assert.throws(() => validateSnapshot(data));
});

test('export uses the same customer calculations and clock and retains importable source metadata', () => {
  const data = input([item('T1', ['SEG-001', 'SEG-002']), item('T2', ['SEG-003'])], [plan('SEG-001', '2028-01-01')]);
  const expected = report(data);
  const bundle = createEvidenceReport(data, clock);
  assert.deepEqual(bundle.customerReport, expected);
  assert.equal(bundle.customerReport.reportingClock, bundle.reportingClock);
  assert.equal(bundle.customerReport.snapshotAt, data.snapshotAt);
  assert.ok(bundle.customerReport.ruleVersion);
  const saved = JSON.parse(JSON.stringify(bundle));
  assert.deepEqual(report(validateSnapshot(saved.snapshot)), expected);
  data.customerReporting.dataItems[0].dataClass = 'Changed later';
  assert.equal(saved.snapshot.customerReporting.dataItems[0].dataClass, 'Telemetry');
});

test('customer demo fixture has six unique items with a two/two/two reconciliation', async () => {
  const data = JSON.parse(await readFile(new URL('../fixtures/customer-snapshot.json', import.meta.url), 'utf8'));
  const result = createCustomerReport(data, data.customerReporting.keyCustomerId, Date.parse(data.snapshotAt));
  assert.deepEqual(counts(result), [6, 2, 2, 2]);
  assert.equal(result.connections.length, 9);
  const telemetry = result.classes.find(row => row.dataClass === 'Operational telemetry');
  const configuration = result.classes.find(row => row.dataClass === 'Configuration');
  const maintenance = result.classes.find(row => row.dataClass === 'Maintenance');
  const unknown = result.classes.find(row => row.dataClass === 'Unknown class');
  assert.deepEqual([telemetry.total, telemetry.exposed, telemetry.unresolved, telemetry.pqc], [2, 1, 0, 1]);
  assert.deepEqual([configuration.total, configuration.exposed, configuration.unresolved, configuration.pqc], [2, 1, 1, 0]);
  assert.deepEqual([maintenance.total, maintenance.exposed, maintenance.unresolved, maintenance.pqc], [1, 0, 0, 1]);
  assert.deepEqual([unknown.total, unknown.exposed, unknown.unresolved, unknown.pqc], [1, 0, 1, 0]);
});

test('separate route records for one item merge all required segments before deciding its bucket', () => {
  const result = report(input([item('T1', ['SEG-002']), item('T1', ['SEG-001'])]));
  assert.deepEqual(counts(result), [1, 1, 0, 0]);
  assert.deepEqual(findItem(result, 'T1').requiredSegmentIds.sort(), ['SEG-001', 'SEG-002']);
});

test('replacement conflict remains visible even if observed key establishment is currently PQC', () => {
  const result = report(input([item('T1', ['SEG-003'])], [
    plan('SEG-003', '2027-12-01', { replacementDate: '2028-06-01' }),
  ]));
  assert.deepEqual(counts(result), [1, 0, 0, 1]);
  assert.equal(connection(result, 'SEG-003').evidenceStatus, 'reported-pqc');
  assert.equal(connection(result, 'SEG-003').scheduleStatus, 'conflict');
  assert.ok(result.risks.some(row => /2027/.test(row.detail)));
});

test('duplicate plans, impossible replacement dates and undeclared report customers are rejected', () => {
  const duplicate = input([item('T1', ['SEG-001'])], [plan('SEG-001'), plan('SEG-001')]);
  assert.throws(() => validateSnapshot(duplicate));
  const badReplacement = input([item('T1', ['SEG-001'])], [plan('SEG-001', null, { replacementDate: '2028-02-30' })]);
  assert.throws(() => validateSnapshot(badReplacement));
  assert.throws(() => createCustomerReport(input(), 'NOT-REGISTERED', clock));
});

test('exporting a different declared customer preserves its selected scope and evaluation clock', () => {
  const data = input([item('T1', ['SEG-003']), item('B1', ['SEG-001'], { customerId: 'CUSTOMER-B' })]);
  const bundle = createEvidenceReport(data, clock, 'CUSTOMER-B');
  assert.deepEqual(bundle.customerReport, createCustomerReport(data, 'CUSTOMER-B', clock));
  assert.equal(bundle.customerReport.customer.id, 'CUSTOMER-B');
  assert.equal(bundle.customerReport.reportingClock, bundle.reportingClock);
  assert.deepEqual(counts(bundle.customerReport), [1, 1, 0, 0]);
});

test('current PQC quantities cannot hide an unresolved plan or deadline conflict in the customer headline', () => {
  const missing = report(input([item('T1', ['SEG-003'])]));
  assert.deepEqual(counts(missing), [1, 0, 0, 1]);
  assert.notEqual(missing.overall.level, 'green');
  assert.match(missing.overall.reason, /plan|schedule/i);
  const conflict = report(input([item('T1', ['SEG-003'])], [
    plan('SEG-003', '2027-12-01', { replacementDate: '2028-06-01' }),
  ]));
  assert.deepEqual(counts(conflict), [1, 0, 0, 1]);
  assert.notEqual(conflict.overall.level, 'green');
  assert.match(conflict.overall.reason, /conflict|2027|deadline/i);
});
