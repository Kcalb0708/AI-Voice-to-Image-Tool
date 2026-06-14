<template>
  <main class="app-shell">
    <section class="workspace">
      <header class="topbar">
        <div>
          <h1>语音绘图</h1>
          <p>{{ canvas.elements.length }} 个元素</p>
        </div>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="导出 SVG" title="导出 SVG" @click="canvas.exportSvg()">
            <Download :size="20" />
          </button>
          <button class="icon-button" type="button" aria-label="清空画布" title="清空画布" @click="canvas.applyCommands([{ action: 'clear' }])">
            <Trash2 :size="20" />
          </button>
        </div>
      </header>

      <CanvasBoard />
    </section>

    <section class="control-rail">
      <VoiceButton :active="status === 'recording'" @toggle="toggleRecording" />
      <TranscriptPanel
        :status="status"
        :transcript="transcript"
        :reply="canvas.lastReply"
        :error="error"
        :warnings="warnings"
      />
    </section>
  </main>
</template>

<script setup lang="ts">
import { Download, Trash2 } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'

import CanvasBoard from '@/components/CanvasBoard.vue'
import TranscriptPanel from '@/components/TranscriptPanel.vue'
import VoiceButton from '@/components/VoiceButton.vue'
import { transcribeAudio, interpretTranscript } from '@/services/api'
import { AudioRecorder } from '@/services/recorder'
import { useCanvasStore } from '@/stores/canvas'
import type { AppStatus } from '@/types'

const canvas = useCanvasStore()
const recorder = new AudioRecorder()

const status = ref<AppStatus>('idle')
const transcript = ref('')
const error = ref('')
const warnings = ref<string[]>([])

async function toggleRecording(): Promise<void> {
  if (status.value === 'recording') {
    await stopRecording()
    return
  }
  await startRecording()
}

async function startRecording(): Promise<void> {
  try {
    error.value = ''
    warnings.value = []
    await recorder.start()
    status.value = 'recording'
  } catch (err) {
    status.value = 'error'
    error.value = normalizeError(err, '需要授权麦克风后才能录音。')
  }
}

async function stopRecording(): Promise<void> {
  try {
    status.value = 'recognizing'
    const audio = await recorder.stop()
    const text = await transcribeAudio(audio)
    transcript.value = text

    status.value = 'thinking'
    const interpreted = await interpretTranscript(text, canvas.elementSummary)
    const result = canvas.applyCommands(interpreted.commands, interpreted.reply)
    warnings.value = [...interpreted.warnings, ...result.warnings]
    status.value = 'rendered'

    if (result.exportRequested) {
      canvas.exportSvg()
    }
  } catch (err) {
    status.value = 'error'
    error.value = normalizeError(err, '这条语音指令未能完成，请重试。')
  }
}

function onKeyDown(event: KeyboardEvent): void {
  if (event.code !== 'Space' || event.repeat) {
    return
  }
  const target = event.target as HTMLElement | null
  if (target?.matches('input, textarea, button, [contenteditable="true"]')) {
    return
  }
  event.preventDefault()
  void toggleRecording()
}

function normalizeError(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  recorder.cancel()
})
</script>
