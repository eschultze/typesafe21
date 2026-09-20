# Architecture — Typesafe 21

## System Overview

```
main.py  ──>  ui/app.py  ──>  ui/screens/game.py  ──>  game.py  ──>  typesafe_ai.py  ──>  TypeSafe API
                                │                               │                               │
                                v                               v                               v
                            ui/widgets/                     player.py              (hit/stand/double/split)
                            (Textual CSS)                   cards.py               (bet sizing via Score)
                                                          basic_strategy.py
                                                          (BasicStrategyPlayer)
```

The game enforces a strict separation: **game mechanics** (dealing, comparing hands, payouts) stay local. **Player decisions** (what to bet, hit or stand) are delegated to each player's strategy. The AI makes every decision autonomously with zero local fallback logic.

## Module Responsibilities

### `main.py` — Entry Point

- Launches the Textual app (`TypesafeApp`)
- Minimal setup code

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

## UI Widgets

- `DealerPanel` — Dealer hand with card art, hides first card until dealer's turn
- `PlayersPanel` — Player hands with card art, win/lose indicators, AI decision display, loading spinner
- `ScoreboardPanel` — Balances, W/L records, win rates
- `DeckPanel` — Cards remaining, true count, running count, shoe penetration
- `BalanceChartPanel` — Custom bar chart with Y-axis labels showing AI balance over time
  - Green bars = above starting balance, Red bars = below
  - Y-axis labels show dollar values
  - Grows one bar per round

## Data Flow: One Round

```
1. do_bets()
   ├── AI calls get_ai_bet() → Score 0-4 → mapped to balance-based percentage
   ├── BasicStrategyPlayer bets minimum
   ├── RandomPlayer picks random flat bet
   └── Bets deducted from balances

2. deal_initial()
   ├── Deal one shared hand (2 cards) → copy to all players
   └── Deal dealer's own hand (2 cards)

3. For each player:
   └── play_player_hand()
       ├── AI calls get_ai_decision() → hit/stand/double/split
       ├── BasicStrategy follows lookup table
       ├── Random picks randomly
       ├── Hit: deal card, loop again
       ├── Double: double bet, deal one card, break
       ├── Split: create two hands, play each independently
       └── Stand: break

4. play_dealer()
   └── Dealer hits until >= 17

5. settle_round()
   ├── determine_winner() for each player/hand
   ├── Win: balance += bet + bet * multiplier
   ├── Push: balance += bet (returned)
   └── Lose: bet already deducted

6. save_round() to database
7. Update balance chart
```

## Key Design Decisions

1. **Autonomous AI** — Every decision goes to TypeSafe with zero local bias. No basic strategy hints sent.

2. **Same starting hand** — All three players receive identical cards for fair strategy comparison.

3. **Score for betting** — Bet sizing is a continuous spectrum. Score maps to balance-based percentages (5%-50%).

4. **Structured Choice criteria** — Each action has `what`, `not_for`, and `examples` fields.

5. **Rich state** — AI sees shoe composition, opponent balances, and session performance.

6. **No fallbacks** — If the API is down, the game stops. This forces the AI to actually play rather than silently reverting to local rules.
