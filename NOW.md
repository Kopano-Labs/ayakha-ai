# Ayakha Current State

Updated: 2026-08-26
Repository: `RobynAwesome/ayakha-ai`
Branch: `main`
State: POC-0 truth lock seeded; implementation has not started.

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

Implement POC-1: the local Aya input-to-design-brief loop.

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
