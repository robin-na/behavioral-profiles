---
name: learn-behavioral-profiles
description: Develop literature-grounded behavioral profiles from human records and select their contents through simulation against human outcomes. Use for adapting this workflow to surveys, interviews, behavioral logs, or interactions, including EDSL studies.
---

# Learn behavioral profiles

Help a researcher define candidate behavioral features, infer supported values from their human data, and test which profile contents help simulate a specified behavior. Begin with the researcher's question and available evidence. A game, numerical feature scale, model, or evaluation metric is not built into this method.

This skill includes offline scripts and an optional EDSL exporter. They prepare and check artifacts; they do not search the literature, infer behavioral features, or call models on their own. Use available research tools and model execution tools for those steps when authorized. The synthetic examples are software demonstrations, not empirical evidence for the method.

## Establish the application

Read [the input contract](references/contracts.md) before preparing a study. Identify:

- The behavior to predict, population, context, and intended use. Distinguish predictions for particular people from population distributions or effects of a design change.
- What a profile describes: a person, session, group, or response type. Preserve repeated observations, interaction partners, opportunities to act, and sampling weights where relevant.
- What information is available when a prediction is made. Keep target outcomes, future observations, and private information unavailable to that prediction out of extraction and simulation prompts.
- How construction records, learning comparisons, and validation outcomes are separated. Choose grouping and time boundaries for the actual design; do not default to splitting individual rows 80/20. The bundled evaluator supports one explicit construction/learning/validation split. Cross-fitting or dynamic environments require an adapter and a documented design.
- The outcome, loss function, weighting, uncertainty unit, and stopping criterion. Freeze these before inspecting final validation outcomes. If no suitable human outcomes exist, offer profile construction only and state that predictive usefulness remains untested.

Use existing answers and documentation. Ask only for consequential missing choices; do not require approval for routine formatting or file handling.

## Build a literature-grounded codebook

Read [literature and evidence guidance](references/literature.md). Use supplied papers or search the agreed literature. Produce a traceable candidate codebook with definitions, supporting passages, operational scoring rules, and evidence requirements. Distinguish an established construct from a proposed operationalization and from an exploratory feature. Do not imply that a newly inferred feature is a validated psychological measure.

Map candidates to the actual data. A missing opportunity to observe behavior is not evidence of an absence of that behavior. Retain a literature-supported feature in the candidate inventory even if the present dataset cannot identify it; record the reason. Let the researcher review substantive codebook choices before large-scale extraction. Preserve previously authorized decisions.

The feature types supported by the scripts are bounded numeric, ordered categories, and unordered categories. Add a documented adapter for other representations; do not coerce them silently into a 0–10 score. EDSL's trait-description codebook is an export view of this richer codebook, not its replacement.

## Construct and inspect profiles

Resolve script paths relative to this skill directory. Commands below use `scripts/workflow.py` from that directory and Python 3.10+.

1. Prepare the study JSON and construction records using the contract. Run:
   `python scripts/workflow.py check --study study.json`
2. Build evidence-bounded requests:
   `python scripts/workflow.py prepare --study study.json --out private/extraction.json`
3. Use a separately authorized generator to answer those requests in the documented assessment format. For machine-readable records, a transparent deterministic rule may be preferable to an LLM. Record which method was used.
4. Validate imported assessments and build profiles:
   `python scripts/workflow.py profiles --study study.json --assessments private/assessments.json --out private/profiles.json`

Each identifiable feature needs a value, certainty, and evidence IDs belonging to that record. Unsupported features have no value and are omitted from displayed profiles. Certainty is a reported assessment, not a calibrated probability. Review a sample against its original records: the script can validate types and evidence references, but cannot establish that an interpretation is substantively correct.

## Compare, select, and validate

Build profile conditions with `plan`; keep profile assignments and target tasks the same across comparisons. The plan contains no human target outcomes. Supply a JSON list of feature IDs with `--features` (use `[]` for no profile), and choose `--split learning` or `validation`:

`python scripts/workflow.py plan --study study.json --profiles private/profiles.json --split learning --features '["feature_a"]' --out private/plan.json`

Execute the planned tasks with the researcher's simulator and import predictions as specified in the contract. For EDSL, read [the integration notes](references/edsl.md). Preview exact task/profile content before execution. Running models, uploading private objects, and publishing results are separate actions; preparing artifacts does not authorize them. Estimate the cost and obtain authorization before a new model job. Do not automatically retry paid calls.

Run forward feature selection with `select`. It reports missing candidate conditions instead of interpreting missing predictions as poor performance. Generate the requested conditions and rerun selection using learning results only. Each accepted addition must improve the configured loss by more than the chosen threshold in every named learning comparison and overall. Explicit redundancy groups are optional. No statistical significance test is implied by this stopping rule.

`python scripts/workflow.py select --study study.json --predictions private/learning_predictions.json --out private/selection.json`

Freeze the completed selection artifact. Generate validation predictions for the frozen condition, no profile, and the complete candidate set, then run:

`python scripts/workflow.py evaluate --study study.json --selection private/selection.json --predictions private/validation_predictions.json --out private/evaluation.json`

Evaluation reports losses and paired cluster-bootstrap differences. Use the sign convention in the output: negative selected-minus-baseline loss favors the selected profile. The bootstrap is conditional on the supplied model outputs. For additional simulation draws or other uncertainty designs, adapt the evaluation explicitly. Do not alter feature selection based on validation performance. An all-missing or unhelpful candidate set may correctly select no profile.

## Deliver and reuse

Return the codebook, data mapping, model/prompt settings, extraction audit, selection path, validation report, and limitations of the evidence. Distinguish supported feature values from their predictive usefulness and descriptive patterns from causal conclusions.

Keep human data and individual profiles in the researcher's private workspace. Public examples use only invented records. EDSL exports may contain evidence and must remain private unless separately approved for release. Keep any paper reproduction package separate; this skill does not depend on it.

Run the bundled demonstrations and tests without models or API keys:

```sh
python scripts/make_examples.py --out /tmp/behavioral-profile-examples
python scripts/run_examples.py --examples /tmp/behavioral-profile-examples --out /tmp/behavioral-profile-demo
python -m unittest discover -s tests -v
```

The examples cover structured survey data, repeated behavioral records, and interview text. All literature entries and model outputs in them are explicitly synthetic fixtures. Consult [the contracts](references/contracts.md) for extending ingestion, outcomes, and evaluation to a new application.
