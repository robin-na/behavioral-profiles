# Public data boundary

The release contains aggregate analysis tables, literature-grounded feature definitions, published table rows, a framework diagram, bibliographic metadata, and counts of numerical simulated outcomes. It excludes raw human observations from all three empirical settings; individual personas and behavioral profiles; evidence excerpts; participant, cohort, game-record and model-request identifiers; prompts; and raw API input/output files.

## Aggregate analysis tables

`data/main` and `data/appendix` contain estimates, uncertainty intervals, sample counts, feature definitions, identification rates, feature correlations, and comparison summaries. An experimental design or game family can be described in aggregate without including its participants' records. Feature-score summaries describe distributions, not individual profiles.

Many CSVs retain compact identifiers used by the analysis. `pgg` means public goods, `chip` means bargaining, and `bounds1120` means generalized 11–20. In the validation figure's `category` column, `selected_1`, `selected_2`, `complete`, and `none` identify the leading one-feature, leading two-feature, all-feature, and no-profile conditions. The `condition` column retains the original analysis identifier. Feature identifiers such as P08, C05, and B02 are defined in the published codebook tables and ancillary TSV. Original names are retained to keep joins unambiguous; plot labels and captions use the paper's terminology.

## Numerical simulation outputs

`data/model_outputs/simulated_outcome_counts.csv.gz` contains only:

| Field | Meaning |
|---|---|
| `family` | Public goods, bargaining, or generalized 11–20 |
| `analysis` | Analysis group, such as validation, feature comparisons, or model comparisons |
| `condition` | Analysis condition identifier |
| `simulated_value` | Parsed numerical simulation outcome |
| `count` | Number of outputs with that value in the family/analysis/condition group |

Public goods uses predicted future normalized efficiency; bargaining uses final surplus ratio; generalized 11–20 uses the chosen request. Values are retained at their parsed numerical precision. Equal numerical values are counted together. Some values occur only once, but no record key or associated text is released. These files include outputs from general-purpose persona comparisons, but never the personas themselves.

These are **unweighted marginal counts**. They omit human outcomes, human-derived weights, record-level pairing, and payoff-design assignments. Consequently, pooled simulated means should not be read as the paper's distributional-alignment scores or used as substitutes for its weighted comparisons. `model_outputs/manifest.json` records exported fields and total counts by analysis group.

## Version and integrity

`release.json` identifies the manuscript snapshot and records hashes of the upstream artifacts. `input_checksums.json` checks the public input files themselves before reproduction. Internal research paths and repository history are not included. The archived arXiv table rows and the figure-input tables are checked for agreement separately from these file-integrity checks.
