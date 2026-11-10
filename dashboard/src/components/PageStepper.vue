<script setup>
import AppIcon from './AppIcon.vue';
defineProps({
  page: { type: Number, required: true },
  count: { type: Number, required: true },
  label: { type: String, default: 'Page' },
});
defineEmits(['change']);
</script>

<template>
  <div class="stepper" :aria-label="label">
    <button type="button" class="icon-button" :aria-label="'Previous ' + label.toLowerCase()" :disabled="page <= 0" @click="$emit('change', page - 1)"><AppIcon name="back" /></button>
    <span role="status">{{ page + 1 }} / {{ count }}</span>
    <button type="button" class="icon-button" :aria-label="'Next ' + label.toLowerCase()" :disabled="page + 1 >= count" @click="$emit('change', page + 1)"><AppIcon name="arrow" /></button>
  </div>
</template>
