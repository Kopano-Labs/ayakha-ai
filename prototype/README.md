# Aya prototype: voice to SolidWorks pipeline

Exploratory prototype built by H with Claude between September and October 2026.
It was developed on H's Windows machine and is now merged into `main` through
[PR #4](https://github.com/RobynAwesome/ayakha-ai/pull/4) and
[PR #3](https://github.com/RobynAwesome/ayakha-ai/pull/3). At merged commit
`8d15cd7`, hosted Ubuntu and Windows CI each passed **57 tests** and compilation:
[main run](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600).
The current safety baseline still needs a live SolidWorks run.

It is **not** the MVP described in [the truth lock](../docs/MVP_TRUTH_LOCK.md).
Read [NOW.md](../NOW.md) and [next steps](../docs/NEXT_STEPS.md) for current scope
and the next machine proof. Earlier reported runs remain in the dated receipts.

## What it does

Student speaks (or types) a request, a cloud model (Groq, `openai/gpt-oss-120b`)
returns a structured `MacroAction`, the student approves it, and the local driver
executes a locally allowed macro in SolidWorks via COM, pausing between steps.
Approval covers the displayed whole macro and is mandatory, regardless of model
output. A local ledger records attempts and attribution (student or Aya).

The connected prototype sends typed requests to Groq. Voice mode sends audio to
Google speech recognition and the transcript to Groq. Startup requires explicit
consent to those flows; use fictional demo data. This is separate from the
truth lock's planned local inference runtime.

## Execution boundary and recovery

- Only `new_sketch`, `draw_line`, `draw_rectangle`, `draw_circle` and `extrude`
  are enabled. The entire macro is validated before execution: at most 50
  actions, finite numeric values within 1000 mm and positive sizes/depths.
- Only exact `y` or `yes` authorizes. Ambiguous input, EOF or Ctrl+C cancels.
- Close existing SolidWorks documents first. After approval Aya creates an
  unsaved disposable part and checks its identity before each action. Switching,
  closing or saving that part blocks further execution; it never adopts a
  student's existing part. Identity checks use `ISldWorks.IsSame` with
  `swObjectSame=1`; unsupported identity results fail closed.
- Automatic saving, toolbar clicks, generic desktop control, Canva dispatch,
  feature selection, dimension and fillet actions are disabled. Canva source
  is preserved for a later independently reviewed connection.
- Ctrl+C aborts a running macro; there is no pause/resume or automated undo.
  Failure can leave partial geometry in the unsaved part. Inspect it, close it
  without saving, then restart. A failed driver cannot continue editing.
- Feature-tree comparison can detect missing features. Presence alone cannot
  prove size, placement, material or tolerances: the ledger records it as
  unverified. Only verified results count toward learning progress. Existing
  ledger entries are preserved; historical verification flags are not re-audited.

## Files

| File | Purpose |
|---|---|
| `macro_action_schema.py` | Pydantic contract between the brain and the local driver |
| `ayakha_local_driver.py` | Entry point: consent, voice/text loop, Groq call, approval gate and SolidWorks dispatch |
| `execution_policy.py` | Local action allowlist and full-plan parameter validation |
| `ayakha_ledger.py` | SQLite learning ledger + lecturer-readable markdown report |
| `ayakha_canva_driver.py` | Playwright browser automation for Canva (untested) |
| `ayakha_brain_benchmark.py` | Groq vs Gemini benchmark on MacroAction validity |
| `inspect_solidworks_ui.py` | Read-only dump of SolidWorks' UI Automation tree |
| `tests/` | Offline execution-safety, verification and ledger regressions |
| `requirements-test.txt` | Pinned offline test dependencies used by CI |

## Run (Windows, SolidWorks installed)

```powershell
cd C:\Users\rkhol\ayakha-ai
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements.txt
$env:GROQ_API_KEY="your_key"
.\.venv\Scripts\python.exe prototype/ayakha_local_driver.py
```

Never commit API keys. Keep them in environment variables.

## Tests (no SolidWorks needed)

Run from the repository root with Python 3.12; create `.venv` first if needed.

```powershell
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest prototype/tests -q
.\.venv\Scripts\python.exe -m compileall -q prototype
```

Linux equivalents:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r prototype/requirements-test.txt
.venv/bin/python -m pytest prototype/tests -q
.venv/bin/python -m compileall -q prototype
```

These commands validate the cross-platform Python logic. SolidWorks COM itself
requires Windows; passing Ubuntu CI does not establish a Linux CAD adapter.

They use fake drivers to check confirmation, policy, document ownership,
interruption, verification and ledger logic. CI runs them on Windows and Linux
without cloud keys or SolidWorks. Real COM identity and geometry behaviour still
requires a live SolidWorks run.

## Local development to GitHub

The working folder is `C:\Users\rkhol\ayakha-ai`. `origin` is
`https://github.com/RobynAwesome/ayakha-ai.git`. PR #4 was merged into the prototype
branch, then PR #3 into `main`; the former stack is history.

Check status, fetch and compare incoming changes while preserving unrelated work.
Start new work from current `main` on a scoped `codex/` branch; edit and test
locally, commit the intended files, then push for review. Rebase only when
divergence warrants it; do not force-push to refresh a date.

The next live session must measure the rectangle/extrude and M15 positioning
cases, exercise ownership/recovery and inspect the ledger. Follow
[NEXT_STEPS.md](../docs/NEXT_STEPS.md) for the receipt and acceptance boundaries.
