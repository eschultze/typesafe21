# PLAN: TypeSafe21 Web UI Redesign (Hallmark)

## Design System

**Hallmark · v1.1.0**

- **Genre** · Playful (consumer, fun, casual)
- **Theme** · Midnight (deep cool blue paper `oklch(15% 0.022 250)` · electric blue accent `oklch(72% 0.16 220)` · Geist display light 300)
- **Macrostructure** · Marquee Hero (landing page)
- **Nav** · N7 Brutal Slab (heavy uppercase wordmark + 2px border-bottom)
- **Footer** · Ft5 Statement (one large closing sentence + minimal links)
- **Enrichment** · Tier D (Three.js — kept)
- **Motion** · 3 primitives max — card-deal entrance, hover-lift, value-pop

## Key Design Decisions

| Axis | Current | Hallmark Redesign |
|------|---------|-------------------|
| Paper | `oklch(0% 0 0)` (pure black) | `oklch(15% 0.022 250)` (cool blue-tinted dark) |
| Accent | Hardcoded `green-500/600/700` | `oklch(72% 0.16 220)` tokenized as `--color-accent` |
| Ink | `#ffffff` (pure white) | `oklch(95% 0.008 230)` (tinted near-white) |
| Neutrals | Zero chroma grayscale | Tinted toward hue 250 (cool blue) |
| Landing | Centred splash, min-h-screen | Marquee Hero — left-aligned statement + Three.js right |
| Players | 3-column equal grid | Varied widths (`1.2fr 1fr 0.8fr`) |
| Buttons | Hover-only states | Full 8-state |
| Motion | Arbitrary durations | Tokenized: 120ms / 220ms / 420ms |
| Reduced motion | None | `prefers-reduced-motion` on every animation |

## Open Questions (Resolved)

1. **Hero text**: "Typesafe 21" as title, "Three players. One shoe. Zero mercy." as subtitle
2. **Nav links**: Play + History (no GitHub)
3. **Footer tagline**: "The AI always wins. Sometimes."
4. **Player order**: AI first (left) — it's the star

## Execution Phases

### Phase 1: Design Token Foundation
- `frontend/src/app/globals.css` — Replace shadcn grayscale with Midnight tokens, add game semantic tokens, motion tokens, spacing scale, z-index scale
- `frontend/src/app/layout.tsx` — Add `data-theme="midnight"` to `<html>`

### Phase 2: Landing Page Redesign
- `frontend/src/app/page.tsx` — Full rewrite: N7 nav + Marquee Hero + How It Works + AI Brain + Ft5 footer

### Phase 3: Game Page Layout
- `frontend/src/app/game/page.tsx` — Asymmetric layout, varied column widths, themed dividers

### Phase 4: Component Token Migration
- All game components: Replace hardcoded green/red Tailwind values with `var(--color-*)` tokens

### Phase 5: Button 8-State Discipline
- `GameControls.tsx` + landing CTA: All 8 states (default/hover/focus/active/disabled/loading/error/success)

### Phase 6: Motion + Reduced Motion
- PlayingCard, PlayerHand, DealerHand, Scoreboard: Tokenized durations, `prefers-reduced-motion` fallbacks

### Phase 7: Typography Refinements
- Tabular nums on all data displays, weight contrast (300 display vs 400 body)

### Phase 8: Design Documentation
- `DESIGN.md` — Lock the system into a portable file

## Files Changed

| File | Change | Phase |
|------|--------|-------|
| `frontend/src/app/globals.css` | Major edit (tokens) | 1 |
| `frontend/src/app/layout.tsx` | Minor edit (data-theme) | 1 |
| `frontend/src/app/page.tsx` | Full rewrite (landing) | 2 |
| `frontend/src/app/game/page.tsx` | Layout restructure | 3 |
| `frontend/src/components/game/PlayingCard.tsx` | Token + motion | 4,6 |
| `frontend/src/components/game/PlayerHand.tsx` | Token + motion | 4,6 |
| `frontend/src/components/game/DealerHand.tsx` | Token + motion | 6 |
| `frontend/src/components/game/Scoreboard.tsx` | Token + motion | 4,6 |
| `frontend/src/components/game/GameControls.tsx` | Token + 8-state | 4,5 |
| `frontend/src/components/game/BalanceChart.tsx` | Token migration | 4 |
| `frontend/src/components/game/ShoeIndicator.tsx` | Token migration | 4 |
| `frontend/src/components/game/CardTracker.tsx` | Token migration | 4 |
| `frontend/src/components/game/StatsPanel.tsx` | Token + tabular nums | 4,7 |
| `frontend/src/components/game/LastAction.tsx` | Token migration | 4 |
| `DESIGN.md` | New file | 8 |

## Verification

- Visual check at `http://localhost:3000` via Playwright/Chrome MCP
- Landing page: Marquee Hero layout, nav, footer, Three.js scene
- Game page: varied columns, tokenized colors, motion, 8-state buttons
- `prefers-reduced-motion` test via Chrome DevTools emulation
- Run `npm run build` to verify no type errors
