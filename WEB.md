# TypeSafe21 — Web Version

AI-powered Blackjack with three players, one shoe, and zero mercy.

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env .env   # or create with TYPESAFE_API_KEY, TYPESAFE_API_URL, TYPESAFE_MODEL
python3 main.py
```

Backend runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

## Architecture

- **Backend**: FastAPI + WebSocket — ports the existing Python game logic (cards, players, basic strategy, TypeSafe AI)
- **Frontend**: Next.js 15 + Tailwind + shadcn/ui + Motion + Three.js + Zustand

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
| New Game | Start a fresh session |
| Continue | Resume last incomplete session |
| Play Round | Play a single round |
| Auto Play | Play N rounds automatically (500ms delay) |
| Stop | Halt auto-play |
