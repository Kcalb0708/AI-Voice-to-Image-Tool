import { defineStore } from 'pinia'

import type { CanvasElement, DrawingCommand } from '@/types'
import { buildSvgDocument, filterAttrs, isSafeElementId, isSvgTag } from '@/utils/sanitize'

interface ApplyResult {
  exportRequested: boolean
  warnings: string[]
}

interface CanvasState {
  elements: CanvasElement[]
  lastReply: string
}

export const useCanvasStore = defineStore('canvas', {
  state: (): CanvasState => ({
    elements: [],
    lastReply: '',
  }),
  getters: {
    elementSummary: (state): CanvasElement[] =>
      state.elements.map((element) => ({
        id: element.id,
        tag: element.tag,
        attrs: element.attrs,
        text: element.text ?? null,
      })),
    svgDocument: (state): string => buildSvgDocument(state.elements),
  },
  actions: {
    applyCommands(commands: DrawingCommand[], reply = ''): ApplyResult {
      const result: ApplyResult = { exportRequested: false, warnings: [] }

      for (const command of commands) {
        switch (command.action) {
          case 'add':
            this.addElement(command, result)
            break
          case 'modify':
            this.modifyElement(command, result)
            break
          case 'delete':
            this.deleteElement(command, result)
            break
          case 'clear':
            this.elements = []
            break
          case 'export':
            result.exportRequested = true
            break
          default:
            result.warnings.push('已跳过未知指令。')
        }
      }

      this.lastReply = reply
      return result
    },
    exportSvg(filename = '语音绘图.svg'): void {
      const blob = new Blob([this.svgDocument], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    },
    addElement(command: DrawingCommand, result: ApplyResult): void {
      if (!isSafeElementId(command.id) || !isSvgTag(command.tag)) {
        result.warnings.push('新增图形指令无效，已跳过。')
        return
      }

      const element: CanvasElement = {
        id: command.id,
        tag: command.tag,
        attrs: filterAttrs(command.tag, command.attrs ?? {}),
        text: command.text ?? null,
      }
      const existingIndex = this.elements.findIndex((item) => item.id === element.id)
      if (existingIndex >= 0) {
        this.elements.splice(existingIndex, 1, element)
        return
      }
      this.elements.push(element)
    },
    modifyElement(command: DrawingCommand, result: ApplyResult): void {
      if (!isSafeElementId(command.id)) {
        result.warnings.push('修改图形指令无效，已跳过。')
        return
      }

      const target = this.elements.find((element) => element.id === command.id)
      if (!target) {
        result.warnings.push(`未找到图形 ${command.id}。`)
        return
      }

      target.attrs = {
        ...target.attrs,
        ...filterAttrs(target.tag, command.attrs ?? {}),
      }
      if (command.text !== undefined) {
        target.text = command.text
      }
    },
    deleteElement(command: DrawingCommand, result: ApplyResult): void {
      if (!isSafeElementId(command.id)) {
        result.warnings.push('删除图形指令无效，已跳过。')
        return
      }
      const nextElements = this.elements.filter((element) => element.id !== command.id)
      if (nextElements.length === this.elements.length) {
        result.warnings.push(`未找到图形 ${command.id}。`)
      }
      this.elements = nextElements
    },
  },
})
