import random
from enum import Enum


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Card:
    def __init__(self, rank: str, suit: Suit):
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        if self.rank in ("J", "Q", "K"):
            return 10
        elif self.rank == "A":
            return 11
        else:
            return int(self.rank)

    def to_dict(self) -> dict:
        return {"rank": self.rank, "suit": self.suit.value, "value": self.value}

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()


class Hand:
    def __init__(self):
        self.cards: list[Card] = []
        self._value_cache: int | None = None
        self._soft_cache: bool | None = None

    def add_card(self, card: Card):
        self.cards.append(card)
        self._value_cache = None
        self._soft_cache = None

    @property
    def value(self) -> int:
        if self._value_cache is not None:
            return self._value_cache
        total = sum(card.value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        self._value_cache = total
        return total

    @property
    def is_soft(self) -> bool:
        if self._soft_cache is not None:
            return self._soft_cache
        raw_total = sum(card.value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == "A")
        if aces == 0 or raw_total > 21:
            self._soft_cache = False
            return False
        adjusted = raw_total
        temp_aces = aces
        while adjusted > 21 and temp_aces:
            adjusted -= 10
            temp_aces -= 1
        result = temp_aces > 0
        self._soft_cache = result
        return result

    @property
    def num_aces(self) -> int:
        return sum(1 for card in self.cards if card.rank == "A")

    @property
    def is_bust(self) -> bool:
        return self.value > 21

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value == 21

    def clear(self):
        self.cards.clear()
        self._value_cache = None
        self._soft_cache = None

    def to_dict(self) -> dict:
        return {
            "cards": [c.to_dict() for c in self.cards],
            "value": self.value,
            "is_soft": self.is_soft,
            "is_bust": self.is_bust,
            "is_blackjack": self.is_blackjack,
        }

    def __str__(self) -> str:
        return " ".join(str(card) for card in self.cards)

    def __repr__(self) -> str:
        return self.__str__()


class TrackedDeck:
    RESHUFFLE_THRESHOLD = 0.25

    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.total_cards = num_decks * 52
        self.cards: list[Card] = []
        self.played_cards: list[Card] = []
        self.played_ranks: dict[str, int] = {r: 0 for r in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]}
        self.running_count = 0
        self._remaining_by_rank_cache: dict[str, int] | None = None
        self._build()
        self.shuffle()

    def _build(self):
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in Suit
            for rank in ranks
        ]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if len(self.cards) <= self.total_cards * self.RESHUFFLE_THRESHOLD:
            self._reshuffle()
        return self.cards.pop()

    def _reshuffle(self):
        self.cards.extend(self.played_cards)
        self.played_cards.clear()
        self.played_ranks = {r: 0 for r in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]}
        self.running_count = 0
        self._remaining_by_rank_cache = None
        self.shuffle()

    def record_played(self, card: Card):
        self.played_cards.append(card)
        self.played_ranks[card.rank] += 1
        self.running_count += self._hi_lo_value(card)
        self._remaining_by_rank_cache = None

    def _hi_lo_value(self, card: Card) -> int:
        if card.value >= 10 or card.rank == "A":
            return -1
        elif card.value <= 6:
            return 1
        return 0

    @property
    def true_count(self) -> int:
        decks_remaining = max(1, len(self.cards) / 52)
        return round(self.running_count / decks_remaining)

    @property
    def remaining(self) -> int:
        return len(self.cards)

    def get_remaining_by_rank(self) -> dict[str, int]:
        if self._remaining_by_rank_cache is not None:
            return self._remaining_by_rank_cache
        total_by_rank = {r: self.num_decks * 4 for r in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]}
        for rank, count in self.played_ranks.items():
            total_by_rank[rank] -= count
        self._remaining_by_rank_cache = total_by_rank
        return total_by_rank

    def get_cards_since_reshuffle(self) -> int:
        return len(self.played_cards)

    def to_dict(self) -> dict:
        return {
            "remaining": self.remaining,
            "total": self.total_cards,
            "running_count": self.running_count,
            "true_count": self.true_count,
            "penetration_pct": round((self.get_cards_since_reshuffle() / self.total_cards) * 100, 1),
        }

    def __len__(self) -> int:
        return len(self.cards)
