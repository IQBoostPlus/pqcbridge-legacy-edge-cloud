<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import PageStepper from './PageStepper.vue';

const props = defineProps({ text: { type: String, required: true } });
const box = ref(null);
const content = ref(null);
const page = ref(0);
const count = ref(1);
let observer;

function go(next) {
  page.value = Math.max(0, Math.min(next, count.value - 1));
  if (box.value) box.value.scrollLeft = page.value * box.value.clientWidth;
}

function measure() {
  const width = box.value.clientWidth;
  if (!width) return;
  content.value.style.columnWidth = width + 'px';
  count.value = Math.max(1, Math.ceil(content.value.scrollWidth / width));
  go(page.value);
}

onMounted(() => {
  observer = new ResizeObserver(measure);
  observer.observe(box.value);
  measure();
});
onBeforeUnmount(() => observer?.disconnect());
watch(() => props.text, async () => {
  page.value = 0;
  await nextTick();
  if (box.value) measure();
});
</script>

<template>
  <div class="paged-text">
    <div ref="box" class="text-viewport"><p ref="content">{{ text }}</p></div>
    <PageStepper v-if="count > 1" :page="page" :count="count" label="Text page" @change="go" />
  </div>
</template>
