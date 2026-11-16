# Calibration

Calibration uses only the development set (LibriSpeech `dev-clean`, 20 speakers,
200 utterances) under the eight canonical conditions. No evaluation speaker is used.

1. **EER grid.** Anonymize the development set at every candidate strength
   `{0.3, ..., 0.8}` under every condition and measure the lazy-informed EER.
2. **Margin.** Split the 20 development speakers into two halves at random 500 times
   with stratification by gender. On the grid cells whose development EER lies
   between 35% and 46%, compute the absolute EER difference between the halves,
   scale it by `1/sqrt(2)` to the case of 20 versus 20 speakers, and take the 90th
   percentile rounded up to 0.1. This gives `m = 3.2` points and the calibration
   threshold `tau_cal = 40.5 + 3.2 = 43.7%`.
3. **Reference policy.** For each condition `c`, `g(c)` is the smallest candidate
   whose development-set EER meets `tau_cal`. The released values are in
   `configs/offline_reference_policy.json`.
4. **Regressor.** Extract the spectral centroid and the energy contrast of every
   development utterance, expand them to five second-order terms, standardize them,
   and fit a ridge regressor (`lambda = 1e-3`, unpenalized intercept) to the target `g(c)` of
   the utterance's condition. The coefficients and standardization statistics are in
   `configs/casr_policy.json`.
5. **Fixed thresholds.** The down-step thresholds (dispersion 0.04, mode-median gap
   0.05, shift 0.05) and the ACEG thresholds (mode share 0.50, entropy 1.10,
   dispersion 0.08, mode-median gap 0.10) are fixed values shared by all experiments.

The released artifact `artifacts/canonical_utterance_predictions.json` contains the
features and the regressor outputs of the 20-speaker main panel. Running
`python scripts/recover_canonical.py` reproduces the batch strengths reported for
that panel.
