#!/usr/bin/env python3
"""Recover CASR strengths for all eight released canonical conditions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from casr.controller import load_policy, recover_condition_strength


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path("configs/casr_policy.json"))
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("artifacts/canonical_utterance_predictions.json"),
    )
    args = parser.parse_args()
    policy = load_policy(args.policy)
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    rows = payload["utterances"]
    conditions = sorted({row["condition"] for row in rows})
    report = {}
    for condition in conditions:
        selected = [row for row in rows if row["condition"] == condition]
        resolved = recover_condition_strength(selected, policy)
        report[condition] = {
            "resolved_alpha": resolved["resolved_alpha"],
            "calibration_strategy": resolved["calibration_strategy"],
            "aceg_pass": resolved["aceg"]["gate_pass"],
            "mode_share": resolved["aceg"]["mode_share"],
            "entropy": resolved["aceg"]["alpha_entropy"],
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
