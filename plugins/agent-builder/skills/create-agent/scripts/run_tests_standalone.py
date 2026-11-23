#!/usr/bin/env python3
"""Run your agent's test cases and grade the answers.

Copied by the Agent Builder into <agent-id>/tests/run_tests.py for standalone apps.

Usage (from the agent's folder, with the virtual environment active):
  python tests/run_tests.py                # run all tests
  python tests/run_tests.py --only T1,T4   # run some tests
  python tests/run_tests.py --no-grade     # just collect the answers

Reads tests/test-cases.json, sends each input to the agent in "test mode" (it
can't change anything for real), asks Claude to grade each answer against
your expectations, prints a summary, and writes tests/test-report.md.
Uses your ANTHROPIC_API_KEY, so each run costs a little.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
AGENT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(AGENT_DIR))

try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        TextBlock,
        query,
    )
except ImportError:
    sys.exit("The Claude Agent SDK isn't installed. Activate your environment and run: pip install -r requirements.txt")

try:
    from agent import AGENT_NAME, MODEL, build_options  # noqa: E402
except ImportError as exc:
    sys.exit(f"Couldn't load agent.py next to the tests folder ({exc}).")

GRADER_PROMPT = """You are a strict, fair test grader for an AI agent.
You get one test case (the user's input and the expectations) and the agent's actual answer.
Check the answer against every expectation:
- expected_output: compare by meaning, not wording, unless the notes say "exact match".
- must_include: every item must be clearly present or done.
- must_not_include: none of these may be present or done.
The verdict is "pass" only if every expectation is met. Otherwise it is "fail".
Use "couldnt_run" only if the answer shows the test itself couldn't run (for example, a technical
error unrelated to the agent's behavior).
Reply with only a JSON object, no other text:
{"verdict": "pass" | "fail" | "couldnt_run", "reason": "<one plain-English sentence>",
 "evidence": "<short quote from the answer that supports the verdict>",
 "suggested_fix": "<one sentence on what to change in the agent's instructions, or empty>"}"""

ICON = {"pass": "✅", "fail": "❌", "couldnt_run": "⚪", "not_graded": "📝"}
LABEL = {"pass": "passed", "fail": "failed", "couldnt_run": "couldn't run", "not_graded": "not graded"}


async def run_agent(case_input: str) -> str:
    parts: list[str] = []
    async with ClaudeSDKClient(options=build_options(test_mode=True)) as client:
        await client.query(case_input)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                parts.extend(b.text for b in message.content if isinstance(b, TextBlock))
    return "\n\n".join(p for p in parts if p.strip())


async def grade(case: dict, answer: str) -> dict:
    payload = {k: case.get(k) for k in ("input", "expected_output", "must_include", "must_not_include", "notes")}
    prompt = f"TEST CASE:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\nAGENT'S ANSWER:\n{answer or '(empty answer)'}"
    options = ClaudeAgentOptions(system_prompt=GRADER_PROMPT, tools=[], setting_sources=[], model=MODEL, max_turns=1)
    text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            text += "".join(b.text for b in message.content if isinstance(b, TextBlock))
    match = re.search(r"\{.*\}", text, re.S)
    try:
        result = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        result = {}
    if result.get("verdict") not in ("pass", "fail", "couldnt_run"):
        return {"verdict": "couldnt_run", "reason": "The grader's reply couldn't be read.", "evidence": text[:200], "suggested_fix": ""}
    return result


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated test ids, e.g. T1,T3")
    ap.add_argument("--no-grade", action="store_true", help="collect answers without grading")
    ap.add_argument("--cases", default=str(TESTS_DIR / "test-cases.json"))
    args = ap.parse_args()

    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = spec.get("cases", [])
    if args.only:
        wanted = {x.strip().upper() for x in args.only.split(",")}
        cases = [c for c in cases if str(c.get("id", "")).upper() in wanted]
    cases = [c for c in cases if "manual only" not in str(c.get("notes", "")).lower()]
    if not cases:
        print("No tests to run.")
        return 0

    print(f"🧪 Testing {AGENT_NAME}: {len(cases)} test(s)\n")
    results = []
    for case in cases:
        label = f"{case.get('id', '?')}  {case.get('name', '')}"
        print(f"   running {label} …", flush=True)
        try:
            answer = await run_agent(case["input"])
            verdict = {"verdict": "not_graded", "reason": "", "evidence": "", "suggested_fix": ""} if args.no_grade else await grade(case, answer)
        except Exception as exc:  # keep going; report it
            answer, verdict = "", {"verdict": "couldnt_run", "reason": f"{type(exc).__name__}: {exc}", "evidence": "", "suggested_fix": ""}
        results.append((case, answer, verdict))

    counts = {k: sum(1 for _, _, v in results if v["verdict"] == k) for k in ICON}
    summary = " · ".join(f"{ICON[k]} {n} {LABEL[k]}" for k, n in counts.items() if n)
    print(f"\n🧪 Test results: {AGENT_NAME}   {summary}\n")
    for case, _, v in results:
        print(f"{ICON[v['verdict']]} {case.get('id')}  {case.get('name', '')}")
        if v["verdict"] in ("fail", "couldnt_run"):
            print(f"     Why: {v.get('reason', '')}")
            if v.get("evidence"):
                print(f"     Got: \"{v['evidence'][:200]}\"")
            if v.get("suggested_fix"):
                print(f"     💡 Fix: {v['suggested_fix']}")

    lines = [f"# Test report: {AGENT_NAME}", "",
             f"_Run {datetime.now():%Y-%m-%d %H:%M} · method: live (standalone app, test mode) · {summary}_", ""]
    for case, answer, v in results:
        lines += [f"## {ICON[v['verdict']]} {case.get('id')} · {case.get('name', '')}  ({case.get('type', '')})", "",
                  f"**Input:** {case.get('input', '')}", ""]
        if v.get("reason"):
            lines += [f"**Verdict:** {v['verdict']}: {v['reason']}", ""]
        if v.get("suggested_fix") and v["verdict"] != "pass":
            lines += [f"**Suggested fix:** {v['suggested_fix']}", ""]
        lines += ["<details><summary>Agent's full answer</summary>", "", answer or "(empty)", "", "</details>", ""]
    report = TESTS_DIR / "test-report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nFull report: {report}")
    return 1 if counts["fail"] or counts["couldnt_run"] else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
