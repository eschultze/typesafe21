# Typesafe 21

AI-powered blackjack simulator where three players with different strategies compete head-to-head, powered by [TypeSafe System One](https://docs.typesafe.ai). Available as both a **terminal app** (Textual TUI) and a **web app** (Next.js + FastAPI) with a [Hallmark](https://github.com/Nutlope/hallmark)-designed Midnight theme.

> **Note:** The terminal version is being sunset in favor of the web version. The web app provides the same gameplay with a richer UI, 3D visuals, animated cards, and session history. The terminal code remains in the repo for reference but is no longer actively maintained.

## Quick Start

### Web (recommended)

```bash
cd typesafe21
./dev.sh
```

Opens `http://localhost:3000` (frontend) and `http://localhost:8000` (backend). Press `Ctrl+C` to stop both.

### Terminal

```bash
cd typesafe21
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## How It Works

Three players sit at the table, each dealt the **same starting hand** for fair comparison:

| Player | Strategy | Bet Sizing |
|--------|----------|------------|
| **Random** | Random hit/stand decisions | Random flat bets ($10-$30) |
| **Basic** | Follows basic strategy (6-deck, dealer stands S17) | Always minimum bet |
| **You (AI)** | TypeSafe AI decides everything autonomously | AI-scored, balance-based (% of bankroll) |

The AI sends the full game state to TypeSafe's System One API on every decision. It sees:

- All visible cards (your hand, dealer upcard)
- Shoe composition (running count, true count, cards remaining by rank)
- Shoe penetration and remaining aces/tens
- Session performance (wins, losses)
- Opponent balances

The AI decides **autonomously** — no basic strategy hints or bias are sent. Basic strategy is only displayed for reference.

## Rules

- 6-deck shoe, auto-reshuffle at 25% remaining
- Hi-Lo card counting (for AI's bet sizing context)
- Dealer stands on soft 17
- Blackjack pays 3:2
- Double down allowed on first two cards
- Split pairs allowed (one split per hand, no double after split)
- Starting balance: $100 per player
- Minimum bet: $10

## Game Modes (Web)

- **New Game** — Start a fresh session with a new shoe
- **Play Round** — Play a single round
- **End Session** — Complete the current session (saved to history)
- **Auto Play** — Play unlimited rounds automatically (500ms delay)
- **+1 / +5 / +10 rounds** — Play a fixed number of rounds automatically
- **History** — Browse completed sessions at `/history`

## AI Primitives Used

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

The web version reads these environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL (used by Next.js rewrites) |
| `NEXT_PUBLIC_WS_HOST` | `window.location.hostname` | WebSocket host for frontend |
| `NEXT_PUBLIC_WS_PORT` | `8000` | WebSocket port for frontend |
| `TYPESAFE_API_KEY` | — | TypeSafe API key |
| `TYPESAFE_API_URL` | — | TypeSafe API endpoint |
| `TYPESAFE_MODEL` | `jev-latest` | TypeSafe model |

## File Structure

```
typesafe21/
  dev.sh                 # Start frontend + backend (Ctrl+C to stop)
  DESIGN.md              # Hallmark Midnight design system (tokens, palette, motion)
  PLAN_WEB_REDESIGN.md   # Full redesign plan (8 phases)
  main.py                # Terminal entry point
  game.py                # Round logic, dealing, payouts, split handling
  player.py              # Player classes (Random, BasicStrategy, AI)
  typesafe_ai.py         # TypeSafe API integration (Choice + Score)
  basic_strategy.py      # Basic strategy lookup (displayed for reference)
  cards.py               # Card, Hand, Deck, TrackedDeck
  database.py            # SQLite persistence
  cash_register.mp3      # Sound effect on AI win
  requirements.txt       # Terminal dependencies
  .env                   # API keys (gitignored)
  game_history.db        # Created at runtime

  backend/               # FastAPI + WebSocket backend
    main.py              # FastAPI app, WebSocket endpoint, REST API
    game_manager.py      # GameSession wrapping game logic for web
    connection_manager.py # WebSocket broadcast manager
    models.py            # Pydantic models (GameState, PlayerState, etc.)
    database.py          # SQLite persistence (same schema as root)
    rules/               # Game logic ported from root with to_dict()
      cards.py
      player.py
      game.py
      basic_strategy.py
      typesafe_ai.py

  frontend/              # Next.js 19 + React + Three.js
    src/
      app/
        globals.css      # Hallmark Midnight tokens, motion, reduced-motion
        layout.tsx       # Root layout with data-theme="midnight"
        page.tsx         # Landing page (Marquee Hero, N7 nav, Ft5 footer)
        game/page.tsx    # Main game board (asymmetric layout)
        history/page.tsx # Session history browser
      stores/
        gameStore.ts     # Zustand state (game state, WebSocket, animations)
      hooks/
        useGameSocket.ts # WebSocket hook with reconnection
      components/
        game/            # PlayingCard, PlayerHand, DealerHand, Scoreboard,
                         # GameControls, BalanceChart, ShoeIndicator,
                         # CardTracker, StatsPanel, LastAction, WinSound,
                         # HeroScene, ChipScene
        ui/              # shadcn/ui components (button, badge, card, etc.)
      components3d/      # Three.js scenes (ChipStack3D, CardShuffle)

  ui/                    # Terminal UI (Textual) [sunset, kept for reference]
    app.py               # Textual app, screen routing
    styles.tss           # Textual CSS
    screens/
      game.py            # Main game screen with state machine
      menu.py            # Menu screen
      summary.py         # Session summary
      history.py         # Session history (modal)
    widgets/
      card_art.py        # ASCII card rendering (5-line box art)
      dealer_panel.py    # Dealer hand display
      players_panel.py   # Player hands with card art + loading spinner
      scoreboard_panel.py # Balances, W/L, win rate
      deck_panel.py      # Deck remaining, true count, running count
      balance_chart.py   # Custom bar chart with Y-axis labels
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design and [WEB.md](WEB.md) for web-specific details.
