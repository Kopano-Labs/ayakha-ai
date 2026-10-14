# Ayakha MVP Truth Lock

Status: active
Date: 2026-08-26
Authority: product and engineering scope for the first proof

Implementation note (2026-10-14): PRs #3 and #4 have merged an exploratory
connected prototype, and its offline Ubuntu/Windows CI passed. This contract
remains active; the merges do not ratify hosted inference, replace canonical
intent/clarification or complete the acceptance test below. See
[NOW.md](../NOW.md) for current evidence and [NEXT_STEPS.md](NEXT_STEPS.md) for
the prototype proof and POC-1 implementation lanes. The original contract date
above remains the date of the scope authority.

## 1. Problem

A student can often see or feel a design before they can describe it in engineering language. The current journey breaks that intent across conversation, visual communication and CAD tools.

Ayakha exists to preserve the student's intent while helping them clarify, communicate, edit, learn and test.

## 2. User

Primary user: a student or beginner maker working on a real design problem.

Secondary users: tutors, mentors and collaborators who need to understand what the student intends to build.

## 3. MVP outcome

The student starts with a spoken, typed or visual idea and finishes with:

1. A structured design brief.
2. Clear missing requirements and clarifying questions.
3. A visible result in Canva.
4. One approved, reversible change in SolidWorks.
5. An explanation of what changed and why.
6. A local ledger entry that can be inspected later.

## 4. Runtime boundary

The Aya intelligence runs on the desktop:

```
mic / text / sketch
        |
        v
local input adapters
        |
        v
Aya orchestrator
(STT + local planner + vision adapter + TTS)
        |
        v
intent JSON + clarification + design brief
        |
        +--> Canva connector (web-based, opt-in)
        |
        +--> SolidWorks connector (Windows MVP lane)
        |
        v
local design ledger and evidence
```

The local runtime must not depend on a hosted Ayakha web application. Connected tools may require internet access, user authentication or platform-specific software; that boundary must be visible to the user.

## 5. Canonical intent contract

The planner must produce a structured object rather than an ungoverned prose action:

```json
{
  "mode": "clarify | brief | edit",
  "problem": "",
  "user_or_context": "",
  "desired_outcome": "",
  "constraints": [],
  "known_requirements": [],
  "missing_requirements": [],
  "assumptions": [],
  "questions": [],
  "proposed_action": null,
  "target_tool": null,
  "confidence": 0.0,
  "requires_confirmation": true
}
```

Rules:

- Missing dimensions, materials, interfaces or safety requirements become questions.
- The planner may propose an action; it may not execute an external-tool action without confirmation.
- Confidence is evidence about the current interpretation, not permission to act.
- The student can correct, reject or take over every edit.

## 6. Acceptance test

Use this seed request:

> Aya, I need a motor mount for our Cars4Mars rover. It must fit the motor, survive vibration, stay within our printer volume and be easy for a student to explain.

Expected behaviour:

1. Aya captures the request locally.
2. Aya asks for the motor dimensions, bolt pattern, load, material, printer limits and other missing constraints instead of guessing.
3. Aya creates an editable design brief in the local workspace.
4. After approval, Aya creates or updates a one-page Canva design brief using only the approved payload.
5. After approval, Aya changes one known parameter in a prepared SolidWorks test part.
6. Aya reports the change, assumptions, result and next test.
7. The local ledger records the input, clarification, approval, tool action and result.

## 7. MVP exclusions

The following are explicitly outside the first acceptance test:

- Automatic printer start or physical machine control.
- Full free-form CAD generation.
- Autonomous Canva publishing or sharing.
- Blender, animation, game-asset and mascot-generation pipelines.
- Multi-user cloud collaboration.
- Hosted model inference required for normal operation.
- Unreviewed external actions.

## 8. Engineering decisions to validate

- Cross-platform desktop shell and packaging.
- Local model adapters for Whisper-compatible STT, a local planner/model, visual input and Piper-compatible TTS.
- Local project storage and ledger format.
- Canva connection method: supported design-editing/deep-link flow.
- SolidWorks connection method: Windows API/add-in/macro bridge for one safe operation.
- Test-fixture strategy for machines that do not have SolidWorks installed.

These choices may evolve only when a test, constraint or measured failure requires it.

## 9. Definition of done

The MVP is not done because a screen looks polished. It is done when the team can demonstrate, on a real desktop:

- local Aya runtime status;
- voice or text input;
- clarification instead of hallucinated requirements;
- structured brief;
- approved Canva result;
- approved SolidWorks edit;
- visible approval and undo/version evidence;
- local ledger receipt;
- repeatable setup instructions;
- a short recording or live demonstration with the Cars4Mars case.

## 10. Agent governance

Before modifying code, an agent must read:

1. `NOW.md`
2. this file
3. the relevant issue or pull-request acceptance criteria

Agents must leave a receipt containing:

- files changed;
- commands/tests run;
- proof observed;
- unresolved uncertainty;
- next action.

No agent may expand MVP scope silently.
