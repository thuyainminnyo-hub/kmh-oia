# Case Study: Universal AI Filmmaking Master Prompt — KMH Production System Review v1.0

## Evidence boundary
This review is based only on the prompt text supplied by the user. No benchmark run, generated film, model-specific test, or external validation was provided. This is a prompt/workflow review, not proof that one prompt can automatically produce a finished film.

## Executive verdict
**ACCEPT WITH REFINEMENTS as a reusable production-planning template.**
The prompt is useful because it decomposes filmmaking into story analysis, character/environment references, scenes, shots, image/video prompts, sound, continuity, editing and QA. Its main weakness is that it treats these outputs as if they can be reliably produced in one pass and transferred unchanged across many tools. KMH should convert it into a gated, versioned pipeline.

## Strong parts
- Story-first workflow and preservation of key events/ending.
- Character identity and wardrobe continuity intent.
- Environment references and shot-by-shot breakdown.
- Separate image prompts and video prompts.
- Dialogue, sound design, edit plan and export requirements.
- Explicit continuity checklist and production deliverables.

## Main limitations and corrections

### 1. One giant prompt can exceed context and produce uneven outputs
The output may be truncated, become repetitive, or skip later deliverables. Generate one phase at a time, save each approved artifact, and pass forward only versioned references and decisions.

### 2. “Character Identity Lock” is a process, not a guarantee
Text instructions alone cannot ensure consistent faces, costumes, proportions or props across image/video models. Use approved reference images, fixed descriptions, seed/reference controls where available, and a visual QA gate. Record intentional changes as separate approved versions.

### 3. Tool-neutral prompts are not automatically portable
Each image/video tool has different duration limits, reference-image behavior, camera controls, aspect ratios, model versions and prompt syntax. Keep a tool-neutral creative brief, then generate a tool-specific prompt adapter for the selected model. Validate current tool limits in its UI/docs before production.

### 4. Shot durations need to be driven by dialogue and action
A list of estimated durations does not ensure a film runtime. Calculate dialogue duration from word count and delivery pace, then add pauses/action beats and transitions. Reconcile the shot timeline against target runtime before generation.

### 5. Audio generation and lip-sync are separate gates
Voice-over, dialogue, ambience, effects and music may require separate generation and synchronization. Specify speaker IDs, language, pronunciation, delivery, timecodes, rights/consent for voice likeness, and whether lip-sync is required. Do not assume every video model will generate production-ready dialogue/audio.

### 6. Continuity needs machine-readable records
Create a canonical Character Bible, Location Bible, Prop Register, Scene Ledger and Shot Ledger. Each shot should reference IDs, approved versions, screen direction, time of day, lighting state and start/end state. Avoid copying long descriptions inconsistently by hand.

### 7. Editing instructions are not a rendered final film
The master prompt can propose an edit plan, but actual assembly requires generated media files, an editor/timeline, audio mix, subtitles, color matching, and final export checks. Do not label the film complete until the actual export is inspected.

### 8. Copyright, consent and safety checks are missing
Record source/story rights, image/reference permissions, voice consent, music/SFX licences, model/tool terms, disclosure needs and platform requirements. Avoid imitating a living artist’s exact style or cloning a person’s voice without permission.

## KMH recommended pipeline

### Gate 0 — Intake & brief
- Story source and rights
- Runtime, aspect ratio, target platform, language
- Genre, audience, style references and tool constraints
- Deliverable definition and budget/credit limit

**Exit:** brief approved; unresolved high-impact choices clarified.

### Gate 1 — Story lock
- Logline, synopsis, theme, dramatic beats
- Preserve essential events and ending
- Dialogue/voice-over draft and runtime estimate

**Exit:** story and script version approved.

### Gate 2 — Visual bible
- Character IDs and approved reference prompts/images
- Location IDs and environment references
- Prop/wardrobe variants and palette/lighting rules

**Exit:** references reviewed and locked.

### Gate 3 — Scene and shot plan
- Scene ledger and shot ledger
- Camera language, action beats, screen direction
- Duration, asset dependencies, dialogue/audio requirements

**Exit:** timeline fits target duration; continuity risks logged.

### Gate 4 — Asset generation
- Generate reference images first
- Generate shot keyframes and review them
- Generate short video clips using model-specific prompts
- Record model/version, prompt version, settings, cost and asset IDs

**Exit:** each asset has a QA status and provenance.

### Gate 5 — Audio
- Voice casting/consent, pronunciation, delivery
- Dialogue/VO, ambience, effects and music
- Synchronization and loudness review

**Exit:** audio approved and mapped to timeline.

### Gate 6 — Edit and finish
- Assemble clips, trims, transitions and sound
- Color/continuity matching, subtitles and titles
- Export to platform-specific settings

**Exit:** actual exported file reviewed.

### Gate 7 — Production QA and release
- Story accuracy and runtime
- Identity/wardrobe/location/prop continuity
- Visual artifacts, motion errors and audio sync
- Rights/licences, privacy, export integrity
- Human approval and delivery record

**Exit:** QA PASS + human approval + actual final file.

## Required canonical data objects
- PROJECT_BRIEF
- SCRIPT_LOCK
- CHARACTER_BIBLE
- LOCATION_BIBLE
- PROP_WARDROBE_REGISTER
- SCENE_LEDGER
- SHOT_LEDGER
- PROMPT_LIBRARY
- ASSET_MANIFEST
- AUDIO_CUE_SHEET
- EDIT_DECISION_LIST
- QA_REPORT
- FINAL_DELIVERY_RECORD

Every artifact should carry project ID, version, owner, status, dependencies and approval date. Never overwrite approved versions silently.

## Minimal shot record schema
- Project / scene / shot ID
- Story beat and purpose
- Duration target
- Character/location/prop IDs and approved versions
- Shot size, angle, movement and screen direction
- Start state and end state
- Image prompt + selected tool adapter
- Video prompt + model/version/settings
- Dialogue/audio cue IDs
- Asset paths and provenance
- QA issues and status

## Metrics for a pilot
- Percentage of planned shots successfully generated
- Character/wardrobe continuity pass rate
- Usable-clip rate after first generation
- Average generation attempts and credit cost per approved shot
- Timeline/runtime deviation
- Audio-sync defect count
- QA rework rate
- Final delivery completion rate

Do not invent results; collect them during a real pilot.

## Recommended pilot
Run this workflow on one short 30–60 second film first. Generate and approve one character reference, one location reference, three storyboard keyframes and three short clips before expanding. This validates continuity and tool limits without spending the full production budget.

## Final decision
**ACCEPT WITH REFINEMENTS.** The supplied master prompt is a good high-level checklist, but KMH should operationalize it as a gated workflow with versioned bibles, shot/asset ledgers, tool-specific prompt adapters, QA evidence and human approvals. It does not by itself generate, assemble or verify a final film.
