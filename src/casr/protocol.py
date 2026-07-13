"""Deterministic LibriSpeech protocol construction used in the paper."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from itertools import combinations
from pathlib import Path

SEED = 2026
N_SPEAKERS = 20
UTTERANCES_PER_SPEAKER = 10


def parse_speakers(path: Path) -> dict[str, dict]:
    speakers: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(";") or not line.strip():
                continue
            fields = [field.strip() for field in line.split("|")]
            if len(fields) >= 5:
                speakers[fields[0]] = {"gender": fields[1], "subset": fields[2]}
    return speakers


def collect_utterances(subset: Path) -> tuple[dict[str, list[tuple[str, Path]]], dict[str, str]]:
    utterances: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    transcripts: dict[str, str] = {}
    for audio_path in sorted(subset.rglob("*.flac")):
        utterances[audio_path.parts[-3]].append((audio_path.stem, audio_path))
    for transcript_path in sorted(subset.rglob("*.trans.txt")):
        with transcript_path.open(encoding="utf-8") as handle:
            for line in handle:
                fields = line.strip().split(maxsplit=1)
                if len(fields) == 2:
                    transcripts[fields[0]] = fields[1]
    return dict(utterances), transcripts


def select_protocol(
    data_root: Path,
    *,
    seed: int = SEED,
    n_speakers: int = N_SPEAKERS,
    utterances_per_speaker: int = UTTERANCES_PER_SPEAKER,
) -> dict:
    """Select 20 speakers x 10 utterances and construct 900/900 trials."""
    rng = random.Random(seed)
    subset = data_root / "test-clean"
    if not subset.is_dir():
        raise FileNotFoundError(f"LibriSpeech test-clean not found under {data_root}")
    metadata = parse_speakers(data_root / "SPEAKERS.TXT")
    utterances, transcripts = collect_utterances(subset)
    eligible = [
        speaker for speaker, rows in utterances.items() if len(rows) >= utterances_per_speaker
    ]
    male = [speaker for speaker in eligible if metadata.get(speaker, {}).get("gender") == "M"]
    female = [speaker for speaker in eligible if metadata.get(speaker, {}).get("gender") == "F"]
    rng.shuffle(male)
    rng.shuffle(female)
    selected = sorted(male[: n_speakers // 2] + female[: n_speakers - n_speakers // 2])
    if len(selected) != n_speakers:
        raise ValueError("not enough eligible speakers for the requested gender-balanced protocol")

    selected_rows: dict[str, list[tuple[str, Path]]] = {}
    for speaker in selected:
        rows = list(utterances[speaker])
        rng.shuffle(rows)
        selected_rows[speaker] = rows[:utterances_per_speaker]

    positive = []
    for speaker, rows in selected_rows.items():
        for enrol, test in combinations(rows, 2):
            positive.append((1, enrol[0], test[0], speaker, speaker))

    flat = [(speaker, row[0]) for speaker, rows in selected_rows.items() for row in rows]
    negative_candidates = [
        (0, left[1], right[1], left[0], right[0])
        for left, right in combinations(flat, 2)
        if left[0] != right[0]
    ]
    rng.shuffle(negative_candidates)
    negative = negative_candidates[: len(positive)]
    return {
        "seed": seed,
        "selected_speakers": selected,
        "utterances": selected_rows,
        "transcripts": transcripts,
        "trials": positive + negative,
        "n_positive_trials": len(positive),
        "n_negative_trials": len(negative),
    }


def write_protocol(protocol: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "speaker_pairs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("label", "enrol_id", "test_id", "enrol_spk", "test_spk"))
        writer.writerows(protocol["trials"])
    with (output_dir / "utterance_list.txt").open("w", encoding="utf-8") as handle:
        for speaker in protocol["selected_speakers"]:
            for utterance_id, path in protocol["utterances"][speaker]:
                handle.write(f"{utterance_id} {path}\n")
    with (output_dir / "transcripts.txt").open("w", encoding="utf-8") as handle:
        for speaker in protocol["selected_speakers"]:
            for utterance_id, _ in protocol["utterances"][speaker]:
                handle.write(f"{utterance_id} {protocol['transcripts'][utterance_id]}\n")
    metadata = {
        "seed": protocol["seed"],
        "n_speakers": len(protocol["selected_speakers"]),
        "utterances_per_speaker": len(next(iter(protocol["utterances"].values()))),
        "n_positive_trials": protocol["n_positive_trials"],
        "n_negative_trials": protocol["n_negative_trials"],
        "selected_speakers": protocol["selected_speakers"],
    }
    (output_dir / "protocol_config.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
