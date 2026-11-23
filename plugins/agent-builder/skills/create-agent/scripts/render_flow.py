#!/usr/bin/env python3
"""Render the agent's Flow Preview diagram as a standalone HTML page.

Usage:
  render_flow.py <flow.json> <output.html> [--open]

<flow.json> follows the spec in references/flow-preview.md. The page is fully
self-contained (no internet needed) and adapts to light/dark mode and phones.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "flow-template.html"
START, END = "/*FLOW_DATA_START*/", "/*FLOW_DATA_END*/"
KINDS = {"input", "think", "tool", "guard", "output", "handoff"}


def validate(spec: dict) -> list[str]:
    problems = []
    if not isinstance(spec.get("agent"), dict) or not spec["agent"].get("name"):
        problems.append('"agent.name" is required')
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        problems.append('"steps" must be a non-empty list')
        return problems
    for i, s in enumerate(steps, 1):
        if not s.get("title"):
            problems.append(f"step {i}: missing title")
        if s.get("kind") not in KINDS:
            problems.append(f"step {i}: kind must be one of {sorted(KINDS)}")
        b = s.get("branch")
        if b is not None and (not b.get("when") or not b.get("then")):
            problems.append(f"step {i}: branch needs both 'when' and 'then'")
    if len(steps) > 9:
        problems.append("more than 9 steps; merge some so the diagram stays readable")
    return problems


def render(spec: dict) -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    a, b = html.index(START) + len(START), html.index(END)
    data = json.dumps(spec, ensure_ascii=False, indent=2)
    # Keep the JSON from closing the <script> tag or breaking JS string parsing.
    data = data.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return html[:a] + data + html[b:]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec")
    p.add_argument("output")
    p.add_argument("--open", action="store_true", help="open the result in the default browser")
    args = p.parse_args()

    spec = json.loads(Path(args.spec).expanduser().read_text(encoding="utf-8"))
    problems = validate(spec)
    if problems:
        sys.exit("Flow spec problems:\n  - " + "\n  - ".join(problems))

    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(spec), encoding="utf-8")
    print(f"Flow preview written to {out.resolve()}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
