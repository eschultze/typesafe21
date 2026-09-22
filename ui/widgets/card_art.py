from __future__ import annotations

from rules.cards import Card, Suit


# Face-down card (back)
BACK = (
    "[dim]\u250c\u2500\u2500\u2500\u2500\u2500\u2510[/]\n"
    "[dim]\u2502 . . \u2502[/]\n"
    "[dim]\u2502. . .\u2502[/]\n"
    "[dim]\u2502 . . \u2502[/]\n"
    "[dim]\u2514\u2500\u2500\u2500\u2500\u2500\u2518[/]"
)

# Card width constant (inside the borders: 5 chars)
_CARD_INNER = 5


def _suit_char(suit: Suit) -> str:
    return suit.value


def _is_red(suit: Suit) -> bool:
    return suit in (Suit.HEARTS, Suit.DIAMONDS)


def render_card(card: Card) -> str:
    """Render a single card as 5 lines of Rich-markup ASCII art."""
    s = _suit_char(card.suit)
    r = card.rank
    color = "red" if _is_red(card.suit) else "white"

    # Pad rank to fill inner width: rank + spaces = 5 chars
    # Put rank top-left, suit bottom-right for visual balance
    r_top = r.ljust(_CARD_INNER)
    r_bot = " " * (len(r)) + " " * (_CARD_INNER - len(r))

    lines = [
        f"[{color}]\u250c\u2500\u2500\u2500\u2500\u2500\u2510[/]",
        f"[{color}]\u2502{r_top}\u2502[/]",
        f"[{color}]\u2502  {s}  \u2502[/]",
        f"[{color}]\u2502 {r_bot}\u2502[/]",
        f"[{color}]\u2514\u2500\u2500\u2500\u2500\u2500\u2518[/]",
    ]
    return "\n".join(lines)


def render_hand_cards(cards: list[Card]) -> str:
    """Render multiple cards side by side as a single Rich-markup string.
    Returns a string with newlines separating the 5 rows."""
    if not cards:
        return ""

    card_arts = [render_card(c).split("\n") for c in cards]
    num_lines = 5

    rows = []
    for line_idx in range(num_lines):
        parts = [art[line_idx] for art in card_arts]
        rows.append("  ".join(parts))

    return "\n".join(rows)
