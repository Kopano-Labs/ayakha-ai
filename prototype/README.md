# Aya prototype: voice to SolidWorks pipeline

Exploratory prototype built by H with Claude between September and October 2026.
It runs on H's Windows machine. It is **not** the MVP described in
`docs/MVP_TRUTH_LOCK.md`; see the receipt in `docs/receipts/` for how it differs.

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
| `ayakha_local_driver.py` | Entry point: voice loop, Groq call, approval gate, SolidWorks/Canva dispatch |
| `ayakha_ledger.py` | SQLite learning ledger + lecturer-readable markdown report |
| `ayakha_canva_driver.py` | Playwright browser automation for Canva (untested) |
| `ayakha_brain_benchmark.py` | Groq vs Gemini benchmark on MacroAction validity |
| `inspect_solidworks_ui.py` | Read-only dump of SolidWorks' UI Automation tree |

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

```powershell
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest prototype/tests -q
```

They use fake drivers to check confirmation, policy, document ownership,
interruption, verification and ledger logic. CI runs them on Windows and Linux
without cloud keys or SolidWorks. Real COM identity and geometry behaviour still
requires a live SolidWorks run.

## Local development to GitHub

The working folder is `C:\Users\rkhol\ayakha-ai`. `origin` is
`https://github.com/Kopano-Labs/ayakha-ai.git`; local `fix/ledger-verification`
tracks the existing PR #4 branch. Check status, fetch, inspect incoming changes,
edit and test locally, commit the intended files, then push this branch.
PR #4 targets `prototype/voice-solidworks-pipeline` (PR #3), which targets `main`.
Preserve that stack. Rebase only when divergence warrants it; do not force-push
to refresh a date. Review #4, integrate it into #3, then revalidate #3's exact head
before any authorized merge to `main`.
