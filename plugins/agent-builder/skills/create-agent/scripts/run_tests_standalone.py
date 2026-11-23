#!/usr/bin/env python3
"""Run your agent's test cases and grade the answers.

Copied by the Agent Builder into <agent-id>/tests/run_tests.py for standalone apps.

Usage (from the agent's folder, with the virtual environment active):
  python tests/run_tests.py                # run all tests
  python tests/run_tests.py --only T1,T4   # run some tests
  python tests/run_tests.py --no-grade     # just collect the answers

Reads tests/test-cases.json, sends each input to the agent in "test mode" (it
can't change anything for real), asks Claude to grade each answer against
your expectations, prints a summary, and writes tests/test-report.md plus
tests/test-results.json (used for the visual HTML report).
Scenario tests ("turns": [...]) send several messages in one conversation.
Tests marked "expert_check": true that pass are shown as "needs your check",
because only you can tell whether the answer is right for your business.
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
You get one test case (the user's input, or several turns of a conversation, and the expectations)
and the agent's actual answer (or the whole conversation).
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

ICON = {"pass": "✅", "review": "👀", "fail": "❌", "couldnt_run": "⚪", "not_graded": "📝"}
LABEL = {"pass": "passed", "review": "need your check", "fail": "failed", "couldnt_run": "couldn't run", "not_graded": "not graded"}


def case_turns(case: dict) -> list[str]:
    turns = case.get("turns")
    if isinstance(turns, list) and turns:
        return [str(t) for t in turns]
    return [case["input"]]


async def run_agent(turns: list[str]) -> str:
    """Send each turn in one conversation. One turn: the plain answer. Several: a transcript."""
    transcript: list[str] = []
    async with ClaudeSDKClient(options=build_options(test_mode=True)) as client:
        for turn in turns:
            await client.query(turn)
            parts: list[str] = []
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    parts.extend(b.text for b in message.content if isinstance(b, TextBlock))
            reply = "\n\n".join(p for p in parts if p.strip())
            if len(turns) == 1:
                return reply
            transcript += [f"USER: {turn}", f"AGENT: {reply}"]
    return "\n\n".join(transcript)


async def grade(case: dict, answer: str) -> dict:
    payload = {k: case.get(k) for k in ("input", "turns", "expected_output", "must_include", "must_not_include", "notes") if case.get(k)}
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
            answer = await run_agent(case_turns(case))
            verdict = {"verdict": "not_graded", "reason": "", "evidence": "", "suggested_fix": ""} if args.no_grade else await grade(case, answer)
            if verdict["verdict"] == "pass" and case.get("expert_check"):
                verdict["verdict"] = "review"
                verdict["reason"] = (verdict.get("reason", "") + " Only you can confirm this is right for your business.").strip()
        except Exception as exc:  # keep going; report it
            answer, verdict = "", {"verdict": "couldnt_run", "reason": f"{type(exc).__name__}: {exc}", "evidence": "", "suggested_fix": ""}
        results.append((case, answer, verdict))

    counts = {k: sum(1 for _, _, v in results if v["verdict"] == k) for k in ICON}
    summary = " · ".join(f"{ICON[k]} {n} {LABEL[k]}" for k, n in counts.items() if n)
    print(f"\n🧪 Test results: {AGENT_NAME}   {summary}\n")
    for case, answer, v in results:
        print(f"{ICON[v['verdict']]} {case.get('id')}  {case.get('name', '')}")
        if v["verdict"] == "review":
            last = " ".join(answer.rsplit("AGENT: ", 1)[-1].split())  # final reply, on one line
            print(f"     👀 Is this how you'd do it? \"{last[:160]}\" (full answer in the report)")
        if v["verdict"] in ("fail", "couldnt_run"):
            print(f"     Why: {v.get('reason', '')}")
            if v.get("evidence"):
                print(f"     Got: \"{v['evidence'][:200]}\"")
            if v.get("suggested_fix"):
                print(f"     💡 Fix: {v['suggested_fix']}")

    lines = [f"# Test report: {AGENT_NAME}", "",
             f"_Run {datetime.now():%Y-%m-%d %H:%M} · method: live (standalone app, test mode) · {summary}_", ""]
    for case, answer, v in results:
        lines += [f"## {ICON[v['verdict']]} {case.get('id')} · {case.get('name', '')}  ({case.get('type', '')})", ""]
        turns = case_turns(case)
        if len(turns) == 1:
            lines += [f"**Input:** {turns[0]}", ""]
        else:
            lines += ["**Conversation:**", ""] + [f"{i}. {t}" for i, t in enumerate(turns, 1)] + [""]
        if v.get("reason"):
            lines += [f"**Verdict:** {v['verdict']}: {v['reason']}", ""]
        if v.get("suggested_fix") and v["verdict"] != "pass":
            lines += [f"**Suggested fix:** {v['suggested_fix']}", ""]
        lines += ["<details><summary>Agent's full answer</summary>", "", answer or "(empty)", "", "</details>", ""]
    report = TESTS_DIR / "test-report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    structured = {
        "agent": {"id": spec.get("agent", ""), "name": AGENT_NAME},
        "run": {"date": f"{datetime.now():%Y-%m-%dT%H:%M}", "method": "live"},
        "results": [{**{k: case.get(k) for k in ("id", "name", "type", "source", "input", "turns", "expected_output",
                                                 "must_include", "must_not_include", "notes", "expert_check")
                        if k in case},
                     "verdict": v["verdict"], "reason": v.get("reason", ""), "evidence": v.get("evidence", ""),
                     "suggested_fix": v.get("suggested_fix", ""), "answer": answer}
                    for case, answer, v in results],
    }
    (TESTS_DIR / "test-results.json").write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFull report: {report}")
    print("For a visual report, ask the Agent Builder: \"show my test report\".")
    return 1 if counts["fail"] or counts["couldnt_run"] else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
