"""
Ayakha Learning Ledger
========================

Records WHO performed each design skill (student vs. Aya) so the product
produces evidence of growth, not just a CAD file — the concrete answer to
"what does the student keep" (resolved: the skill, not just the output).

Local-only: SQLite in ~/.ayakha/. Works with no network — matters for
load-shedding/offline resilience.

NOTE ON INTEGRATION: this version is written against the REAL MacroAction
schema (macro_action_schema.py), not a summary of it. Key correction from
an earlier draft: `teaching` (mode/narration/correcting) belongs to the
whole MacroAction, not to each individual atomic action — a macro's
actions all share one teaching context, since they're one instruction
from the cloud brain.
"""
from __future__ import annotations
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

LEDGER_DIR = Path.home() / ".ayakha"
LEDGER_DB = LEDGER_DIR / "ledger.db"


# ---------------------------------------------------------------- taxonomy
class Attribution(str, Enum):
    STUDENT_UNAIDED = "student_unaided"          # student did it, Aya silent (needs the observer, not built yet)
    STUDENT_GUIDED = "student_guided"            # student directed it via voice, Aya's hands executed
    AYA_DEMONSTRATED = "aya_demonstrated"        # "allow me to demonstrate" — teaching moment
    AYA_DID_FOR_STUDENT = "aya_did_for_student"  # student said "just do it"


# Matches SolidWorksActionType's exact enum values from macro_action_schema.py.
SKILL_MAP = {
    "new_sketch": "sketch_plane_selection",
    "draw_rectangle": "sketch_rectangle",
    "draw_line": "sketch_line",
    "draw_circle": "sketch_circle",
    "add_dimension": "dimensioning",
    "extrude": "extrude_boss",
    "fillet": "fillet",
    "select_feature": "feature_tree_navigation",
    "save_file": "file_management",
    "click_toolbar": "ui_navigation",
}


def derive_skills(action_type: str, params: dict) -> list[str]:
    """Maps a raw action type to the skill(s) it represents. Some skills
    only exist as a *combination*, detected from params rather than type."""
    skills = [SKILL_MAP.get(action_type, action_type)]
    if action_type == "new_sketch" and params.get("offset_mm"):
        skills.append("coaxial_positioning")
    return skills


# ---------------------------------------------------------------- models
class LedgerEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    session_id: str
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool: str
    action_type: str
    skill: str
    attribution: Attribution
    correcting: Optional[str] = None
    narration: Optional[str] = None
    verified: Optional[bool] = None


class SkillStatus(BaseModel):
    skill: str
    unaided: int = 0
    guided: int = 0
    demonstrated: int = 0
    done_for: int = 0
    last_attribution: Optional[Attribution] = None
    status: str = "not_started"  # not_started | shown | practicing | learned


