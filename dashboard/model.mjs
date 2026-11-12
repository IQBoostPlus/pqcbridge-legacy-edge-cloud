// Shared reporting rules and traceable evidence for the synthetic dashboard.
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
  if (Object.hasOwn(raw, 'customerReporting')) validateCustomerMetadata(raw.customerReporting, snapshotAt);
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
  const ids = predicate => rows.filter(predicate).map(row => row.id);
  const evidence = {
    clock: now,
    snapshotAt: snapshot.snapshotAt,
    numeratorIds: ids(row => row.status === 'pqc'),
    denominatorIds: rows.map(row => row.id),
    unknownIds: ids(row => row.status === 'unknown'),
    staleIds: ids(row => now - Date.parse(row.observedAt) > FRESHNESS_HOURS * HOUR),
    futureIds: ids(row => Date.parse(row.observedAt) > now),
    suspectedIds: suspectedRows.map(row => row.id),
    expectedFallbackIds: ids(row => row.fallbackKind === 'expected'),
    reasons: [],
  };
  // Retain simultaneous reasons even when a higher-priority condition sets the headline.
  if (suspected) evidence.reasons.push({ code: 'suspected', label: 'Suspected downgrade needs investigation; not a confirmed attack.', ids: [...evidence.suspectedIds] });
  if (!total) evidence.reasons.push({ code: 'empty', label: 'No connection segments available; coverage is unavailable.', ids: [] });
  if (unknown) evidence.reasons.push({ code: 'unknown', label: 'Protection is unknown; these segments remain in the coverage denominator.', ids: [...evidence.unknownIds] });
  if (stale) evidence.reasons.push({ code: 'stale', label: `Observations are older than ${FRESHNESS_HOURS} hours; refresh evidence before a current all-clear.`, ids: [...evidence.staleIds] });
  if (future) evidence.reasons.push({ code: 'future', label: 'Observations are ahead of the reporting clock; check their times.', ids: [...evidence.futureIds] });
  if (futureSnapshot) evidence.reasons.push({ code: 'future-snapshot', label: 'Snapshot time is ahead of the reporting clock.', ids: [] });
  if (evidence.expectedFallbackIds.length) evidence.reasons.push({ code: 'expected-fallback', label: 'Expected classical fallback remains; review exceptions and replacement blockers.', ids: [...evidence.expectedFallbackIds] });
  return { total, pqc, fallback, unknown, coverage: total ? pqc / total * 100 : null,
    stale, future, futureSnapshot, suspected, overall, risks: risks.slice(0, 3), evidence };
}

export function createEvidenceReport(snapshot, now = Date.now(), customerId = snapshot?.customerReporting?.keyCustomerId) {
  const summary = summarize(snapshot, now);
  if (!Number.isFinite(new Date(now).getTime())) throw new Error('Reporting clock must be a representable calendar time.');
  return {
    schemaVersion: 1,
    synthetic: true,
    snapshot: structuredClone(snapshot),
    reportingClock: new Date(now).toISOString(),
    rules: {
      coverage: 'PQC connection segments / all in-scope connection segments, including unknowns, multiplied by 100. Empty coverage is unavailable; display rounds to one decimal.',
      unit: 'Connection segment; device-to-gateway and gateway-to-cloud links count separately. Inventory filters do not change global coverage.',
      freshnessHours: FRESHNESS_HOURS,
      freshnessBoundary: 'Evaluate each observation against the reporting clock. Exactly 24 hours is current; greater than 24 hours is stale. Future observations and future snapshot time prevent an all-clear.',
      statusPrecedence: 'Suspected downgrade -> investigate; otherwise empty/unknown/stale/future evidence -> insufficient evidence; otherwise expected fallback -> migration remaining; otherwise reported segments migrated. Coexisting evidence reasons remain applicable. Migration is not a system-security guarantee.',
    },
    summary,
    customerReport: createCustomerReport(snapshot, customerId, now),
  };
}

export function filterConnections(snapshot, status = 'all', query = '') {
  validateSnapshot(snapshot);
  if (status !== 'all' && !STATUSES.includes(status)) throw new Error('Unsupported connection filter.');
  if (typeof query !== 'string') throw new Error('Search query must be a string.');
  const needle = query.trim().toLowerCase();
  return snapshot.connections.filter(row => (status === 'all' || row.status === status)
    && (!needle || FIELDS.map(field => row[field]).join(' ').toLowerCase().includes(needle)));
}

export const CUSTOMER_DEADLINE = '2027-12-31';
export const CUSTOMER_RULE_VERSION = 'customer-items-v1';

function calendarDate(value, name) {
  if (value === null || value === undefined) return;
  text(value, name);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value))
      || new Date(value).toISOString().slice(0, 10) !== value) {
    throw new Error(`${name} must be a valid YYYY-MM-DD calendar date or null.`);
  }
}

