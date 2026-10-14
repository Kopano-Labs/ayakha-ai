# Ayakha Current State

- Updated: 2026-10-14 (Africa/Johannesburg).
- Repository: [RobynAwesome/ayakha-ai](https://github.com/RobynAwesome/ayakha-ai).
- Published implementation baseline: `main` at `8d15cd70ac0a6aec472a3db0bf5b13e90dae6601`.
- State: exploratory prototype and safety fixes merged; hosted Ubuntu/Windows CI passed. POC-1 remains open.

## Verified success

The repository was transferred from Kopano-Labs to RobynAwesome, retaining GitHub repository ID `1347630895`, history and PRs. Robyn reported that the billing issue belonged to Kopano-Labs; successful Actions runs verify execution in the current repository, not the billing status of the former organization.

| Event | Exact evidence |
|---|---|
| PR #4 merged into the prototype branch | [PR #4](https://github.com/RobynAwesome/ayakha-ai/pull/4), merge `da9e0a0affced54501db06f593c4f397e5b86c76`, 2026-10-14 01:43:49 SAST |
| PR #3 merged into main | [PR #3](https://github.com/RobynAwesome/ayakha-ai/pull/3), merge `8d15cd70ac0a6aec472a3db0bf5b13e90dae6601`, 2026-10-14 01:45:17 SAST |
| Hosted CI on merged main | [Run 38486145600](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600), same `8d15cd7` commit, Python 3.12 |
| Ubuntu and Windows jobs | Each ran **57 passing tests** and successful `compileall`; no SolidWorks or provider keys required |

The former PR stack is merged history. Do not resume PR #4 or treat the old billing blocker as current. The full observation is in the [transfer, merge and CI receipt](docs/receipts/2026-10-14-transfer-merge-ci-success.md). Re-query main, PRs and CI before making new current-state claims.

## What exists in source

| Area | Current implementation and limits |
|---|---|
| Exploratory input/planner | Typed input, optional Google speech recognition and Groq `openai/gpt-oss-120b`; hosted flows require startup consent |
| Action contract | Prototype MacroAction, mandatory local approval and whole-plan preflight; not the canonical MVP intent contract |
| SolidWorks driver | Windows COM sketch/extrude primitives, bounded parameters, checks for Aya's unsaved disposable part; actual machine behavior remains to be validated |
| Execution gates | Exact y/yes, document ownership checks, failed/interrupted driver invalidation; no pause/resume or automated rollback |
| Disabled actions | Generic desktop control, toolbar clicks, automatic saving, Canva dispatch, feature selection, dimension and fillet execution |
| Ledger | Local SQLite attempts/attribution and Markdown reports; failed or unknown results do not establish learning progress; historical flags were not re-audited |
| Verification | Before/after feature trees can detect missing features. Presence alone remains geometry-unverified |
| Tests and CI | 57 offline tests with fake COM drivers/documents; hosted Windows/Linux checks passed at the baseline above |
| Preserved exploratory files | Untested Canva driver, schema benchmark and read-only SolidWorks UI inspection script |

## Canonical MVP status

Aya is the everyday persona; Ayakha is the broader local-first desktop product. [MVP_TRUTH_LOCK.md](docs/MVP_TRUTH_LOCK.md) remains active. Merging the prototype does not change the local-inference requirement, intent/clarification contract or the one-approved-parameter-edit acceptance case.

POC-1 [issue #1](https://github.com/RobynAwesome/ayakha-ai/issues/1) remains
open. Its local input-to-brief implementation is prepared for review on
`codex/poc1-local-aya-brief`, beginning at
`ebc9fe774edebf87b4083b5922a9a7a3c910bce4`, and is under review in
[PR #6](https://github.com/RobynAwesome/ayakha-ai/pull/6). It supplies the local development
shell, canonical intent, clarification loop, editable Markdown brief and
Cars4Mars fixture, with no external action. The [POC-1 receipt](docs/receipts/2026-10-14-poc1-local-input-brief.md)
records its local evidence; it is neither merged nor a hosted-CI result yet.
Canva proof, an approved edit in a prepared SolidWorks part, undo/version
evidence, packaging and student-field evidence remain pending. The exploratory
COM driver and ledger exist; that does not make their MVP acceptance complete.

## Next work

Use [NEXT_STEPS.md](docs/NEXT_STEPS.md) for acceptance criteria and handoff details.

1. Review [POC-1 PR #6](https://github.com/RobynAwesome/ayakha-ai/pull/6) and run the existing hosted Ubuntu/Windows workflow at its exact head. Its required captured intent and clarification response are already in the POC-1 receipt; merge evidence remains pending.
2. Validate the merged prototype on the actual Windows/SolidWorks machine: disposable 100x50 mm rectangle extruded 10 mm, then the M15 positioning regression, with measured geometry and ledger evidence. Preserve approval gates and record failures honestly.
3. Robyn and H resolve the prototype/MVP scope differences before promotion: hosted versus local inference, MacroAction versus canonical intent, COM versus visible clicks, and free-form creation versus one prepared-part parameter edit. Until a documented decision changes scope, the active truth lock governs.

These are separate evidence and implementation lanes. Successful CI is not live CAD, local-inference, student-learning, deployment or completed-MVP proof.

## Local development and agent entry

- Working folder: `C:\Users\rkhol\ayakha-ai`.
- Canonical remote: `https://github.com/RobynAwesome/ayakha-ai.git`.

Start with [AGENTS.md](AGENTS.md), this file, the truth lock and the active issue. Inspect dirty state, fetch and compare; preserve unrelated changes. Start each new task from current main on a scoped `codex/` branch, edit and validate locally, then push the intended commits for review. Do not reuse the merged PR branches or force-push to refresh dates.

Every implementation receipt must include changed files, setup/run commands, test results, observed proof, unresolved uncertainty and the next proof action. POC-1 additionally needs a captured intent JSON and clarification response. Keep historical receipts intact; use a new dated receipt for new observations.
