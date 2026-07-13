# Research Ethics and Release Review

- Review object: public CASR code, protocol metadata, and derived predictions
- Review type: code and supplementary-material release
- Reviewer/date: Codex-assisted author review, 2026-07-13
- Applicable context: public academic software release; dataset terms remain those
  of the original providers

## Risk assessment

| Level | Category | Evidence and decision | Mitigation | Third-party review |
|---|---|---|---|---|
| NOTE | Research integrity | Released coefficients and prediction records are copied from the experiment repository; no result is fabricated or recomputed for presentation. | Preserve source artifact names and test all numerical paths. | No |
| NOTE | Selective reporting | The release includes all eight canonical conditions and documents unseen-noise limits. | Keep boundary statements in README and protocol document. | No |
| NOTE | Images | No generated or edited research images are included. | None required. | No |
| NOTE | Citations | Dataset names are documented; the paper remains the source of the full bibliography. | Add formal citation metadata after the paper receives a stable identifier. | No |
| NOTE | Authorship | Repository publication does not determine paper authorship. | Paper authors must approve the final CRediT statement separately. | Corresponding author |
| NOTE | Privacy and human data | No newly recorded human data, raw corpus audio, or personal identifiers are released. LibriSpeech utterance IDs are public corpus identifiers. | Do not add local recordings, enrollment audio, or user metadata. | No |
| NOTE | Animal research | Not applicable. | None required. | No |
| WARN | Copyright and licenses | External corpora, checkpoints, and third-party model code are excluded. LibriSpeech-derived prediction records are released without audio. The repository itself has no software license yet. | Obtain datasets from official sources; choose a software license before inviting reuse. | Repository owner |
| NOTE | Claim strength | README states that this is a control-layer release, not a complete SSL-SAS backbone or evidence of universal unseen-noise generalization. | Retain the scope and limitation section. | No |
| NOTE | AI assistance | AI assisted with code extraction, documentation, and review; the author remains responsible for validation. | Disclose according to the target journal's policy if required. | Corresponding author/editor if required |
| NOTE | Patents and software registration | No patent or software-copyright claim is made in this repository. | Reassess before a later IP filing. | No |

## Authorship and contribution boundary

The repository does not assign authorship. Each paper author must satisfy the
journal's authorship requirements and approve the final manuscript. CRediT roles
must be completed by the author team; AI tools are not authors.

## Decision

**Conditionally approved for public release.** No blocking privacy, fabrication,
or third-party redistribution issue was found in the selected files. The remaining
warning is the absence of an explicit software license; until the repository owner
chooses one, the default copyright position applies and reuse is not granted.
