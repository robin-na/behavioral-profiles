# Behavioral profiles

This repository contains two independent resources:

- **[Learn behavioral profiles](skills/learn-behavioral-profiles/SKILL.md):** a reusable research workflow for defining candidate features from literature, constructing evidence-grounded profiles from human records, and selecting their contents through simulation. It includes offline scripts, synthetic examples, and an optional Expected Parrot EDSL exporter.
- **[Paper reproduction](reproduction/README.md):** code and aggregate inputs for regenerating the figures and tables in *Designing Behavioral Profiles for Language Model Simulation of Out-of-Distribution Human Behavior*, by Robin Na, Kehang Zhu, Logan Cross, and Michiel A. Bakker. The release corresponds to the October 31, 2026 arXiv manuscript snapshot.

The skill does not depend on the paper's datasets. The reproduction package contains no raw human records, individual personas or profiles, evidence excerpts, participant identifiers, or raw model request/response files.

## Try the skill

The core workflow needs Python 3.10 or newer and uses only the standard library. From the repository root:

```sh
python skills/learn-behavioral-profiles/scripts/make_examples.py --out /tmp/behavioral-profile-examples
python skills/learn-behavioral-profiles/scripts/run_examples.py --examples /tmp/behavioral-profile-examples --out /tmp/behavioral-profile-demo
python -m unittest discover -s skills/learn-behavioral-profiles/tests -v
```

These demonstrations use invented records and predictions. They do not make model calls. Start with the [usage guide](USAGE.md) to apply the workflow to your own literature and data.

The optional [EDSL integration](skills/learn-behavioral-profiles/references/edsl.md) exports local EDSL objects. It does not execute a study, upload private data, or publish objects to Expected Parrot. Its separately pinned dependency is in `skills/learn-behavioral-profiles/requirements-edsl.txt`.

## Reproduce the paper displays

With Python 3.12 in a virtual environment:

```sh
python -m pip install -r requirements.txt
python reproduction/reproduce.py
python -m unittest discover -s tests -v
```

Outputs appear in `reproduction/outputs/main`, `reproduction/outputs/appendix`, and `reproduction/outputs/derived`. The script redraws three empirical main figures and one appendix figure, copies the authored framework diagram, and reconstructs all 15 published tables as LaTeX and cell archives. An optional LaTeX compilation produces a readable table collection; see the reproduction guide.

This is **reproduction from released aggregate results**. The original human-comparison estimates and confidence intervals are preserved, not re-estimated. Feature rank correlations, arithmetic changes in learning loss, interval-direction checks, and unweighted simulation summaries can be recomputed from the included inputs. Re-running the original comparisons would require human records and experimental assignments that are not distributed here.

## Release and reuse

See [the artifact map](reproduction/ARTIFACTS.md) for the inputs behind each display and [the data description](reproduction/DATA.md) for included fields and exclusions. Input checksums detect changes to the archived evidence. See [licensing status](LICENSING.md) before redistribution.
