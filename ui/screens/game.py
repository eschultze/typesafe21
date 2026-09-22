from __future__ import annotations

import asyncio
import subprocess
from enum import Enum, auto
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Horizontal, Vertical
from textual import work

from rules.cards import TrackedDeck, Hand
from rules.player import RandomPlayer, BasicStrategyPlayer, AIPlayer, LayaPlayer, STARTING_BALANCE
from database import (
    init_db, create_session, save_round, complete_session,
    get_last_incomplete_session, get_round_count, get_session_stats,
)
from rules.typesafe_ai import get_ai_decision, get_ai_bet
from rules.game import (
    BetInfo, PlayerHandResult, RoundResult,
    do_bets, deal_initial, play_player_hand, play_dealer, settle_round,
)
from ui.widgets.dealer_panel import DealerPanel
from ui.widgets.deck_panel import DeckPanel
from ui.widgets.players_panel import PlayersPanel
from ui.widgets.scoreboard_panel import ScoreboardPanel
from ui.widgets.balance_chart import BalanceChartPanel


class GameState(Enum):
    IDLE = auto()
    BETTING = auto()
    DEALING = auto()
    PLAYER_TURNS = auto()
    DEALER_TURN = auto()
    RESULTS = auto()


class GameScreen(Screen):

    BINDINGS = [
        ("space", "advance", "Deal / Next"),
        ("q", "quit_game", "Quit to Menu"),
    ]

    def __init__(self, continue_mode: bool = False, auto_rounds: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.continue_mode = continue_mode
        self.auto_rounds = auto_rounds

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                DealerPanel(id="dealer-panel"),
                PlayersPanel(id="players-panel"),
                id="left-column",
            ),
            Vertical(
                DeckPanel(id="deck-panel"),
                ScoreboardPanel(id="scoreboard-panel"),
                BalanceChartPanel(id="balance-chart"),
                Horizontal(
                    Static(
                        "[dim][Space] Next  |  [Q] Quit[/]",
                        id="controls-content",
                    ),
                    Input(placeholder="auto-play rounds...", id="rounds-input"),
                    id="controls-row",
                ),
                id="right-column",
            ),
            id="game-layout",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.state = GameState.IDLE
        self.session_id = 0
        self.round_number = 0
        self.deck: TrackedDeck | None = None
        self.players: list = []
        self.dealer_hand: Hand | None = None
        self.auto_timer = None

        if self.continue_mode:
            session = get_last_incomplete_session()
            if session:
                self.session_id = session["id"]
                self.round_number = get_round_count(self.session_id) + 1
                self._init_players()
            else:
                self._start_new_session()
        else:
            self._start_new_session()

        self._update_controls()

        if self.auto_rounds > 0:
            self._do_round()

    def _init_players(self) -> None:
        self.players = [
            RandomPlayer("Random"),
            BasicStrategyPlayer("Basic"),
            AIPlayer("Jev (AI)"),
            LayaPlayer("Laya (AI)"),
        ]
        self.deck = TrackedDeck(num_decks=6)
        self._refresh_panels()

    def _start_new_session(self) -> None:
        self.session_id = create_session()
        self.round_number = 1
        self.deck = TrackedDeck(num_decks=6)
        self.players = [
            RandomPlayer("Random"),
            BasicStrategyPlayer("Basic"),
            AIPlayer("Jev (AI)"),
            LayaPlayer("Laya (AI)"),
        ]
        self._refresh_panels()

    def _refresh_panels(self) -> None:
        dealer = self.query_one("#dealer-panel", DealerPanel)
        deck_p = self.query_one("#deck-panel", DeckPanel)
        players = self.query_one("#players-panel", PlayersPanel)
        score = self.query_one("#scoreboard-panel", ScoreboardPanel)

        dealer.update_dealer(
            self.dealer_hand,
            hide_first=True,
            session_id=self.session_id,
            round_number=self.round_number,
        )
        if self.deck:
            deck_p.update_deck(self.deck)
        players.update_waiting(len(self.players))
        score.update_balances(self.players)

    def _update_controls(self) -> None:
        ctrl = self.query_one("#controls-content")
        inp = self.query_one("#rounds-input")
        if self.state == GameState.IDLE:
            if self.auto_rounds > 0:
                ctrl.update(f"[dim][Space] Skip  |  Auto: {self.auto_rounds} left[/]")
                inp.visible = False
            else:
                ctrl.update("[dim][Space] Deal  |  [Q] Quit[/]")
                inp.visible = True
        elif self.state == GameState.RESULTS:
            ctrl.update("[dim][Space] Next  |  [Q] Quit[/]")
            inp.visible = True
        else:
            ctrl.update("[dim]Processing...[/]")
            inp.visible = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.state not in (GameState.IDLE, GameState.RESULTS):
            return
        try:
            value = int(event.value.strip())
            if value <= 0:
                self.notify("Enter a positive number.", severity="warning")
                return
        except ValueError:
            self.notify("Invalid number.", severity="warning")
            return

        event.input.value = ""
        self.auto_rounds = value

        if self.state == GameState.RESULTS:
            self._advance_to_next_round()
        else:
            self._do_round()

    def action_advance(self) -> None:
        if self.state == GameState.IDLE:
            self._do_round()
        elif self.state == GameState.RESULTS:
            self.auto_rounds = 0
            self._advance_to_next_round()

    def _do_round(self) -> None:
        active = [p for p in self.players if p.can_play()]
        if not active:
            self.notify("All players are out of money!", severity="warning")
            self._finish_session()
            return

        ai_players = [p for p in self.players if isinstance(p, (AIPlayer, LayaPlayer))]
        for ai_p in ai_players:
            if not ai_p.can_play():
                self.notify(f"{ai_p.name} is out of money!", severity="warning")
                self._finish_session()
                return

        self.state = GameState.BETTING
        self._update_controls()
        self._run_round()

    @work(exclusive=True, group="round")
    async def _run_round(self) -> None:
        assert self.deck is not None

        bets = do_bets(self.players, self.deck)

        dealer = self.query_one("#dealer-panel", DealerPanel)
        dealer.update_dealer(
            None,
            hide_first=True,
            session_id=self.session_id,
            round_number=self.round_number,
        )

        players_p = self.query_one("#players-panel", PlayersPanel)

        bet_lines = []
        for b in bets:
            if b.is_ai and b.reasoning:
                short = b.reasoning[:60] + "..." if len(b.reasoning) > 60 else b.reasoning
                bet_lines.append(f"{b.name} bets [green]${b.bet}[/] (TC: {self.deck.true_count:+d})")
                bet_lines.append(f"  [dim]{short}[/]")
            else:
                bet_lines.append(f"{b.name} bets [green]${b.bet}[/]")

        players_p.query_one("#players-content").update(
            "[bold]BETTING PHASE[/]\n\n" + "\n".join(bet_lines)
        )

        if self.auto_rounds == 0:
            await asyncio.sleep(0.5)

        self.state = GameState.DEALING
        self.dealer_hand = deal_initial(self.players, self.deck)

        dealer.update_dealer(
            self.dealer_hand,
            hide_first=True,
            session_id=self.session_id,
            round_number=self.round_number,
        )
        deck_p = self.query_one("#deck-panel", DeckPanel)
        deck_p.update_deck(self.deck)

        hands: list[PlayerHandResult] = []
        player_status_lines: list[str] = ["[bold]DEALING...[/]", ""]

        for i, player in enumerate(self.players):
            if player.current_bet == 0:
                hands.append(PlayerHandResult(
                    player_index=i + 1,
                    name=player.name,
                    hand=player.hand,
                    result=None,
                    bet=0,
                    balance=player.balance,
                ))
                player_status_lines.append(f"Player {i+1} ({player.name}): Sitting out")
                continue

            self.state = GameState.PLAYER_TURNS
            self._update_controls()

            is_ai = isinstance(player, (AIPlayer, LayaPlayer))
            if is_ai:
                player_status_lines.append(f"Player {i+1} ({player.name}): [cyan]Consulting AI...[/]")
                players_p.query_one("#players-content").update(
                    "\n".join(player_status_lines)
                )
                players_p.show_spinner()
                decision, confidence, last_ai_decision = await asyncio.to_thread(
                    play_player_hand, player, self.deck, self.dealer_hand
                )
                players_p.hide_spinner()
            else:
                decision, confidence, last_ai_decision = play_player_hand(
                    player, self.deck, self.dealer_hand
                )

            hands.append(PlayerHandResult(
                player_index=i + 1,
                name=player.name,
                hand=player.hand,
                result=None,
                is_ai=is_ai,
                confidence=confidence,
                decision=last_ai_decision if is_ai else "",
                bet=player.current_bet,
                balance=player.balance,
            ))

            # Add split hands if any
            for split_hand, split_bet, split_dec, split_conf in player.split_hands:
                hands.append(PlayerHandResult(
                    player_index=i + 1,
                    name=player.name,
                    hand=split_hand,
                    result=None,
                    is_ai=is_ai,
                    confidence=split_conf,
                    decision=split_dec if is_ai else "",
                    bet=split_bet,
                    balance=player.balance,
                ))

            cards_str = " ".join(str(c) for c in player.hand.cards)
            val = player.hand.value
            ai_tag = f" [dim]({last_ai_decision.upper()} {confidence:.0%})[/]" if is_ai else ""
            player_status_lines.append(
                f"Player {i+1} ({player.name}): {cards_str} = {val}{ai_tag}"
            )
            players_p.query_one("#players-content").update(
                "\n".join(player_status_lines)
            )

        self.state = GameState.DEALER_TURN
        self._update_controls()
        play_dealer(self.dealer_hand, self.deck)

        dealer.update_dealer(
            self.dealer_hand,
            hide_first=False,
            session_id=self.session_id,
            round_number=self.round_number,
        )
        deck_p.update_deck(self.deck)

        result = settle_round(
            self.players, self.dealer_hand, self.session_id, self.round_number
        )

        players_p.update_hands(result.hands)
        score = self.query_one("#scoreboard-panel", ScoreboardPanel)
        score.update_balances(self.players)

        # Update balance chart (show Jev AI)
        jev_player = next((p for p in self.players if isinstance(p, AIPlayer)), None)
        if jev_player:
            chart = self.query_one("#balance-chart", BalanceChartPanel)
            chart.update_chart(jev_player)

        # Play cash register sound on AI win (either AI)
        ai_won = any(h.is_ai and h.result == "win" for h in result.hands)
        if ai_won:
            subprocess.Popen(["afplay", "cash_register.mp3"],
                             cwd=str(Path(__file__).parent.parent))

        # Build player results for save_round
        player_results: list[dict] = []
        for h in result.hands:
            player_results.append({
                "player_index": h.player_index,
                "player_name": h.name,
                "result": h.result,
                "bet": h.bet,
                "confidence": h.confidence,
                "decision": h.decision,
                "balance_after": h.balance,
            })

        save_round(
            session_id=self.session_id,
            round_number=self.round_number,
            player_results=player_results,
            dealer_final_value=self.dealer_hand.value,
        )

        self.state = GameState.RESULTS
        self._update_controls()

        if self.auto_rounds > 0:
            self.auto_rounds -= 1
            self._update_controls()
            if self.auto_rounds > 0:
                self.auto_timer = self.set_timer(0.5, self._auto_advance)
            else:
                self.notify("Auto-play complete.", severity="information")

    def _auto_advance(self) -> None:
        if self.state == GameState.RESULTS and self.auto_rounds > 0:
            self._advance_to_next_round()

    def _advance_to_next_round(self) -> None:
        self.round_number += 1
        self.dealer_hand = None

        for p in self.players:
            p.reset_hand()
            p.current_bet = 0

        self.state = GameState.IDLE
        self._refresh_panels()
        self._update_controls()

        if self.auto_rounds > 0:
            self._do_round()

    def _finish_session(self) -> None:
        complete_session(self.session_id)
        stats = get_session_stats(self.session_id)
        # Show final state briefly before transitioning
        self.state = GameState.RESULTS
        self._update_controls()
        ctrl = self.query_one("#controls-content")
        ctrl.update("[bold green]Session complete![/] [dim]Press any key for summary.[/]")
        self.query_one("#rounds-input").visible = False
        self._waiting_for_finish = True

    def on_key(self, event) -> None:
        if event.key == "q":
            if getattr(self, "_waiting_for_finish", False):
                self._push_summary()
            else:
                self.action_quit_game()

    def _push_summary(self) -> None:
        stats = get_session_stats(self.session_id)
        player_names = [p.name for p in self.players]
        self.app.pop_screen()
        from ui.screens.summary import SummaryScreen
        self.app.push_screen(SummaryScreen(stats, self.session_id, player_names))

    def action_quit_game(self) -> None:
        if self.auto_timer:
            self.auto_timer.stop()
            self.auto_timer = None
        self.auto_rounds = 0
        self.app.pop_screen()
