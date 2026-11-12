<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { FRESHNESS_HOURS } from '../../model.mjs';
import { state, clockTime } from '../dashboard.js';
import { statusLabels, segmentLabels, utc } from '../display.js';
import AppIcon from './AppIcon.vue';
import PagedText from './PagedText.vue';

const route = useRoute();
const field = ref(0);
const row = computed(() => state.snapshot.connections.find(connection => connection.id === route.params.id));
const back = computed(() => ['security', 'migration'].includes(route.query.from) ? route.query.from : 'connections');
const fields = computed(() => row.value ? [
  ['Classification reason', row.value.reason], ['Confidentiality', row.value.confidentiality],
  ['Migration blocker', row.value.blocker], ['Business impact', row.value.impact], ['Next action', row.value.action],
  ['Connection identity', row.value.id + ' · ' + row.value.device + ' · ' + segmentLabels[row.value.segment]],
  ['Path context', state.snapshot.connections.filter(item => item.device === row.value.device).map(item => `${item.id}: ${segmentLabels[item.segment]} reports ${item.status} (${item.keyEstablishment}).`).join(' ') + ' These are reported segments, not proof of a complete inventory or end-to-end security.'],
] : []);
const freshness = computed(() => {
  const age = clockTime.value - Date.parse(row.value.observedAt);
  if (age < 0) return 'Future-dated evidence';
  return age > FRESHNESS_HOURS * 3_600_000 ? 'Stale evidence' : 'Within freshness limit';
});
watch(() => route.params.id, () => { field.value = 0; });
</script>

<template>
  <section v-if="row" class="panel focus-card evidence-card">
    <div class="panel-heading focus-heading">
      <div class="focus-title"><h2 :title="row.device">{{ row.device }}</h2><p :title="row.id">{{ row.id }} · {{ segmentLabels[row.segment] }}</p></div>
      <span class="badge" :class="row.status">{{ statusLabels[row.status] }}</span>
    </div>
    <div class="evidence-meta">
      <div><span>Key establishment</span><strong>{{ row.keyEstablishment }}</strong></div>
      <div><span>Classification</span><strong>{{ row.fallbackKind === 'suspected' ? 'Suspected · synthetic' : row.fallbackKind === 'expected' ? 'Expected fallback' : row.fallbackKind === 'unknown' ? 'Unknown' : 'PQC' }}</strong></div>
      <div><span>{{ freshness }}</span><time :datetime="row.observedAt">{{ utc(row.observedAt) }}</time></div>
    </div>
    <label class="field-control"><span>Evidence field</span>
      <select v-model.number="field" aria-label="Evidence field"><option v-for="([label], index) in fields" :key="label" :value="index">{{ label }}</option></select>
    </label>
    <PagedText :text="fields[field][1]" />
    <div class="focus-footer"><RouterLink class="text-link" :to="{ name: back }"><AppIcon name="back" />Back to {{ back }}</RouterLink><RouterLink class="text-link" :to="{ name: 'indicators' }">Indicator evidence</RouterLink></div>
  </section>
  <section v-else class="panel centered">
    <h2>Connection not in this snapshot</h2><p>Choose a segment from the current inventory.</p>
    <RouterLink class="button" :to="{ name: 'connections' }">Open connections</RouterLink>
  </section>
</template>
