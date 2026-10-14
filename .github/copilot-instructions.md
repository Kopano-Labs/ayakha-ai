# Ayakha repository instructions

Before changing code, read:

1. `AGENTS.md` (repository-wide instructions)
2. `NOW.md`
3. `docs/MVP_TRUTH_LOCK.md` and `docs/NEXT_STEPS.md`
4. the active issue or pull-request acceptance criteria

## Merged baseline

As verified on 2026-10-14, the repository is `RobynAwesome/ayakha-ai`. PR #4 and
PR #3 are merged; `main` at `8d15cd7` passed hosted Ubuntu and Windows CI with
57 tests and compilation on each platform. Exact links are in `NOW.md`.
The earlier billing lock and PR stack are historical. Re-query GitHub before
making current-state claims and start new work from current `main`.

The prototype uses connected Groq/Google flows and a different action contract.
The merges do not satisfy the canonical local-inference MVP. POC-1 issue #1
remains the next canonical implementation; live SolidWorks proof is a separate
next step. Keep mandatory local approval, disposable-part ownership checks and
disabled capabilities intact. Feature presence is not verified geometry.

## Product language

- Aya is the canonical everyday mascot/persona.
- Ayakha is the broader platform.
- The MVP is a local-first desktop application.
- Canva remains a connected web-based proof tool.
- SolidWorks remains a connected engineering proof tool and is a Windows-specific MVP adapter.
- The local brain must clarify missing requirements and show uncertainty.

## Scope discipline

Build the vertical slice in this order:

1. local input-to-design-brief loop;
2. Canva proof connection;
3. SolidWorks proof connection;
4. approval gates, ledger, tests and packaging.

Do not pull printer control, Blender, game assets, collaboration, cloud workspaces or full generative CAD into the MVP without a documented scope change.

## Implementation rules

- Prefer small interfaces around STT, planner/model, vision, TTS and tool connectors.
- Keep local inference separate from external-tool adapters.
- Make external actions explicit and confirmable.
- Never fabricate dimensions, materials, tolerances, tool state or test results.
- Every pull request must report tests, proof and remaining uncertainty.
