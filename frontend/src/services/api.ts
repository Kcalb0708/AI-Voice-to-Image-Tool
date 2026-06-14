import type { AsrResponse, CanvasElement, InterpretResponse } from '@/types'

export async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData()
  const extension = blob.type.includes('ogg') ? 'ogg' : 'webm'
  form.append('audio', blob, `speech.${extension}`)

  const response = await fetch('/api/asr', {
    method: 'POST',
    body: form,
  })

  if (!response.ok) {
    throw new Error(await readApiError(response, '语音识别失败，请重试。'))
  }

  const payload = (await response.json()) as AsrResponse
  return payload.text
}

export async function interpretTranscript(text: string, elements: CanvasElement[]): Promise<InterpretResponse> {
  const response = await fetch('/api/interpret', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, elements }),
  })

  if (!response.ok) {
    throw new Error(await readApiError(response, '指令理解失败，请重试。'))
  }

  return (await response.json()) as InterpretResponse
}

async function readApiError(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // 响应体不是 JSON，使用兜底错误提示。
  }
  return fallback
}
