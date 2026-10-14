# Next work after the prototype merge

Updated: 2026-10-14. Read [NOW.md](../NOW.md) for exact source and CI receipts.
The merged prototype and Windows/Ubuntu CI are established; canonical MVP and
live CAD acceptance remain pending.

## 1. Next prototype proof: actual SolidWorks machine

Coordinate the session with Robyn and H on the actual Windows/SolidWorks setup.
Use the [prototype setup and recovery instructions](../prototype/README.md).
Supply provider keys only through environment variables, disclose Groq/Google
flows and obtain the driver's normal session and macro consent. Keep student
documents closed; operate on Aya's newly created disposable unsaved part.

| Proof | Required observation |
|---|---|
| Rectangle baseline | Requested 100x50 mm rectangle with 10 mm extrusion; measure all three dimensions in SolidWorks, record actual feature names/types and capture screenshots |
| Ownership boundary | In a controlled disposable session, verify that switching, closing or saving the target blocks subsequent mutation; never use a student's file for this test |
| Failure/recovery | Confirm interrupted/failed execution cannot continue; retain partial-result evidence, then discard the unsaved demo part and restart |
| Ledger | Inspect the session events/report: missing features fail, presence-only geometry remains unverified, and unknown/failed attempts do not advance progress |
| M15 positioning | Record the requested model, actual offsets, alignment and separation; check whether head/shaft still fuse. Simplified primitives do not prove standards-compliant M15 geometry |

Record exact commit, OS, SolidWorks version, request and approved MacroAction,
expected versus observed results, measurements, ledger output, screenshots,
failures and recovery in a new dated receipt. Keep sensitive payloads out of Git.
Do not flip `verified=True` just because a human sees features or COM succeeds;
a geometry verifier needs its own scoped implementation and tests.

Pass this proof only when observations support each claim. If a case fails,
record the failing request and create a bounded fix; do not weaken gates or
describe wrong geometry as success. Live proof is not student-learning proof.

## 2. Resolve prototype/MVP differences

Robyn and H need a documented decision before MVP promotion. Until then, the
[active truth lock](MVP_TRUTH_LOCK.md) governs canonical implementation.

| Topic | Merged prototype | Active MVP contract |
|---|---|---|
| Inference/input | Groq planner; optional Google STT | Local inference and local input adapters |
| Contract | MacroAction execution plan | Canonical intent with clarification and editable brief |
| CAD operation | Primitive geometry in a disposable new part | One approved known-parameter edit in a prepared test part |
| Actuation | COM mutations with read-only feature checks | Connection/visibility decision still needs validation; no silent ratification of true-click claims |
| Recovery | Abort and manually discard; no automatic rollback | Visible approval and undo/version evidence |

A decision receipt must state whether to bring the prototype into conformance or
explicitly revise scope, the accepted tradeoffs and required acceptance proof.
The merges themselves do not make that decision.

## 3. Next canonical implementation: POC-1

[Issue #1](https://github.com/RobynAwesome/ayakha-ai/issues/1) remains open and is
the next canonical engineering task. Keep it separate from the live prototype
session; it can proceed under the unchanged truth lock.

Acceptance requires:

1. A desktop or local development shell with visible Aya runtime status.
2. Deterministic text input fallback.
3. A local planner adapter returning the truth-lock intent object.
4. Clarifying questions for missing dimensions, material, interfaces and safety
   constraints; no fabricated motor specifications.
5. An editable design brief.
6. A repeatable Cars4Mars motor-mount request fixture.
7. No external-tool execution in this issue.
8. Tests, captured intent JSON, a clarification response and an honest receipt of
   unresolved model/hardware constraints.

Voice, vision and TTS may remain explicit interfaces if hardware/models are not
ready; do not weaken acceptance or substitute hosted inference silently.
Canva connection, prepared-part SolidWorks editing, packaging and field sessions
are subsequent scoped work. No field recruitment or messages are authorized by
this plan.

## Handoff for every new task

Record the local folder, remote, branch/commit, dirty-state boundary, acceptance
criteria, changed files, commands/results, observed proof, remaining blockers and
next admissible action. Link the current CI run at the exact head when available.
The existing Ubuntu/Windows workflow is sufficient for these offline prototype
checks; add tests/infrastructure only when the actual change requires them.
