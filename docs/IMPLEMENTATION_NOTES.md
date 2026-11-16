# Implementation Notes

The public implementation was extracted from the experiment repository and keeps
the numerical path used for the reported canonical experiments:

1. extract spectral centroid and energy contrast from each 16 kHz utterance;
2. expand them to six polynomial terms including the bias;
3. standardize features using the released calibration statistics;
4. predict and snap each strength to the candidate grid;
5. aggregate snapped predictions by condition-level mode;
6. apply the down-step rule (`conservative_shift` in the code);
7. compute ACEG after strength selection as read-only audit metadata.

The down-step rule is separate from ACEG. When the utterance-level estimates of a
batch are dispersed (standard deviation of at least 0.04), the rule takes the
snapped median if the mode and the median differ by at least 0.05; otherwise it
shifts all estimates down by 0.05 and votes again. ACEG never changes the selected
strength. Its pass flag summarizes the consistency of the estimates and does not
guarantee agreement with the reference policy.