function nullableText(value, name) {
  if (value !== null && value !== undefined) text(value, name);
}

function validateCustomerMetadata(meta, snapshotAt) {
  if (!object(meta)) throw new Error('customerReporting must be an object.');
  if (typeof meta.inventoryComplete !== 'boolean') throw new Error('inventoryComplete must be a boolean.');
  if (!Array.isArray(meta.customers) || !Array.isArray(meta.dataItems) || !Array.isArray(meta.plans)) {
    throw new Error('customerReporting requires customers, dataItems and plans arrays.');
  }
  const customers = new Set();
  for (const customer of meta.customers) {
    if (!object(customer)) throw new Error('Customer must be an object.');
    text(customer.id, 'Customer id'); text(customer.name, 'Customer name');
    if (customers.has(customer.id)) throw new Error(`Duplicate customer id: ${customer.id}.`);
    customers.add(customer.id);
  }
  text(meta.keyCustomerId, 'keyCustomerId');
  if (!customers.has(meta.keyCustomerId)) throw new Error('keyCustomerId must refer to a declared customer.');
  const items = new Map();
  for (const item of meta.dataItems) {
    if (!object(item)) throw new Error('Data item must be an object.');
    text(item.dataItemId, 'dataItemId');
    if (item.customerId !== null && !customers.has(item.customerId)) {
      throw new Error(`Data item ${item.dataItemId}: customerId must be declared or null for unknown ownership.`);
    }
    nullableText(item.dataClass, 'dataClass');
    text(item.confidentiality, 'Data item confidentiality');
    if (utc(item.observedAt, 'Data item observedAt') > snapshotAt) throw new Error('Data item observedAt is after snapshotAt.');
    if (typeof item.mappingComplete !== 'boolean' || !Array.isArray(item.requiredSegmentIds)) {
      throw new Error('Data item requires boolean mappingComplete and requiredSegmentIds array.');
    }
    for (const id of item.requiredSegmentIds) text(id, 'Required segment id');
    // Route records may repeat an item; stable item properties must agree.
    const key = JSON.stringify([item.customerId, item.dataItemId]);
    const signature = JSON.stringify([item.dataClass ?? null, item.confidentiality, item.observedAt, item.mappingComplete]);
    if (items.has(key) && items.get(key) !== signature) throw new Error(`Contradictory data item: ${item.dataItemId}.`);
    items.set(key, signature);
  }
  const plans = new Set();
  for (const plan of meta.plans) {
    if (!object(plan)) throw new Error('Migration plan must be an object.');
    text(plan.segmentId, 'Plan segmentId');
    if (plans.has(plan.segmentId)) throw new Error(`Duplicate migration plan: ${plan.segmentId}.`);
    plans.add(plan.segmentId);
    for (const field of ['plannedMigrationDate', 'replacementDate', 'targetDate']) calendarDate(plan[field], field);
    for (const field of ['blocker', 'consequence', 'action', 'owner']) nullableText(plan[field], `Plan ${field}`);
  }
}

function distinctItems(records) {
  const items = new Map();
  for (const record of records) {
    const key = JSON.stringify([record.customerId, record.dataItemId]);
    if (!items.has(key)) items.set(key, { ...record, requiredSegmentIds: [] });
    const item = items.get(key);
    item.requiredSegmentIds = [...new Set([...item.requiredSegmentIds, ...record.requiredSegmentIds])];
  }
  return [...items.values()];
}

function quantities(items) {
  const total = items.length;
  const counts = Object.fromEntries(['exposed', 'unresolved', 'pqc'].map(bucket =>
    [bucket, items.filter(item => item.bucket === bucket).length]));
  return { total, ...counts, ...Object.fromEntries(Object.entries(counts).map(([key, count]) =>
    [`${key}Percent`, total ? count / total * 100 : null])) };
}

function timeFlags(observedAt, now) {
  const timestamp = Date.parse(observedAt);
  return [...(now - timestamp > FRESHNESS_HOURS * HOUR ? ['stale'] : []), ...(timestamp > now ? ['future'] : [])];
}

