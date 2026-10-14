# POC-1 local input-to-design-brief receipt

Observed: 2026-10-14 (Africa/Johannesburg)
Scope: source implementation and local offline validation
State: review pending; this receipt does not establish a merge, hosted-CI result,
desktop package, local-model inference, external-tool action, live CAD proof or
student-field validation.

## Source under review

- Repository: `RobynAwesome/ayakha-ai`.
- Base: `main` at `bd5778f7c41e66cb5ecfa65b50929823f2da494f`.
- Implementation commit: `ebc9fe774edebf87b4083b5922a9a7a3c910bce4`
  (`feat: add local Aya POC-1 brief loop`).
- Branch: `codex/poc1-local-aya-brief`.
- Governing issue: [#1](https://github.com/RobynAwesome/ayakha-ai/issues/1).
- Scope authority: [MVP truth lock](../MVP_TRUTH_LOCK.md).

## What this increment proves locally

`aya_runtime` supplies a local development shell with visible READY status, a
deterministic text planner, the canonical intent object, a clarification loop and
an editable Markdown brief. It has no provider, browser, Canva, SolidWorks,
device-control or operating-system automation dependency. Its intent explicitly
has `proposed_action: null` and `target_tool: null`.

The repeatable [Cars4Mars fixture](../../fixtures/cars4mars_motor_mount.json)
produces the [captured intent JSON](2026-10-14-poc1-cars4mars-intent.json).
It asks for motor dimensions, mounting interface and bolt pattern, material, load
and safety requirements, and printer build limits. This is the clarification
response for the seed request; it does not invent any motor specification.

## Files changed in the implementation commit

- `aya_runtime/`: typed canonical intent, deterministic planner, editable-brief
  renderer and `python -m aya_runtime` local development shell.
- `fixtures/cars4mars_motor_mount.json`: repeatable incomplete-request fixture.
- `prototype/tests/test_poc1_runtime.py`: canonical intent, completed brief,
  editable brief and subprocess shell tests.
- `.github/workflows/prototype-tests.yml`: compiles `aya_runtime` after the
  existing Ubuntu/Windows offline test command.
- `.gitignore`: excludes the local `aya-workspace/` output.
- `README.md`: documents safe local commands and the fixture.

## Commands and observations

```powershell
.\.venv\Scripts\python.exe -m aya_runtime status
.\.venv\Scripts\python.exe -m aya_runtime brief --request "Aya, I need a motor mount for our Cars4Mars rover. It must fit the motor, survive vibration, stay within our printer volume and be easy for a student to explain." --output .\aya-workspace\manual-smoke-brief.md
.\.venv\Scripts\python.exe -m pytest prototype\tests -q
.\.venv\Scripts\python.exe -m compileall -q prototype aya_runtime
git diff --check
```

Observed locally: the shell printed `Aya runtime: READY`, emitted the captured
intent and wrote an editable brief. The offline suite passed **61 tests in
3.49 seconds**; compilation and `git diff --check` passed. The manual output
path is ignored and is not part of this receipt.

## Remaining constraints and next proof

The planner is deterministic code, not the locally hosted planner/model adapter
called for by the broader MVP. Voice, vision, TTS, packaging, local ledger
integration, Canva and prepared-part SolidWorks editing remain outside this
increment. The next admissible action is review and hosted CI of this exact
branch; after merge, the next scoped product proof is the local model-adapter
decision or a separately authorized connector issue. No external action is
authorized or performed here.
