<template>
  <button
    class="voice-button"
    :class="{ 'voice-button--active': active }"
    type="button"
    :aria-pressed="active"
    :aria-label="active ? '停止录音' : '开始录音'"
    :title="active ? '停止录音' : '开始录音'"
    @click="$emit('toggle')"
  >
    <Mic v-if="!active" :size="32" />
    <Square v-else :size="32" />
    <span>{{ active ? '停止录音' : '开始录音' }}</span>
  </button>
</template>

<script setup lang="ts">
import { Mic, Square } from '@lucide/vue'

defineProps<{
  active: boolean
}>()

defineEmits<{
  toggle: []
}>()
</script>
