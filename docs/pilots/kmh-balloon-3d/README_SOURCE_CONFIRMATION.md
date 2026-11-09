# Source Owner State Confirmation Pack v1.0

Use this pack to obtain documented provenance for the 16 existing references. No item should be promoted from UNKNOWN unless the confirmer and evidence are recorded.

## Contents
- State confirmation guide.
- One-row-per-image CSV register.
- JSON confirmation template.
- JSON registry of the current conservative state labels.
- Python validator.

Run:
```bash
python source_owner_confirmation_validator.py source_owner_confirmation_register.csv
```

Allowed labels: BASE-UNLOADED, DISPLAYED-ATTACHED, UNKNOWN, NOT_APPLICABLE. A state change from UNKNOWN to a confirmed state requires a named confirmer, their relationship to the source, an accepted evidence basis, a traceable evidence reference, and a date. VISUAL_INFERENCE_ONLY is insufficient.
