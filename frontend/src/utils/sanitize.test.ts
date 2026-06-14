import { describe, expect, it } from 'vitest'

import { buildSvgDocument, filterAttrs, renderElementsToSafeMarkup, sanitizeSvgFragment } from '@/utils/sanitize'

describe('SVG sanitizer', () => {
  it('removes unsafe tags and event attributes', () => {
    const sanitized = sanitizeSvgFragment('<circle cx="10" cy="10" r="5" onload="alert(1)" /><script>alert(1)</script>')

    expect(sanitized).toContain('<circle')
    expect(sanitized).not.toContain('onload')
    expect(sanitized).not.toContain('script')
  })

  it('filters unsupported attributes before render', () => {
    const attrs = filterAttrs('circle', {
      cx: 10,
      cy: 10,
      r: 5,
      style: 'color:red',
      fill: 'url(http://example.test/a.svg)',
    })

    expect(attrs).toEqual({ cx: 10, cy: 10, r: 5 })
  })

  it('renders safe element markup', () => {
    const markup = renderElementsToSafeMarkup([
      { id: 'el_1', tag: 'text', attrs: { x: 10, y: 20, 'font-size': 18 }, text: '<hello>' },
    ])

    expect(markup).toContain('el_1')
    expect(markup).toContain('&lt;hello&gt;')
  })

  it('builds an exportable SVG document', () => {
    const svg = buildSvgDocument([{ id: 'el_1', tag: 'circle', attrs: { cx: 10, cy: 10, r: 5 }, text: null }])

    expect(svg).toContain('<svg')
    expect(svg).toContain('<circle')
  })
})
