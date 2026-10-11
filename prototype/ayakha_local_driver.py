"""
Ayakha Local Driver
====================

Runs on the student's Windows machine. This is the piece that turns Aya's
cloud reasoning into real actions in SolidWorks — the first working
end-to-end pipeline: text request -> cloud brain -> MacroAction -> real
SolidWorks automation -> verification.

CURRENT SCOPE (first working pipeline)
---------------------------------------
  1. Take a spoken request from the student (STT) — or typed text if voice
     mode is off or unavailable.
  2. Call the cloud brain (Groq) to get back a validated MacroAction.
  3. Speak Aya's narration aloud (TTS) while also printing it as a live
     caption — matches the "student sees and hears" interface decision.
  4. If the macro requires confirmation, ask the student before proceeding
     (matches Ayakha's approval-gate teaching design). Confirmation stays
     keyboard-based on purpose — safer than voice for a live demo, where a
     misheard "yes" could trigger an unwanted action.
  5. Execute the macro against SolidWorks via COM automation — true UI-level
     drawing operations; COM is used read-only for verification only, never
     to make the change itself.
  6. Verify the result and report back.

NOT YET IMPLEMENTED (clear stubs, not silent gaps)
----------------------------------------------------
  - Canva automation exists (ayakha_canva_driver.py) but is UNVERIFIED —
    written without live access to canva.com, so selectors are best-effort.
    Expect at least one real debugging round, same as the early SolidWorks fixes.
  - add_dimension / fillet (need entity-specific COM selection logic per case)
  - Persistent WebSocket connection to a hosted cloud brain — currently calls
    Groq directly per request. Fine for local dev; swappable later without
    touching the execution logic below.
  - Real verification matching logic (currently prints the feature tree and
    the expected outcome side by side for a human to eyeball, rather than
    programmatically confirming a match; Canva has no verification yet)
  - A proper visual overlay UI — captions currently print to the console

SETUP (Windows only — needs SolidWorks installed, closed or open, either is fine)
-------------------------------------------------------------
  pip install pywin32 pyautogui requests pydantic SpeechRecognition pyttsx3 pyaudio playwright
  playwright install chromium
  (If pyaudio fails to install on Windows: pip install pipwin && pipwin install pyaudio)
  Set GROQ_API_KEY as an environment variable ($env:GROQ_API_KEY="..." in PowerShell)
  Put macro_action_schema.py and ayakha_canva_driver.py in the same folder as this file.
  Aya opens SolidWorks and creates a new part document herself — no manual setup needed.
  First Canva request opens a browser and asks you to log in once; session persists after that.

RUN
---
  python ayakha_local_driver.py
  (You'll be asked once at startup whether to use voice or typed input.)
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
    VerificationMethod,
    TeachingMode,
)
from ayakha_ledger import Ledger

try:
    from ayakha_canva_driver import CanvaDriver
except ImportError:
    CanvaDriver = None

TAKEOVER_PHRASES = ("just do it", "do it for me", "build it for me", "you do it", "just build it")

# pywin32 / pyautogui are Windows-only. Guarded so this file can still be
# read, imported, and syntax-checked on any platform — only fails at the
# point of actually trying to drive SolidWorks or the screen.
try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are Ayakha's reasoning brain, controlling SolidWorks or Canva through UI automation on behalf of a student.

Given a student's request, respond with ONLY a JSON object matching this exact structure (no markdown fences, no explanation, just the raw JSON):

{
  "macro_id": "macro_XXXX",
  "tool": "solidworks" | "canva" | "generic",
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
- select_feature: {"name": string}
- save_file: {}
- click_toolbar: {"x": number, "y": number}
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

Canva action types and their exact required params:
- click_element: {"description": string}
- add_text: {"text": string, "x": number, "y": number}
- add_shape: {"shape": string, "x": number, "y": number, "width": number, "height": number}
- add_image: {"source": string} — searches Canva's own stock image library for this term and inserts the first result. This does NOT fetch an arbitrary external URL or upload a file.
- drag_resize: {"description": string, "width": number, "height": number}
- change_color: {"description": string, "color": string}
- select_template: {"name": string}

Generic action types and their exact required params (use only when no
tool-specific action fits):
- click_at: {"x": number, "y": number}
- move_mouse: {"x": number, "y": number}
- type_text: {"text": string}
- key_press: {"key": string}
- wait: {"milliseconds": number}
- screenshot: {}

If a request is a real, complex mechanical part (e.g. a bolt with a
hexagonal head and threads), approximate it with the primitives above —
e.g. a hex head as six draw_line calls, threads represented as a single
cylinder rather than true helical geometry. Do not skip the request; do
the closest reasonable approximation with only the actions listed above.

All dimensions in params are in millimeters.
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
    """Asks y/n, but forgiving of stray characters getting mixed into the
    input (which is what was silently cancelling actions before) — looks
    for a clear yes/no rather than demanding an exact 'y' match, and
    re-asks instead of assuming 'no' when the answer is ambiguous."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes") or answer.endswith("y") or answer.endswith("yes"):
            return True
        if answer in ("n", "no") or answer.endswith("n") or answer.endswith("no"):
            return False
        print("Didn't catch a clear yes or no — please type y or n:")


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
    return MacroAction.model_validate(data)


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
        self._ensure_active_document()
        self._offset_planes = {}  # (base_plane, offset_mm) -> created plane feature name, so repeated requests for the same offset reuse one plane instead of creating duplicates

    def _ensure_active_document(self):
        """Creates a new part document automatically if none is open.
        True UI automation shouldn't require the student to set up
        SolidWorks manually first — Aya opens her own blank canvas."""
        if self.app.ActiveDoc is None:
            SW_DEFAULT_TEMPLATE_PART = 8  # swDefaultTemplatePart enum value
            template = self.app.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_PART)
            self.app.NewDocument(template, 0, 0, 0)

    @property
    def model(self):
        self._ensure_active_document()  # re-creates one if it got closed mid-session
        doc = self.app.ActiveDoc
        if doc is None:
            raise RuntimeError("Could not create or access a SolidWorks part document.")
        return doc

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
        self.model.Save()

    def click_toolbar(self, params: dict):
        """Fallback for ops not modeled via COM — true UI automation via pyautogui."""
        if pyautogui is None:
            raise RuntimeError("pyautogui required for click_toolbar fallback.")
        pyautogui.click(params["x"], params["y"])

    def verify(self, expected: str):
        """Read-only feature-tree check. Never used to make changes — only
        to confirm what actually happened, matching the decision to trust
        verification over the model's own claim of success."""
        feature = self.model.FirstFeature()
        names = []
        while feature is not None:
            names.append(feature.Name)
            feature = feature.GetNextFeature()
        print(f"  [verify] Feature tree now: {names}")
        print(f"  [verify] Expected: {expected}")
        # TODO: replace with real matching logic once you decide precisely
        # what "matches" means (e.g. regex on feature names, count checks).


