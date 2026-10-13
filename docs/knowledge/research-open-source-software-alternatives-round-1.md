# KMH Research Register — Open-Source Software Alternatives (Round 1)

**Register ID:** KMH-RESEARCH-OSS-001  
**Date:** 2026-10-13  
**Status:** Candidate shortlist verified against GitHub repository search; suitability and license obligations still require project-specific review.  
**Purpose:** Identify mature, real open-source alternatives for controlled evaluation. This list is *not* a claim that these are the specific early-stage AI-vibe-coded clones mentioned in the original post.

## Candidate shortlist

| Domain | Candidate | Official repository | Initial use case | Evaluation status |
|---|---|---|---|---|
| Digital painting / creative | Krita | https://github.com/KDE/krita | Illustration, painting, concept art | Candidate; run workflow tests |
| Raster image editing | GIMP | https://github.com/GNOME/gimp | Image editing and compositing | Candidate; run workflow tests |
| Vector graphics | Inkscape | https://github.com/inkscape/inkscape | SVG, logos, vector illustration | Candidate; run workflow tests |
| Office suite | LibreOffice | https://github.com/LibreOffice/core | Documents, spreadsheets, presentations | Candidate; test OOXML/ODF compatibility |
| UI design / prototyping | Penpot | https://github.com/penpot/penpot | Web-based interface design and prototyping | Candidate; test self-hosting and export |
| Parametric CAD | FreeCAD | https://github.com/FreeCAD/FreeCAD | Parametric 3D design and engineering workflows | Candidate; test target formats and constraints |

## Evidence notes

- The repository search returned the official-looking upstream repositories listed above, with non-archived status in the returned metadata at the time of search.
- GitHub repository existence does not by itself prove release quality, security, license compatibility, or fit for KMH's workflow.
- A repository's license file may be named differently from `COPYING`; confirm the exact LICENSE / COPYING / license metadata for the default branch before integration.
- These are established open-source alternatives, not evidence of the specific new AI-generated clones discussed in the source commentary.
- No performance benchmark has been run as part of this research round.

## Gate 0 — before hands-on use

For each candidate, record:
1. Exact upstream repository and default branch.
2. License file and any bundled third-party licenses.
3. Latest stable release and release date.
4. Security advisories and dependency posture.
5. Installation path, platform support, and minimum hardware.
6. A small representative task and measurable acceptance criteria.
7. File import/export compatibility and rollback strategy.

## Proposed pilot tasks

- **Krita / GIMP:** edit a non-sensitive sample image; export to PNG and a layered format where applicable; check fidelity and reproducibility.
- **Inkscape:** edit an SVG and export PDF/SVG; compare text, paths, and fonts.
- **LibreOffice:** open and round-trip a sample DOCX/XLSX/PPTX plus ODT/ODS/ODP; compare formatting and formulas.
- **Penpot:** build a small UI mockup; test export, team access, and self-hosting requirements.
- **FreeCAD:** model a simple parametric part; reopen the file and verify dimensions/constraints and export format.

## Scoring rubric (0–2 per criterion)

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Task fit | Fails | Partial | Meets acceptance criteria |
| Stability | Crashes / data loss | Minor defects | Repeatable |
| Compatibility | Critical mismatch | Workarounds needed | Required round-trip works |
| License clarity | Unclear / unacceptable | Review pending | Approved for intended use |
| Security | Critical concern | Needs mitigation | Review passed |
| Maintenance | Abandoned / unresponsive | Mixed signals | Maintained and documented |
| Total cost | Not viable | Uncertain | Viable for target workflow |

**Adoption rule:** Unknown is not pass. Do not adopt into production until required license, security, task-fit, and compatibility gates pass.

## Next action

Obtain the original post or names/links of the alleged new AI-vibe-coded alternatives. Compare those projects separately against this mature baseline; do not conflate “open-source alternative exists” with “new clone has reached product parity.”
