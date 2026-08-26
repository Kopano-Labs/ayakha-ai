# Ayakha repository instructions

Before changing code, read:

1. `NOW.md`
2. `docs/MVP_TRUTH_LOCK.md`
3. the active issue or pull-request acceptance criteria

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
