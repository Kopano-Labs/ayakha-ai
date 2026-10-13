"""
Ayakha Macro-Action Schema
==========================

This is the contract between Aya's cloud brain (reasoning) and the local
driver (hands/eyes) on the student's machine.

Design principles this schema encodes:
1. BATCHED, not raw clicks — the brain sends one macro ("draw a 100x50
   rectangle"), and the local driver expands it into however many
   individual mouse/keyboard events are needed. This is what keeps Aya
   responsive over slow/unreliable connections instead of round-tripping
   to the cloud for every click.
2. COM ACTUATION — the current SolidWorks driver mutates via COM.
   Feature-tree verification uses read-only COM calls. True-click actuation
   remains an unresolved product decision.
3. TEACHING IS FIRST-CLASS — narration and demonstration mode aren't
   bolted on after the fact. A macro can be executed silently, narrated
   step-by-step, or flagged as a "let me demonstrate" moment where Aya
   takes over from the student to show the correct move.
4. VERIFIABLE — every macro states how the local driver (or brain, on
   the next turn) should confirm it actually worked, instead of trusting
   the model's own claim of success. Matches the existing SolidWorks
   COM-readonly pattern.

This file defines the schema only (pydantic models for validation).
It does not execute anything — that's the local driver's job.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Union, Literal
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Which tool this macro targets. Determines which action vocabulary applies.
# ---------------------------------------------------------------------------
class Tool(str, Enum):
    SOLIDWORKS = "solidworks"
    CANVA = "canva"
    GENERIC = "generic"  # any tool without a dedicated action set yet


# ---------------------------------------------------------------------------
# SolidWorks action vocabulary
# ---------------------------------------------------------------------------
class SolidWorksActionType(str, Enum):
    NEW_SKETCH = "new_sketch"
    DRAW_LINE = "draw_line"
    DRAW_RECTANGLE = "draw_rectangle"
    DRAW_CIRCLE = "draw_circle"
    ADD_DIMENSION = "add_dimension"
    EXTRUDE = "extrude"
    FILLET = "fillet"
    SELECT_FEATURE = "select_feature"
    CLICK_TOOLBAR = "click_toolbar"  # fallback for ops not yet modeled
    SAVE_FILE = "save_file"


class SolidWorksAction(BaseModel):
    type: SolidWorksActionType
    # Params are intentionally loose (dict) at this layer — each action
    # type validates its own required keys in the local driver, similar
    # to how ayakha_brain.py already validates cad_parameters.
    params: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Canva action vocabulary
# ---------------------------------------------------------------------------
class CanvaActionType(str, Enum):
    CLICK_ELEMENT = "click_element"
    ADD_TEXT = "add_text"
    ADD_SHAPE = "add_shape"
    ADD_IMAGE = "add_image"
    DRAG_RESIZE = "drag_resize"
    CHANGE_COLOR = "change_color"
    SELECT_TEMPLATE = "select_template"


class CanvaAction(BaseModel):
    type: CanvaActionType
    params: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generic fallback vocabulary — true UI automation primitives.
# Used when a tool-specific action doesn't exist yet, or for any
# tool under Tool.GENERIC. This is what keeps automation "true" even
# for actions nobody has explicitly coded — Aya can still act like a
# human would: look at the screen, click, type.
# ---------------------------------------------------------------------------
class GenericActionType(str, Enum):
    CLICK_AT = "click_at"          # params: x, y
    MOVE_MOUSE = "move_mouse"      # params: x, y
    TYPE_TEXT = "type_text"        # params: text
    KEY_PRESS = "key_press"        # params: key
    WAIT = "wait"                  # params: milliseconds
    SCREENSHOT = "screenshot"      # no params — local driver returns image


class GenericAction(BaseModel):
    type: GenericActionType
    params: dict = Field(default_factory=dict)


AtomicAction = Union[SolidWorksAction, CanvaAction, GenericAction]


# ---------------------------------------------------------------------------
# Verification — how to confirm the macro actually did what it claimed.
# ---------------------------------------------------------------------------
class VerificationMethod(str, Enum):
    COM_READONLY = "com_readonly"      # e.g. check SolidWorks feature tree
    SCREENSHOT_DIFF = "screenshot_diff"  # e.g. compare before/after for Canva
    NONE = "none"                       # low-stakes actions (e.g. a click to focus)


class Verification(BaseModel):
    method: VerificationMethod = VerificationMethod.NONE
    # Human-readable description of what "success" looks like, for the
    # brain to check against on its next turn (e.g. "one new extrude
    # feature named 'Boss-Extrude2' exists in the feature tree").
    expected: Optional[str] = None


# ---------------------------------------------------------------------------
# Teaching metadata — makes the pedagogy explicit in the schema itself,
# not an afterthought bolted onto a purely mechanical action list.
# ---------------------------------------------------------------------------
class TeachingMode(str, Enum):
    SILENT = "silent"            # student asked Aya to just do it
    NARRATED = "narrated"        # Aya explains while doing it (default for teaching)
    DEMONSTRATION = "demonstration"  # "allow me to demonstrate" — Aya takes over
                                      # from the student to show the correct move


class Teaching(BaseModel):
    mode: TeachingMode = TeachingMode.NARRATED
    # What Aya says to the student while/before executing, e.g.
    # "I'm sketching a 100x50 rectangle on the front plane."
    narration: Optional[str] = None
    # Only meaningful when mode == DEMONSTRATION: the mistake being
    # corrected, so the student understands *why* Aya is stepping in.
    correcting: Optional[str] = None


# ---------------------------------------------------------------------------
# The top-level unit the cloud brain sends to the local driver.
# ---------------------------------------------------------------------------
class MacroAction(BaseModel):
    macro_id: str
    tool: Tool
    # Plain-language description of the overall goal, e.g.
    # "Draw a 100x50mm rectangle on the front plane and extrude 10mm."
    goal: str
    actions: list[AtomicAction] = Field(min_length=1, max_length=50)
    teaching: Teaching = Field(default_factory=Teaching)
    verification: Verification = Field(default_factory=Verification)
    # Approval gate — matches the "every AI action requires confirmation"
    # decision. The model cannot disable local approval.
    requires_confirmation: Literal[True] = True
    # Planner metadata only; no pause/resume control is implemented.
    # Ctrl+C aborts execution regardless of this value.
    interruptible: bool = True

    @model_validator(mode="after")
    def match_action_tool(self):
        action_class = {Tool.SOLIDWORKS: SolidWorksAction,
                        Tool.CANVA: CanvaAction, Tool.GENERIC: GenericAction}[self.tool]
        if any(not isinstance(action, action_class) for action in self.actions):
            raise ValueError("Every action must match the macro's target tool")
        return self


# ---------------------------------------------------------------------------
# Example: what the cloud brain would actually emit for
# "draw a 100x50 rectangle and extrude it 10mm" on SolidWorks.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example = MacroAction(
        macro_id="macro_0001",
        tool=Tool.SOLIDWORKS,
        goal="Draw a 100x50mm rectangle on the front plane and extrude 10mm.",
        actions=[
            SolidWorksAction(type=SolidWorksActionType.NEW_SKETCH, params={"plane": "Front"}),
            SolidWorksAction(
                type=SolidWorksActionType.DRAW_RECTANGLE,
                params={"x": 0, "y": 0, "width": 100, "height": 50},
            ),
            SolidWorksAction(
                type=SolidWorksActionType.EXTRUDE,
                params={"depth": 10},
            ),
        ],
        teaching=Teaching(
            mode=TeachingMode.NARRATED,
            narration="I'm sketching a 100 by 50 millimeter rectangle on the front plane, then extruding it 10mm.",
        ),
        verification=Verification(
            method=VerificationMethod.COM_READONLY,
            expected="One new extrude feature exists in the feature tree with depth 10mm.",
        ),
        requires_confirmation=True,
        interruptible=True,
    )

    print(example.model_dump_json(indent=2))
