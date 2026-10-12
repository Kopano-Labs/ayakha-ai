"""Ayakha exploratory connected prototype.

Groq plans; the local policy validates and requests keyboard approval for every
macro. Only bounded SolidWorks sketch/extrude primitives are executable, via
COM mutations in an unsaved disposable part. Feature-tree reads establish
presence only; correct geometry remains unverified. Canva and global desktop
control are disabled. Ctrl+C aborts; partial geometry must be discarded manually.
See prototype/README.md for setup, connected data flows and recovery.
"""

import os
import json
import time
import requests
from pydantic import ValidationError

from macro_action_schema import (
    MacroAction,
    Tool,
    GenericActionType,
    TeachingMode,
)
from ayakha_ledger import Ledger
from execution_policy import validate_execution

TAKEOVER_PHRASES = ("just do it", "do it for me", "build it for me", "you do it", "just build it")

# pywin32 is Windows-only. Guarded so this file can still be
# read, imported, and syntax-checked on any platform — only fails at the
# point of actually trying to drive SolidWorks or the screen.
try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

# The exception type for SolidWorks COM failures. An empty tuple catches
# nothing, so this stays valid on machines without pywin32.
COM_ERROR = pythoncom.com_error if pythoncom is not None else ()

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are Ayakha's prototype planner, proposing SolidWorks COM actions for student approval.

Given a student's request, respond with ONLY a JSON object matching this exact structure (no markdown fences, no explanation, just the raw JSON):

{
  "macro_id": "macro_XXXX",
  "tool": "solidworks",
  "goal": "plain language description of what this macro accomplishes",
  "actions": [
    {"type": "<action_type>", "params": {...}}
  ],
  "teaching": {
    "mode": "silent" | "narrated" | "demonstration",
    "narration": "what Aya says while doing this, or null",
    "correcting": "what mistake is being corrected, or null (only used in demonstration mode)"
  },
  "verification": {
    "method": "com_readonly" | "screenshot_diff" | "none",
    "expected": "what success looks like, or null"
  },
  "requires_confirmation": true,
  "interruptible": true
}

CRITICAL: Only use the exact action types and exact param keys listed below.
Never invent a new action type (e.g. there is no "draw_polygon" — build a
polygon out of multiple "draw_line" actions instead). Never invent a param
key not listed here (e.g. use "x"/"y", never "center_x"/"cx").

SolidWorks action types and their exact required params:
- new_sketch: {"plane": "Front" | "Top" | "Right", "offset_mm": number (optional, default 0)}
- draw_line: {"x1": number, "y1": number, "x2": number, "y2": number}
- draw_rectangle: {"x": number, "y": number, "width": number, "height": number}
- draw_circle: {"x": number, "y": number, "radius": number}
- extrude: {"depth": number}
- add_dimension: not yet supported — avoid this type, describe the dimension in narration instead
- fillet: not yet supported — avoid this type, skip fillets for now

COAXIAL STACKING (critical for multi-feature parts like bolts/shafts):
Every new_sketch defaults to starting at the base plane's origin (offset 0),
so two features sketched with no offset will overlap instead of sitting
end-to-end. To stack a second feature coaxially against a previous one
(e.g. a bolt shaft against the bottom of its head), set that sketch's
offset_mm to the cumulative extrude depth of everything already built
along that axis. Track this running total yourself across the actions
you emit — e.g.: sketch+extrude the head 10mm deep at offset_mm 0, then
sketch the shaft at offset_mm 10 (not 0) before extruding it — so the
shaft starts exactly where the head ends rather than fusing into it.

Canva, generic desktop controls, saving and feature selection are disabled.
If a request is a real, complex mechanical part (e.g. a bolt with a
hexagonal head and threads), approximate it with the primitives above —
e.g. a hex head as six draw_line calls, threads represented as a single
cylinder rather than true helical geometry. Do not skip the request; do
the closest reasonable approximation with only the actions listed above.

All dimensions in params are in millimeters, finite and within 1000 mm.
Every macro requires confirmation. Do not include unsupported actions.
"""


def speak(text: str, tts_engine):
    """Speaks narration aloud via TTS, and always prints it as a live
    caption regardless of whether TTS is available — matches the decision
    that students should both see and hear Aya's narration."""
    print(f"Aya says: {text}")
    if tts_engine is not None:
        tts_engine.say(text)
        tts_engine.runAndWait()


