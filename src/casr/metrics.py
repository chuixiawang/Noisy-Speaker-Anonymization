"""Metric helpers used by the released evaluation protocol."""

from __future__ import annotations

import re
from collections.abc import Sequence

import numpy as np


def normalize_transcript(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return " ".join(text.split())


def _edit_counts(reference: Sequence[str], hypothesis: Sequence[str]) -> dict[str, int]:
    rows = len(reference) + 1
    cols = len(hypothesis) + 1
    cost = [[0] * cols for _ in range(rows)]
    op = [[""] * cols for _ in range(rows)]
    for i in range(1, rows):
        cost[i][0] = i
        op[i][0] = "D"
    for j in range(1, cols):
        cost[0][j] = j
        op[0][j] = "I"
    for i in range(1, rows):
        for j in range(1, cols):
            if reference[i - 1] == hypothesis[j - 1]:
                cost[i][j] = cost[i - 1][j - 1]
                op[i][j] = "="
                continue
            options = (
                (cost[i - 1][j - 1] + 1, "S"),
                (cost[i - 1][j] + 1, "D"),
                (cost[i][j - 1] + 1, "I"),
            )
            cost[i][j], op[i][j] = min(options, key=lambda item: item[0])
    counts = {"S": 0, "I": 0, "D": 0, "N": len(reference)}
    i, j = len(reference), len(hypothesis)
    while i or j:
        action = op[i][j]
        if action == "=":
            i -= 1
            j -= 1
        elif action == "S":
            counts["S"] += 1
            i -= 1
            j -= 1
        elif action == "D":
            counts["D"] += 1
            i -= 1
        elif action == "I":
            counts["I"] += 1
            j -= 1
        else:
            raise RuntimeError("invalid edit-distance backtrace")
    return counts


def word_error_counts(reference: str, hypothesis: str) -> dict[str, int]:
    return _edit_counts(
        normalize_transcript(reference).split(), normalize_transcript(hypothesis).split()
    )


def character_error_counts(reference: str, hypothesis: str) -> dict[str, int]:
    ref = list(normalize_transcript(reference).replace(" ", ""))
    hyp = list(normalize_transcript(hypothesis).replace(" ", ""))
    return _edit_counts(ref, hyp)


def error_rate_percent(counts: dict[str, int]) -> float:
    return 100.0 * (counts["S"] + counts["I"] + counts["D"]) / max(counts["N"], 1)


def eer_percent(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Compute EER by sweeping score thresholds and averaging FAR/FRR at the crossing."""
    scores_array = np.asarray(scores, dtype=np.float64)
    labels_array = np.asarray(labels, dtype=np.int8)
    if scores_array.shape != labels_array.shape or scores_array.ndim != 1:
        raise ValueError("scores and labels must be one-dimensional arrays of equal length")
    positives = int(labels_array.sum())
    negatives = len(labels_array) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("EER requires both positive and negative trials")
    order = np.argsort(scores_array)[::-1]
    sorted_labels = labels_array[order]
    true_positive = np.cumsum(sorted_labels)
    false_positive = np.cumsum(1 - sorted_labels)
    false_reject = (positives - true_positive) / positives
    false_accept = false_positive / negatives
    index = int(np.argmin(np.abs(false_accept - false_reject)))
    return float((false_accept[index] + false_reject[index]) * 50.0)
