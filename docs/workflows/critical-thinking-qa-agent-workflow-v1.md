# KMH Workflow — Critical Thinking Agent + QA Agent v1.0

**Workflow ID:** KMH-WF-CRIT-QA-001  
**Related case study:** KMH-CS-HUMAN-LOVE-LOGIC-001 — Human Love, Logic & the Fallacy of Rational Control  
**Classification:** Agent workflow / Critical thinking / Narrative QA  
**Status:** BUILD SPEC — RUNTIME NOT VERIFIED  
**Owner principle:** KMH owns the task contract, source memory, QA rules, evidence trail, and final approval. An agent framework is only an execution layer.

## 1. Objective

Turn a supplied argument, dialogue, story, or case study into an evidence-grounded critical-thinking report. The workflow must identify reasoning patterns without treating every disagreement, emotion, or imperfect statement as a fallacy.

This is a literary-analysis and reasoning-support workflow, not a system for diagnosing people or deciding whether a relationship is right for someone.

## 2. Pipeline

```text
Trigger / User submits text
        |
        v
Create Correlation_ID
        |
        v
Normalize source + preserve exact quotations
        |
        v
Critical Thinking Agent
  - extract claims and premises
  - identify conclusion and implied assumptions
  - propose fallacy labels with evidence
  - note uncertainty and alternative readings
        |
        v
QA Agent (independent review)
  - verify quotation-to-claim traceability
  - check whether the label fits the reasoning
  - distinguish factual errors from fallacies
  - check nuance, autonomy, and unsupported inference
        |
        +---- FAIL / UNCERTAIN ----> Rework or Human Review
        |                                |
        |                                v
        |                          Re-run QA (bounded)
        v
PASS
        |
        v
Generate report + source links + QA record
        |
        v
Human approval
        |
        v
Approved reusable lesson -> KMH Knowledge Base
```

**Hard rule:** No item enters approved Production Memory solely because an agent generated it. It must pass QA and the configured human-approval gate.

## 3. Input contract

Required:
- `Correlation_ID`: stable ID carried across all stages, logs, QA, and review.
- `source_text`: the exact user-provided text or a clearly identified excerpt.
- `task_mode`: `literary_analysis`, `argument_review`, or `teaching_example`.

Optional:
- `language`
- `context_notes`
- `known_source`
- `requested_output_format`

Preserve original wording for quoted evidence. If the input is Burmese, do not silently replace its meaning with an English paraphrase.

## 4. Critical Thinking Agent — task contract

For each candidate reasoning issue, return:
- `claim_id`
- `exact_quote`
- `speaker_or_character` (if identifiable)
- `claim`
- `premises`
- `conclusion`
- `candidate_label`
- `why_it_may_fit`
- `what_evidence_is_missing`
- `alternative_interpretation`
- `confidence` (`low`, `medium`, `high`)

The agent must:
1. Separate the speaker's claim from the analyst's interpretation.
2. Explain the reasoning pattern, not merely name a fallacy.
3. Consider whether the conclusion could still be true for other reasons.
4. Avoid inferring a person's entire character from one argument.
5. Flag factual or medical claims for separate verification rather than treating them as established facts.
6. Preserve the distinction between literary irony and evidence about real human behavior.

## 5. QA Agent — independent acceptance rules

QA returns `PASS`, `REWORK`, or `HUMAN_REVIEW`.

### PASS only if
- Every fallacy label is tied to an exact quote and a clear explanation.
- The explanation demonstrates the mismatch between premises and conclusion, or another precise reasoning defect.
- Uncertainty and plausible alternative readings are disclosed.
- Factual claims are not presented as verified when only the supplied story supports them.
- Emotional language is not automatically labeled a fallacy; the argument's relevance to the conclusion is assessed.
- The report respects human autonomy and does not frame Ratana as property, a prize, or a person who owes romance in exchange for instruction.
- The report contains no unsupported psychological diagnosis.

### REWORK if
- A quote is missing, the reasoning is misrepresented, the fallacy label is weak, or the explanation is too generic.
- A literary example is repeated as factual advice without qualification.
- A response confuses disagreement with irrationality.

### HUMAN_REVIEW if
- Two labels remain plausible and materially change the interpretation.
- A high-impact factual or health-related assertion needs a qualified source.
- The output would be used to judge a real person's mental state, consent, safety, or relationship decision.
- Critical Thinking Agent and QA Agent disagree after one bounded revision.

