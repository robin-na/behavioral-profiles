#!/usr/bin/env python3
"""Regenerate paper displays from archived aggregates, without models or human records."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

os.environ.setdefault("MPLBACKEND", "Agg")
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"


def verify_inputs():
    expected = json.loads((ROOT / "input_checksums.json").read_text())
    actual = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for directory in [DATA, ROOT / "assets"] for p in directory.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Input files differ from the release checksums; inspect the changes before reproducing.")


def table_outputs():
    tables = json.loads((DATA / "published_tables.json").read_text())
    references = {"fig:heldout": "2", "fig:cross-family": "4", "oa-sec:outcomes": "E"}
    references.update({t["label"]: t["number"] for t in tables})
    preamble = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs,array,longtable,amsmath,amssymb,setspace,graphicx,microtype}
\usepackage[round]{natbib}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\renewcommand{\theHtable}{\thetable}
\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\setlength{\tabcolsep}{3pt}
\setlength{\LTcapwidth}{\textwidth}
\begin{document}
\section*{Published tables}
These tables preserve the published values and captions in the October 31, 2026
arXiv snapshot. Statistical estimates and confidence intervals are archived;
they are not re-estimated by this script. Figure and section references refer
to the paper. The bibliography includes works cited in these tables.
"""
    combined = [preamble]
    for t in tables:
        folder = OUT / t["scope"] / "tables"
        folder.mkdir(parents=True, exist_ok=True)
        block = t["template"].replace("@@ROWS@@", "\n".join(t["rows"]))
        block = re.sub(r"\\ref\{([^}]+)\}", lambda m: references[m[1]], block)
        (folder / f"{t['id']}.tex").write_text(block + "\n")
        # Cells retain LaTeX markup and citations to avoid changing their meaning.
        with (folder / f"{t['id']}_cells.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["row_number", "cells_as_json"])
            for i, row in enumerate(t["rows"], 1):
                writer.writerow([i, json.dumps(re.split(r"(?<!\\)&", row), ensure_ascii=False)])
        n = int(t["number"].lstrip("A"))
        combined.append("\\clearpage\n" + (r"\renewcommand{\thetable}{A\arabic{table}}" if t["scope"] == "appendix" else r"\renewcommand{\thetable}{\arabic{table}}") + f"\n\\setcounter{{table}}{{{n-1}}}\n" + block)
    combined.append("\n\\clearpage\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n")
    (OUT / "published_tables.tex").write_text("\n".join(combined))
    shutil.copy2(ROOT / "assets/references.bib", OUT / "references.bib")
    return len(tables)


def derived_outputs():
    derived = OUT / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    ranks = []
    for family, name in [("Public goods", "pgg"), ("Bargaining", "chip_family"), ("Generalized 11–20", "bounds1120")]:
        frame = pd.read_csv(DATA / "main" / f"figure3_{name}_singleton_transfer.csv")
        ranks.append({"family": family, "features": len(frame),
                      "spearman_rho": float(spearmanr(frame.learning_improvement, frame.validation_improvement).statistic)})
    pd.DataFrame(ranks).to_csv(derived / "feature_rank_correlations.csv", index=False)
    # Recompute marginal numerical distributions only, without human-derived weights.
    counts = pd.read_csv(DATA / "model_outputs/simulated_outcome_counts.csv.gz")
    summaries = []
    for (family, analysis, condition), frame in counts.groupby(["family", "analysis", "condition"]):
        summaries.append({"family": family, "analysis": analysis, "condition": condition,
                          "outputs": int(frame['count'].sum()),
                          "unweighted_mean_simulated_value": float((frame.simulated_value * frame['count']).sum() / frame['count'].sum()),
                          "min_simulated_value": float(frame.simulated_value.min()),
                          "max_simulated_value": float(frame.simulated_value.max())})
    pd.DataFrame(summaries).to_csv(derived / "unweighted_simulation_summaries.csv", index=False)
    learning = pd.read_csv(DATA / "appendix/appendix_learning_comparisons.csv")
    learning['recomputed_change'] = learning.candidate_loss - learning.current_loss
    learning.to_csv(derived / "learning_loss_changes.csv", index=False)
    cross = pd.read_csv(DATA / "main/figure5_cross_domain_portability.csv")
    def direction(row):
        if pd.isna(row.paired_ci_low) or pd.isna(row.paired_ci_high):
            return "not available"
        return "lower loss" if row.paired_ci_high < 0 else "higher loss" if row.paired_ci_low > 0 else "interval includes zero"
    cross['paired_interval_direction'] = cross.apply(direction, axis=1)
    cross.to_csv(derived / "cross_family_interval_directions.csv", index=False)
    return len(summaries)


def main():
    verify_inputs()
    for scope in ["main", "appendix"]:
        (OUT / scope / "figures").mkdir(parents=True, exist_ok=True)
        folder = OUT / scope / "tables"
        folder.mkdir(parents=True, exist_ok=True)
        for path in (DATA / scope).iterdir():
            shutil.copy2(path, folder / path.name)
    from plotting import main_figures, redundancy
    main_figures.style()
    main_figures.headline_figure()
    main_figures.rank_transfer_figure()
    main_figures.cross_domain_portability_figure()
    redundancy.main()
    shutil.copy2(ROOT / "assets/figure_1_framework.png", OUT / "main/figures/figure_1_framework.png")
    tables = table_outputs()
    conditions = derived_outputs()
    report = {"input_checksums_verified": True, "main_figures": 4, "appendix_figures": 1,
              "tables_typeset_from_archived_rows": tables, "simulation_condition_summaries": conditions,
              "original_confidence_intervals_reestimated": False, "model_calls": 0}
    (OUT / "reproduction_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
