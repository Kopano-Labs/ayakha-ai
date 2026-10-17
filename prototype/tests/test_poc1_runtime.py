"""POC-1 tests for the local Aya input-to-design-brief vertical slice."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from aya_runtime import DeterministicPlanner, write_design_brief  # noqa: E402


@pytest.fixture
def cars4mars_fixture():
    return json.loads(
        (REPOSITORY_ROOT / "fixtures" / "cars4mars_motor_mount.json").read_text(encoding="utf-8")
    )


def test_cars4mars_request_returns_canonical_clarification_intent(cars4mars_fixture):
    intent = DeterministicPlanner().plan(cars4mars_fixture["request"])

    assert set(intent.model_dump()) == {
        "mode", "problem", "user_or_context", "desired_outcome", "constraints",
        "known_requirements", "missing_requirements", "assumptions", "questions",
        "proposed_action", "target_tool", "confidence", "requires_confirmation",
    }
    assert intent.mode == "clarify"
    assert intent.missing_requirements == cars4mars_fixture["expected_missing_requirements"]
    assert len(intent.questions) == len(intent.missing_requirements)
    assert intent.proposed_action is None
    assert intent.target_tool is None
    assert intent.requires_confirmation is True


def test_complete_local_request_can_progress_to_a_brief_without_connectors():
    request = (
        "Design an 80 mm x 50 mm motor mount for a 42 mm motor with a 31 mm bolt pattern "
        "and four M3 mounting holes. Use PETG. It carries a 1.2 kg load with a safety factor "
        "of 2 and must fit a 220 mm x 220 mm x 250 mm printer build volume."
    )

    intent = DeterministicPlanner().plan(request)

    assert intent.mode == "brief"
    assert intent.missing_requirements == []
    assert intent.questions == []
    assert intent.proposed_action is None
    assert intent.target_tool is None


def test_editable_brief_records_questions_and_external_action_boundary(tmp_path, cars4mars_fixture):
    intent = DeterministicPlanner().plan(cars4mars_fixture["request"])
    brief_path = write_design_brief(intent, tmp_path / "design-brief.md")
    brief = brief_path.read_text(encoding="utf-8")

    assert "This local Markdown file is editable." in brief
    assert "What are the motor body, shaft, and mounting-face dimensions" in brief
    assert "No external action has been proposed or executed in POC-1." in brief


def test_local_development_shell_reports_status_and_writes_brief(tmp_path, cars4mars_fixture):
    output = tmp_path / "brief.md"
    result = subprocess.run(
        [
            sys.executable, "-m", "aya_runtime", "brief", "--request",
            cars4mars_fixture["request"], "--output", str(output),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "Aya runtime: READY" in result.stdout
    assert '"mode": "clarify"' in result.stdout
    assert "External actions: none proposed or executed." in result.stdout
    assert output.exists()