def listen_for_request(recognizer, microphone) -> str | None:
    """Captures one spoken request via STT. Returns None on silence, an
    unrecognized phrase, or a service error — caller falls back to asking
    again rather than crashing the session over one bad audio capture.

    pause_threshold is set higher than the library default (0.8s) because
    the default was cutting students off mid-sentence — 1.4s gives a more
    natural amount of room for a pause without ending the phrase early.
    """
    recognizer.pause_threshold = 1.4
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print("\n🎤 Listening... (take your time, it waits for a real pause)")
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            print("No speech detected — try again.")
            return None
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Couldn't understand that — try again, speaking a bit slower.")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        return None


def confirm(prompt: str) -> bool:
    """Only exact positive tokens authorize; ambiguity and interruption cancel."""
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def get_macro_action(student_request: str) -> MacroAction:
    """Calls the cloud brain (Groq) and returns a validated MacroAction.

    This is a direct HTTP call rather than a persistent WebSocket — that's
    a deliberate simplification for now. Swapping this out for a real
    push-based connection later won't require changing execute_macro below.
    """
    api_key = os.environ["GROQ_API_KEY"]
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": student_request},
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return validate_execution(MacroAction.model_validate(data))


def _null_callout():
    """SolidWorks' SelectByID2 expects a specifically-typed null IDispatch
    pointer for its Callout argument. Passing plain Python None causes
    pywin32 to send the wrong VARIANT type, raising a COM 'Type mismatch'
    error on argument 8 — this wraps None as the correct VARIANT type."""
    return win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)


