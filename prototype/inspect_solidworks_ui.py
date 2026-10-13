"""
Ayakha - SolidWorks UI Automation inspection
=============================================

Answers one question before we rebuild the SolidWorks driver:
does SolidWorks expose its buttons (Sketch, Rectangle, Extruded Boss/Base,
Smart Dimension) to Windows UI Automation, with names and screen positions?

If yes  -> Aya can find each button by name and visibly move the mouse to it.
If no   -> we need a screenshot/vision fallback for finding buttons.

HOW TO RUN
----------
  1. pip install pywinauto
  2. Open SolidWorks, create a new Part, and click the "Sketch" tab on the
     CommandManager ribbon so the sketch tools are visible.
  3. python inspect_solidworks_ui.py
  4. Tell Claude it's done. Results are saved to ui_dump.txt in this folder.

It only READS the UI. It does not click or change anything.
"""

import sys
import time
from pathlib import Path

try:
    from pywinauto import Application
except ImportError:
    sys.exit("pywinauto is missing. Run: pip install pywinauto")

OUT = Path(__file__).with_name("ui_dump.txt")
MAX_ELEMENTS = 6000  # safety cap so a huge tree doesn't take forever

TARGETS = [
    "Sketch",
    "Corner Rectangle",
    "Rectangle",
    "Circle",
    "Line",
    "Smart Dimension",
    "Extruded Boss/Base",
    "Features",
    "Exit Sketch",
    "Fillet",
]


def describe(el) -> dict:
    info = el.element_info
    try:
        r = info.rectangle
        rect = f"({r.left},{r.top})-({r.right},{r.bottom})"
    except Exception:
        rect = "?"
    return {
        "type": info.control_type or "?",
        "name": (info.name or "").strip(),
        "auto_id": info.automation_id or "",
        "class": info.class_name or "",
        "rect": rect,
    }


def main():
    print("Connecting to SolidWorks...")
    try:
        app = Application(backend="uia").connect(path="SLDWORKS.exe", timeout=15)
    except Exception as e:
        sys.exit(f"Could not find a running SolidWorks (SLDWORKS.exe). Open it first. ({e})")

    windows = [w for w in app.windows() if "SOLIDWORKS" in (w.window_text() or "").upper()]
    if not windows:
        windows = app.windows()
    if not windows:
        sys.exit("SolidWorks is running but no window was found.")
    main_win = max(windows, key=lambda w: w.rectangle().width() * w.rectangle().height())
    print(f"Main window: {main_win.window_text()!r}")

    print("Reading the UI tree (this can take up to a minute)...")
    start = time.time()
    rows, count = [], 0
    for el in main_win.descendants():
        rows.append(describe(el))
        count += 1
        if count >= MAX_ELEMENTS:
            break
    elapsed = time.time() - start

    named = [r for r in rows if r["name"]]
    type_counts = {}
    for r in rows:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1

    lines = [
        "AYAKHA - SolidWorks UIA inspection",
        f"Window: {main_win.window_text()!r}",
        f"Elements read: {count} (cap {MAX_ELEMENTS}) in {elapsed:.1f}s",
        f"Elements with a name: {len(named)}",
        "",
        "== Control types found ==",
    ]
    for t, n in sorted(type_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {t}: {n}")

    lines += ["", "== Target buttons =="]
    for target in TARGETS:
        hits = [r for r in rows if target.lower() in r["name"].lower()]
        if not hits:
            lines.append(f"  [MISSING] {target}")
            continue
        lines.append(f"  [FOUND x{len(hits)}] {target}")
        for h in hits[:5]:
            lines.append(f"      {h['type']:<14} name={h['name']!r} id={h['auto_id']!r} "
                         f"class={h['class']!r} rect={h['rect']}")

    lines += ["", "== All named elements (first 800) =="]
    for r in named[:800]:
        lines.append(f"  {r['type']:<14} {r['name']!r:<45} id={r['auto_id']!r} rect={r['rect']}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done. {count} elements read, {len(named)} named.")
    print(f"Results saved to {OUT}")
    found = sum(1 for t in TARGETS if any(t.lower() in r["name"].lower() for r in rows))
    print(f"Target buttons found: {found}/{len(TARGETS)}")


if __name__ == "__main__":
    main()
