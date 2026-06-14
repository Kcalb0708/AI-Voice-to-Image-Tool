<template>
  <aside class="panel" aria-label="会话状态">
    <div class="status-row">
      <span class="status-dot" :class="`status-dot--${status}`"></span>
      <span class="status-label">{{ statusLabel }}</span>
    </div>

    <div class="transcript">
      <span class="panel-label">识别文本</span>
      <p>{{ transcript || '等待识别结果' }}</p>
    </div>

    <div class="transcript">
      <span class="panel-label">系统回复</span>
      <p>{{ reply || '等待系统回复' }}</p>
    </div>

    <div v-if="error || warnings.length" class="messages" role="status">
      <p v-if="error" class="message message--error">{{ error }}</p>
      <p v-for="warning in warnings" :key="warning" class="message message--warning">{{ warning }}</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { AppStatus } from '@/types'

const props = defineProps<{
  status: AppStatus
  transcript: string
  reply: string
  error: string
  warnings: string[]
}>()

const statusLabel = computed(() => {
  const labels: Record<AppStatus, string> = {
    idle: '准备就绪',
    recording: '录音中',
    recognizing: '识别中',
    thinking: '理解中',
    rendered: '已完成',
    error: '出错',
  }
  return labels[props.status]
})
</script>
