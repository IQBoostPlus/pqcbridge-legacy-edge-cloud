// Shared reporting rules for the synthetic Sprint 1 dashboard.
export const FRESHNESS_HOURS = 24;
const HOUR = 60 * 60 * 1000;
const STATUSES = ['pqc', 'fallback', 'unknown'];
const SEGMENTS = ['device-to-gateway', 'gateway-to-cloud'];
const FIELDS = ['id', 'device', 'segment', 'keyEstablishment', 'status', 'reason',
  'observedAt', 'fallbackKind', 'blocker', 'confidentiality', 'impact', 'action'];

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function text(value, name) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${name} must be a nonempty string.`);
  }
}

function utc(value, name) {
  text(value, name);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/.test(value)) {
    throw new Error(`${name} must be an ISO UTC timestamp (ending in Z).`);
  }
  const time = Date.parse(value);
  const normalized = value.includes('.') ? value : value.replace('Z', '.000Z');
  if (!Number.isFinite(time) || new Date(time).toISOString() !== normalized) {
    throw new Error(`${name} must be a valid calendar timestamp.`);
  }
  return time;
}

export function validateSnapshot(raw) {
  if (!object(raw)) throw new Error('Snapshot must be an object.');
  if (raw.schemaVersion !== 1) throw new Error('Unsupported snapshot schemaVersion; expected 1.');
  if (raw.synthetic !== true) throw new Error('Snapshot must explicitly declare synthetic: true.');
  text(raw.title, 'Snapshot title');
  const snapshotAt = utc(raw.snapshotAt, 'snapshotAt');
  if (!Array.isArray(raw.connections)) throw new Error('connections must be an array.');
  const ids = new Set();
  raw.connections.forEach((row, index) => {
    const context = `Connection ${index + 1}`;
    if (!object(row)) throw new Error(`${context} must be an object.`);
    for (const field of FIELDS) text(row[field], `${context} ${field}`);
    if (ids.has(row.id)) throw new Error(`Duplicate connection id: ${row.id}.`);
    ids.add(row.id);
    if (!SEGMENTS.includes(row.segment)) throw new Error(`${context} has an unsupported segment.`);
    if (!STATUSES.includes(row.status)) throw new Error(`${context} has an unsupported status.`);
    const observedAt = utc(row.observedAt, `${context} observedAt`);
    if (observedAt > snapshotAt) throw new Error(`${context} observedAt is after snapshotAt.`);
    if (row.status === 'pqc' && (row.keyEstablishment !== 'ML-KEM-768' || row.fallbackKind !== 'none')) {
      throw new Error(`${context}: PQC requires ML-KEM-768 and fallbackKind none.`);
    }
    if (row.status === 'fallback' && (row.keyEstablishment !== 'ECDH-P256' || !['expected', 'suspected'].includes(row.fallbackKind))) {
      throw new Error(`${context}: fallback requires ECDH-P256 and expected/suspected fallbackKind.`);
    }
    if (row.status === 'unknown' && (row.keyEstablishment !== 'unknown' || row.fallbackKind !== 'unknown')) {
      throw new Error(`${context}: unknown status requires unknown keyEstablishment and fallbackKind.`);
    }
  });
  return raw;
}

export function summarize(snapshot, now = Date.now()) {
  validateSnapshot(snapshot);
  if (typeof now !== 'number' || !Number.isFinite(now)) throw new Error('Reporting clock must be a finite epoch time.');
  const rows = snapshot.connections;
  const total = rows.length;
  const pqc = rows.filter(row => row.status === 'pqc').length;
  const fallback = rows.filter(row => row.status === 'fallback').length;
  const unknown = total - pqc - fallback;
  const stale = rows.filter(row => now - Date.parse(row.observedAt) > FRESHNESS_HOURS * HOUR).length;
  const future = rows.filter(row => Date.parse(row.observedAt) > now).length;
  const futureSnapshot = Date.parse(snapshot.snapshotAt) > now;
  const suspectedRows = rows.filter(row => row.fallbackKind === 'suspected');
  const suspected = suspectedRows.length;
  let overall;
  if (suspected) {
    const cases = suspected === 1 ? 'One synthetic case needs review' : `${suspected} synthetic cases need review`;
    overall = { level: 'red', label: 'Investigate', reason: `${cases} for suspected downgrade. This is not a confirmed attack.` };
  } else if (!total || unknown || stale || future || futureSnapshot) {
    overall = { level: 'unknown', label: 'Insufficient evidence', reason: `${total ? `${unknown} unknown, ${stale} stale and ${future} future-dated segment(s).` : 'No connection segments available.'}${futureSnapshot ? ' Snapshot time is ahead of the reporting clock.' : ''} An all-clear cannot be established.` };
  } else if (fallback) {
    overall = { level: 'amber', label: 'Migration remaining', reason: `${fallback} expected classical fallback segment(s) remain. Review confidentiality assumptions and replacement blockers.` };
  } else {
    overall = { level: 'green', label: 'Reported segments migrated', reason: 'All reported segments use ML-KEM-768 and are current under the prototype rule. This is a migration indication, not a system-security guarantee.' };
  }
  const risks = [];
  if (suspected) risks.push({
    title: `${suspected} suspected downgrade scenario(s)`,
    detail: suspectedRows.map(row => `${row.id}: ${row.reason} Business impact: ${row.impact}`).join(' '),
    action: suspectedRows.map(row => `${row.id}: ${row.action}`).join(' '),
  });
  if (!total || unknown || stale || future || futureSnapshot) risks.push({
    title: 'Incomplete or out-of-date evidence',
    detail: `${unknown} unknown; ${stale} older than ${FRESHNESS_HOURS} hours; ${future} future-dated segments.${futureSnapshot ? ' Snapshot is ahead of the reporting clock.' : ''}${!total ? ' No segments reported.' : ''} Uncertainty can hide migration blockers and delay decisions.`,
    action: 'Confirm inventory and observation times before reporting an all-clear or committing migration dates.',
  });
  if (fallback) risks.push({
    title: `${fallback} classical fallback segment(s)`,
    detail: 'Synthetic ECDH-P256 traffic may remain exposed to future decryption under the stated confidentiality assumptions. Replacement delays must be balanced against service continuity.',
    action: 'Inspect each confidentiality assumption and blocker; agree time-limited exceptions and replacement priorities with stakeholders.',
  });
  return { total, pqc, fallback, unknown, coverage: total ? pqc / total * 100 : null,
    stale, suspected, overall, risks: risks.slice(0, 3) };
}

export function filterConnections(snapshot, status = 'all', query = '') {
  validateSnapshot(snapshot);
  if (status !== 'all' && !STATUSES.includes(status)) throw new Error('Unsupported connection filter.');
  if (typeof query !== 'string') throw new Error('Search query must be a string.');
  const needle = query.trim().toLowerCase();
  return snapshot.connections.filter(row => (status === 'all' || row.status === status)
    && (!needle || FIELDS.map(field => row[field]).join(' ').toLowerCase().includes(needle)));
}
