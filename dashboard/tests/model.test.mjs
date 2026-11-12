import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateSnapshot, summarize, filterConnections, createEvidenceReport, FRESHNESS_HOURS } from '../model.mjs';

const fixture = JSON.parse(await readFile(new URL('../fixtures/snapshot.json', import.meta.url), 'utf8'));
const clock = Date.parse(fixture.snapshotAt);
const clone = () => structuredClone(fixture);
const just = status => ({ ...clone(), connections: clone().connections.filter(row => row.status === status) });

test('fixed fixture reconciles to eight segments, five PQC, two fallback and one unknown', () => {
  assert.equal(validateSnapshot(fixture), fixture);
  const result = summarize(fixture, clock);
  assert.deepEqual([result.total, result.pqc, result.fallback, result.unknown, result.coverage], [8, 5, 2, 1, 62.5]);
  assert.equal(result.stale, 0);
  assert.equal(result.suspected, 1);
  assert.equal(result.overall.level, 'red');
  assert.equal(result.risks.length, 3);
  assert.match(result.risks[0].detail, /SEG-007/);
  assert.match(result.risks[0].detail, /pressure monitoring/);
  assert.equal(JSON.stringify(validateSnapshot(clone())), JSON.stringify(fixture));
});

test('unknown-only and zero-record snapshots never report all-clear or 100 percent', () => {
  const unknown = summarize(just('unknown'), clock);
  assert.equal(unknown.coverage, 0);
  assert.equal(unknown.total, 1);
  assert.equal(unknown.overall.level, 'unknown');
  const empty = summarize({ ...clone(), connections: [] }, clock);
  assert.equal(empty.total, 0);
  assert.equal(empty.coverage, null);
  assert.equal(empty.overall.level, 'unknown');
  assert.equal(empty.risks.length, 1);
});

test('known current PQC segments give a qualified migration indication', () => {
  const result = summarize(just('pqc'), clock);
  assert.equal(result.coverage, 100);
  assert.equal(result.overall.level, 'green');
  assert.match(result.overall.reason, /not a system-security guarantee/);
  assert.deepEqual(result.risks, []);
});

test('expected classical fallback is amber; suspicion is explicit and takes priority', () => {
  const data = clone();
  data.connections = data.connections.filter(row => row.fallbackKind === 'expected');
  const expected = summarize(data, clock);
  assert.equal(expected.overall.level, 'amber');
  assert.equal(expected.suspected, 0);
  data.connections.push(clone().connections.find(row => row.fallbackKind === 'suspected'));
  const suspected = summarize(data, clock + 48 * 3600000);
  assert.equal(suspected.overall.level, 'red');
  assert.match(suspected.overall.reason, /not a confirmed attack/);
  assert.equal(suspected.stale, 2);
});

test('freshness uses every observation, including old data inside a recent snapshot', () => {
  assert.equal(FRESHNESS_HOURS, 24);
  const data = just('pqc');
  data.connections[0].observedAt = '2026-11-07T04:00:00Z';
  assert.equal(summarize(data, clock).stale, 0); // Exactly 24h is current.
  assert.equal(summarize(data, clock + 1).stale, 1);
  assert.equal(summarize(data, clock + 1).overall.level, 'unknown');
  assert.equal(summarize(just('pqc'), clock + 48 * 3600000).stale, 5);
});

test('future observation or future snapshot prevents a green result', () => {
  const result = summarize(just('pqc'), clock - 3600000);
  assert.equal(result.overall.level, 'unknown');
  assert.match(result.overall.reason, /future-dated/);
  const data = just('pqc');
  data.connections.forEach(row => { row.observedAt = '2026-11-07T04:00:00Z'; });
  assert.match(summarize(data, clock - 3600000).overall.reason, /Snapshot time is ahead/);
});

