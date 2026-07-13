# Implementation Notes

The public implementation was extracted from the experiment repository and keeps
the numerical path used for the reported canonical experiments:

1. extract spectral centroid and energy contrast from each 16 kHz utterance;
2. expand them to six polynomial terms including the bias;
3. standardize features using the released calibration statistics;
4. predict and snap each strength to the candidate grid;
5. aggregate snapped predictions by condition-level mode;
6. apply the released uncertainty calibration;
7. compute ACEG after strength selection as read-only audit metadata.

The uncertainty calibration is separate from ACEG. ACEG never changes the selected
strength. Its pass flag summarizes internal concentration and does not guarantee
agreement with the offline reference policy.

The `aggregation_mode: p75` field in the policy records the model-selection setting
used when fitting the predictor. Runtime condition recovery uses the mode of snapped
utterance-level predictions, as implemented in `recover_condition_strength`.
