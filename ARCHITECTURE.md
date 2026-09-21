# Architecture — Typesafe 21

> **Note:** The terminal version is being sunset in favor of the web version. The architecture below covers both for reference, but active development targets the web app.

## System Overview

### Terminal (sunset)

```
main.py  ──>  ui/app.py  ──>  ui/screens/game.py  ──>  game.py  ──>  typesafe_ai.py  ──>  TypeSafe API
                                │                               │                               │
                                v                               v                               v
                            ui/widgets/                     player.py              (hit/stand/double/split)
                            (Textual CSS)                   cards.py               (bet sizing via Score)
                                                          basic_strategy.py
                                                          (BasicStrategyPlayer)
```

### Web (active)

```
Browser (Next.js)                Backend (FastAPI)              TypeSafe API
┌─────────────────┐             ┌──────────────────┐           ┌──────────┐
│  React + Zustand │◄─WebSocket─┤  game_manager.py  │───────────┤  Choice  │
│  Tailwind + 3D   │             │  rules/           │           │  Score   │
│  shadcn/ui       │◄──REST─────┤  database.py      │           └──────────┘
└─────────────────┘             └──────────────────┘
      :3000                           :8000
```

The web version ports the existing Python game logic to a FastAPI backend with WebSocket real-time updates. The frontend is a Next.js SPA with Zustand state management, Motion animations, and Three.js 3D scenes.

## Core Game Logic

These modules are shared between terminal and web (the web version ports them to `backend/rules/`).

### `game.py` — Game Mechanics

- `do_bets()` — Collects bets from all players, passes opponent balances and shoe composition to AI
- `deal_initial()` — Deals one shared starting hand to all players (same cards for fair comparison), plus dealer's own hand
- `play_player_hand()` — Decision loop for a single hand (hit/stand/double/split)
- `_play_hand_loop()` — Helper to play out a split hand (no double/split allowed after split)
- `play_dealer()` — Dealer hits until soft 17 or higher
- `determine_winner()` — Compares player hand vs dealer hand (win/lose/push)
- `settle_round()` — Settles all hands including split hands, updates balances
- `get_payout_multiplier()` — Returns 1.5 for blackjack, 1.0 otherwise

Game mechanics stay here. No strategy logic. No decision-making.

### `player.py` — Player Abstractions

- `Player` (ABC) — Base class with balance, betting, hand management, split_hands storage, balance_history
- `RandomPlayer` — Random hit/stand, random flat bets ($10-$30)
- `BasicStrategyPlayer` — Follows basic strategy exactly (6-deck, dealer stands S17), always bets minimum
- `AIPlayer` — Delegates all decisions to TypeSafe API via `typesafe_ai.py`
  - `decide_bet()` — Calls `get_ai_bet()` with full shoe composition
  - `make_decision()` — Calls `get_ai_decision()` for hit/stand/double/split
  - `split_hands` — List of `(hand, bet, decision, confidence)` for split hands

### `typesafe_ai.py` — AI Decision Engine

Two functions, two TypeSafe API calls per round:

**`get_ai_decision()`** — Action selection
- Sends full game state (player hand, dealer upcard, counts, shoe composition)
- Uses **Choice** primitive with 4 options: `hit`, `stand`, `double`, `split`
- Structured criteria with `what`, `not_for`, and `examples` for each action
- No basic strategy hints — AI decides autonomously
- Returns: decision, confidence, probabilities

**`get_ai_bet()`** — Bet sizing
- Sends balance, count, shoe position, opponent balances, session performance, shoe composition
- Uses **Score** primitive with 5 levels (minimum → maximum)
- Maps continuous score (0.0-4.0) to balance-based percentage:
  - Score 0 → 5%, Score 1 → 15%, Score 2 → 25%, Score 3 → 35%, Score 4 → 50%
- Dynamic hint based on actual true count
- Returns: bet, score, confidence, probabilities, reasoning

### `basic_strategy.py` — Basic Strategy Reference

- Complete lookup tables for 6-deck, dealer stands S17
- Hard totals, soft totals, pairs
- `get_basic_strategy()` — Returns H/S/D/P recommendation
- `get_basic_strategy_action()` — Returns actionable decision (hit/stand/double/split)
- Used by `BasicStrategyPlayer` for gameplay and displayed for reference

### `cards.py` — Card Game Primitives

- `Suit` — Enum: Hearts, Diamonds, Clubs, Spades
- `Card` — Rank + suit with computed value
- `Hand` — Card collection with value calculation, soft/hard detection, bust/blackjack checks
- `Deck` — Basic deck with shuffle and deal
- `TrackedDeck` — Deck with card counting (Hi-Lo), shoe penetration tracking, auto-reshuffle at 25%

