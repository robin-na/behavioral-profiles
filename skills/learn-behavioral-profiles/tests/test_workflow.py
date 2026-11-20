"""Behavioral and statistical invariants; all input data are invented."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from contracts import ContractError, condition, load_study, outcomes, predictions, read, write
from evaluation import distribution_loss, evaluate, score, select
from make_examples import build
from workflow import make_profiles, plan, prepare


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = build(Path(self.tmp.name) / "examples")
        self.path = self.root / "survey" / "study.json"
        self.study = load_study(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def data(self, split="learning", study=None):
        study = study or self.study
        return outcomes(study, split), predictions(study, split, study["path"].parent / f"{split}_predictions.json")

    def test_three_input_types_complete_workflow(self):
        for name in ["survey", "longitudinal", "interview"]:
            study = load_study(self.root / name / "study.json")
            h, p = self.data(study=study)
            selection = select(study, h, p)
            self.assertTrue(selection["complete"])
            self.assertEqual(selection["selected_features"], ["signal"])
            h, p = self.data("validation", study)
            result = evaluate(study, selection, h, p)
            self.assertTrue(all(c["ci_95"][1] < 0 for c in result["paired_differences"]))

    def test_no_validation_outcomes_read_during_selection(self):
        h, p = self.data()
        before = select(self.study, h, p)
        (self.path.parent / "validation_outcomes.json").write_text("not even JSON")
        after = select(load_study(self.path), *self.data())
        self.assertEqual(before, after)

    def test_partition_overlap_rejected(self):
        tasks = read(self.path.parent / "learning_tasks.json")
        tasks[0]["partition_id"] = "construction-person-0"
        tasks[1]["partition_id"] = "construction-person-0"
        write(self.path.parent / "learning_tasks.json", tasks)
        with self.assertRaisesRegex(ContractError, "overlap"):
            load_study(self.path)

    def test_cluster_cannot_cross_split(self):
        tasks = read(self.path.parent / "validation_tasks.json")
        tasks[0]["cluster_id"] = "learning-person-0"
        write(self.path.parent / "validation_tasks.json", tasks)
        with self.assertRaisesRegex(ContractError, "Cluster overlaps"):
            load_study(self.path)

    def test_evidence_from_other_record_rejected(self):
        a = read(self.path.parent / "assessments.json")
        a["assessments"][0]["evidence_ids"] = ["evidence-1"]
        with self.assertRaisesRegex(ContractError, "Evidence"):
            make_profiles(self.study, a)

    def test_unsupported_values_cannot_be_neutral(self):
        a = read(self.path.parent / "assessments.json")
        a["assessments"][2]["value"] = "low"
        with self.assertRaisesRegex(ContractError, "Unsupported"):
            make_profiles(self.study, a)

    def test_unsupported_features_omitted_and_no_profile_empty(self):
        a = make_profiles(self.study, read(self.path.parent / "assessments.json"))
        complete = plan(self.study, a, "learning", list(self.study["features"]))
        self.assertTrue(all(len(t["profile"]) == 2 for t in complete["tasks"]))
        baseline = plan(self.study, a, "learning", [])
        self.assertTrue(all(t["profile"] == [] for t in baseline["tasks"]))
        extraction = prepare(self.study)
        self.assertNotIn("outcomes", extraction)
        self.assertNotIn("tasks", extraction)

    def test_modified_profiles_rejected(self):
        p = make_profiles(self.study, read(self.path.parent / "assessments.json"))
        p["profiles"]["record-0"]["signal"]["value"] = "low"
        with self.assertRaisesRegex(ContractError, "changed"):
            plan(self.study, p, "learning", ["signal"])

    def test_missing_candidate_requests_more_predictions(self):
        h, p = self.data()
        del p[condition(["nuisance"])]
        result = select(self.study, h, p)
        self.assertFalse(result["complete"])
        self.assertEqual(result["selected_features"], [])
        self.assertIn(["nuisance"], result["required_conditions"])
        with self.assertRaisesRegex(ContractError, "incomplete"):
            evaluate(self.study, result, *self.data("validation"))

    def test_improvement_must_hold_in_every_learning_comparison(self):
        h, p = self.data()
        # Perfect first-half predictions cannot compensate for a worse second half.
        for row in p[condition(["signal"])]:
            if int(row["task_id"].split("-")[-1]) >= 6:
                row["value"] = "variable" if row["value"] == "stable" else "stable"
        result = select(self.study, h, p)
        self.assertEqual(result["selected_features"], [])

    def test_incomplete_support_and_duplicate_draws_rejected(self):
        p = read(self.path.parent / "learning_predictions.json")
        p["predictions"].pop()
        broken = self.path.parent / "broken.json"
        write(broken, p)
        with self.assertRaisesRegex(ContractError, "coverage|support"):
            predictions(self.study, "learning", broken)
        p = read(self.path.parent / "learning_predictions.json")
        p["predictions"].append(p["predictions"][0])
        write(broken, p)
        with self.assertRaisesRegex(ContractError, "Duplicate"):
            predictions(self.study, "learning", broken)

    def test_frozen_selection_detects_edits(self):
        selection = select(self.study, *self.data())
        selection["selected_features"] = ["nuisance"]
        with self.assertRaisesRegex(ContractError, "modified"):
            evaluate(self.study, selection, *self.data("validation"))

    def test_paired_identical_predictions_have_zero_difference(self):
        selection = select(self.study, *self.data())
        h, p = self.data("validation")
        p[condition([])] = copy.deepcopy(p[condition(["signal"])])
        result = evaluate(self.study, selection, h, p)
        baseline = next(c for c in result["paired_differences"] if c["right"] == condition([]))
        self.assertEqual(baseline["difference"], 0)
        self.assertEqual(baseline["ci_95"], [0, 0])
        self.assertEqual(result, evaluate(self.study, selection, h, p))

    def test_distribution_distance_known_values(self):
        self.assertEqual(distribution_loss([(0, 1)], [(2, 1)], "wasserstein"), 2)
        self.assertEqual(distribution_loss([("a", 1), ("b", 1)], [("a", 1)], "total_variation"), .5)

    def test_aggregate_match_does_not_imply_task_match(self):
        h, p = self.data()
        sim = copy.deepcopy(p[condition(["signal"])])
        # Permute predictions: pooled counts are preserved, task correspondence is lost.
        values = [r["value"] for r in sim]
        for r, value in zip(sim, values[1:] + values[:1]):
            r["value"] = value
        self.assertGreater(score(self.study, "learning", h, sim), 0)
        self.study["spec"]["evaluation"]["metric"] = "total_variation"
        self.assertAlmostEqual(score(self.study, "learning", h, sim), 0)

    def test_custom_loss_receives_weights_and_task_metadata(self):
        h, p = self.data()
        def adapter(human, simulated):
            self.assertIn("cluster_id", human[0])
            self.assertIn("comparison", simulated[0])
            self.assertEqual(sum(r["weight"] for r in human), sum(r["weight"] for r in simulated))
            return .123
        self.study["spec"]["evaluation"]["metric"] = "custom"
        self.assertEqual(score(self.study, "learning", h, p[condition([])], adapter=adapter), .123)

    def test_nonfinite_or_unknown_values_rejected(self):
        study = load_study(self.root / "longitudinal" / "study.json")
        payload = read(study["path"].parent / "learning_predictions.json")
        payload["predictions"][0]["value"] = float("nan")
        bad = study["path"].parent / "bad.json"
        bad.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ContractError, "finite"):
            predictions(study, "learning", bad)

    def test_cli_returns_error_for_missing_input(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "workflow.py"), "profiles", "--study", str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--assessments required", result.stderr)


if __name__ == "__main__":
    unittest.main()
