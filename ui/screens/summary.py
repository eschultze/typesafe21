from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical


class SummaryScreen(Screen):

    def __init__(self, stats: dict, session_id: int, player_names: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.stats = stats
        self.session_id = session_id
        self.player_names = player_names or ["P1", "P2", "P3"]

    BINDINGS = [
        ("escape", "back", "Back"),
        ("enter", "back", "Back"),
        ("space", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        total = self.stats.get("total_rounds", 0) or 0
        players = self.stats.get("players", {})

        lines = [
            f"[bold cyan]SESSION #{self.session_id} COMPLETE[/]",
            "",
            f"[bold]Rounds Played: {total}[/]",
            "",
        ]

        for name in self.player_names:
            p = players.get(name, {})
            w = p.get("wins", 0)
            l = p.get("losses", 0)
            pu = p.get("pushes", 0)
            conf = p.get("avg_confidence", 0) or 0
            label = f"{name} (AI)" if conf > 0 else name
            lines.append(
                f"{label}:  [green]{w}W[/] / [red]{l}L[/] / [yellow]{pu}P[/]"
                + (f"  (avg confidence: {conf:.0%})" if conf > 0 else "")
            )

        lines.append("")
        lines.append("[cyan]Press any key to return to menu.[/]")

        yield Header()
        yield Vertical(
            Static("\n".join(lines), id="summary-content"),
            id="summary-container",
        )
        yield Footer()

    def on_key(self, event) -> None:
        self.app.pop_screen()
