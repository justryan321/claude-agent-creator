# Test cases: check the finished agent really works

The test drive (Phase 4) is a quick feel-check while designing. **Test cases** are a repeatable check of the *finished* agent: a list of inputs, each with what a good answer looks like, run against the real agent and graded. The user can add their own cases (an input plus the output they expect) at any time, and re-run the tests whenever they change the agent.

## 1. Test case format

Save as `<agent-id>/tests/test-cases.json`:

```json
{
  "agent": "<agent-id>",
  "cases": [
    {
      "id": "T1",
      "name": "Summarizes a normal news article",
      "type": "everyday",
      "source": "generated",
      "input": "Summarize https://en.wikipedia.org/wiki/Photosynthesis",
      "expected_output": "",
      "must_include": ["a 3–5 sentence summary", "5–10 bolded key items", "the page title"],
      "must_not_include": ["facts that aren't on the page"],
      "notes": ""
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | `T1`, `T2`, … (user-added cases continue the numbering) |
| `name` | Short plain-language label shown in reports |
| `type` | `everyday` (typical request) · `tricky` (edge case, unclear or incomplete input) · `boundary` (should refuse, hand off, or ask first) · `format` (checks shape, length, tone) · `scenario` (a whole job over several turns; workflow agents) |
| `source` | `generated` · `you` (the user wrote it) · `your chat` (taken from imported context) |
| `input` | Exactly what a user would type. For tests that need a file, describe the file in `notes` and put a small sample in `tests/fixtures/`. |
| `turns` | Scenario tests only, instead of `input`: the user's messages in order, sent in one conversation. Expectations are checked against the whole conversation. |
| `expert_check` | Optional, `true` when only the user can tell whether the answer is right (prices, rules, trade judgment). A pass is reported as **👀 needs your check** with the answer shown, not as ✅. |
| `expected_output` | Optional. A full example of the ideal answer. Graded on **meaning, not exact wording**, unless `notes` says "exact match". |
| `must_include` | Things a passing answer must contain or do (plain language, each one checkable) |
| `must_not_include` | Things a passing answer must not contain or do |
| `notes` | Anything the grader should know |

Each case needs at least one of `expected_output`, `must_include`, or `must_not_include`, and either `input` or `turns`.

## 2. Generate the starter set

Build **6–8 cases** from the Agent Card, the instructions, and any imported context:

- **2–3 everyday** cases from the user's example requests.
- **1–2 tricky** cases, such as vague or incomplete input, an unusual page or file, or a very long input.
- **1–2 boundary** cases, one for each important "won't do", "asks first", or handoff rule. These matter most.
- **1 format** case that checks tone, length, and structure.
- If the user imported a past chat, turn **real question → answer they liked** pairs into cases with `source: "your chat"` and that answer as `expected_output`. These are the most valuable tests there are.

For agents that read web pages, prefer stable public pages (Wikipedia, official docs) over news that will change.

### Workflow agents

For agents built in workflow mode (`workflow-mode.md`), the starter set changes:

- **1–2 `scenario` cases** that take one job through 3+ stages, built from the real job the user walked through. Check that facts from early turns carry through (the budget from intake shows up in the bid), that each playbook rule that applies is followed, and that the hand-off info is passed on.
- **One `boundary` case per expert check** (structural question, permit/code question, contract dispute…): passes only if the agent flags it and doesn't decide.
- **One case per ❓ item** (or the most important ones): passes only if the agent asks instead of inventing an answer.
- **One stale-data case** if there's changing data: the file's date is old, and the agent must warn before using the numbers.
- Write `must_include` items from the **playbook's own numbers and wording** ("applies 15% contingency because the house is from 1962"), never from general knowledge. Claude's idea of a "correct" estimate may not match the user's business.
- Set `expert_check: true` on every case where correctness depends on the user's expertise. Ask the user to look at those answers themselves. Their verdict beats the grader's.

Up to 10–12 cases is fine for workflow agents.

## 3. Let the user add their own

Always offer, in plain words: "Do you have a real example of something you'd ask it, and the answer you'd want back? I'll add it as a test."

Accept any form and convert it:
- **Input + full answer** → `expected_output` (graded on meaning) and derive 2–4 `must_include` items from it. Show these so the user can correct them.
- **Input + "it should…"** → `must_include` / `must_not_include`.
- **Input + "exactly this"** → `expected_output` with `notes: "exact match"`. Use this only for short, fixed answers (a contact email, a fixed phrase).
- **Input only** → propose the expectations yourself and ask "Is this what you'd expect?"

Users can add, edit, or remove cases later. Re-running the builder with "update my tests" or "add a test" should load `tests/test-cases.json` and continue from there.

## 4. Run the tests

Run each case **in a fresh context**, so earlier conversation doesn't help the agent, and keep the agent's raw answer. For `scenario` cases, send each of the `turns` in order within that one fresh conversation (when calling a subagent, resume the same agent for each turn, or pass the earlier turns and replies along), and keep the whole transcript. Then grade it (section 5). Pick the method by destination and environment:

| Destination | Claude Code (has subagents/shell) | claude.ai / no tools |
|---|---|---|
| **Subagent** | Call the installed agent by name with your subagent/Agent tool, once per case, passing only the test input. If it isn't found yet, start a general-purpose subagent whose prompt is the agent's full instructions plus "Respond to this user message as this agent:" + input. | Simulate (see below) |
| **Skill** | Start a general-purpose subagent: "Use the `<agent-id>` skill to handle this request:" + input (or paste the SKILL.md body if the skill isn't installed). | Simulate |
| **Claude.ai Project** | Simulate, then give the user the manual checklist | Simulate, then give the user the manual checklist |
| **Standalone app** | Run `python tests/run_tests.py` in the agent's folder (it calls the real agent and grades each answer; needs the API key in `.env`, and costs a little per run). Offer to run it for the user. | Give the user the command |

**Simulate** means answering as the agent, strictly from its instructions, in a clearly separated block for each case. Label the results **"simulated"**, because they show whether the instructions are right, not how the live setup behaves.

**Manual checklist** (for Claude.ai Projects, and whenever the user wants to check it themselves): save `tests/test-checklist.md` with one section per case containing the input to paste, what a good answer must and must not include, and `[ ] Pass  [ ] Fail` boxes.

**Safety during tests:** tests must never change real things. Tell test runs that they're in **test mode**: describe any file edit, message, or other action instead of doing it. The standalone `run_tests.py` blocks such actions automatically. Don't run tests that would send real emails or messages. Mark those cases "manual only".

## 5. Grade

For each case, compare the answer against `expected_output` (meaning), each `must_include`, and each `must_not_include`. Be strict and specific:

- **Pass** only if every expectation is met.
- **Fail** if any is missed, and quote the part of the answer that shows the problem.
- **Couldn't run** if the test couldn't execute (page unreachable, missing file, no API key). This is not a fail of the agent; say what's needed.
- **👀 Needs your check** if the case has `expert_check: true` and every expectation is met. Show the user the answer (or the key part of it) and ask "Is this what you'd have done?" If they say no, it becomes a fail, and their correction becomes a playbook edit and a sharper `must_include`.

## 6. Report and fix

Show a compact report in chat:

```
🧪 Test results: <Display Name>   ✅ 6 passed · ❌ 1 failed · ⚪ 0 couldn't run

