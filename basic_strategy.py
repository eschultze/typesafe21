"""Blackjack basic strategy for 6-deck, dealer stands on soft 17, double after split allowed."""

# Hard totals: key = (player_total, dealer_upcard_value)
# dealer_upcard_value: 2-10, 11=Ace
# Values: 'H'=Hit, 'S'=Stand, 'D'=Double (or Hit if can't double), 'P'=Split
_HARD: dict[tuple[int, int], str] = {}

# 4-8: always hit
for total in range(4, 9):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'H'

# 9: double vs 3-6, else hit
for dc in range(2, 12):
    _HARD[(9, dc)] = 'D' if 3 <= dc <= 6 else 'H'

# 10: double vs 2-9, else hit
for dc in range(2, 12):
    _HARD[(10, dc)] = 'D' if 2 <= dc <= 9 else 'H'

# 11: always double
for dc in range(2, 12):
    _HARD[(11, dc)] = 'D'

# 12: stand vs 4-6, else hit
for dc in range(2, 12):
    _HARD[(12, dc)] = 'S' if 4 <= dc <= 6 else 'H'

# 13-16: stand vs 2-6, else hit
for total in range(13, 17):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'S' if 2 <= dc <= 6 else 'H'

# 17+: always stand
for total in range(17, 22):
    for dc in range(2, 12):
        _HARD[(total, dc)] = 'S'

# Soft totals: key = (non_ace_card_value, dealer_upcard_value)
# non_ace_card_value: 2-10 (value of the non-ace card in a soft hand)
# Soft total = non_ace_value + 11 (Ace counted as 11)
_SOFT: dict[tuple[int, int], str] = {}

# Soft 13 (A+2): double vs 5-6, else hit
for dc in range(2, 12):
    _SOFT[(2, dc)] = 'D' if 5 <= dc <= 6 else 'H'

# Soft 14 (A+3): double vs 5-6, else hit
for dc in range(2, 12):
    _SOFT[(3, dc)] = 'D' if 5 <= dc <= 6 else 'H'

# Soft 15 (A+4): double vs 4-6, else hit
for dc in range(2, 12):
    _SOFT[(4, dc)] = 'D' if 4 <= dc <= 6 else 'H'

# Soft 16 (A+5): double vs 4-6, else hit
for dc in range(2, 12):
    _SOFT[(5, dc)] = 'D' if 4 <= dc <= 6 else 'H'

# Soft 17 (A+6): double vs 3-6, else hit
for dc in range(2, 12):
    _SOFT[(6, dc)] = 'D' if 3 <= dc <= 6 else 'H'

# Soft 18 (A+7): double vs 4-6, stand vs 2,3,7,8,A, hit vs 9,10
for dc in range(2, 12):
    if 4 <= dc <= 6:
        _SOFT[(7, dc)] = 'D'
    elif dc in (2, 3, 7, 8, 11):
        _SOFT[(7, dc)] = 'S'
    else:
        _SOFT[(7, dc)] = 'H'

# Soft 19 (A+8): always stand
for dc in range(2, 12):
    _SOFT[(8, dc)] = 'S'

# Soft 20 (A+9): always stand
for dc in range(2, 12):
    _SOFT[(9, dc)] = 'S'

# Pairs: key = (pair_value, dealer_upcard_value)
# pair_value: 2-10 (value of each card in the pair, A=11)
_PAIRS: dict[tuple[int, int], str] = {}

# Pair of Aces: always split
for dc in range(2, 12):
    _PAIRS[(11, dc)] = 'P'

# Pair of 2s: split vs 2-7, else hit
for dc in range(2, 12):
    _PAIRS[(2, dc)] = 'P' if 2 <= dc <= 7 else 'H'

# Pair of 3s: split vs 2-7, else hit
for dc in range(2, 12):
    _PAIRS[(3, dc)] = 'P' if 2 <= dc <= 7 else 'H'

# Pair of 4s: split vs 5-6, else hit
for dc in range(2, 12):
    _PAIRS[(4, dc)] = 'P' if 5 <= dc <= 6 else 'H'

# Pair of 5s: double vs 2-9, else hit (never split)
for dc in range(2, 12):
    _PAIRS[(5, dc)] = 'D' if 2 <= dc <= 9 else 'H'

# Pair of 6s: split vs 2-6, else hit
for dc in range(2, 12):
    _PAIRS[(6, dc)] = 'P' if 2 <= dc <= 6 else 'H'

# Pair of 7s: split vs 2-7, else stand
for dc in range(2, 12):
    _PAIRS[(7, dc)] = 'P' if 2 <= dc <= 7 else 'S'

# Pair of 8s: always split
for dc in range(2, 12):
    _PAIRS[(8, dc)] = 'P'

