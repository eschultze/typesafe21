_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Pip values used to score a single drawn card. Aces are intentionally absent:
# a drawn ace can always be counted as 1, so it can never bust a hand.
_DRAW_VALUES: dict[str, int] = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
    "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10,
}


def chance_to_bust_on_next_draw(
    hand_value: int,
    is_soft: bool,
    remaining_by_rank: dict[str, int],
) -> float:
    """Percent chance (0.0-100.0) that the next drawn card busts the hand.

    Pure board state: derived only from the current hand value and the
    remaining shoe composition, with no strategic framing.

    - Soft hands cannot bust on a single draw, because the ace can always be
      counted as 1. A drawn ace can never bust for the same reason, so aces
      are excluded from the busting-card count.
    - A hand only busts when a card with pip value strictly greater than
      ``21 - hand_value`` remains in the shoe.
    """
    total_remaining = sum(remaining_by_rank.values())
    if total_remaining <= 0 or is_soft:
        return 0.0

    threshold = 21 - hand_value
    if threshold >= 10:
        return 0.0

    busting = sum(
        remaining_by_rank.get(rank, 0)
        for rank, value in _DRAW_VALUES.items()
        if value > threshold
    )
    return round(busting / total_remaining * 100, 1)


def dealer_bust_probability(
    upcard_value: int,
    unseen_by_rank: dict[str, int],
    hit_soft_17: bool = True,
) -> float:
    """Percent chance (0.0-100.0) that the dealer busts, from the unseen shoe.

    Pure board state: enumerates every dealer draw sequence without
    replacement over the cards the player cannot see — the remaining shoe plus
    the dealer's unknown hole card. ``unseen_by_rank`` must therefore include
    the hole card and exclude the upcard (which the player can see).

    ``upcard_value`` is the face value of the upcard (an ace is 11). Memoized
    on the remaining composition, so each call is a small dynamic program
    rather than an exponential walk.
    """
    counts = tuple(unseen_by_rank.get(rank, 0) for rank in _RANKS)
    memo: dict[tuple[int, int, tuple[int, ...]], float] = {}

    def rec(total: int, aces: int, counts: tuple[int, ...]) -> float:
        key = (total, aces, counts)
        cached = memo.get(key)
        if cached is not None:
            return cached

        soft = aces > 0 and total + 10 <= 21
        best = total + (10 if soft else 0)
        if best > 21:
            result = 1.0
        elif best >= 17 and not (hit_soft_17 and soft and best == 17):
            result = 0.0
        else:
            available = sum(counts)
            if available == 0:
                result = 0.0
            else:
                bust = 0.0
                for i, rank in enumerate(_RANKS):
                    count = counts[i]
                    if not count:
                        continue
                    if rank == "A":
                        next_total, next_aces = total + 1, aces + 1
                    else:
                        next_total, next_aces = total + _DRAW_VALUES[rank], aces
                    next_counts = list(counts)
                    next_counts[i] -= 1
                    bust += (count / available) * rec(
                        next_total, next_aces, tuple(next_counts)
                    )
                result = bust

        memo[key] = result
        return result

    total, aces = (1, 1) if upcard_value == 11 else (upcard_value, 0)
    return round(rec(total, aces, counts) * 100, 1)


