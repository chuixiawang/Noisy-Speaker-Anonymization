# Noisy Speaker Anonymization

Reference code and evaluation protocol for **Condition-Aggregated State Recovery
(CASR)**, a runtime control layer for noisy speaker anonymization.

CASR does not replace or retrain the anonymization backbone. It estimates an
utterance-level anonymization strength from lightweight acoustic cues, aggregates
the predictions into one condition-level decision, applies the calibration path
used in the reported experiments, and emits a read-only Alpha-Control Evidence
Gate (ACEG) record.

## Released components

- `src/casr/features.py`: eight acoustic descriptors used in the ablation study.
- `src/casr/controller.py`: quadratic predictor, condition aggregation,
  uncertainty calibration, and ACEG.
- `src/casr/protocol.py`: deterministic 20-speaker/200-utterance LibriSpeech
  protocol with 900 positive and 900 negative verification trials.
- `src/casr/noise.py`: deterministic additive-noise mixing at a target SNR.
- `src/casr/metrics.py` and `bootstrap.py`: EER, WER/CER, and paired bootstrap
  helpers.
- `configs/`: the released CASR policy, offline reference strengths, and protocol
  metadata.
- `artifacts/canonical_utterance_predictions.json`: 1,600 derived prediction
  records for checking condition-level recovery without distributing speech.

The repository intentionally excludes speech corpora, noise recordings, model
weights, generated audio, and third-party anonymization implementations.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The reference controller requires Python 3.10 or later and NumPy. Audio passed to
the released policy must be mono, 16-bit PCM, and sampled at 16 kHz.

## Reproduce the canonical controller decisions

```bash
python scripts/recover_canonical.py
```

The command reads the released utterance-level predictions, applies the same
condition-level control path, and prints the recovered strength and ACEG metadata
for each of the eight canonical conditions.

To inspect one condition:

```bash
casr recover \
  --policy configs/casr_policy.json \
  --predictions artifacts/canonical_utterance_predictions.json \
  --condition babble_snr5dB
```

## Build the fixed evaluation protocol

Download LibriSpeech separately and point the command to the directory containing
`SPEAKERS.TXT` and `test-clean/`:

```bash
casr build-protocol \
  --data-root /path/to/LibriSpeech \
  --output outputs/eval_protocol \
  --seed 2026
```

The generated protocol contains 20 speakers, 10 utterances per speaker, 900
same-speaker trials, and 900 different-speaker trials. See
[`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md) for the complete
evaluation definition.

## Scope and limitations

This is the paper's control-layer and protocol release, not a standalone SSL-SAS
backbone. End-to-end waveform anonymization still requires a compatible backbone
that exposes anonymization strength `alpha`. The reported policy was calibrated on
white and babble noise at 20, 10, 5, and 0 dB; results on unseen noise types should
not be interpreted as guaranteed generalization.

## Data and licensing notice

No corpus audio is redistributed. Obtain [LibriSpeech](https://www.openslr.org/12/)
and [MUSAN](https://www.openslr.org/17/) from OpenSLR under CC BY 4.0. Obtain
[DEMAND](https://zenodo.org/records/1227121) from its official Zenodo record under
CC BY-SA 3.0. The repository currently does not assign an open-source software
license; absent an explicit license, reuse rights are not granted beyond viewing
and evaluating the published material.
