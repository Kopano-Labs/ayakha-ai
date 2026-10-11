# Aya prototype: voice to SolidWorks pipeline

Exploratory prototype built by H with Claude between September and October 2026.
It runs on H's Windows machine. It is **not** the MVP described in
`docs/MVP_TRUTH_LOCK.md`; see the receipt in `docs/receipts/` for how it differs.

## What it does

Student speaks (or types) a request, a cloud model (Groq, `openai/gpt-oss-120b`)
returns a structured `MacroAction`, the student approves it, and the local driver
executes it in SolidWorks, pausing between steps so the build is visible. A local
ledger records who did each step (student or Aya).

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
pip install -r requirements.txt
playwright install chromium
$env:GROQ_API_KEY="your_key"
python ayakha_local_driver.py
```

Never commit API keys. Keep them in environment variables.
