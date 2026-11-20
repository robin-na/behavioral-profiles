"""Publication plotting functions, restricted to the three empirical main figures."""

from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import (
    Circle,
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Rectangle,
)
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/main/figures"
SOURCE = ROOT / "outputs/main/tables"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
GRAY = "#6B7280"
LIGHT = "#E5E7EB"
DARK = "#172033"
PALE_BLUE = "#E8F3F8"
PALE_GREEN = "#E7F5EF"


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 10,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.bbox": "tight",
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    name = {
        "figure3_heldout_results": "figure_2_validation",
        "figure4_dimension_transfer": "figure_3_feature_transfer",
        "figure5_cross_domain_portability": "figure_4_cross_family",
    }.get(name, name)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUTPUT / f"{name}.svg"
    fig.savefig(OUTPUT / f"{name}.pdf", facecolor="white")
    fig.savefig(svg_path, facecolor="white")
    fig.savefig(OUTPUT / f"{name}.png", dpi=300, facecolor="white")
    svg_path.write_text(
        "\n".join(
            (
                line.rstrip()
                for line in svg_path.read_text(encoding="utf-8").splitlines()
            )
        )
        + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


def headline_figure() -> None:
    """Plot the same seven held-out profile conditions in every domain."""
    frame = pd.read_csv(SOURCE / "figure3_heldout_results.csv")
    families = ["Public goods", "Bargaining", "Generalized 11–20"]
    panel_titles = ["a  Public goods", "b  Bargaining", "c  Generalized 11–20"]
    colors = {
        "selected_1": ORANGE,
        "selected_2": GREEN,
        "complete": BLUE,
        "nemotron": "#7C6DAF",
        "twin": "#7C6DAF",
        "argyle": "#7C6DAF",
        "none": DARK,
    }
    markers = {
        "selected_1": "o",
        "selected_2": "D",
        "complete": "s",
        "nemotron": "P",
        "twin": "P",
        "argyle": "P",
        "none": "o",
    }
    labels = {
        "selected_1": "Leading · 1 feature",
        "selected_2": "Leading · 2 features",
        "complete": "Complete profile",
        "nemotron": "Nemotron",
        "twin": "Twin-2K-500",
        "argyle": "ANES",
        "none": "No profile",
    }
    fig, axes = plt.subplots(1, 3, figsize=(7.25, 3.42), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.205, right=0.99, top=0.88, bottom=0.245, wspace=0.23)
    xmin = min(-30.0, float(frame["ci_low"].min()) - 3)
    xmax = max(105.0, float(frame["ci_high"].max()) + 3)
    category_order: list[str] | None = None
    for panel_index, (ax, family, title) in enumerate(
        zip(axes, families, panel_titles, strict=True)
    ):
        subset = frame[frame["family"] == family].sort_values("display_order")
        categories = subset["category"].tolist()
        if category_order is None:
            category_order = categories
        elif categories != category_order:
            raise ValueError(f"Figure 3 category order differs for {family}")
        yvals = np.arange(len(subset))[::-1]
        ax.axvspan(xmin, 0, color="#FAF3F1", alpha=0.5, zorder=0)
        ax.axvline(0, color=GRAY, linewidth=0.85, linestyle="--", zorder=1)
        ax.axvline(100, color=GREEN, linewidth=0.85, linestyle=":", zorder=1)
        for y, row in zip(yvals, subset.itertuples(index=False), strict=True):
            color = colors[row.category]
            ax.errorbar(
                row.alignment,
                y,
                xerr=[[row.alignment - row.ci_low], [row.ci_high - row.alignment]],
                fmt=markers[row.category],
                color=color,
                markerfacecolor=color if row.category != "none" else "white",
                markeredgecolor=color,
                markersize=5.6,
                elinewidth=1.05,
                capsize=2.2,
                capthick=0.8,
                zorder=4,
            )
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(-0.55, len(subset) - 0.45)
        ax.set_title(
            title, loc="left", fontsize=8.9, fontweight="bold", color=DARK, pad=9
        )
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.grid(axis="x", color=LIGHT, linewidth=0.5, zorder=0)
        ax.tick_params(axis="y", length=0, pad=6)
        ax.tick_params(axis="x", labelsize=6.8)
        if panel_index == 0:
            ax.set_yticks(
                yvals, [labels[category] for category in categories], fontsize=6.7
            )
        else:
            ax.tick_params(axis="y", labelleft=False)
    fig.supxlabel(
        "Normalized distributional alignment", y=0.115, fontsize=8.0, color=DARK
    )
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="P",
            linestyle="none",
            markersize=5.2,
            markerfacecolor=colors["nemotron"],
            markeredgecolor=colors["nemotron"],
            label="General-purpose persona",
        ),
        Line2D(
            [0],
            [0],
            color=GRAY,
            linewidth=0.9,
            linestyle="--",
            label="Uninformed reference (0)",
        ),
        Line2D(
            [0],
            [0],
            color=GREEN,
            linewidth=0.9,
            linestyle=":",
            label="Human reference (100)",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.6, 0.012),
        ncol=3,
        frameon=False,
        fontsize=6.6,
        handlelength=2.0,
        handletextpad=0.55,
        columnspacing=1.7,
    )
    save(fig, "figure3_heldout_results")


