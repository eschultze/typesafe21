import asyncio
from rules.cards import TrackedDeck, Hand, Card
from rules.player import RandomPlayer, BasicStrategyPlayer, AIPlayer
from rules.game import do_bets, deal_initial, play_player_hand, play_dealer, settle_round
from models import GameState, PlayerState, HandModel, ShoeState, BetResult, HandResult, RoundResultModel
import database as db


class GameManager:
    def __init__(self):
        self.games: dict[str, "GameSession"] = {}

    def get_or_create(self, game_id: str) -> "GameSession":
        if game_id not in self.games:
            self.games[game_id] = GameSession(game_id)
        return self.games[game_id]

    def remove(self, game_id: str):
        self.games.pop(game_id, None)


class GameSession:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.deck = TrackedDeck(num_decks=6)
        self.players: list = [
            RandomPlayer("Random"),
            BasicStrategyPlayer("Basic"),
            AIPlayer("You"),
        ]
        self.dealer_hand = Hand()
        self.round_number = 0
        self.session_id: int | None = None
        self.phase = "idle"
        self.current_player_idx = 0
        self.last_action: dict | None = None
        self.auto_play = False
        self.auto_play_delay_ms = 500
        self._auto_play_task: asyncio.Task | None = None

    def new_game(self):
        self.deck = TrackedDeck(num_decks=6)
        for p in self.players:
            p.reset_session()
        self.session_id = db.create_session()
        self.round_number = 0
        self.phase = "idle"
        self.last_action = None
        return self.get_state()

    def continue_game(self):
        session = db.get_last_incomplete_session()
        if session:
            self.session_id = session["id"]
            self.round_number = db.get_round_count(self.session_id)
        else:
            return self.new_game()
        return self.get_state()

    def get_state(self, reveal_dealer: bool = False) -> dict:
        dealer_dict = self.dealer_hand.to_dict() if self.dealer_hand.cards else None
        if dealer_dict and not reveal_dealer and len(dealer_dict["cards"]) > 0:
            dealer_dict["cards"][1] = {"rank": "?", "suit": "?", "value": 0}
            dealer_dict["value"] = self.dealer_hand.cards[0].value

        players = []
        for p in self.players:
            players.append(PlayerState(
                name=p.name,
                balance=p.balance,
                current_bet=p.current_bet,
                wins=p.wins,
                losses=p.losses,
                pushes=p.pushes,
                hand=p.hand.to_dict(),
                balance_history=p.balance_history,
            ).model_dump())

        current_player = None
        if self.phase == "player_turn" and self.current_player_idx < len(self.players):
            current_player = self.players[self.current_player_idx].name

        return GameState(
            phase=self.phase,
            round_number=self.round_number,
            players=players,
            dealer=dealer_dict,
            dealer_hidden=not reveal_dealer,
            shoe=self.deck.to_dict(),
            current_player=current_player,
            last_action=self.last_action,
            session_id=self.session_id,
            auto_play=self.auto_play,
            auto_play_delay_ms=self.auto_play_delay_ms,
        ).model_dump()

    def play_round(self) -> dict:
        self.round_number += 1

        # Bets
        self.phase = "betting"
        bets = do_bets(self.players, self.deck)
        bet_results = [BetResult(
            name=b.name, bet=b.bet, is_ai=b.is_ai,
            reasoning=b.reasoning, confidence=b.confidence,
        ).model_dump() for b in bets]

        # Deal
        self.phase = "dealing"
        self.dealer_hand = deal_initial(self.players, self.deck)

        # Player turns
        self.phase = "player_turn"
        actions = []
        for i, player in enumerate(self.players):
            if player.current_bet == 0:
                continue
            self.current_player_idx = i
            decision, confidence, last_ai_decision = play_player_hand(player, self.deck, self.dealer_hand)
            actions.append({
                "player": player.name,
                "decision": decision,
                "confidence": confidence,
                "ai_decision": last_ai_decision,
            })

        # Dealer
        self.phase = "dealer_turn"
        play_dealer(self.dealer_hand, self.deck)

        # Settle
        self.phase = "results"
        result = settle_round(self.players, self.dealer_hand, self.session_id or 0, self.round_number)

        # Save to DB
        player_results = []
        for hand_result in result.hands:
            player_results.append({
                "player_index": hand_result.player_index,
                "player_name": hand_result.name,
                "result": hand_result.result,
                "bet": hand_result.bet,
                "confidence": hand_result.confidence,
                "decision": hand_result.decision,
                "balance_after": hand_result.balance,
            })
        db.save_round(self.session_id or 0, self.round_number, player_results, self.dealer_hand.value)

        self.last_action = {
            "type": "round_result",
            "bets": bet_results,
            "actions": actions,
            "result": {
                "dealer_hand": result.dealer_hand.to_dict(),
                "hands": [HandResult(
                    player_index=h.player_index,
                    name=h.name,
                    hand=h.hand.to_dict(),
                    result=h.result,
                    is_ai=h.is_ai,
                    confidence=h.confidence,
                    decision=h.decision,
                    bet=h.bet,
                    balance=h.balance,
                ).model_dump() for h in result.hands],
                "ai_confidence": result.ai_confidence,
                "ai_decision": result.ai_decision,
            },
        }

        self.phase = "idle"
        return self.get_state(reveal_dealer=True)

    def set_auto_play(self, enabled: bool, delay_ms: int = 500, rounds: int | None = None):
        self.auto_play = enabled
        self.auto_play_delay_ms = delay_ms
        self._auto_play_rounds = rounds

    async def auto_play_loop(self, broadcast_fn):
        count = 0
        max_rounds = self._auto_play_rounds or float("inf")
        while self.auto_play and count < max_rounds:
            state = self.play_round()
            await broadcast_fn({
                "type": "state_update",
                "state": state,
            })
            count += 1
            await asyncio.sleep(self.auto_play_delay_ms / 1000)
        self.auto_play = False

    def end_session(self):
        if self.session_id:
            db.complete_session(self.session_id)

    def get_history(self) -> list[dict]:
        return db.get_all_sessions()

    def get_session_stats(self, session_id: int) -> dict:
        return db.get_session_stats(session_id)

    def get_session_rounds(self, session_id: int) -> list[dict]:
        return db.get_session_rounds(session_id)
