<template>
  <section class="canvas-shell" aria-label="绘图画布">
    <svg class="canvas-board" viewBox="0 0 960 540" role="img" aria-label="当前绘图">
      <rect width="960" height="540" fill="#ffffff" />
      <g v-html="safeMarkup"></g>
    </svg>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useCanvasStore } from '@/stores/canvas'
import { renderElementsToSafeMarkup } from '@/utils/sanitize'

const canvas = useCanvasStore()
const safeMarkup = computed(() => renderElementsToSafeMarkup(canvas.elements))
</script>
