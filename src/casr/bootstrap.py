"""Paired bootstrap confidence intervals for EER, WER, and CER."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np


def percentile_interval(samples: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between zero and one")
    tail = (1.0 - confidence) / 2.0
    values = np.asarray(samples, dtype=np.float64)
    return float(np.quantile(values, tail)), float(np.quantile(values, 1.0 - tail))


def paired_bootstrap(
    items_a: Sequence,
    items_b: Sequence,
    statistic: Callable[[Sequence], float],
    *,
    n_resamples: int = 1000,
    seed: int = 2026,
) -> dict:
    """Estimate paired percentile intervals for two aligned collections."""
    if len(items_a) != len(items_b) or not items_a:
        raise ValueError("paired inputs must have equal non-zero length")
    rng = np.random.default_rng(seed)
    values_a: list[float] = []
    values_b: list[float] = []
    deltas: list[float] = []
    for _ in range(n_resamples):
        indices = rng.integers(0, len(items_a), size=len(items_a))
        sample_a = [items_a[index] for index in indices]
        sample_b = [items_b[index] for index in indices]
        value_a = float(statistic(sample_a))
        value_b = float(statistic(sample_b))
        values_a.append(value_a)
        values_b.append(value_b)
        deltas.append(value_a - value_b)
    return {
        "n_items": len(items_a),
        "n_resamples": n_resamples,
        "seed": seed,
        "method_a_ci95": percentile_interval(values_a),
        "method_b_ci95": percentile_interval(values_b),
        "delta_ci95": percentile_interval(deltas),
    }
