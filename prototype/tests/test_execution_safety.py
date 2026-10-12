"""Offline boundary tests: no COM, network, browser or desktop input needed."""
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ayakha_local_driver as driver
from execution_policy import validate_execution
from macro_action_schema import MacroAction
from test_verification import FakeSolidWorks, plate_macro, verified_values
from ayakha_ledger import Ledger


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "STEP_DELAY_SECONDS", 0)
    led = Ledger("safety", tmp_path / "ledger.db")
    led.start_session("solidworks", "make plate")
    yield led
    led.db.close()


@pytest.mark.parametrize("answer", ["maybe", "probably", "not yes", "deny", "n", "no", "", "y please"])
def test_ambiguous_confirmation_cancels(answer, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert driver.confirm("approve?") is False


@pytest.mark.parametrize("answer", ["y", "yes", " YES "])
def test_exact_confirmation_accepts(answer, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert driver.confirm("approve?") is True


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_interrupted_confirmation_cancels(error, monkeypatch):
    def interrupted(_):
        raise error()
    monkeypatch.setattr("builtins.input", interrupted)
    assert driver.confirm("approve?") is False


def test_false_confirmation_rejected_by_schema_and_runtime(monkeypatch, ledger):
    data = plate_macro().model_dump()
    data["requires_confirmation"] = False
    with pytest.raises(ValidationError):
        MacroAction.model_validate(data)
    forged = plate_macro().model_copy(update={"requires_confirmation": False})
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("must reject before prompting"))
    sw = FakeSolidWorks()
    with pytest.raises(ValidationError):
        driver.execute_macro(forged, sw, None, None, ledger)
    assert len(sw.tree) == 2
    assert verified_values(ledger) == []


@pytest.mark.parametrize("tool,action", [("generic", "click_at"), ("canva", "add_text"),
    ("solidworks", "click_toolbar"), ("solidworks", "save_file"),
    ("solidworks", "fillet"), ("solidworks", "add_dimension"), ("solidworks", "select_feature")])
def test_disabled_actions_rejected_before_any_mutation(tool, action, monkeypatch, ledger):
    data = plate_macro().model_dump()
    data["tool"] = tool
    if tool == "solidworks":
        data["actions"].append({"type": action, "params": {}})
    if tool != "solidworks":
        data["actions"] = [{"type": action, "params": {}}]
    macro = MacroAction.model_validate(data)
    sw = FakeSolidWorks()
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("must reject before prompting"))
    with pytest.raises(ValueError):
        driver.execute_macro(macro, sw, None, None, ledger)
    assert len(sw.tree) == 2
    assert verified_values(ledger) == []


def test_mixed_tool_action_rejected():
    data = plate_macro().model_dump()
    data["actions"].append({"type": "key_press", "params": {"key": "enter"}})
    with pytest.raises(ValidationError, match="target tool"):
        MacroAction.model_validate(data)


@pytest.mark.parametrize("params", [{"depth": -1}, {"depth": 0}, {"depth": float("nan")},
    {"depth": float("inf")}, {"depth": 1001}, {"depth": "10"}, {"depth": True},
    {}, {"depth": 10, "path": "student.sldprt"}])
def test_bad_late_parameters_reject_entire_macro(params):
    macro = plate_macro()
    macro.actions[-1].params = params
    with pytest.raises(ValueError):
        validate_execution(macro)


def test_cancellation_does_not_connect_or_write(monkeypatch, ledger):
    monkeypatch.setattr("builtins.input", lambda _: "maybe")
    monkeypatch.setattr(driver, "SolidWorksDriver", lambda: pytest.fail("connection before consent"))
    assert driver.execute_macro(plate_macro(), None, None, None, ledger) is None
    assert verified_values(ledger) == []


class FakeDoc:
    def __init__(self, path="", kind=1):
        self.path, self.kind = path, kind

    def GetPathName(self):
        return self.path

    def GetType(self):
        return self.kind


class FakeApp:
    def __init__(self, active=None):
        self.ActiveDoc = active
        self.created = 0
        self.equality = None

    def GetUserPreferenceStringValue(self, _):
        return "part-template"

    def NewDocument(self, *args):
        self.created += 1
        self.ActiveDoc = FakeDoc()
        return self.ActiveDoc

    def IsSame(self, a, b):
        return self.equality if self.equality is not None else int(a is b)


