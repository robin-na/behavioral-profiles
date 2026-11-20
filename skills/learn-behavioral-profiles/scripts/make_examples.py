#!/usr/bin/env python3
"""Create wholly invented fixtures; never reads research data or personas."""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

from contracts import load_study, write


def build(root):
    root = Path(root)
    for name in ["survey", "longitudinal", "interview"]:
        out = root / name
        numeric = name == "longitudinal"
        feature_type = ({"type": "numeric", "minimum": 0, "maximum": 1} if numeric else
                        {"type": "ordinal", "levels": ["low", "high"]})
        features = []
        for fid, label, rule in [
            ("signal", "Preference for predictable options", "Use explicit choices between predictable and varying options; high or 1 when predictable is preferred."),
            ("nuisance", "Preference for short descriptions", "Use an explicit preference for brief wording; high or 1 when present."),
            ("unsupported", "Response to a service failure", "Requires a recorded service failure and a subsequent response.")]:
            features.append({"id": fid, "name": label, "definition": label + " within the observed context.",
                             **feature_type, "basis": "synthetic", "scoring_rule": rule,
                             "evidence_requirement": "Direct statement or relevant observed opportunity and choice.",
                             "unsupported_when": "No relevant statement or opportunity is recorded.",
                             "references": [{"literature_id": "fixture", "locator": fid,
                                             "support": "Invented demonstration construct, not a research citation."}]})
        records = []
        for i in range(4):
            if name == "survey":
                content = {"question": "Would you choose a stable delivery time or a variable time?", "answer": "Stable", "wording_preference": "Brief"}
                kind = "survey"
            elif name == "longitudinal":
                content = {"available_options": ["stable", "variable"],
                           "events": [{"time": f"day-{j}", "choice": "stable"} for j in range(3)],
                           "wording_choice": "brief"}
                kind = "event"
            else:
                content = "Interviewer: Which schedule would you prefer? Respondent: I prefer a predictable time, and brief descriptions. We have not discussed service failures."
                kind = "text"
            records.append({"id": f"record-{i}", "partition_id": f"construction-person-{i}",
                            "evidence": [{"id": f"evidence-{i}", "kind": kind, "content": content,
                                          "locator": f"invented-{name}-record-{i}"}]})
        write(out / "construction.json", records)
        spec = {"schema_version": 1, "study_id": f"synthetic-{name}", "synthetic": True,
                "research_question": "Does selecting supported descriptions improve this synthetic prediction task?",
                "profile_unit": "A fictional participant's available record",
                "partition_unit": "Fictional participant", "prediction_target": "Behavior distribution in the task",
                "split_rationale": "Distinct fictional participants for construction, learning, and validation; repeated tasks stay together.",
                "literature": [{"id": "fixture", "citation": "Synthetic fixture specification (not a publication)",
                                "location": "../../SYNTHETIC.md", "status": "synthetic"}],
                "features": features,
                "evaluation": {"metric": "mae" if numeric else "error_rate",
                               "outcome": {"type": "numeric", "minimum": 0, "maximum": 1} if numeric else
                                          {"type": "categorical", "levels": ["stable", "variable"]},
                               "aggregation": "weighted_by_observation", "bootstrap_draws": 200, "seed": 71},
                "selection": {"min_improvement": .001, "max_features": 3, "redundancy_groups": []},
                "files": {"construction": "construction.json"}}
        for split in ["learning", "validation"]:
            tasks, human, predictions = [], [], []
            for i in range(12):
                task_id = f"{split}-{i}"
                value = (0.8 if i % 3 else 0.2) if numeric else ("stable" if i % 3 else "variable")
                tasks.append({"id": task_id, "partition_id": f"{split}-person-{i//2}",
                              "cluster_id": f"{split}-person-{i//2}", "stratum": "all",
                              "comparison": "first" if i < 6 else "second", "profile_id": f"record-{i%4}",
                              "prompt": f"Synthetic decision {i}: predict the next choice between a stable and a variable option."})
                human.append({"task_id": task_id, "value": value, "weight": 1})
                ids = [f["id"] for f in features]
                for n in range(4):
                    for fs in combinations(ids, n):
                        pred = value if "signal" in fs else (0.3 if numeric else "variable")
                        if "nuisance" in fs and "signal" in fs:
                            pred = min(1, pred + .15) if numeric else "variable"
                        predictions.append({"task_id": task_id, "draw_id": "synthetic-draw-0", "features": list(fs), "value": pred})
            spec["files"][f"{split}_tasks"] = f"{split}_tasks.json"
            spec["files"][f"{split}_outcomes"] = f"{split}_outcomes.json"
            write(out / f"{split}_tasks.json", tasks)
            write(out / f"{split}_outcomes.json", human)
            write(out / f"{split}_predictions.json", predictions)
        write(out / "study.json", spec)
        study = load_study(out / "study.json")
        for split in ["learning", "validation"]:
            from contracts import read
            prediction_path = out / f"{split}_predictions.json"
            write(prediction_path, {"study_fingerprint": study["fingerprint"], "split": split,
                                   "provenance": {"method": "synthetic", "description": "Engineered numerical fixture; not generated by a model."},
                                   "predictions": read(prediction_path)})
        assessments = []
        for record in records:
            for f in features:
                supported = f["id"] != "unsupported"
                assessments.append({"record_id": record["id"], "feature_id": f["id"],
                                    "identifiable": supported, "value": (1 if numeric else "high") if supported else None,
                                    "certainty": .8 if supported else None,
                                    "evidence_ids": [record["evidence"][0]["id"]] if supported else [],
                                    "reason": "Invented example explicitly provides this preference." if supported else "No service failure was observed."})
        write(out / "assessments.json", {"study_fingerprint": study["fingerprint"],
                                        "provenance": {"method": "synthetic", "description": "Hand-designed deterministic fixture; no LLM or human data."},
                                        "assessments": assessments})
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.out)
    print(f"Created three synthetic studies in {args.out}")
