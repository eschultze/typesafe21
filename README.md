# Typesafe 21

A terminal-based blackjack simulator where three players with different strategies compete head-to-head, powered by [TypeSafe System One](https://docs.typesafe.ai).

## Quick Start

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

## Game Modes

- **New Game** — Start a fresh session
- **Continue Previous Game** — Resume an incomplete session
- **View History** — Browse past sessions and round details
- **Auto-play** — Enter a number of rounds to play automatically (0.5s delay between rounds)

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

## File Structure

```
typesafe21/
  main.py              # Entry point
  game.py              # Round logic, dealing, payouts, split handling
  player.py            # Player classes (Random, BasicStrategy, AI)
  typesafe_ai.py       # TypeSafe API integration (Choice + Score)
  basic_strategy.py    # Basic strategy lookup (displayed for reference)
  cards.py             # Card, Hand, Deck, TrackedDeck
  database.py          # SQLite persistence
  cash_register.mp3    # Sound effect on AI win
  requirements.txt     # Dependencies
  game_history.db      # Created at runtime
  ui/
    app.py             # Textual app, screen routing
    styles.tss         # Textual CSS
    screens/
      game.py          # Main game screen with state machine
      menu.py          # Menu screen
      summary.py       # Session summary
      history.py       # Session history (modal)
    widgets/
      card_art.py      # ASCII card rendering (5-line box art)
      dealer_panel.py  # Dealer hand display
      players_panel.py # Player hands with card art + loading spinner
      scoreboard_panel.py # Balances, W/L, win rate
      deck_panel.py    # Deck remaining, true count, running count
      balance_chart.py # Custom bar chart with Y-axis labels
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.
