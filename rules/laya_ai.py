import logging
import threading
import laya
from rules.ai_shared import build_bet_state, process_bet_result
from rules.cards import Hand, TrackedDeck

log = logging.getLogger("laya_ai")

_agent = None
_agent_lock = threading.Lock()


def _get_agent():
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                _agent = laya.load("convaiinnovations/laya")
    return _agent


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

    # Approximate dealer bust probabilities by upcard (basic strategy estimates).
    # TODO: Consider adjusting by ±1% based on true_count direction
    # (positive count = slightly lower bust prob, negative = slightly higher).
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

    instructions = f"What is the best blackjack action? Consider: your hand value ({player_hand.value}{'soft' if player_hand.is_soft else 'hard'}), dealer upcard ({dealer_upcard}={dealer_upcard_value}), dealer bust probability ({dealer_bust_pct.get(dealer_upcard_value, 25)}%), true count ({deck.true_count:+.1f}), and shoe composition."

    if not can_double:
        del criteria["double"]
    if not can_split:
        del criteria["split"]

    questions = {
        "action": {
            "type": "choice",
            "instructions": instructions,
            "criteria": criteria,
        }
    }

    agent = _get_agent()
    result = agent.predict(state, questions)

    action_answer = result.get("answers", {}).get("action", {})
    decision = action_answer.get("choice", "stand")
    confidence = action_answer.get("confidence", 0.0)
    log.info("Laya decision: %s (conf: %.2f) | hand=%s vs dealer=%s",
             decision, confidence, player_hand.value, dealer_upcard_value)
    return {
        "decision": decision,
        "confidence": confidence,
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
    state, questions = build_bet_state(
        balance, min_bet, true_count, running_count,
        cards_remaining, cards_dealt, total_cards,
        session_wins, session_losses, opponent_balances, remaining_by_rank,
    )

    agent = _get_agent()
    result = agent.predict(state, questions)

    bet_answer = result.get("answers", {}).get("bet_sizing", {})
    log.info("Laya bet result: %s", bet_answer)

    return process_bet_result(bet_answer, min_bet, balance, true_count, session_wins, session_losses)


def _score_to_bet(score: float, min_bet: int, balance: int, true_count: int = 0) -> int:
    from rules.ai_shared import _score_to_bet as _shared_score_to_bet
    return _shared_score_to_bet(score, min_bet, balance, true_count)


def _build_bet_reasoning(score: float, true_count: int, balance: int, wins: int, losses: int) -> str:
    from rules.ai_shared import _build_bet_reasoning as _shared_build_reasoning
    return _shared_build_reasoning(score, true_count, balance, wins, losses)