class SolidWorksDriver:
    """Executes SolidWorks actions via COM automation.

    Method names match SolidWorksActionType enum values exactly, so
    dispatch in execute_macro() can use getattr(driver, action.type.value)
    without a big if/elif chain.
    """

    def __init__(self):
        if win32com is None or pythoncom is None:
            raise RuntimeError("pywin32 is required on Windows to drive SolidWorks.")
        self.app = win32com.client.Dispatch("SldWorks.Application")
        self.app.Visible = True
        self._owned_document = None
        self._failed = False
        self._ensure_active_document()
        self._offset_planes = {}  # (base_plane, offset_mm) -> created plane feature name, so repeated requests for the same offset reuse one plane instead of creating duplicates

    def _ensure_active_document(self):
        """Create one unsaved part; refuse to adopt any existing document."""
        if self._owned_document is not None:
            return
        if self.app.ActiveDoc is not None:
            raise RuntimeError("Close existing SolidWorks documents before starting the disposable demo.")
        SW_DEFAULT_TEMPLATE_PART = 8
        template = self.app.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_PART)
        if not template:
            raise RuntimeError("No default SolidWorks part template is configured.")
        self._owned_document = self.app.NewDocument(template, 0, 0, 0)
        if self._owned_document is None:
            raise RuntimeError("Could not create a disposable SolidWorks part.")
        self.assert_execution_target()

    def assert_execution_target(self):
        """Check ownership before every action; uncertain identity fails closed."""
        if self._failed:
            raise RuntimeError("Demo interrupted or failed. Discard the unsaved part and restart.")
        doc = self._owned_document
        active = self.app.ActiveDoc
        # swObjectSame=1; swObjectUnsupported=2 must not be treated as truthy.
        if doc is None or active is None or self.app.IsSame(doc, active) != 1:
            raise RuntimeError("The disposable part is no longer active. Restart the demo.")
        if doc.GetPathName() or doc.GetType() != 1:
            raise RuntimeError("Execution requires Aya's unsaved disposable part.")

    def invalidate(self):
        self._failed = True

    @property
    def model(self):
        self.assert_execution_target()
        return self._owned_document

    def new_sketch(self, params: dict):
        plane = params.get("plane", "Front")
        offset_mm = params.get("offset_mm", 0)
        model = self.model
        if offset_mm:
            plane_name = self._get_or_create_offset_plane(plane, offset_mm)
            model.Extension.SelectByID2(plane_name, "PLANE", 0, 0, 0, False, 0, _null_callout(), 0)
        else:
            model.Extension.SelectByID2(f"{plane} Plane", "PLANE", 0, 0, 0, False, 0, _null_callout(), 0)
        model.SketchManager.InsertSketch(True)

    def _get_or_create_offset_plane(self, base_plane: str, offset_mm: float) -> str:
        """Creates a reference plane offset a fixed distance from a base
        plane (Front/Top/Right), so a second feature can be sketched
        coaxially against the end of a previous one — e.g. a bolt shaft
        starting exactly where the head extrude ends — instead of every
        sketch defaulting back to the origin and overlapping.

        NOTE: InsertRefPlane's reference-constraint constant (8 = distance
        offset) and FeatureByPositionReverse (grabbing the just-created
        feature by its position from the end of the tree) are both
        commonly documented patterns for SolidWorks COM automation, but
        the exact enum value can vary slightly by SolidWorks version —
        same category of thing as the SelectByID2 fix. If this raises a
        COM error, that argument number is the first place to look.
        """
        key = (base_plane, offset_mm)
        if key in self._offset_planes:
            return self._offset_planes[key]

        model = self.model
        model.Extension.SelectByID2(f"{base_plane} Plane", "PLANE", 0, 0, 0, False, 0, _null_callout(), 0)
        SW_REF_PLANE_DISTANCE = 8  # swRefPlaneReferenceConstraint_Distance
        model.FeatureManager.InsertRefPlane(SW_REF_PLANE_DISTANCE, offset_mm / 1000, 0, 0, 0, 0)
        new_plane_feature = model.FeatureManager.FeatureByPositionReverse(0)  # most recently created feature
        plane_name = new_plane_feature.Name
        self._offset_planes[key] = plane_name
        return plane_name

    def draw_rectangle(self, params: dict):
        x = params.get("x", 0) / 1000  # mm -> m (SolidWorks API units)
        y = params.get("y", 0) / 1000
        w = params["width"] / 1000
        h = params["height"] / 1000
        self.model.SketchManager.CreateCornerRectangle(x, y, 0, x + w, y + h, 0)

    def draw_line(self, params: dict):
        self.model.SketchManager.CreateLine(
            params["x1"] / 1000, params["y1"] / 1000, 0,
            params["x2"] / 1000, params["y2"] / 1000, 0,
        )

    def draw_circle(self, params: dict):
        self.model.SketchManager.CreateCircleByRadius(
            params.get("x", 0) / 1000, params.get("y", 0) / 1000, 0,
            params["radius"] / 1000,
        )

    def extrude(self, params: dict):
        model = self.model
        depth = params["depth"] / 1000
        model.SketchManager.InsertSketch(True)  # exit sketch before extruding
        model.FeatureManager.FeatureExtrusion2(
            True, False, False, 0, 0, depth, 0, False, False, False, False,
            0, 0, False, False, False, False, True, True, True, 0, 0, False,
        )

    def add_dimension(self, params: dict):
        raise NotImplementedError(
            "add_dimension needs entity-specific COM selection logic "
            "(which line/edge to dimension) — fill in once you hit a real case."
        )

    def fillet(self, params: dict):
        raise NotImplementedError(
            "fillet needs edge selection via params — fill in once you hit a real case."
        )

    def select_feature(self, params: dict):
        self.model.Extension.SelectByID2(params["name"], "BODYFEATURE", 0, 0, 0, False, 0, _null_callout(), 0)

    def save_file(self, params: dict):
        raise RuntimeError("Automatic saving is disabled for disposable demo parts.")

    def click_toolbar(self, params: dict):
        raise RuntimeError("Raw desktop clicks are disabled by local policy.")

    def feature_snapshot(self) -> list[tuple[str, str]]:
        """Read-only: (name, type) for every feature in the tree, e.g.
        ("Boss-Extrude1", "Extrusion"). Never changes the model."""
        out = []
        feature = self.model.FirstFeature()
        while feature is not None:
            try:
                type_name = feature.GetTypeName2()
            except Exception:
                type_name = "?"
            out.append((feature.Name, type_name))
            feature = feature.GetNextFeature()
        return out


