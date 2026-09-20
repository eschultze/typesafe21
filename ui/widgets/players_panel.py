from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static, LoadingIndicator

from game import PlayerHandResult
from ui.widgets.card_art import render_hand_cards

_SEPARATOR = "[dim]" + "\u2500" * 50 + "[/]"


class PlayersPanel(Widget):

    DEFAULT_CSS = """
    PlayersPanel {
        height: 3fr;
        border: solid $primary;
        padding: 0 1;
    }
    #ai-spinner {
        height: 1;
        display: none;
    }
    #ai-spinner.visible {
        display: block;
    }
    """

    def compose(self) -> None:
        yield Static("No players", id="players-content")
        yield LoadingIndicator(id="ai-spinner")

    def update_hands(self, hands: list[PlayerHandResult]) -> None:
        content = self.query_one("#players-content")

        if not hands:
            content.update("[bold]PLAYERS[/]\n\nWaiting for round...")
            return

        lines = ["[bold]PLAYERS[/]", ""]

        for idx, h in enumerate(hands):
            # Win/lose indicator - prominent
            if h.result == "win":
                if h.hand.is_blackjack:
                    result_tag = " [bold white on green] BLACKJACK! [/]"
                else:
                    result_tag = " [bold white on green] WIN [/]"
            elif h.result == "lose":
                if h.hand.is_bust:
                    result_tag = " [bold white on red] BUST [/]"
                else:
                    result_tag = " [bold white on red] LOSE [/]"
            elif h.result == "push":
                result_tag = " [bold black on yellow] PUSH [/]"
            else:
                result_tag = ""

            # AI info - fix markup leak by using separate tags
            ai_info = ""
            if h.is_ai and h.confidence > 0:
                conf_style = (
                    "green" if h.confidence >= 0.8
                    else "yellow" if h.confidence >= 0.5
                    else "red"
                )
                ai_info = f"  [dim]AI: {h.decision.upper()}[/] [{conf_style}]{h.confidence:.0%}[/]"

            bet_info = f"  [dim]${h.bet} / ${h.balance}[/]" if h.bet > 0 else ""

            label = f"[bold]P{h.player_index} ({h.name})[/]{result_tag}{bet_info}"
            lines.append(label)

            # Card art - indented
            art = render_hand_cards(h.hand.cards)
            for art_line in art.split("\n"):
                lines.append(f"  {art_line}")

            # Hand value - directly below cards
            value = h.hand.value
            lines.append(f"  [bold]= {value}[/]")

            # AI decision line
            if ai_info:
                lines.append(f"  {ai_info}")

            # Separator between players (not after last)
            if idx < len(hands) - 1:
                lines.append(f"\n{_SEPARATOR}\n")

        content.update("\n".join(lines))

    def update_waiting(self, num_players: int = 3) -> None:
        content = self.query_one("#players-content")
        lines = ["[bold]PLAYERS[/]", ""]
        for i in range(1, num_players + 1):
            lines.append(f"Player {i}:  Waiting...")
        content.update("\n".join(lines))

    def show_spinner(self) -> None:
        spinner = self.query_one("#ai-spinner")
        spinner.add_class("visible")

    def hide_spinner(self) -> None:
        spinner = self.query_one("#ai-spinner")
        spinner.remove_class("visible")