# Pair of 9s: split vs 2-6,8-9, stand vs 7,10,A
for dc in range(2, 12):
    if dc in (2, 3, 4, 5, 6, 8, 9):
        _PAIRS[(9, dc)] = 'P'
    else:
        _PAIRS[(9, dc)] = 'S'

# Pair of 10s: always stand (never split)
for dc in range(2, 12):
    _PAIRS[(10, dc)] = 'S'


def _card_value(card) -> int:
    """Get numeric value of a card (A=11, J/Q/K=10)."""
    if hasattr(card, 'value'):
        return card.value
    return 10


def _is_soft(hand) -> bool:
    """Check if a hand is soft (contains an Ace counted as 11)."""
    if hasattr(hand, 'is_soft'):
        return hand.is_soft
    return False


def _hand_total(hand) -> int:
    """Get the hand's total value."""
    if hasattr(hand, 'value'):
        return hand.value
    return sum(_card_value(c) for c in hand)


def _is_pair(hand) -> bool:
    """Check if the hand is a pair."""
    cards = hand.cards if hasattr(hand, 'cards') else hand
    if len(cards) != 2:
        return False
    return _card_value(cards[0]) == _card_value(cards[1])


def _dealer_upcard_value(dealer_hand) -> int:
    """Get the dealer's upcard value (Ace=11)."""
    cards = dealer_hand.cards if hasattr(dealer_hand, 'cards') else dealer_hand
    if len(cards) > 1:
        return _card_value(cards[1])
    return _card_value(cards[0])


def get_basic_strategy(hand, dealer_hand) -> str:
    """Return basic strategy recommendation: 'H', 'S', 'D', or 'P'.
    
    Args:
        hand: Player's hand (Hand object or list of cards)
        dealer_hand: Dealer's hand (Hand object or list of cards)
    
    Returns:
        'H' = Hit, 'S' = Stand, 'D' = Double (or Hit if can't double), 'P' = Split
    """
    total = _hand_total(hand)
    dealer_upcard = _dealer_upcard_value(dealer_hand)

    if total > 21:
        return 'S'

    # Check pairs first (only with 2 cards)
    if _is_pair(hand):
        cards = hand.cards if hasattr(hand, 'cards') else hand
        pair_value = _card_value(cards[0])
        key = (pair_value, dealer_upcard)
        if key in _PAIRS:
            result = _PAIRS[key]
            return result

    # Check soft hands
    if _is_soft(hand):
        cards = hand.cards if hasattr(hand, 'cards') else hand
        non_ace_value = sum(_card_value(c) for c in cards) - 11
        key = (non_ace_value, dealer_upcard)
        if key in _SOFT:
            return _SOFT[key]

    # Hard totals
    key = (total, dealer_upcard)
    if key in _HARD:
        return _HARD[key]

    return 'H'


def get_basic_strategy_action(hand, dealer_hand, can_double=True, can_split=True) -> str:
    """Return the actionable decision: 'hit', 'stand', 'double', or 'split'.
    
    Respects can_double and can_split constraints.
    """
    rec = get_basic_strategy(hand, dealer_hand)

    if rec == 'P' and can_split:
        return 'split'
    if rec == 'D' and can_double:
        return 'double'
    if rec == 'D':
        return 'hit'  # Can't double, so hit instead
    if rec == 'H':
        return 'hit'
    if rec == 'S':
        return 'stand'

    return 'hit'


def describe_recommendation(hand, dealer_hand, can_double=True, can_split=True) -> str:
    """Return a human-readable description of the basic strategy recommendation."""
    rec = get_basic_strategy(hand, dealer_hand)
    total = _hand_total(hand)
    soft = _is_soft(hand)
    pair = _is_pair(hand)

    labels = {'H': 'Hit', 'S': 'Stand', 'D': 'Double', 'P': 'Split'}
    label = labels.get(rec, 'Hit')

    parts = [label]
    if soft:
        parts.append(f"soft {total}")
    else:
        parts.append(f"hard {total}")

    if pair:
        cards = hand.cards if hasattr(hand, 'cards') else hand
        pair_val = _card_value(cards[0])
        names = {11: 'Aces', 10: '10s', 9: '9s', 8: '8s', 7: '7s',
                 6: '6s', 5: '5s', 4: '4s', 3: '3s', 2: '2s'}
        parts.append(f"pair of {names.get(pair_val, str(pair_val))}")

    # Get the actual dealer card rank, not just the value
    dealer_cards = dealer_hand.cards if hasattr(dealer_hand, 'cards') else dealer_hand
    if len(dealer_cards) > 1:
        dealer_card = dealer_cards[1]
    else:
        dealer_card = dealer_cards[0]
    dealer_name = dealer_card.rank if hasattr(dealer_card, 'rank') else ('A' if _card_value(dealer_card) == 11 else str(_card_value(dealer_card)))
    parts.append(f"vs dealer {dealer_name}")

    if rec == 'D' and not can_double:
        parts.append("(can't double, hit instead)")

    return " ".join(parts)
