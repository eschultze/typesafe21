# TypeSafe21 — Web Version

AI-powered Blackjack with three players, one shoe, and zero mercy.

> **Note:** The terminal version is being sunset. This web version is the primary interface going forward.

## Quick Start

```bash
cd typesafe21
./dev.sh
```

Opens `http://localhost:3000` (frontend) and `http://localhost:8000` (backend). Press `Ctrl+C` to stop both.

### Manual Setup

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env .env   # or create with TYPESAFE_API_KEY, TYPESAFE_API_URL, TYPESAFE_MODEL
python main.py
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Architecture

- **Backend**: FastAPI + WebSocket — ports the existing Python game logic (cards, players, basic strategy, TypeSafe AI)
- **Frontend**: Next.js 19 + React 19 + Tailwind + shadcn/ui + Motion + Three.js + Zustand
- **Communication**: WebSocket for real-time game state, REST for history API
- **API Proxy**: Next.js rewrites proxy `/api/*` to the backend, avoiding CORS issues

## Game Rules

- 6-deck shoe, auto-reshuffle at 25% penetration
- Hi-Lo card counting
- Dealer stands on soft 17
- Blackjack pays 3:2
- Three players: Random, Basic Strategy, AI (TypeSafe)
- Starting balance: $100, minimum bet: $10

## Controls

| Action | Description |
|--------|-------------|
| New Game | Start a fresh session with a new shoe |
| Play Round | Play a single round |
| End Session | Complete the current session (saved to history) |
| Auto Play | Play unlimited rounds automatically (500ms delay) |
| Stop Auto | Halt auto-play |
| +1 / +5 / +10 rounds | Play a fixed number of rounds automatically |

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL (used by Next.js rewrites in `next.config.ts`) |
| `NEXT_PUBLIC_WS_HOST` | `window.location.hostname` | WebSocket host for frontend |
| `NEXT_PUBLIC_WS_PORT` | `8000` | WebSocket port for frontend |
| `TYPESAFE_API_KEY` | — | TypeSafe API key (backend `.env`) |
| `TYPESAFE_API_URL` | — | TypeSafe API endpoint (backend `.env`) |
| `TYPESAFE_MODEL` | `jev-latest` | TypeSafe model (backend `.env`) |

## Frontend Stack

| Library | Purpose |
|---------|---------|
| Next.js 19 | Framework, routing, API rewrites |
| React 19 | UI rendering |
| Zustand | State management (game state, WebSocket, animations) |
| Motion (Framer) | Card spring animations, page transitions |
| Three.js / R3F | 3D chip stacks, card shuffle scene |
| Tailwind CSS 4 | Styling |
| shadcn/ui | Button, Badge, Card, Dialog, Progress, Tabs, Tooltip |

## Project Structure

```
backend/
  main.py              # FastAPI app, WebSocket endpoint, REST API
  game_manager.py      # GameSession wrapping game logic for web
  connection_manager.py # WebSocket broadcast manager
  models.py            # Pydantic models (GameState, PlayerState, etc.)
  database.py          # SQLite persistence (same schema as root)
  rules/               # Game logic ported from root with to_dict()
    cards.py, player.py, game.py, basic_strategy.py, typesafe_ai.py

frontend/
  src/
    app/
      page.tsx         # Landing page ("Play" button)
      game/page.tsx    # Main game board (assembles all components)
      history/page.tsx # Session history browser
    stores/
      gameStore.ts     # Zustand store (game state, WS, chip animation)
    hooks/
      useGameSocket.ts # WebSocket hook with exponential backoff reconnection
    components/
      game/            # PlayingCard, PlayerHand, DealerHand, Scoreboard,
                       # GameControls, BalanceChart, ShoeIndicator,
                       # CardTracker, StatsPanel, LastAction, WinSound,
                       # HeroScene, ChipScene
      ui/              # shadcn/ui primitives
    components3d/      # Three.js scenes (ChipStack3D, CardShuffle)
```