## 6. Case-specific QA notes

Using the supplied retelling of Max Shulman's “Love Is a Fallacy”:

- **Thihanra's central error:** He assumes intelligence and logical vocabulary entitle him to plan, train, or control Ratana's preferences. This is an ethical and interpersonal failure, not just a formal fallacy.
- **Ratana's agency:** Her choice is her own. The jacket is the comic twist; it should not be interpreted as proof that material possessions are the only basis of love in real relationships.
- **Fallacy labels need verification:** Do not automatically accept the story's labels when characters apply them. For example, calling a statement “counterfactual” does not by itself prove it is a counterfactual fallacy. Check the actual inference.
- **Appeal to pity:** An appeal to hardship is fallacious when it substitutes for relevant evidence in a context where evidence is requested; a hardship claim is not inherently irrelevant or dishonest.
- **False analogy:** Similarity between professions or situations must be relevant to the specific conclusion, not merely superficial.
- **Post hoc / false cause:** Sequence or correlation alone does not establish causation.
- **Health claims:** The story's exercise example is only an illustration. Do not reuse it as medical advice; individual exercise guidance depends on health status and qualified clinical advice.

## 7. Output schema

Recommended machine-readable record:

```json
{
  "workflow_id": "KMH-WF-CRIT-QA-001",
  "correlation_id": "required-stable-id",
  "source_ref": "page-or-file-url",
  "task_mode": "literary_analysis",
  "findings": [
    {
      "claim_id": "CLM-001",
      "exact_quote": "verbatim excerpt",
      "candidate_label": "hasty_generalization",
      "reasoning_explanation": "why the inference is unsupported",
      "confidence": "medium",
      "qa_status": "PASS",
      "qa_note": "quote and label checked"
    }
  ],
  "overall_qa": "REWORK",
  "human_review_required": true,
  "approval_status": "PENDING"
}
```

This is a contract example, not evidence that a runtime integration is already producing this JSON.

## 8. Logging and evidence requirements

Each stage must record:
- `Correlation_ID`
- workflow and prompt version
- input/source reference
- agent output reference
- QA result and reasons
- revision count
- human reviewer decision
- timestamp and execution status

Do not log secrets or unnecessary personal data. Keep source quotations limited to what is needed for traceability.

## 9. Minimum evaluation set

Before runtime promotion, test at least these cases:
1. Clear hasty generalization.
2. Clear post hoc reasoning.
3. Appeal to pity that substitutes for requested evidence.
4. Emotional statement that is relevant context, not automatically a fallacy.
5. A superficially similar analogy with a material difference.
6. A case where the correct result is “insufficient evidence”.
7. A dialogue where a character applies the wrong fallacy label.
8. A relationship statement requiring consent/autonomy-sensitive wording.
9. Burmese input with an English report, checking that meaning is preserved.
10. Conflicting agent outputs that must route to human review.

Track per-case label accuracy, quote fidelity, unsupported-claim rate, appropriate uncertainty, QA false-pass rate, and human-review routing. Set acceptance thresholds before testing; do not claim quality from an unrun test set.

## 10. Build → Connect → Run → Verify gate

- **BUILD:** This contract and the test cases are documented.
- **CONNECT:** Pending. Connect the orchestrator to source retrieval, agent execution, execution log, QA record, and approved Knowledge Base.
- **RUN:** Pending. Execute a real run with a stable `Correlation_ID`.
- **VERIFY:** Pending. Fetch the output and logs, check the QA gate, and confirm that a failed or unapproved item cannot enter approved memory.

### Promotion rule

Status may become `RUNTIME VERIFIED` only after a real execution record, corresponding QA evidence, and end-to-end traceability have been inspected. Until then, keep status at `BUILD SPEC — RUNTIME NOT VERIFIED`.

## 11. Next implementation step

Run one deliberately small dry-run record against the story, using a new `Correlation_ID`, then manually compare:
1. the exact source quote,
2. the Critical Thinking Agent's analysis,
3. the independent QA decision,
4. the execution log and final approval state.

Do not claim that this dry run has occurred until the evidence exists.


## Test Fixtures

- [KMH-TC-001 — Hasty Generalization (manual desk-check; runtime not run)](tests/KMH-TC-001-hasty-generalization.md)

The fixture defines expected outputs and acceptance checks. It is not evidence of live agent execution.
