"""Local development shell for Aya's POC-1 input-to-brief loop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .brief import write_design_brief
from .planner import DeterministicPlanner


RUNTIME_STATUS = "Aya runtime: READY - local deterministic planner; external actions disabled."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local Aya POC-1 input-to-brief loop.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("status", help="show local runtime status")

    brief = subcommands.add_parser("brief", help="turn a text request into intent JSON and an editable brief")
    brief.add_argument("--request", required=True, help="student design request")
    brief.add_argument("--output", default="aya-workspace/design-brief.md", help="local Markdown brief path")

    interactive = subcommands.add_parser("interactive", help="read text requests until the student exits")
    interactive.add_argument("--workspace", default="aya-workspace", help="local folder for the editable brief")
    return parser


def _create_brief(request: str, output: str | Path) -> None:
    intent = DeterministicPlanner().plan(request)
    path = write_design_brief(intent, output)
    print(RUNTIME_STATUS)
    print("\nCaptured intent JSON:")
    print(json.dumps(intent.model_dump(), indent=2))
    print(f"\nEditable brief: {path}")
    print("External actions: none proposed or executed.")


def run_interactive(workspace: str | Path) -> None:
    print(RUNTIME_STATUS)
    print("Type a design request. Press Enter on an empty line to exit.")
    while True:
        try:
            request = input("\nStudent request: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAya local shell closed without external actions.")
            return
        if not request:
            print("Aya local shell closed without external actions.")
            return
        _create_brief(request, Path(workspace) / "design-brief.md")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        print(RUNTIME_STATUS)
        return 0
    if args.command == "brief":
        _create_brief(args.request, args.output)
        return 0
    if args.command == "interactive":
        run_interactive(args.workspace)
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")