✅ T1  Summarizes a normal news article
✅ T2  Summarizes a documentation page
❌ T5  Page behind a login (boundary)
     Expected: says it couldn't read the page and asks for the text
     Got: "This page appears to be about pricing plans…" (guessed from the title)
     💡 Suggested fix: add to its instructions "If you can't read the page content, never summarize from the URL or title."
...
```

Save the same report to `tests/test-report.md` with the date, method (live / simulated / manual), and the full answers.

**Visual report.** Also save the results as `tests/test-results.json` (the standalone `run_tests.py` writes this for you):

```json
{
  "agent": {"id": "<agent-id>", "name": "<Display Name>", "emoji": "<emoji>"},
  "run": {"date": "YYYY-MM-DDTHH:MM", "method": "live | simulated | manual"},
  "results": [
    {"id": "T3", "verdict": "pass | review | fail | couldnt_run", "reason": "<one plain sentence>",
     "evidence": "<short quote from the answer>", "suggested_fix": "<one sentence, failures only>", "answer": "<the agent's full answer>"}
  ]
}
```

Each result's input and expectations are filled in from `tests/test-cases.json` by `id`. Then show the visual report: one card per test, failures first, with **what we expected** beside **what it actually did**, the suggested fix, and copyable phrases.
- **Claude Code:** `python3 <skill-dir>/scripts/render_test_report.py tests/test-results.json tests/test-report.html --open`
- **Artifacts (claude.ai):** read `assets/test-report-template.html`, merge each result with its test case, replace everything between `/*REPORT_DATA_START*/` and `/*REPORT_DATA_END*/` with the JSON (escape `</` as `<\/`), and show it as an HTML artifact.

When the user later says "show my test report", re-render it from `tests/test-results.json`. Then update the agent's entry in **My Agents** so the dashboard shows its health: `python3 <skill-dir>/scripts/agent_registry.py set-tests <agent-id> --passed N --total N --method live|simulated|manual --report <full path of tests/test-report.html>` (on claude.ai, update `tests` in `my-agents.json`). This also adds the run to the agent's test history, which the dashboard shows. Count a 👀 **review** result as passed only after the user confirms the answer is right.

Then, for each failure:
1. Suggest a specific fix: an instruction change, a tool change, or an adjustment to the test if the expectation itself was unreasonable. Explain it in one plain sentence.
2. With the user's OK, apply it to every agent file (and `agent-brief.md`).
3. **Re-run all tests**, not just the failed ones, to catch fixes that break something else.

In workflow mode, a failure is usually a **playbook** fix (a missing or unclear rule), not an instruction fix. Say which: "Your playbook doesn't say what to do when…: what would you do?"

Stop after the tests pass or after 3 fix rounds. If something still fails, explain why plainly and let the user decide.

## 7. Files added to the agent folder

```
<agent-id>/tests/
├── test-cases.json      # the tests (edit or add to them anytime)
├── test-report.md       # latest results (text)
├── test-results.json    # latest results (structured, for the visual report)
├── test-report.html     # visual report
├── test-checklist.md    # manual checklist (Claude.ai Projects, or on request)
├── run_tests.py         # standalone app only (copied from the skill's scripts/run_tests_standalone.py)
└── fixtures/            # sample files used by tests, if any
```

Mention in `HOW-TO-USE.md` how to re-run the tests: "Run the Agent Builder and say *run my tests*", or `python tests/run_tests.py` for the standalone app.
