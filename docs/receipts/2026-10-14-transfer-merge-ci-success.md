# Repository transfer, merged prototype and hosted CI success

- Observation date: 2026-10-14 (Africa/Johannesburg).
- Repository: `RobynAwesome/ayakha-ai`, GitHub ID `1347630895`.
- Published implementation baseline: `8d15cd70ac0a6aec472a3db0bf5b13e90dae6601` on `main`.

## Authority and observation

Robyn reported transferring Aya from Kopano-Labs to the personal repository
because billing belonged to the organization, then merging both PRs after CI.
GitHub API queries verified the repository identity, both merges and passing
hosted CI. This establishes repository/Actions success; it does not establish
that Kopano-Labs' organization billing has been repaired.

| Event | Exact receipt |
|---|---|
| PR #4 merged | [PR #4](https://github.com/RobynAwesome/ayakha-ai/pull/4), head `efbf5d33ca3ccc27115f8b5004a245e2de3c1470`, merge `da9e0a0affced54501db06f593c4f397e5b86c76` into `prototype/voice-solidworks-pipeline` |
| PR #3 merged | [PR #3](https://github.com/RobynAwesome/ayakha-ai/pull/3), head `da9e0a0affced54501db06f593c4f397e5b86c76`, merge `8d15cd70ac0a6aec472a3db0bf5b13e90dae6601` into `main` |
| Main CI passed | [Run 38486145600](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600), push at that exact merged-main commit |
| Windows job | [Job 115600163717](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600/job/115600163717): 57 tests passed in 2.36 s; compilation succeeded |
| Ubuntu job | [Job 115600164088](https://github.com/RobynAwesome/ayakha-ai/actions/runs/38486145600/job/115600164088): 57 tests passed in 0.39 s; compilation succeeded |

PR #4 merged at 2026-10-13 23:43:49 UTC / 2026-10-14 01:43:49 SAST.
PR #3 merged at 2026-10-13 23:45:17 UTC / 2026-10-14 01:45:17 SAST.
These are owner-performed merges, not agent merge actions.

The local checkout was clean, its remote updated to
`https://github.com/RobynAwesome/ayakha-ai.git`, and local `main` fast-forwarded to
the merged baseline without overwriting local work. Historical PR branches were
preserved. New documentation is prepared on `codex/docs-merged-prototype-status`
for review; the baseline above describes the merged implementation, not a claim
that this documentation branch has already merged.

## Documentation refresh

Files changed: root `README.md`, `NOW.md`, `AGENTS.md`, Copilot instructions,
`prototype/README.md`, `docs/MVP_TRUTH_LOCK.md` (implementation note only),
`docs/NEXT_STEPS.md`, `docs/README.md` and this receipt.

The refresh records success, replaces stale current billing/PR-stack guidance,
distinguishes existing source from pending MVP acceptance, provides offline setup
and gives agents acceptance criteria for the next work. Earlier receipts are
preserved as dated history. Runtime code, dependency pins and CI configuration
are unchanged.

Validation: queried repository/PR/run metadata and the hosted job logs; checked
local Markdown targets, source/command consistency and `git diff --check` before
commit. This documentation update uses the existing PR CI for its own head;
the baseline CI above is not a claim that the documentation PR has passed.

## Remaining proof and next action

- Live SolidWorks identity, geometry dimensions/positioning and recovery remain
  unverified by the offline tests. Run the disposable rectangle 100x50/extrude
  10 and M15 regressions with measured evidence and ledger inspection.
- Feature presence alone remains unverified geometry and cannot establish
  learning progress. Historical ledger flags were not re-audited.
- The active truth lock is unchanged in scope. Robyn and H still need to resolve
  prototype/MVP differences before promotion; POC-1 issue #1 remains open.
- No Canva proof, field learning, packaged release, deployment or completed MVP
  is claimed by the transfer, merges or hosted CI.

Use [NEXT_STEPS.md](../NEXT_STEPS.md) for the acceptance criteria and evidence
format; refresh [NOW.md](../../NOW.md) after new verified results.
