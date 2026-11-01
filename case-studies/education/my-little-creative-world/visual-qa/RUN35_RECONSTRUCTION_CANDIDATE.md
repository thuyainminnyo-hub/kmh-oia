# MLCW V1.0.8 — Run #35 Reconstruction Candidate Inspection

**Approval:** Option B approved by user.  
**Candidate asset:** `Thiri_Clean_Base_Reconstruction_Candidate.png`  
**Original reference:** `15309(1).png`

## Candidate file facts

- Dimensions: 1024 × 1536 (matches the canonical canvas dimensions).
- Mode: RGB (white background; not transparent).
- SHA-256: `361f18a1c2046acc4c9bf90740a3a398923c735f79852d1fabaed63de0de8633`
- Stored in user Library: `/My Little Creative World/Run 35/Thiri_Clean_Base_Reconstruction_Candidate.png`
- The candidate is a newly generated reconstruction guided by the supplied Thiri reference, not an exact pixel edit or recovered original body.
- It depicts a fully clothed neutral gray long-sleeve top and ankle-length skirt to keep the base modest and reusable.

## Reference file facts

- Original `15309(1).png`: 1024 × 1536 RGBA.
- SHA-256: `6abcdb53c85ef40eaab0f824c3a0ae164cc38ac3ca6fee1a7c823ed0e77f632e`
- Alpha channel is fully opaque.

## What is verified

- A reconstruction candidate image was generated.
- Candidate dimensions match the 1024 × 1536 reference canvas.
- Candidate is saved to the user's persistent Library.

## What is not verified

- Exact face/hair/earring pixel preservation (candidate is generated, not an edit of original pixels).
- Quantitative identity similarity, SSIM/IoU or protected-region delta.
- Transparent background / alpha channel (candidate is RGB on white).
- Clean-body fit as a production garment-underlayer.
- P01 layer extraction, garment alignment, compositing or final outfit QA.

## Decision

**Run #35 reconstruction candidate: GENERATED / VISUAL REVIEW REQUIRED.**  
**Production Master Base: NOT APPROVED YET.**

Before using it as the canonical base, the user must visually approve the face, eye shape, bun, flower, earrings, pose and proportions. If approved, next prepare an alpha-matted version and a neutral underlayer specification; then separate the P01 blouse, longyi and drape and proceed to composite/QA. Do not report PASS for identity preservation or P01 composite at this stage.
