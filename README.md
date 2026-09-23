# Typesafe 21

AI-powered blackjack simulator where four players with different strategies compete head-to-head — two remote AIs (TypeSafe Jev + local Laya) and two deterministic baselines. Built with Next.js + FastAPI with a [Hallmark](https://github.com/Nutlope/hallmark)-designed Midnight theme.

## Quick Start

```bash
cd typesafe21
./dev.sh
```

Opens `http://localhost:3000` (frontend) and `http://localhost:8000` (backend). Press `Ctrl+C` to stop both.

## How It Works

Four players sit at the table, each dealt the **same starting hand** for fair comparison:

```
Random | Basic
Jev    | Laya
```

| Player | Strategy | Bet Sizing |
|--------|----------|------------|
| **Random** | Random hit/stand decisions | Random flat bets ($10-$30) |
| **Basic** | Follows basic strategy (6-deck, dealer hits soft 17) | Always minimum bet |
| **Jev (AI)** | Remote TypeSafe API — decides everything autonomously | AI-scored, balance-based (% of bankroll) |
| **Laya (AI)** | Local [Laya](https://github.com/NandhaKishorM/laya) model — 33ms decisions on GPU | AI-scored, balance-based (% of bankroll) |

Both AI players send the full game state to their respective engines on every decision. They see:

- All visible cards (your hand, dealer upcard)
- Shoe composition (running count, true count, cards remaining by rank)
- Shoe penetration and remaining aces/tens
- Session performance (wins, losses)
- Opponent balances

The AIs decide **autonomously** — no basic strategy hints or bias are sent. Basic strategy is only displayed for reference.

## Rules

- 6-deck shoe, auto-reshuffle at 25% remaining
- Hi-Lo card counting (for AI's bet sizing context)
- Dealer hits soft 17
- Blackjack pays 3:2
- Double down allowed on first two cards
- Split pairs allowed (one split per hand, no double after split)
- Starting balance: $100 per player
- Minimum bet: $10

## Game Modes

- **New Game** — Start a fresh session with a new shoe
- **Play Round** — Play a single round
- **End Session** — Complete the current session (saved to history)
- **Auto Play** — Play unlimited rounds automatically (500ms delay)
- **+1 / +5 / +10 rounds** — Play a fixed number of rounds automatically
- **Clear Database** — Wipe all persisted history (with a second confirmation) and start fresh
- **History** — Browse completed sessions at `/history`

## Benchmarking

The game page has a **Benchmark** panel comparing Jev vs Laya, with two scopes:

- **This session** — the current live session
- **All time** — every persisted round across all sessions

Metrics (all computed server-side from `/api/benchmark`, so the two scopes stay consistent):

| Tab | Metrics |
|-----|---------|
| **Scorecard** | Edge (profit ÷ wagered), net profit, win rate, W/P/L, avg bet, confidence, calibration gap, latency p50/p95, tokens/decision, AI calls/round, head-to-head paired diff with 95% CI |
| **Betting** | Avg/max bet, bet-vs-true-count buckets (avg bet + EV), count exploitation |
| **Risk** | Max drawdown, volatility/round, return/risk, Brier score |

Latency, token usage, decision counts, and true-count-at-bet are persisted per player-round (`player_rounds.latency_ms/tokens/decisions/true_count`), so all-time stats accumulate across reloads and sessions.

## AI Engines

| Engine | Type | Latency | Model |
|--------|------|---------|-------|
| **Jev (AI)** | Remote API | ~240ms | TypeSafe System One (`jev-latest`) |
| **Laya (AI)** | Local inference | ~33ms GPU / ~300ms CPU | Laya English (ModernBERT-large, 421M) |

Both use the same **Choice** and **Score** primitives with identical prompts:

| Primitive | Purpose |
|-----------|---------|
| **Choice** | Hit, stand, double, or split — with structured criteria (`what`, `not_for`, `examples`) |
| **Score** | Bet sizing on a continuous 0-4 spectrum — mapped to balance-based percentages |

## Bet Sizing

The AI uses balance-based percentages driven by its Score response:

| Score | % of Balance | Example ($150) |
|-------|-------------|----------------|
| 0 (min) | 5% | $10 |
| 1 (small) | 15% | $22 |
| 2 (medium) | 25% | $37 |
| 3 (large) | 35% | $52 |
| 4 (max) | 50% | $75 |

The AI's Score determines the bet aggressiveness. No hardcoded formula — the AI decides.

## Configuration

The app reads these environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL (used by Next.js rewrites) |
| `NEXT_PUBLIC_WS_HOST` | `window.location.hostname` | WebSocket host for frontend |
| `NEXT_PUBLIC_WS_PORT` | `8000` | WebSocket port for frontend |
| `TYPESAFE_API_KEY` | — | TypeSafe API key |
| `TYPESAFE_API_URL` | — | TypeSafe API endpoint |
| `TYPESAFE_MODEL` | `jev-latest` | TypeSafe model (used by Jev AI) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins for the backend |

## File Structure

```
typesafe21/
├── pyproject.toml          # uv project config
├── dev.sh                  # Start frontend + backend (Ctrl+C to stop)
│
├── rules/                  # Game logic
│   ├── cards.py            # Card, Hand, TrackedDeck (with to_dict())
│   ├── player.py           # Player classes (Random, Basic, AI, Laya)
│   ├── game.py             # Round logic, dealing, payouts, splits
│   ├── basic_strategy.py   # Basic strategy lookup tables
│   ├── typesafe_ai.py      # TypeSafe API integration (Jev)
│   ├── laya_ai.py          # Local Laya integration (Laya)
│   └── ai_shared.py        # Shared AI bet logic (DRY)
│
├── database.py             # SQLite persistence (WAL, indexes, foreign keys)
├── models.py               # Pydantic models (GameState, PlayerState, etc.)
├── game_manager.py         # Game session manager (async, to_thread)
├── connection_manager.py   # WebSocket broadcast manager
├── web_main.py             # FastAPI entry point
│
├── frontend/               # Next.js 19 + React + Three.js
├── game_history.db         # Created at runtime
└── .env                    # API keys (gitignored)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design and [WEB.md](WEB.md) for web-specific details.
