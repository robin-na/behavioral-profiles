"""Optional installed-EDSL serialization tests with networking blocked."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from contracts import load_study, read
from edsl_export import export
from make_examples import build
from workflow import make_profiles, plan, prepare


@unittest.skipUnless(importlib.util.find_spec("edsl"), "Optional EDSL dependency is not installed")
class EDSLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {"EDSL_LOG_DIR": str(Path(cls.tmp.name) / "logs"),
                                         "EDSL_DISABLE_VERSION_CHECK": "true"})
        cls.env.start()
        cls.network = patch("socket.socket.connect", side_effect=AssertionError("Offline export attempted a network connection"))
        cls.network.start()
        cls.root = build(Path(cls.tmp.name) / "examples")

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        cls.env.stop()
        cls.tmp.cleanup()

    def test_roundtrip_all_input_and_output_types(self):
        for name in ["survey", "longitudinal", "interview"]:
            study = load_study(self.root / name / "study.json")
            profiles = make_profiles(study, read(self.root / name / "assessments.json"))
            for mode, payload in [("extraction", prepare(study)),
                                  ("simulation", plan(study, profiles, "validation", ["signal"]))]:
                bundle = json.loads(json.dumps(export(payload, mode)))
                from edsl import Agent, Scenario, Survey
                survey = Survey.from_dict(bundle["survey"])
                self.assertEqual(len(survey.questions), 1)
                self.assertEqual(len(bundle["assignments"]), len(bundle["scenarios"]))
                for assignment in bundle["assignments"]:
                    scenario = Scenario.from_dict(bundle["scenarios"][assignment["scenario_key"]])
                    self.assertNotIn("outcome", scenario)
                    if assignment["agent_key"] is not None:
                        agent = Agent.from_dict(bundle["agents"][assignment["agent_key"]])
                        self.assertEqual(set(agent.traits), {"behavioral_profile"})
                        self.assertNotIn('"unsupported"', agent.traits["behavioral_profile"])

    def test_no_profile_does_not_add_agent(self):
        study = load_study(self.root / "survey" / "study.json")
        profiles = make_profiles(study, read(self.root / "survey" / "assessments.json"))
        bundle = export(plan(study, profiles, "validation", []), "simulation")
        self.assertEqual(bundle["agents"], {})
        self.assertTrue(all(x["agent_key"] is None for x in bundle["assignments"]))


if __name__ == "__main__":
    unittest.main()