# Feature type (as reported by SolidWorks' GetTypeName2) that each action is
# expected to add to the tree. Only actions that create a top-level feature are
# listed: drawing lines/rectangles inside an open sketch adds no feature.
# UNVERIFIED: "ProfileFeature" (sketch) and "Extrusion" (boss-extrude) are the
# documented type names; if a live run reports different names, the [verify]
# line prints the actual types so this table can be corrected.
EXPECTED_FEATURE_TYPES = {
    "new_sketch": "ProfileFeature",
    "extrude": "Extrusion",
}


def check_new_features(before, after, action_types):
    """Compares feature-tree snapshots taken before and after a macro.

    Returns (verified, detail):
      True  - every feature the macro should have created actually appeared
      False - at least one expected feature is missing
      None  - the macro has no action whose result shows up in the tree,
              so the tree can't confirm or deny it (e.g. only drew a line)
    """
    before_names = {name for name, _ in before}
    new = [(name, t) for name, t in after if name not in before_names]

    expected = [EXPECTED_FEATURE_TYPES[a] for a in action_types if a in EXPECTED_FEATURE_TYPES]
    if "extrude" in action_types:
        # An extrude absorbs its sketch in the tree, so only require the extrude.
        expected = [t for t in expected if t != "ProfileFeature"]

    new_desc = ", ".join(f"{n} ({t})" for n, t in new) or "none"
    if not expected:
        return None, f"nothing checkable in the feature tree; new features: {new_desc}"

    pool = [t for _, t in new]
    missing = []
    for t in expected:
        if t in pool:
            pool.remove(t)
        else:
            missing.append(t)
    if missing:
        return False, f"FAILED: expected {expected}, missing {missing}; new features: {new_desc}"
    return True, f"confirmed: {new_desc}"


def execute_generic_action(action_type: GenericActionType, params: dict):
    raise RuntimeError("Generic desktop control is disabled by local policy.")


STEP_DELAY_SECONDS = 0.8  # pause between actions so the student can actually watch, not just see a teleported result


def execute_macro(macro: MacroAction, sw_driver, canva_driver, tts_engine, ledger: Ledger):
    macro = validate_execution(macro)
    print(f"\nGoal: {macro.goal}")
    for action in macro.actions:
        print(f"  Proposed: {action.type.value}({action.params})")

    if macro.teaching.narration:
        speak(macro.teaching.narration, tts_engine)
    if macro.teaching.mode == TeachingMode.DEMONSTRATION and macro.teaching.correcting:
        speak(f"Allow me to demonstrate. {macro.teaching.correcting}", tts_engine)

    if not confirm("Approve this whole macro in an unsaved disposable part? [y/n]: "):
        print("Cancelled by student.")
        return sw_driver

    # Connecting and creating a document are also deferred until approval.
    if sw_driver is None:
        sw_driver = SolidWorksDriver()
    sw_driver.assert_execution_target()

    # Snapshot the feature tree first, so success is judged by what actually
    # appears in SolidWorks, not by whether the API calls happened to not throw.
    before = _safe_snapshot(sw_driver) if macro.tool == Tool.SOLIDWORKS else None

    try:
        _run_actions(macro, sw_driver, canva_driver)
        verified_ok = _verify_macro_result(macro, sw_driver, before)
    except (Exception, KeyboardInterrupt):
        sw_driver.invalidate()
        ledger.record_macro_actions(macro, verified=False)
        raise

    ledger.record_macro_actions(macro, verified=verified_ok)
    if verified_ok is False:
        sw_driver.invalidate()
    return sw_driver


def _verify_macro_result(macro, sw_driver, before):
    after = _safe_snapshot(sw_driver)
    if before is None or after is None:
        print("  [verify] Skipped: could not read the SolidWorks feature tree.")
        return None
    present, detail = check_new_features(before, after, [a.type.value for a in macro.actions])
    print(f"  [verify] {detail}")
    if macro.verification.expected:
        print(f"  [verify] Aya expected: {macro.verification.expected}")
    if present is True:
        print("  [verify] Feature presence only; dimensions and positioning are unverified.")
        return None
    return present


def _safe_snapshot(sw_driver):
    if sw_driver is None:
        return None
    try:
        return sw_driver.feature_snapshot()
    except Exception as e:
        print(f"  [verify] Could not read feature tree: {e}")
        return None


