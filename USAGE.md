# Using your own literature and human data

Keep your study files in a private directory outside this repository. A researcher or coding assistant follows `skills/learn-behavioral-profiles/SKILL.md`; the scripts implement the checks and calculations. They do not independently read papers or interpret human behavior.

## What you provide

1. **A prediction question:** the behavior, population, setting, and intended use of the simulations.
2. **Literature:** relevant papers, excerpts, or an agreed search scope. The resulting codebook records where each candidate feature comes from and how your records can support it.
3. **Human records:** surveys, interview transcripts, behavioral logs, or other evidence you are permitted to use. Explain repeated observations, interactions, dates, and sampling weights. An adapter maps these records to the [input contract](skills/learn-behavioral-profiles/references/contracts.md).
4. **Outcomes for comparison:** human outcomes for learning and final validation, plus a defensible split that keeps unavailable information out of predictions. If these outcomes are unavailable, you can construct profiles but cannot establish their predictive usefulness.
5. **Simulation choices:** the tasks and information shown to the simulator, model settings, comparison metric, uncertainty unit, and stopping criterion. Large model jobs require separate authorization and a cost estimate.

## What happens

For example, suppose you want to simulate how customers respond to a new service policy. You provide relevant behavioral literature, earlier customer interactions, and separately reserved responses to policy changes. The assistant helps define features that the earlier interactions can support, documents their scoring rules, and prepares your study configuration. It should not treat an unobserved behavior as an average feature value.

The workflow then checks the study configuration and prepares extraction requests. A separately chosen model or transparent rule answers those requests. The scripts validate imported assessments and construct profiles, retaining evidence links for your private audit. You inspect a sample for substantive accuracy.

Next, the workflow prepares simulation conditions. You run them with your chosen simulator and import numerical predictions. Forward feature selection compares candidate additions using learning outcomes only. When the stopping rule is met, the selected contents are frozen. Final evaluation compares those contents, no profile, and all candidate features on validation outcomes, including paired uncertainty intervals.

## What you receive

- A literature-grounded codebook and documented mapping from your records.
- Extraction requests, checked assessments, and evidence-grounded profiles for private review.
- Simulation plans and, optionally, local EDSL export objects.
- A recorded feature-selection path and frozen selection artifact.
- A validation report with losses and paired differences, plus limitations of the evaluation.

The bundled evaluator supports one explicit construction/learning/validation split, bounded numerical or categorical features, and the losses documented in the contract. New representations, outcomes, cross-fitting designs, or model execution systems need an adapter. The synthetic examples demonstrate the complete file workflow; they do not establish performance on a real application.
