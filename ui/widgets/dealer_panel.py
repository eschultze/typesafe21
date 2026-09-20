from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static

from cards import Hand
from ui.widgets.card_art import render_card, render_hand_cards, BACK


class DealerPanel(Widget):

    DEFAULT_CSS = """
    DealerPanel {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def compose(self) -> None:
        yield Static("No round in progress", id="dealer-content")

    def update_dealer(
        self,
        hand: Hand | None,
        hide_first: bool = True,
        session_id: int = 0,
        round_number: int = 0,
    ) -> None:
        content = self.query_one("#dealer-content")

        header = f"[bold]Round {round_number} | Session #{session_id}[/]"

        if hand is None or len(hand.cards) == 0:
            content.update(f"{header}\n\nWaiting to deal...")
            return

        if hide_first and len(hand.cards) >= 2:
            # Show back card + visible card side by side
            visible_art = render_card(hand.cards[1])
            showing = hand.cards[1].value
            art_lines = BACK.split("\n")
            vis_lines = visible_art.split("\n")
            merged = []
            for al, vl in zip(art_lines, vis_lines):
                merged.append(f"{al}  {vl}")
            art_block = "\n".join(merged)
            value_line = f"  [dim]showing {showing}[/]"
        else:
            art_block = render_hand_cards(hand.cards)
            value = hand.value
            bust = "  [bold red]BUST![/]" if hand.is_bust else ""
            value_line = f"  [bold]= {value}{bust}[/]"

        content.update(f"{header}\n\n{art_block}\n{value_line}")

    def clear(self) -> None:
        content = self.query_one("#dealer-content")
        content.update("Waiting to deal...")
