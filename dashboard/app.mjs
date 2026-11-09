import { validateSnapshot, summarize, filterConnections, FRESHNESS_HOURS } from './model.mjs';

const $ = id => document.getElementById(id);
const state = { snapshot: null, role: 'security', status: 'all', query: '', clock: 'snapshot' };
let loadVersion = 0;
const roleButtons = [...document.querySelectorAll('[data-role]')];
const statusLabels = { pqc: 'PQC', fallback: 'Fallback', unknown: 'Unknown' };
const segmentLabels = { 'device-to-gateway': 'Device → gateway', 'gateway-to-cloud': 'Gateway → cloud' };

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function utc(value) {
  return new Date(value).toISOString().replace('T', ' ').replace('.000Z', ' UTC');
}

function now() {
  return state.clock === 'snapshot' ? Date.parse(state.snapshot.snapshotAt) : Date.now();
}

function badge(text, kind) { return node('span', text, `badge ${kind}`); }

function paragraph(label, value) {
  const p = node('p');
  p.append(node('strong', `${label}: `), document.createTextNode(value));
  return p;
}

function clearResults(message) {
  state.snapshot = null;
  for (const id of ['total', 'coverage', 'fallback', 'unknown']) $(id).textContent = '—';
  $('coverage-detail').textContent = 'No valid dataset';
  $('snapshot-title').textContent = 'Dataset unavailable';
  $('snapshot-time').textContent = 'No snapshot loaded';
  $('clock-note').textContent = 'No current assessment is available.';
  $('connections').replaceChildren();
  $('role-panel').replaceChildren(node('p', 'Load a valid synthetic snapshot to assess this view.', 'muted'));
  $('row-count').textContent = 'No valid dataset';
  $('empty').hidden = true;
  $('error-message').textContent = message;
  $('error').hidden = false;
  for (const control of [...roleButtons, $('clock'), $('status-filter'), $('search')]) control.disabled = true;
}

function render() {
  if (!state.snapshot) return;
  const snapshot = state.snapshot;
  const summary = summarize(snapshot, now());
  $('error').hidden = true;
  for (const control of [...roleButtons, $('clock'), $('status-filter'), $('search')]) control.disabled = false;
  $('snapshot-title').textContent = snapshot.title;
  $('snapshot-time').textContent = utc(snapshot.snapshotAt);
  $('clock-note').textContent = `${state.clock === 'snapshot' ? 'Historical simulation: clock pinned to snapshot time. This is not live monitoring.' : `Current-time assessment at ${utc(now())}.` } ${summary.stale} stale segment(s); freshness limit ${FRESHNESS_HOURS} hours. Unknown or future-dated evidence cannot support an all-clear.`;
  $('total').textContent = summary.total;
  $('coverage').textContent = summary.coverage === null ? 'Unavailable' : `${summary.coverage.toFixed(1)}%`;
  $('coverage').classList.toggle('unavailable', summary.coverage === null);
  $('coverage-detail').textContent = `${summary.pqc} PQC / ${summary.total} total segments · rounded to 1 decimal`;
  $('fallback').textContent = summary.fallback;
  $('unknown').textContent = summary.unknown;
  roleButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.role === state.role)));
  renderRole(summary);
  renderConnections();
}

function card(record, kind) {
  const article = node('article', undefined, 'context-card');
  article.append(node('p', `${record.id} · ${record.device}`, 'context-label'));
  article.append(node('h3', segmentLabels[record.segment]));
  if (kind === 'security') {
    article.append(badge(record.fallbackKind === 'suspected' ? 'Suspected downgrade · synthetic' : record.status === 'fallback' ? 'Expected legacy fallback' : 'Unknown protection', record.fallbackKind === 'suspected' ? 'suspected' : record.status));
    article.append(paragraph('Reason', record.reason), paragraph('Confidentiality assumption', record.confidentiality));
  } else {
    article.append(badge(statusLabels[record.status], record.status), paragraph('Migration blocker', record.blocker));
  }
  article.append(paragraph('Business impact', record.impact), paragraph('Next action', record.action));
  return article;
}

