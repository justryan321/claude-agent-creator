#!/usr/bin/env python3
"""Render the agent's Flow Preview diagram as a standalone HTML page.

Usage:
  render_flow.py <flow.json> <output.html> [--previous old-flow.json] [--open]

With --previous, steps that are new or changed since the old version are
tagged "New" / "Updated", removed steps are listed, and new "at a glance"
items are marked, so the user can see that their feedback was applied.

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


def _norm(text) -> str:
    return " ".join(str(text or "").lower().split())


def _step_sig(step: dict) -> tuple:
    b = step.get("branch") or {}
    return (step.get("kind"), step.get("icon"), _norm(step.get("detail")),
            _norm(b.get("when")), _norm(b.get("then")), b.get("kind"), b.get("icon"),
            tuple(_norm(x) for x in step.get("rules") or []), tuple(_norm(x) for x in step.get("open") or []))


def _all_steps(spec: dict) -> list[tuple[str, str, dict]]:
    """(match key, label, step) for every step: the flat list, or every stage's steps for workflow agents."""
    if spec.get("stages"):
        return [(_norm(st.get("title")) + "|" + _norm(s.get("title")), f"{st.get('title', '')}: {s.get('title', '')}", s)
                for st in spec["stages"] if isinstance(st, dict) for s in st.get("steps") or []]
    return [(_norm(s.get("title")), s.get("title", ""), s) for s in spec.get("steps") or []]


def mark_changes(spec: dict, previous: dict) -> int:
    """Tag what changed since `previous`. Steps are matched by title (within their stage), then by position.
    Returns the number of changes."""
    old_steps = _all_steps(previous)
    new_steps = _all_steps(spec)
    by_key = {k: s for k, _, s in old_steps}
    new_keys = {k for k, _, _ in new_steps}
    matched = set()
    changes = 0
    for i, (key, _, step) in enumerate(new_steps):
        step.pop("change", None)
        old = by_key.get(key)
        if old is None and i < len(old_steps) and id(old_steps[i][2]) not in matched and old_steps[i][0] not in new_keys:
            old = old_steps[i][2]  # same position, renamed
        if old is None:
            step["change"] = "new"
            changes += 1
            continue
        matched.add(id(old))
        if _step_sig(old) != _step_sig(step) or _norm(old.get("title")) != _norm(step.get("title")):
            step["change"] = "updated"
            changes += 1
    removed = [label for _, label, s in old_steps if id(s) not in matched]
    spec["removed_steps"] = removed
    changes += len(removed)
    glance_new = {}
    for key in ("can", "wont", "asks_first", "expert_checks"):
        before = {_norm(x) for x in (previous.get("glance") or {}).get(key, []) or []}
        new_items = [x for x in (spec.get("glance") or {}).get(key, []) or [] if _norm(x) not in before]
        if new_items:
            glance_new[key] = new_items
            changes += len(new_items)
    spec["glance_new"] = glance_new
    spec["revision"] = int(previous.get("revision", 1)) + 1
    return changes


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
    p.add_argument("--previous", help="the previous version of the flow spec, to highlight what changed")
    args = p.parse_args()

    spec = json.loads(Path(args.spec).expanduser().read_text(encoding="utf-8"))
    problems = validate(spec)
    if problems:
        sys.exit("Flow spec problems:\n  - " + "\n  - ".join(problems))

    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.previous:
        prev_path = Path(args.previous).expanduser()
        if prev_path.exists():
            n = mark_changes(spec, json.loads(prev_path.read_text(encoding="utf-8")))
            print(f"Compared with the previous version: {n} change(s) highlighted.")
        else:
            print(f"No previous version at {prev_path}; nothing to compare.")
    out.write_text(render(spec), encoding="utf-8")
    print(f"Flow preview written to {out.resolve()}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