/** Customer quantities are logical items, never segment counts or traffic volume. */
export function createCustomerReport(snapshot, customerId = snapshot?.customerReporting?.keyCustomerId, now = Date.now()) {
  validateSnapshot(snapshot);
  if (typeof now !== 'number' || !Number.isFinite(now) || !Number.isFinite(new Date(now).getTime())) {
    throw new Error('Reporting clock must be a finite, representable calendar time.');
  }
  const meta = snapshot.customerReporting;
  if (!meta) return { available: false, reason: 'This legacy snapshot has no customer attribution or data-class inventory. Import a customer-reporting snapshot or reset the demo.' };
  const customer = meta.customers.find(row => row.id === customerId);
  if (!customer) throw new Error('Select a declared customer.');
  const allItems = distinctItems(meta.dataItems);
  const segments = new Map(snapshot.connections.map(row => [row.id, row]));
  const plans = new Map(meta.plans.map(row => [row.segmentId, row]));
  const futureSnapshot = Date.parse(snapshot.snapshotAt) > now;
  const items = allItems.filter(item => item.customerId === customerId).map(item => {
    const path = item.requiredSegmentIds.map(id => segments.get(id));
    const flags = [...timeFlags(item.observedAt, now)];
    if (futureSnapshot) flags.push('future-snapshot');
    if (!item.mappingComplete || !path.length) flags.push('incomplete-path');
    if (path.some(row => !row)) flags.push('missing-segment');
    if (path.some(row => row?.status === 'unknown')) flags.push('unknown-segment');
    for (const row of path.filter(Boolean)) flags.push(...timeFlags(row.observedAt, now));
    const qualityFlags = [...new Set(flags)];
    const exposed = path.some(row => row?.status === 'fallback');
    const bucket = exposed ? 'exposed' : qualityFlags.length ? 'unresolved' : 'pqc';
    const reasons = qualityFlags.map(flag => flag.replaceAll('-', ' '));
    for (const row of path.filter(Boolean)) {
      if (row.status === 'fallback') reasons.push(`${row.id}: ${row.fallbackKind === 'suspected' ? 'Suspected downgrade; not a confirmed attack' : 'Expected classical fallback; no deadline exemption'}. ${row.reason}`);
    }
    if (bucket === 'pqc') reasons.push('All required mapped segments report current PQC evidence.');
    if (!item.dataClass) reasons.push('Unknown class; confidentiality/classification requires review.');
    return { ...item, dataClass: item.dataClass ?? 'Unknown class', bucket, qualityFlags,
      reasons, requiredSegmentIds: [...item.requiredSegmentIds] };
  });
  const classes = [...new Set(items.map(item => item.dataClass))].map(dataClass => {
    const members = items.filter(item => item.dataClass === dataClass);
    return { dataClass, ...quantities(members), confidentialityAssumptions: [...new Set(members.map(item => item.confidentiality))],
      qualityFlags: [...new Set(members.flatMap(item => item.qualityFlags))], itemIds: members.map(item => item.dataItemId) };
  });
  const unattributed = allItems.filter(item => item.customerId === null);
  const incompletePaths = items.some(item => !item.mappingComplete || !item.requiredSegmentIds.length || item.requiredSegmentIds.some(id => !segments.has(id)));
  const limitations = [];
  if (!meta.inventoryComplete) limitations.push('Inventory completeness is not declared; additional customer data/connections may be absent.');
  if (unattributed.length) limitations.push(`${unattributed.length} logical item(s) have unknown customer ownership and are excluded from attributed quantities; customer inventory completeness cannot be established.`);
  if (incompletePaths) limitations.push('Required customer paths are incomplete or reference missing connection evidence.');
  const scope = { inventoryComplete: meta.inventoryComplete && !unattributed.length && !incompletePaths,
    unattributedItemIds: unattributed.map(item => item.dataItemId), unrelatedItemCount: allItems.filter(item => item.customerId && item.customerId !== customerId).length, limitations };
  const connections = [...new Set(items.flatMap(item => item.requiredSegmentIds))].map(segmentId => {
    const row = segments.get(segmentId);
    const plan = plans.get(segmentId);
    const members = items.filter(item => item.requiredSegmentIds.includes(segmentId));
    const qualityFlags = row ? timeFlags(row.observedAt, now) : ['missing-segment'];
    if (futureSnapshot) qualityFlags.push('future-snapshot');
    if (members.some(item => !item.mappingComplete)) qualityFlags.push('incomplete-path');
    const evidenceStatus = row?.status === 'fallback' ? 'classical'
      : row?.status === 'pqc' && !qualityFlags.length ? 'reported-pqc' : 'unresolved';
    const plannedMigrationDate = plan?.plannedMigrationDate ?? null;
    const replacementDate = plan?.replacementDate ?? null;
    const conflict = [plannedMigrationDate, replacementDate].some(date => date && date > CUSTOMER_DEADLINE);
    const scheduleStatus = conflict ? 'conflict' : !plannedMigrationDate ? 'unplanned'
      : plannedMigrationDate === CUSTOMER_DEADLINE ? 'on-deadline' : 'before-deadline';
    return { segmentId, status: row?.status ?? 'missing', evidenceStatus, qualityFlags: [...new Set(qualityFlags)],
      label: evidenceStatus === 'classical' ? 'Classical gap' : evidenceStatus === 'reported-pqc' ? 'Reported current PQC' : 'Unresolved evidence',
      plannedMigrationDate, replacementDate, scheduleStatus,
      blocker: plan?.blocker ?? row?.blocker ?? 'Unknown; verify missing connection.',
      consequence: plan?.consequence ?? row?.impact ?? 'Missing evidence prevents a reliable customer commitment.',
      action: plan?.action ?? row?.action ?? 'Confirm inventory, path and migration plan.',
      owner: plan?.owner ?? null, targetDate: plan?.targetDate ?? null,
      dataClasses: [...new Set(members.map(item => item.dataClass))], dataItemIds: members.map(item => item.dataItemId) };
  });
  const totals = quantities(items);
  const conflicts = connections.filter(row => row.scheduleStatus === 'conflict');
  const unplanned = connections.filter(row => row.scheduleStatus === 'unplanned');
  const scheduleReason = `${conflicts.length} connection(s) have dates beyond the 2027 deadline; ${unplanned.length} have no recorded migration plan. Current PQC evidence and future planning are separate.`;
  const risks = [];
  if (conflicts.length) risks.push({ title: 'Migration or replacement dates miss the 2027 target',
    detail: `${conflicts.map(row => `${row.segmentId} (migration: ${row.plannedMigrationDate ?? 'unknown'}; replacement: ${row.replacementDate ?? 'unknown'})`).join(', ')}: declared replacement or migration is after 31 December 2027. Local fallback approval does not waive the proposed customer requirement.`,
    action: 'Investigate earlier certified replacement or a validated alternative; escalate budget, continuity and contract choices. Feasibility and approval remain unknown.', owner: null, targetDate: null });
  if (totals.exposed) risks.push({ title: `${totals.exposed} customer data item(s) potentially exposed to HNDL`,
    detail: 'At least one required segment uses classical key establishment. Short-lived data is not automatically zero-risk; suspected downgrade is not a confirmed attack.',
    action: 'Sarah investigates the segment evidence; Michael assesses migration and service-continuity options; Emma escalates required decisions.', owner: null, targetDate: null });
  if (totals.unresolved || !scope.inventoryComplete || connections.some(row => row.scheduleStatus === 'unplanned')) risks.push({ title: 'Unresolved evidence or migration planning',
    detail: `${totals.unresolved} unresolved attributed item(s). ${limitations.join(' ')} Missing plans remain unresolved even for reported-PQC connections.`,
    action: 'Confirm customer ownership, data classes, complete paths, observations and accountable migration plans before a customer commitment.', owner: null, targetDate: null });
  const overall = totals.exposed ? { level: 'amber', label: 'Customer migration gaps', reason: `${totals.exposed} of ${totals.total} attributed logical items have potential HNDL exposure; ${totals.unresolved} remain unresolved. ${scope.inventoryComplete ? '' : 'Scope completeness is unresolved. '}${scheduleReason}` }
    : !scope.inventoryComplete || totals.unresolved || !totals.total ? { level: 'unknown', label: 'Customer evidence incomplete', reason: 'Scope or protection evidence is unresolved; a customer all-clear cannot be established.' }
      : conflicts.length || unplanned.length ? { level: 'amber', label: 'Customer planning gaps', reason: `Declared paths report usable PQC evidence. ${scheduleReason} Confirm the customer commitment at review.` }
      : { level: 'green', label: 'Reported customer paths use PQC', reason: 'All declared customer item paths report usable PQC evidence. This is not a security guarantee or production-migration acceptance.' };
  return { available: true, reason: overall.reason, overall, ruleVersion: CUSTOMER_RULE_VERSION, customer: { ...customer },
    deadline: CUSTOMER_DEADLINE, reportingClock: new Date(now).toISOString(), snapshotAt: snapshot.snapshotAt,
    unit: 'Distinct logical data items', scope, totals, classes, items, connections, risks: risks.slice(0, 3),
    methodology: [
      'A logical item represents a declared stream or information asset. Counts/proportions do not estimate bytes, traffic volume, attack probability or financial loss.',
      'Deduplicate by customer + dataItemId and merge required segment IDs. One primary class per item; unknown class remains visible.',
      'Any known classical required segment establishes potential HNDL exposure, retaining simultaneous quality flags; otherwise incomplete/missing/unknown/stale/future evidence is unresolved; otherwise reported PQC.',
      'Known-classical observations remain potential exposure even when stale. Exactly 24 hours is current; older is stale. Future item/segment/snapshot evidence cannot support reported PQC.',
      'Unknown ownership is outside attributed totals but prevents complete-customer claims. Inventory filters do not change customer totals.',
      'The proposed deadline applies to every required customer-data connection, including expected fallback and short-lived telemetry. A plan is not migration completion; 2028 replacements conflict with 2027.',
      'All records are synthetic; no confirmed harvesting/attack, live protection, accepted waiver, funding or feasible replacement is inferred.'
    ] };
}
