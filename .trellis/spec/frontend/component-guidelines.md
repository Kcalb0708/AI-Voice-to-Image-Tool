# Component Guidelines

> How components are built in this project.

---

## Overview

<!--
Document your project's component conventions here.

Questions to answer:
- What component patterns do you use?
- How are props defined?
- How do you handle composition?
- What accessibility standards apply?
-->

User-facing UI copy in this project must be Simplified Chinese. This includes visible text, placeholders, button text, `aria-label`, `title`, status labels, warning messages, and error fallback messages.

---

## Component Structure

<!-- Standard structure of a component file -->

(To be filled by the team)

---

## Props Conventions

<!-- How props should be defined and typed -->

(To be filled by the team)

---

## Styling Patterns

<!-- How styles are applied (CSS modules, styled-components, Tailwind, etc.) -->

(To be filled by the team)

---

## Accessibility

<!-- A11y requirements and patterns -->

Accessible labels must be localized with the visible UI. Do not leave English-only `aria-label` or `title` text when the corresponding visible control is Chinese.

### Convention: Simplified Chinese UI Copy

**What**: All user-facing frontend text is Simplified Chinese.

**Why**: The voice drawing workflow is intended for Chinese-speaking users. Mixed English/Chinese UI makes status, failure recovery, and voice-command feedback harder to scan.

**Applies to**:

- Page title and visible headings
- Button labels, icon button `aria-label`, and `title`
- Status labels such as recording, recognizing, thinking, completed, and error
- Empty-state placeholders
- Frontend-generated warnings and fallback errors
- Download file names when they are user-visible

**Example**:

```vue
<button aria-label="导出 SVG" title="导出 SVG">
  <Download />
</button>
```

**Wrong**:

```vue
<button aria-label="Export SVG" title="Export SVG">
  <Download />
</button>
```

---

## Common Mistakes

<!-- Component-related mistakes your team has made -->

Leaving English text in accessibility attributes after translating visible text. Screen-reader and tooltip text are part of the UI contract.