The `TrackedDeck` provides:
- `running_count` — Hi-Lo count
- `true_count` — Running count adjusted for decks remaining
- `get_remaining_by_rank()` — Cards left by rank (for AI context)
- `get_cards_since_reshuffle()` — Shoe penetration

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
    balance_after INTEGER
)
```

Functions: `init_db`, `create_session`, `save_round`, `complete_session`, `get_last_incomplete_session`, `get_round_count`, `get_session_stats`, `get_all_sessions`, `get_session_rounds`, `clear_database`

## Web Backend

### `backend/main.py` — FastAPI App

- REST endpoints: `GET /api/health`, `GET /api/history`, `GET /api/history/{id}`
- WebSocket endpoint: `/ws/{game_id}`
- Actions handled via WebSocket JSON messages:
  - `new_game` — Reset deck, players, start fresh session
  - `play_round` — Play one complete round (bet, deal, player turns, dealer, settle)
  - `auto_play` — Start/stop auto-play loop with configurable delay and round limit
  - `end_session` — Mark session complete, start new game
  - `get_state` — Request current state

### `backend/game_manager.py` — Game Session Manager

- `GameManager` — Pool of `GameSession` instances by game ID
- `GameSession` — Wraps game logic for web: converts state to Pydantic models, manages auto-play loop
- Delegates history/stats to `database.py`

### `backend/models.py` — Pydantic Models

- `GameState` — Full game state (phase, players, dealer, shoe, last_action, etc.)
- `PlayerState` — Per-player state (name, balance, hand, wins/losses/pushes)
- `HandModel` — Hand with cards, value, soft/bust/blackjack flags
- `ShoeState` — Shoe state (remaining, counts, played_ranks)
- `BetResult`, `HandResult`, `RoundResultModel` — Round result models

### `backend/connection_manager.py` — WebSocket Manager

- `ConnectionManager` — Tracks WebSocket connections per game ID
- `broadcast()` — Sends messages to all connected clients in a game

## Web Frontend

### State Management — `gameStore.ts` (Zustand)

- `GameState` — Mirror of backend state (phase, players, dealer, shoe)
- `ai_bet_history` / `ai_confidence_history` — Tracked across rounds for StatsPanel
- `prev_bets` — Used to detect bet changes and trigger chip animations
- `chipsAnimating` — Animation flag
- WebSocket integration via `sendAction()` and `updateState()`

### Key Components

- `PlayingCard` — Animated card with spring physics (Motion), suit-colored text, tokenized background/border
- `PlayerHand` — Player hand panel with cards, badges (BJ/bust), accent glow, profit/loss coloring
- `DealerHand` — Dealer hand with card hiding until reveal phase, themed transitions
- `GameControls` — New Game, Play Round (accent), End Session, Auto Play with 8-state styling
- `Scoreboard` — Player balances with animated profit indicators, varied column widths
- `ShoeIndicator` — Progress bar (accent) showing shoe depletion + true count badge
- `BalanceChart` — SVG line chart of AI balance over time with themed stroke/fill colors
- `CardTracker` — Bar chart showing card composition by rank with themed bar colors
- `StatsPanel` — AI average bet, confidence, round count on card background
- `LastAction` — Displays previous round's results with profit/loss badges
- `WinSound` — Plays cash register sound on AI win
- `HeroScene` / `ChipScene` — Three.js 3D scenes

### WebSocket Hook — `useGameSocket.ts`

- Connects to backend WebSocket with exponential backoff reconnection
- Configurable host/port via `NEXT_PUBLIC_WS_HOST` / `NEXT_PUBLIC_WS_PORT`
- Dispatches `state_update` messages to Zustand store

## Data Flow: One Round (Web)

```
1. Frontend sends { action: "play_round" } via WebSocket
2. Backend: do_bets()
   ├── AI calls get_ai_bet() → Score 0-4 → mapped to balance-based percentage
   ├── BasicStrategyPlayer bets minimum
   ├── RandomPlayer picks random flat bet
   └── Bets deducted from balances
3. Backend: deal_initial()
   ├── Deal one shared hand (2 cards) → copy to all players
   └── Deal dealer's own hand (2 cards)
4. Backend: For each player: play_player_hand()
   ├── AI calls get_ai_decision() → hit/stand/double/split
   ├── BasicStrategy follows lookup table
   └── Random picks randomly
5. Backend: play_dealer() — Dealer hits until >= 17
6. Backend: settle_round() — Win/lose/push for each player
7. Backend: save_round() to database
8. Backend: Broadcast full state to all WebSocket clients
9. Frontend: Zustand store updates → React re-renders
```

## Key Design Decisions

1. **Autonomous AI** — Every decision goes to TypeSafe with zero local bias. No basic strategy hints sent.

2. **Same starting hand** — All three players receive identical cards for fair strategy comparison.

3. **Score for betting** — Bet sizing is a continuous spectrum. Score maps to balance-based percentages (5%-50%).

4. **Structured Choice criteria** — Each action has `what`, `not_for`, and `examples` fields.

5. **Rich state** — AI sees shoe composition, opponent balances, and session performance.

6. **No fallbacks** — If the API is down, the game stops. This forces the AI to actually play rather than silently reverting to local rules.

7. **Shared game logic** — The `backend/rules/` directory mirrors root game modules with `to_dict()` serialization, keeping terminal and web independent.

8. **Real-time updates** — WebSocket broadcasts full game state after every phase, enabling smooth animations and live updates.

## Design System — Midnight (Hallmark)

The web frontend uses a [Hallmark](https://github.com/Nutlope/hallmark)-designed Midnight theme. Tokens are defined in `frontend/src/app/globals.css` and consumed by all components via CSS custom properties.

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
