"""Standard-library input validation; no model execution or repository dependencies."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


class ContractError(ValueError):
    pass


def require(test, message):
    if not test:
        raise ContractError(message)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def read(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def unique(rows, key, label):
    require(isinstance(rows, list), f"{label} must be a list")
    ids = [r.get(key) for r in rows]
    require(all(isinstance(x, str) and x for x in ids), f"{label}: missing {key}")
    require(len(set(ids)) == len(ids), f"{label}: duplicate {key}")
    return {r[key]: r for r in rows}


def check_value(value, definition, label):
    kind = definition.get("type")
    if kind == "numeric":
        require(number(value), f"{label}: expected a finite number")
        require(definition["minimum"] <= value <= definition["maximum"], f"{label}: value outside bounds")
    else:
        require(value in definition["levels"] and isinstance(value, str), f"{label}: invalid category")


def definition(spec, label):
    require(spec.get("type") in {"numeric", "ordinal", "categorical"}, f"{label}: unsupported type")
    if spec["type"] == "numeric":
        require(number(spec.get("minimum")) and number(spec.get("maximum")), f"{label}: finite bounds required")
        require(spec["minimum"] < spec["maximum"], f"{label}: invalid bounds")
    else:
        levels = spec.get("levels", [])
        require(len(levels) >= 2 and all(isinstance(x, str) and x for x in levels), f"{label}: levels required")
        require(len(set(levels)) == len(levels), f"{label}: duplicate levels")


def load_study(path):
    """Load construction and task metadata, never outcomes."""
    path = Path(path)
    spec = read(path)
    for name in ["study_id", "research_question", "profile_unit", "partition_unit", "split_rationale", "prediction_target"]:
        require(isinstance(spec.get(name), str) and spec[name].strip(), f"Study needs {name}")
    require(spec.get("schema_version") == 1, "Unsupported schema_version")
    sources = unique(spec.get("literature", []), "id", "literature")
    features = unique(spec.get("features", []), "id", "features")
    require(features, "At least one candidate feature is required")
    for f in features.values():
        definition(f, f["id"])
        for key in ["name", "definition", "scoring_rule", "evidence_requirement", "unsupported_when"]:
            require(isinstance(f.get(key), str) and f[key].strip(), f"{f['id']}: needs {key}")
        require(f.get("basis") in {"literature", "exploratory", "synthetic"}, "Feature needs basis")
        require(f["basis"] != "synthetic" or spec.get("synthetic") is True, "Synthetic feature in real study")
        refs = f.get("references", [])
        require(refs or f["basis"] == "exploratory", f"{f['id']}: references required")
        for ref in refs:
            require(ref.get("literature_id") in sources and ref.get("locator") and ref.get("support"), "Incomplete literature link")
            s = sources[ref["literature_id"]]
            require(s.get("citation") and s.get("location"), "Literature needs citation and location")
            require(s.get("status") in {"verified", "synthetic"}, "Verify cited literature before extraction")
            require(s["status"] != "synthetic" or spec.get("synthetic") is True, "Synthetic citation in real study")
    evaluation = spec["evaluation"]
    definition(evaluation["outcome"], "outcome")
    require(evaluation.get("metric") in {"mae", "mse", "error_rate", "total_variation", "wasserstein", "custom"}, "Unsupported metric")
    if evaluation["metric"] in {"mae", "mse", "wasserstein"}:
        require(evaluation["outcome"]["type"] == "numeric", "Numeric metric requires numeric outcome")
    require(evaluation.get("aggregation") == "weighted_by_observation", "Specify aggregation: weighted_by_observation")
    require(evaluation.get("bootstrap_draws", 0) >= 100 and isinstance(evaluation["bootstrap_draws"], int), "Use at least 100 bootstrap draws")
    require(isinstance(evaluation.get("seed"), int), "Bootstrap seed required")
    threshold = spec["selection"].get("min_improvement")
    require(number(threshold) and threshold >= 0, "Nonnegative min_improvement required")
    limit = spec["selection"].get("max_features")
    require(isinstance(limit, int) and 0 <= limit <= len(features), "Invalid max_features")
    groups = spec["selection"].get("redundancy_groups", [])
    flattened = [x for g in groups for x in g]
    require(all(x in features for x in flattened) and len(flattened) == len(set(flattened)), "Redundancy groups must be disjoint known features")
    records = read(path.parent / spec["files"]["construction"])
    record_map = unique(records, "id", "construction")
    for r in records:
        require(isinstance(r.get("partition_id"), str) and r["partition_id"], "Record partition_id required")
        evidence = unique(r.get("evidence", []), "id", "evidence")
        require(evidence, "Record requires evidence")
        for e in evidence.values():
            require(e.get("kind") in {"survey", "event", "text", "interaction", "other"}, "Unknown evidence kind")
            require("content" in e and e.get("locator"), "Evidence needs content and locator")
    tasks = {}
    partitions = {"construction": {r["partition_id"] for r in records}}
    for split in ["learning", "validation"]:
        tasks[split] = read(path.parent / spec["files"][f"{split}_tasks"])
        unique(tasks[split], "id", f"{split} tasks")
        require(tasks[split], f"No {split} tasks")
        group_partitions = {}
        for task in tasks[split]:
            for key in ["partition_id", "cluster_id", "comparison", "stratum", "prompt"]:
                require(isinstance(task.get(key), str) and task[key], f"Task needs {key}")
            require(set(task) <= {"id", "partition_id", "cluster_id", "comparison", "stratum", "prompt", "profile_id"}, "Unexpected task field: keep outcomes in their separate file")
            require(task.get("profile_id") in record_map, "Task refers to unknown construction record")
            group_partitions.setdefault(task["cluster_id"], set()).add(task["partition_id"])
        require(all(len(v) == 1 for v in group_partitions.values()), "A bootstrap cluster crosses partition units")
        partitions[split] = {t["partition_id"] for t in tasks[split]}
    require(not ({t['id'] for t in tasks['learning']} & {t['id'] for t in tasks['validation']}), "Task IDs overlap across splits")
    for a, b in [("construction", "learning"), ("construction", "validation"), ("learning", "validation")]:
        require(not partitions[a] & partitions[b], f"Partition overlap: {a} / {b}")
    require(not ({t['cluster_id'] for t in tasks['learning']} & {t['cluster_id'] for t in tasks['validation']}), "Cluster overlaps learning and validation")
    # Pin all design choices and construction content; outcome files are intentionally excluded.
    fingerprint = digest({"spec": spec, "records": records, "tasks": tasks})
    return {"path": path, "spec": spec, "features": features, "records": record_map,
            "tasks": tasks, "fingerprint": fingerprint}


def outcomes(study, split):
    rows = read(study["path"].parent / study["spec"]["files"][f"{split}_outcomes"])
    require(rows, "No outcomes")
    tasks = {t["id"]: t for t in study["tasks"][split]}
    require({r.get("task_id") for r in rows} == set(tasks), "Outcome/task coverage differs")
    for row in rows:
        check_value(row.get("value"), study["spec"]["evaluation"]["outcome"], "outcome")
        require(number(row.get("weight")) and row["weight"] > 0, "Outcome weight must be positive")
    return rows


def condition(features):
    return json.dumps(sorted(features), separators=(",", ":"))


def predictions(study, split, path):
    payload = read(path)
    require(isinstance(payload, dict) and payload.get("study_fingerprint") == study["fingerprint"], "Predictions need the current study_fingerprint")
    require(payload.get("split") == split, "Prediction file has the wrong split")
    provenance = payload.get("provenance", {})
    require(provenance.get("method") in {"model", "deterministic", "synthetic"} and provenance.get("description"), "Prediction provenance required")
    require(provenance["method"] != "synthetic" or study["spec"].get("synthetic") is True, "Synthetic predictions in real study")
    if provenance["method"] == "model":
        require(all(provenance.get(k) for k in ["model", "settings", "plan_hashes"]), "Model predictions need model/settings/plan_hashes")
    rows = payload.get("predictions", [])
    require(isinstance(rows, list) and rows, "No predictions")
    tasks = {t["id"]: t for t in study["tasks"][split]}
    conditions = {}
    for row in rows:
        fs = row.get("features", [])
        require(isinstance(fs, list) and all(f in study["features"] for f in fs) and len(set(fs)) == len(fs), "Unknown/duplicate feature in predictions")
        require(row.get("task_id") in tasks, "Prediction outside requested split")
        require(isinstance(row.get("draw_id"), str) and row["draw_id"], "Prediction draw_id required")
        check_value(row.get("value"), study["spec"]["evaluation"]["outcome"], "prediction")
        conditions.setdefault(condition(fs), []).append(row)
    expected = None
    for name, group in conditions.items():
        keys = [(r["task_id"], r["draw_id"]) for r in group]
        require(len(keys) == len(set(keys)), "Duplicate prediction draw")
        require({k[0] for k in keys} == set(tasks), f"Incomplete task coverage: {name}")
        if expected is None:
            expected = set(keys)
        require(set(keys) == expected, "Conditions must share task/draw support")
    return conditions
