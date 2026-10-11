"""
Ayakha Brain Benchmark
=======================

Sends the same set of test requests to Groq (Llama 3.3 70B) and Gemini
(Flash-Lite) and checks which one reliably produces valid MacroAction JSON
— i.e. which one is actually usable as Aya's brain, not just which one
"sounds" capable.

SETUP
-----
1. pip install requests pydantic
2. Set your API keys as environment variables:
     export GROQ_API_KEY="your_key_here"
     export GEMINI_API_KEY="your_key_here"
   (Groq: console.groq.com/keys | Gemini: aistudio.google.com/apikey)
3. Put macro_action_schema.py in the same folder as this file.
4. Run: python ayakha_brain_benchmark.py

WHAT IT MEASURES
-----------------
For each test case, for each provider:
  - latency (seconds)
  - whether the response was valid JSON at all
  - whether that JSON validates against the MacroAction pydantic schema
  - the specific validation error, if any (so you can see WHERE models
    tend to fail — e.g. wrong enum value, missing required field)

This is intentionally simple and readable rather than a full eval
framework — the goal is a quick, honest signal you can act on today,
not a research-grade benchmark.
"""

import os
import json
import time
import requests
from pydantic import ValidationError

from macro_action_schema import MacroAction


# ---------------------------------------------------------------------------
# The instruction every provider gets. Keep this identical across providers
# so the comparison is fair — differences in output should come from model
# capability, not prompt wording.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Ayakha's reasoning brain, controlling SolidWorks or Canva through UI automation on behalf of a student.

Given a student's request, respond with ONLY a JSON object matching this exact structure (no markdown fences, no explanation, just the raw JSON):

{
  "macro_id": "macro_XXXX",
  "tool": "solidworks" | "canva" | "generic",
  "goal": "plain language description of what this macro accomplishes",
  "actions": [
    {"type": "<action_type>", "params": {...}}
  ],
  "teaching": {
    "mode": "silent" | "narrated" | "demonstration",
    "narration": "what Aya says while doing this, or null",
    "correcting": "what mistake is being corrected, or null (only used in demonstration mode)"
  },
  "verification": {
    "method": "com_readonly" | "screenshot_diff" | "none",
    "expected": "what success looks like, or null"
  },
  "requires_confirmation": true,
  "interruptible": true
}

Valid SolidWorks action types: new_sketch, draw_line, draw_rectangle, draw_circle, add_dimension, extrude, fillet, select_feature, click_toolbar, save_file
Valid Canva action types: click_element, add_text, add_shape, add_image, drag_resize, change_color, select_template
Valid generic action types: click_at, move_mouse, type_text, key_press, wait, screenshot
"""

TEST_CASES = [
    "Draw a 100x50mm rectangle on the front plane and extrude it 10mm.",
    "Add a 5mm fillet to all edges of the last extrude, then save the file.",
    "On Canva, add a text box that says 'Ayakha Pilot' and change its color to blue.",
    "The student's circle is off-center. Take over and redraw it correctly at the origin with a 20mm radius, and explain what they got wrong.",
]


def call_groq(prompt: str) -> tuple[str, float]:
    """Returns (raw_response_text, latency_seconds).

    Note: llama-3.3-70b-versatile was decommissioned by Groq on 2026-08-16.
    Using their recommended replacement, openai/gpt-oss-120b, instead.
    """
    api_key = os.environ["GROQ_API_KEY"]
    start = time.time()
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )
    latency = time.time() - start
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return text, latency


def call_gemini(prompt: str) -> tuple[str, float]:
    """Returns (raw_response_text, latency_seconds).

    Note: Google is phasing out old AIzaSy... keys in favor of new AQ...
    keys, which are OAuth-style tokens. AQ. keys must be sent as an
    Authorization: Bearer header, NOT as a ?key= query parameter (that
    only works for the legacy AIzaSy format, which Google will stop
    accepting entirely this month). This function sends the key both
    ways isn't possible in one request, so it detects the key format
    and picks the right method automatically.
    """
    api_key = os.environ["GEMINI_API_KEY"]
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    start = time.time()
    if api_key.startswith("AQ."):
        # New-style auth key: send as Bearer token, key NOT in the URL.
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=30,
        )
    else:
        # Legacy AIzaSy... key: still works as a query parameter for now.
        resp = requests.post(f"{url}?key={api_key}", json=payload, timeout=30)
    latency = time.time() - start
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return text, latency


def strip_markdown_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json ... ``` even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def evaluate(provider_name: str, call_fn, prompt: str) -> dict:
    result = {"provider": provider_name, "prompt": prompt[:50] + "..."}
    try:
        raw_text, latency = call_fn(prompt)
        result["latency_seconds"] = round(latency, 2)
    except Exception as e:
        result["outcome"] = "API_ERROR"
        result["error"] = str(e)
        return result

    cleaned = strip_markdown_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        result["outcome"] = "INVALID_JSON"
        result["error"] = str(e)
        result["raw_snippet"] = cleaned[:150]
        return result

    try:
        MacroAction.model_validate(parsed)
        result["outcome"] = "VALID_MACRO_ACTION"
    except ValidationError as e:
        result["outcome"] = "SCHEMA_VALIDATION_FAILED"
        result["error"] = str(e.errors()[0])  # just the first error, for readability

    return result


def main():
    providers = []
    if "GROQ_API_KEY" in os.environ:
        providers.append(("Groq (Llama 3.3 70B)", call_groq))
    if "GEMINI_API_KEY" in os.environ:
        providers.append(("Gemini 2.5 Flash-Lite", call_gemini))

    if not providers:
        print("No API keys found. Set GROQ_API_KEY and/or GEMINI_API_KEY and try again.")
        return

    results = []
    for name, fn in providers:
        for prompt in TEST_CASES:
            print(f"Testing {name} on: {prompt[:50]}...")
            results.append(evaluate(name, fn, prompt))

    # --- Summary ---
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for r in results:
        line = f"[{r['provider']}] {r['outcome']}"
        if "latency_seconds" in r:
            line += f" ({r['latency_seconds']}s)"
        print(line)
        if r["outcome"] != "VALID_MACRO_ACTION" and "error" in r:
            print(f"    -> {r['error']}")

    # --- Scorecard per provider ---
    print("\n" + "=" * 70)
    print("SCORECARD")
    print("=" * 70)
    for name, _ in providers:
        provider_results = [r for r in results if r["provider"] == name]
        valid = sum(1 for r in provider_results if r["outcome"] == "VALID_MACRO_ACTION")
        total = len(provider_results)
        avg_latency = sum(r.get("latency_seconds", 0) for r in provider_results) / total
        print(f"{name}: {valid}/{total} valid ({round(avg_latency, 2)}s avg latency)")


if __name__ == "__main__":
    main()
