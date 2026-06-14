export type FrequencyBandsListener = (bands: number[]) => void

export class AudioRecorder {
  private analyser: AnalyserNode | null = null
  private chunks: BlobPart[] = []
  private frequencyData: Uint8Array<ArrayBuffer> | null = null
  private meterContext: AudioContext | null = null
  private meterFrame = 0
  private meterSource: MediaStreamAudioSourceNode | null = null
  private onFrequencyBands: FrequencyBandsListener | null = null
  private recorder: MediaRecorder | null = null
  private startedAt = 0
  private stream: MediaStream | null = null

  constructor(onFrequencyBands?: FrequencyBandsListener) {
    this.onFrequencyBands = onFrequencyBands ?? null
  }

  get isRecording(): boolean {
    return this.recorder?.state === 'recording'
  }

  async start(): Promise<void> {
    if (this.isRecording) {
      return
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        autoGainControl: true,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })

    const mimeType = chooseMimeType()
    this.recorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined)
    this.chunks = []
    this.startedAt = performance.now()
    this.startMeter(this.stream)

    this.recorder.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data)
      }
    })

    this.recorder.start()
  }

  async stop(): Promise<Blob> {
    if (!this.recorder || this.recorder.state === 'inactive') {
      throw new Error('录音器未启动。')
    }

    const recorder = this.recorder
    const sourceType = recorder.mimeType || 'audio/webm'
    const durationMs = performance.now() - this.startedAt

    const sourceBlob = await new Promise<Blob>((resolve, reject) => {
      recorder.addEventListener(
        'stop',
        () => {
          const blob = new Blob(this.chunks, { type: sourceType })
          resolve(blob)
        },
        { once: true },
      )
      recorder.addEventListener('error', () => reject(new Error('录音失败，请重试。')), { once: true })
      recorder.stop()
    })

    this.cleanup()

    if (durationMs < 500) {
      throw new Error('录音时间太短，请重新录制。')
    }
    if (sourceBlob.size === 0) {
      throw new Error('没有采集到音频，请重新录制。')
    }

    return transcodeToWav(sourceBlob)
  }

  cancel(): void {
    if (this.recorder?.state === 'recording') {
      this.recorder.stop()
    }
    this.cleanup()
  }

  private cleanup(): void {
    this.stopMeter()
    this.stream?.getTracks().forEach((track) => track.stop())
    this.chunks = []
    this.recorder = null
    this.startedAt = 0
    this.stream = null
  }

  private startMeter(stream: MediaStream): void {
    if (!this.onFrequencyBands) {
      return
    }

    const AudioContextConstructor = getAudioContextConstructor()
    this.meterContext = new AudioContextConstructor()
    this.meterSource = this.meterContext.createMediaStreamSource(stream)
    this.analyser = this.meterContext.createAnalyser()
    this.analyser.fftSize = 256
    this.analyser.smoothingTimeConstant = 0.72
    this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount)
    this.meterSource.connect(this.analyser)
    void this.meterContext.resume()
    this.tickMeter()
  }

  private tickMeter(): void {
    if (!this.analyser || !this.frequencyData || !this.onFrequencyBands) {
      return
    }

    this.analyser.getByteFrequencyData(this.frequencyData)
    this.onFrequencyBands(buildFrequencyBands(this.frequencyData, 12))
    this.meterFrame = window.requestAnimationFrame(() => this.tickMeter())
  }

  private stopMeter(): void {
    if (this.meterFrame) {
      window.cancelAnimationFrame(this.meterFrame)
    }
    this.meterSource?.disconnect()
    this.analyser?.disconnect()
    void this.meterContext?.close().catch(() => undefined)
    this.onFrequencyBands?.(Array.from({ length: 12 }, () => 0))

    this.analyser = null
    this.frequencyData = null
    this.meterContext = null
    this.meterFrame = 0
    this.meterSource = null
  }
}

const WAV_HEADER_BYTES = 44

type AudioContextConstructor = new () => AudioContext

function chooseMimeType(): string {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/ogg']
  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ?? ''
}

export function buildFrequencyBands(data: Uint8Array, bandCount: number): number[] {
  if (bandCount <= 0 || data.length === 0) {
    return []
  }

  return Array.from({ length: bandCount }, (_, bandIndex) => {
    const start = Math.floor((bandIndex * data.length) / bandCount)
    const end = Math.max(start + 1, Math.floor(((bandIndex + 1) * data.length) / bandCount))
    let total = 0

    for (let index = start; index < end; index += 1) {
      total += data[index] ?? 0
    }

    const average = total / (end - start)
    return Math.min(1, Math.sqrt(average / 255))
  })
}

async function transcodeToWav(blob: Blob): Promise<Blob> {
  const AudioContextConstructor = getAudioContextConstructor()
  const audioContext = new AudioContextConstructor()

  try {
    const audioBuffer = await audioContext.decodeAudioData(await blob.arrayBuffer())
    const samples = audioBuffer.getChannelData(0)
    if (samples.length === 0) {
      throw new Error('没有采集到音频，请重新录制。')
    }
    return encodeWav([new Float32Array(samples)], audioBuffer.sampleRate)
  } catch (error) {
    if (error instanceof Error && error.message) {
      throw error
    }
    throw new Error('无法处理录音，请重新录制。')
  } finally {
    await audioContext.close().catch(() => undefined)
  }
}

function getAudioContextConstructor(): AudioContextConstructor {
  const candidate =
    window.AudioContext ?? (window as typeof window & { webkitAudioContext?: AudioContextConstructor }).webkitAudioContext

  if (!candidate) {
    throw new Error('当前浏览器不支持音频录制。')
  }

  return candidate
}

export function encodeWav(chunks: Float32Array[], sampleRate: number): Blob {
  const samples = flattenSamples(chunks)
  const buffer = new ArrayBuffer(WAV_HEADER_BYTES + samples.length * 2)
  const view = new DataView(buffer)

  writeAscii(view, 0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeAscii(view, 8, 'WAVE')
  writeAscii(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeAscii(view, 36, 'data')
  view.setUint32(40, samples.length * 2, true)

  let offset = WAV_HEADER_BYTES
  for (const sample of samples) {
    const clamped = Math.max(-1, Math.min(1, sample))
    const pcm = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff
    view.setInt16(offset, pcm, true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

function flattenSamples(chunks: Float32Array[]): Float32Array {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0)
  const samples = new Float32Array(length)
  let offset = 0

  for (const chunk of chunks) {
    samples.set(chunk, offset)
    offset += chunk.length
  }

  return samples
}

function writeAscii(view: DataView, offset: number, value: string): void {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index))
  }
}
