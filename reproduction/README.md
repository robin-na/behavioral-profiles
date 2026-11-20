# Reproducing the paper displays

This package corresponds to the **October 31, 2026 arXiv snapshot**, identified by manuscript and PDF hashes in `release.json`. Main-text and appendix outputs are kept separate. Older ISR numbering is not used for the generated figures and published tables; some CSV filenames retain their original analysis identifiers.

From the repository root:

```sh
python -m pip install -r requirements.txt
python reproduction/reproduce.py
python -m unittest discover -s tests -v
```

The calculation needs no model access, API keys, or private research files. Installing dependencies initially requires internet access or an existing local package cache. Once installed, the reproduction script runs offline.

The outputs are:

- `outputs/main/figures`: Figures 1–4. Figure 1 is the authored diagram; Figures 2–4 are regenerated in PDF, SVG, and PNG.
- `outputs/appendix/figures`: Figure A1, regenerated in PDF, SVG, and PNG.
- `outputs/main/tables` and `outputs/appendix/tables`: published table fragments, cell archives, and aggregate input tables.
- `outputs/derived`: recomputed feature rank correlations, arithmetic loss changes, paired-interval directions, and unweighted numerical simulation summaries.
- `outputs/published_tables.tex`: a table collection with citations and captions preserved from the paper.
- `outputs/reproduction_report.json`: execution counts and the scope of the calculations.

To compile the table collection, install Tectonic or another LaTeX distribution, then run:

```sh
cd reproduction/outputs
tectonic published_tables.tex
```

Tectonic may need to download its TeX bundle on the first use. This optional compilation is independent of the offline numerical reproduction. Table and figure references within captions refer to the paper. The cell CSVs retain LaTeX markup and citations; they are lossless cell archives rather than newly estimated statistics.

## Scope of reproducibility

Archived aggregate inputs regenerate the published displays. The script independently recomputes feature rank correlations, loss differences where both component losses are available, and simulation summaries. It also checks that the cross-family arrows agree with the archived paired confidence intervals.

The original human-versus-simulation Wasserstein distances, human resampling references, feature extraction, learning comparisons, and bootstrap intervals are not re-estimated. Their original observation-level inputs and assignments are intentionally absent. In particular, the released numerical model-output counts do not retain pairings, payoff-design assignments, or human-derived weights and cannot reconstruct those estimators.

The [artifact map](ARTIFACTS.md) distinguishes drawing a figure, re-typesetting a table, and recomputing a quantity. The [data description](DATA.md) explains the included files. Checksums establish that files match this release; they do not independently validate the original analysis.
