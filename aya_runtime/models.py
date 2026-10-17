"""The canonical POC-1 intent object from the MVP truth lock."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DesignIntent(BaseModel):
    """A local interpretation of a design request, before any tool action."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["clarify", "brief", "edit"]
    problem: str
    user_or_context: str
    desired_outcome: str
    constraints: list[str] = Field(default_factory=list)
    known_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    proposed_action: str | None = None
    target_tool: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_confirmation: Literal[True] = True
