"""Local execution policy. Model output proposes; this policy authorizes nothing.

Only the reviewed SolidWorks primitives are executable in this import baseline.
Validate the entire plan before confirmation or connecting to an external tool.
"""
import math

from macro_action_schema import MacroAction, SolidWorksAction, Tool

# Required keys, optional keys. Millimetres, bounded for a disposable demo part.
PARAMS = {
    "new_sketch": ({"plane"}, {"offset_mm"}),
    "draw_line": ({"x1", "y1", "x2", "y2"}, set()),
    "draw_rectangle": ({"width", "height"}, {"x", "y"}),
    "draw_circle": ({"radius"}, {"x", "y"}),
    "extrude": ({"depth"}, set()),
}


def validate_execution(macro):
    # Revalidate even a model constructed or altered without Pydantic validation.
    macro = MacroAction.model_validate(macro.model_dump())
    if macro.requires_confirmation is not True:
        raise ValueError("Local confirmation is mandatory")
    if macro.tool != Tool.SOLIDWORKS:
        raise ValueError("Only SolidWorks execution is enabled in this baseline")
    for action in macro.actions:
        if not isinstance(action, SolidWorksAction) or action.type.value not in PARAMS:
            raise ValueError(f"Action '{action.type.value}' is disabled by local policy")
        required, optional = PARAMS[action.type.value]
        p = action.params
        if not required <= p.keys() or p.keys() - required - optional:
            raise ValueError(f"Invalid parameters for '{action.type.value}'")
        for key, value in p.items():
            if key == "plane":
                if value not in ("Front", "Top", "Right"):
                    raise ValueError("Unknown sketch plane")
                continue
            if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1000:
                raise ValueError(f"'{key}' must be a finite number within 1000 mm")
            if key in ("width", "height", "radius", "depth") and value <= 0:
                raise ValueError(f"'{key}' must be positive")
    return macro
