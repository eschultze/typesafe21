from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static

from rules.player import Player, STARTING_BALANCE


class ScoreboardPanel(Widget):

    DEFAULT_CSS = """
    ScoreboardPanel {
        height: 2fr;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def compose(self) -> None:
        yield Static("No session data", id="scoreboard-content")

    def update_balances(self, players: list[Player]) -> None:
        content = self.query_one("#scoreboard-content")

        lines = ["[bold]SCOREBOARD[/]", ""]

        # Balances
        for p in players:
            bal_color = "green" if p.balance >= 100 else "yellow" if p.balance >= 50 else "red"
            bet_display = f"  [dim](bet ${p.current_bet})[/]" if p.current_bet > 0 else ""
            lines.append(f"  {p.name}: [{bal_color}]${p.balance}[/]{bet_display}")

        lines.append("")

        # Stats per player
        for p in players:
            total = p.wins + p.losses + p.pushes
            win_rate = (p.wins / total * 100) if total > 0 else 0
            profit = p.balance - STARTING_BALANCE
            profit_pct = (profit / STARTING_BALANCE) * 100
            profit_style = "green" if profit >= 0 else "red"
            wr_style = "green" if win_rate >= 50 else "yellow" if win_rate >= 40 else "red"
            lines.append(
                f"  {p.name}: [green]{p.wins}W[/] [red]{p.losses}L[/] [yellow]{p.pushes}P[/]"
                f"  [{wr_style}]{win_rate:.0f}%[/]"
                f"  [{profit_style}]{profit:+d} ({profit_pct:+.0f}%)[/]"
            )

        content.update("\n".join(lines))
