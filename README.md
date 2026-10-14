# Ayakha / Aya

Ayakha is a local-first, multimodal design-thinking desktop companion for students and makers.

Aya is the canonical everyday face of the product: the name, icon, voice and patient guide a learner meets. Ayakha is the broader system that helps a person move from an idea to a clear brief, an editable artifact and a testable next step.

## Current success and starting point

As verified on **2026-10-14**, the canonical repository is
[RobynAwesome/ayakha-ai](https://github.com/RobynAwesome/ayakha-ai), transferred
from Kopano-Labs with its history intact. [PR #4](https://github.com/RobynAwesome/ayakha-ai/pull/4)
and [PR #3](https://github.com/RobynAwesome/ayakha-ai/pull/3) are merged. The published
implementation baseline is `main` at `8d15cd7`.

**Hosted Ubuntu and Windows CI each passed 57 tests and compilation on that
merged commit.** [View the successful main run](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600).
The earlier billing blocker no longer prevents Actions execution in this repository.

The merged `prototype/` contains a connected voice/text-to-SolidWorks experiment,
local execution gates, a SQLite ledger and offline tests. It still uses Groq and
optional Google speech recognition; Canva execution is disabled and real CAD
geometry remains to be validated. The local-inference MVP below is the intended
product contract, not a claim that these PRs completed it.

| Read | Purpose |
|---|---|
| [NOW.md](NOW.md) | Current evidence, implementation inventory and remaining gaps |
| [AGENTS.md](AGENTS.md) | Entry instructions for every coding agent |
| [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) | Live SolidWorks proof, scope decision and POC-1 acceptance |
| [prototype/README.md](prototype/README.md) | Prototype setup, execution boundaries and recovery |
| [docs/README.md](docs/README.md) | Scope authority and dated evidence index |

## Start with offline checks

From the repository root, use Python 3.12. This exercises fake COM drivers and
temporary ledgers without SolidWorks, provider keys, a microphone or a browser.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest prototype/tests -q
.\.venv\Scripts\python.exe -m compileall -q prototype
```

For Linux commands or a Windows/SolidWorks live session, follow the
[prototype instructions](prototype/README.md). The next live proof is a measured
100x50x10 mm disposable part followed by the M15 positioning regression. The next
canonical implementation is [POC-1 issue #1](https://github.com/RobynAwesome/ayakha-ai/issues/1):
local input, clarification and an editable brief, with no external-tool execution.

## Run POC-1 locally

POC-1 now provides a connector-free local development shell. It uses a
deterministic, explainable planner until a separately scoped local-model adapter
is ready. It makes no network, Canva, SolidWorks, browser or device calls.

```powershell
.\.venv\Scripts\python.exe -m aya_runtime status
.\.venv\Scripts\python.exe -m aya_runtime brief --request "Aya, I need a motor mount for our Cars4Mars rover. It must fit the motor, survive vibration, stay within our printer volume and be easy for a student to explain."
.\.venv\Scripts\python.exe -m aya_runtime interactive
```

The `brief` and `interactive` commands print the canonical intent JSON and write
an editable local Markdown brief to `aya-workspace/design-brief.md` by default.
The checked-in [Cars4Mars fixture](fixtures/cars4mars_motor_mount.json) makes the
clarification case repeatable. Its missing requirements are intentional; Aya must
ask instead of inventing motor specifications.

## Intended MVP outcome

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

1. Read `AGENTS.md`, `NOW.md`, `docs/MVP_TRUTH_LOCK.md` and the active issue.
2. Build the local Aya input-to-brief loop.
3. Add the Canva connector.
4. Add the SolidWorks connector.
5. Add approval, ledger, verification and packaging evidence.
6. Only then expand the creative lanes.

## Repository continuity

Every agent or contributor—including GitHub Copilot, Claude, Codex and human contributors—must recover the current state before acting:

- `NOW.md` is the volatile current-state receipt.
- `AGENTS.md` applies repository-wide; `.github/copilot-instructions.md` points Copilot to the same guidance.
- `docs/NEXT_STEPS.md` sets out the next proof and implementation acceptance; dated receipts in `docs/receipts/` preserve earlier states.
- `docs/MVP_TRUTH_LOCK.md` is the scope and acceptance authority.
- Pull requests must state the proof they add, the test run, and any remaining uncertainty.
- New capability must be proposed in an issue before it becomes implementation scope.

Develop locally, then push scoped commits for review. The local working folder is
`C:\Users\rkhol\ayakha-ai`; `origin` is
`https://github.com/RobynAwesome/ayakha-ai.git`. Start new work from current `main`
on a `codex/` branch. PRs #3/#4 are merged history, not active development lanes.

## Brand note

Aya is the canonical simple sense used in the UI, documents and social identity. Ayakha is the broader platform and future design world. The Xhosa-rooted identity should be reviewed with fluent isiXhosa speakers before formal brand lock.
