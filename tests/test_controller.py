import json
import unittest
from pathlib import Path

from casr.controller import (
    EvidenceThresholds,
    build_evidence_gate,
    load_policy,
    predict_from_features,
    recover_condition_strength,
    snap_to_candidates,
)

ROOT = Path(__file__).resolve().parents[1]


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(ROOT / "configs" / "casr_policy.json")

    def test_snap_ties_toward_lower_strength(self):
        self.assertEqual(snap_to_candidates(0.55, [0.5, 0.6]), 0.5)

    def test_prediction_uses_released_feature_names(self):
        prediction = predict_from_features(
            {"centroid_norm_mean": 0.64, "energy_contrast_norm": 0.53},
            self.policy,
        )
        self.assertIn(prediction["snapped_prediction"], [0.3, 0.4, 0.5, 0.6, 0.7, 0.8])

    def test_aceg_is_read_only(self):
        summary = {
            "mode_share": 0.8,
            "mode_margin": 0.6,
            "alpha_entropy": 0.4,
            "raw_std": 0.03,
            "preview_gap": 0.0,
            "n_utterances": 20,
            "snapped_mode_alpha": 0.7,
        }
        before = dict(summary)
        certificate = build_evidence_gate(summary, EvidenceThresholds())
        self.assertTrue(certificate["gate_pass"])
        self.assertEqual(summary, before)

    def test_released_manifest_has_eight_conditions(self):
        payload = json.loads(
            (ROOT / "artifacts" / "canonical_utterance_predictions.json").read_text()
        )
        conditions = sorted({row["condition"] for row in payload["utterances"]})
        self.assertEqual(len(conditions), 8)
        for condition in conditions:
            rows = [row for row in payload["utterances"] if row["condition"] == condition]
            self.assertEqual(len(rows), 200)
            result = recover_condition_strength(rows, self.policy)
            self.assertIn(result["resolved_alpha"], [0.3, 0.4, 0.5, 0.6, 0.7, 0.8])


if __name__ == "__main__":
    unittest.main()
