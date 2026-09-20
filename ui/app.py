from textual.app import App, ComposeResult
from textual.screen import Screen

from ui.screens.menu import MenuScreen
from ui.screens.game import GameScreen
from ui.screens.history import HistoryScreen


class TypesafeApp(App):
    CSS_PATH = "styles.tss"
    TITLE = "Typesafe 21"

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def action_new_game(self) -> None:
        self.push_screen(GameScreen(auto_rounds=1))

    def action_continue_game(self) -> None:
        self.push_screen(GameScreen(continue_mode=True, auto_rounds=1))

    def action_view_history(self) -> None:
        self.push_screen(HistoryScreen())

    def action_quit(self) -> None:
        self.exit()
