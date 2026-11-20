# Input contracts and extension points

All inputs are UTF-8 JSON. Python 3.10+ is sufficient for the core scripts; only EDSL export needs an extra package. `scripts/make_examples.py` generates complete, runnable examples. Use them as structural examples, never as real literature or model results.

## Study definition

`study.json` has `schema_version: 1`, `study_id`, `research_question`, `profile_unit`, `partition_unit`, `split_rationale`, and `prediction_target`. Set `synthetic: true` only for invented demonstrations.

- `literature`: entries with `id`, `citation`, `location` (URL or accessible file), and `status: verified`. Synthetic demos may use `status: synthetic`.
- `features`: entries with `id`, `name`, `definition`, `type`, `scoring_rule`, `evidence_requirement`, `unsupported_when`, `basis`, and `references`. Each reference identifies `literature_id`, `locator`, and `support`. Exploratory features may have no literature reference but must have a substantive definition and justification in the study documentation.
- Types: `numeric` requires finite `minimum` and `maximum`; `ordinal` and `categorical` require unique string `levels`. Order matters only for ordinal interpretation; ordinal distances are not silently treated as numeric distances.
- `selection`: `min_improvement` (nonnegative absolute loss decrease), `max_features`, and optional disjoint `redundancy_groups` containing feature IDs. Groups are researcher-defined; the scripts do not infer semantic redundancy from correlations alone. Ties are resolved by lexical feature ID after overall loss. The feature inventory and stopping rule are fixed before selection.
- `evaluation`: `outcome` (same type specification), `metric`, `aggregation: weighted_by_observation`, integer `bootstrap_draws` of at least 100, and integer `seed`. Demonstrations use 200 draws for speed; choose enough draws for the precision required by a real analysis.
- `files`: relative paths for `construction`, `learning_tasks`, `learning_outcomes`, `validation_tasks`, and `validation_outcomes`.

The study fingerprint covers the complete specification, construction records, and both task lists. It deliberately excludes outcome files. Fingerprints detect accidental changes; they are not access control or cryptographic attestations of a study's honesty.

## Construction records and tasks

Construction is a list of records with `id`, `partition_id`, and `evidence`. Each evidence entry has an `id` unique within its record, a `kind` (`survey`, `event`, `text`, `interaction`, or `other`), `content` (JSON-compatible structured data or text), and `locator`. Keep relevant time, alternatives, opportunities, instructions, and context within that evidence. File adapters should preserve these semantics rather than flattening every input to one row per person.

Learning and validation task lists contain only:

| Field | Meaning |
|---|---|
| `id` | Unique task identifier across both stages |
| `partition_id` | Unit that must not cross construction/learning/validation boundaries |
| `cluster_id` | Independent unit to resample; all its tasks remain together |
| `comparison` | Named learning comparison in which an addition must improve |
| `stratum` | Context in which outcome distributions are compared and clusters resampled |
| `prompt` | The target task and permitted context, excluding its human outcome |
| `profile_id` | Assigned construction record; held constant across conditions |

Choose `partition_id` to reflect the actual generalization design. For future behavior of the same person, an independently justified time/session partition may be appropriate; for unseen people use person-level separation. The script checks declared IDs, not whether a misleading mapping hides overlap. Review repeated people, interactions, duplicated records, chronology, and prompt content separately. Cross-fitting, overlapping hierarchical clusters, and interacting simulations need a documented adapter; the initial bundled implementation does not implement those designs.

Each cluster belongs to one partition and one validation stratum. Cluster IDs cannot cross learning and validation. Validation requires at least two clusters per stratum; this is a computational minimum, not assurance of reliable inference.

Outcome files contain rows `{task_id, value, weight}`. Multiple observed outcomes per task are allowed. Weights must be positive and finite. Their interpretation (frequency, sampling, or another prespecified weighting scheme) must be documented. Simulation draws receive the task's total human weight divided equally among its draws.

## Assessments and profiles

An assessment file contains `study_fingerprint`, `provenance`, and an `assessments` list. There is exactly one assessment for every construction-record/candidate-feature pair:

