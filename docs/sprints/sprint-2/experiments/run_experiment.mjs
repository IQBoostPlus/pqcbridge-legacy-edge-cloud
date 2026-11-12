import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { summarize, filterConnections } from '../../../../dashboard/model.mjs';

// Predeclared expectations use fixture counts and the documented reporting rules.
// This is an AI-authored technical rehearsal, not participant response data.
const fixture = JSON.parse(await readFile(new URL('../../../../dashboard/fixtures/snapshot.json', import.meta.url), 'utf8'));
const clock = Date.parse(fixture.snapshotAt);
const hour = 3600000;
const clone = () => structuredClone(fixture);
const pick = predicate => ({ ...clone(), connections: clone().connections.filter(predicate) });
const pqc = () => pick(row => row.status === 'pqc');
const cases = [];
function check(id, expected, observe) {
  const actual = observe();
  assert.deepEqual(actual, expected, id);
  cases.push({ id, expected, actual, result: 'pass' });
}
const metrics = (data, time = clock) => {
  const s = summarize(data, time);
  return { total: s.total, pqc: s.pqc, fallback: s.fallback, unknown: s.unknown,
    coverage: s.coverage, stale: s.stale, suspected: s.suspected, level: s.overall.level };
};
check('C01-default', { total: 8, pqc: 5, fallback: 2, unknown: 1, coverage: 62.5, stale: 0, suspected: 1, level: 'red' }, () => metrics(fixture));
check('C02-filter-denominator', { ids: ['SEG-001', 'SEG-007'], globalCoverage: 62.5 }, () => ({ ids: filterConnections(fixture, 'fallback').map(row => row.id), globalCoverage: summarize(fixture, clock).coverage }));
check('C03-empty', { coverage: null, level: 'unknown' }, () => { const s = summarize({ ...clone(), connections: [] }, clock); return { coverage: s.coverage, level: s.overall.level }; });
check('C04-unknown', { total: 1, coverage: 0, level: 'unknown' }, () => { const s = summarize(pick(row => row.status === 'unknown'), clock); return { total: s.total, coverage: s.coverage, level: s.overall.level }; });
check('C05-stale-all-pqc', { coverage: 100, stale: 5, level: 'unknown' }, () => { const s = summarize(pqc(), clock + 48 * hour); return { coverage: s.coverage, stale: s.stale, level: s.overall.level }; });
check('C06-mixed-path', { ids: ['SEG-001', 'SEG-002'], statuses: ['fallback', 'pqc'], coverage: 50 }, () => { const data = pick(row => row.device === 'Pump station A'); return { ids: data.connections.map(row => row.id), statuses: data.connections.map(row => row.status), coverage: summarize(data, clock).coverage }; });
check('C07-expected-fallback', { level: 'amber', suspected: 0 }, () => { const s = summarize(pick(row => row.fallbackKind === 'expected'), clock); return { level: s.overall.level, suspected: s.suspected }; });
check('C08-suspected-and-stale', { level: 'red', stale: 8, suspected: 1, riskCount: 3 }, () => { const s = summarize(fixture, clock + 48 * hour); return { level: s.overall.level, stale: s.stale, suspected: s.suspected, riskCount: s.risks.length }; });
check('C09-freshness-boundary', { atBoundary: 0, afterBoundary: 1 }, () => { const data = pqc(); data.connections = data.connections.slice(0, 1); data.connections[0].observedAt = new Date(clock - 24 * hour).toISOString(); return { atBoundary: summarize(data, clock).stale, afterBoundary: summarize(data, clock + 1).stale }; });
check('C10-future-clock', { level: 'unknown' }, () => ({ level: summarize(pqc(), clock - hour).overall.level }));
check('C11-invalid-data', { rejected: true }, () => { const data = clone(); data.connections[0].status = 'secure'; try { summarize(data, clock); return { rejected: false }; } catch { return { rejected: true }; } });
const hashes = {};
for (const [name, path] of Object.entries({model: '../../../../dashboard/model.mjs', fixture: '../../../../dashboard/fixtures/snapshot.json', runner: './run_experiment.mjs'})) {
  hashes[name] = createHash('sha256').update(await readFile(new URL(path, import.meta.url))).digest('hex');
}
const result = { evidenceType: 'AI-authored model rehearsal; no human participants', baselineRevision: '7ce2898745e69a5e4943080e605db5b2f36dcd3b', sourceState: 'Sprint 2 development working tree', sourceSha256: hashes, runAt: new Date().toISOString(), reportingClock: fixture.snapshotAt, scenarioCount: cases.length, cases };
await writeFile(new URL('results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
console.log(`${cases.length}/${cases.length} independent scenario comparisons passed; results.json written.`);
