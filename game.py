from __future__ import annotations

from dataclasses import dataclass, field

from cards import TrackedDeck, Hand, Card
from player import Player, AIPlayer, BasicStrategyPlayer


@dataclass
class BetInfo:
    name: str
    bet: int
    is_ai: bool = False
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class PlayerHandResult:
    player_index: int
    name: str
    hand: Hand
    result: str | None = None
    is_ai: bool = False
    confidence: float = 0.0
    decision: str = ""
    bet: int = 0
    balance: int = 0


@dataclass
class RoundResult:
    session_id: int
    round_number: int
    dealer_hand: Hand
    hands: list[PlayerHandResult] = field(default_factory=list)
    ai_confidence: float = 0.0
    ai_decision: str = ""


def determine_winner(player_hand: Hand, dealer_hand: Hand) -> str:
    if player_hand.is_bust:
        return "lose"
    if dealer_hand.is_bust:
        return "win"
    if player_hand.is_blackjack and not dealer_hand.is_blackjack:
        return "win"
    if dealer_hand.is_blackjack and not player_hand.is_blackjack:
        return "lose"
    if player_hand.value > dealer_hand.value:
        return "win"
    elif player_hand.value < dealer_hand.value:
        return "lose"
    else:
        return "push"


def get_payout_multiplier(result: str, player_hand: Hand) -> float:
    if result == "win" and player_hand.is_blackjack:
        return 1.5
    return 1.0


def do_bets(
    players: list[Player],
    deck: TrackedDeck,
) -> list[BetInfo]:
    bets: list[BetInfo] = []
    opponent_balances = [p.balance for p in players if not isinstance(p, AIPlayer)]

    for player in players:
        if not player.can_play():
            continue

        if isinstance(player, AIPlayer):
            bet = player.decide_bet(deck, opponent_balances=opponent_balances)
        else:
            bet = player.decide_bet(deck)
        player.place_bet(bet)

        info = BetInfo(
            name=player.name,
            bet=bet,
            is_ai=isinstance(player, AIPlayer),
        )
        if isinstance(player, AIPlayer):
            bet_info = player.last_bet_info
            info.reasoning = bet_info.get("reasoning", "")
            info.confidence = bet_info.get("confidence", 0.0)

        bets.append(info)

    return bets


def deal_initial(
    players: list[Player],
    deck: TrackedDeck,
) -> Hand:
    dealer_hand = Hand()

    for p in players:
        p.reset_hand()
    dealer_hand.clear()

    # Deal one shared hand, then copy it to all players
    shared_cards: list[Card] = []
    for _ in range(2):
        card = deck.deal()
        shared_cards.append(card)
        deck.record_played(card)

    for p in players:
        if p.current_bet > 0:
            for card in shared_cards:
                p.hand.add_card(Card(card.rank, card.suit))

    # Dealer gets their own cards
    for _ in range(2):
        card = deck.deal()
        dealer_hand.add_card(card)
        deck.record_played(card)

    return dealer_hand


def play_player_hand(
    player: Player,
    deck: TrackedDeck,
    dealer_hand: Hand,
) -> tuple[str, float, str]:
    decision = ""
    confidence = 0.0
    last_ai_decision = ""
    needs_extra_args = isinstance(player, (AIPlayer, BasicStrategyPlayer))

    cards_dealt = len(player.hand.cards)
    can_double = cards_dealt == 2
    can_split = (
        cards_dealt == 2
        and player.hand.cards[0].rank == player.hand.cards[1].rank
    )

    while True:
        if player.hand.value >= 21:
            break

        if needs_extra_args:
            decision = player.make_decision(
                dealer_hand, deck, can_double=can_double, can_split=can_split
            )
            confidence = player.last_confidence
            last_ai_decision = player.last_decision
        else:
            decision = player.make_decision(dealer_hand, deck)

        if decision == "hit":
            card = deck.deal()
            player.hand.add_card(card)
            deck.record_played(card)
            can_double = False
            can_split = False
        elif decision == "double" and can_double:
            additional = min(player.current_bet, player.balance)
            player.balance -= additional
            player.current_bet += additional
            card = deck.deal()
            player.hand.add_card(card)
            deck.record_played(card)
            break
        elif decision == "split" and can_split:
            # Split: create two hands, play each independently
            card1 = player.hand.cards[0]
            card2 = player.hand.cards[1]
            original_bet = player.current_bet
            splitting_aces = card1.rank == "A"

            # Create first hand
            hand1 = Hand()
            hand1.add_card(card1)
            card = deck.deal()
            hand1.add_card(card)
            deck.record_played(card)

            # Create second hand
            hand2 = Hand()
            hand2.add_card(card2)
            card = deck.deal()
            hand2.add_card(card)
            deck.record_played(card)

            # Play first hand
            player.hand = hand1
            player.current_bet = original_bet
            if splitting_aces:
                # Split Aces get only one card each, stand immediately
                decision1, conf1, dec1 = "", 0.0, ""
            else:
                decision1, conf1, dec1 = _play_hand_loop(player, deck, dealer_hand, needs_extra_args)
            player.split_hands.append((hand1, original_bet, dec1, conf1))

            # Play second hand (return this one)
            player.hand = hand2
            player.current_bet = original_bet
            if splitting_aces:
                decision2, conf2, dec2 = "", 0.0, ""
            else:
                decision2, conf2, dec2 = _play_hand_loop(player, deck, dealer_hand, needs_extra_args)
            return decision2, conf2, dec2
        else:
            break

    return decision, confidence, last_ai_decision


