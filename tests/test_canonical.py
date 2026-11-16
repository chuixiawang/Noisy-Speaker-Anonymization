import json
import unittest
from pathlib import Path

from casr.controller import load_policy, recover_condition_strength

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "white_snr20dB": 0.8,
    "white_snr10dB": 0.8,
    "white_snr5dB": 0.7,
    "white_snr0dB": 0.7,
    "babble_snr20dB": 0.8,
    "babble_snr10dB": 0.7,
    "babble_snr5dB": 0.6,
    "babble_snr0dB": 0.5,
}


class CanonicalDecisionTests(unittest.TestCase):
    def test_released_artifact_reproduces_batch_strengths(self):
        policy = load_policy(ROOT / "configs" / "casr_policy.json")
        rows = json.loads(
            (ROOT / "artifacts" / "canonical_utterance_predictions.json").read_text(encoding="utf-8")
        )["utterances"]
        for condition, expected in EXPECTED.items():
            selected = [row for row in rows if row["condition"] == condition]
            resolved = recover_condition_strength(selected, policy)
            self.assertAlmostEqual(resolved["resolved_alpha"], expected, msg=condition)


if __name__ == "__main__":
    unittest.main()
