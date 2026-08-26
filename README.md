# Ayakha / Aya

Ayakha is a local-first, multimodal design-thinking desktop companion for students and makers.

Aya is the canonical everyday face of the product: the name, icon, voice and patient guide a learner meets. Ayakha is the broader system that helps a person move from an idea to a clear brief, an editable artifact and a testable next step.

## MVP sentence

> A student can speak, type, sketch or show a design intention; Aya runs locally, clarifies what is missing, creates an explainable design brief, and helps the student make one approved change in Canva and one approved change in SolidWorks.

## MVP truth lock

The first proof is intentionally narrow:

- One desktop application with a local Aya runtime.
- Local speech-to-text, planning/reasoning, visual-input handling, text-to-speech and a local design ledger.
- Canva remains a connected web-based visual-design tool.
- SolidWorks remains the connected engineering/CAD tool.
- The core runtime is cross-platform; the SolidWorks adapter is a Windows lane for the MVP.
- External-tool actions are visible, reversible where possible and require explicit student approval.
- Aya explains assumptions and uncertainty instead of inventing missing requirements.

The MVP is a desktop product, not a web application. Platform-appropriate packaging is expected: Windows installer/.exe, Linux package and macOS app bundle.

## First proof case

Use one authentic Cars4Mars rover component as the shared test case:

- Engineering artifact: a known test motor mount, sensor bracket or similar parametric part in SolidWorks.
- Communication artifact: a one-page visual design brief in Canva.
- Starting input: a student voice request plus an optional sketch or reference image.
- Proof: the same intent becomes a structured brief, a visible Canva result and one safe, reversible SolidWorks edit.

The exact dimensions, material and motor specification must be supplied by the student or team. Aya must ask when they are missing.

## Product boundary

### In the MVP

- Aya desktop shell and local runtime status.
- Voice input with text fallback.
- One visual-input path for a sketch or reference image.
- Structured intent and design-brief generation.
- Clarifying questions and engineering-communication coaching.
- One Canva proof flow.
- One SolidWorks proof flow.
- Confirmation gates, undo/version evidence and local ledger entries.
- A Windows-first demonstration with a cross-platform core.

### After the MVP

- Direct 3D-printer control and slicer orchestration.
- Full generative CAD and automatic manufacturing.
- Blender, 2.5D/3D animation, game assets and keyframe generation.
- Open-source collaboration, forks, sharing and hosted workspaces.
- Mobile/web clients and autonomous external actions.

These are valid Ayakha expansion paths. They are not allowed to dilute the first proof.

## Canonical execution order

1. Read `NOW.md` and `docs/MVP_TRUTH_LOCK.md`.
2. Build the local Aya input-to-brief loop.
3. Add the Canva connector.
4. Add the SolidWorks connector.
5. Add approval, ledger, verification and packaging evidence.
6. Only then expand the creative lanes.

## Repository continuity

Every agent or contributor—including GitHub Copilot, Claude, Codex and human contributors—must recover the current state before acting:

- `NOW.md` is the volatile current-state receipt.
- `docs/MVP_TRUTH_LOCK.md` is the scope and acceptance authority.
- Pull requests must state the proof they add, the test run, and any remaining uncertainty.
- New capability must be proposed in an issue before it becomes implementation scope.

## Brand note

Aya is the canonical simple sense used in the UI, documents and social identity. Ayakha is the broader platform and future design world. The Xhosa-rooted identity should be reviewed with fluent isiXhosa speakers before formal brand lock.
