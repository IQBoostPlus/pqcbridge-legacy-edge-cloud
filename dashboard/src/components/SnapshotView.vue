<script setup>
import { clockTime, importFile, resetDemo, state, summary } from '../dashboard.js';
import { utc } from '../display.js';
import AppIcon from './AppIcon.vue';
import PagedText from './PagedText.vue';
</script>

<template>
  <section class="panel focus-card settings-card">
    <div class="panel-heading focus-heading"><div><h2>Data &amp; reporting clock</h2><p>Course prototype using synthetic scenarios</p></div><AppIcon name="database" /></div>
    <div class="settings-controls">
      <label class="field-control"><span>Freshness clock</span>
        <select v-model="state.clock" aria-label="Freshness clock" :disabled="!state.snapshot || state.loading">
          <option value="snapshot">Historical snapshot</option><option value="current">Current time</option>
        </select>
      </label>
      <div class="dataset-actions">
        <label class="button primary upload">Load local JSON<input type="file" accept=".json,application/json" @change="importFile"></label>
        <button class="button" type="button" @click="resetDemo">Reset demo</button>
      </div>
    </div>
    <div v-if="state.error" class="dataset-feedback danger" role="alert"><strong>Snapshot rejected</strong><PagedText :text="state.error" /></div>
    <div v-else-if="state.loading" class="dataset-feedback" role="status"><strong>Reading snapshot…</strong></div>
    <div v-else class="dataset-feedback">
      <strong>{{ state.source }} · {{ summary.total }} segments</strong>
      <span>{{ state.clock === 'snapshot' ? 'Snapshot clock' : 'Current evaluation' }} · <time>{{ utc(clockTime) }}</time></span>
      <span>{{ summary.stale }} stale segments with a 24-hour limit.</span>
      <small>File contents stay in this browser session.</small>
    </div>
    <div class="focus-footer"><RouterLink class="text-link" :to="{ name: 'overview' }">Open overview <AppIcon name="arrow" /></RouterLink></div>
  </section>
</template>
