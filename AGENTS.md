# Ayakha agent instructions

These instructions apply throughout this repository.

## Recover authority and current state

Before making changes, read:

1. [NOW.md](NOW.md) for the current verified baseline and next work.
2. [docs/MVP_TRUTH_LOCK.md](docs/MVP_TRUTH_LOCK.md) for scope and acceptance.
3. The active issue/PR criteria and [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md).
4. [prototype/README.md](prototype/README.md) before touching the prototype.

The canonical repository is `RobynAwesome/ayakha-ai`. PRs #4 and #3 are merged;
the published implementation baseline is `main` at `8d15cd7`, with hosted Ubuntu
and Windows CI passing 57 tests each. These are dated observations: re-query
GitHub before claiming current heads or checks. Older billing/stack receipts are
history, not instructions to revive old work.

## Product and evidence boundaries

- Aya is the everyday persona; Ayakha is the broader local-first desktop product.
- The merged `prototype/` uses Groq and optional Google STT. Local development
  does not make its inference local or satisfy the canonical MVP contract.
- Keep the truth lock active until Robyn and H document a scope decision. Do not
  silently promote the prototype or expand into printers, Blender, game assets,
  collaboration, a marketing site or a hosted application.
- Preserve mandatory local confirmation, whole-plan validation and unsaved-part
  ownership checks. Keep disabled capabilities disabled unless a separately
  scoped change supplies review, boundaries and tests.
- Feature presence alone is not correct geometry. Unknown or failed outcomes
  cannot establish learning progress. Do not invent requirements or test results.
- Distinguish source, offline tests, hosted CI, real-machine evidence and field
  evidence. CI does not establish live SolidWorks, deployment or MVP completion.

## Working method

- Inspect `git status`, the remote and branch before editing. Preserve unrelated
  local work; fetch and compare without resetting or overwriting it.
- Develop locally in `C:\Users\rkhol\ayakha-ai`, then push scoped changes. Start
  new work from current `main` on a `codex/` branch; do not continue merged #3/#4
  branches or rebase for cosmetic freshness.
- Read acceptance criteria before implementation. POC-1 issue #1 executes
  no Canva, SolidWorks or other external actions.
- Keep secrets in environment variables. Never commit keys, student data or
  credentials in receipts, remotes or command output.
- Use the pinned offline test dependencies in `prototype/requirements-test.txt`.
  Run relevant tests for code changes; for documentation-only changes, check
  links, commands, source consistency and `git diff --check`. Existing PR CI
  still validates the documentation branch without new test infrastructure.
- Update `NOW.md` when current status changes; append a dated receipt for exact
  evidence. Preserve earlier receipts and distinguish the documented baseline
  from an unmerged documentation update.

## Offline validation

From the repository root, with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest prototype/tests -q
.\.venv\Scripts\python.exe -m compileall -q prototype
```

Linux equivalents are in [prototype/README.md](prototype/README.md). Never run
live tool/provider scripts merely to validate a documentation change.
