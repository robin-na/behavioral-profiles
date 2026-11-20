# Synthetic examples

Generate the fixtures with `scripts/make_examples.py`. Nothing is read from the research repository, a participant dataset, a persona library, or a model service.

The three fixtures represent structured survey responses, repeated choices with recorded alternatives, and interview text. Their candidate definitions, evidence, assessments, human-comparison outcomes, and simulated outputs are all invented. The literature entry is labeled as a synthetic specification and is not a claim about any published work.

The prediction fixtures intentionally favor `signal`, make `nuisance` harmful when added, and leave `unsupported` unidentified. These fixtures test workflow behavior, not an LLM's extraction ability or the empirical effectiveness of feature selection. Real applications must inspect extraction quality and run their own evaluation.

Fixtures are generated on demand so the distributable skill contains no stored individual profiles, human records, or persona libraries. Generated demonstration profiles should remain outside the skill directory.
