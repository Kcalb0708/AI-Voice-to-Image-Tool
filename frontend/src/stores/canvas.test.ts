import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCanvasStore } from '@/stores/canvas'

describe('canvas store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('applies add, modify, delete, and clear commands', () => {
    const canvas = useCanvasStore()

    canvas.applyCommands([
      { action: 'add', id: 'el_1', tag: 'circle', attrs: { cx: 100, cy: 100, r: 20, fill: 'red' } },
      { action: 'modify', id: 'el_1', attrs: { fill: 'green', r: 32 } },
      { action: 'delete', id: 'missing' },
    ])

    expect(canvas.elements).toHaveLength(1)
    expect(canvas.elements[0].attrs.fill).toBe('green')
    expect(canvas.elements[0].attrs.r).toBe(32)

    canvas.applyCommands([{ action: 'clear' }])

    expect(canvas.elements).toHaveLength(0)
  })

  it('reports export requests without changing the canvas', () => {
    const canvas = useCanvasStore()

    const result = canvas.applyCommands([{ action: 'export' }])

    expect(result.exportRequested).toBe(true)
    expect(canvas.elements).toHaveLength(0)
  })

  it('exports an SVG document', () => {
    const canvas = useCanvasStore()
    const click = vi.fn()
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(),
    })
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    })
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    const originalCreateElement = document.createElement.bind(document)
    const links: HTMLAnchorElement[] = []
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      const element = originalCreateElement(tagName)
      if (tagName === 'a') {
        const anchor = element as HTMLAnchorElement
        anchor.click = click
        links.push(anchor)
      }
      return element
    })

    canvas.applyCommands([{ action: 'add', id: 'el_1', tag: 'rect', attrs: { x: 10, y: 10, width: 40, height: 30 } }])
    canvas.exportSvg('test.svg')

    expect(click).toHaveBeenCalledOnce()
    expect(links[0]?.download).toBe('test.svg')
    expect(create).toHaveBeenCalledOnce()
    expect(revoke).toHaveBeenCalledWith('blob:test')
  })
})
