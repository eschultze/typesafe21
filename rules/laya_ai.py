import logging
import threading
import time
import laya
from rules.ai_shared import (
    build_bet_state,
    process_bet_result,
    chance_to_bust_on_next_draw,
    dealer_bust_probability,
)
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

    # Index 0 is the face-up card. Index 1 is the hole card and is hidden from
    # the UI (see GameSession.get_state), so the player only knows cards[0].
    dealer_cards = [str(card) for card in dealer_hand.cards]
    dealer_upcard = dealer_cards[0] if dealer_cards else "?"
    dealer_upcard_value = dealer_hand.cards[0].value if dealer_hand.cards else 0

    remaining = deck.get_remaining_by_rank()

    # The dealer's hole card has been dealt (so it is absent from `remaining`)
    # but is unknown to the player, so add it back to the pool the dealer bust
    # probability draws from. The upcard is visible and already excluded.
    unseen = dict(remaining)
    if len(dealer_hand.cards) > 1:
        hole_rank = dealer_hand.cards[1].rank
        unseen[hole_rank] = unseen.get(hole_rank, 0) + 1

    dealer_bust = dealer_bust_probability(dealer_upcard_value, unseen)

    state = {
        "player_hand": cards,
        "player_value": player_hand.value,
        "is_soft_hand": player_hand.is_soft,
        "is_pair": is_pair,
        "num_cards": len(player_hand.cards),
        "dealer_upcard": dealer_upcard,
        "dealer_upcard_value": dealer_upcard_value,
        "dealer_bust_probability_pct": dealer_bust,
        "our_chance_to_bust_on_next_draw": chance_to_bust_on_next_draw(
            player_hand.value, player_hand.is_soft, remaining
        ),
        "deck_cards_remaining": deck.remaining,
        "cards_dealt_this_shoe": deck.get_cards_since_reshuffle(),
        "shoe_penetration_pct": round((deck.get_cards_since_reshuffle() / deck.total_cards) * 100, 1),
        "running_count": deck.running_count,
        "true_count": deck.true_count,
        "remaining_by_rank": remaining,
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
    }

    instructions = f"What is the best blackjack action? Consider: your hand value ({player_hand.value}{'soft' if player_hand.is_soft else 'hard'}), dealer upcard ({dealer_upcard}={dealer_upcard_value}), dealer bust probability ({dealer_bust}%), true count ({deck.true_count:+.1f}), and shoe composition."

    # Only offer the actions that are actually legal this turn. There is no
    # "other" option: the four actions cover every legal move, and an
    # out-of-vocabulary answer is handled explicitly below rather than
    # silently falling through.
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
    started = time.perf_counter()
    result = agent.predict(state, questions)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)

    action_answer = result.get("answers", {}).get("action", {})
    decision = action_answer.get("choice", "stand")
    if decision not in criteria:
        # The model answered outside the legal set; standing is the safe,
        # non-destructive fallback.
        decision = "stand"
    confidence = action_answer.get("confidence", 0.0)
    log.info("Laya decision: %s (conf: %.2f, %.1fms) | hand=%s vs dealer=%s",
             decision, confidence, latency_ms, player_hand.value, dealer_upcard_value)
    return {
        "decision": decision,
        "confidence": confidence,
        "probabilities": action_answer.get("probabilities", {}),
        "latency_ms": latency_ms,
        "tokens": 0,
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
    started = time.perf_counter()
    result = agent.predict(state, questions)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)

    bet_answer = result.get("answers", {}).get("bet_sizing", {})
    log.info("Laya bet result: %s (%.1fms)", bet_answer, latency_ms)

    out = process_bet_result(bet_answer, min_bet, balance, true_count, session_wins, session_losses)
    out["latency_ms"] = latency_ms
    out["tokens"] = 0
    return out


def _score_to_bet(score: float, min_bet: int, balance: int, true_count: int = 0) -> int:
    from rules.ai_shared import _score_to_bet as _shared_score_to_bet
    return _shared_score_to_bet(score, min_bet, balance, true_count)


def _build_bet_reasoning(score: float, true_count: int, balance: int, wins: int, losses: int) -> str:
    from rules.ai_shared import _build_bet_reasoning as _shared_build_reasoning
    return _shared_build_reasoning(score, true_count, balance, wins, losses)
