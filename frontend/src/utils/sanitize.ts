import DOMPurify from 'dompurify'

import type { CanvasElement, SvgAttrs, SvgTag } from '@/types'

export const allowedTags = ['circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text'] as const
const sanitizerTags = ['svg', 'g', ...allowedTags] as const

const commonAttrs = ['id', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'opacity'] as const

const tagAttrs: Record<SvgTag, readonly string[]> = {
  circle: ['cx', 'cy', 'r'],
  rect: ['x', 'y', 'width', 'height', 'rx', 'ry'],
  ellipse: ['cx', 'cy', 'rx', 'ry'],
  line: ['x1', 'y1', 'x2', 'y2'],
  polyline: ['points'],
  polygon: ['points'],
  path: ['d'],
  text: ['x', 'y', 'font-size', 'text-anchor', 'dominant-baseline'],
}

export const allowedAttrs = Array.from(new Set([...commonAttrs, ...Object.values(tagAttrs).flat()]))

const idPattern = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/

export function isSvgTag(value: unknown): value is SvgTag {
  return typeof value === 'string' && allowedTags.includes(value as SvgTag)
}

export function isSafeElementId(value: unknown): value is string {
  return typeof value === 'string' && idPattern.test(value)
}

export function filterAttrs(tag: SvgTag, attrs: SvgAttrs = {}): SvgAttrs {
  const allowed = new Set([...commonAttrs, ...tagAttrs[tag]])
  const output: SvgAttrs = {}

  for (const [key, value] of Object.entries(attrs)) {
    if (!allowed.has(key)) {
      continue
    }
    const stringValue = String(value)
    const lowered = stringValue.toLowerCase()
    if (key.startsWith('on') || lowered.includes('javascript:') || lowered.includes('data:') || lowered.includes('url(')) {
      continue
    }
    output[key] = value
  }

  return output
}

export function sanitizeSvgFragment(fragment: string): string {
  const cleanDocument = DOMPurify.sanitize(`<svg xmlns="http://www.w3.org/2000/svg"><g>${fragment}</g></svg>`, {
    USE_PROFILES: { svg: true, svgFilters: false },
    ALLOWED_TAGS: [...sanitizerTags],
    ALLOWED_ATTR: ['xmlns', ...allowedAttrs],
    FORBID_TAGS: ['script', 'foreignObject', 'iframe', 'audio', 'video', 'image', 'a', 'use'],
    FORBID_ATTR: ['style', 'href', 'xlink:href', 'src', 'onload', 'onclick'],
  })

  const template = document.createElement('template')
  template.innerHTML = cleanDocument
  return template.content.querySelector('g')?.innerHTML ?? ''
}

export function renderElementToString(element: CanvasElement): string {
  const attrs = filterAttrs(element.tag, element.attrs)
  const attrString = Object.entries({ id: element.id, ...attrs })
    .map(([key, value]) => `${key}="${escapeAttribute(value)}"`)
    .join(' ')

  if (element.tag === 'text') {
    return `<text ${attrString}>${escapeText(element.text ?? '')}</text>`
  }

  return `<${element.tag} ${attrString}></${element.tag}>`
}

export function renderElementsToSafeMarkup(elements: CanvasElement[]): string {
  return sanitizeSvgFragment(elements.map(renderElementToString).join(''))
}

export function buildSvgDocument(elements: CanvasElement[]): string {
  const content = renderElementsToSafeMarkup(elements)
  return [
    '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
    '<rect width="960" height="540" fill="white"/>',
    content,
    '</svg>',
  ].join('')
}

function escapeAttribute(value: string | number): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeText(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