def _run_actions(macro: MacroAction, sw_driver, canva_driver):
    macro = validate_execution(macro)
    for action in macro.actions:
        if macro.tool == Tool.SOLIDWORKS:
            if sw_driver is None:
                raise RuntimeError("SolidWorks driver not initialized — check SolidWorks is installed correctly.")
            sw_driver.assert_execution_target()
            handler = getattr(sw_driver, action.type.value, None)
            if handler is None:
                raise NotImplementedError(f"No handler for SolidWorks action '{action.type.value}'")
            print(f"  → {action.type.value}({action.params})")
            try:
                handler(action.params)
            except KeyError as e:
                raise RuntimeError(
                    f"Action '{action.type.value}' is missing required parameter {e} — "
                    f"received params: {action.params}. The cloud brain likely used the "
                    f"wrong key name for this action."
                )
            except COM_ERROR as e:
                arg_num = e.args[3] if len(e.args) > 3 else "unknown"
                raise RuntimeError(
                    f"SolidWorks COM error on action '{action.type.value}' "
                    f"(params: {action.params}) — argument #{arg_num} caused a "
                    f"'{e.args[1] if len(e.args) > 1 else e}'. This usually means a "
                    f"None or wrongly-typed value was passed to that argument position."
                )
            # Redraw and pause so the student can actually watch the step happen,
            # instead of the whole macro teleporting to its final state.
            try:
                sw_driver.model.GraphicsRedraw2()
                if action.type.value in ("extrude", "draw_rectangle", "draw_circle"):
                    sw_driver.model.ViewZoomtofit2()  # re-frame after a visible geometry change
            except Exception:
                pass  # redraw/zoom failures shouldn't abort the actual build
            time.sleep(STEP_DELAY_SECONDS)


def main():
    print("Ayakha local driver — say or type a request. Type 'quit' anytime to exit.\n")

    print("Connected prototype: typed requests are sent to Groq; voice audio is sent to Google.")
    if not confirm("Consent to these connected data flows for this session? [y/n]: "):
        return
    sw_driver = None  # created only after an approved macro
    canva_driver = None  # preserved source; execution disabled

    tts_engine = pyttsx3.init() if pyttsx3 is not None else None
    if tts_engine is None:
        print("pyttsx3 not available — Aya's narration will print as text only, no voice.")

    ledger = Ledger(student_id=os.environ.get("AYAKHA_STUDENT", "demo_student"))

    voice_mode = False
    recognizer = microphone = None
    if sr is not None:
        answer = input("Use voice input? [y/n]: ").strip().lower()
        if answer == "y":
            try:
                recognizer = sr.Recognizer()
                microphone = sr.Microphone()
                voice_mode = True
            except Exception as e:
                print(f"Couldn't set up microphone ({e}). Falling back to typed input.")
    else:
        print("SpeechRecognition not available — using typed input only.")

    while True:
        if voice_mode:
            request = listen_for_request(recognizer, microphone)
            if request is None:
                continue
        else:
            request = input("\nYou: ").strip()

        if request.lower() in ("quit", "exit"):
            break
        if not request:
            continue

        if any(phrase in request.lower() for phrase in TAKEOVER_PHRASES):
            takeover_intent = True
        else:
            takeover_intent = False

        try:
            macro = get_macro_action(request)
        except ValidationError as e:
            print(f"Cloud brain returned invalid MacroAction: {e}")
            continue
        except Exception as e:
            print(f"Error calling cloud brain: {e}")
            continue

        ledger.start_session(tool=macro.tool.value, request=request)
        if takeover_intent:
            speak(ledger.request_full_takeover(), tts_engine)

        try:
            sw_driver = execute_macro(macro, sw_driver, canva_driver, tts_engine, ledger)
        except KeyboardInterrupt:
            print("Interrupted. Discard the unsaved demo part before restarting.")
            break
        except Exception as e:
            print(f"Execution error: {e}")
        finally:
            ledger.end_session()
            speak(ledger.session_summary_spoken(), tts_engine)
            report_path = ledger.export_markdown()
            print(f"[ledger] progress report → {report_path}")


if __name__ == "__main__":
    main()
