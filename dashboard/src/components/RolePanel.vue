<script setup>
import { computed, ref } from 'vue';
import { customerReport, state, summary } from '../dashboard.js';
import { segmentLabels } from '../display.js';
import AppIcon from './AppIcon.vue';
import PageStepper from './PageStepper.vue';
import PagedText from './PagedText.vue';
import CustomerReport from './CustomerReport.vue';

const props = defineProps({ role: { type: String, required: true } });
const active = ref(0);
const field = ref(0);
const executive = computed(() => props.role === 'executive');
const security = computed(() => props.role === 'security');
const items = computed(() => {
  if (executive.value) return summary.value.risks;
  const remaining = state.snapshot.connections.filter(row => row.status !== 'pqc');
  if (security.value) {
    remaining.sort((a, b) => Number(b.fallbackKind === 'suspected') - Number(a.fallbackKind === 'suspected'));
  }
  return remaining;
});
const page = computed(() => Math.min(active.value, Math.max(0, items.value.length - 1)));
const item = computed(() => items.value[page.value]);
const copy = {
  security: ['Sarah', 'Security officer', 'Assess exposure and prioritize investigations.'],
  migration: ['Michael', 'Migration manager', 'Prioritize blockers and time-limited exceptions.'],
  executive: ['Emma', 'Chief information officer', 'Review business impact and decide what needs action.'],
};
const fields = computed(() => {
  if (!item.value) return [];
  if (executive.value) return [['Business impact', item.value.detail], ['Next decision', item.value.action], ['Status rationale', summary.value.overall.reason]];
  if (security.value) return [['Reason', item.value.reason], ['Confidentiality', item.value.confidentiality], ['Impact', item.value.impact], ['Next action', item.value.action]];
  return [['Blocker', item.value.blocker], ['Impact', item.value.impact], ['Next action', item.value.action]];
});

function show(next) {
  active.value = next;
  field.value = 0;
}

function protectionLabel(row) {
  if (row.fallbackKind === 'suspected') return 'Suspected downgrade · synthetic';
  if (row.status === 'unknown') return 'Protection unknown';
  return 'Expected legacy fallback';
}
</script>

<template>
  <CustomerReport v-if="customerReport.available" :role="role" />
  <div v-else class="role-layout">
    <div class="role-brief">
      <div class="avatar" aria-hidden="true">{{ copy[role][0][0] }}</div>
      <div><strong>{{ copy[role][0] }}</strong><span>{{ copy[role][1] }}</span><p>{{ copy[role][2] }}</p></div>
      <span v-if="executive" class="badge" :class="summary.overall.level">{{ summary.overall.level }}</span>
      <span v-else-if="security" class="brief-number">{{ summary.suspected }} to investigate</span>
      <span v-else class="brief-number">{{ summary.pqc }} / {{ summary.total }} migrated</span>
    </div>
    <section v-if="item" class="panel focus-card">
      <div class="panel-heading focus-heading">
        <div class="focus-title">
          <h2 :title="executive ? item.title : item.device">{{ executive ? item.title : item.device }}</h2>
          <p v-if="!executive" :title="item.id">{{ item.id }} · {{ segmentLabels[item.segment] }}</p>
          <p v-else>{{ summary.overall.label }}</p>
        </div>
        <PageStepper v-if="items.length > 1" :page="page" :count="items.length" :label="executive ? 'Risk' : 'Segment'" @change="show" />
      </div>
      <div class="focus-toolbar">
        <span v-if="!executive" class="badge" :class="item.fallbackKind === 'suspected' ? 'red' : item.status">{{ protectionLabel(item) }}</span>
        <span v-else class="muted">Executive priorities</span>
        <label class="field-control"><span>Show</span>
          <select v-model.number="field" aria-label="View field"><option v-for="([label], index) in fields" :key="label" :value="index">{{ label }}</option></select>
        </label>
      </div>
      <div class="role-detail">
        <div class="role-reading">
          <h3>{{ fields[field]?.[0] }}</h3>
          <PagedText :text="fields[field]?.[1] ?? ''" />
        </div>
        <nav class="case-notes" aria-label="Case notes">
          <h3>Case notes</h3>
          <button v-for="([label, value], index) in fields" :key="label" type="button"
            :aria-pressed="field === index" @click="field = index">
            <strong>{{ label }}</strong><span>{{ value }}</span>
          </button>
        </nav>
      </div>
      <div class="focus-footer">
        <RouterLink v-if="!executive" class="text-link" :to="{ name: 'evidence', params: { id: item.id }, query: { from: role } }">Open connection evidence <AppIcon name="arrow" /></RouterLink>
        <RouterLink v-else class="text-link" :to="{ name: 'methodology', query: { topic: 'status' } }">How status is determined <AppIcon name="arrow" /></RouterLink>
      </div>
    </section>
    <section v-else class="panel centered">
      <h2>{{ summary.total ? 'No items flagged' : 'No connection segments' }}</h2>
      <p>{{ executive ? summary.overall.reason : 'Review the overall status and freshness before acting.' }}</p>
      <RouterLink :to="{ name: 'overview' }" class="button">Open overview</RouterLink>
    </section>
  </div>
</template>
