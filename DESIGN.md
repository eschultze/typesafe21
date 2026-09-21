# DESIGN.md — TypeSafe21 Design System

> Locked system. Subsequent Hallmark runs defer to this file.

## Genre & Theme

- **Genre**: Playful (consumer, fun, casual)
- **Theme**: Midnight (Hallmark catalog)
- **Voice**: Warm, direct, technical but approachable. Not childish, not corporate.

## Palette (OKLCH)

### Surfaces

| Token | Value | Usage |
|-------|-------|-------|
| `--color-paper` | `oklch(15% 0.022 250)` | Page background |
| `--color-paper-2` | `oklch(20% 0.024 250)` | Elevated cards |
| `--color-paper-3` | `oklch(25% 0.026 250)` | Hover states |

### Text

| Token | Value | Usage |
|-------|-------|-------|
| `--color-ink` | `oklch(95% 0.008 230)` | Headlines, primary text |
| `--color-ink-2` | `oklch(86% 0.010 230)` | Body text |
| `--color-muted` | `oklch(60% 0.018 240)` | Captions, labels |

### Accent

| Token | Value | Usage |
|-------|-------|-------|
| `--color-accent` | `oklch(72% 0.16 220)` | Primary accent (electric blue) |
| `--color-profit` | `oklch(72% 0.12 150)` | Positive balance |
| `--color-loss` | `oklch(0.65 0.20 25)` | Negative balance |

### Borders

| Token | Value | Usage |
|-------|-------|-------|
| `--color-rule` | `oklch(33% 0.024 245)` | Dividers, borders |

## Typography

- **Display**: Geist Sans, weight 300 (light), tracking -0.03em
- **Body**: Geist Sans, weight 400
- **Label**: Geist Mono, weight 400, tracking 0.16em (uppercase)
- **Scale**: CSS custom properties (`--text-display`, `--text-display-s`, etc.)
- **Tabular nums**: `font-variant-numeric: tabular-nums` on all data displays

## Spacing

4pt base scale:

| Token | Value |
|-------|-------|
| `--space-xs` | 0.5rem |
| `--space-sm` | 0.75rem |
| `--space-md` | 1rem |
| `--space-lg` | 1.5rem |
| `--space-xl` | 2.5rem |
| `--space-2xl` | 4rem |
| `--space-3xl` | 6.5rem |

## Motion

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entering elements |
| `--ease-in` | `cubic-bezier(0.7, 0, 0.84, 0)` | Exiting elements |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Toggles |
| `--dur-micro` | 120ms | Button press, value pop |
| `--dur-short` | 220ms | Hover states, card transitions |
| `--dur-long` | 420ms | Page reveals, card dealing |

**Reduced motion**: All animations collapse to `0.01ms` duration via `@media (prefers-reduced-motion: reduce)`.

## Component Shape

| Token | Value |
|-------|-------|
| `--radius-card` | 10px |
| `--radius-pill` | 999px |
| `--radius-input` | 8px |
| `--rule-card` | 1px |
| `--shadow-card` | none |

## Z-Index Scale

| Level | Token | Value |
|-------|-------|-------|
| Base | `--z-base` | 1 |
| Raised | `--z-raised` | 10 |
| Dropdown | `--z-dropdown` | 100 |
| Sticky | `--z-sticky` | 200 |
| Modal | `--z-modal` | 400 |
| Toast | `--z-toast` | 500 |
| Tooltip | `--z-tooltip` | 600 |

## Layout

- **Max width**: 76rem
- **Page gutter**: `clamp(1.25rem, 4vw, 3rem)`
- **Measure**: 60ch (prose)
- **Overflow**: `overflow-x: clip` on html and body

## Exports

### CSS (globals.css)

All tokens are defined as CSS custom properties in `:root` in `frontend/src/app/globals.css`.

### Tailwind v4

Tokens are exposed via `@theme inline` block in globals.css. Use `bg-card`, `text-muted-foreground`, `border-border`, etc.

### shadcn/ui

Existing shadcn component variants (Button, Badge, etc.) consume these tokens via CSS custom properties. No changes needed to component APIs.