function renderRole(summary) {
  const panel = $('role-panel');
  panel.replaceChildren();
  const names = {
    security: ['S', 'Sarah · Security officer', 'Which connections need investigation, and what is the exposure?'],
    migration: ['M', 'Michael · Migration manager', 'How far have we progressed, and what is blocking the remaining segments?'],
    executive: ['E', 'Emma · CIO', 'What needs attention, what could affect the business, and what decision comes next?']
  };
  const [initial, title, description] = names[state.role];
  const intro = node('div', undefined, 'role-intro');
  const heading = node('div');
  heading.append(node('h3', title), node('p', description));
  intro.append(node('span', initial, 'avatar'), heading);
  panel.append(intro);
  if (state.role === 'executive') {
    const status = node('div', undefined, `status-banner ${summary.overall.level}`);
    const explanation = node('div');
    explanation.append(node('h3', summary.overall.label), node('p', summary.overall.reason));
    status.append(badge(summary.overall.level.toUpperCase(), summary.overall.level), explanation);
    panel.append(status);
    const grid = node('div', undefined, 'role-grid');
    for (const [index, risk] of summary.risks.entries()) {
      const article = node('article', undefined, 'context-card');
      article.append(node('p', `PRIORITY ${index + 1}`, 'context-label'), node('h3', risk.title), node('p', risk.detail), paragraph('Decision / next action', risk.action));
      grid.append(article);
    }
    panel.append(grid);
    if (!summary.risks.length) panel.append(node('p', 'No additional risks are flagged by these limited prototype rules. Reported migration status is not a security guarantee.', 'muted'));
    panel.append(node('p', 'Rule: suspected downgrade → red; empty / unknown / stale / future evidence → unknown; fallback → amber; otherwise green for reported segment migration only. Team / PO review pending.', 'role-note'));
    return;
  }
  const records = state.snapshot.connections.filter(record => record.status !== 'pqc');
  if (state.role === 'migration') {
    panel.append(node('p', `${summary.pqc} of ${summary.total} connection segments report PQC. ${summary.fallback + summary.unknown} segments remain fallback or unknown. These are connection counts, not device counts.`, 'role-note'));
  } else {
    panel.append(node('p', `${summary.suspected} suspected downgrade scenario(s), ${summary.fallback} fallback segment(s), ${summary.unknown} unknown segment(s). HNDL exposure is assessed from assumptions, not detected attacks.`, 'role-note'));
  }
  const grid = node('div', undefined, 'role-grid');
  for (const record of records) grid.append(card(record, state.role));
  panel.append(grid);
  if (!records.length) panel.append(node('p', summary.total ? 'No fallback or unknown segments in this snapshot. Check freshness and interpretation limits before making decisions.' : 'No connection records available. Migration and exposure cannot be assessed.', 'muted'));
  if (summary.stale) panel.append(node('p', `Data quality: ${summary.stale} segment(s) are stale under the selected clock. Revalidate evidence before relying on reported status.`, 'role-note'));
}

function renderConnections() {
  const rows = filterConnections(state.snapshot, state.status, state.query);
  const body = $('connections');
  body.replaceChildren();
  for (const record of rows) {
    const row = node('tr');
    const identity = node('td');
    identity.append(node('strong', record.id), node('span', record.device, 'cell-sub'));
    const segment = node('td');
    segment.append(node('strong', segmentLabels[record.segment]), node('span', record.keyEstablishment, 'cell-sub'));
    const protection = node('td');
    protection.append(badge(statusLabels[record.status], record.status));
    if (record.fallbackKind === 'expected' || record.fallbackKind === 'suspected') protection.append(node('span', record.fallbackKind === 'expected' ? 'Expected legacy path' : 'Suspected downgrade · synthetic', 'cell-sub'));
    const context = node('td');
    context.append(node('span', record.reason));
    const details = node('details');
    details.append(node('summary', 'View context & next action'), paragraph('Fallback classification', record.fallbackKind), paragraph('Confidentiality assumption', record.confidentiality), paragraph('Migration blocker', record.blocker), paragraph('Business impact', record.impact), paragraph('Next action', record.action));
    context.append(details);
    const time = node('td');
    const age = now() - Date.parse(record.observedAt);
    time.append(node('span', utc(record.observedAt)), node('span', age < 0 ? 'Future-dated evidence' : age > FRESHNESS_HOURS * 3600000 ? 'Stale evidence' : 'Within freshness limit', 'cell-sub'));
    row.append(identity, segment, protection, context, time);
    body.append(row);
  }
  $('row-count').textContent = `Showing ${rows.length} of ${state.snapshot.connections.length} segments`;
  $('empty').hidden = rows.length !== 0;
  $('empty').textContent = state.snapshot.connections.length ? 'No connections match these filters.' : 'This valid snapshot contains no connection records. Coverage is unavailable.';
}

function accept(raw) {
  state.snapshot = validateSnapshot(raw);
  state.status = 'all';
  state.query = '';
  $('status-filter').value = 'all';
  $('search').value = '';
  render();
}

async function loadDemo() {
  const version = ++loadVersion;
  try {
    const response = await fetch('./fixtures/snapshot.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Demo snapshot could not be loaded (HTTP ${response.status}).`);
    const raw = await response.json();
    if (version !== loadVersion) return;
    state.clock = 'snapshot';
    $('clock').value = 'snapshot';
    $('upload').value = '';
    accept(raw);
  } catch (error) {
    if (version === loadVersion) clearResults(error.message);
  }
}

$('upload').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  const version = ++loadVersion;
  try {
    if (file.size > 1_000_000) throw new Error('Choose a JSON snapshot smaller than 1 MB.');
    const raw = JSON.parse(await file.text());
    if (version !== loadVersion) return;
    accept(raw);
  } catch (error) {
    if (version === loadVersion) clearResults(`Local snapshot rejected: ${error.message}`);
  } finally {
    event.target.value = '';
  }
});
$('reset').addEventListener('click', loadDemo);
$('clock').addEventListener('change', event => { state.clock = event.target.value; render(); });
$('status-filter').addEventListener('change', event => { state.status = event.target.value; if (state.snapshot) renderConnections(); });
$('search').addEventListener('input', event => { state.query = event.target.value; if (state.snapshot) renderConnections(); });
roleButtons.forEach(button => button.addEventListener('click', () => { state.role = button.dataset.role; render(); }));
setInterval(() => { if (state.snapshot && state.clock === 'current') render(); }, 60_000);
loadDemo();
