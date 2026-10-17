"""Deterministic local planning for the POC-1 input-to-brief loop.

This adapter deliberately makes no network, provider, CAD, Canva, browser, or
operating-system automation calls.  It is an explainable fallback while a
separately scoped local model adapter is evaluated.
"""

from __future__ import annotations

import re

from .models import DesignIntent


MATERIAL_WORDS = {"abs", "aluminium", "aluminum", "nylon", "petg", "pla", "steel", "tpu"}


class DeterministicPlanner:
    """Turn a text request into the truth-lock intent shape without guessing."""

    def plan(self, request: str) -> DesignIntent:
        cleaned_request = " ".join(request.split())
        if not cleaned_request:
            raise ValueError("A design request is required.")

        lowered = cleaned_request.lower()
        constraints = self._constraints(lowered)
        missing_requirements, questions = self._clarifications(lowered)
        known_requirements = [
            item for item in constraints if item not in {"printer volume", "material"}
        ]
        confidence = 0.3 + 0.14 * (5 - len(missing_requirements))

        return DesignIntent(
            mode="clarify" if missing_requirements else "brief",
            problem=self._problem(lowered),
            user_or_context="Cars4Mars student rover project" if "cars4mars" in lowered else "student design project",
            desired_outcome="An explainable, printable motor-mount design brief" if "motor mount" in lowered else "An explainable design brief",
            constraints=constraints,
            known_requirements=known_requirements,
            missing_requirements=missing_requirements,
            assumptions=[],
            questions=questions,
            proposed_action=None,
            target_tool=None,
            confidence=round(confidence, 2),
            requires_confirmation=True,
        )

    @staticmethod
    def _problem(request: str) -> str:
        if "motor mount" in request:
            return "Create a motor mount that fits the rover motor and can be explained by a student."
        return "Clarify the student's design request before proposing a design brief."

    @staticmethod
    def _constraints(request: str) -> list[str]:
        constraints: list[str] = []
        if "fit" in request and "motor" in request:
            constraints.append("fit the motor")
        if "vibration" in request:
            constraints.append("survive vibration")
        if "printer" in request and "volume" in request:
            constraints.append("printer volume")
        if "student" in request and ("explain" in request or "explanation" in request):
            constraints.append("easy for a student to explain")
        return constraints

    @staticmethod
    def _clarifications(request: str) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        questions: list[str] = []

        if not re.search(r"\b\d+(?:\.\d+)?\s*(?:mm|cm|in|inch(?:es)?)\b", request):
            missing.append("motor dimensions")
            questions.append("What are the motor body, shaft, and mounting-face dimensions in millimetres?")

        if not any(marker in request for marker in ("bolt pattern", "mounting hole", "m3", "m4", "hole spacing")):
            missing.append("mounting interface and bolt pattern")
            questions.append("What bolt pattern, hole size, and mounting interface must the motor mount use?")

        if not any(re.search(rf"\b{re.escape(material)}\b", request) for material in MATERIAL_WORDS):
            missing.append("material")
            questions.append("Which material and print orientation are available for this part?")

        if not ("safety factor" in request or ("load" in request and re.search(r"\d", request))):
            missing.append("load and safety requirements")
            questions.append("What vibration or load profile and safety factor must the mount withstand?")

        has_printer_dimensions = bool(
            re.search(r"\d+(?:\.\d+)?\s*(?:mm|cm|in).*\b(?:printer|build volume)\b", request)
            or re.search(r"\b(?:printer|build volume).*\d+(?:\.\d+)?\s*(?:mm|cm|in)", request)
        )
        if not has_printer_dimensions:
            missing.append("printer build limits")
            questions.append("What are the printer build dimensions, nozzle limits, and minimum wall thickness?")

        return missing, questions
