export type SvgTag =
  | 'circle'
  | 'rect'
  | 'ellipse'
  | 'line'
  | 'polyline'
  | 'polygon'
  | 'path'
  | 'text'

export type CommandAction = 'add' | 'modify' | 'delete' | 'clear' | 'export'

export type SvgAttrs = Record<string, string | number>

export interface CanvasElement {
  id: string
  tag: SvgTag
  attrs: SvgAttrs
  text?: string | null
}

export interface DrawingCommand {
  action: CommandAction
  id?: string | null
  tag?: SvgTag | null
  attrs?: SvgAttrs
  text?: string | null
}

export interface InterpretRequest {
  text: string
  elements: CanvasElement[]
}

export interface InterpretResponse {
  commands: DrawingCommand[]
  reply: string
  warnings: string[]
}

export interface AsrResponse {
  text: string
}

export type AppStatus = 'idle' | 'recording' | 'recognizing' | 'thinking' | 'rendered' | 'error'
