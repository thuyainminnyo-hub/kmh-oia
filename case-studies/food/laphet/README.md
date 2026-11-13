# KMH Laphet Scientific + Cultural Pilot

- Pilot ID: \`KMH-LAPHET-001\`
- Pilot type: Scientific + Cultural End-to-End
- Owner decision: Laphet selected as first pilot; no new architecture domains during this pilot.
- Current status: **HOLD — Gate 0 not passed**
- Tracking: [GitHub issue #226](https://github.com/thuyainminnyo-hub/kmh-oia/issues/226)
- Source of truth: [Notion execution record](https://app.notion.com/p/417fd51bf57581e59eb3df4464370f28)

## Purpose

Produce one accurate, traceable, community-authorized Laphet heritage record. Reuse existing KMH/OIA evidence, access, review and publication controls. This directory is a pilot package, not a new platform or subsystem.

## Research baseline

### Laphet microbiology (2020)

Bo Bo, Seul-Ah Kim and Nam Soo Han studied 14 Laphet products collected from different locations in Myanmar using culture-dependent and culture-independent methods. They reported Lactobacillus and Acetobacter as abundant bacteria and Candida, Pichia, Cyberlindnera and Debaryomyces as abundant yeasts. The article reports pH values from 4.53 to 6.91 and detected Enterococci in 10 of 14 samples.

- [PubMed record](https://pubmed.ncbi.nlm.nih.gov/31986350/)
- [Elsevier article / DOI 10.1016/j.ijfoodmicro.2020.108508](https://www.sciencedirect.com/science/article/pii/S0168160520300027)

**Limits:** 14 samples are not a representative national survey. The study is not a process specification, food-safety certification, or basis for health claims. pH alone cannot establish safety.

### Heritage and nomination context

Myanmar's Ministry of Foreign Affairs reported on 18 June 2026 that Myanmar Laphet (Fermented Tea Leaves) Culture had been submitted for the 2027 UNESCO cycle.

- [Myanmar MOFA — 18 June 2026](https://www.mofa.gov.mm/en/ambassador-charge-daffaires-attends-the-11th-session-of-the-general-assembly-of-the-states-parties-to-the-2003-convention-for-the-safeguarding-of-the-intangible-cultural-heritage18-6-2026-paris/)

This is a government-reported submission status, not UNESCO inscription and not blanket consent for KMH documentation.

## Reused existing KMH/OIA boundaries

- Existing repository trace and evidence concepts: use; do not create a parallel event platform.
- Existing authorization/security boundaries: preserve; do not add unrestricted tool execution.
- Existing test command: \`python -m unittest discover -s tests -v\`.
- Pilot-specific code in \`src/laphet_pilot.py\` is a fail-closed publication gate validator only. It does not collect, store, publish, or certify any data.

## Gate sequence

| Gate | Purpose | Exit evidence |
|---|---|---|
| G0 | Readiness and willing partner | Named accountable partner/contact route and safe scope note |
| G1 | Consent and rights | Ongoing, scope-specific consent and authority evidence |
| G2 | Evidence intake | Permitted claims and evidence with provenance |
| G3 | Cultural review | Community-appointed review and corrections |
| G4 | Scientific review | Qualified interpretation of studies and any approved tests |
| G5 | Independent QA | No unresolved critical defects |
| G6 | Community approval | Exact version/hash approved for channels and languages |
| G7 | Publication | Released artifact, location and timestamp recorded |
| G8 | Benefit and review | Agreed benefits and feedback tracked |

Missing evidence means HOLD. Do not infer consent or approval.

## Consent and data handling

Separate permission is required for interviews/oral histories, naming/anonymous attribution, photo/video/audio, recipe/process documentation, research access, public publication/translation, commercial reuse, retention and withdrawal. Community consent does not replace individual contributor, producer, site, research ethics, sample, regulatory or applicable ABS permissions.

Do not collect or upload sacred, restricted or confidential knowledge merely to classify it. Use the minimum metadata necessary to enforce the community's access decision.

## Food science and safety

New sampling requires permissions, an approved protocol, suitable chain of custody, qualified laboratory and methods, and relevant legal/ethics approvals. Report results only for the sampled batch and methods. Do not assert that Laphet is safe based on the 2020 study or a pH reading. Do not publish health/probiotic claims in this pilot.

## Publication rule

Only publish a version that has:
- active and scope-matched consent;
- public access classification for the record and every public claim;
- evidence and publication permission for every public claim/media item;
- cultural review and independent QA PASS;
- explicit community approval of the exact artifact hash, languages and channels;
- a correction, withdrawal and takedown route.

The validator rejects unsupported/disputed claims, missing approvals, private evidence used in public claims, unapproved attribution, unmatched artifact hashes, and unsubstantiated health or food-safety claims.

## Status at bootstrap

No community partner, consent, recipe fieldwork, producer record, laboratory sample/result, independent review, community approval, publication artifact or benefit delivery is asserted by adding this package. Initial state remains **HOLD — G0**.
