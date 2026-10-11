"""
Verification and ledger tests that run without SolidWorks.

A fake driver stands in for SolidWorks: its handlers append to a fake feature
tree the way the real model would (or deliberately don't, to simulate a step
that "succeeds" without producing anything).

Run from the prototype folder:  python -m pytest tests -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ayakha_ledger import Ledger  # noqa: E402
from ayakha_local_driver import check_new_features, execute_macro  # noqa: E402
from macro_action_schema import (  # noqa: E402
    MacroAction, SolidWorksAction, SolidWorksActionType, Teaching, TeachingMode, Tool,
)


class FakeSolidWorks:
    """Mimics SolidWorksDriver's interface with an in-memory feature tree."""

    def __init__(self, extrude_works=True, crash_on=None):
        self.tree = [("Origin", "OriginProfileFeature"), ("Front Plane", "RefPlane")]
        self.extrude_works = extrude_works
        self.crash_on = crash_on
        self._n = 0
        self.model = self  # execute_macro calls model.GraphicsRedraw2()/ViewZoomtofit2()

    def GraphicsRedraw2(self):
        pass

    def ViewZoomtofit2(self):
        pass

    def feature_snapshot(self):
        return list(self.tree)

    def _maybe_crash(self, name):
        if self.crash_on == name:
            raise RuntimeError(f"simulated failure in {name}")

    def new_sketch(self, params):
        self._maybe_crash("new_sketch")
        self._n += 1
        self.tree.append((f"Sketch{self._n}", "ProfileFeature"))

    def draw_rectangle(self, params):
        self._maybe_crash("draw_rectangle")

    def extrude(self, params):
        self._maybe_crash("extrude")
        if self.extrude_works:
            self.tree.append((f"Boss-Extrude{self._n}", "Extrusion"))


def plate_macro(mode=TeachingMode.NARRATED):
    return MacroAction(
        macro_id="m1", tool=Tool.SOLIDWORKS, goal="100x50 plate, 10 mm thick",
        actions=[
            SolidWorksAction(type=SolidWorksActionType.NEW_SKETCH, params={"plane": "Front"}),
            SolidWorksAction(type=SolidWorksActionType.DRAW_RECTANGLE,
                             params={"x": 0, "y": 0, "width": 100, "height": 50}),
            SolidWorksAction(type=SolidWorksActionType.EXTRUDE, params={"depth": 10}),
        ],
        teaching=Teaching(mode=mode, narration=None),
        requires_confirmation=False,
    )


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr("ayakha_local_driver.STEP_DELAY_SECONDS", 0)
    led = Ledger(student_id="test", db_path=tmp_path / "ledger.db")
    led.start_session("solidworks", "make a plate")
    return led


def verified_values(led):
    return [v for (v,) in led.db.execute("SELECT verified FROM events").fetchall()]


# ---- check_new_features: pure logic -------------------------------------------------

def test_extrude_confirmed_when_extrusion_appears():
    before = [("Origin", "OriginProfileFeature")]
    after = before + [("Sketch1", "ProfileFeature"), ("Boss-Extrude1", "Extrusion")]
    ok, detail = check_new_features(before, after, ["new_sketch", "draw_rectangle", "extrude"])
    assert ok is True, detail


def test_extrude_fails_when_nothing_appears():
    before = [("Origin", "OriginProfileFeature")]
    ok, detail = check_new_features(before, list(before), ["new_sketch", "extrude"])
    assert ok is False
    assert "Extrusion" in detail


def test_sketch_left_unextruded_still_fails_an_extrude():
    before = [("Origin", "OriginProfileFeature")]
    after = before + [("Sketch1", "ProfileFeature")]
    ok, _ = check_new_features(before, after, ["new_sketch", "extrude"])
    assert ok is False


def test_two_extrudes_need_two_extrusions():
    before = []
    after = [("Boss-Extrude1", "Extrusion")]
    ok, _ = check_new_features(before, after, ["new_sketch", "extrude", "new_sketch", "extrude"])
    assert ok is False


def test_drawing_inside_a_sketch_is_not_checkable():
    ok, _ = check_new_features([("Sketch1", "ProfileFeature")],
                               [("Sketch1", "ProfileFeature")], ["draw_line"])
    assert ok is None


# ---- execute_macro + ledger: end to end with the fake driver ---------------------------

def test_successful_build_is_recorded_as_confirmed(ledger):
    execute_macro(plate_macro(), FakeSolidWorks(), None, None, ledger)
    assert verified_values(ledger) and all(v == 1 for v in verified_values(ledger))


def test_build_that_silently_produces_nothing_is_recorded_as_failed(ledger):
    execute_macro(plate_macro(), FakeSolidWorks(extrude_works=False), None, None, ledger)
    assert verified_values(ledger) and all(v == 0 for v in verified_values(ledger))
    assert ledger.skill_status() == []  # failed steps don't count as practice
    assert "didn't" in ledger.session_summary_spoken()


def test_crash_mid_macro_is_recorded_as_failed_and_reraised(ledger):
    with pytest.raises(RuntimeError, match="simulated failure"):
        execute_macro(plate_macro(), FakeSolidWorks(crash_on="extrude"), None, None, ledger)
    assert verified_values(ledger) and all(v == 0 for v in verified_values(ledger))


def test_failed_demonstration_does_not_count_as_shown(ledger):
    execute_macro(plate_macro(TeachingMode.DEMONSTRATION),
                  FakeSolidWorks(extrude_works=False), None, None, ledger)
    assert all(s.demonstrated == 0 for s in ledger.skill_status())


def test_report_counts_failed_steps_separately(ledger, tmp_path):
    execute_macro(plate_macro(), FakeSolidWorks(), None, None, ledger)
    execute_macro(plate_macro(), FakeSolidWorks(extrude_works=False), None, None, ledger)
    report = ledger.export_markdown(tmp_path / "report.md").read_text(encoding="utf-8")
    assert "failed (excluded from the table above): 3" in report
    assert "Steps confirmed in the tool: 3" in report
