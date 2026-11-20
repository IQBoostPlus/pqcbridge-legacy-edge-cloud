import { incidentExercise } from './fixtures/mlkem-incident.mjs';

export function assessCheckpoint(checkpoint) {
  const { inventory, rotation, continuity, asOf } = checkpoint;
  const clock = Date.parse(asOf);
  const inventoryTime = Date.parse(inventory?.at);
  const rotationTime = Date.parse(rotation?.at);
  const continuityTime = Date.parse(continuity?.at);
  const ageHours = (clock - inventoryTime) / 3_600_000;
  const hasInventory = Boolean(inventory?.ref && ageHours >= 0);
  const affected = hasInventory && inventory.version === incidentExercise.affectedVersion;
  const upgraded = hasInventory && inventory.version === incidentExercise.fixedVersion;
  const rotated = Boolean(upgraded && rotation?.ref && rotationTime >= inventoryTime && rotationTime <= clock);
  const checked = Boolean(rotated && continuity?.ref && continuityTime >= rotationTime && continuityTime <= clock);
  return {
    version: hasInventory ? inventory.version : null,
    ageHours: hasInventory ? ageHours : null,
    upgraded,
    rotated,
    checked,
    status: checked ? 'verified' : upgraded ? 'pending' : affected ? 'affected' : 'unknown',
  };
}

export function exerciseConnection(source, report, connections) {
  if (source !== 'Demo fixture' || report.customer?.id !== incidentExercise.customerId) return null;
  const id = incidentExercise.segmentId;
  if (!report.connections.some(connection => connection.segmentId === id)) return null;
  return connections.find(connection => connection.id === id) ?? null;
}
