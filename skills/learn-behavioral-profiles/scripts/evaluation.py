"""Configurable losses, forward feature selection, and paired cluster resampling."""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import math
import random

from contracts import condition, digest, number, require


def custom_metric(path):
    if path is None:
        return None
    module_spec = importlib.util.spec_from_file_location("user_metric", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    require(callable(getattr(module, "loss", None)), "Metric adapter must export loss(human, simulated)")
    return module.loss


def distribution_loss(human, simulated, metric):
    h, p = defaultdict(float), defaultdict(float)
    for value, weight in human:
        h[value] += weight
    for value, weight in simulated:
        p[value] += weight
    ht, pt = sum(h.values()), sum(p.values())
    h = {k: v / ht for k, v in h.items()}
    p = {k: v / pt for k, v in p.items()}
    support = set(h) | set(p)
    if metric == "total_variation":
        return sum(abs(h.get(x, 0) - p.get(x, 0)) for x in support) / 2
    ordered = sorted(support)
    cumulative = 0.0
    distance = 0.0
    for i, x in enumerate(ordered[:-1]):
        cumulative += h.get(x, 0) - p.get(x, 0)
        distance += abs(cumulative) * (ordered[i + 1] - x)
    return distance


def score(study, split, human, simulated, comparison=None, multipliers=None, adapter=None):
    tasks = {t["id"]: t for t in study["tasks"][split]}
    hs, ps = defaultdict(list), defaultdict(list)
    for r in human:
        task = tasks[r["task_id"]]
        if comparison is not None and task["comparison"] != comparison:
            continue
        factor = 1 if multipliers is None else multipliers.get(task["cluster_id"], 0)
        if factor:
            hs[r["task_id"]].append((r["value"], r["weight"] * factor))
    for r in simulated:
        ps[r["task_id"]].append(r["value"])
    require(hs, "No outcomes in requested comparison")
    metric = study["spec"]["evaluation"]["metric"]
    total = sum(w for group in hs.values() for _, w in group)
    if metric in {"mae", "mse", "error_rate"}:
        loss = 0.0
        for tid, obs in hs.items():
            for value, weight in obs:
                for pred in ps[tid]:
                    error = (float(value != pred) if metric == "error_rate" else
                             abs(value - pred) ** (2 if metric == "mse" else 1))
                    loss += weight * error / len(ps[tid])
        return loss / total
    pooled_h, pooled_p = defaultdict(list), defaultdict(list)
    for tid, obs in hs.items():
        stratum = tasks[tid]["stratum"]
        pooled_h[stratum].extend(obs)
        weight = sum(w for _, w in obs) / len(ps[tid])
        pooled_p[stratum].extend((value, weight) for value in ps[tid])
    if metric == "custom":
        require(adapter is not None, "Custom metric requires --metric-adapter")
        # Preserve task/group/context metadata for a researcher-defined loss.
        hrows = [{**tasks[tid], "value": v, "weight": w} for tid, obs in hs.items() for v, w in obs]
        prows = [{**tasks[tid], "value": v, "weight": sum(w for _, w in obs)/len(ps[tid])}
                 for tid, obs in hs.items() for v in ps[tid]]
        result = adapter(hrows, prows)
        require(number(result) and result >= 0, "Custom loss must be finite and nonnegative")
        return result
    return sum(distribution_loss(pooled_h[s], pooled_p[s], metric) * sum(w for _, w in pooled_h[s])
               for s in pooled_h) / total


def select(study, human, predicted, adapter=None):
    settings = study["spec"]["selection"]
    names = sorted(study["features"])
    comparisons = sorted({t["comparison"] for t in study["tasks"]["learning"]})
    selected, history = [], []
    cache = {}

    def losses(features):
        key = condition(features)
        if key not in cache:
            cache[key] = {"overall": score(study, "learning", human, predicted[key], adapter=adapter),
                          "comparisons": {c: score(study, "learning", human, predicted[key], c, adapter=adapter)
                                          for c in comparisons}}
        return cache[key]

    complete, reason, missing = True, "max_features", []
    if condition([]) not in predicted:
        complete, reason, missing = False, "missing_predictions", [[]]
    else:
        losses([])
        while len(selected) < settings["max_features"]:
            groups = settings.get("redundancy_groups", [])
            candidates = [sorted(selected + [f]) for f in names if f not in selected
                          and not any(f in group and set(selected) & set(group) for group in groups)]
            if not candidates:
                reason = "no_eligible_additions"
                break
            missing = [fs for fs in candidates if condition(fs) not in predicted]
            if missing:
                complete, reason = False, "missing_predictions"
                break
            previous = losses(selected)
            accepted = []
            checks = []
            for fs in candidates:
                current = losses(fs)
                gains = {c: previous["comparisons"][c] - current["comparisons"][c] for c in comparisons}
                gain = previous["overall"] - current["overall"]
                passes = gain > settings["min_improvement"] and all(v > settings["min_improvement"] for v in gains.values())
                checks.append({"features": fs, "losses": current, "improvement": gain,
                               "comparison_improvements": gains, "passes": passes})
                if passes:
                    accepted.append((current["overall"], fs))
            if not accepted:
                history.append({"from": selected[:], "candidates": checks, "chosen": None})
                reason = "no_improving_addition"
                break
            chosen = min(accepted)[1]
            history.append({"from": selected[:], "candidates": checks, "chosen": chosen})
            selected = chosen
    artifact = {"schema_version": 1, "study_id": study["spec"]["study_id"],
                "study_fingerprint": study["fingerprint"], "learning_outcomes_hash": digest(human),
                "learning_predictions_hash": digest(predicted), "complete": complete,
                "selected_features": selected, "stop_reason": reason, "required_conditions": missing,
                "history": history, "losses": cache}
    artifact["selection_hash"] = digest(artifact)
    return artifact


def quantile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    low, high = math.floor(pos), math.ceil(pos)
    return values[low] + (values[high] - values[low]) * (pos - low)


def evaluate(study, selection, human, predicted, adapter=None):
    require(selection.get("complete") is True, "Selection is incomplete: generate the requested learning conditions")
    require(selection.get("study_fingerprint") == study["fingerprint"], "Study changed since selection; freeze a new selection")
    payload = {k: v for k, v in selection.items() if k != "selection_hash"}
    require(digest(payload) == selection.get("selection_hash"), "Selection artifact was modified")
    selected = selection["selected_features"]
    required = {condition([]), condition(selected), condition(study["features"])}
    require(required <= set(predicted), f"Missing validation conditions: {sorted(required - set(predicted))}")
    tasks = study["tasks"]["validation"]
    strata, membership = defaultdict(set), defaultdict(set)
    for task in tasks:
        strata[task["stratum"]].add(task["cluster_id"])
        membership[task["cluster_id"]].add(task["stratum"])
    require(all(len(v) == 1 for v in membership.values()), "Clusters cross strata; provide a suitable resampling adapter")
    require(all(len(v) >= 2 for v in strata.values()), "Need at least two validation clusters per stratum for bootstrap")
    settings = study["spec"]["evaluation"]
    losses = {key: score(study, "validation", human, predicted[key], adapter=adapter) for key in sorted(required)}
    rng = random.Random(settings["seed"])
    samples = {key: [] for key in sorted(required)}
    for _ in range(settings["bootstrap_draws"]):
        multiplicity = Counter()
        for stratum in sorted(strata):
            units = sorted(strata[stratum])
            multiplicity.update(rng.choices(units, k=len(units)))
        for key in samples:
            samples[key].append(score(study, "validation", human, predicted[key], multipliers=multiplicity, adapter=adapter))
    selected_key = condition(selected)
    contrasts = []
    for key in sorted(required - {selected_key}):
        differences = [a - b for a, b in zip(samples[selected_key], samples[key])]
        contrasts.append({"left": selected_key, "right": key, "difference": losses[selected_key] - losses[key],
                          "ci_95": [quantile(differences, .025), quantile(differences, .975)]})
    return {"schema_version": 1, "study_id": study["spec"]["study_id"], "selection_hash": selection["selection_hash"],
            "validation_outcomes_hash": digest(human), "validation_predictions_hash": digest(predicted),
            "metric": settings["metric"], "losses": losses, "paired_differences": contrasts,
            "interpretation": "Negative selected-minus-comparator loss favors selected. Percentile intervals are conditional on supplied simulation outputs.",
            "bootstrap": {"unit": "cluster_id", "stratified_by": "stratum", "draws": settings["bootstrap_draws"], "seed": settings["seed"]}}
