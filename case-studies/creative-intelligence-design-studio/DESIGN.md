# KMH Creative Studio — Design Contract

**Version:** 1.0.0  
**Pilot:** My Little Creative World interactive creative studio  
**Status:** Draft baseline; human design approval required.

## Design intent

Create a warm, culturally respectful, child-friendly creative-learning interface that feels handcrafted rather than generic. The interface should give the character artwork and outfit details room to breathe. Prioritise clarity, trust, and playful exploration over decorative complexity.

## Visual language

- **Canvas:** warm off-white; keep large reading areas calm and low-glare.
- **Surfaces:** white or very light neutral cards with restrained borders.
- **Primary text:** deep navy for strong hierarchy and legibility.
- **Brand accent:** violet for primary actions and selected states.
- **Secondary accent:** muted gold for cultural detail and highlights; never use gold as small body text on white.
- **Success:** green only for verified success states; do not use green as a general decorative accent.
- Avoid default purple-gradient backgrounds, excessive glassmorphism, random floating cards, and decorative labels that do not convey information.

## Color tokens

Use `contracts/design-contract.json` as the machine-readable source of truth. Do not introduce raw hex colors in UI code when a semantic token exists.

## Typography

- Prefer system sans-serif for UI and Burmese/English mixed text.
- Use a clear three-level hierarchy: display/title, section heading, body/supporting.
- Body text must remain readable at mobile widths; do not shrink Burmese text to fit a fixed-width card.
- Use sentence case for controls. Avoid uppercase tracking for long Burmese or mixed-language labels.

## Layout and spacing

- Base spacing unit: 4 px.
- Use a consistent spacing scale; align related controls and group related content.
- Mobile-first layout. No horizontal page scrolling at 320 CSS px width.
- Touch targets: minimum 44 × 44 CSS px unless a platform-specific exception is documented.
- Keep character art, garment previews, and selection controls visually separate so the user can understand what is interactive.

## Components and states

Every interactive component must define default, hover/focus, pressed, selected, disabled, loading, and error states where applicable.

- **Primary button:** brand violet with white label; visible keyboard focus.
- **Secondary button:** neutral surface with clear border and navy label.
- **Outfit card:** preview, outfit name, selection status, and one clear action; selection must not depend on color alone.
- **Character preview:** preserve the approved identity asset; outfit overlays must not alter protected face/hair regions.
- **Toast/status:** announce meaningful state changes in text, not color alone.

## Motion

- Motion must communicate cause and effect: selection, drag, confirmation, loading, or feedback.
- Respect reduced-motion preferences.
- Avoid looping ambient motion that competes with learning content.
- Motion timing, easing, and choreography require interaction review; do not treat a motion skill's suggestion as automatic approval.

## Accessibility and localization

- Text contrast target: WCAG AA 4.5:1 for normal text and 3:1 for large text and meaningful non-text UI boundaries.
- Every action must be keyboard reachable and have an accessible name.
- Do not convey success, error, selection, or status by color alone.
- Support Burmese and English without clipping; test actual Myanmar font rendering, line-height, wrapping, and focus order.
- Provide alt text or an equivalent text description for informative illustrations.

## Cultural and child-safety constraints

- Preserve approved Myanmar cultural references and garment motifs; do not invent authenticity claims.
- Do not collect a child's full name, precise location, school, contact details, face image, or other unnecessary personal data in the pilot.
- Do not place analytics, advertising, tracking pixels, or third-party media upload in the prototype without a separately approved privacy review.

## QA expectations

A design is not accepted because it looks polished in a screenshot. Verify responsive layout, keyboard use, visible focus, text scaling, color contrast, meaningful interaction states, asset identity preservation, and evidence traceability. See `docs/phase-01-acceptance.md`.
