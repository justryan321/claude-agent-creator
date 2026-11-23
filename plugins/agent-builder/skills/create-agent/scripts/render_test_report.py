#!/usr/bin/env python3
"""Render a visual test report (HTML) from an agent's test results.

Usage:
  render_test_report.py <test-results.json> <output.html> [--cases test-cases.json] [--open]

<test-results.json> (see references/test-cases.md):
  {"agent": {"id", "name", "emoji"}, "run": {"date", "method"},
   "results": [{"id", "verdict", "reason", "evidence", "suggested_fix", "answer", ...}]}

Each result's input and expectations (name, type, source, input, expected_output,
must_include, must_not_include, notes) are filled in from --cases (default:
test-cases.json next to the results file) when the result doesn't include them.
The page is self-contained, works offline, and has a light/dark theme switch.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "test-report-template.html"
START, END = "/*REPORT_DATA_START*/", "/*REPORT_DATA_END*/"
VERDICTS = {"pass", "fail", "couldnt_run", "not_graded"}
CASE_FIELDS = ("name", "type", "source", "input", "expected_output", "must_include", "must_not_include", "notes")


def merge_cases(data: dict, cases_path: Path) -> None:
    if not cases_path.exists():
        return
    try:
        cases = {c.get("id"): c for c in json.loads(cases_path.read_text(encoding="utf-8")).get("cases", [])}
    except (json.JSONDecodeError, AttributeError):
        print(f"Warning: couldn't read {cases_path}; showing results without their expectations.", file=sys.stderr)
        return
    for r in data.get("results", []):
        case = cases.get(r.get("id"), {})
        for f in CASE_FIELDS:
            if r.get(f) in (None, "", []) and case.get(f) not in (None, "", []):
                r[f] = case[f]


def validate(data: dict) -> list[str]:
    problems = []
    if not isinstance(data.get("results"), list) or not data["results"]:
        problems.append('"results" must be a non-empty list')
        return problems
    for i, r in enumerate(data["results"], 1):
        if r.get("verdict") not in VERDICTS:
            problems.append(f"result {i} ({r.get('id', '?')}): verdict must be one of {sorted(VERDICTS)}")
        if not r.get("input"):
            problems.append(f"result {i} ({r.get('id', '?')}): no input (add it, or pass --cases with the matching test)")
    return problems


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("results")
    p.add_argument("output")
    p.add_argument("--cases", help="test-cases.json to fill in inputs and expectations")
    p.add_argument("--open", action="store_true", help="open the report in the default browser")
    args = p.parse_args()

    res_path = Path(args.results).expanduser()
    try:
        data = json.loads(res_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"Couldn't read {res_path}: {exc}")
    merge_cases(data, Path(args.cases).expanduser() if args.cases else res_path.with_name("test-cases.json"))
    problems = validate(data)
    if problems:
        sys.exit("Test results problems:\n  - " + "\n  - ".join(problems))

    html = TEMPLATE.read_text(encoding="utf-8")
    a, b = html.index(START) + len(START), html.index(END)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html[:a] + payload + html[b:], encoding="utf-8")
    counts = {v: sum(1 for r in data["results"] if r["verdict"] == v) for v in VERDICTS}
    print(f"Test report written to {out.resolve()}  ({counts['pass']} passed, {counts['fail']} failed, "
          f"{counts['couldnt_run'] + counts['not_graded']} couldn't run or not graded)")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
