"""CASR prediction, condition aggregation, calibration, and ACEG auditing."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .features import extract_utterance_features


@dataclass(frozen=True)
class EvidenceThresholds:
    """Thresholds for the read-only Alpha-Control Evidence Gate (ACEG)."""

    mode_share_min: float = 0.50
    entropy_max: float = 1.10
    raw_std_max: float = 0.08
    preview_gap_max: float = 0.10


def load_policy(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        policy = json.load(handle)
    validate_policy(policy)
    return policy


def validate_policy(policy: Mapping) -> None:
    model = policy.get("utterance_level_model")
    if not isinstance(model, Mapping):
        raise ValueError("policy must contain utterance_level_model")
    features = model.get("features", [])
    coefficients = model.get("coefficients", [])
    if not features or len(features) != len(coefficients):
        raise ValueError("model features and coefficients must have equal non-zero length")
    candidates = [float(value) for value in model.get("candidate_alphas", [])]
    if not candidates or candidates != sorted(set(candidates)):
        raise ValueError("candidate_alphas must be a non-empty sorted unique list")


def snap_to_candidates(value: float, candidates: Iterable[float]) -> float:
    values = [float(candidate) for candidate in candidates]
    if not values:
        raise ValueError("candidate_alphas cannot be empty")
    return min(values, key=lambda candidate: (round(abs(candidate - value), 12), candidate))


def _feature_value(name: str, values: Mapping[str, float]) -> float:
    if name == "bias":
        return 1.0
    if name in values:
        return float(values[name])
    if name.endswith("_sq"):
        base = name[:-3]
        if base not in values:
            raise KeyError(f"Missing base feature for {name}: {base}")
        return float(values[base]) ** 2
    if "_x_" in name:
        left, right = name.split("_x_", maxsplit=1)
        if left not in values or right not in values:
            raise KeyError(f"Missing interaction feature input for {name}")
        return float(values[left]) * float(values[right])
    raise KeyError(f"Unsupported policy feature: {name}")


def predict_from_features(feature_values: Mapping[str, float], policy: Mapping) -> dict:
    """Predict a continuous and discretized strength for one utterance."""
    validate_policy(policy)
    model = policy["utterance_level_model"]
    raw = 0.0
    for name, coefficient in zip(model["features"], model["coefficients"], strict=True):
        value = _feature_value(name, feature_values)
        if name != "bias" and name in model.get("feature_means", {}):
            mean = float(model["feature_means"][name])
            std = float(model.get("feature_stds", {}).get(name, 1.0))
            value = (value - mean) / (std if abs(std) >= 1e-8 else 1.0)
        raw += float(coefficient) * value

    clipped = min(float(model.get("alpha_max", raw)), max(float(model.get("alpha_min", raw)), raw))
    snapped = snap_to_candidates(clipped, model["candidate_alphas"])
    return {
        "raw_prediction": float(raw),
        "snapped_prediction": float(snapped),
        "candidate_alphas": [float(value) for value in model["candidate_alphas"]],
        "features": {key: float(value) for key, value in feature_values.items()},
    }


def predict_utterance(waveform: np.ndarray, sample_rate: int, policy: Mapping) -> dict:
    features = extract_utterance_features(waveform, sample_rate)
    return predict_from_features(features, policy)


def summarize_predictions(
    predictions: Sequence[Mapping[str, float]],
    candidates: Sequence[float] | None = None,
) -> dict:
    if not predictions:
        raise ValueError("at least one utterance prediction is required")
    raw = np.asarray([item["raw_prediction"] for item in predictions], dtype=np.float64)
    snapped = [float(item["snapped_prediction"]) for item in predictions]
    counts = Counter(snapped)
    max_count = max(counts.values())
    mode_alpha = min(value for value, count in counts.items() if count == max_count)
    sorted_counts = sorted(counts.values(), reverse=True)
    second_count = sorted_counts[1] if len(sorted_counts) > 1 else 0
    probabilities = np.asarray([count / len(snapped) for count in counts.values()])
    entropy = float(-(probabilities * np.log(probabilities)).sum())
    if candidates is None:
        candidates = predictions[0].get("candidate_alphas", (0.3, 0.4, 0.5, 0.6, 0.7, 0.8))
    median_preview = snap_to_candidates(float(np.median(snapped)), candidates)
    return {
        "n_utterances": len(predictions),
        "raw_mean": float(np.mean(raw)),
        "raw_std": float(np.std(raw)),
        "raw_min": float(np.min(raw)),
        "raw_p25": float(np.percentile(raw, 25)),
        "raw_median": float(np.median(raw)),
        "raw_p75": float(np.percentile(raw, 75)),
        "raw_max": float(np.max(raw)),
        "snapped_mode_alpha": float(mode_alpha),
        "mode_share": float(max_count / len(snapped)),
        "mode_margin": float((max_count - second_count) / len(snapped)),
        "alpha_entropy": entropy,
        "snapped_histogram": {f"{key:.1f}": counts[key] for key in sorted(counts)},
        "preview_condition_prediction": float(median_preview),
        "preview_gap": float(abs(mode_alpha - median_preview)),
    }


def _calibrate_predictions(
    predictions: Sequence[Mapping[str, float]],
    candidates: Sequence[float],
    *,
    disagreement_threshold: float = 0.05,
    uncertainty_std_threshold: float = 0.04,
    conservative_shift: float = 0.05,
) -> tuple[dict, str]:
    """Apply the calibration path used for the reported CASR experiments."""
    base = summarize_predictions(predictions, candidates)
    raw = np.asarray([item["raw_prediction"] for item in predictions], dtype=np.float64)
    strategy = "identity"
    if (
        base["raw_std"] >= uncertainty_std_threshold
        and abs(base["snapped_mode_alpha"] - base["preview_condition_prediction"])
        >= disagreement_threshold
    ):
        strategy = "preview_anchor"
        raw = np.full(len(predictions), base["preview_condition_prediction"], dtype=np.float64)
    elif base["raw_std"] >= uncertainty_std_threshold:
        strategy = "conservative_shift"
        raw = raw - conservative_shift

    calibrated = [
        {
            "raw_prediction": float(value),
            "snapped_prediction": snap_to_candidates(value, candidates),
        }
        for value in raw
    ]
    summary = summarize_predictions(calibrated, candidates)
    summary.update(
        {
            "calibration_strategy": strategy,
            "base_mode_alpha": base["snapped_mode_alpha"],
            "uncertainty_std_threshold": uncertainty_std_threshold,
            "disagreement_threshold": disagreement_threshold,
            "conservative_shift": conservative_shift,
        }
    )
    return summary, strategy


def build_evidence_gate(
    summary: Mapping[str, float],
    thresholds: EvidenceThresholds | None = None,
) -> dict:
    """Build the read-only ACEG certificate without modifying strength."""
    thresholds = thresholds or EvidenceThresholds()
    preview_gap = summary.get("preview_gap")
    checks = {
        "mode_share": float(summary["mode_share"]) >= thresholds.mode_share_min,
        "alpha_entropy": float(summary["alpha_entropy"]) <= thresholds.entropy_max,
        "raw_std": float(summary["raw_std"]) <= thresholds.raw_std_max,
    }
    if preview_gap is not None:
        checks["preview_gap"] = float(preview_gap) <= thresholds.preview_gap_max
    return {
        "version": "aceg_v0",
        "gate_pass": all(checks.values()),
        "mode_share": float(summary["mode_share"]),
        "mode_margin": float(summary["mode_margin"]),
        "alpha_entropy": float(summary["alpha_entropy"]),
        "raw_std": float(summary["raw_std"]),
        "preview_gap": float(preview_gap) if preview_gap is not None else None,
        "n_utterances": int(summary["n_utterances"]),
        "checks": checks,
    }


def recover_condition_strength(
    predictions: Sequence[Mapping[str, float]],
    policy: Mapping,
    *,
    apply_calibration: bool = True,
) -> dict:
    """Recover one condition-level strength and attach a read-only ACEG audit."""
    validate_policy(policy)
    model = policy["utterance_level_model"]
    candidates = [float(value) for value in model["candidate_alphas"]]
    base = summarize_predictions(predictions, candidates)
    if apply_calibration:
        final, source = _calibrate_predictions(predictions, candidates)
    else:
        final, source = base, "disabled"
    return {
        "resolved_alpha": float(final["snapped_mode_alpha"]),
        "calibration_strategy": source,
        "base_summary": base,
        "final_summary": final,
        "aceg": build_evidence_gate(final),
    }
