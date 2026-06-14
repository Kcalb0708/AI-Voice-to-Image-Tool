import { describe, expect, it } from 'vitest'

import { buildFrequencyBands, encodeWav } from './recorder'

describe('encodeWav', () => {
  it('creates a mono 16-bit wav blob', async () => {
    const blob = encodeWav([new Float32Array([-1, 0, 1])], 16000)
    const view = new DataView(await blob.arrayBuffer())

    expect(blob.type).toBe('audio/wav')
    expect(readAscii(view, 0, 4)).toBe('RIFF')
    expect(readAscii(view, 8, 4)).toBe('WAVE')
    expect(readAscii(view, 12, 4)).toBe('fmt ')
    expect(view.getUint16(20, true)).toBe(1)
    expect(view.getUint16(22, true)).toBe(1)
    expect(view.getUint32(24, true)).toBe(16000)
    expect(view.getUint16(34, true)).toBe(16)
    expect(readAscii(view, 36, 4)).toBe('data')
    expect(view.getUint32(40, true)).toBe(6)
  })
})

describe('buildFrequencyBands', () => {
  it('returns normalized frequency bands', () => {
    const bands = buildFrequencyBands(new Uint8Array([0, 64, 128, 255]), 2)

    expect(bands).toHaveLength(2)
    expect(bands[0]).toBeGreaterThan(0)
    expect(bands[0]).toBeLessThan(1)
    expect(bands[1]).toBeGreaterThan(bands[0])
    expect(bands[1]).toBeLessThanOrEqual(1)
  })

  it('handles empty inputs', () => {
    expect(buildFrequencyBands(new Uint8Array([]), 12)).toEqual([])
    expect(buildFrequencyBands(new Uint8Array([1, 2, 3]), 0)).toEqual([])
  })
})

function readAscii(view: DataView, offset: number, length: number): string {
  return String.fromCharCode(...new Uint8Array(view.buffer, offset, length))
}
