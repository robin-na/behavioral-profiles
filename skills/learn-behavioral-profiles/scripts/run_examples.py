#!/usr/bin/env python3
"""Exercise the public CLI using synthetic fixtures only."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(examples, output):
    cli = Path(__file__).with_name("workflow.py")
    summary = []
    for name in ["survey", "longitudinal", "interview"]:
        inputs = Path(examples) / name
        out = Path(output) / name
        out.mkdir(parents=True, exist_ok=True)

        def call(command, *args):
            subprocess.run([sys.executable, str(cli), command, "--study", str(inputs / "study.json"), *map(str, args)], check=True)

        call("check")
        call("prepare", "--out", out / "extraction.json")
        call("profiles", "--assessments", inputs / "assessments.json", "--out", out / "profiles.json")
        call("select", "--predictions", inputs / "learning_predictions.json", "--out", out / "selection.json")
        selected = json.loads((out / "selection.json").read_text())
        if selected["selected_features"] != ["signal"] or not selected["complete"]:
            raise RuntimeError(f"Unexpected synthetic selection: {name}")
        call("plan", "--profiles", out / "profiles.json", "--split", "validation", "--features", json.dumps(selected["selected_features"]), "--out", out / "simulation_plan.json")
        call("evaluate", "--selection", out / "selection.json", "--predictions", inputs / "validation_predictions.json", "--out", out / "evaluation.json")
        result = json.loads((out / "evaluation.json").read_text())
        summary.append({"example": name, "selected_features": selected["selected_features"],
                        "stop_reason": selected["stop_reason"], "validation_losses": result["losses"]})
    (Path(output) / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.examples, args.out), indent=2))
