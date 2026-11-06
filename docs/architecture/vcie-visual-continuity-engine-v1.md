# VCIE v1 — Visual Continuity Engine

**Status:** Implemented deterministic policy gate; visual inference adapter is not implemented.
**Branch:** `feat/vcie-visual-continuity-engine-v1`

## Purpose

VCIE evaluates whether a generated shot has sufficient, traceable continuity evidence against approved references in the KMH OIA registry. It is a production QA gate, not a video generator.

Higgsfield's Elements workflow supports reusable characters, locations and props; Cinema Studio 4.0 documentation describes up to 50 references per generation and camera/style controls. KMH stores canonical IDs and versions independently so the pipeline is not tied to one vendor.

## Architecture

1. **Registry** — immutable asset IDs and approved versions for character, costume, props, location and visual style.
2. **Execution Bridge** — records provider, model/version, prompt version, settings, generated asset ID and provider job ID.
3. **Evaluator Adapter (future)** — produces normalized dimension scores and evidence URIs using vision models and/or human review.
4. **Policy Gate (implemented)** — validates score ranges, required dimensions and versioned thresholds; missing dimensions become REVIEW, low scores become REWORK.
5. **Evidence/Audit** — stores report, policy version, evaluator/version and evidence references.
6. **Learning** — consumes approved human decisions and classified failures; does not silently change thresholds.

## Evaluation contract

All scores are normalized to [0, 1]. Default pilot thresholds:

| Dimension | Threshold |
|---|---:|
| Face identity | 0.95 |
| Costume | 0.90 |
| Props | 0.90 |
| Environment | 0.90 |
| Lighting | 0.85 |

These are **provisional engineering thresholds**, not Higgsfield settings, scientific guarantees, or validated human-perception cutoffs. Calibrate them against a labelled KMH dataset.

### Status semantics

- `PASS`: every required dimension has a score at/above threshold. Human review remains enabled by default.
- `REWORK`: all required dimensions are present and at least one is below threshold.
- `REVIEW`: one or more required dimensions are missing. Missing evidence never passes.

A score is only as trustworthy as its evaluator. SSIM/LPIPS are not identity metrics; use task-specific face embeddings only where consent and applicable law permit, plus human review. SSIM requires aligned references and can penalize legitimate camera/view changes. LPIPS is a perceptual distance, not proof of identity. Never use a single scalar as the final creative-quality decision.

## Python API

```python
from src.visual_continuity import (
    ShotEvidence, RuleBasedContinuityEvaluator, ContinuityPolicy
)

evidence = ShotEvidence(
    film_id="FILM-001",
    scene_id="SCENE-001",
    shot_id="SHOT-001",
    reference_asset_ids=("CHAR-001-v1", "LOC-001-v1"),
    generated_asset_id="ASSET-001",
    evaluator="human-review",
    evaluator_version="1",
    scores={
        "face_identity": 0.98,
        "costume": 0.95,
        "props": 0.93,
        "environment": 0.94,
        "lighting": 0.90,
    },
    evidence_uris=("evidence://review/001",),
)
report = RuleBasedContinuityEvaluator().evaluate(evidence, ContinuityPolicy())
print(report.to_dict())
```

## Non-goals / limitations

- No image/video is read or compared by this module.
- No face-recognition model, embedding store, optical-flow analysis or CV dependency is bundled.
- No automatic Higgsfield API call is performed.
- No persistence adapter is wired into the current OIA StateStore.
- The evaluator scores in tests are fixtures, not real production measurements.

## Verification

Run:

```bash
python -m unittest discover -s tests -v
```

The test suite covers pass, rework, missing-evidence review, invalid scores, missing references, policy integrity and report serialization.

## Next gates

1. Define Registry asset/version contract and immutable provenance.
2. Implement a pluggable image evaluator; benchmark against human-labelled shots.
3. Add video-level temporal continuity (shot boundaries, motion, screen direction).
4. Persist reports through a dedicated evidence repository.
5. Add calibrated policy promotion/rollback and human sign-off.
