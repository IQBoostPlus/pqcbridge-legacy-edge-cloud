<script setup>
import { computed, ref, watch } from 'vue';
import { clockTime, customerReport, downloadEvidence, state } from '../dashboard.js';
import { utc } from '../display.js';
import AppIcon from './AppIcon.vue';

const props = defineProps({ role: { type: String, default: 'executive' } });
const classFilter = ref('all');
const bucketFilter = ref('all');
const report = customerReport;
const buckets = { exposed: 'Potential HNDL exposure', unresolved: 'Unresolved evidence', pqc: 'Reported PQC' };
const roles = {
  security: ['Sarah · Security officer', 'Inspect exposed classes and their complete paths. Check confidentiality assumptions, suspected downgrade and concurrent evidence gaps.'],
  migration: ['Michael · Migration manager', 'Identify customer connections still requiring work. Compare the 2027 target with 2028 replacements and continuity constraints before proposing a decision.'],
  executive: ['Emma · Chief information officer', 'Explain where the customer stands, the limits of the evidence and the decisions needed on budget, continuity and the revised deadline.'],
};
const persona = computed(() => roles[props.role] ?? roles.executive);
const filteredItems = computed(() => (report.value.items ?? []).filter(item =>
  (classFilter.value === 'all' || item.dataClass === classFilter.value)
  && (bucketFilter.value === 'all' || item.bucket === bucketFilter.value)));
const percent = value => value === null || value === undefined ? 'Unavailable' : `${value.toFixed(1)}%`;
const connectionExists = id => state.snapshot.connections.some(row => row.id === id);
const flagLabel = code => code.replaceAll('-', ' ');
watch(() => [state.revision, state.customerId], () => { classFilter.value = 'all'; bucketFilter.value = 'all'; });
</script>

