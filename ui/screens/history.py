from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable, RichLog
from textual.containers import Vertical

from database import get_all_sessions, get_session_rounds, get_session_stats


class HistoryScreen(Screen):

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("[bold cyan]GAME HISTORY (Last 10 Sessions)[/]", id="history-title"),
            id="history-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        sessions = get_all_sessions()
        self._sessions = sessions
        table = DataTable()
        table.add_columns("Session", "Date", "Rounds")
        for s in sessions:
            table.add_row(str(s["id"]), s["started_at"], str(s["total_rounds"]), key=str(s["id"]))
        table.cursor_type = "row"
        self.query_one("#history-container").mount(table)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key
        if row_key is None or row_key.value is None:
            return
        try:
            session_id = int(str(row_key.value))
        except (ValueError, TypeError):
            return
        rounds = get_session_rounds(session_id)

        detail_lines = [f"[bold]Session #{session_id} — Round Details[/]", ""]
        for r in rounds:
            player_parts = []
            for p in r.get("players", []):
                name = p["player_name"]
                result = p["result"]
                conf = p.get("confidence", 0)
                conf_str = f" (conf: {conf:.0%})" if conf > 0 else ""
                player_parts.append(f"{name}={result}{conf_str}")
            detail_lines.append(
                f"  Round {r['round_number']}: " + ", ".join(player_parts)
            )
        detail_lines.append("")
        detail_lines.append("[dim]Press Escape to close.[/]")

        self.query_one("#history-container").remove_children()
        log = RichLog(markup=True, highlight=True)
        for line in detail_lines:
            log.write(line)
        self.query_one("#history-container").mount(log)

    def on_key(self, event) -> None:
        if event.key in ("escape", "q"):
            self.app.pop_screen()
