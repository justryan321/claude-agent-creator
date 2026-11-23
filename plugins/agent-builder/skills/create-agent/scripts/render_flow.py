#!/usr/bin/env python3
"""Render the agent's Flow Preview diagram as a standalone HTML page.

Usage:
  render_flow.py <flow.json> <output.html> [--open]

<flow.json> follows the spec in references/flow-preview.md (a list of "steps", or
"stages" for workflow agents). The page is fully
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


def validate_steps(steps, where: str, max_steps: int) -> list[str]:
    problems = []
    if not isinstance(steps, list) or not steps:
        return [f'{where}: "steps" must be a non-empty list']
    for i, s in enumerate(steps, 1):
        if not s.get("title"):
            problems.append(f"{where} step {i}: missing title")
        if s.get("kind") not in KINDS:
            problems.append(f"{where} step {i}: kind must be one of {sorted(KINDS)}")
        b = s.get("branch")
        if b is not None and (not b.get("when") or not b.get("then")):
            problems.append(f"{where} step {i}: branch needs both 'when' and 'then'")
        for key in ("rules", "open"):
            if key in s and not (isinstance(s[key], list) and all(isinstance(x, str) for x in s[key])):
                problems.append(f"{where} step {i}: '{key}' must be a list of strings")
    if len(steps) > max_steps:
        problems.append(f"{where}: more than {max_steps} steps; merge some so the diagram stays readable")
    return problems


def validate(spec: dict) -> list[str]:
    problems = []
    if not isinstance(spec.get("agent"), dict) or not spec["agent"].get("name"):
        problems.append('"agent.name" is required')
    stages = spec.get("stages")
    if stages:  # workflow agents: a stage map, each stage with its own steps
        if not isinstance(stages, list):
            return problems + ['"stages" must be a list']
        if len(stages) > 8:
            problems.append("more than 8 stages; start with the most important ones")
        for n, st in enumerate(stages, 1):
            if not isinstance(st, dict) or not st.get("title"):
                problems.append(f"stage {n}: missing title")
                continue
            problems += validate_steps(st.get("steps"), f"stage {n}", 6)
    else:
        problems += validate_steps(spec.get("steps"), "flow", 9)
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