def _play_hand_loop(
    player: Player,
    deck: TrackedDeck,
    dealer_hand: Hand,
    needs_extra_args: bool,
) -> tuple[str, float, str]:
    """Play out a single hand to completion (used for split hands)."""
    decision = ""
    confidence = 0.0
    last_ai_decision = ""

    while True:
        if player.hand.value >= 21:
            break

        if needs_extra_args:
            decision = player.make_decision(
                dealer_hand, deck, can_double=False, can_split=False
            )
            confidence = player.last_confidence
            last_ai_decision = player.last_decision
        else:
            decision = player.make_decision(dealer_hand, deck)

        if decision == "hit":
            card = deck.deal()
            player.hand.add_card(card)
            deck.record_played(card)
        else:
            break

    return decision, confidence, last_ai_decision


def play_dealer(dealer_hand: Hand, deck: TrackedDeck) -> None:
    while dealer_hand.value < 17:
        card = deck.deal()
        dealer_hand.add_card(card)
        deck.record_played(card)


def settle_round(
    players: list[Player],
    dealer_hand: Hand,
    session_id: int,
    round_number: int,
) -> RoundResult:
    result = RoundResult(
        session_id=session_id,
        round_number=round_number,
        dealer_hand=dealer_hand,
    )

    for i, player in enumerate(players):
        if player.current_bet == 0 and not player.split_hands:
            continue

        is_ai = isinstance(player, (AIPlayer, BasicStrategyPlayer))

        # Settle split hands first
        for split_hand, split_bet, split_dec, split_conf in player.split_hands:
            # Temporarily set player hand/bet for settlement
            orig_hand = player.hand
            orig_bet = player.current_bet
            player.hand = split_hand
            player.current_bet = split_bet

            winner = determine_winner(split_hand, dealer_hand)
            multiplier = get_payout_multiplier(winner, split_hand)
            player.record_result(winner)

            if winner == "win":
                player.win_bet(multiplier)
            elif winner == "push":
                player.push_bet()
            else:
                player.lose_bet()

            hand_result = PlayerHandResult(
                player_index=i + 1,
                name=player.name,
                hand=split_hand,
                result=winner,
                is_ai=is_ai,
                confidence=split_conf,
                decision=split_dec if is_ai else "",
                bet=split_bet,
                balance=player.balance,
            )
            result.hands.append(hand_result)

            # Restore original hand/bet
            player.hand = orig_hand
            player.current_bet = orig_bet

        # Settle main hand (if any bet remains)
        if player.current_bet > 0:
            winner = determine_winner(player.hand, dealer_hand)
            multiplier = get_payout_multiplier(winner, player.hand)
            player.record_result(winner)

            if winner == "win":
                player.win_bet(multiplier)
            elif winner == "push":
                player.push_bet()
            else:
                player.lose_bet()

            conf = player.last_confidence if is_ai else 0.0
            dec = player.last_decision if is_ai else ""

            hand_result = PlayerHandResult(
                player_index=i + 1,
                name=player.name,
                hand=player.hand,
                result=winner,
                is_ai=is_ai,
                confidence=conf,
                decision=dec,
                bet=player.current_bet,
                balance=player.balance,
            )
            result.hands.append(hand_result)

            if is_ai:
                result.ai_confidence = conf
                result.ai_decision = dec

    return result
