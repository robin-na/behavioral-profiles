#!/usr/bin/env python3
"""Plot learning-only feature correlations used by the redundancy constraint.

The figure is descriptive: it visualizes the exact pairwise-complete Spearman
correlations and connected components used by the frozen primary selection
paths. It does not read validation outcomes or alter feature eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs/appendix/figures"
SOURCE = ROOT / "outputs/appendix/tables/figure_redundancy_correlations.csv"
PDF = OUTPUT_DIR / "figure_a1_redundancy.pdf"
PNG = OUTPUT_DIR / "figure_a1_redundancy.png"
SVG = OUTPUT_DIR / "figure_a1_redundancy.svg"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
DARK = "#172033"
MID_GRAY = "#87919A"
LIGHT_GRAY = "#D7DDE1"


@dataclass(frozen=True)
class Study:
    key: str
    title: str
    features: tuple[str, ...]
    nontrivial_components: tuple[tuple[str, ...], ...]
    representatives: tuple[str, ...]
    selection_order: tuple[tuple[str, int], ...]


STUDIES = (
    Study(
        key="public_goods",
        title="a  Public goods",
        features=(
            "P01",
            "P02",
            "P03",
            "P04",
            "P05",
            "P06",
            "P08",
            "P11",
            "P23",
            "P24",
            "P25",
            "P26",
            "P27",
            "P10",
            "P12",
            "P13",
            "P15",
            "P19",
            "P28",
        ),
        nontrivial_components=(
            ("P01", "P02", "P03", "P04", "P05", "P06", "P08", "P11"),
            ("P23", "P24", "P25", "P26", "P27"),
        ),
        representatives=("P08", "P23"),
        selection_order=(("P08", 1), ("P13", 2)),
    ),
    Study(
        key="bargaining",
        title="b  Bargaining",
        features=(
            "C01",
            "C19",
            "C03",
            "C08",
            "C06",
            "C14",
            "C20",
            "C02",
            "C05",
            "C07",
            "C09",
            "C10",
            "C11",
            "C17",
            "C18",
        ),
        nontrivial_components=(
            ("C01", "C19"),
            ("C03", "C08"),
            ("C06", "C14", "C20"),
        ),
        representatives=("C01", "C08", "C20"),
        selection_order=(("C07", 1), ("C02", 2)),
    ),
)


def _connected_components(
    correlation: pd.DataFrame,
    threshold: float = 0.70,
) -> set[frozenset[str]]:
    features = list(correlation.index)
    neighbors = {feature: set() for feature in features}
    for i, left in enumerate(features):
        for right in features[i + 1 :]:
            rho = correlation.loc[left, right]
            if pd.notna(rho) and abs(rho) >= threshold:
                neighbors[left].add(right)
                neighbors[right].add(left)
    components: set[frozenset[str]] = set()
    unseen = set(features)
    while unseen:
        root = unseen.pop()
        stack = [root]
        members = {root}
        while stack:
            current = stack.pop()
            new = neighbors[current] & unseen
            unseen -= new
            members |= new
            stack.extend(new)
        components.add(frozenset(members))
    return components


def validate_components(study: Study, correlation: pd.DataFrame) -> None:
    observed = _connected_components(correlation)
    expected_nontrivial = {
        frozenset(component) for component in study.nontrivial_components
    }
    observed_nontrivial = {component for component in observed if len(component) > 1}
    if observed_nontrivial != expected_nontrivial:
        raise ValueError(
            f"{study.key}: frozen and reconstructed components differ: "
            f"{observed_nontrivial} != {expected_nontrivial}"
        )


def build_source() -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    data = pd.read_csv(SOURCE)
    matrices = {}
    for study in STUDIES:
        panel = data[data.game_family == study.key]
        corr = panel.pivot(
            index="feature_left", columns="feature_right", values="spearman_rho"
        ).reindex(index=study.features, columns=study.features)
        counts = panel.pivot(
            index="feature_left", columns="feature_right", values="pairwise_numeric_n"
        ).reindex(index=study.features, columns=study.features)
        validate_components(study, corr)
        matrices[study.key] = (corr, counts)
    return matrices


def _style_ticks(axis: plt.Axes, study: Study) -> None:
    representative_set = set(study.representatives)
    for tick in [*axis.get_xticklabels(), *axis.get_yticklabels()]:
        if tick.get_text() in representative_set:
            tick.set_fontweight("bold")
            tick.set_color(DARK)
        else:
            tick.set_color("#4E5963")


def _plot_panel(
    axis: plt.Axes,
    study: Study,
    correlation: pd.DataFrame,
    cmap: LinearSegmentedColormap,
) -> object:
    matrix = correlation.loc[list(study.features), list(study.features)].to_numpy(
        dtype=float
    )
    image = axis.imshow(matrix, cmap=cmap, vmin=-1, vmax=1, interpolation="nearest")
    size = len(study.features)
    axis.set_xticks(range(size), labels=study.features, rotation=90)
    axis.set_yticks(range(size), labels=study.features)
    axis.tick_params(axis="both", which="both", length=0, pad=2)
    axis.set_title(study.title, loc="left", fontweight="bold", pad=7)
    axis.spines[:].set_visible(False)
    axis.set_anchor("N")
    _style_ticks(axis, study)

    start = 0
    for component in study.nontrivial_components:
        width = len(component)
        axis.add_patch(
            Rectangle(
                (start - 0.48, start - 0.48),
                width - 0.04,
                width - 0.04,
                fill=False,
                edgecolor=DARK,
                linewidth=1.15,
                zorder=4,
            )
        )
        start += width

    selection_colors = {1: ORANGE, 2: GREEN}
    for feature, order in study.selection_order:
        position = study.features.index(feature)
        axis.scatter(
            [size + 0.42],
            [position],
            s=75,
            color=selection_colors[order],
            edgecolor="white",
            linewidth=0.7,
            clip_on=False,
            zorder=5,
        )
        axis.text(
            size + 0.42,
            position,
            str(order),
            ha="center",
            va="center",
            fontsize=7.2,
            fontweight="bold",
            color="white",
            clip_on=False,
            zorder=6,
        )
    axis.set_xlim(-0.5, size + 0.9)
    axis.set_ylim(size - 0.5, -0.5)
    return image


def plot(matrices: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "xtick.labelsize": 8.3,
            "ytick.labelsize": 8.3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    cmap = LinearSegmentedColormap.from_list(
        "behavioral_portability_diverging",
        [BLUE, "#F7F8F8", ORANGE],
    )
    cmap.set_bad(LIGHT_GRAY)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.2, 4.3),
        gridspec_kw={"width_ratios": [19, 15], "wspace": 0.38},
    )
    image = None
    for axis, study in zip(axes, STUDIES):
        correlation, _ = matrices[study.key]
        image = _plot_panel(axis, study, correlation, cmap)
    if image is None:
        raise RuntimeError("No heatmap was drawn")
    color_axis = fig.add_axes([0.31, 0.075, 0.38, 0.025])
    colorbar = fig.colorbar(image, cax=color_axis, orientation="horizontal")
    colorbar.set_ticks([-1, -0.5, 0, 0.5, 1])
    colorbar.set_label("Spearman correlation (ρ)", labelpad=3)
    colorbar.outline.set_edgecolor(MID_GRAY)
    colorbar.outline.set_linewidth(0.6)
    fig.subplots_adjust(left=0.065, right=0.965, top=0.93, bottom=0.19)
    fig.savefig(PDF, bbox_inches="tight")
    fig.savefig(PNG, dpi=300, bbox_inches="tight")
    fig.savefig(SVG, bbox_inches="tight")
    svg_path = PDF.with_suffix(".svg")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n"
    )
    plt.close(fig)


def main() -> None:
    matrices = build_source()
    plot(matrices)


if __name__ == "__main__":
    main()
