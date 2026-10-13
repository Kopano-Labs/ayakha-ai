# Ayakha local checkout and prototype safety review

Date: 2026-10-12 (Africa/Johannesburg)
Scope: local development and bounded fixes to the existing PR #4 stack.
This receipt establishes source and offline test evidence, not live CAD or MVP proof.

## Source population and branch freshness

- Local folder: `C:\Users\rkhol\ayakha-ai`.
- The folder already contained a clean Git checkout. No local changes were
  overwritten and no second nested repository was created.
- Both old `RobynAwesome/ayakha-ai` and current `Kopano-Labs/ayakha-ai` API URLs
  resolved to repository ID `1347630895`. Updated the repository's `origin` URL
  to `https://github.com/Kopano-Labs/ayakha-ai.git` and fetched its branches.
- Local working branch: `fix/ledger-verification`, tracking its existing remote.
- Audited `main`: `a20e6d5c93b8b9ae464515059b37ce988752659b`.
- Audited PR #3 head: `b9d8b5aeb2ab9f85d2ecc70e997f986d7c001f4a`, targeting `main`.
- Audited PR #4 head: `ddd2b75de2caf2571c507f1240e0fec370f8159c`, targeting PR #3's
  `prototype/voice-solidworks-pipeline` branch.
- `git rev-list --left-right --count` returned `0 1` for each base/head pair:
  each head was one commit ahead, zero behind. Both were mergeable; no rebase
  or history rewrite was needed. PR #3 had a requested-changes review. Both
  audited heads had no CI checks.

## Changes

- `prototype/macro_action_schema.py`: mandatory confirmation, matching action/tool
  classes and nonempty plans capped at 50 actions; corrected COM/pause comments.
- `prototype/execution_policy.py`: local full-plan preflight, reviewed primitive
  allowlist, exact parameter keys, finite bounded millimetres and positive sizes.
- `prototype/ayakha_local_driver.py`: exact confirmation tokens, plan preview,
  connected-flow consent, deferred tool connection, owned unsaved part identity
  checks before actions, interruption/failure invalidation, disabled saving and
  generic/Canva dispatch. COM mutation is described accurately.
- `prototype/ayakha_ledger.py`: feature presence remains geometry-unverified;
  unknown results cannot establish learning progress. Explicit test databases
  create their own parent directory instead of touching the default ledger folder.
- `prototype/ayakha_brain_benchmark.py`: corrected Groq model labels. The benchmark
  remains a schema probe; unsupported executable requests are rejected locally.
- `prototype/tests/test_verification.py` and `test_execution_safety.py`: offline
  regression coverage for approval, policy, ownership, interruption and evidence.
- `prototype/requirements-test.txt`, `.github/workflows/prototype-tests.yml`:
  isolated Python 3.12 test dependencies and offline Windows/Linux CI on push/PR.
- `.gitignore`, `prototype/README.md`, `NOW.md`: ignored local virtual environment,
  repeatable local workflow, connected-flow disclosure and recovery instructions.
- This receipt records scope, proof and remaining uncertainty.

## Commands and observed results

Created `.venv` using the bundled Python 3.12.14 runtime, then ran:

```powershell
.\.venv\Scripts\python.exe -m pip install -r prototype/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest prototype/tests -q
.\.venv\Scripts\python.exe -m compileall -q prototype
git diff --check
```

Observed: **57 passed**, pytest exit code 0; compileall and diff whitespace checks
passed. Tests use fake COM documents/drivers and temporary SQLite databases.
No SolidWorks, browser, microphone, provider inference or student session was run.
Cloud CI results must be checked on the pushed commit; local success is not a
claim that GitHub Actions has passed.

## Push and cloud CI observation

The local safety change was committed and pushed without a history rewrite:
`5218b949d5717fe4a9d561c3f9c51c52e160b73b`. GitHub PR #4's head matched that
commit; its base stayed `prototype/voice-solidworks-pipeline`. The working tree
was clean and synchronized. PR #4's title/description now reflect the safety
scope. `main` and PR #3's branch were not changed.

GitHub created both workflow events at that source commit:

- [Push run 38243910978](https://github.com/Kopano-Labs/ayakha-ai/actions/runs/38243910978)
- [Pull-request run 38243911850](https://github.com/Kopano-Labs/ayakha-ai/actions/runs/38243911850)

The runs failed before execution. Job annotations reported:
“The job was not started because your account is locked due to a billing issue.”
The matrix sibling was also canceled on the PR event. This is a GitHub account
billing blocker, not a test failure observed on a runner. No hosted test passed.
The account owner must resolve billing, then rerun CI at the current PR head;
repository billing/settings were not modified. This receipt update is a separate
documentation commit after the tested source commit.

The API reported Actions enabled. The classic `main` protection endpoint returned
`404 Branch not protected`; active branch rules and repository rulesets returned
empty arrays. This is the observed enforcement state, not a request to change
repository settings. CI configuration alone does not enforce merge policy.

## Remaining uncertainty and next proof

- Live COM identity, unsaved-part guard, feature types and geometry remain
  untested against the actual SolidWorks installation. Identity uses
  [ISldWorks.IsSame](https://help.solidworks.com/2021/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~IsSame.html)
  and the documented `swObjectSame=1`; unsupported results block execution.
- Feature presence cannot verify dimensions or positioning. No geometry verifier
  was added and no successful CAD result is claimed. Historical ledger records
  are preserved, including prior verification flags; they were not re-audited.
- A failure can leave partial unsaved geometry. There is no automatic rollback or
  pause/resume. Discard the demo part without saving and restart after failure.
- Development now proceeds locally to GitHub. The imported prototype still uses
  hosted Groq inference and Google STT; local development does not make inference
  local. `docs/MVP_TRUTH_LOCK.md` is unchanged and remains active.
- Review PR #4 at its new exact head after CI. If accepted, integrate #4 into #3's
  branch, then revalidate #3 and its outstanding review before an owner-authorized
  merge to `main`. No merge/auto-merge or scope ratification is part of this work.
- Next machine proof: disposable rectangle 100x50 mm, extrude 10 mm, record actual
  dimensions, identity checks and ledger; then repeat the M15 positioning test.
  Owner/student field evidence and the truth-lock scope decision remain pending.
