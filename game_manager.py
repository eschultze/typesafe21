import asyncio
import traceback
from rules.cards import TrackedDeck, Hand, Card
from rules.player import RandomPlayer, BasicStrategyPlayer, AIPlayer, LayaPlayer
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

    def get_history(self) -> list[dict]:
        return db.get_all_sessions()

    def get_session_stats(self, session_id: int) -> dict:
        return db.get_session_stats(session_id)

    def get_session_rounds(self, session_id: int) -> list[dict]:
        return db.get_session_rounds(session_id)


class GameSession:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.deck = TrackedDeck(num_decks=6)
        self.players: list = [
            RandomPlayer("Random"),
            BasicStrategyPlayer("Basic"),
            AIPlayer("Jev (AI)"),
            LayaPlayer("Laya (AI)"),
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
        self._auto_play_rounds: int | None = None
        # Serializes play_round so a manual request and the auto-play loop (or
        # two clients) cannot mutate the same session concurrently.
        self._round_lock = asyncio.Lock()

    def new_game(self):
        self.deck = TrackedDeck(num_decks=6)
        self.dealer_hand = Hand()
        for p in self.players:
            p.reset_session()
            p.reset_hand()
            p.current_bet = 0
        self.session_id = db.create_session()
        self.round_number = 0
        self.phase = "idle"
        self.last_action = None
        return self.get_state()

    def get_state(self, reveal_dealer: bool = False) -> dict:
        dealer_dict = self.dealer_hand.to_dict() if self.dealer_hand.cards else None
        if dealer_dict and not reveal_dealer and len(dealer_dict["cards"]) > 0:
            dealer_dict["cards"][1] = {"rank": "?", "suit": "?", "value": 0}
            dealer_dict["value"] = self.dealer_hand.cards[0].value
            # These flags are computed on the full hand; scrub them so the
            # hidden hole card isn't leaked through is_blackjack/is_soft/is_bust.
            dealer_dict["is_soft"] = False
            dealer_dict["is_bust"] = False
            dealer_dict["is_blackjack"] = False

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
                can_play=p.can_play(),
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

    async def play_round(self, broadcast_fn=None) -> dict:
        # Serialize rounds, and if anything fails (e.g. the remote AI is down)
        # roll the round back and stay alive instead of tearing down the session.
        async with self._round_lock:
            snapshot = [
                (p, p.balance, p.wins, p.losses, p.pushes, len(p.balance_history))
                for p in self.players
            ]
            try:
                return await self._play_round_inner(broadcast_fn)
            except Exception as e:
                traceback.print_exc()
                self._rollback_round(snapshot)
                self.auto_play = False
                self.phase = "idle"
                self.last_action = {"type": "error", "message": str(e)}
                return self.get_state()

    def _rollback_round(self, snapshot) -> None:
        for p, balance, wins, losses, pushes, hist_len in snapshot:
            p.balance = balance
            p.wins = wins
            p.losses = losses
            p.pushes = pushes
            p.current_bet = 0
            p.reset_hand()
            del p.balance_history[hist_len:]
        self.dealer_hand = Hand()

    async def _play_round_inner(self, broadcast_fn=None) -> dict:
        self.round_number += 1

        # Ensure we have a session to FK into
        if self.session_id is None:
            self.session_id = await asyncio.to_thread(db.create_session)

        # Bets
        self.phase = "betting"
        if broadcast_fn:
            await broadcast_fn({"type": "state_update", "state": self.get_state()})
            await asyncio.sleep(0)
        true_count_at_bet = self.deck.true_count
        bets = await asyncio.to_thread(do_bets, self.players, self.deck)
        bet_results = [BetResult(
            name=b.name, bet=b.bet, is_ai=b.is_ai,
            reasoning=b.reasoning, confidence=b.confidence,
            latency_ms=b.latency_ms, tokens=b.tokens,
        ).model_dump() for b in bets]

        # Deal
        self.phase = "dealing"
        if broadcast_fn:
            await broadcast_fn({"type": "state_update", "state": self.get_state()})
            await asyncio.sleep(0)
        self.dealer_hand = await asyncio.to_thread(deal_initial, self.players, self.deck)

        # Player turns
        self.phase = "player_turn"
        if broadcast_fn:
            await broadcast_fn({"type": "state_update", "state": self.get_state()})
            await asyncio.sleep(0)
        actions = []
        for i, player in enumerate(self.players):
            if player.current_bet == 0:
                continue
            self.current_player_idx = i

            # Broadcast "thinking" state for AI players
            is_ai = isinstance(player, (AIPlayer, LayaPlayer))
            if broadcast_fn and is_ai:
                await broadcast_fn({
                    "type": "state_update",
                    "state": self.get_state(),
                })
                await asyncio.sleep(0)

            decision, confidence, last_ai_decision = await asyncio.to_thread(
                play_player_hand, player, self.deck, self.dealer_hand
            )
            actions.append({
                "player": player.name,
                "decision": decision,
                "confidence": confidence,
                "ai_decision": last_ai_decision,
                "latency_ms": player.avg_latency_ms() if is_ai else 0.0,
                "tokens": int(round(player.avg_tokens())) if is_ai else 0,
                "decisions": player.decision_count if is_ai else 0,
            })

        # Dealer
        self.phase = "dealer_turn"
        if broadcast_fn:
            # Reveal the hole card now that all players are done.
            await broadcast_fn({"type": "state_update", "state": self.get_state(reveal_dealer=True)})
            await asyncio.sleep(0)
        await asyncio.to_thread(play_dealer, self.dealer_hand, self.deck)

        # Settle
        self.phase = "results"
        result = settle_round(self.players, self.dealer_hand, self.session_id, self.round_number)

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
                "latency_ms": hand_result.latency_ms,
                "tokens": hand_result.tokens,
                "decisions": hand_result.decisions,
                "true_count": true_count_at_bet,
            })
        await asyncio.to_thread(
            db.save_round, self.session_id, self.round_number, player_results, self.dealer_hand.value
        )

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
                    latency_ms=h.latency_ms,
                    tokens=h.tokens,
                    decisions=h.decisions,
                ).model_dump() for h in result.hands],
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
        try:
            while self.auto_play and count < max_rounds:
                state = await self.play_round(broadcast_fn=broadcast_fn)
                await broadcast_fn({
                    "type": "state_update",
                    "state": state,
                })
                count += 1
                await asyncio.sleep(self.auto_play_delay_ms / 1000)
        except Exception:
            traceback.print_exc()
            self.auto_play = False
            try:
                await broadcast_fn({
                    "type": "state_update",
                    "state": self.get_state(),
                })
            except Exception:
                pass
        self.auto_play = False
        await broadcast_fn({
            "type": "state_update",
            "state": self.get_state(),
        })

    def end_session(self):
        if self.session_id:
            db.complete_session(self.session_id)

    def get_history(self) -> list[dict]:
        return db.get_all_sessions()

    def get_session_stats(self, session_id: int) -> dict:
        return db.get_session_stats(session_id)

    def get_session_rounds(self, session_id: int) -> list[dict]:
        return db.get_session_rounds(session_id)
