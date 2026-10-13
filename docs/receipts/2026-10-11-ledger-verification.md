# Receipt: real verification for the ledger

Date: 2026-10-11
Author: H, with Claude
Branch: `fix/ledger-verification` (stacked on `prototype/voice-solidworks-pipeline`, PR #3)

## Problem

Flagged by Forge in review: the ledger recorded `verified=True` whenever the
read-only COM check ran without throwing, not when the geometry actually appeared.
A step that silently produced nothing still counted as practice or as a
demonstration the student saw. Failed macros were not recorded at all.

## Change

- `SolidWorksDriver.feature_snapshot()` reads `(name, type)` for every feature.
- `execute_macro` snapshots the tree before and after each SolidWorks macro and
  calls `check_new_features`, which requires one `Extrusion` per `extrude` and a
  `ProfileFeature` for a standalone `new_sketch`. Result is `True`, `False`, or
  `None` when nothing in the macro shows up in the tree (e.g. only a line drawn
  inside an open sketch).
- Verification now runs for every SolidWorks macro, regardless of the method the
  model asked for, so the model's own claim is never trusted.
- A macro that raises mid-way is recorded as `verified=False`, then the error is re-raised.
- Ledger: failed steps are excluded from skill counts and status, Aya's spoken summary
  says what didn't work, and the lecturer report shows confirmed / not checkable /
  failed counts.
- Canva and generic macros are recorded as not verified (`None`); no check exists yet.
- `COM_ERROR` guard so the `except` clause is valid on machines without pywin32.

## Tests run

`python -m pytest prototype/tests -q` → 10 passed (Linux, Python 3, fake driver).
Covers: confirmed extrude, extrude producing nothing, sketch left unextruded,
two extrudes needing two extrusions, unverifiable sketch edits, crash mid-macro,
failed demonstration not counted, report counts.

## Uncertainty

- The feature type names `"Extrusion"` and `"ProfileFeature"` come from SolidWorks
  API documentation and are **not yet confirmed on H's SolidWorks 2026**. The
  `[verify]` line prints actual types on every run, so the first live run will show it.
- This proves a feature was created, not that it has the right dimensions or position.
  It would not catch the fused bolt (head and shaft both extrude successfully).
  Dimension/position checks are the next step after the bolt regression run.

## Next proof action

Live run on H's machine: rectangle 100x50 extrude 10. Expect `[verify] confirmed: ...
Boss-Extrude1 (Extrusion)`. If the type differs, update `EXPECTED_FEATURE_TYPES`.
