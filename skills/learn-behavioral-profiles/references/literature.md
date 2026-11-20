# From literature and records to candidate features

Start with a scope: the target behavior, population, setting, and which literature the researcher wants considered. Supplied papers can be sufficient; do not describe a bounded search as an exhaustive review. Record search terms and dates when searches are performed.

For each candidate, retain:

1. A verified bibliographic entry or supplied document location, with page/section/table and a short supporting excerpt or faithful paraphrase.
2. The original construct and the result or argument motivating its relevance. Preserve distinctions between correlational evidence, causal effects, theoretical propositions, and measurement validation.
3. The proposed behavioral feature and the reasoning connecting it to that construct. A feature can be inspired by several papers without being identical to a scale in any of them.
4. A scoring rule, allowable values, direction, and required evidence. Prefer direct computation when a clear observable quantity is available. Distinguish reported preferences from demonstrated behavior and opportunities from realized actions.
5. An explicit unidentifiability rule. Missing opportunities, conflicting evidence, and insufficient observations may need different explanations. Never infer a neutral value simply because evidence is missing.

Inspect the available data schema and a representative sample before finalizing scoring rules. Keep the final validation outcomes unavailable during this step. Do not invent alternative choices for a transaction log, infer a persistent trait from a single ambiguous response, or treat the number of recorded events as a preference without considering exposure.

The output is a researcher-reviewable codebook. Candidate status can be `literature`, `exploratory`, or (only in an invented demo) `synthetic`. Exploratory candidates must be labeled and justified. The software checks required fields and references, not the truth of the literature interpretation. A `verified` citation status is an assertion by the researcher/agent who actually checked the document, not automated verification.

For extraction audits, inspect unsupported cases as well as identified ones; compare evidence-to-value judgments across record types and depth. If human coding is available, use it to assess agreement. Changing the codebook or extraction procedure after an audit requires regenerating affected assessments and freezing a new study snapshot before final evaluation.