def build_bet_state(
    balance: int,
    min_bet: int,
    true_count: int,
    running_count: int,
    cards_remaining: int,
    cards_dealt: int,
    total_cards: int,
    session_wins: int = 0,
    session_losses: int = 0,
    opponent_balances: list[int] | None = None,
    remaining_by_rank: dict[str, int] | None = None,
) -> dict:
    if remaining_by_rank:
        high_cards = (remaining_by_rank.get("10", 0) + remaining_by_rank.get("J", 0) +
                      remaining_by_rank.get("Q", 0) + remaining_by_rank.get("K", 0) +
                      remaining_by_rank.get("A", 0))
        low_cards = sum(remaining_by_rank.get(r, 0) for r in ["2", "3", "4", "5", "6"])
        total_remaining = sum(remaining_by_rank.values())
    else:
        high_cards = 0
        low_cards = 0
        total_remaining = 1

    state = {
        "balance": balance,
        "min_bet": min_bet,
        "true_count": true_count,
        "running_count": running_count,
        "cards_remaining": cards_remaining,
        "cards_dealt": cards_dealt,
        "total_cards": total_cards,
        "shoe_penetration_pct": round((cards_dealt / total_cards) * 100, 1),
        "session_wins": session_wins,
        "session_losses": session_losses,
        "win_loss_ratio": f"{session_wins}-{session_losses}",
        "opponent_balances": opponent_balances or [],
        "remaining_by_rank": remaining_by_rank or {},
        "high_cards_remaining": high_cards,
        "low_cards_remaining": low_cards,
        "high_card_ratio": round(high_cards / total_remaining, 3) if total_remaining > 0 else 0.5,
    }

    questions = {
        "bet_sizing": {
            "type": "score",
            "instructions": (
                f"This is a game of blackjack (6-deck shoe, dealer hits soft 17, "
                f"blackjack pays 3:2). How aggressively should you bet this hand? "
                f"True count is {true_count:+.1f}. Balance is ${balance}."
            ),
            "criteria": [
                "Minimum bet — no edge, neutral or negative count",
                "Small bet — mild edge, true count +1 to +2",
                "Medium bet — solid edge, true count +3 to +4",
                "Large bet — strong edge, true count +5 to +6",
                "Maximum bet — massive edge, true count +7 or higher",
            ],
        }
    }

    return state, questions


def process_bet_result(bet_answer: dict, min_bet: int, balance: int, true_count: int, session_wins: int, session_losses: int) -> dict:
    probabilities = bet_answer.get("probabilities", {})
    # The API returns `score` as the probability-weighted mean of the level
    # numbers (0..4), which is exactly what the bet mapping expects. Fall back
    # to computing it from `probabilities` if it is absent.
    score = bet_answer.get("score")
    if score is None:
        score = 0.0
        for level_str, prob in probabilities.items():
            try:
                score += int(level_str) * prob
            except (ValueError, TypeError):
                continue

    bet = _score_to_bet(score, min_bet, balance, true_count)
    reasoning = _build_bet_reasoning(score, true_count, balance, session_wins, session_losses)

    return {
        "bet": bet,
        "score": score,
        "confidence": bet_answer.get("confidence", 0.5),
        "probabilities": probabilities,
        "reasoning": reasoning,
    }


def _score_to_bet(score: float, min_bet: int, balance: int, true_count: int = 0) -> int:
    # Note: true_count parameter is reserved for future use (e.g., adjusting bet spread)
    if balance < min_bet:
        return 0
    bet_pcts = [0.05, 0.15, 0.25, 0.35, 0.50]
    idx = int(round(score))
    idx = max(0, min(idx, len(bet_pcts) - 1))
    bet = int(balance * bet_pcts[idx])
    bet = max(min_bet, bet)
    bet = min(bet, balance)
    return bet


def _build_bet_reasoning(score: float, true_count: int, balance: int, wins: int, losses: int) -> str:
    parts = []
    bet_pcts = [5, 15, 25, 35, 50]
    idx = int(round(score))
    idx = max(0, min(idx, len(bet_pcts) - 1))
    pct = bet_pcts[idx]

    if score <= 0.5:
        parts.append(f"No edge - betting {pct}% of balance")
    elif score <= 1.5:
        parts.append(f"Mild edge - betting {pct}% of balance")
    elif score <= 2.5:
        parts.append(f"Solid edge - betting {pct}% of balance")
    elif score <= 3.5:
        parts.append(f"Strong edge - betting {pct}% of balance")
    else:
        parts.append(f"Massive edge - betting {pct}% of balance")

    if true_count > 0:
        edge = true_count * 0.5
        parts.append(f"TC +{true_count} → edge ~{edge:.1f}%")
    elif true_count < 0:
        parts.append(f"TC {true_count} → no player edge")

    if balance < 50:
        parts.append("Low bankroll")
    elif balance > 150:
        parts.append("Healthy bankroll")

    return ". ".join(parts)