```json
{"record_id":"r1","feature_id":"f1","identifiable":true,
 "value":0.7,"certainty":0.8,"evidence_ids":["e1"],
 "reason":"Explanation tied to the scoring rule."}
```

Unsupported assessments use `identifiable: false`, `value: null`, and `certainty: null`, with a reason. Evidence references may be empty. Supported assessments need valid referenced evidence, a value within the declared scale, and certainty in [0,1]. The script verifies references, not the entailment of a behavioral inference.

`provenance.method` is `model`, `deterministic`, `human`, or `synthetic`, with a `description`. Model extraction also requires `model`, nonempty `settings`, and `prompt_hash`. Record model snapshot, sampling/reasoning settings, extraction prompt, and parsing method. Synthetic provenance is rejected outside synthetic studies.

The profile builder retains evidence references and all missingness explanations. The plan renderer shows only identifiable selected features, including name, definition, value, certainty, and actual referenced evidence. No-profile plans have an empty profile. No undocumented summary persona is added.

## Prediction files

Keep learning and validation predictions in separate files. Each has `study_fingerprint`, `split`, `provenance`, and `predictions`:

```json
{"task_id":"learning-1","draw_id":"replicate-0",
 "features":["f1"],"value":0.6}
```

`features: []` means no profile. Conditions are canonicalized by sorted feature IDs. Every supplied condition must cover the same task/draw pairs exactly once. Failed or missing predictions are errors, not silently dropped cases. Do not manufacture missing results.

Prediction provenance uses `method: model`, `deterministic`, or `synthetic` and a `description`. Model outputs additionally need `model`, nonempty `settings`, and `plan_hashes`. Keep exact generated plans and model settings privately; the importer records provenance but cannot establish that an external executor followed the plans. Add a provider-specific response parser when needed. Never treat an EDSL result cache export as automatically appropriate for public release.

## Metrics and uncertainty

- `mae` and `mse`: expected absolute/squared error over each task's observed outcomes and simulation draws, then averaged with the declared human weights.
- `error_rate`: the analogous mismatch probability, suitable for categories or exact-choice prediction. It is not a probability forecast scoring rule.
- `total_variation`: distance between weighted empirical outcome distributions within each stratum, averaged using stratum human weight.
- `wasserstein`: weighted one-dimensional Wasserstein distance within each stratum, with the same averaging. Requires numeric outcomes.
- `custom`: pass `--metric-adapter /path/to/metric.py` to both selection and evaluation. It exports `loss(human, simulated)` and returns a finite nonnegative scalar, lower being better. Arguments are lists with task metadata, `value`, and effective `weight`. The adapter runs once per requested comparison or bootstrap sample and is responsible for its own aggregation. Treat it as executable trusted code; use a self-contained file or separately pin its dependencies. The workflow pins this file's hash in the selection artifact.

The bundled losses do not normalize to a paper-specific alignment scale. They do not infer treatment effects or score arbitrary free-text responses. For those tasks define and justify an outcome representation and custom evaluator; do not silently use an LLM judge.

Selection needs no profile and every eligible one-feature addition at the current step. It returns `complete: false` and `required_conditions` if any are missing, and does not choose among a partially observed set. Add requested predictions and rerun; cached results can be reused. A completed selection can contain zero features. Validation requires the frozen selected condition, no profile, and the complete candidate set. This provides a minimum baseline comparison; additional reporting is an extension rather than post-validation reselection.

For intervals, the same sampled clusters and multiplicities are applied to every condition and its human outcomes, within each declared stratum. The percentile intervals cover paired loss differences conditional on the supplied simulation outputs. They do not estimate uncertainty from rerunning model generation, codebook development, or feature selection. Archive actual paired draws if a later public reproduction package needs them; separate condition intervals are insufficient.

## Adding a new application

Write an input adapter from the researcher's format to these records, tasks, and outcomes. Add a synthetic fixture that preserves its dependence structure and information boundaries. Use a custom metric when the bundled losses do not match the research question. Extend the simulation executor for stateful interactions; do not equate independent EDSL survey responses with a multi-agent environment. Validate the adapted information flow and evaluation before running a large study.
