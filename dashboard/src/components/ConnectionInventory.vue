<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { rows, state, summary } from '../dashboard.js';
import { segmentLabels, statusLabels, utc } from '../display.js';
import AppIcon from './AppIcon.vue';
import PageStepper from './PageStepper.vue';

const windowBox = ref(null);
const capacity = ref(3);
const current = ref(0);
const count = computed(() => Math.max(1, Math.ceil(rows.value.length / capacity.value)));
const page = computed(() => Math.min(current.value, count.value - 1));
const visible = computed(() => rows.value.slice(page.value * capacity.value, (page.value + 1) * capacity.value));
let observer;

function fit() {
  const box = windowBox.value;
  const header = box.querySelector('.connection-columns').offsetHeight;
  const rowHeight = parseFloat(getComputedStyle(box).getPropertyValue('--row-height'));
  capacity.value = Math.max(1, Math.floor((box.clientHeight - header) / rowHeight));
}

onMounted(() => {
  observer = new ResizeObserver(fit);
  observer.observe(windowBox.value);
  fit();
});
onBeforeUnmount(() => observer?.disconnect());
watch(() => [state.status, state.query, state.revision], () => { current.value = 0; });

function clear() {
  state.status = 'all';
  state.query = '';
}
</script>

<template>
  <section class="panel inventory-panel" aria-label="Connection inventory">
    <div class="inventory-filters">
      <label class="search-field"><span>Search connections</span><input v-model="state.query" type="search" placeholder="Device, ID or reason"></label>
      <label><span>Protection</span>
        <select v-model="state.status" aria-label="Protection"><option value="all">All statuses</option><option value="pqc">PQC</option><option value="fallback">Fallback</option><option value="unknown">Unknown</option></select>
      </label>
    </div>
    <div ref="windowBox" class="inventory-window">
      <div class="connection-columns" aria-hidden="true"><span>Connection</span><span>Segment / algorithm</span><span>Protection</span><span>Last observed (UTC)</span><span></span></div>
      <ul v-if="visible.length" class="connection-list" aria-label="Matching connection segments">
        <li v-for="row in visible" :key="row.id">
          <RouterLink class="connection-row" :to="{ name: 'evidence', params: { id: row.id } }">
            <span class="connection-name"><strong>{{ row.device }}</strong><small>{{ row.id }}</small></span>
            <span class="connection-method"><span>{{ segmentLabels[row.segment] }}</span><small>{{ row.keyEstablishment }}</small></span>
            <span><span class="badge" :class="row.status">{{ statusLabels[row.status] }}</span><small v-if="row.fallbackKind === 'suspected'" class="downgrade-label">Synthetic suspicion</small></span>
            <time :datetime="row.observedAt">{{ utc(row.observedAt) }}</time>
            <AppIcon name="arrow" />
          </RouterLink>
        </li>
      </ul>
      <div v-else class="inventory-empty">
        <h2>{{ summary.total ? 'No matching connections' : 'No segments in this snapshot' }}</h2>
        <button v-if="summary.total" type="button" class="button" @click="clear">Clear filters</button>
        <RouterLink v-else class="button" :to="{ name: 'snapshot' }">Choose a dataset</RouterLink>
      </div>
    </div>
    <div class="inventory-footer">
      <span aria-live="polite">{{ rows.length }} of {{ summary.total }} segments</span>
      <PageStepper v-if="count > 1" :page="page" :count="count" @change="current = $event" />
    </div>
  </section>
</template>
