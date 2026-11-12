<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { destinations } from './router.js';
import { state, summary } from './dashboard.js';
import AppIcon from './components/AppIcon.vue';

const route = useRoute();
const main = ref(null);
const mainNav = destinations.slice(0, 6);
const tools = destinations.slice(6);
const canRender = computed(() => summary.value || ['customer', 'snapshot', 'methodology', 'indicators'].includes(route.name));
let timer;

watch(() => state.clock, () => { state.time = Date.now(); });
watch(() => route.meta.title, title => {
  document.title = (title ?? 'Migration overview') + ' | PQC Bridge';
}, { immediate: true });
onMounted(() => {
  timer = window.setInterval(() => {
    if (state.clock === 'current') state.time = Date.now();
  }, 60_000);
});
onUnmounted(() => window.clearInterval(timer));
</script>

<template>
  <div class="console">
    <a class="skip-link" href="#main" @click.prevent="main.focus()">Skip to content</a>
    <header class="brand-bar">
      <RouterLink :to="{ name: 'customer' }" class="brand">
        <span class="brand-mark"><AppIcon name="logo" /></span>
        <span>PQC <strong>Bridge</strong><small>Migration console</small></span>
      </RouterLink>
      <nav class="mobile-tools" aria-label="Supporting pages">
        <RouterLink v-for="item in tools" :key="item.name" :to="{ name: item.name }" :aria-label="item.label" class="icon-button"><AppIcon :name="item.icon" /></RouterLink>
      </nav>
    </header>

    <aside class="rail">
      <nav class="main-nav" aria-label="Main navigation">
        <RouterLink v-for="item in mainNav" :key="item.name" :to="{ name: item.name }"
          :class="{ 'related-active': item.name === 'connections' && route.name === 'evidence' }">
          <AppIcon :name="item.icon" /><span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <nav class="desktop-tools" aria-label="Supporting pages">
        <RouterLink v-for="item in tools" :key="item.name" :to="{ name: item.name }"><AppIcon :name="item.icon" /><span>{{ item.label }}</span></RouterLink>
      </nav>
      <div class="rail-footer"><span class="signal-dot"></span><span>Synthetic exercise</span><strong>Sprint 2</strong></div>
    </aside>

    <main id="main" ref="main" tabindex="-1" class="workspace">
      <div class="workspace-heading">
        <div>
          <h1>{{ route.meta.title ?? 'Migration overview' }}</h1>
          <p v-if="state.snapshot" :title="state.snapshot.title">{{ state.snapshot.title }}</p>
          <p v-else>Dataset unavailable</p>
        </div>
        <RouterLink :to="{ name: 'snapshot' }" class="source-pill"><span class="signal-dot"></span>Synthetic data</RouterLink>
      </div>
      <div class="workspace-body">
        <RouterView v-if="canRender" v-slot="{ Component }"><component :is="Component" :key="route.name" /></RouterView>
        <section v-else class="panel centered">
          <AppIcon name="warning" /><h2>Snapshot unavailable</h2>
          <p>Load a valid synthetic snapshot to restore the workspace.</p>
          <RouterLink class="button primary" :to="{ name: 'snapshot' }">Open dataset settings</RouterLink>
        </section>
      </div>
    </main>
  </div>
</template>
