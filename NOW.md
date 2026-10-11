# Ayakha Current State

Updated: 2026-10-11
Repository: `Kopano-Labs/ayakha-ai`
Branch: `main`
State: POC-0 truth lock seeded; POC-1 is open for implementation. A separate exploratory prototype exists (see below).

## Exploratory prototype (added 2026-10-11)

H built a voice to SolidWorks prototype on his machine (Sept–Oct 2026), now in
`prototype/` on branch `prototype/voice-solidworks-pipeline`. It uses a cloud brain
(Groq), which conflicts with the truth lock's local-inference rule. The truth lock
has **not** been changed; Robyn and H need to decide. Full evidence, defects and
next actions: `docs/receipts/2026-10-11-voice-solidworks-prototype.md`.

## Canonical product state

- Product: Ayakha
- Everyday face/persona: Aya
- Core: local-first multimodal design-thinking desktop companion
- MVP proof tools: Canva + SolidWorks
- Development lane: Windows-first for the SolidWorks adapter; cross-platform core and packaging

## What is proven

- The pitch has been redesigned around Aya as the canonical simple identity and Ayakha as the broader platform.
- The repository was empty before this truth-lock seed.
- MVP scope and acceptance criteria are now recorded in `docs/MVP_TRUTH_LOCK.md`.
- Agent continuity rules are recorded in `.github/copilot-instructions.md`.
- GitHub issue #1 records the POC-1 acceptance criteria: https://github.com/RobynAwesome/ayakha-ai/issues/1

## Current implementation status

Not started:

- desktop shell;
- local STT/planner/vision/TTS loop;
- intent JSON contract implementation;
- Canva connector;
- SolidWorks connector;
- local ledger;
- packaging and demo evidence.

## Next action

Implement POC-1: the local Aya input-to-design-brief loop (issue #1).

POC-1 must provide:

1. a launchable desktop shell or local development shell;
2. text input fallback;
3. a local planner adapter returning the canonical intent JSON;
4. clarification questions for missing requirements;
5. a rendered design brief;
6. a test fixture for the Cars4Mars motor-mount request.

Voice, visual input and TTS remain interfaces in POC-1 if the local hardware/model environment is not ready; the acceptance contract must not be weakened.

## Required receipt for the next change

Record:

- files changed;
- install/run commands;
- test command and result;
- one captured intent JSON;
- one captured clarification response;
- remaining model or hardware constraints;
- next proof action.

## Do not do yet

Do not begin with:

- a marketing website;
- a web-only application;
- full printer control;
- Blender or game-asset generation;
- cloud collaboration;
- autonomous external actions.

The next proof is local understanding, not feature breadth.