<template>
  <section v-if="!report.available" class="panel centered">
    <AppIcon name="warning" /><h2>Customer report unavailable</h2>
    <p>{{ report.reason }}</p>
    <p>Legacy snapshots still support the all-system views. Customer attribution is never inferred from global connection counts.</p>
    <RouterLink class="button primary" :to="{ name: 'snapshot' }">Load or reset customer demo</RouterLink>
    <RouterLink class="text-link" :to="{ name: 'overview' }">Open all-system overview</RouterLink>
  </section>
  <article v-else class="panel customer-report" aria-label="Customer migration report">
    <header class="report-heading">
      <div>
        <span class="report-eyebrow">CUSTOMER REPORT · SYNTHETIC SCENARIO</span>
        <h2>{{ report.customer.name }}</h2>
        <p>{{ report.customer.id }} · Initial report for Sprint review</p>
      </div>
      <button type="button" class="button primary" :disabled="state.loading" @click="downloadEvidence">Export report evidence</button>
    </header>

    <div class="report-controls">
      <label class="field-control"><span>Customer scope</span>
        <select v-model="state.customerId" aria-label="Customer scope" @change="classFilter = 'all'; bucketFilter = 'all'">
          <option v-for="customer in state.snapshot.customerReporting.customers" :key="customer.id" :value="customer.id">{{ customer.name }}</option>
        </select>
      </label>
      <label class="field-control"><span>Reporting clock</span>
        <select v-model="state.clock" aria-label="Customer reporting clock">
          <option value="snapshot">Historical snapshot</option><option value="current">Current time</option>
        </select>
      </label>
      <p>As of <time>{{ utc(clockTime) }}</time><br>Snapshot <time>{{ utc(report.snapshotAt) }}</time></p>
    </div>

    <section class="report-status" :class="report.overall.level" aria-label="Customer position">
      <div><span class="badge" :class="report.overall.level">{{ report.overall.label }}</span><h3>All customer-data connections: PQC by 31 Dec 2027</h3></div>
      <p>{{ report.overall.reason }}</p>
      <p>Previously end of 2030. The proposed requirement includes telemetry and approved fallback. A migration plan is not completed migration.</p>
    </section>

    <div class="report-persona"><strong>{{ persona[0] }}</strong><p>{{ persona[1] }}</p></div>

    <section class="report-section" aria-labelledby="data-exposure">
      <div class="report-section-title"><div><h3 id="data-exposure">Customer data exposure by class</h3><p>Unit: distinct logical data items · {{ report.totals.total }} in scope</p></div><span class="badge" :class="report.scope.inventoryComplete ? 'pqc' : 'unknown'">{{ report.scope.inventoryComplete ? 'Declared inventory complete' : 'Scope completeness unresolved' }}</span></div>
      <div class="report-metrics">
        <div v-for="bucket in ['exposed', 'unresolved', 'pqc']" :key="bucket" class="report-metric" :class="bucket">
          <span>{{ buckets[bucket] }}</span><strong>{{ report.totals[bucket] }} <small>/ {{ report.totals.total }} items</small></strong><span>{{ percent(report.totals[`${bucket}Percent`]) }}</span>
        </div>
      </div>
      <div class="class-table-wrap" tabindex="0" role="region" aria-label="Data class quantities, scroll horizontally if needed">
        <table class="class-table">
          <caption>Each item counts once across all required segments. The three categories reconcile to each class total.</caption>
          <thead><tr><th scope="col">Data class / confidentiality assumption</th><th scope="col">Total items</th><th scope="col">Potential HNDL</th><th scope="col">Unresolved</th><th scope="col">Reported PQC</th></tr></thead>
          <tbody><tr v-for="group in report.classes" :key="group.dataClass">
            <th scope="row">{{ group.dataClass }}<small v-for="assumption in group.confidentialityAssumptions" :key="assumption">{{ assumption }}</small><small v-if="group.qualityFlags.length">Evidence flags: {{ group.qualityFlags.map(flagLabel).join(', ') }}</small></th>
            <td>{{ group.total }}</td><td>{{ group.exposed }} <small>{{ percent(group.exposedPercent) }}</small></td><td>{{ group.unresolved }} <small>{{ percent(group.unresolvedPercent) }}</small></td><td>{{ group.pqc }} <small>{{ percent(group.pqcPercent) }}</small></td>
          </tr></tbody>
        </table>
      </div>
      <p v-if="!report.totals.total" class="report-notice">No customer data items are available. Percentages are unavailable; this is not evidence of protection.</p>
      <div class="report-notice">
        <strong>Scope and uncertainty</strong>
        <ul v-if="report.scope.limitations.length"><li v-for="limitation in report.scope.limitations" :key="limitation">{{ limitation }}</li></ul>
        <p>{{ report.scope.unrelatedItemCount }} item(s) assigned to other customers are excluded from these totals.</p>
        <p v-if="report.scope.unattributedItemIds.length">Customer attribution unresolved: {{ report.scope.unattributedItemIds.join(', ') }}. These records are not silently assigned to this customer.</p>
      </div>
      <p>These are item counts, not bytes, traffic-volume shares or attack probabilities. Short confidentiality lifetimes do not imply zero HNDL risk. Reported PQC does not establish future security.</p>
    </section>

    <section class="report-section" aria-labelledby="connection-gap">
      <h3 id="connection-gap">2027 migration gap and continuity</h3>
      <p>All distinct required customer connections are listed, including missing evidence. Current key establishment and planned timing are separate. Relevant 2028 replacements conflict with the 2027 target.</p>
      <div class="gap-list">
        <details v-for="connection in report.connections" :key="connection.segmentId" class="gap-card">
          <summary><strong>{{ connection.segmentId }}</strong><span>{{ connection.label }}</span><span class="badge" :class="connection.scheduleStatus === 'conflict' ? 'red' : 'unknown'">{{ flagLabel(connection.scheduleStatus) }}</span></summary>
          <div class="gap-content">
            <p><strong>Data:</strong> {{ connection.dataClasses.join(', ') }} · {{ connection.dataItemIds.join(', ') }}</p>
            <p><strong>Evidence flags:</strong> {{ connection.qualityFlags.length ? connection.qualityFlags.map(flagLabel).join(', ') : 'None under the selected clock' }}</p>
            <dl class="report-facts">
              <div><dt>Planned PQC migration</dt><dd>{{ connection.plannedMigrationDate ?? 'Unknown / no agreed plan' }}</dd></div>
              <div><dt>Replacement availability</dt><dd>{{ connection.replacementDate ?? 'Unknown / not recorded' }}</dd></div>
              <div><dt>Blocker</dt><dd>{{ connection.blocker }}</dd></div>
              <div><dt>Continuity / business consequence</dt><dd>{{ connection.consequence }}</dd></div>
              <div><dt>Proposed next action</dt><dd>{{ connection.action }}</dd></div>
              <div><dt>Owner / action target</dt><dd>{{ connection.owner ?? 'Unassigned' }} · {{ connection.targetDate ?? 'Unknown' }}</dd></div>
            </dl>
            <p v-if="connection.scheduleStatus === 'conflict'" class="conflict-note">Decision required: investigate earlier replacement or a validated alternative, or escalate the contract conflict. Feasibility, funding and a customer waiver are not established.</p>
            <RouterLink v-if="connectionExists(connection.segmentId)" class="text-link" :to="{ name: 'evidence', params: { id: connection.segmentId } }">Inspect connection evidence <AppIcon name="arrow" /></RouterLink>
            <p v-else>Required segment has no connection record; inventory confirmation is needed.</p>
          </div>
        </details>
        <p v-if="!report.connections.length">No required connections mapped. The customer's full connection inventory is not established.</p>
      </div>
    </section>

    <section class="report-section" aria-labelledby="customer-decisions">
      <h3 id="customer-decisions">Priority risks and next decisions</h3>
      <ol class="report-risks">
        <li v-for="risk in report.risks" :key="risk.title"><h4>{{ risk.title }}</h4><p>{{ risk.detail }}</p><p><strong>Proposed action:</strong> {{ risk.action }}</p><small>Owner: {{ risk.owner ?? 'Unassigned' }} · Target: {{ risk.targetDate ?? 'Unknown' }}</small></li>
      </ol>
      <p v-if="!report.risks.length">No additional risk is flagged under these reporting rules. Confirm scope, evidence and stakeholder decisions at review.</p>
      <p>Emma must weigh the deadline against service continuity and budget. Michael's replacement constraint and Sarah's exposure concerns remain visible; no outage, spending or exception is authorized by this report.</p>
    </section>

    <section class="report-section" aria-labelledby="item-evidence">
      <h3 id="item-evidence">Trace the data items</h3>
      <div class="report-controls">
        <label class="field-control"><span>Data class</span><select v-model="classFilter" aria-label="Filter data class"><option value="all">All classes</option><option v-for="group in report.classes" :key="group.dataClass" :value="group.dataClass">{{ group.dataClass }}</option></select></label>
        <label class="field-control"><span>Exposure category</span><select v-model="bucketFilter" aria-label="Filter exposure category"><option value="all">All categories</option><option v-for="(label, key) in buckets" :key="key" :value="key">{{ label }}</option></select></label>
      </div>
      <p role="status">Showing {{ filteredItems.length }} of {{ report.totals.total }} customer items. Filters affect this list only; customer and class totals remain unchanged.</p>
      <div class="item-list">
        <details v-for="item in filteredItems" :key="item.dataItemId" class="item-card">
          <summary><strong>{{ item.dataItemId }}</strong><span>{{ item.dataClass }}</span><span class="badge" :class="item.bucket === 'exposed' ? 'amber' : item.bucket === 'pqc' ? 'pqc' : 'unknown'">{{ buckets[item.bucket] }}</span></summary>
          <div class="gap-content">
            <p><strong>Confidentiality assumption:</strong> {{ item.confidentiality }}</p>
            <p><strong>Item observed:</strong> <time>{{ utc(item.observedAt) }}</time> · Path mapping {{ item.mappingComplete ? 'declared complete' : 'incomplete' }}</p>
            <p><strong>Required segments:</strong> {{ item.requiredSegmentIds.length ? item.requiredSegmentIds.join(', ') : 'Not mapped' }}</p>
            <p><strong>Concurrent quality flags:</strong> {{ item.qualityFlags.length ? item.qualityFlags.map(flagLabel).join(', ') : 'None under the selected clock' }}</p>
            <ul><li v-for="reason in item.reasons" :key="reason">{{ reason }}</li></ul>
            <div class="item-links"><template v-for="id in item.requiredSegmentIds" :key="id"><RouterLink v-if="connectionExists(id)" class="text-link" :to="{ name: 'evidence', params: { id } }">{{ id }}</RouterLink><span v-else>{{ id }} · missing record</span></template></div>
          </div>
        </details>
      </div>
    </section>

    <section class="report-section" aria-labelledby="customer-method">
      <h3 id="customer-method">Methodology and reporting limits</h3>
      <p>Rules: {{ report.ruleVersion }} · {{ report.unit }}</p>
      <ul><li v-for="rule in report.methodology" :key="rule">{{ rule }}</li></ul>
      <p>Known classical exposure takes precedence over unresolved evidence; quality flags remain visible. Otherwise incomplete or unusable evidence is unresolved. Reported PQC requires a complete mapped path and usable evidence on every segment.</p>
      <p>Observations older than 24 hours are stale; exactly 24 hours is current. Current-time mode re-evaluates this synthetic snapshot without fetching live data. Missing classification remains Unknown class.</p>
      <p>Connection-segment coverage is a separate inventory measure. The historical all-system value 5/8 = 62.5% does not measure this customer's data exposure.</p>
      <div class="item-links"><RouterLink class="text-link" :to="{ name: 'indicators' }">All-system indicator audit <AppIcon name="arrow" /></RouterLink><RouterLink class="text-link" :to="{ name: 'overview' }">All-system overview</RouterLink></div>
    </section>
  </article>
</template>
