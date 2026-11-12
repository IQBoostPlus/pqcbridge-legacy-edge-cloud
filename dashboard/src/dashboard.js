import { computed, shallowReactive } from 'vue';
import fixture from '../fixtures/customer-snapshot.json';
import { createCustomerReport, createEvidenceReport, filterConnections, summarize, validateSnapshot } from '../model.mjs';

export const state = shallowReactive({
  snapshot: validateSnapshot(fixture),
  revision: 0,
  source: 'Demo fixture',
  clock: 'snapshot',
  time: Date.now(),
  status: 'all',
  query: '',
  error: '',
  loading: false,
  customerId: fixture.customerReporting.keyCustomerId,
});

export const clockTime = computed(() => state.clock === 'current' ? state.time : Date.parse(state.snapshot?.snapshotAt));
export const summary = computed(() => state.snapshot ? summarize(state.snapshot, clockTime.value) : null);
export const rows = computed(() => state.snapshot ? filterConnections(state.snapshot, state.status, state.query) : []);
export const customerReport = computed(() => state.snapshot
  ? createCustomerReport(state.snapshot, state.customerId, clockTime.value)
  : { available: false, reason: 'Load a valid synthetic snapshot to view the customer report.' });

export function downloadEvidence() {
  if (!state.snapshot || state.loading) return;
  const report = createEvidenceReport(state.snapshot, clockTime.value, state.customerId);
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + '\n'], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'pqc-evidence-report.json';
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
let request = 0;

function applySnapshot(snapshot, source) {
  state.snapshot = validateSnapshot(snapshot);
  state.revision += 1;
  state.source = source;
  state.error = '';
  state.status = 'all';
  state.query = '';
  state.customerId = snapshot.customerReporting?.keyCustomerId ?? '';
}

export function resetDemo() {
  request += 1;
  state.loading = false;
  state.clock = 'snapshot';
  applySnapshot(fixture, 'Demo fixture');
}

export async function importFile(event) {
  const input = event.target;
  const file = input.files[0];
  if (!file) return;
  input.value = '';
  const version = ++request;
  state.loading = true;
  state.error = '';
  try {
    if (file.size > 1_000_000) throw new Error('Choose a JSON snapshot no larger than 1 MB.');
    const raw = JSON.parse(await file.text());
    if (version === request) applySnapshot(raw, 'Local JSON');
  } catch (error) {
    if (version === request) {
      state.snapshot = null;
      state.error = error.message;
    }
  } finally {
    if (version === request) state.loading = false;
  }
}
