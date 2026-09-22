"""Blackjack basic strategy for 6-deck, dealer stands on soft 17, double after split allowed."""

_HARD: dict[tuple[int, int], str] = {}

for total in range(4, 9):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'H'

for dc in range(2, 12):
    _HARD[(9, dc)] = 'D' if 3 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _HARD[(10, dc)] = 'D' if 2 <= dc <= 9 else 'H'

for dc in range(2, 12):
    _HARD[(11, dc)] = 'D'

for dc in range(2, 12):
    _HARD[(12, dc)] = 'S' if 4 <= dc <= 6 else 'H'

for total in range(13, 17):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'S' if 2 <= dc <= 6 else 'H'

for total in range(17, 22):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'S'

_SOFT: dict[tuple[int, int], str] = {}

for dc in range(2, 12):
    _SOFT[(2, dc)] = 'D' if 5 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _SOFT[(3, dc)] = 'D' if 5 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _SOFT[(4, dc)] = 'D' if 4 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _SOFT[(5, dc)] = 'D' if 4 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _SOFT[(6, dc)] = 'D' if 3 <= dc <= 6 else 'H'

for dc in range(2, 12):
    if 4 <= dc <= 6:
        _SOFT[(7, dc)] = 'D'
    elif dc in (2, 3, 7, 8, 11):
        _SOFT[(7, dc)] = 'S'
    else:
        _SOFT[(7, dc)] = 'H'

for dc in range(2, 12):
    _SOFT[(8, dc)] = 'S'

for dc in range(2, 12):
    _SOFT[(9, dc)] = 'S'

_PAIRS: dict[tuple[int, int], str] = {}

for dc in range(2, 12):
    _PAIRS[(11, dc)] = 'P'

for dc in range(2, 12):
    _PAIRS[(2, dc)] = 'P' if 2 <= dc <= 7 else 'H'

for dc in range(2, 12):
    _PAIRS[(3, dc)] = 'P' if 2 <= dc <= 7 else 'H'

for dc in range(2, 12):
    _PAIRS[(4, dc)] = 'P' if 5 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _PAIRS[(5, dc)] = 'D' if 2 <= dc <= 9 else 'H'

for dc in range(2, 12):
    _PAIRS[(6, dc)] = 'P' if 2 <= dc <= 6 else 'H'

for dc in range(2, 12):
    _PAIRS[(7, dc)] = 'P' if 2 <= dc <= 7 else 'S'

for dc in range(2, 12):
    _PAIRS[(8, dc)] = 'P'

for dc in range(2, 12):
    if dc in (2, 3, 4, 5, 6, 8, 9):
        _PAIRS[(9, dc)] = 'P'
    else:
        _PAIRS[(9, dc)] = 'S'

for dc in range(2, 12):
    _PAIRS[(10, dc)] = 'S'


def _card_value(card) -> int:
    if hasattr(card, 'value'):
        return card.value
    return 10


def _is_soft(hand) -> bool:
    if hasattr(hand, 'is_soft'):
        return hand.is_soft
    return False


def _hand_total(hand) -> int:
    if hasattr(hand, 'value'):
        return hand.value
    return sum(_card_value(c) for c in hand)


def _is_pair(hand) -> bool:
    cards = hand.cards if hasattr(hand, 'cards') else hand
    if len(cards) != 2:
        return False
    return cards[0].rank == cards[1].rank


def _dealer_upcard_value(dealer_hand) -> int:
    cards = dealer_hand.cards if hasattr(dealer_hand, 'cards') else dealer_hand
    if len(cards) > 1:
        return _card_value(cards[1])
    return _card_value(cards[0])


def get_basic_strategy(hand, dealer_hand) -> str:
    total = _hand_total(hand)
    dealer_upcard = _dealer_upcard_value(dealer_hand)

    if total > 21:
        return 'S'

    if _is_pair(hand):
        cards = hand.cards if hasattr(hand, 'cards') else hand
        pair_value = _card_value(cards[0])
        key = (pair_value, dealer_upcard)
        if key in _PAIRS:
            return _PAIRS[key]

    if _is_soft(hand):
        cards = hand.cards if hasattr(hand, 'cards') else hand
        non_ace_value = sum(_card_value(c) for c in cards) - 11
        key = (non_ace_value, dealer_upcard)
        if key in _SOFT:
            return _SOFT[key]

    key = (total, dealer_upcard)
    if key in _HARD:
        return _HARD[key]

    return 'H'


def get_basic_strategy_action(hand, dealer_hand, can_double=True, can_split=True) -> str:
    rec = get_basic_strategy(hand, dealer_hand)

    if rec == 'P' and can_split:
        return 'split'
    if rec == 'D' and can_double:
        return 'double'
    if rec == 'D':
        return 'hit'
    if rec == 'H':
        return 'hit'
    if rec == 'S':
        return 'stand'

    return 'hit'
