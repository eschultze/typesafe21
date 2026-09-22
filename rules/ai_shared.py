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

    if true_count >= 5:
        aggressive_hint = "Massive edge. Bet the maximum."
    elif true_count >= 3:
        aggressive_hint = "Strong edge. Bet large."
    elif true_count >= 1:
        aggressive_hint = "Mild edge. Bet moderately."
    elif true_count == 0:
        aggressive_hint = "No edge. Bet minimum."
    else:
        aggressive_hint = "Negative count. Bet minimum and wait."

    questions = {
        "bet_sizing": {
            "type": "score",
            "instructions": f"How aggressively should you bet this hand? True count is {true_count:+.1f}. Balance is ${balance}. {aggressive_hint}",
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
    weighted_sum = 0.0
    for level_str, prob in probabilities.items():
        try:
            weighted_sum += int(level_str) * prob
        except (ValueError, TypeError):
            continue

    bet = _score_to_bet(weighted_sum, min_bet, balance, true_count)
    reasoning = _build_bet_reasoning(weighted_sum, true_count, balance, session_wins, session_losses)

    return {
        "bet": bet,
        "score": weighted_sum,
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
