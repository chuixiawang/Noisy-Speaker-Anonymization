"""Deterministic additive-noise utilities for the canonical evaluation panel."""

from __future__ import annotations

import numpy as np


def rms(signal: np.ndarray) -> float:
    signal = np.asarray(signal, dtype=np.float64)
    return float(np.sqrt(np.mean(signal**2) + 1e-12))


def mix_at_snr(clean: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """Crop/tile a noise signal and mix it with clean speech at the requested SNR."""
    clean = np.asarray(clean, dtype=np.float32).reshape(-1)
    noise = np.asarray(noise, dtype=np.float32).reshape(-1)
    if clean.size == 0 or noise.size == 0:
        raise ValueError("clean and noise signals must be non-empty")
    if noise.size < clean.size:
        noise = np.tile(noise, int(np.ceil(clean.size / noise.size)))
    noise = noise[: clean.size]
    scale = rms(clean) / (rms(noise) * (10.0 ** (float(snr_db) / 20.0)))
    mixed = clean.astype(np.float64) + noise.astype(np.float64) * scale
    peak = float(np.max(np.abs(mixed)))
    if peak > 0.999:
        mixed = mixed * (0.999 / peak)
    return mixed.astype(np.float32)


def add_white_noise(clean: np.ndarray, snr_db: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(np.asarray(clean).size).astype(np.float32)
    return mix_at_snr(clean, white, snr_db)
