# Receipt: voice to SolidWorks prototype

Date: 2026-10-11
Author: H (Wahina Hlulani Njoku), with Claude as development partner
Branch: `prototype/voice-solidworks-pipeline`
Environment: H's Windows laptop, SOLIDWORKS Design Standard 2026 SP3.2 (Academic), Python 3.13

## Scope note: this conflicts with the truth lock

This prototype does **not** follow `docs/MVP_TRUTH_LOCK.md` as written, and this
receipt does not change the truth lock. Robyn owns that decision.

| Truth lock says | Prototype does | Why |
|---|---|---|
| Local planner, no hosted inference for normal operation | Cloud brain on Groq (`openai/gpt-oss-120b`) | H and Robyn agreed (early Sept) that cloud is the primary mode, with local as an opt-in fallback, because capable local models need hardware most students lack |
| Canonical intent JSON (`mode`, `problem`, `missing_requirements`, ...) | `MacroAction` schema (batched tool actions + teaching + verification fields) | Built for executing visible tool actions; it does not yet carry the brief/clarification fields |
| POC-1 is the input-to-brief loop; SolidWorks comes later | Went straight to voice + SolidWorks execution | Build-order choice made outside the repo |
| Changes one known parameter in a prepared test part | Creates new geometry from scratch | Exploratory |

Decision needed from Robyn + H: update the truth lock to match the agreed direction,
or bring the prototype back in line with it.

## Files changed

- `prototype/` (new): six Python files, `requirements.txt`, `README.md`
- `docs/receipts/2026-10-11-voice-solidworks-prototype.md` (this file)
- `NOW.md` (current-state update)
- `.gitignore` (new)

## Proof observed on H's machine

1. **Brain benchmark** (`ayakha_brain_benchmark.py`): Groq returned 4/4 schema-valid
   `MacroAction` objects at about 2 s average, including a "take over and demonstrate"
   case. Gemini could not be tested: new `AQ.` API keys return
   401 `ACCESS_TOKEN_TYPE_UNSUPPORTED` (Google-side issue). Narrow test: 4 prompts only.
2. **Voice loop**: SpeechRecognition (Google free recognizer) transcribes spoken
   requests; pyttsx3 speaks narration with a printed caption. Pause threshold tuned
   after the first test cut speech off.
3. **SolidWorks execution**: after fixing a COM `Type mismatch` (arg 8 of
   `SelectByID2` needed a typed null VARIANT), a spoken "M15 bolt and nut" request
   produced three real Boss-Extrude features in a live part.
   **The geometry was wrong**: head and shaft fused into one overlapping body.

## Built but not yet tested live

- Coaxial positioning via offset reference planes (`offset_mm` on `new_sketch`).
  Meant to fix the fused-bolt defect. Needs its own regression run on the bolt case.
- Learning ledger inside a real SolidWorks session (only tested in a sandbox
  against real `MacroAction` objects).
- Auto-creation of a new part document, visible step pacing (0.8 s + redraw).
- Canva driver (Playwright). Written without access to canva.com; selectors are guesses.
  Canva's Apps SDK should be evaluated before debugging this.
- `inspect_solidworks_ui.py`: not run yet.

## Known defects and uncertainty

- **Ledger verification is not real verification.** `verified=True` is recorded when
  the COM check runs without throwing, not when geometry is confirmed correct.
- SolidWorks changes are made through COM API calls, not visible UI clicks. Whether
  real clicks are required (2 Sept decision) or visible paced COM is enough is an
  open product question; `inspect_solidworks_ui.py` gathers evidence for it.
- `add_dimension` and `fillet` are not implemented.
- No observer of the student's own actions, so the ledger can never mark a skill
  as "learned".
- No automated tests. No student has used it.

## Next proof actions

1. Regression run A: rectangle 100x50, extrude 10 (baseline + ledger in a live session).
2. Regression run B: the M15 bolt case (does the coaxial fix work?).
3. Run `inspect_solidworks_ui.py` and record which toolbar controls are exposed.
4. Robyn + H decide the truth-lock conflict above.
5. Two exploratory sessions with CPUT students.
