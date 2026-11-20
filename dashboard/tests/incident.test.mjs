import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { incidentExercise } from '../fixtures/mlkem-incident.mjs';
import { assessCheckpoint, exerciseConnection } from '../incident.mjs';
import { createCustomerReport, createEvidenceReport } from '../model.mjs';

const { checkpoints } = incidentExercise;

test('incident closure requires upgrade, key rotation and then a continuity check', () => {
  assert.equal(assessCheckpoint(checkpoints.affected).status, 'affected');
  assert.equal(assessCheckpoint(checkpoints.unknown).status, 'unknown');
  assert.equal(assessCheckpoint(checkpoints.upgraded).status, 'pending');
  assert.equal(assessCheckpoint(checkpoints.upgraded).rotated, false);
  assert.equal(assessCheckpoint(checkpoints.verified).status, 'verified');
  assert.equal(assessCheckpoint({ ...checkpoints.verified, rotation: undefined }).status, 'pending');
  assert.equal(assessCheckpoint({ ...checkpoints.verified, rotation: { ...checkpoints.verified.rotation, at: checkpoints.verified.asOf } }).checked, false);
  assert.equal(assessCheckpoint({ ...checkpoints.verified, asOf: checkpoints.affected.asOf }).status, 'unknown');
});

test('incident evidence is limited to the bundled Northfield fixture and omitted from report export', () => {
  const snapshot = JSON.parse(readFileSync(new URL('../fixtures/customer-snapshot.json', import.meta.url)));
  const clock = Date.parse(snapshot.snapshotAt);
  const report = createCustomerReport(snapshot, incidentExercise.customerId, clock);
  const other = createCustomerReport(snapshot, 'CUS-OTHER', clock);
  assert.equal(exerciseConnection('Demo fixture', report, snapshot.connections)?.id, incidentExercise.segmentId);
  assert.equal(exerciseConnection('Demo fixture', other, snapshot.connections), null);
  assert.equal(exerciseConnection('Local JSON', report, snapshot.connections), null);
  assert.equal(exerciseConnection('Demo fixture', { available: false }, []), null);
  const exported = createEvidenceReport(snapshot, clock, incidentExercise.customerId);
  assert.deepEqual(['total', 'exposed', 'unresolved', 'pqc'].map(key => exported.customerReport.totals[key]), [6, 2, 2, 2]);
  assert.doesNotMatch(JSON.stringify(exported), /Training KEM|SIM-INV|SIM-KEY|SIM-OPS/);
});
