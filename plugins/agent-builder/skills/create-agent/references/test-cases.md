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
| `type` | `everyday` (typical request) · `tricky` (edge case, unclear or incomplete input) · `boundary` (should refuse, hand off, or ask first) · `format` (checks shape, length, tone) |
| `source` | `generated` · `you` (the user wrote it) · `your chat` (taken from imported context) |
| `input` | Exactly what a user would type. For tests that need a file, describe the file in `notes` and put a small sample in `tests/fixtures/`. |
| `expected_output` | Optional. A full example of the ideal answer. Graded on **meaning, not exact wording**, unless `notes` says "exact match". |
| `must_include` | Things a passing answer must contain or do (plain language, each one checkable) |
| `must_not_include` | Things a passing answer must not contain or do |
| `notes` | Anything the grader should know |

Each case needs at least one of `expected_output`, `must_include`, or `must_not_include`.

## 2. Generate the starter set

Build **6–8 cases** from the Agent Card, the instructions, and any imported context:

- **2–3 everyday** cases from the user's example requests.
- **1–2 tricky** cases, such as vague or incomplete input, an unusual page or file, or a very long input.
- **1–2 boundary** cases, one for each important "won't do", "asks first", or handoff rule. These matter most.
- **1 format** case that checks tone, length, and structure.
- If the user imported a past chat, turn **real question → answer they liked** pairs into cases with `source: "your chat"` and that answer as `expected_output`. These are the most valuable tests there are.

For agents that read web pages, prefer stable public pages (Wikipedia, official docs) over news that will change.

## 3. Let the user add their own

Always offer, in plain words: "Do you have a real example of something you'd ask it, and the answer you'd want back? I'll add it as a test."

Accept any form and convert it:
- **Input + full answer** → `expected_output` (graded on meaning) and derive 2–4 `must_include` items from it. Show these so the user can correct them.
- **Input + "it should…"** → `must_include` / `must_not_include`.
- **Input + "exactly this"** → `expected_output` with `notes: "exact match"`. Use this only for short, fixed answers (a contact email, a fixed phrase).
- **Input only** → propose the expectations yourself and ask "Is this what you'd expect?"

Users can add, edit, or remove cases later. Re-running the builder with "update my tests" or "add a test" should load `tests/test-cases.json` and continue from there.

## 4. Run the tests

Run each case **in a fresh context**, so earlier conversation doesn't help the agent, and keep the agent's raw answer. Then grade it (section 5). Pick the method by destination and environment:

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

Then, for each failure:
1. Suggest a specific fix: an instruction change, a tool change, or an adjustment to the test if the expectation itself was unreasonable. Explain it in one plain sentence.
2. With the user's OK, apply it to every agent file (and `agent-brief.md`).
3. **Re-run all tests**, not just the failed ones, to catch fixes that break something else.

Stop after the tests pass or after 3 fix rounds. If something still fails, explain why plainly and let the user decide.

## 7. Files added to the agent folder

```
<agent-id>/tests/
├── test-cases.json      # the tests (edit or add to them anytime)
├── test-report.md       # latest results
├── test-checklist.md    # manual checklist (Claude.ai Projects, or on request)
├── run_tests.py         # standalone app only (copied from the skill's scripts/run_tests_standalone.py)
└── fixtures/            # sample files used by tests, if any
```

Mention in `HOW-TO-USE.md` how to re-run the tests: "Run the Agent Builder and say *run my tests*", or `python tests/run_tests.py` for the standalone app.
