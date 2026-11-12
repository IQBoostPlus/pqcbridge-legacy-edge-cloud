<script setup>
import { computed } from 'vue';
import { summary, state } from '../dashboard.js';
import { utc } from '../display.js';
import AppIcon from './AppIcon.vue';

const legend = computed(() => [
  { id: 'pqc', title: 'Reported PQC', value: summary.value.pqc },
  { id: 'fallback', title: 'Classical fallback', value: summary.value.fallback },
  { id: 'unknown', title: 'Unknown', value: summary.value.unknown },
]);
const arcs = computed(() => {
  let offset = 0;
  return legend.value.filter(item => item.value > 0).map(item => {
    const length = 100 * item.value / summary.value.total;
    const gap = item.value === summary.value.total ? 0 : Math.min(1, length / 2);
    const arc = { ...item, length: length - gap, offset };
    offset += length;
    return arc;
  });
});
</script>

<template>
  <div class="overview-layout">
    <section class="panel coverage-card">
      <div class="panel-heading">
        <div><h2>Connection coverage</h2><p>Share of all in-scope connection segments</p></div>
        <RouterLink :to="{ name: 'connections' }" class="icon-button" aria-label="Open connection inventory"><AppIcon name="arrow" /></RouterLink>
      </div>
      <div class="coverage-graphic">
        <div class="ring-wrap">
          <svg viewBox="0 0 240 240" class="ring" aria-hidden="true">
            <circle class="ring-guide" cx="120" cy="120" r="110"/>
            <circle class="ring-track" cx="120" cy="120" r="94" pathLength="100"/>
            <circle v-for="arc in arcs" :key="arc.id" :class="'ring-' + arc.id" cx="120" cy="120" r="94" pathLength="100"
              :stroke-dasharray="arc.length + ' ' + (100 - arc.length)" :stroke-dashoffset="-arc.offset"/>
          </svg>
          <div class="ring-caption">
            <strong>{{ summary.coverage === null ? '—' : summary.coverage.toFixed(1) + '%' }}</strong>
            <span>{{ summary.coverage === null ? 'Unavailable' : 'PQC coverage' }}</span>
          </div>
        </div>
        <div class="coverage-breakdown">
          <dl class="legend">
            <div v-for="item in legend" :key="item.id"><dt><i :class="item.id"></i>{{ item.title }}</dt><dd>{{ item.value }}</dd></div>
            <div class="legend-total"><dt>Total segments</dt><dd>{{ summary.total }}</dd></div>
          </dl>
          <p class="coverage-note">{{ summary.pqc }} / {{ summary.total }} segments × 100. Unknown segments count toward the total.</p>
        </div>
      </div>
      <div class="coverage-audit-link"><RouterLink class="text-link" :to="{ name: 'customer' }">Customer exposure report</RouterLink> · <RouterLink class="text-link" :to="{ name: 'indicators' }">Trace segment calculation</RouterLink></div>
    </section>

    <section class="panel status-card">
      <div class="panel-heading"><h2>Overall status</h2><span class="badge" :class="summary.overall.level">{{ summary.overall.level }}</span></div>
      <div class="status-reading">
        <h3>{{ summary.overall.label }}</h3>
        <p>{{ summary.overall.reason }}</p>
        <p v-if="summary.stale || summary.unknown || summary.future || summary.futureSnapshot" class="status-evidence-note">Evidence limits: {{ summary.unknown }} unknown · {{ summary.stale }} stale · {{ summary.future }} future-dated segments<span v-if="summary.futureSnapshot"> · snapshot ahead of reporting clock</span>.</p>
      </div>
      <RouterLink :to="{ name: 'executive' }" class="text-link">Executive briefing <AppIcon name="arrow" /></RouterLink>
    </section>

    <section class="panel snapshot-card">
      <div class="snapshot-label">
        <span class="snapshot-icon"><AppIcon name="database" /></span>
        <div><h2>Evidence freshness</h2><p>{{ state.clock === 'snapshot' ? 'Historical snapshot' : 'Evaluated against current time' }}</p></div>
      </div>
      <div class="freshness-reading">
        <p><strong>{{ summary.stale }}</strong> stale segments</p>
        <small>24-hour limit</small>
      </div>
      <div class="snapshot-timestamp">
        <small>Snapshot time</small>
        <time :datetime="state.snapshot.snapshotAt">{{ utc(state.snapshot.snapshotAt) }}</time>
      </div>
      <RouterLink :to="{ name: 'snapshot' }" class="text-link snapshot-link">Dataset settings <AppIcon name="arrow" /></RouterLink>
    </section>
  </div>
</template>
