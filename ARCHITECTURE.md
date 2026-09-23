# Architecture — Typesafe 21

## System Overview

```
Browser (Next.js)                Backend (FastAPI)              AI Engines
┌─────────────────┐             ┌──────────────────┐           ┌──────────────┐
│  React + Zustand │◄─WebSocket─┤  game_manager.py  │───────────┤ TypeSafe API │
│  Tailwind + 3D   │             │  rules/           │           │ (Jev AI)     │
│  shadcn/ui       │◄──REST─────┤  database.py      │           ├──────────────┤
└─────────────────┘             └──────────────────┘           │ Laya model   │
      :3000                           :8000                    │ (Local AI)   │
                                                                └──────────────┘
```

FastAPI backend in `web_main.py` manages sessions, broadcasts state via WebSocket, and persists rounds to SQLite. Frontend is a Next.js SPA with Zustand state management, Motion animations, and Three.js 3D scenes.

## Project Structure

```
typesafe21/
├── pyproject.toml          # uv project config
├── .venv/                  # Managed by uv
├── dev.sh                  # Starts both frontend and backend
│
├── rules/                  # Game logic
│   ├── cards.py
│   ├── player.py
│   ├── game.py
│   ├── basic_strategy.py
│   ├── typesafe_ai.py
│   ├── laya_ai.py
│   └── ai_shared.py
│
├── database.py             # SQLite (WAL, indexes, foreign keys, leaderboards)
├── models.py               # Pydantic models for WebSocket API
├── game_manager.py         # Game session manager (async, asyncio.to_thread)
├── connection_manager.py   # WebSocket broadcast manager
├── web_main.py             # FastAPI entry point
│
└── frontend/               # Next.js 19 frontend
```

## Core Game Logic

### `rules/game.py` — Game Mechanics

- `do_bets()` — Collects bets from all players, passes opponent balances and shoe composition to AI
- `deal_initial()` — Deals one shared starting hand to all players (same cards for fair comparison), plus dealer's own hand
- `play_player_hand()` — Decision loop for a single hand (hit/stand/double/split)
- `_play_hand_loop()` — Helper to play out a split hand (no double/split allowed after split)
- `play_dealer()` — Dealer hits soft 17, hits on hard 16 or less
- `determine_winner()` — Compares player hand vs dealer hand (win/lose/push)
- `settle_round()` — Settles all hands including split hands, updates balances
- `get_payout_multiplier()` — Returns 1.5 for blackjack, 1.0 otherwise

Game mechanics stay here. No strategy logic. No decision-making.

### `rules/player.py` — Player Abstractions

- `Player` (ABC) — Base class with balance, betting, hand management, split_hands storage, balance_history
- `RandomPlayer` — Random hit/stand, random flat bets ($10-$30), clamped to balance. Seedable for reproducibility.
- `BasicStrategyPlayer` — Follows basic strategy exactly (6-deck, dealer hits soft 17), always bets minimum
- `AIPlayer` — Delegates all decisions to TypeSafe API via `typesafe_ai.py` (Jev AI)
  - `decide_bet()` — Calls `get_ai_bet()` with full shoe composition
  - `make_decision()` — Calls `get_ai_decision()` for hit/stand/double/split
  - `split_hands` — List of `(hand, bet, decision, confidence)` for split hands
- `LayaPlayer` — Delegates all decisions to local Laya model via `laya_ai.py` (Laya AI)
  - Same interface as `AIPlayer` — uses identical prompts with Choice and Score primitives
  - Laya runs locally: ~33ms on GPU, ~300ms on CPU (vs ~240ms for TypeSafe API)

### `rules/ai_shared.py` — Shared AI Bet Logic

Extracted from `typesafe_ai.py` and `laya_ai.py` to eliminate duplication. Contains:

- `build_bet_state()` — Constructs the full state dictionary sent to both AI engines (balance, count, shoe position, opponent balances, session performance, shoe composition)
- `process_bet_result()` — Processes the AI's Score response into a bet amount using balance-based percentages (Score 0 → 5%, 1 → 15%, 2 → 25%, 3 → 35%, 4 → 50%)
- `build_bet_reasoning()` — Generates the human-readable bet summary shown in the UI
- `chance_to_bust_on_next_draw()` — Percent chance the next card busts the player's hand, from the remaining shoe
- `dealer_bust_probability()` — Exact dealer bust probability from the unseen shoe (remaining + unknown hole card), respecting H17

Both AI modules import and call these shared functions, keeping only their engine-specific API calls locally.

### `rules/typesafe_ai.py` — TypeSafe AI Decision Engine (Jev)

Two functions, two TypeSafe API calls per round:

