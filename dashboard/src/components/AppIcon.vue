<script setup>
defineProps({ name: { type: String, required: true } });
const icons = {
  logo: 'M3 7h5l4 5h4l5-5M3 17h5l4-5m4 0 5 5M3 5v4m0 6v4M21 5v4m0 6v4',
  overview: 'M3 3h8v8H3zM15 3h6v5h-6zM3 15h8v6H3zM15 12h6v9h-6z',
  shield: 'M12 22s7-3 7-9V6l-7-3-7 3v7c0 6 7 9 7 9Zm-3-10 2 2 4-4',
  trend: 'M3 20h18M4 15l5-5 4 3 7-8m-5 0h5v5',
  brief: 'M3 8h18v12H3zM8 8V5h8v3M3 13h18m-11 0v2h4v-2',
  links: 'M10 7l2-2a4 4 0 0 1 6 6l-2 2m-2 4-2 2a4 4 0 0 1-6-6l2-2m0 5 8-8',
  database: 'M4 6c0-2 16-2 16 0s-16 2-16 0Zm0 0v12c0 3 16 3 16 0V6M4 12c0 3 16 3 16 0',
  book: 'M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Zm0 0v15',
  arrow: 'M5 12h14m-5-5 5 5-5 5',
  back: 'M19 12H5m5-5-5 5 5 5',
  warning: 'M12 3 2 20h20L12 3Zm0 6v5m0 3v.1',
};
</script>

<template>
  <svg :data-icon="name" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="icons[name]" /></svg>
</template>
