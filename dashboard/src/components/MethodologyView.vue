<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppIcon from './AppIcon.vue';
import PageStepper from './PageStepper.vue';
import PagedText from './PagedText.vue';

const route = useRoute();
const router = useRouter();
const topics = [
  ['coverage', 'Coverage & scope', 'Coverage = PQC connection segments ÷ all in-scope segments, including unknowns. The result is rounded to one decimal. An empty snapshot has no coverage value. The device-to-gateway and gateway-to-cloud links count separately. ML-KEM-768 on the latter only describes that link.'],
  ['exposure', 'HNDL & fallback', 'Harvest-now-decrypt-later (HNDL) describes potential future decryption of traffic collected today. The view shows exposure under stated confidentiality assumptions. Expected fallback is an approved legacy scenario. A suspected downgrade represents an unexpected change requiring investigation. Both classifications come from the synthetic input.'],
  ['status', 'Status & freshness', 'Red takes priority when any synthetic suspected downgrade needs investigation. Otherwise, empty, unknown, stale or future-dated evidence yields Unknown. Remaining expected fallback yields Amber. Green describes current reported segment migration. Historical mode uses the snapshot time. Current time re-evaluates the loaded snapshot. An observation becomes stale after 24 hours.'],
  ['tradeoffs', 'Stakeholder trade-offs', 'Sarah prioritizes reducing exposure and investigating suspicious changes. Michael needs monitoring continuity until certified replacements are expected in 2028. Emma weighs outages, budget and contractual timing. Discuss the pump station exception as a trade-off between continued monitoring and residual exposure. The proposed rules are subject to team and Product Owner review.'],
  ['simulation', 'Simulation boundaries', 'The course snapshot models classical fallback with ECDH-P256. The separate Device/Gateway/Cloud prototype uses a preconfigured symmetric-key device path. This console uses only synthetic snapshots. The default numbers and indicators describe the course scenario.'],
];
const page = computed(() => Math.max(0, topics.findIndex(([id]) => id === route.query.topic)));
function show(next) {
  router.replace({ name: 'methodology', query: { topic: topics[next][0] } });
}
</script>

<template>
  <section class="panel focus-card methodology-card">
    <div class="panel-heading focus-heading"><div class="focus-title"><h2>{{ topics[page][1] }}</h2><p>Indicator definitions and limits</p></div>
      <PageStepper :page="page" :count="topics.length" label="Topic" @change="show" />
    </div>
    <label class="field-control"><span>Topic</span><select :value="page" aria-label="Topic" @change="show(Number($event.target.value))">
      <option v-for="([id, title], index) in topics" :key="id" :value="index">{{ title }}</option>
    </select></label>
    <PagedText :text="topics[page][2]" />
    <div class="focus-footer"><RouterLink class="text-link" :to="{ name: 'overview' }"><AppIcon name="back" />Back to overview</RouterLink></div>
  </section>
</template>
