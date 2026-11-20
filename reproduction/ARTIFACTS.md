# Artifact map

All table layouts and rows are archived in `data/published_tables.json`. The table generator preserves the paper's published values and captions. Aggregate CSVs provide machine-readable evidence where available.

| Paper artifact | Public inputs | Operation |
|---|---|---|
| Figure 1: framework | `assets/figure_1_framework.png` | Copy authored diagram |
| Figure 2: validation | `data/main/figure3_heldout_results.csv` | Redraw estimates and archived intervals |
| Figure 3: feature usefulness | Three `data/main/figure3_*_singleton_transfer.csv` files | Redraw points and recompute Spearman correlations |
| Figure 4: cross-family comparisons | `data/main/figure5_cross_domain_portability.csv` | Redraw matrix; check arrow directions against archived paired intervals |
| Figure A1: redundancy | `data/appendix/figure_redundancy_correlations.csv` | Redraw correlations and check connected components |
| Table 1: study overview | Published table rows | Re-typeset |
| Table 2: leading features | Published table rows | Re-typeset with references |
| Tables A1–A3: candidate features | Published rows; `feature_codebooks.tsv` | Re-typeset with references |
| Table A4: feature rankings | Published rows; three singleton-transfer CSVs | Re-typeset; recompute rank correlations separately |
| Table A5: selection comparisons | Published rows; `appendix_learning_comparisons.csv` | Re-typeset; recompute loss changes where both losses are available |
| Table A6: paired comparisons | Published rows; `appendix_paired_comparisons.csv` | Re-typeset archived estimates and intervals |
| Table A7: validation scores | Published rows; `figure3_heldout_results.csv` | Re-typeset; test agreement with all 21 figure rows |
| Table A8: normalization references | Published rows; normalization columns in `figure3_heldout_results.csv` | Re-typeset archived reference losses |
| Table A9: persona calibration | Published rows; `calibration.csv` | Re-typeset archived results |
| Table A10: cross-family bargaining observations | Published rows; `cross_family_bargaining_support.csv` | Re-typeset archived counts and reference losses |
| Table A11: model comparisons | Published rows; `appendix_model_comparisons.csv` | Re-typeset archived results |
| Table A12: generic-profile controls | Published rows; generic comparisons in `appendix_paired_comparisons.csv` | Re-typeset archived results |
| Table A13: action-level diagnostics | Published rows; `table_s4_bounds1120_design_diagnostics.csv` | Re-typeset archived results |
| Appendix feature-identification detail | `feature_identification.tsv`, `table_s1_all_dimension_identifiability_distributions.csv` | Preserve aggregate rates and score distributions |
| Appendix alternative bargaining split | `interpolation_alignment.csv`, `interpolation_comparisons.csv` | Preserve aggregate scores and paired comparisons discussed in the text |
| Simulation counts | `observation_counts.csv` | Preserve aggregate analysis counts |
| Numerical model-output summaries | `data/model_outputs/simulated_outcome_counts.csv.gz` | Recompute unweighted counts, means, and ranges by family, analysis, and condition |

`pgg_alignment_paired_alignment.csv` preserves supplementary paired alignment-score differences alongside the task-specific loss differences. These are archived results, not intervals recalculated from marginal figure bars.
