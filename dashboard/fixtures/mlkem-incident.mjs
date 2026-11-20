// Fictional provider, versions, timestamps and record references for the course exercise.
export const incidentExercise = {
  customerId: 'CUS-NORTH',
  segmentId: 'SEG-002',
  notice: 'Sarah’s Sprint 3 letter · course exercise, p. 2',
  provider: 'Training KEM (fictional)',
  affectedVersion: '1.4.0',
  fixedVersion: '1.5.0',
  checkpoints: {
    affected: {
      label: 'Advisory received',
      asOf: '2026-11-20T09:00:00Z',
      inventory: { version: '1.4.0', at: '2026-11-20T08:00:00Z', ref: 'SIM-INV-01' },
    },
    unknown: {
      label: 'Version evidence missing',
      asOf: '2026-11-20T09:00:00Z',
    },
    upgraded: {
      label: 'Upgrade recorded',
      asOf: '2026-11-21T12:00:00Z',
      inventory: { version: '1.5.0', at: '2026-11-21T11:30:00Z', ref: 'SIM-INV-02' },
    },
    verified: {
      label: 'Response verified',
      asOf: '2026-11-22T10:00:00Z',
      inventory: { version: '1.5.0', at: '2026-11-21T11:30:00Z', ref: 'SIM-INV-02' },
      rotation: { at: '2026-11-22T09:00:00Z', ref: 'SIM-KEY-01' },
      continuity: { at: '2026-11-22T09:40:00Z', ref: 'SIM-OPS-01' },
    },
  },
};
