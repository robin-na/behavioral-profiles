# Release-candidate verification

Checked locally on November 20, 2026 with Python 3.12 and the pinned reproduction dependencies.

- Copied the distributable files to a temporary directory, without original Git history or generated outputs.
- Ran the reproduction script with network connections and reads of the private research workspace blocked.
- Passed nine release checks covering input checksums, the numerical-output field allowlist and counts, excluded identifiers, local-path and credential-pattern screening, all 21 validation-table values against figure inputs, the three reported feature rank correlations, available learning-loss differences, paired-interval directions, and the table inventory.
- Passed all 20 skill tests, including the two optional EDSL export tests, under the same isolation conditions.
- Completed the three synthetic examples: survey responses, repeated choices, and interview text. No model calls were made.
- Compiled and inspected the table PDF and inspected the five figures. The table collection retains published rows and citations; compilation is separate from numerical reproduction.

This verifies the public workflow and its released inputs. It does not independently re-estimate the paper's original human-comparison statistics or establish extraction quality on new data. The proposed GitHub checks have not yet run on GitHub. The code and reusable skill use the MIT License. The repository is intended to remain private under robin-na; reuse terms for the research materials remain to be specified before a public release.
