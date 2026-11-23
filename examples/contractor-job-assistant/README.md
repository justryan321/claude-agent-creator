# Example: Job Assistant (workflow mode)

A sample of what the Agent Builder produces in **workflow mode**: for agents that have to make decisions the way *you* would at several steps of a job. This one helps a (fictional) remodeling contractor, Dana, take a job from first call to signed bid.

Compare it with the [Page Summarizer](../page-summarizer/), a single-job agent. The difference is where the know-how lives: a summarizer needs general skill, but a contractor's agent needs *Dana's* markup, contingency, minimum job size, and the moments she'd call an engineer. Claude can't guess those, so the builder captures them.

## What's in this folder

| File | What it is |
|---|---|
| [`agent-flow.html`](agent-flow.html) | The Flow Preview in the **stages** layout: a stage map, then each stage's steps, the rules it decides by, ❓ questions still open, and what passes on to the next stage. Open it in any browser. Source: [`flow.json`](flow.json). |
| [`playbook.md`](playbook.md) | Dana's rules, one table per stage (When → Do → Why), plus expert checks, hand-offs between stages, and the ❓ items still needing her answer. |
| [`tests/test-cases.json`](tests/test-cases.json) | 8 tests, including a **scenario** test (T3) that walks one job from intake to estimate, boundary tests for each expert check, and a test that the agent *asks* about an open ❓ rule instead of guessing. |

## How the conversation goes differently

1. **The builder notices the signals:** stages ("first… then once they sign…"), numbers (markup, contingency), and regulated work (permits, structural). It switches to workflow mode and says it'll take 30–45 minutes, or offers to start with one stage.
2. **Stage map:** "Walk me through a job from first call to final invoice." Dana picks 4 stages to start with.
3. **One real job, stage by stage:** for each stage it asks what she looks at, her rule of thumb, exceptions, red flags, and when she'd call someone. Then: "Tell me about a job that went wrong." (That's where the pre-1978 contingency rule came from.)
4. **No invented rules:** when Dana wasn't sure about commercial jobs or client-supplied fixtures, the builder marked them ❓ instead of picking a default. The agent asks her about those until she fills them in.
5. **Three kinds of knowledge:** rules → `playbook.md`; stable facts (terms, contacts, service area) → knowledge files; the price sheet → a dated file that the agent checks for staleness.
6. **Progress is saved** after each stage (`agent-brief.draft.md`), so an interrupted session can pick up with *"continue my agent"*.
7. **Test drive** walks a whole job through three stages, then **tests** include a multi-turn scenario. Answers whose correctness depends on Dana's expertise come back as **👀 needs your check** rather than an automatic ✅.
