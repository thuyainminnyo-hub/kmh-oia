# KMH_BAL_001 — Source Owner State Confirmation Pack v1.0

Use this pack to obtain source-backed state confirmation for the existing balloon reference images.

## Files
- `SOURCE_OWNER_STATE_CONFIRMATION_V1.md` — definitions, confirmation standards, and evidence rules.
- `templates/source_owner_confirmation_register.csv` — one row per existing image.
- `templates/source_owner_confirmation_template.json` — machine-readable confirmation record.
- `registry/source_owner_confirmation_registry_v1.json` — current known source information and state status.
- `scripts/source_owner_confirmation_validator.py` — prevents unsupported state promotion.

## Allowed states
- `BASE-UNLOADED`
- `DISPLAYED-ATTACHED`
- `UNKNOWN`
- `NOT_APPLICABLE`

Do not infer BASE-UNLOADED from a cropped or hidden attachment area. A close-up of the Yan-Khwe alone does not prove that it is attached to the balloon in the same scene.

## Confirmation required to promote a state
A change from UNKNOWN to BASE-UNLOADED or DISPLAYED-ATTACHED requires:
- confirmer identity/role and relationship to source;
- a basis of DIRECT_WITNESS, ORIGINAL_CREATOR, TEAM_RECORD, or DOCUMENTED_SOURCE;
- an evidence reference; and
- a confirmation date.

VISUAL_INFERENCE_ONLY is insufficient.

## Validate the register
```bash
python scripts/source_owner_confirmation_validator.py templates/source_owner_confirmation_register.csv
```

The current template passes with all uncertain states preserved. Validation does not itself confirm any state.

## Scope
This pack concerns source identity and visual-state provenance only. It does not request or record pyrotechnic construction, attachment mechanics, ignition, timing, launch, or operating information. Original images and SHA-256 hashes must remain unchanged.
