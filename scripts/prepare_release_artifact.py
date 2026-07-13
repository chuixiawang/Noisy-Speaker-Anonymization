#!/usr/bin/env python3
"""Strip private experiment metadata to the fields needed for CASR verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for path in sorted(args.metadata_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        condition = payload["learned_alpha_online_condition"]
        for utterance in payload["utterances"]:
            shadow = utterance["learned_alpha_shadow"]
            rows.append(
                {
                    "condition": condition,
                    "utt_id": utterance["utt_id"],
                    "raw_prediction": shadow["raw_prediction"],
                    "snapped_prediction": shadow["snapped_prediction"],
                    "features": shadow["features"],
                }
            )

    result = {
        "artifact": "canonical_runtime_utterance_predictions",
        "source": "CASR online evaluation metadata",
        "n_utterances": len(rows),
        "conditions": sorted({row["condition"] for row in rows}),
        "utterances": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
