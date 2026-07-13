"""Lightweight acoustic features used by the CASR controller."""

from __future__ import annotations

import contextlib
import wave
from pathlib import Path

import numpy as np

BASE_FEATURES = (
    "flatness_mean",
    "low_band_ratio_mean",
    "high_band_ratio_mean",
    "zcr_mean",
    "centroid_norm_mean",
    "rolloff85_norm_mean",
    "active_frame_ratio",
    "energy_contrast_norm",
)


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a mono 16-bit PCM WAV file as float32 samples."""
    path = Path(path)
    with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
        num_frames = wav_file.getnframes()
        sample_width = wav_file.getsampwidth()
        num_channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        pcm = wav_file.readframes(num_frames)
    if sample_width != 2 or num_channels != 1:
        raise ValueError(f"Only 16-bit mono WAV is supported: {path}")
    waveform = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    return waveform, sample_rate


def extract_utterance_features(
    waveform: np.ndarray,
    sample_rate: int,
) -> dict[str, float]:
    """Extract the eight descriptors used in the feature ablation.

    The released policy was calibrated at 16 kHz. Inputs at another sampling
    rate must be resampled before calling this function.
    """
    if sample_rate != 16_000:
        raise ValueError(f"CASR expects 16 kHz audio, received {sample_rate} Hz")

    waveform = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if waveform.size == 0:
        raise ValueError("waveform must contain at least one sample")

    frame_size = 512
    hop_size = 256
    eps = 1e-8
    if len(waveform) < frame_size:
        waveform = np.pad(waveform, (0, frame_size - len(waveform)))

    num_frames = 1 + (len(waveform) - frame_size) // hop_size
    frames = np.lib.stride_tricks.as_strided(
        waveform,
        shape=(num_frames, frame_size),
        strides=(waveform.strides[0] * hop_size, waveform.strides[0]),
    ).copy()
    frames *= np.hanning(frame_size)[None, :]

    magnitude = np.abs(np.fft.rfft(frames, axis=1)) + eps
    power = magnitude**2
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)

    frame_energy = np.mean(frames**2, axis=1) + eps
    rms_db = 20.0 * np.log10(np.sqrt(frame_energy) + eps)
    zcr = np.mean(np.abs(np.diff(np.signbit(frames), axis=1)), axis=1)
    centroid = (magnitude * freqs[None, :]).sum(axis=1) / magnitude.sum(axis=1)
    flatness = np.exp(np.mean(np.log(power), axis=1)) / np.mean(power, axis=1)

    cumulative = np.cumsum(power, axis=1)
    total = cumulative[:, -1]
    rolloff_idx = np.argmax(cumulative >= (0.85 * total)[:, None], axis=1)
    rolloff_hz = freqs[rolloff_idx]

    low_energy = power[:, freqs <= 1000].sum(axis=1)
    high_energy = power[:, freqs >= 3000].sum(axis=1)
    total_energy = power.sum(axis=1)
    active_threshold_db = float(np.percentile(rms_db, 20.0) + 6.0)
    contrast_db = float(np.percentile(rms_db, 95.0) - np.percentile(rms_db, 20.0))

    return {
        "flatness_mean": float(np.mean(flatness)),
        "low_band_ratio_mean": float(np.mean(low_energy / total_energy)),
        "high_band_ratio_mean": float(np.mean(high_energy / total_energy)),
        "zcr_mean": float(np.mean(zcr)),
        "centroid_norm_mean": float(np.mean(centroid) / 4000.0),
        "rolloff85_norm_mean": float(np.mean(rolloff_hz) / 8000.0),
        "active_frame_ratio": float(np.mean(rms_db > active_threshold_db)),
        "energy_contrast_norm": float(contrast_db / 30.0),
    }
