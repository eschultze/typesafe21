from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static

from rules.cards import TrackedDeck


class DeckPanel(Widget):

    DEFAULT_CSS = """
    DeckPanel {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def compose(self) -> None:
        yield Static("No deck loaded", id="deck-content")

    def update_deck(self, deck: TrackedDeck) -> None:
        content = self.query_one("#deck-content")
        remaining = deck.remaining
        total = deck.total_cards
        pct = (remaining / total) * 100
        true_count = deck.true_count
        dealt = deck.get_cards_since_reshuffle()

        if pct > 50:
            pct_style = "green"
        elif pct > 25:
            pct_style = "yellow"
        else:
            pct_style = "red"

        if true_count > 0:
            count_style = "green"
        elif true_count < 0:
            count_style = "red"
        else:
            count_style = "white"

        rc = deck.running_count
        rc_style = "green" if rc > 0 else "red" if rc < 0 else "white"

        lines = [
            "[bold]DECK & COUNT[/]",
            "",
            f"  [{pct_style}]{remaining}/{total}[/] ([{pct_style}]{pct:.0f}%[/])",
            f"  True: [{count_style}]{true_count:+d}[/]  Run: [{rc_style}]{rc:+d}[/]",
            f"  Dealt: [cyan]{dealt}[/]",
        ]

        content.update("\n".join(lines))
