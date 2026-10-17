"""Editable local Markdown design briefs for POC-1."""

from __future__ import annotations

from pathlib import Path

from .models import DesignIntent


def _items(items: list[str], empty: str = "None recorded.") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def render_design_brief(intent: DesignIntent) -> str:
    """Render an intentionally editable brief without initiating any connector."""

    return f"""# Aya design brief

> This local Markdown file is editable. Correct it as the student supplies evidence.

## Request interpretation

**Problem:** {intent.problem}

**Context:** {intent.user_or_context}

**Desired outcome:** {intent.desired_outcome}

**Planner mode:** {intent.mode}

**Interpretation confidence:** {intent.confidence:.2f}

## Known constraints

{_items(intent.constraints)}

## Known requirements

{_items(intent.known_requirements)}

## Missing requirements

{_items(intent.missing_requirements)}

## Clarifying questions

{_items(intent.questions)}

## Student edits and answers

- Add confirmed dimensions, material, interface, load, safety, and printer information here.

## External-tool boundary

No external action has been proposed or executed in POC-1. Canva and SolidWorks
remain separate, approval-gated connector issues.
"""


def write_design_brief(intent: DesignIntent, output_path: str | Path) -> Path:
    """Write the editable local brief and return its resolved path."""

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_design_brief(intent), encoding="utf-8")
    return path.resolve()
