from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical

from database import get_last_incomplete_session, clear_database


class MenuScreen(Screen):

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(
                "  ♠ ♥ ♦ ♣  TYPESAFE 21  ♣ ♦ ♥ ♠",
                id="menu-title",
            ),
            OptionList(
                Option("New Game", id="new"),
                Option("Continue Previous Game", id="continue"),
                Option("View History", id="history"),
                Option("Clear Database", id="clear"),
                Option("Quit", id="quit"),
                id="menu-options",
            ),
            id="menu-container",
        )
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option_id
        if option_id == "new":
            self.app.action_new_game()
        elif option_id == "continue":
            session = get_last_incomplete_session()
            if session:
                self.app.action_continue_game()
            else:
                self.notify("No incomplete game found. Starting new game.", severity="warning")
                self.app.action_new_game()
        elif option_id == "history":
            self.app.action_view_history()
        elif option_id == "clear":
            clear_database()
            self.notify("Database cleared.", severity="information")
        elif option_id == "quit":
            self.app.action_quit()

    def on_key(self, event) -> None:
        if event.character == "q":
            self.app.action_quit()
