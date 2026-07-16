"""Matplotlib donut-chart rendering for portfolio data."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Keep Matplotlib's generated cache out of the project folder.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "python-stock-tracker-matplotlib")
)

from matplotlib import colors

from portfolio import Holding, load_portfolio


def portfolio_allocations(holdings: list[Holding]) -> tuple[list[Holding], list[float]]:
    """Return priced holdings and values, sorted from largest to smallest."""
    allocations = [
        (holding, value)
        for holding in holdings
        if (value := holding.market_value) is not None and value > 0
    ]
    allocations.sort(key=lambda item: item[1], reverse=True)
    if not allocations:
        raise ValueError("Refresh prices before creating a chart.")
    return (
        [holding for holding, _ in allocations],
        [value for _, value in allocations],
    )


def gradient_colors(
    start_hex: str,
    end_hex: str,
    count: int,
) -> list[tuple[float, float, float, float]]:
    """Create count evenly spaced colors from one hex color to another."""
    if count < 1:
        return []
    try:
        colors.to_rgba(start_hex)
        colors.to_rgba(end_hex)
    except ValueError as error:
        raise ValueError("Chart colors must be valid hex values such as #4F46E5") from error

    gradient = colors.LinearSegmentedColormap.from_list(
        "portfolio",
        [start_hex, end_hex],
    )
    return [gradient(step / max(count - 1, 1)) for step in range(count)]


def show_portfolio_chart(
    start_hex: str = "#4F46E5",
    end_hex: str = "#22C55E",
    save_path: str | None = None,
) -> None:
    """Show or save a donut chart of portfolio market-value allocation."""
    if save_path:
        # A file export does not need a graphical window and works in headless contexts.
        import matplotlib

        matplotlib.use("Agg", force=True)

    from matplotlib import pyplot as plt

    holdings, values = portfolio_allocations(load_portfolio())
    total = sum(values)
    palette = gradient_colors(start_hex, end_hex, len(holdings))
    background = "#F8FAFC"
    figure_height = min(12, max(6, 2.8 + (0.46 * len(holdings))))

    figure, axis = plt.subplots(figsize=(10, figure_height), facecolor=background)
    axis.set_facecolor(background)
    wedges, _, percentage_labels = axis.pie(
        values,
        colors=palette,
        startangle=90,
        counterclock=False,
        autopct=lambda percentage: f"{percentage:.1f}%" if percentage >= 4 else "",
        pctdistance=0.80,
        textprops={"color": "white", "fontsize": 10, "weight": "bold"},
        wedgeprops={"width": 0.38, "edgecolor": background, "linewidth": 3},
    )
    for label in percentage_labels:
        label.set_path_effects([])

    axis.set_title("Portfolio Allocation", fontsize=18, weight="bold", pad=18)
    axis.text(
        0,
        0.09,
        "TOTAL VALUE",
        ha="center",
        va="center",
        color="#64748B",
        fontsize=9,
        weight="bold",
    )
    axis.text(
        0,
        -0.08,
        f"${total:,.2f}",
        ha="center",
        va="center",
        color="#0F172A",
        fontsize=17,
        weight="bold",
    )
    axis.legend(
        wedges,
        [
            f"{holding.ticker}   {value / total:.1%}   ${value:,.2f}"
            for holding, value in zip(holdings, values)
        ],
        title="Holdings",
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        frameon=False,
        fontsize=10,
        title_fontproperties={"weight": "bold", "size": 11},
        labelspacing=1.0,
    )
    axis.set(aspect="equal")
    figure.subplots_adjust(left=0.04, right=0.72, top=0.88, bottom=0.08)

    if save_path:
        output_path = Path(save_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            output_path,
            dpi=180,
            bbox_inches="tight",
            facecolor=figure.get_facecolor(),
        )
        print(f"Saved chart to {output_path}")
    else:
        plt.show()
    plt.close(figure)
