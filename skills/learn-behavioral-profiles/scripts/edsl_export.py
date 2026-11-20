#!/usr/bin/env python3
"""Export local EDSL objects and explicit task assignments. No run/push calls."""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os

from contracts import read, write


def export(payload, mode):
    # EDSL's import-time version check is unnecessary for an offline exporter.
    os.environ["EDSL_DISABLE_VERSION_CHECK"] = "true"
    from edsl import Agent, QuestionFreeText, QuestionMultipleChoice, QuestionNumerical, Scenario, Survey

    agents, scenarios, assignments = {}, {}, []
    if mode == "extraction":
        question = QuestionFreeText(question_name="assessment", question_text=(payload["instructions"] +
            "\nReturn a JSON array of assessments.\nRecord and codebook:\n{{ scenario.material }}"))
        for i, request in enumerate(payload["requests"]):
            key = str(i)
            scenarios[key] = Scenario({"material": json.dumps(request, ensure_ascii=False)}).to_dict()
            assignments.append({"scenario_key": key, "agent_key": None,
                                "record_id": request["record"]["id"]})
    else:
        outcome = payload["outcome"]
        kwargs = {"question_name": "behavior", "question_text": payload["instruction"] + "\n{{ scenario.task }}"}
        if outcome["type"] == "numeric":
            question = QuestionNumerical(**kwargs, min_value=outcome["minimum"], max_value=outcome["maximum"])
        else:
            question = QuestionMultipleChoice(**kwargs, question_options=outcome["levels"])
        for i, task in enumerate(payload["tasks"]):
            key = str(i)
            scenarios[key] = Scenario({"task": task["task"]}).to_dict()
            agent_key = None
            if task["profile"]:
                agent_key = key
                agents[key] = Agent(traits={"behavioral_profile": json.dumps(task["profile"], ensure_ascii=False)},
                                    traits_presentation_template="Behavioral profile:\n{{ behavioral_profile }}",
                                    instruction="Use the supplied behavioral evidence when predicting the task behavior.").to_dict()
            assignments.append({"scenario_key": key, "agent_key": agent_key,
                                "task_id": task["task_id"], "features": task["features"]})
    return {"schema_version": 1, "edsl_version": version("edsl"), "mode": mode,
            "study_fingerprint": payload["study_fingerprint"], "survey": Survey([question]).to_dict(),
            "agents": agents, "scenarios": scenarios, "assignments": assignments,
            "execution": "Not executed. Each assignment is one intended scenario/agent pair; do not cross all objects. Model configuration and run authorization are separate."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["extraction", "simulation"], required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    write(a.out, export(read(a.input), a.mode))
    print(f"Saved local EDSL objects to {a.out}; no model calls or uploads.")


if __name__ == "__main__":
    main()
