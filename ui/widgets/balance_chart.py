from __future__ import annotations

from textual.app import RenderResult
from textual.color import Color
from textual.geometry import Size
from textual.widget import Widget
from textual.widgets import Static

from player import Player, STARTING_BALANCE

BAR_CHARS = " ▁▂▃▄▅▆▇█"


class BalanceChart(Widget):
    """Custom bar chart with Y-axis labels for balance history."""

    DEFAULT_CSS = """
    BalanceChart {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[int] = []

    def set_data(self, history: list[int]) -> None:
        self._history = list(history)
        self.refresh()

    def render(self) -> RenderResult:
        if not self._history:
            return "[dim]  No data yet[/]"

        history = self._history
        width = self.size.width
        height = self.size.height

        if width < 10 or height < 3:
            return f"  ${history[-1]}"

        # Reserve left margin for Y-axis labels (6 chars: "$100 ")
        axis_width = 6
        chart_width = width - axis_width

        if chart_width < 1:
            return f"  ${history[-1]}"

        # Each round = 1 bar char + 1 space = 2 chars per round
        # So max bars we can fit = chart_width // 2
        max_bars = chart_width // 2

        n = len(history)
        if n <= max_bars:
            # Show only the data we have, no padding
            sampled = history
        else:
            # Downsample: pick evenly spaced points
            step = n / max_bars
            sampled = [history[int(i * step)] for i in range(max_bars)]

        data_min = min(sampled)
        data_max = max(sampled)
        data_range = data_max - data_min if data_max != data_min else 1

        # Build Y-axis labels: 3 ticks (top, middle, bottom)
        tick_top = data_max
        tick_mid = (data_max + data_min) // 2
        tick_bot = data_min

        # Chart area is (height - 1) rows, last row is the baseline
        chart_rows = max(1, height - 1)

        lines: list[str] = []

        for row in range(chart_rows):
            # Y-axis label: only on first, middle, last row
            if row == 0:
                label = f"${tick_top:>4}"
            elif row == chart_rows // 2:
                label = f"${tick_mid:>4}"
            elif row == chart_rows - 1:
                label = f"${tick_bot:>4}"
            else:
                label = "     "

            # Build bar row with spaces between bars
            bar_parts: list[str] = []
            for val in sampled:
                # Normalize value to 0..1 within chart_rows
                normalized = (val - data_min) / data_range if data_range > 0 else 0.5
                bar_height = normalized * chart_rows

                if bar_height >= (chart_rows - row):
                    if val >= STARTING_BALANCE:
                        bar_parts.append("[green]█[/]")
                    else:
                        bar_parts.append("[red]█[/]")
                else:
                    bar_parts.append(" ")

            bar_str = " ".join(bar_parts)

            lines.append(f"[dim]{label}[/] {bar_str}")

        # Bottom axis line
        num_bars = len(sampled)
        axis_line = "─" * (num_bars * 2 - 1)
        lines.append(f"       [dim]{axis_line}[/]")

        return "\n".join(lines)


class BalanceChartPanel(Widget):
    """Panel containing the balance chart and summary labels."""

    DEFAULT_CSS = """
    BalanceChartPanel {
        height: 3fr;
        border: solid $primary;
        padding: 0 1;
    }
    #balance-chart {
        height: 1fr;
    }
    #balance-labels {
        height: 1;
    }
    """

    def compose(self) -> None:
        yield BalanceChart(id="balance-chart")
        yield Static("", id="balance-labels")

    def update_chart(self, player: Player) -> None:
        chart = self.query_one("#balance-chart", BalanceChart)
        labels = self.query_one("#balance-labels", Static)

        history = player.balance_history
        if not history:
            chart.set_data([])
            labels.update("[dim]No data yet[/]")
            return

        chart.set_data(history)

        current = history[-1]
        high = max(history)
        low = min(history)
        profit = current - STARTING_BALANCE

        color = "green" if profit >= 0 else "red"
        high_color = "green" if high >= STARTING_BALANCE else "red"
        low_color = "green" if low >= STARTING_BALANCE else "red"

        labels.update(
            f"  [bold {color}]${current}[/]"
            f"  [dim]H: [/][{high_color}]${high}[/]"
            f"  [dim]L: [/][{low_color}]${low}[/]"
            f"  [dim]{len(history) - 1} rounds[/]"
        )
        self.refresh()
