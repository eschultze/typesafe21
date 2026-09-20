import random
from abc import ABC, abstractmethod
from cards import Hand, TrackedDeck
from typesafe_ai import get_ai_decision, get_ai_bet

STARTING_BALANCE = 100
MIN_BET = 10


class Player(ABC):
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.balance = STARTING_BALANCE
        self.current_bet = 0
        self.split_hands: list[tuple[Hand, int, str, float]] = []  # (hand, bet, decision, confidence)
        self.balance_history: list[int] = [STARTING_BALANCE]

    def reset_hand(self):
        self.hand.clear()
        self.split_hands.clear()

    def reset_session(self):
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.balance = STARTING_BALANCE
        self.balance_history = [STARTING_BALANCE]

    def can_play(self) -> bool:
        return self.balance >= MIN_BET

    def place_bet(self, amount: int) -> int:
        amount = max(MIN_BET, min(amount, self.balance))
        self.balance -= amount
        self.current_bet = amount
        return amount

    def win_bet(self, multiplier: float = 1.0):
        self.balance += self.current_bet + round(self.current_bet * multiplier)

    def lose_bet(self):
        pass

    def push_bet(self):
        self.balance += self.current_bet

    @abstractmethod
    def make_decision(self, dealer_hand: Hand, deck: TrackedDeck) -> str:
        pass

    def decide_bet(self, deck: TrackedDeck) -> int:
        return MIN_BET

    def record_result(self, result: str):
        if result == "win":
            self.wins += 1
        elif result == "lose":
            self.losses += 1
        elif result == "push":
            self.pushes += 1
        self.balance_history.append(self.balance)


class RandomPlayer(Player):
    def make_decision(self, dealer_hand: Hand, deck: TrackedDeck) -> str:
        if self.hand.value >= 21:
            return "stand"
        return random.choice(["hit", "stand"])

    def decide_bet(self, deck: TrackedDeck) -> int:
        if self.balance < MIN_BET:
            return 0
        return random.choice([10, 15, 20, 25, 30])


class BasicStrategyPlayer(Player):
    def __init__(self, name: str = "BasicStrategy"):
        super().__init__(name)
        self.last_confidence = 0.0
        self.last_decision = ""

    def make_decision(
        self,
        dealer_hand: Hand,
        deck: TrackedDeck,
        can_double: bool = True,
        can_split: bool = True,
    ) -> str:
        if self.hand.value >= 21:
            return "stand"

        from basic_strategy import get_basic_strategy_action
        decision = get_basic_strategy_action(self.hand, dealer_hand, can_double, can_split)
        self.last_decision = decision
        self.last_confidence = 1.0
        return decision

    def decide_bet(self, deck: TrackedDeck) -> int:
        if self.balance < MIN_BET:
            return 0
        return MIN_BET


class AIPlayer(Player):
    def __init__(self, name: str = "You"):
        super().__init__(name)
        self.last_confidence = 0.0
        self.last_decision = ""
        self.last_probabilities = {}
        self.last_bet_info = {}

    def make_decision(
        self,
        dealer_hand: Hand,
        deck: TrackedDeck,
        can_double: bool = True,
        can_split: bool = True,
    ) -> str:
        if self.hand.value >= 21:
            return "stand"

        result = get_ai_decision(
            self.hand,
            dealer_hand,
            deck,
            session_wins=self.wins,
            session_losses=self.losses,
            can_double=can_double,
            can_split=can_split,
        )
        self.last_confidence = result["confidence"]
        self.last_decision = result["decision"]
        self.last_probabilities = result["probabilities"]

        return result["decision"]

    def decide_bet(self, deck: TrackedDeck, opponent_balances: list[int] | None = None) -> int:
        if self.balance < MIN_BET:
            return 0

        result = get_ai_bet(
            balance=self.balance,
            min_bet=MIN_BET,
            true_count=deck.true_count,
            running_count=deck.running_count,
            cards_remaining=deck.remaining,
            cards_dealt=deck.get_cards_since_reshuffle(),
            total_cards=deck.total_cards,
            session_wins=self.wins,
            session_losses=self.losses,
            opponent_balances=opponent_balances,
            remaining_by_rank=deck.get_remaining_by_rank(),
        )

        self.last_bet_info = result
        bet = max(MIN_BET, min(result["bet"], self.balance))
        return bet
