# Evaluation Protocol

## Evaluation panels and development set

All audio is LibriSpeech at 16 kHz. Three evaluation panels are used:

| Panel | Speakers | Utterances | Source |
|---|---:|---:|---|
| Main panel | 20 | 200 | LibriSpeech `test-clean`, seed 2026, equal male/female split, 10 utterances per speaker |
| 40-speaker panel | 40 | 400 | all speakers of LibriSpeech `test-clean` |
| VPC29 panel | 29 | 290 | `test-clean` speakers used in the VoicePrivacy evaluation |

Calibration uses only a development set of 20 speakers and 200 utterances from
LibriSpeech `dev-clean`, whose speakers do not overlap with any evaluation panel.
Each evaluation set is used once.

## Trials

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

- real recorded noise: 12 DEMAND conditions (four environments, three SNRs);
- unseen noise: MUSAN music and ambient noise;
- re-recorded speech: main-panel utterances replayed through a loudspeaker with
  restaurant noise in a small furnished room and recorded with a laptop microphone
  (about 7 dB and 13 dB SNR);
- mixed batches: utterances of a second condition mixed into a batch at 10%, 25%,
  and 50%.

Noise and speech must be mixed at the requested SNR before anonymization. The same
selected clean utterances are reused across methods and conditions.

## Strength policies

Candidate strengths are `0.3, 0.4, 0.5, 0.6, 0.7, 0.8`. The minimum target EER is
`tau = 40.5%`. The reference policy `g(c)` is the smallest candidate whose
development-set EER meets the calibration threshold `tau_cal = tau + m = 43.7%`
(margin `m = 3.2` points). The global fixed strength, the SNR lookup, and the
reference-policy lookup used for comparison select their parameters on the same
development set. CASR does not read noise type or SNR labels when it selects a
strength; the condition names in released artifacts are used only to group and
report results.

## Attackers and metrics

- Lazy-informed attacker: enrollment is processed by a similar anonymization
  scheme and the verifier is not retrained. All conclusions use this attacker.

Privacy is measured by equal error rate (EER), where higher is better for privacy.
Utility is measured by word error rate (WER) and character error rate (CER), where
lower is better. Text is lowercased, punctuation is removed, and whitespace is
normalized before scoring. WER may exceed 100% because insertions are unbounded.

The ASV verifier is ECAPA-TDNN and the ASR model is Whisper-base. Every WER is
averaged over three decoding seeds. Confidence intervals are 95% speaker-cluster
bootstrap intervals with 2,000 resamples, and paired t-tests and Wilcoxon
signed-rank tests are computed over speakers.

## Reproducibility boundary

The release exposes the CASR controller and deterministic protocol generation.
It does not redistribute external datasets, pretrained verifiers, Whisper,
SSL-SAS, mHuBERT, HiFi-GAN, or their model weights. Users must obtain these
components independently and record the versions used.