**`get_ai_decision()`** — Action selection
- Sends full game state (player hand, dealer **upcard** (index 0), dealer-bust probability, our chance to bust on next draw, counts, full shoe composition)
- Uses **Choice** primitive with 4 options: `hit`, `stand`, `double`, `split` (illegal options are removed; there is no `other` option — an out-of-vocabulary answer falls back to `stand`)
- Structured criteria with `what`, `not_for`, and `examples` for each action
- No basic strategy hints — AI decides autonomously
- Returns: decision, confidence, probabilities, latency_ms, tokens
- Retries on timeout, connection error, HTTP 5xx/429, and malformed responses

**`get_ai_bet()`** — Bet sizing
- Sends balance, count, shoe position, opponent balances, session performance, shoe composition
- Uses **Score** primitive with 5 levels (minimum → maximum)
- Delegates to `ai_shared.py` for score-to-bet mapping
- Returns: bet, score, confidence, probabilities, reasoning

### `rules/laya_ai.py` — Local Laya AI Decision Engine

Same interface as `typesafe_ai.py`, using the [Laya](https://github.com/NandhaKishorM/laya) library for local inference:

- Lazy-loaded singleton with `threading.Lock` for thread safety
- Uses identical state dictionaries and question criteria as TypeSafe
- **Choice** primitive for action selection, **Score** primitive for bet sizing
- Response parsing: `result["answers"]["action"]["choice"]` with `confidence` and `probabilities`
- ~33ms on GPU, ~300ms on CPU (vs ~240ms for TypeSafe API round-trip)

### `rules/basic_strategy.py` — Basic Strategy Reference

- Complete lookup tables for 6-deck, dealer hits soft 17
- Hard totals, soft totals, pairs
- `get_basic_strategy()` — Returns H/S/D/P recommendation, using **only the dealer upcard** (`cards[0]`); the hole card is never consulted
- `get_basic_strategy_action()` — Returns actionable decision (hit/stand/double/split)
- Used by `BasicStrategyPlayer` for gameplay and displayed for reference

### `rules/cards.py` — Card Game Primitives

- `Suit` — Enum: Hearts, Diamonds, Clubs, Spades
- `Card` — Rank + suit with computed value
- `Hand` — Card collection with value calculation, soft/hard detection, bust/blackjack checks
- `TrackedDeck` — Deck with card counting (Hi-Lo), shoe penetration tracking, auto-reshuffle at 25%

The `TrackedDeck` provides:
- `running_count` — Hi-Lo count
- `true_count` — Running count adjusted for decks remaining (float, 1 decimal)
- `get_remaining_by_rank()` — Cards left by rank (for AI context)
- `get_cards_since_reshuffle()` — Shoe penetration
- `to_dict()` — Serialized state for WebSocket API

### `database.py` — SQLite Persistence

Three tables:

```sql
sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_rounds INTEGER DEFAULT 0,
    is_complete INTEGER DEFAULT 0
)

rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    round_number INTEGER,
    dealer_final_value INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

player_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER REFERENCES rounds(id),
    player_index INTEGER,
    player_name TEXT,
    result TEXT,
    bet INTEGER,
    confidence REAL,
    decision TEXT,
    balance_after INTEGER,
    latency_ms REAL DEFAULT 0,      -- avg per AI decision this round
    tokens INTEGER DEFAULT 0,       -- avg tokens per AI decision this round
    decisions INTEGER DEFAULT 0,    -- AI calls this round (bet + plays)
    true_count REAL                 -- true count when bets were placed
)
```

`init_db()` migrates older databases in place via `_ensure_columns()` (adds any missing benchmark columns with `ALTER TABLE`).

Functions: `init_db`, `create_session`, `save_round`, `complete_session`, `get_last_incomplete_session`, `get_round_count`, `get_session_stats`, `get_all_sessions`, `get_session_rounds`, `get_benchmark_rows`, `clear_database`, `get_top_single_turn_profits`, `get_top_session_profits`

### `benchmark.py` — Benchmark Aggregation

Single source of truth for Jev-vs-Laya stats, served by `GET /api/benchmark` (all-time) and `GET /api/benchmark?session_id=N` (one session). `build_benchmark()` collapses raw rows into one record per `(session, round, player)` (splits aggregated; round-end balance wins), derives per-round profit from balance deltas, and returns per-player metrics, head-to-head (paired per-round diff + 95% CI), and true-count buckets. Keeping aggregation server-side means the session and all-time scopes can never diverge.

Configuration:
- WAL mode enabled (`PRAGMA journal_mode=WAL`) for concurrent read/write
- Foreign keys enforced (`PRAGMA foreign_keys = ON`)
- Indexes on `rounds(session_id)`, `player_rounds(round_id)`, `player_rounds(player_name)`

## Backend

### `web_main.py` — FastAPI App

- REST endpoints: `GET /api/health`, `GET /api/history`, `GET /api/history/{id}`, `GET /api/leaderboard`, `GET /api/benchmark?session_id=`
- WebSocket endpoint: `/ws/{game_id}`
- WebSocket message validation: rejects non-dict payloads, unknown actions, and invalid `delay_ms` values (clamped to 100-5000ms)
- CORS origins configurable via `CORS_ORIGINS` (default `*`)
- Auto-play task stored per session, cancelled before re-creating and on disconnect
- Actions handled via WebSocket JSON messages:
  - `new_game` — Reset deck, players, start fresh session
  - `clear_database` — Truncate all persisted history, then start a fresh session
  - `play_round` — Play one complete round. Rejected unless `phase == "idle"` and auto-play is off.
  - `auto_play` — Start/stop auto-play loop with configurable delay and round limit
  - `end_session` — Mark session complete, start new game
  - `get_state` — Request current state

### `game_manager.py` — Game Session Manager

- `GameManager` — Pool of `GameSession` instances by game ID. Sessions are cleaned up on disconnect.
- `GameSession` — Wraps game logic for web: converts state to Pydantic models, manages auto-play loop
  - `play_round()` is async and guarded by an `asyncio.Lock`, so a manual round and the auto-play loop (or two clients) cannot mutate the session concurrently
  - DB calls and blocking AI calls are wrapped in `asyncio.to_thread()` to avoid blocking the event loop
  - If a round raises (e.g. the remote AI is down), the round is **rolled back** (balances/wins/history restored) and the session stays alive with an `error` `last_action`, instead of tearing down the session
  - Intermediate state broadcasts between phases (betting, dealing, player_turn, dealer_turn) so frontend sees phase transitions
  - Creates session before saving rounds to prevent FK violations
- Delegates history/stats/benchmark to `database.py` and `benchmark.py`

### `models.py` — Pydantic Models

- `GameState` — Full game state (phase, players, dealer, shoe, last_action, etc.)
- `PlayerState` — Per-player state (name, balance, hand, wins/losses/pushes, `can_play` for the "Out" badge)
- `HandModel` — Hand with cards, value, soft/bust/blackjack flags
- `ShoeState` — Shoe state (remaining, counts, played_ranks)
- `BetResult`, `HandResult` — Round models, including `latency_ms`, `tokens`, and `decisions`

### `connection_manager.py` — WebSocket Manager

- `ConnectionManager` — Tracks WebSocket connections per game ID
- `broadcast()` — Sends messages to all connected clients in a game. Dead connections that fail during send are automatically removed.

## Frontend

### State Management — `gameStore.ts` (Zustand)

- `GameState` — Mirror of backend state (phase as union type, players, dealer, shoe)
- `player_histories` — Per-player stats: `Record<string, { bets: number[], confidences: number[] }>` — tracks bet and confidence history for all players (Random, Basic, Jev, Laya)
- `prev_bets` — Used to detect bet changes and trigger chip animations
- `chipsAnimating` — Animation flag
- `last_recorded_round` — Tracks most recently recorded round to prevent duplicate stat accumulation
- `chipAnimTimeout` — Reference to chip animation timeout for cleanup (prevents overlapping timers)
- `LastAction` — Typed discriminated union for previous round results (replaces `any`)
- WebSocket integration via `sendAction()` and `updateState()`

### Key Components

- `PlayingCard` — Animated card with spring physics (Motion), suit-colored text, tokenized background/border
- `PlayerHand` — Player hand panel with cards, badges (BJ/bust), accent glow, profit/loss coloring, inline chips, AI thinking overlay
- `DealerHand` — Dealer hand with card hiding until reveal phase, themed transitions
- `GameControls` — New Game, Play Round (accent), End Session, Auto Play with 8-state styling
- `Scoreboard` — Player balances with animated profit indicators, varied column widths
- `ShoeIndicator` — Progress bar (accent) showing shoe depletion + true count badge
- `BalanceChart` — SVG line charts per-player balance over time (player-agnostic via `player_histories`)
- `CardTracker` — Bar chart showing card composition by rank with themed bar colors
- `BenchmarkPanel` — Jev-vs-Laya scorecard with This-session / All-time scopes, polling `/api/benchmark` (Edge, win rate, calibration, latency, tokens, betting-by-count, risk)
- `LastAction` — Displays previous round's results with profit/loss badges (AnimatePresence keyed for exit animations)
- `WinSound` — Plays cash register sound on AI win (proper cleanup on unmount)
- `Leaderboard` — Top players across sessions (fetched via Next.js proxy)
- `HeroScene` / `ChipScene` — Three.js 3D scenes
- `ErrorBoundary` — Catches runtime exceptions, prevents blank-white crashes
- `Nav` — Shared navigation bar extracted from page layouts

### WebSocket Hook — `useGameSocket.ts`

- Connects to backend WebSocket with exponential backoff reconnection
- Configurable host/port via `NEXT_PUBLIC_WS_HOST` / `NEXT_PUBLIC_WS_PORT`
- Dispatches `state_update` messages to Zustand store

## Data Flow: One Round

```
1. Frontend sends { action: "play_round" } via WebSocket
2. Backend: do_bets() [in asyncio.to_thread]
   ├── Broadcasts "betting" phase
   ├── Jev AI calls TypeSafe API get_ai_bet() → Score 0-4 → balance-based %
   ├── Laya AI calls local get_ai_bet() → Score 0-4 → balance-based %
   ├── BasicStrategyPlayer bets minimum
   ├── RandomPlayer picks random flat bet
   └── Bets deducted from balances
3. Backend: deal_initial() [in asyncio.to_thread]
   ├── Broadcasts "dealing" phase
   ├── Deal one shared hand (2 cards) → copy to all 4 players
   └── Deal dealer's own hand (2 cards)
4. Backend: For each player: play_player_hand()
   ├── Broadcasts "player_turn" phase
   ├── Jev AI calls TypeSafe API get_ai_decision() → hit/stand/double/split
   ├── Laya AI calls local get_ai_decision() → hit/stand/double/split
   ├── BasicStrategy follows lookup table
   └── Random picks randomly
5. Backend: play_dealer() [in asyncio.to_thread]
   ├── Broadcasts "dealer_turn" phase
   └── Dealer hits soft 17, stands on hard 17+
6. Backend: settle_round() — Win/lose/push for each player
7. Backend: save_round() to database
8. Backend: Broadcasts final state to all WebSocket clients
9. Frontend: Zustand store updates → React re-renders
```

## Key Design Decisions

1. **Autonomous AI** — Every decision goes to the AI engine with zero local bias. No basic strategy hints sent. Jev uses the remote TypeSafe API; Laya uses a local model.

2. **Same starting hand** — All four players receive identical cards for fair strategy comparison.

3. **Score for betting** — Bet sizing is a continuous spectrum. Score maps to balance-based percentages (5%-50%).

4. **Structured Choice criteria** — Each action has `what`, `not_for`, and `examples` fields.

5. **Rich state** — AI sees shoe composition, opponent balances, and session performance.

6. **No silent fallbacks** — If the API is down, the AI does not quietly revert to local rules; the round is rolled back and surfaced as an error, and auto-play stops. The session stays alive so a transient failure doesn't destroy the run. Laya runs locally so it's always available.

10. **Fair comparison** — All players receive the same starting hand, and the benchmark normalizes by amount wagered (edge) and uses paired per-round Jev-vs-Laya diffs with a 95% CI, so differing bet sizes and variance don't distort the verdict.

11. **Natural blackjack vs split 21** — A split hand that reaches 21 in two cards is *not* a natural: it pays 1:1 and loses to a dealer natural. `determine_winner`/`get_payout_multiplier` take an `allow_player_natural` flag that the split loop sets to `False`.

7. **Dual AI engines** — Jev (remote, ~240ms) and Laya (local, ~33ms GPU) use identical prompts with Choice and Score primitives, enabling direct comparison of remote vs local inference.

8. **Real-time updates** — WebSocket broadcasts full game state after every phase, enabling smooth animations and live updates.

9. **Single venv** — All Python dependencies managed by `uv` with one `pyproject.toml`.

## Design System — Midnight (Hallmark)

The frontend uses a [Hallmark](https://github.com/Nutlope/hallmark)-designed Midnight theme. Tokens are defined in `frontend/src/app/globals.css` and consumed by all components via CSS custom properties.

**Palette** (OKLCH):
- Paper: `oklch(15% 0.022 250)` — dark blue-grey base
- Ink: `oklch(95% 0.008 230)` — primary text
- Accent: `oklch(72% 0.16 220)` — electric blue (buttons, highlights, progress)
- Neutral scale: tinted toward hue 250 (not pure grey)

**Typography**: Geist Sans (`--font-geist-sans`) and Geist Mono (`--font-geist-mono`) with `tabular-nums` on all data displays.

**Spacing scale**: `--space-1` (4px) through `--space-16` (64px), linear 4px step.

**Motion**: `--dur-micro` (120ms), `--dur-short` (220ms), `--dur-long` (420ms), `--ease-out` for emphasis. `prefers-reduced-motion` collapses all durations to 0ms.

**Layout**: Landing page uses Marquee Hero with N7 Brutal Slab nav and Ft5 Statement footer. Game page uses asymmetric column widths (`1.2fr / 1fr / 0.8fr`) for visual variety.

See `DESIGN.md` for the full token reference and component shape specifications.
