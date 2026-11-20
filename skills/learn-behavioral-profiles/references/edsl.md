# EDSL integration

The core workflow is provider-independent. The exporter is an optional bridge to EDSL's Survey, Scenario, and Agent objects; it does not execute jobs or upload objects.

```sh
python scripts/edsl_export.py --mode extraction --input private/extraction.json --out private/extraction_edsl.json
python scripts/edsl_export.py --mode simulation --input private/plan.json --out private/simulation_edsl.json
```

Install EDSL in the researcher's chosen environment if needed. Verify the installed version's object constructors and serialization; the exporter records the version. The core workflow itself has no dependency on EDSL.

The optional `requirements-edsl.txt` pins EDSL 1.0.5, the installed version used for the November 19, 2026 checks. All 20 automated tests passed, including serialization and reconstruction for the three synthetic studies with socket connections blocked. This verifies offline export, not live model execution or compatibility with every EDSL release. In restricted environments, set `EDSL_LOG_DIR` to a writable temporary directory before importing EDSL; its separate best-effort main logger may still warn about its default home-directory location.

Extraction uses a free-text question requesting JSON, with each record/codebook pair in a Scenario. Parse and validate the answer with the profile builder; a fluent answer or a successful API response is not sufficient. A future executor can use EDSL's structured response types where supported without changing the assessment contract.

Simulation uses a numeric or categorical question, one Scenario per target task, and an Agent containing exactly the displayed behavioral profile. When a profile is empty the assignment uses no custom Agent. Stable identifiers remain in the assignment manifest and are not included as simulated traits. Agent instructions and question wording are part of the method and need review when adapting an existing prompt.

The exported JSON has `survey`, `agents`, `scenarios`, and `assignments`. Reconstruct objects with `Survey.from_dict`, `Agent.from_dict`, and `Scenario.from_dict`. Each assignment names one intended scenario/agent pair. Build a job for that pair (omit the agent when `agent_key` is null). Do not run a Cartesian crossing of the entire agent and scenario lists: that would change the planned assignments. Explicitly configure the model and repeat/draw semantics. Inspect rendered prompts before executing.

EDSL objects and cached Results may contain original records, evidence quotations, and individual profiles. Save private working artifacts locally by default. Model execution may send records to the selected service; Expected Parrot remote execution, remote caching, and public object sharing are separate choices. Decide these settings before an authorized run. Do not call `.push()` as part of exporting or reproducing figures.

Useful upstream references (reviewed November 19, 2026):

- [EDSL skills collection](https://github.com/expectedparrot/ep-skills): existing study/agent creation and analysis workflows.
- [Agent reference skill](https://github.com/expectedparrot/ep-skills/blob/main/plugins/edsl-research/skills/edsl-agent-reference/SKILL.md): trait templates, codebooks, and operations.
- [Survey reference skill](https://github.com/expectedparrot/ep-skills/blob/main/plugins/edsl-research/skills/edsl-survey-reference/SKILL.md): response types, prompt templates, and memory.
- [EDSL documentation index](https://docs.expectedparrot.com/llms.txt): current execution, model, caching, cost, and persistence documentation.

The three fixture runs use engineered outputs and do not demonstrate live EDSL inference. The exporter can be checked offline by serializing and reconstructing its objects. No API key or paid call is needed for that test.