test('status filters and free-text search preserve segment-level identities', () => {
  assert.equal(filterConnections(fixture).length, 8);
  assert.deepEqual(filterConnections(fixture, 'fallback').map(row => row.id), ['SEG-001', 'SEG-007']);
  assert.deepEqual(filterConnections(fixture, 'unknown').map(row => row.id), ['SEG-008']);
  assert.equal(filterConnections(fixture, 'pqc').length, 5);
  assert.deepEqual(filterConnections(fixture, 'all', ' PUMP STATION A ').map(row => row.id), ['SEG-001', 'SEG-002']);
  assert.deepEqual(filterConnections(fixture, 'pqc', 'pump').map(row => row.id), ['SEG-002']);
  assert.deepEqual(filterConnections(fixture, 'fallback', 'nothing matches'), []);
  assert.deepEqual(filterConnections(fixture, 'all', 'observedAt'), []); // Searches values, not field names.
  assert.throws(() => filterConnections(fixture, 'invalid'), /filter/);
  assert.throws(() => filterConnections(fixture, 'all', null), /query/);
});

test('search ignores additional JSON fields that are outside the connection schema', () => {
  const data = clone();
  data.connections[0].metadata = { toString: null };
  data.connections[1].extra = 'internal annotation';
  assert.equal(filterConnections(data).length, 8);
  assert.equal(filterConnections(data, 'all', 'pump').length, 2);
  assert.equal(filterConnections(data, 'all', 'internal annotation').length, 0);
});

test('invalid top-level schemas fail visibly rather than becoming healthy empty data', () => {
  for (const value of [null, [], 'data', 42]) assert.throws(() => validateSnapshot(value), /object/);
  for (const [field, value] of [['schemaVersion', 2], ['synthetic', false], ['title', ' '], ['connections', null]]) {
    const data = clone(); data[field] = value;
    assert.throws(() => validateSnapshot(data));
  }
  assert.throws(() => summarize(clone(), NaN), /clock/);
  assert.throws(() => summarize(clone(), '2026-11-08'), /clock/);
});

test('reject duplicate IDs, malformed records, missing fields and unsupported classifications', () => {
  const duplicate = clone(); duplicate.connections[1].id = duplicate.connections[0].id;
  assert.throws(() => validateSnapshot(duplicate), /Duplicate/);
  const malformed = clone(); malformed.connections[0] = null;
  assert.throws(() => validateSnapshot(malformed), /object/);
  for (const [field, value] of [['reason', ' '], ['status', 'secure'], ['segment', 'end-to-end'], ['fallbackKind', 'none'], ['keyEstablishment', 'ML-KEM-768']]) {
    const data = clone(); data.connections[0][field] = value;
    assert.throws(() => validateSnapshot(data));
  }
  const missing = clone(); delete missing.connections[0].confidentiality;
  assert.throws(() => validateSnapshot(missing), /confidentiality/);
});

test('reject PQC and unknown method/fallback contradictions', () => {
  const pqc = just('pqc'); pqc.connections[0].keyEstablishment = 'ECDH-P256';
  assert.throws(() => validateSnapshot(pqc), /PQC requires/);
  pqc.connections[0].keyEstablishment = 'ML-KEM-768'; pqc.connections[0].fallbackKind = 'expected';
  assert.throws(() => validateSnapshot(pqc), /PQC requires/);
  for (const field of ['fallbackKind', 'keyEstablishment']) {
    const unknown = just('unknown'); unknown.connections[0][field] = 'none';
    assert.throws(() => validateSnapshot(unknown), /unknown status requires/);
  }
});

test('timestamps require actual ISO UTC calendar values and observations cannot follow snapshot', () => {
  for (const value of ['tomorrow', '2026-11-08', '2026-02-30T04:00:00Z', '2026-11-08T04:00:00+00:00']) {
    const data = clone(); data.snapshotAt = value;
    assert.throws(() => validateSnapshot(data), /timestamp/);
  }
  const data = clone(); data.connections[0].observedAt = '2026-11-08T04:00:01Z';
  assert.throws(() => validateSnapshot(data), /after snapshotAt/);
});

