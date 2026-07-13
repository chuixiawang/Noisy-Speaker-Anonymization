# Evaluation Protocol

## Main corpus and trials

The main protocol uses LibriSpeech `test-clean` at 16 kHz. With random seed 2026,
the builder selects 20 speakers with an equal male/female split and samples 10
utterances per speaker, producing 200 utterances.

Speaker-verification trials are constructed as follows:

- Positive trials: every unordered pair among the 10 utterances of each speaker,
  giving `20 x C(10, 2) = 900` trials.
- Negative trials: 900 cross-speaker utterance pairs sampled with seed 2026.

The protocol builder writes `speaker_pairs.csv`, `utterance_list.txt`,
`transcripts.txt`, and `protocol_config.json`.

## Noise panels

The canonical panel contains eight conditions formed by two noise types and four
SNR levels:

| Noise type | SNR levels (dB) | Role |
|---|---:|---|
| White | 20, 10, 5, 0 | Known calibration family |
| Babble | 20, 10, 5, 0 | Known calibration family |

Additional boundary panels used in the paper are not bundled as audio:

- unseen noise: MUSAN music and DEMAND ambient noise;
- replay: two replay-recorded noisy conditions;
- hard subset: long-duration, high-word-count utterances;
- stress test: four canonical conditions used for the denoising/control ablation.

Noise and speech must be mixed at the requested SNR before anonymization. The same
selected clean utterances are reused across methods and conditions.

## Strength policies

Candidate strengths are `0.3, 0.4, 0.5, 0.6, 0.7, 0.8`. The offline reference
policy selects the lowest-utility-loss candidate satisfying the lazy-informed
privacy budget. CASR does not read noise type or SNR labels during inference; the
condition names in released artifacts are used only to group and report results.

## Attackers and metrics

- Ignorant attacker: original enrollment and original verifier.
- Lazy-informed attacker: enrollment is processed by a similar anonymization
  scheme; this is the primary privacy protocol.
- Semi-informed attacker: the verifier is retrained on anonymized speech.

Privacy is measured by equal error rate (EER), where higher is better for privacy.
Utility is measured by word error rate (WER) and character error rate (CER), where
lower is better. Text is lowercased, punctuation is removed, and whitespace is
normalized before scoring. WER may exceed 100% because insertions are unbounded.

The primary ASV verifier is ECAPA-TDNN, with WavLM used as a verifier-robustness
check. Whisper-base is used for ASR. Paired 95% bootstrap confidence intervals use
1,000 resamples.

## Reproducibility boundary

The release exposes the CASR controller and deterministic protocol generation.
It does not redistribute external datasets, pretrained verifiers, Whisper,
SSL-SAS, mHuBERT, HiFi-GAN, or their model weights. Users must obtain these
components independently and record the versions used.