# ---------------------------------------------------------------- ledger
class Ledger:
    LEARNED_THRESHOLD = 2  # unaided repetitions AFTER the last demonstration

    def __init__(self, student_id: str, db_path: Path = LEDGER_DB):
        LEDGER_DIR.mkdir(exist_ok=True)
        self.student_id = student_id
        self.session_id: Optional[str] = None
        self.tool: Optional[str] = None
        self.takeover_requested = False
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY, student_id TEXT, session_id TEXT, ts TEXT,
                tool TEXT, action_type TEXT, skill TEXT, attribution TEXT,
                correcting TEXT, narration TEXT, verified INTEGER
            )""")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, student_id TEXT, tool TEXT,
                started TEXT, ended TEXT, request TEXT, takeover INTEGER
            )""")
        self.db.commit()

    # --- session lifecycle -------------------------------------------------
    def start_session(self, tool: str, request: str) -> str:
        self.session_id = uuid.uuid4().hex
        self.tool = tool
        self.takeover_requested = False
        self.db.execute(
            "INSERT INTO sessions VALUES (?,?,?,?,?,?,?)",
            (self.session_id, self.student_id, tool,
             datetime.now(timezone.utc).isoformat(), None, request, 0))
        self.db.commit()
        return self.session_id

    def end_session(self):
        self.db.execute("UPDATE sessions SET ended=? WHERE id=?",
                         (datetime.now(timezone.utc).isoformat(), self.session_id))
        self.db.commit()

    # --- the "just do it" friction ----------------------------------------
    def request_full_takeover(self) -> str:
        """Student asked Aya to do the whole thing. We don't refuse — we
        make the cost visible and log it honestly. Returns Aya's spoken line."""
        self.takeover_requested = True
        self.db.execute("UPDATE sessions SET takeover=1 WHERE id=?", (self.session_id,))
        self.db.commit()
        return ("Okay, I'll build this one for you. I'm recording it as done-for-you, "
                "not learned, so it won't count toward your progress. "
                "Want to try rebuilding it yourself after? I'll watch and only "
                "step in if you get stuck.")

    # --- recording -----------------------------------------------------------
    def record_macro_actions(self, macro, verified: Optional[bool] = None):
        """Call once per executed MacroAction, after the driver runs its
        actions and (optionally) verifies the result. Reads teaching info
        from the MACRO level (mode/correcting/narration), matching the
        real schema — not from each individual action."""
        mode = macro.teaching.mode.value if hasattr(macro.teaching.mode, "value") else macro.teaching.mode
        correcting = macro.teaching.correcting

        if self.takeover_requested:
            attr = Attribution.AYA_DID_FOR_STUDENT
        elif mode == "demonstration" or correcting:
            attr = Attribution.AYA_DEMONSTRATED
        else:
            # Aya acting on the student's spoken instruction is still Aya's
            # hands. True "unaided" requires an observer watching the student
            # build by hand — not built yet, see record_student_action below.
            attr = Attribution.STUDENT_GUIDED

        tool = macro.tool.value if hasattr(macro.tool, "value") else macro.tool
        for action in macro.actions:
            action_type = action.type.value if hasattr(action.type, "value") else action.type
            for skill in derive_skills(action_type, action.params or {}):
                self._insert(LedgerEvent(
                    session_id=self.session_id, tool=tool,
                    action_type=action_type, skill=skill,
                    attribution=attr, correcting=correcting,
                    narration=macro.teaching.narration, verified=verified))

    def record_student_action(self, action_type: str, params: dict | None = None,
                               aya_was_guiding: bool = False):
        """Hook for a future observer (read-only COM polling of the feature
        tree) to call when the STUDENT creates a feature by hand. Not wired
        yet — the observer doesn't exist. This is the API it will need,
        and it's the only path to real 'learned' status, since everything
        Aya executes is at best 'guided'."""
        attr = Attribution.STUDENT_GUIDED if aya_was_guiding else Attribution.STUDENT_UNAIDED
        for skill in derive_skills(action_type, params or {}):
            self._insert(LedgerEvent(
                session_id=self.session_id, tool=self.tool,
                action_type=action_type, skill=skill, attribution=attr))

    def _insert(self, e: LedgerEvent):
        self.db.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (e.id, self.student_id, e.session_id, e.ts, e.tool, e.action_type,
             e.skill, e.attribution.value, e.correcting, e.narration,
             None if e.verified is None else int(e.verified)))
        self.db.commit()

    # --- reading -------------------------------------------------------------
    def skill_status(self, tool: Optional[str] = None) -> list[SkillStatus]:
        # verified=0 means the step was checked and did NOT happen in the tool,
        # so it can't count as practice or as a demonstration the student saw.
        q = ("SELECT skill, attribution, ts FROM events "
             "WHERE student_id=? AND (verified IS NULL OR verified=1)")
        args = [self.student_id]
        if tool:
            q += " AND tool=?"
            args.append(tool)
        q += " ORDER BY ts"
        rows = self.db.execute(q, args).fetchall()

        by_skill: dict[str, SkillStatus] = {}
        unaided_since_demo: dict[str, int] = {}
        for skill, attr, _ in rows:
            s = by_skill.setdefault(skill, SkillStatus(skill=skill))
            attr = Attribution(attr)
            s.last_attribution = attr
            if attr == Attribution.STUDENT_UNAIDED:
                s.unaided += 1
                unaided_since_demo[skill] = unaided_since_demo.get(skill, 0) + 1
            elif attr == Attribution.STUDENT_GUIDED:
                s.guided += 1
            elif attr == Attribution.AYA_DEMONSTRATED:
                s.demonstrated += 1
                unaided_since_demo[skill] = 0
            else:
                s.done_for += 1

        for skill, s in by_skill.items():
            if unaided_since_demo.get(skill, 0) >= self.LEARNED_THRESHOLD:
                s.status = "learned"
            elif s.unaided or s.guided:
                s.status = "practicing"
            elif s.demonstrated or s.done_for:
                s.status = "shown"
        return sorted(by_skill.values(), key=lambda s: s.skill)

    def session_summary_spoken(self) -> str:
        """What Aya says at the end of a session. One short paragraph, no lists."""
        all_rows = self.db.execute(
            "SELECT skill, attribution, verified FROM events WHERE session_id=?",
            (self.session_id,)).fetchall()
        failed = sorted({s for s, _, v in all_rows if v == 0})
        rows = [(s, a) for s, a, v in all_rows if v != 0]
        pretty = lambda xs: ", ".join(x.replace("_", " ") for x in xs)
        if not rows:
            if failed:
                return (f"That didn't work: {pretty(failed)} didn't come out in SolidWorks, "
                        "so none of it counts yet. Let's try again.")
            return "We didn't build anything this session."
        demo = sorted({s for s, a in rows if a == Attribution.AYA_DEMONSTRATED.value})
        guided = sorted({s for s, a in rows if a == Attribution.STUDENT_GUIDED.value})
        unaided = sorted({s for s, a in rows if a == Attribution.STUDENT_UNAIDED.value})
        done_for = sorted({s for s, a in rows if a == Attribution.AYA_DID_FOR_STUDENT.value})

        parts = []
        if unaided:
            parts.append(f"You did {pretty(unaided)} on your own")
        if guided:
            parts.append(f"we worked through {pretty(guided)} together")
        if demo:
            parts.append(f"I showed you {pretty(demo)} — try that yourself next time")
        if done_for:
            parts.append(f"I built {pretty(done_for)} for you, so that one's still yours to learn")
        if failed:
            parts.append(f"{pretty(failed)} didn't work, so it doesn't count yet")
        return "; ".join(parts).capitalize() + "."

    def export_markdown(self, path: Optional[Path] = None) -> Path:
        """Lecturer-facing report. No Aya required to read it."""
        path = path or LEDGER_DIR / f"progress_{self.student_id}.md"
        statuses = self.skill_status()
        lines = [f"# Ayakha progress — {self.student_id}",
                 f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_", "",
                 "| Skill | Status | Unaided | Guided | Aya demonstrated | Done for student |",
                 "|---|---|---|---|---|---|"]
        for s in statuses:
            lines.append(f"| {s.skill.replace('_', ' ')} | **{s.status}** | {s.unaided} | "
                         f"{s.guided} | {s.demonstrated} | {s.done_for} |")
        n_sessions, n_takeover = self.db.execute(
            "SELECT COUNT(*), SUM(takeover) FROM sessions WHERE student_id=?",
            (self.student_id,)).fetchone()
        n_confirmed, n_unchecked, n_failed = self.db.execute(
            "SELECT SUM(verified=1), SUM(verified IS NULL), SUM(verified=0) "
            "FROM events WHERE student_id=?", (self.student_id,)).fetchone()
        lines += ["", f"Sessions: {n_sessions} · Full take-overs requested: {n_takeover or 0}",
                  f"Steps confirmed in the tool: {n_confirmed or 0} · "
                  f"not checkable: {n_unchecked or 0} · "
                  f"failed (excluded from the table above): {n_failed or 0}"]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
