import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { validateSnapshot } from '../../../../dashboard/model.mjs';

const fixture = JSON.parse(await readFile(new URL('../../../../dashboard/fixtures/snapshot.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(fixture);
const out = new URL('./scenarios/', import.meta.url);
await mkdir(out, { recursive: true });
const empty = { ...copy(), connections: [] };
const stale = copy();
stale.connections = stale.connections.filter(row => row.status === 'pqc');
stale.connections.forEach(row => { row.observedAt = '2026-11-06T03:00:00Z'; });
const mixed = copy();
mixed.connections = mixed.connections.filter(row => row.device === 'Pump station A');
const unknown = copy();
unknown.connections = unknown.connections.filter(row => row.status === 'unknown');
const expected = copy();
expected.connections = expected.connections.filter(row => row.fallbackKind === 'expected');
const datasets = { default: fixture, empty, 'stale-pqc': stale, 'mixed-path': mixed, unknown, 'expected-fallback': expected };
for (const [name, data] of Object.entries(datasets)) {
  validateSnapshot(data);
  await writeFile(new URL(name + '.json', out), JSON.stringify(data, null, 2) + '\n');
}
await writeFile(new URL('invalid.json', out), '{"schemaVersion":1,"synthetic":true,"connections":null}\n');
console.log('Prepared six valid synthetic session datasets and one deliberate invalid-input case.');
