<script setup>
import { clockTime, downloadEvidence, state, summary } from '../dashboard.js';
import { utc } from '../display.js';
</script>

<template>
  <section class="panel indicator-audit" aria-label="Indicator evidence">
    <template v-if="summary">
      <div class="panel-heading">
        <div><h2>Trace the indicators</h2><p>Reported migration, evidence quality and investigation needs</p></div>
        <button class="button" :disabled="state.loading" @click="downloadEvidence">Export evidence JSON</button>
      </div>
      <div class="audit-controls">
        <label class="field-control"><span>Reporting clock</span>
          <select v-model="state.clock" aria-label="Reporting clock" :disabled="state.loading">
            <option value="snapshot">Historical snapshot</option><option value="current">Current time</option>
          </select>
        </label>
        <p>Synthetic data · {{ state.source }} · {{ summary.total }} connection segments</p>
      </div>
      <section class="audit-section" aria-labelledby="coverage-rule">
        <h3 id="coverage-rule">Coverage: {{ summary.coverage === null ? 'Unavailable' : summary.coverage.toFixed(1) + '%' }}</h3>
        <p class="audit-formula">{{ summary.pqc }} PQC / {{ summary.total }} in-scope segments × 100</p>
        <p>Unknown segments remain in the denominator. Empty data has no coverage value.
          Inventory filters do not change this global calculation. The displayed percentage is rounded to one decimal.</p>
        <p>A gateway-to-cloud PQC segment describes that link only. Reported migration does not establish end-to-end protection or system security.</p>
      </section>
      <section class="audit-section" aria-labelledby="clock-rule">
        <h3 id="clock-rule">Evidence time</h3>
        <dl class="audit-times">
          <div><dt>Snapshot time</dt><dd>{{ utc(state.snapshot.snapshotAt) }}</dd></div>
          <div><dt>Reporting clock · {{ state.clock === 'snapshot' ? 'historical' : 'current' }}</dt><dd>{{ utc(clockTime) }}</dd></div>
          <div><dt>Freshness rule</dt><dd>Each observation: older than 24 hours is stale; exactly 24 hours is current.</dd></div>
        </dl>
        <p>Historical mode evaluates this snapshot at its own time. Current mode re-evaluates the same observations; it does not fetch live data.</p>
      </section>
      <section class="audit-section" aria-labelledby="status-rule">
        <h3 id="status-rule">{{ summary.overall.label }}</h3>
        <p>{{ summary.overall.reason }}</p>
        <p>Priority: suspected downgrade → insufficient evidence → expected fallback → reported migration.</p>
        <ul class="evidence-reasons" aria-label="All evidence conditions">
          <li v-for="reason in summary.evidence.reasons" :key="reason.code"><strong>{{ reason.label }}</strong>
            <span v-if="reason.ids.length"> · {{ reason.ids.join(', ') }}</span>
          </li>
        </ul>
        <p v-if="!summary.evidence.reasons.length">No investigation or data-quality condition is flagged under the prototype rules.</p>
        <p>Investigation can coexist with stale or unknown evidence. Suspected downgrade is an unconfirmed synthetic classification, not a detected attack.</p>
      </section>
      <section class="audit-section" aria-labelledby="input-records">
        <h3 id="input-records">Inputs behind the percentage</h3>
        <p>{{ summary.pqc }} numerator records · {{ summary.total }} denominator records. Classification, reasons and confidentiality assumptions come from the supplied synthetic snapshot.</p>
        <ul class="audit-records">
          <li v-for="row in state.snapshot.connections" :key="row.id">
            <RouterLink :to="{ name: 'evidence', params: { id: row.id } }">{{ row.id }} · {{ row.device }}</RouterLink>
            <span>{{ row.segment }} · {{ row.status }} · {{ row.status === 'pqc' ? 'Numerator + denominator' : 'Denominator only' }}</span>
            <time :datetime="row.observedAt">Observed {{ utc(row.observedAt) }}</time>
          </li>
        </ul>
      </section>
      <p class="audit-limit">HNDL exposure depends on stated confidentiality assumptions. This report verifies reporting inputs and rules; it does not establish cryptographic assurance.</p>
    </template>
    <template v-else>
      <h2>Evidence unavailable</h2><p>A valid synthetic snapshot is required. Invalid data is not an empty dataset.</p>
      <RouterLink class="text-link" :to="{ name: 'snapshot' }">Open dataset settings</RouterLink>
    </template>
  </section>
</template>
