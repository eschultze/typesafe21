import os
import time

import requests
from dotenv import load_dotenv
from rules.cards import Hand, TrackedDeck

load_dotenv()

API_URL = os.environ.get("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
MODEL = os.environ.get("TYPESAFE_MODEL", "jev-latest")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

MAX_RETRIES = 3
TIMEOUT = 15


def _api_request(payload: dict) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise


def get_ai_decision(
    player_hand: Hand,
    dealer_hand: Hand,
    deck: TrackedDeck,
    session_wins: int = 0,
    session_losses: int = 0,
    can_double: bool = True,
    can_split: bool = True,
) -> dict:
    cards = [str(card) for card in player_hand.cards]
    ranks = [card.rank for card in player_hand.cards]
    is_pair = len(player_hand.cards) == 2 and ranks[0] == ranks[1]

    dealer_cards = [str(card) for card in dealer_hand.cards]
    dealer_upcard = dealer_cards[1] if len(dealer_cards) > 1 else dealer_cards[0]
    dealer_upcard_value = (
        dealer_hand.cards[1].value if len(dealer_hand.cards) > 1 else dealer_hand.cards[0].value
    )

    remaining = deck.get_remaining_by_rank()

    dealer_bust_pct = {
        2: 35, 3: 37, 4: 40, 5: 42, 6: 42,
        7: 26, 8: 24, 9: 23, 10: 23, 11: 17,
    }

    state = {
        "player_hand": cards,
        "player_value": player_hand.value,
        "is_soft_hand": player_hand.is_soft,
        "is_pair": is_pair,
        "num_cards": len(player_hand.cards),
        "dealer_upcard": dealer_upcard,
        "dealer_upcard_value": dealer_upcard_value,
        "dealer_bust_probability_pct": dealer_bust_pct.get(dealer_upcard_value, 25),
        "deck_cards_remaining": deck.remaining,
        "cards_dealt_this_shoe": deck.get_cards_since_reshuffle(),
        "shoe_penetration_pct": round((deck.get_cards_since_reshuffle() / deck.total_cards) * 100, 1),
        "running_count": deck.running_count,
        "true_count": deck.true_count,
        "aces_remaining": remaining.get("A", 0),
        "tens_remaining": remaining.get("10", 0) + remaining.get("J", 0) + remaining.get("Q", 0) + remaining.get("K", 0),
        "session_wins": session_wins,
        "session_losses": session_losses,
        "can_double": can_double,
        "can_split": can_split,
    }

    criteria = {
        "hit": {
            "what": "Take another card to improve your hand",
            "not_for": "Do not use when you should stand on a strong hand, double for value, or split a pair",
            "examples": [
                "Hard 12 vs dealer 10 — need to improve",
                "Soft 16 (A+5) vs dealer 7 — soft hand under 18",
                "Hard 8 vs any dealer — always hit 8 or less",
            ],
        },
        "stand": {
            "what": "Keep your current hand, do not take more cards",
            "not_for": "Do not use when your hand is too low to win or when doubling/splitting offers better value",
            "examples": [
                "Hard 17 vs dealer 6 — strong hand, dealer likely busts",
                "Soft 18 (A+7) vs dealer 3 — good enough against weak upcard",
                "Hard 14 vs dealer 5 — stand, dealer likely busts",
            ],
        },
        "double": {
            "what": "Double your bet and receive exactly one more card, then stand",
            "not_for": "Do not use with weak hands or when dealer has strong upcard. Only available as first two cards",
            "examples": [
                "Hard 11 vs dealer 6 — excellent doubling opportunity",
                "Hard 10 vs dealer 4 — strong position to double",
                "Soft 18 (A+7) vs dealer 5 — edge to double",
            ],
        },
        "split": {
            "what": "Split your pair into two separate hands, each with its own bet",
            "not_for": "Do not split 10s or 5s. Only available with pairs as first two cards",
            "examples": [
                "A+A — always split Aces for two chances at 21",
                "8+8 vs dealer 5 — split 8s to escape a 16",
                "6+6 vs dealer 6 — split 6s against weak dealer",
            ],
        },
        "other": "None of the above actions fits this situation",
    }

    instructions = f"What is the best blackjack action? Consider: your hand value ({player_hand.value}{'soft' if player_hand.is_soft else 'hard'}), dealer upcard ({dealer_upcard}={dealer_upcard_value}), dealer bust probability ({dealer_bust_pct.get(dealer_upcard_value, 25)}%), true count ({deck.true_count:+d}), and shoe composition."

    if not can_double:
        del criteria["double"]
    if not can_split:
        del criteria["split"]

    payload = {
        "state": state,
        "model": MODEL,
        "questions": {
            "action": {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria,
            }
        },
    }

    data = _api_request(payload)

    action_answer = data.get("answers", {}).get("action", {})
    return {
        "decision": action_answer.get("choice", "stand"),
        "confidence": action_answer.get("confidence", 0.0),
        "probabilities": action_answer.get("probabilities", {}),
    }


def get_ai_bet(
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

    payload = {
        "state": state,
        "model": MODEL,
        "questions": {
            "bet_sizing": {
                "type": "score",
                "instructions": f"How aggressively should you bet this hand? True count is {true_count:+d}. Balance is ${balance}. {aggressive_hint}",
                "criteria": [
                    "Minimum bet — no edge, neutral or negative count",
                    "Small bet — mild edge, true count +1 to +2",
                    "Medium bet — solid edge, true count +3 to +4",
                    "Large bet — strong edge, true count +5 to +6",
                    "Maximum bet — massive edge, true count +7 or higher",
                ],
            }
        },
    }

    data = _api_request(payload)

    bet_answer = data.get("answers", {}).get("bet_sizing", {})

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