def transfer_panel(
    ax: plt.Axes, frame: pd.DataFrame, *, title: str, selected: str, selected_label: str
) -> None:
    rho = spearmanr(
        frame["learning_improvement"], frame["validation_improvement"]
    ).statistic
    xmin = min(float(frame["learning_improvement"].min()), 0.0)
    xmax = max(float(frame["learning_improvement"].max()), 0.0)
    ymin = min(float(frame["validation_improvement"].min()), 0.0)
    ymax = max(float(frame["validation_improvement"].max()), 0.0)
    xpad = max((xmax - xmin) * 0.12, 0.008)
    ypad = max((ymax - ymin) * 0.12, 0.008)
    xmin, xmax = (xmin - xpad, xmax + xpad)
    ymin, ymax = (ymin - ypad, ymax + ypad)
    if xmax > 0 and ymax > 0:
        ax.add_patch(
            Rectangle(
                (0, 0),
                xmax,
                ymax,
                facecolor=PALE_GREEN,
                edgecolor="none",
                alpha=0.7,
                zorder=0,
            )
        )
    ax.axhline(0, color=GRAY, linewidth=0.7, zorder=1)
    ax.axvline(0, color=GRAY, linewidth=0.7, zorder=1)
    for row in frame.itertuples(index=False):
        selected_row = row.dimension_id == selected
        color = ORANGE if selected_row else BLUE
        ax.scatter(
            row.learning_improvement,
            row.validation_improvement,
            s=45 if selected_row else 26,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        if selected_row:
            ax.annotate(
                selected_label,
                (row.learning_improvement, row.validation_improvement),
                xytext=(-6, 8),
                textcoords="offset points",
                fontsize=5.7,
                color=ORANGE,
                ha="right",
                va="bottom",
                fontweight="bold",
                arrowprops={
                    "arrowstyle": "-",
                    "color": ORANGE,
                    "linewidth": 0.55,
                    "shrinkA": 2,
                    "shrinkB": 4,
                },
            )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_title(
        f"{title}    ρ = {rho:.2f}",
        loc="left",
        fontsize=8.5,
        fontweight="bold",
        color=DARK,
        pad=7,
    )
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.grid(color=LIGHT, linewidth=0.45, zorder=0)


def rank_transfer_figure() -> None:
    pgg = pd.read_csv(SOURCE / "figure3_pgg_singleton_transfer.csv")
    family = pd.read_csv(SOURCE / "figure3_chip_family_singleton_transfer.csv")
    bounds1120 = pd.read_csv(SOURCE / "figure3_bounds1120_singleton_transfer.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.25, 2.95))
    fig.subplots_adjust(left=0.085, right=0.99, top=0.88, bottom=0.19, wspace=0.34)
    transfer_panel(
        axes[0],
        pgg,
        title="a  Public goods",
        selected="P08",
        selected_label="Adverse-peer withdrawal",
    )
    transfer_panel(
        axes[1],
        family,
        title="b  Bargaining",
        selected="C07",
        selected_label="Package breadth",
    )
    transfer_panel(
        axes[2],
        bounds1120,
        title="c  Generalized 11–20",
        selected="B03",
        selected_label="Payoff sensitivity",
    )
    fig.supxlabel(
        "Improvement during profile learning", y=0.045, fontsize=7.8, color=DARK
    )
    fig.supylabel(
        "Improvement during validation", x=0.018, fontsize=7.8, color=DARK
    )
    save(fig, "figure4_dimension_transfer")


def cross_domain_portability_figure() -> None:
    """Plot leading one-feature, leading two-feature, and complete portability matrices."""
    frame = cross_domain_portability_source()
    domain_order = ["pgg", "chip", "bounds1120"]
    display = {
        "pgg": "Public goods",
        "chip": "Bargaining",
        "bounds1120": "Generalized\n11–20",
    }
    cmap = LinearSegmentedColormap.from_list(
        "cross_domain_alignment",
        [(0.0, "#B64945"), (0.5, "#F6F1F0"), (0.72, PALE_BLUE), (1.0, BLUE)],
    )
    norm = TwoSlopeNorm(vmin=-70, vcenter=0, vmax=100)
    fig, axes = plt.subplots(1, 3, figsize=(7.25, 2.35), sharey=True)
    fig.subplots_adjust(left=0.13, right=0.995, top=0.82, bottom=0.2, wspace=0.12)
    panel_specs = (
        ("selected", "a  Leading · 1 feature"),
        ("two_feature", "b  Leading · 2 features"),
        ("complete", "c  Complete profile"),
    )
    for panel_index, (ax, (scope, title)) in enumerate(
        zip(axes, panel_specs, strict=True)
    ):
        subset = frame[frame["profile_scope"].eq(scope)].copy()
        lookup = subset.set_index(["source_domain", "target_domain"])
        values = np.array(
            [
                [
                    float(lookup.loc[(source, target), "alignment"])
                    for target in domain_order
                ]
                for source in domain_order
            ]
        )
        ax.imshow(values, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")
        ax.set_xticks(range(3), ["Public\ngoods", "Bargaining", "11–20"])
        ax.set_yticks(
            range(3), [display[value].replace("\n", " ") for value in domain_order]
        )
        ax.tick_params(axis="x", length=0, pad=5, labelsize=6.3)
        ax.tick_params(axis="y", length=0, pad=6, labelsize=6.6)
        if panel_index:
            ax.tick_params(axis="y", labelleft=False)
        ax.set_title(
            title, loc="left", fontsize=8.1, fontweight="bold", color=DARK, pad=7
        )
        for boundary in np.arange(-0.5, 3.5, 1):
            ax.axhline(boundary, color="white", linewidth=2.0)
            ax.axvline(boundary, color="white", linewidth=2.0)
        for row_index, source in enumerate(domain_order):
            for column_index, target in enumerate(domain_order):
                record = lookup.loc[source, target]
                value = float(record["alignment"])
                rgba = cmap(norm(value))
                luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                text_color = "white" if luminance < 0.53 else DARK
                ax.text(
                    column_index,
                    row_index,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=9.0,
                    fontweight="bold",
                    color=text_color,
                )
                status = str(record["comparison_status"])
                symbol = (
                    "↑"
                    if status == "better_than_no_profile"
                    else "↓" if status == "worse_than_no_profile" else ""
                )
                if symbol:
                    ax.text(
                        column_index + 0.37,
                        row_index - 0.34,
                        symbol,
                        ha="center",
                        va="center",
                        fontsize=7.2,
                        fontweight="bold",
                        color=text_color,
                    )
                if source == target:
                    ax.add_patch(
                        Rectangle(
                            (column_index - 0.47, row_index - 0.47),
                            0.94,
                            0.94,
                            fill=False,
                            edgecolor=DARK,
                            linewidth=1.45,
                            zorder=4,
                        )
                    )
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.supxlabel("Game family simulated", y=0.015, fontsize=7.0, color=DARK)
    fig.supylabel("Profiles from", x=0.018, fontsize=7.0, color=DARK)
    save(fig, "figure5_cross_domain_portability")


def cross_domain_portability_source():
    return pd.read_csv(SOURCE / "figure5_cross_domain_portability.csv")
