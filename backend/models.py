from pydantic import BaseModel


class CardModel(BaseModel):
    rank: str
    suit: str
    value: int


class HandModel(BaseModel):
    cards: list[CardModel]
    value: int
    is_soft: bool
    is_bust: bool
    is_blackjack: bool


class PlayerState(BaseModel):
    name: str
    balance: int
    current_bet: int
    wins: int
    losses: int
    pushes: int
    hand: HandModel
    balance_history: list[int]


class ShoeState(BaseModel):
    remaining: int
    total: int
    running_count: int
    true_count: int
    penetration_pct: float


class GameState(BaseModel):
    phase: str
    round_number: int
    players: list[PlayerState]
    dealer: HandModel | None = None
    dealer_hidden: bool = True
    shoe: ShoeState
    current_player: str | None = None
    last_action: dict | None = None
    session_id: int | None = None
    auto_play: bool = False
    auto_play_delay_ms: int = 500


class BetResult(BaseModel):
    name: str
    bet: int
    is_ai: bool = False
    reasoning: str = ""
    confidence: float = 0.0


class HandResult(BaseModel):
    player_index: int
    name: str
    hand: HandModel
    result: str | None = None
    is_ai: bool = False
    confidence: float = 0.0
    decision: str = ""
    bet: int = 0
    balance: int = 0


class RoundResultModel(BaseModel):
    dealer_hand: HandModel
    hands: list[HandResult]
    ai_confidence: float = 0.0
    ai_decision: str = ""
