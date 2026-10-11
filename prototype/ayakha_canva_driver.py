"""
Ayakha Canva Driver
=====================

Executes CanvaAction instructions via real browser UI automation
(Playwright) — clicking, typing, and dragging the way a human would,
matching the "true UI automation uniformly for SolidWorks AND Canva"
decision from 2 Sept. Not an unofficial API wrapper.

HONEST STATUS — read before running
-------------------------------------
This is unverified/best-effort, the same category as the early
SolidWorks COM fixes were before you tested them live: I can't reach
canva.com from where this was written (sandboxed, no network access to
it), so every selector below is my best guess at Canva's current UI
structure — element text, button labels, search box placeholders —
not something I confirmed against a live session. Expect this to need
at least one real debugging round, same loop as SolidWorks: run it,
send back exactly which action failed and the error, and it gets fixed
in place rather than guessed at twice.

SETUP
------
  pip install playwright
  playwright install chromium

First run opens a real Chrome window and pauses, asking you to log into
Canva manually. After that, your session persists in a local profile
folder (~/.ayakha/canva_profile/), so you won't need to log in again on
later runs — same student-facing experience either way.
"""

import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

CANVA_PROFILE_DIR = Path.home() / ".ayakha" / "canva_profile"


class CanvaDriver:
    """Method names match CanvaActionType enum values exactly (same
    pattern as SolidWorksDriver), so execute_macro can dispatch via
    getattr(driver, action.type.value) without a big if/elif chain."""

    def __init__(self, headless: bool = False):
        if sync_playwright is None:
            raise RuntimeError(
                "playwright is required for Canva automation. "
                "pip install playwright && playwright install chromium"
            )
        CANVA_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        # Persistent context = the login session survives between runs,
        # so the student only ever logs in once, not every session.
        self.context = self._pw.chromium.launch_persistent_context(
            str(CANVA_PROFILE_DIR), headless=headless,
            viewport={"width": 1400, "height": 900},
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self._ensure_design_open()

    def _ensure_design_open(self):
        if "canva.com" not in self.page.url:
            # NOTE: exact URL for "open a fresh blank design" may need
            # adjusting on first real test — this is Canva's general
            # design-creation entry point as of when this was written.
            self.page.goto("https://www.canva.com/design/play")
            time.sleep(2)
        if self._looks_logged_out():
            print("Please log into Canva in the opened browser window, "
                  "then press Enter here to continue...")
            input()

    def _looks_logged_out(self) -> bool:
        try:
            return self.page.get_by_text("Log in", exact=False).first.is_visible(timeout=2000)
        except Exception:
            return False

    def _canvas_bounding_box(self) -> dict:
        canvas = self.page.locator("[data-testid='canvas'], canvas, .editor-canvas").first
        box = canvas.bounding_box()
        if box is None:
            raise RuntimeError("Could not locate the Canva design canvas on screen.")
        return box

    def click_element(self, params: dict):
        description = params["description"]
        self.page.get_by_text(description, exact=False).first.click(timeout=8000)

    def add_text(self, params: dict):
        self.page.get_by_text("Text", exact=False).first.click(timeout=8000)  # left sidebar "Text" tool
        time.sleep(0.5)
        box = self._canvas_bounding_box()
        x = box["x"] + params.get("x", box["width"] / 2)
        y = box["y"] + params.get("y", box["height"] / 2)
        self.page.mouse.click(x, y)
        self.page.keyboard.type(params["text"])

    def add_shape(self, params: dict):
        self.page.get_by_text("Elements", exact=False).first.click(timeout=8000)
        search = self.page.get_by_placeholder("Search", exact=False).first
        search.fill(params["shape"])
        search.press("Enter")
        time.sleep(1)
        self.page.locator("[role='button']").first.click(timeout=8000)  # first search result

    def add_image(self, params: dict):
        """Searches Canva's own stock image library for params['source']
        as a search term and inserts the first result — this does NOT
        fetch an arbitrary external URL/file. The system prompt reflects
        this so the cloud brain's expectations match what's actually
        implemented, rather than requesting a capability that doesn't exist."""
        self.page.get_by_text("Elements", exact=False).first.click(timeout=8000)
        search = self.page.get_by_placeholder("Search", exact=False).first
        search.fill(params["source"])
        search.press("Enter")
        time.sleep(1)
        self.page.locator("[role='button']").first.click(timeout=8000)

    def drag_resize(self, params: dict):
        description = params["description"]
        el = self.page.get_by_text(description, exact=False).first
        el.click(timeout=8000)
        box = el.bounding_box()
        if box is None:
            raise RuntimeError(f"Could not find bounding box for element '{description}' to resize.")
        handle_x, handle_y = box["x"] + box["width"], box["y"] + box["height"]
        target_x, target_y = box["x"] + params["width"], box["y"] + params["height"]
        self.page.mouse.move(handle_x, handle_y)
        self.page.mouse.down()
        self.page.mouse.move(target_x, target_y, steps=10)
        self.page.mouse.up()

    def change_color(self, params: dict):
        description = params["description"]
        self.page.get_by_text(description, exact=False).first.click(timeout=8000)
        time.sleep(0.3)
        self.page.locator("[aria-label*='Color' i]").first.click(timeout=8000)
        time.sleep(0.3)
        hex_input = self.page.get_by_placeholder("Hex code", exact=False)
        hex_input.fill(params["color"].lstrip("#"))
        hex_input.press("Enter")

    def select_template(self, params: dict):
        search = self.page.get_by_placeholder("Search", exact=False).first
        search.fill(params["name"])
        search.press("Enter")
        time.sleep(1)
        self.page.locator("[role='button']").first.click(timeout=8000)

    def close(self):
        self.context.close()
        self._pw.stop()
