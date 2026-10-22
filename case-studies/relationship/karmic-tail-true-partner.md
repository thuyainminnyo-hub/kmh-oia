# Karmic Tail — True Partner Case Study

- **Case ID:** `KMH-OIA-CS-KTTP-001`
- **Registry:** `data/karmic_tail_true_partner_registry.json`
- **Runtime helper:** `src/karmic_tail_registry.py`
- **Tests:** `tests/test_karmic_tail_registry.py`
- **Mode:** Symbolic self-reflection, not prediction or psychological assessment

## Purpose

Use the 22 Major Arcana archetypes as optional reflection prompts about relationship habits. The cards are not evidence that a person has a particular trait and cannot determine when or whether someone will meet a partner.

## Execution contract

1. Load and validate the canonical JSON registry.
2. Select cards by canonical IDs (1–22).
3. Present the interpretation as a hypothesis.
4. Ask a neutral reflection question and respect the user's answer.
5. Offer an optional, practical action.
6. Reject unsupported certainty, guaranteed predictions, and diagnosis.
7. Record only the minimum event metadata needed for audit, subject to approved privacy and retention rules.

## Verification

Run from the repository root:

```bash
python -m unittest tests.test_karmic_tail_registry -v
```

The test suite covers the 22-card inventory, duplicate and missing IDs, required safeguards, and user-confirmation handling.

## Status and limitations

This change adds a registry and deterministic helper logic. It does not add a web API, persistent event storage, production telemetry, or a deployed user-facing workflow. Tests must be executed in CI or a suitable local environment before the module can be marked verified.
