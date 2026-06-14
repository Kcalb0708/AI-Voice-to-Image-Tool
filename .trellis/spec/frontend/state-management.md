# State Management

> How state is managed in this project.

---

## Overview

The frontend uses Pinia for canvas state that must be shared across the voice workflow, canvas rendering, and export controls.

Canvas SVG elements are the client-side source of truth after backend validation. Server responses are not cached as server state; each voice turn is a request/response action that mutates the local canvas store.

---

## Scenario: Voice Drawing Canvas Commands

### 1. Scope / Trigger

- Trigger: the voice drawing MVP consumes backend `InterpretResponse.commands` and applies them to the SVG canvas.
- Applies to: `frontend/src/stores/canvas.ts`, `frontend/src/types.ts`, `frontend/src/utils/sanitize.ts`, and components rendering/exporting SVG.

### 2. Signatures

```typescript
type CommandAction = 'add' | 'modify' | 'delete' | 'clear' | 'export'

interface CanvasElement {
  id: string
  tag: SvgTag
  attrs: Record<string, string | number>
  text?: string | null
}

function applyCommands(commands: DrawingCommand[], reply?: string): {
  exportRequested: boolean
  warnings: string[]
}
```

### 3. Contracts

- `add` requires a safe `id`, supported `tag`, and sanitized attrs.
- `modify` requires an existing safe `id`; attrs are filtered against the target element tag.
- `delete` requires a safe `id`; missing ids are warnings, not crashes.
- `clear` removes all elements.
- `export` returns `exportRequested=true`; the caller triggers download.
- `elementSummary` must match the backend `DrawingElement[]` contract.

### 4. Validation & Error Matrix

- Unknown/unsafe id -> skip command with warning.
- Unsupported SVG tag -> skip command with warning.
- Unsupported or unsafe attribute -> drop attribute before rendering.
- Missing modify/delete target -> keep canvas unchanged and add warning.
- Export without elements -> still creates a valid blank SVG document.

### 5. Good/Base/Bad Cases

- Good: ordered add/modify/delete commands produce a matching element list and render safely.
- Base: duplicate `add` id replaces the existing element so ids remain stable.
- Bad: command includes `style`, event handlers, `javascript:`, `data:`, or `url(...)`; these must not reach rendered SVG.

### 6. Tests Required

- Store tests cover add/modify/delete/clear/export.
- Sanitizer tests cover unsafe tags, event attributes, unsafe color references, text escaping, and SVG document export.
- Build/type-check must pass after command type changes.

### 7. Wrong vs Correct

#### Wrong

```typescript
// Do not trust command attrs directly in v-html.
elements.push(command as CanvasElement)
```

#### Correct

```typescript
const element: CanvasElement = {
  id: command.id,
  tag: command.tag,
  attrs: filterAttrs(command.tag, command.attrs ?? {}),
  text: command.text ?? null,
}
```
