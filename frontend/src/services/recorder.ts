export class AudioRecorder {
  private recorder: MediaRecorder | null = null
  private stream: MediaStream | null = null
  private chunks: BlobPart[] = []

  get isRecording(): boolean {
    return this.recorder?.state === 'recording'
  }

  async start(): Promise<void> {
    if (this.isRecording) {
      return
    }

    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = chooseMimeType()
    this.recorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined)
    this.chunks = []

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
    const mimeType = recorder.mimeType || 'audio/webm'

    return new Promise((resolve, reject) => {
      recorder.addEventListener(
        'stop',
        () => {
          const blob = new Blob(this.chunks, { type: mimeType })
          this.cleanup()
          if (blob.size === 0) {
            reject(new Error('没有采集到音频，请重新录制。'))
            return
          }
          resolve(blob)
        },
        { once: true },
      )
      recorder.stop()
    })
  }

  cancel(): void {
    if (this.recorder?.state === 'recording') {
      this.recorder.stop()
    }
    this.cleanup()
  }

  private cleanup(): void {
    this.stream?.getTracks().forEach((track) => track.stop())
    this.stream = null
    this.recorder = null
    this.chunks = []
  }
}

function chooseMimeType(): string {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg']
  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ?? ''
}