def owned_driver(app):
    sw = driver.SolidWorksDriver.__new__(driver.SolidWorksDriver)
    sw.app, sw._owned_document, sw._failed = app, None, False
    return sw


def test_existing_document_is_never_adopted():
    app = FakeApp(FakeDoc("student.sldprt"))
    sw = owned_driver(app)
    with pytest.raises(RuntimeError, match="existing"):
        sw._ensure_active_document()
    assert app.created == 0


@pytest.mark.parametrize("change", ["switch", "close", "save", "assembly", "unsupported", "failed"])
def test_owned_document_guard_fails_closed(change):
    app = FakeApp()
    sw = owned_driver(app)
    sw._ensure_active_document()
    assert sw.model is app.ActiveDoc
    if change == "switch": app.ActiveDoc = FakeDoc()
    if change == "close": app.ActiveDoc = None
    if change == "save": app.ActiveDoc.path = "student.sldprt"
    if change == "assembly": app.ActiveDoc.kind = 2
    if change == "unsupported": app.equality = 2
    if change == "failed": sw.invalidate()
    with pytest.raises(RuntimeError):
        _ = sw.model
    assert app.created == 1  # closed/switched docs are never silently replaced


def test_document_switch_mid_macro_stops_later_actions(monkeypatch, ledger):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    class SwitchingDriver(FakeSolidWorks):
        switched = False
        def new_sketch(self, params):
            super().new_sketch(params)
            self.switched = True
        def assert_execution_target(self):
            if self.switched:
                raise RuntimeError("target switched")
        def draw_rectangle(self, params):
            pytest.fail("must stop before second action")
    sw = SwitchingDriver()
    with pytest.raises(RuntimeError, match="target switched"):
        driver.execute_macro(plate_macro(), sw, None, None, ledger)
    assert sw.invalidated
    assert all(v == 0 for v in verified_values(ledger))


def test_keyboard_interrupt_invalidates_partial_part(monkeypatch, ledger):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    class InterruptedDriver(FakeSolidWorks):
        def extrude(self, params):
            raise KeyboardInterrupt()
    sw = InterruptedDriver()
    with pytest.raises(KeyboardInterrupt):
        driver.execute_macro(plate_macro(), sw, None, None, ledger)
    assert sw.invalidated
    assert all(v == 0 for v in verified_values(ledger))


def test_unknown_snapshot_cannot_establish_progress(monkeypatch, ledger):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    class UnreadableDriver(FakeSolidWorks):
        def feature_snapshot(self):
            raise RuntimeError("unreadable")
    driver.execute_macro(plate_macro(), UnreadableDriver(), None, None, ledger)
    assert all(v is None for v in verified_values(ledger))
    assert ledger.skill_status() == []


def test_interrupt_during_verification_invalidates_part(monkeypatch, ledger):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    class InterruptedSnapshot(FakeSolidWorks):
        calls = 0
        def feature_snapshot(self):
            self.calls += 1
            if self.calls == 2:
                raise KeyboardInterrupt()
            return super().feature_snapshot()
    sw = InterruptedSnapshot()
    with pytest.raises(KeyboardInterrupt):
        driver.execute_macro(plate_macro(), sw, None, None, ledger)
    assert sw.invalidated
    assert all(v == 0 for v in verified_values(ledger))


@pytest.mark.parametrize("count", [0, 51])
def test_empty_and_oversized_plans_rejected(count):
    data = plate_macro().model_dump()
    data["actions"] = [data["actions"][0]] * count
    with pytest.raises(ValidationError):
        MacroAction.model_validate(data)


def test_startup_rejects_connected_flows_before_side_effects(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "no")
    monkeypatch.setattr(driver, "Ledger", lambda **_: pytest.fail("must stop before ledger creation"))
    monkeypatch.setattr(driver, "SolidWorksDriver", lambda: pytest.fail("must stop before COM connection"))
    driver.main()


def test_raw_desktop_and_save_entry_points_are_disabled():
    with pytest.raises(RuntimeError, match="disabled"):
        driver.execute_generic_action(None, {})
    sw = driver.SolidWorksDriver.__new__(driver.SolidWorksDriver)
    with pytest.raises(RuntimeError, match="disabled"):
        sw.click_toolbar({"x": 1, "y": 2})
    with pytest.raises(RuntimeError, match="disabled"):
        sw.save_file({})