test('metric evidence traces global numerator, unknown denominator and mixed device path to exact IDs', () => {
  const result = summarize(clone(), clock);
  assert.deepEqual(result.evidence.numeratorIds, ['SEG-002', 'SEG-003', 'SEG-004', 'SEG-005', 'SEG-006']);
  assert.deepEqual(result.evidence.denominatorIds, ['SEG-001', 'SEG-002', 'SEG-003', 'SEG-004', 'SEG-005', 'SEG-006', 'SEG-007', 'SEG-008']);
  assert.deepEqual(result.evidence.unknownIds, ['SEG-008']);
  assert.deepEqual(result.evidence.suspectedIds, ['SEG-007']);
  assert.deepEqual(result.evidence.expectedFallbackIds, ['SEG-001']);
  const pump = clone();
  pump.connections = pump.connections.filter(row => row.device === 'Pump station A');
  assert.deepEqual(summarize(pump, clock).evidence.numeratorIds, ['SEG-002']);
  assert.deepEqual(summarize(pump, clock).evidence.denominatorIds, ['SEG-001', 'SEG-002']);
  filterConnections(pump, 'pqc');
  assert.equal(summarize(pump, clock).coverage, 50);
});

test('investigation headline retains coexisting unknown, stale and expected fallback evidence', () => {
  const result = summarize(clone(), clock + 48 * 3600000);
  assert.equal(result.overall.level, 'red');
  assert.deepEqual(result.evidence.reasons.map(reason => reason.code), ['suspected', 'unknown', 'stale', 'expected-fallback']);
  assert.deepEqual(result.evidence.reasons.find(reason => reason.code === 'stale').ids,
    ['SEG-001', 'SEG-002', 'SEG-003', 'SEG-004', 'SEG-005', 'SEG-006', 'SEG-007', 'SEG-008']);
  assert.equal(result.future, 0);
  assert.equal(result.futureSnapshot, false);
  assert.equal(result.evidence.clock, clock + 48 * 3600000);
  assert.equal(result.evidence.snapshotAt, fixture.snapshotAt);
});

test('future and empty evidence are explicit with IDs only for contributing observations', () => {
  const future = summarize(just('pqc'), clock - 3600000);
  assert.equal(future.future, 5);
  assert.equal(future.futureSnapshot, true);
  assert.deepEqual(future.evidence.reasons.map(reason => reason.code), ['future', 'future-snapshot']);
  assert.deepEqual(future.evidence.futureIds, ['SEG-002', 'SEG-003', 'SEG-004', 'SEG-005', 'SEG-006']);
  assert.deepEqual(future.evidence.reasons.find(reason => reason.code === 'future-snapshot').ids, []);
  const empty = summarize({ ...clone(), connections: [] }, clock);
  assert.deepEqual(empty.evidence.reasons, [{ code: 'empty', label: 'No connection segments available; coverage is unavailable.', ids: [] }]);
  assert.deepEqual(empty.evidence.denominatorIds, []);
});

test('evidence report freezes the evaluation context as a detached serializable snapshot', () => {
  const input = clone();
  const report = createEvidenceReport(input, clock);
  const saved = JSON.parse(JSON.stringify(report));
  assert.equal(saved.synthetic, true);
  assert.equal(saved.schemaVersion, 1);
  assert.equal(saved.reportingClock, '2026-11-08T04:00:00.000Z');
  assert.deepEqual(saved.snapshot, fixture);
  assert.equal(saved.summary.coverage, 62.5);
  assert.equal(saved.rules.freshnessHours, 24);
  assert.match(saved.rules.unit, /filters do not change global coverage/);
  input.connections[0].reason = 'Changed after export';
  assert.equal(report.snapshot.connections[0].reason, fixture.connections[0].reason);
  report.snapshot.connections[1].device = 'Changed report';
  assert.equal(input.connections[1].device, fixture.connections[1].device);
  assert.deepEqual(saved.summary.evidence.denominatorIds, fixture.connections.map(row => row.id));
});

test('evidence export rejects invalid snapshots and unusable reporting clocks', () => {
  assert.throws(() => createEvidenceReport(null, clock), /object/);
  assert.throws(() => createEvidenceReport(clone(), NaN), /clock/);
  assert.throws(() => createEvidenceReport(clone(), Infinity), /clock/);
  assert.throws(() => createEvidenceReport(clone(), 1e20), /calendar time/);
  const contradictory = clone();
  contradictory.connections[0].status = 'pqc';
  assert.throws(() => createEvidenceReport(contradictory, clock), /PQC requires/);
});