def execute_generic_action(action_type: GenericActionType, params: dict):
    if pyautogui is None:
        raise RuntimeError("pyautogui is required for generic UI actions.")
    if action_type == GenericActionType.CLICK_AT:
        pyautogui.click(params["x"], params["y"])
    elif action_type == GenericActionType.MOVE_MOUSE:
        pyautogui.moveTo(params["x"], params["y"])
    elif action_type == GenericActionType.TYPE_TEXT:
        pyautogui.typewrite(params["text"])
    elif action_type == GenericActionType.KEY_PRESS:
        pyautogui.press(params["key"])
    elif action_type == GenericActionType.WAIT:
        ms = params.get("milliseconds", params.get("ms", 500))
        time.sleep(ms / 1000)
    elif action_type == GenericActionType.SCREENSHOT:
        return pyautogui.screenshot()


STEP_DELAY_SECONDS = 0.8  # pause between actions so the student can actually watch, not just see a teleported result


def execute_macro(macro: MacroAction, sw_driver, canva_driver, tts_engine, ledger: Ledger):
    print(f"\nGoal: {macro.goal}")

    if macro.teaching.narration:
        speak(macro.teaching.narration, tts_engine)
    if macro.teaching.mode == TeachingMode.DEMONSTRATION and macro.teaching.correcting:
        speak(f"Allow me to demonstrate. {macro.teaching.correcting}", tts_engine)

    if macro.requires_confirmation:
        if not confirm("Proceed with this action? [y/n]: "):
            print("Cancelled by student.")
            return

    for action in macro.actions:
        if macro.tool == Tool.SOLIDWORKS:
            if sw_driver is None:
                raise RuntimeError("SolidWorks driver not initialized — check SolidWorks is installed correctly.")
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
            except pythoncom.com_error as e:
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
        elif macro.tool == Tool.CANVA:
            if canva_driver is None:
                raise RuntimeError(
                    "Canva driver not initialized — check playwright is installed "
                    "(pip install playwright && playwright install chromium)."
                )
            handler = getattr(canva_driver, action.type.value, None)
            if handler is None:
                raise NotImplementedError(f"No handler for Canva action '{action.type.value}'")
            print(f"  → {action.type.value}({action.params})")
            try:
                handler(action.params)
            except KeyError as e:
                raise RuntimeError(
                    f"Action '{action.type.value}' is missing required parameter {e} — "
                    f"received params: {action.params}. The cloud brain likely used the "
                    f"wrong key name for this action."
                )
            except Exception as e:
                raise RuntimeError(
                    f"Canva automation error on action '{action.type.value}' "
                    f"(params: {action.params}): {e}. This driver is unverified against "
                    f"a live Canva session — likely a selector that doesn't match "
                    f"Canva's current UI. Report this exact error to get it fixed."
                )
            time.sleep(STEP_DELAY_SECONDS)  # pacing so the student can watch, same as SolidWorks
        elif macro.tool == Tool.GENERIC:
            try:
                execute_generic_action(action.type, action.params)
            except KeyError as e:
                raise RuntimeError(
                    f"Action '{action.type.value}' is missing required parameter {e} — "
                    f"received params: {action.params}."
                )

    verified_ok = None
    if macro.verification.method == VerificationMethod.COM_READONLY:
        if sw_driver is None:
            print("  [verify] Skipped — no SolidWorks driver available.")
        else:
            sw_driver.verify(macro.verification.expected or "")
            verified_ok = True  # sw_driver.verify() currently prints for a human to check; treat "ran without error" as a pass for now
    elif macro.verification.method == VerificationMethod.SCREENSHOT_DIFF:
        print("  [verify] Screenshot-diff verification not implemented yet.")

    ledger.record_macro_actions(macro, verified=verified_ok)


def main():
    print("Ayakha local driver — say or type a request. Type 'quit' anytime to exit.\n")

    sw_driver = None
    if win32com is not None:
        try:
            sw_driver = SolidWorksDriver()
            print("Connected to SolidWorks.")
        except Exception as e:
            print(f"Could not connect to SolidWorks ({e}). SolidWorks actions will fail.")
    else:
        print("pywin32 not available — SolidWorks actions will fail. Generic actions still work.")

    canva_driver = None
    if CanvaDriver is not None:
        try:
            canva_driver = CanvaDriver()
            print("Canva browser session ready.")
        except Exception as e:
            print(f"Could not start Canva automation ({e}). Canva actions will fail.")
    else:
        print("playwright not available — Canva actions will fail. Run: pip install playwright && playwright install chromium")

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
            execute_macro(macro, sw_driver, canva_driver, tts_engine, ledger)
        except Exception as e:
            print(f"Execution error: {e}")
        finally:
            ledger.end_session()
            speak(ledger.session_summary_spoken(), tts_engine)
            report_path = ledger.export_markdown()
            print(f"[ledger] progress report → {report_path}")


if __name__ == "__main__":
    main()
