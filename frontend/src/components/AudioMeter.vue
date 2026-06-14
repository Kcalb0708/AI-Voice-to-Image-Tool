<template>
  <section class="audio-meter" aria-label="麦克风输入">
    <div class="audio-meter__header">
      <span>麦克风输入</span>
      <strong>{{ active ? '录音中' : '待机' }}</strong>
    </div>
    <div class="audio-meter__bars" role="meter" aria-label="当前麦克风输入强度" :aria-valuenow="meterValue" aria-valuemin="0" aria-valuemax="100">
      <span
        v-for="(band, index) in normalizedBands"
        :key="index"
        class="audio-meter__bar"
        :style="{ transform: `scaleY(${band})` }"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  active: boolean
  bands: number[]
}>()

const normalizedBands = computed(() => {
  const values = props.bands.length > 0 ? props.bands : Array.from({ length: 12 }, () => 0)
  return values.map((value) => Math.max(0.04, Math.min(1, value)))
})

const meterValue = computed(() => {
  const peak = Math.max(0, ...props.bands)
  return Math.round(Math.min(1, peak) * 100)
})
</script>
