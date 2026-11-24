# Output formats

Generate the files for every destination the user chose. Put all of them in one folder named `<agent-id>/`, with a `HOW-TO-USE.md` and an `agent-brief.md` at the top level. Replace every `<placeholder>`; none may remain in the final files.

## Always included: the Flow Preview

Keep `flow.json` and `agent-flow.html` from the Flow Preview step (`flow-preview.md`) in the `<agent-id>/` folder, updated to the final design. Mention it in HOW-TO-USE.md: "Open `agent-flow.html` in your browser for a picture of how your agent works." Without file tools, the artifact or the text diagram shown earlier is enough.

## Register the agent (My Agents)

Every agent you build or update is recorded in the user's **My Agents** registry, so they can keep track of everything they've made (`/agent-builder:my-agents`). Write this entry to a temporary JSON file and run `python3 <skill-dir>/scripts/agent_registry.py upsert <entry.json>` in Claude Code. On claude.ai, add or replace the entry with the same `id` in the user's `my-agents.json` (`{"schema": 1, "agents": [...]}`), set `created`, `updated` (`YYYY-MM-DDTHH:MM`), and `version` yourself, and hand the file back.

```json
{
  "id": "<agent-id>",
  "name": "<Display Name>",
  "emoji": "<same emoji as the Flow Preview>",
  "tagline": "<Agent Card: Job>",
  "for": "<Agent Card: For>",
  "abilities": ["<Agent Card: Can, as short plain items>"],
  "scope": "personal | project",
  "project": "<only for scope 'project': full path of the project folder, e.g. /Users/sam/acme-site>",
  "destinations": [
    {"type": "subagent | skill | claude-ai-project | standalone-app", "location": "<FULL path of the installed file or folder, or 'claude.ai Project: <name>'>"}
  ],
  "brief_path": "<absolute path to agent-brief.md, or 'kept by user' on claude.ai>",
  "usage": {
    "start": "<the exact first message to type, e.g. 'Use the page-summarizer agent to summarize https://example.com/pricing' or '/meeting-notes'>",
    "examples": ["<example request 1>", "<example request 2>", "<tricky example>"],
    "guide_path": "<full path to HOW-TO-USE.md; leave out if it sits next to agent-brief.md, or on claude.ai>"
  },
  "tags": [],
  "notes": ""
}
```

- **Always use full paths** (starting with `/`, `~`, or a drive letter like `C:\`) for `location`, `project`, and `brief_path`. Never use paths like `.claude/agents/x.md`. The registry is shared by all of the user's projects, so a short path would point somewhere different depending on where it's read from. Turn a short path into a full one by joining it to the current project folder (`pwd`) before registering. The script rejects short paths.
- **Scope:**
  - `"personal"` = installed "just for me, in all projects" (under `~/.claude/`), a standalone app, or a claude.ai Project.
  - `"project"` = installed "only in this project" (under `<project>/.claude/`). Set `project` to that project's folder (the top of the repository, i.e. `git rev-parse --show-toplevel`, or the current folder if it isn't a git repository). The install path must be inside it.
- Use one `destinations` item per place it lives.
- **Always fill `usage`.** `start` is the same first message you tell the user in "▶️ How to use it" (below), and `examples` are the "Try these first" requests from HOW-TO-USE.md. The My Agents dashboard shows them as a **Start using it** box on the agent's card and a step-by-step **How to use it** section in its Details panel, and `agent_registry.py how <agent-id>` prints the same steps in chat. To save or change just these two fields later, without a new version, use `agent_registry.py set-usage <agent-id> --start "…" --example "…"`.
- Leave `tests` out; Phase 6 records them with `set-tests`. On an update, tags, notes, and the creation date are kept automatically.
- Offer one or two tags based on the job ("work", "business", "personal"), only if the user wants them.

## Always included: "▶️ How to use it" (in the chat and in HOW-TO-USE.md)

Building the files is not the finish line: the user must leave knowing **exactly how to start using the agent**. Always write `HOW-TO-USE.md` (shape at the end of this file), and right after the agent is built or installed, show this block **in the chat**, before testing starts. Fill it from the matching "HOW-TO-USE.md section" of each chosen destination below, using the real names and paths, not placeholders:

```
▶️ How to use <Display Name>

<Destination label, e.g. "In Claude Code (helper agent)">
1. <where to go, e.g. "Open Claude Code in any project" or "Open Claude Code in acme-site (it only works there)">
2. <exactly what to type, e.g. "Type: Use the page-summarizer agent to summarize https://example.com/pricing">
3. <one more way, if any, e.g. "Or type @ and pick page-summarizer">

<repeat for each destination>

Try these first:
- "<example request 1>"
- "<tricky example>" (watch how it handles this one)

📄 Full guide: <full path to HOW-TO-USE.md, or "the HOW-TO-USE.md file above">
🗂️ These steps are also in My Agents: open the agent's **Details** → **How to use it**.
```

- Keep it to the steps the user still has to do. If you installed it for them, start at "open/type"; don't repeat install steps.
- If something must happen before it works (paste instructions into a Project, upload knowledge files, add an API key to `.env`, turn on a skill), make that step 1 and say it plainly.
- In the Wrap-up, repeat only the first message to type and the guide's location.
- If the user later asks "how do I use <agent>?" (or pastes `how do I use <agent-id>` from the dashboard), show this block again. In Claude Code, `agent_registry.py how <agent-id>` prints it from My Agents; also read the agent's `HOW-TO-USE.md` for setup details.

## Always included: tests

A `tests/` folder with `test-cases.json` and `test-report.md`, plus `test-checklist.md` for Claude.ai Projects (see `test-cases.md`). For the standalone app, copy `scripts/run_tests_standalone.py` unchanged to `tests/run_tests.py`. In HOW-TO-USE.md, add a short "Check it still works" section that says how to re-run the tests.

## Always included: `agent-brief.md`

The agent's "save file". It lets the user (or the Agent Builder later) update the agent without starting over, and works as bring-your-own-context input.

```markdown
# Agent Brief: <Display Name>
_Created with the Claude Agent Builder on <date>. To change this agent, run the Agent Builder, say "update my agent", and share this file._

## Agent Card
<the final Agent Card, as shown in Phase 3>

## Example requests
- <example 1>
- <example 2>
- <tricky example>

## Where it came from
<one line per context source used, e.g. "Chat: 'Bakery FAQ bot' (Oct 2026)", "File: pricing.pdf". Or "Built from scratch".>

## Instructions
<INSTRUCTIONS>
```

For workflow-mode agents, add `## Stages`, `## Playbook` (the full `playbook.md` content), `## Still needs your answer` (❓ items), and `## Later ideas` (stages left for later) to the brief, so an update never loses the rules.

## Workflow agents (extra files)

For agents built in workflow mode (`workflow-mode.md`), add to the `<agent-id>/` folder:

```
<agent-id>/
├── playbook.md            # the decision rules, one section per stage (source of truth, user-editable)
├── knowledge/
│   ├── price-sheet.md     # changing data: one file each, "Last updated: <date>" on line 1
│   └── ...
└── jobs/                  # only if the agent remembers jobs (Claude Code / standalone app)
    └── README.md          # "One file per job. The agent creates and updates these."
```

**The playbook always travels with the instructions.** Rules the agent only *might* look up get skipped, so:

| Destination | Where the playbook goes |
|---|---|
| Claude.ai Project | Appended to `project-instructions.md` under `## Playbook`, so it's in the same paste. Changing data goes to Project knowledge. |
| Subagent | Appended to the body of `<agent-id>.md` under `## Playbook`. |
| Skill | `skill/<agent-id>/playbook.md` next to `SKILL.md`, which says "Read `playbook.md` before starting any stage." |
| Standalone app | `playbook.md` next to `instructions.md`. `agent.py` loads both. |

Keep `playbook.md` as the editable source either way. When the user edits it, rebuild the destination files from it (on "update my agent").

**Job memory** (if chosen): the instructions say where job files live (`jobs/` next to the agent, or `~/.claude/agents/knowledge/<agent-id>/jobs/` for an installed subagent), to read a job's file before working on it, and to update it at the end of each stage with status, stage, key facts, decisions, and open items. The agent needs `Read`, `Write`, `Edit` (and `Glob` to find jobs); creating or updating job files can be auto-approved, but deleting them can't. On a Claude.ai Project, instead tell the agent to end every stage with a **Job summary** block, and explain in HOW-TO-USE.md: "Use one chat per job. Paste the last Job summary at the start of the next chat, or add it to Project knowledge."

**A team of agents** (only if chosen, Claude Code): one subagent per stage (`<agent-id>-<stage>.md`), each with the core instructions, its own playbook section, and the hand-off rules, plus a coordinator `<agent-id>.md` with the stage map and hand-off rules whose description says to hand each stage to its specialist. Register the coordinator in My Agents with the specialists listed in `notes`.

**HOW-TO-USE.md additions:** a "Keeping it current" section (which changing-data files to update, how often, and that the agent warns when they're stale), a "Your playbook" section ("Edit `playbook.md` in any text editor when your rules change, then run the Agent Builder and say *update my agent*. To answer the ❓ items, say *fill in my agent's questions*."), and the job-memory steps if used.

## "Install it for me" (Claude Code only)

When the user picks install, write the agent directly to its live location instead of (or in addition to) `./<agent-id>/`, after checking that nothing with that name exists there:

| Format | Just for me, all projects | Only this project |
|---|---|---|
| Subagent | `~/.claude/agents/<agent-id>.md` | `.claude/agents/<agent-id>.md` |
| Skill | `~/.claude/skills/<agent-id>/SKILL.md` | `.claude/skills/<agent-id>/SKILL.md` |
| Knowledge files | `~/.claude/agents/knowledge/<agent-id>/` | `.claude/agents/knowledge/<agent-id>/` |

"Only this project" paths are relative to the project folder. When registering the agent, record them as full paths, plus `scope: "project"` and the project folder (see "Register the agent"). Tell the user plainly: "This agent only works when you're in **<project name>**."

Still save `agent-brief.md` and `HOW-TO-USE.md` to `./<agent-id>/` (or next to the installed file if they prefer). Then tell them exactly how to try it right now, for example: "Type: *Use the <agent-id> agent to <example 1>*". New subagents and skills are picked up within seconds, so no restart is needed. If it doesn't show up, suggest restarting Claude Code.

For the **standalone app**, if you have a shell and the user agrees, run the setup for them (create the virtual environment, install requirements, copy `.env.example` to `.env`). Then have them paste their API key into `.env` themselves. Never ask for the key in chat.

`<INSTRUCTIONS>` below always means the full agent instructions written per `writing-instructions.md`, after the test-drive revisions.

---

## A. Claude.ai Project (no install, easiest)

**Files**
```
<agent-id>/
├── HOW-TO-USE.md
├── project-instructions.md      # <INSTRUCTIONS>, ready to paste
└── knowledge/                   # only if the agent uses documents
    └── README.md                # list of documents the user should upload
```

`project-instructions.md` contains only `<INSTRUCTIONS>`: no frontmatter, no commentary.

**HOW-TO-USE.md section**
```markdown
## Use it on claude.ai (Projects)
1. Go to claude.ai and click **Projects** → **Create project**. Name it "<Display Name>".
2. Open **Project instructions** (sometimes labeled "Set custom instructions"), then paste everything from `project-instructions.md`.
3. <If knowledge> Under **Project knowledge**, upload: <list of documents>.
4. <If web search> In a chat inside the project, turn on **Web search** from the tools menu.
5. <If app connections> Open **Settings → Connectors** and connect <apps>.
6. Start a new chat inside the project and try: "<example request 1>".
```
(Menu names on claude.ai change from time to time. Add: "If a button has a slightly different name, look for the closest match.")

---

## B. Claude Code subagent

A Markdown file whose top part (between `---` lines) holds settings, with the instructions below it.

**Files**
```
<agent-id>/
├── HOW-TO-USE.md
├── <agent-id>.md                # the subagent
└── knowledge/                   # optional
```

**`<agent-id>.md`**
```markdown
---
name: <agent-id>
description: <what it does>. Use when <concrete trigger situations/phrases>.
tools: <comma-separated tools from the abilities table in interview-guide.md>
model: inherit
---

<INSTRUCTIONS>
```

Rules:
- `name`: lowercase letters, digits, hyphens; no `:`.
- `tools`: list only what the abilities need. For a "just chat" agent, use `Read` so it can at least read what it's given. Leave `tools` out entirely only if the user explicitly wants every tool.
- Optional fields (add only when useful): `model` (`sonnet`, `opus`, `haiku`, or `inherit`); `permissionMode` (`default` normally; `plan` for an advisor that should never change things); `mcpServers` for app connections; `color` (`red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`) so the user can spot it.
- If it uses knowledge files, the instructions must point at them with a path the agent can read, for example `~/.claude/agents/knowledge/<agent-id>/` for a personal install, or `.claude/agents/knowledge/<agent-id>/` for a project install. Tell the user to copy the `knowledge/` folder there.

**HOW-TO-USE.md section**
```markdown
## Use it in Claude Code (as a helper agent)
1. Copy `<agent-id>.md` into one of these folders:
   - **Just for you, in every project:** `~/.claude/agents/`
   - **Only for one project (and shareable with your team):** `<your-project>/.claude/agents/`
2. <If knowledge> Copy the `knowledge/` folder to <path used in the instructions>.
3. In Claude Code, ask: "Use the <agent-id> agent to <example request 1>", or type `@` and pick it from the list.
4. To make it the main agent for a whole session, start Claude Code with: `claude --agent <agent-id>`
```
For "Install it for me", see the install table near the top of this file.

---

## C. Claude skill (Claude Code and claude.ai)

A skill is a folder with a `SKILL.md` file. Use this format when the agent is a repeatable *task* ("turn notes into action items") more than an ongoing *persona*.

**Files**
```
<agent-id>/
├── HOW-TO-USE.md
└── skill/
    └── <agent-id>/
        ├── SKILL.md
        └── reference/          # optional: knowledge documents
```

**`SKILL.md`**
```markdown
---
name: <agent-id>
description: <what it does>. Use when <concrete trigger situations/phrases>.
---

<INSTRUCTIONS, written as instructions for carrying out the task. If there are reference files, add: "Reference material is in the `reference/` folder next to this file. Read it when <situation>.">
```

**HOW-TO-USE.md section**
```markdown
## Use it as a skill
**In Claude Code:** copy the folder `skill/<agent-id>/` into `~/.claude/skills/` (for all projects) or `<your-project>/.claude/skills/`. Then type `/<agent-id>`, or just ask for the task and Claude will use the skill when it fits.

**On claude.ai:** zip the `<agent-id>` folder (the one containing `SKILL.md`). In claude.ai open **Settings → Capabilities → Skills** (or **Customize → Skills**) and upload the zip. Turn it on, then ask for the task in any chat.
```

---

## D. Standalone app (Python, Claude Agent SDK)

For users who want the agent to run on its own, outside Claude Code or claude.ai. It needs Python 3.10+ and an Anthropic API key from platform.claude.com. The SDK bundles the Claude Code engine, so the agent gets the same built-in tools.

**Files**
```
<agent-id>/
├── HOW-TO-USE.md
├── agent.py
├── instructions.md            # <INSTRUCTIONS>
├── requirements.txt
├── .env.example
├── .gitignore
├── tests/                     # see test-cases.md (run_tests.py is copied as-is)
└── knowledge/                 # optional
```

**`requirements.txt`**
```
claude-agent-sdk
python-dotenv
```

**`.env.example`**
```
# Copy this file to .env and paste your key after the = sign.
# Get a key at https://platform.claude.com (API keys). Never share it.
ANTHROPIC_API_KEY=
```

**`.gitignore`**
```
.env
.venv/
__pycache__/
```

**`agent.py`**: fill in the three marked lists from the abilities table in `interview-guide.md`.
```python
"""<Display Name>: <one-line job>. Run with:  python agent.py"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    TextBlock,
    ToolPermissionContext,
)

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

AGENT_NAME = "<Display Name>"
INSTRUCTIONS = (HERE / "instructions.md").read_text(encoding="utf-8")
# Workflow agents: the playbook always travels with the instructions.
if (HERE / "playbook.md").exists():
    INSTRUCTIONS += "\n\n" + (HERE / "playbook.md").read_text(encoding="utf-8")

# Built-in tools this agent may use at all (empty list = chat only).
TOOLS = [<e.g. "Read", "Glob", "Grep", "WebSearch", "WebFetch", "Write", "Edit">]

# Tools that run without asking (keep these to safe, read-only ones).
AUTO_APPROVED = [<e.g. "Read", "Glob", "Grep", "WebSearch", "WebFetch">]

MODEL = "claude-opus-5-5"

# App connections (MCP servers). Leave empty if none.
MCP_SERVERS = {
    # "<server-name>": {"type": "http", "url": "<server URL from the app's docs>"},
}


async def ask_before_acting(
    tool: str, tool_input: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Any tool not in AUTO_APPROVED asks you first."""
    print(f"\n⚠️  {AGENT_NAME} wants to use {tool}:")
    for key, value in tool_input.items():
        print(f"   {key}: {str(value)[:300]}")
    answer = await asyncio.to_thread(input, "Allow? (y/n) ")
    if answer.strip().lower() in ("y", "yes"):
        return PermissionResultAllow()
    return PermissionResultDeny(message="The user said no. Ask what they'd like instead.")


async def test_mode_block(
    tool: str, tool_input: dict, context: ToolPermissionContext
) -> PermissionResultDeny:
    """During tests, never change anything for real."""
    return PermissionResultDeny(
        message="Test mode: don't do this for real. Describe exactly what you would do instead."
    )


def build_options(test_mode: bool = False) -> ClaudeAgentOptions:
    """The agent's settings. tests/run_tests.py reuses them with test_mode=True."""
    return ClaudeAgentOptions(
        system_prompt=INSTRUCTIONS,
        tools=TOOLS,
        allowed_tools=AUTO_APPROVED,
        mcp_servers=MCP_SERVERS,
        can_use_tool=test_mode_block if test_mode else ask_before_acting,
        cwd=str(HERE),          # the agent works inside this folder
        setting_sources=[],     # ignore any personal Claude Code settings
        model=MODEL,
    )


async def main() -> None:
    options = build_options()

    print(f"👋 {AGENT_NAME} is ready. Type your message, or 'quit' to exit.\n")
    async with ClaudeSDKClient(options=options) as client:
        while True:
            user_text = (await asyncio.to_thread(input, "You: ")).strip()
            if user_text.lower() in ("quit", "exit"):
                break
            if not user_text:
                continue
            await client.query(user_text)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"\n{AGENT_NAME}: {block.text}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

Notes for generation:
- `TOOLS` and `AUTO_APPROVED` must be valid Python lists; use `[]` for none. Never auto-approve `Write`, `Edit`, or `Bash`.
- For MCP, use the server's documented `http` URL, or a `stdio` entry: `{"type": "stdio", "command": "npx", "args": ["-y", "<package>"]}`. MCP tool names look like `mcp__<server-name>__<tool>`; add specific read-only ones to `AUTO_APPROVED` only if the user wants that. Never invent a server URL or package name. If you don't know it, leave the entry commented out and explain in HOW-TO-USE.md where to find it.
- If the user named a different model, use it. Otherwise keep `claude-opus-5-5` and mention in HOW-TO-USE.md that they can switch to a cheaper model (for example `claude-haiku-5-5`) for simple agents.
- For SDK details beyond this template, the reference is https://code.claude.com/docs/en/agent-sdk/overview

**HOW-TO-USE.md section**
````markdown
## Run it as a standalone app
You'll need **Python 3.10 or newer** (python.org) and an **Anthropic API key** (platform.claude.com → API keys). Using the API is billed per use.

1. Open a terminal in this folder.
2. Create a private Python environment and install the parts:
   - macOS/Linux:
     ```
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```
   - Windows (PowerShell):
     ```
     py -m venv .venv
     .venv\Scripts\Activate.ps1
     pip install -r requirements.txt
     ```
3. Copy `.env.example` to a new file named `.env` and paste your API key after `ANTHROPIC_API_KEY=`.
4. <If knowledge> Put your documents in the `knowledge/` folder.
5. Start it: `python agent.py`. Try: "<example request 1>". Type `quit` to stop.

Whenever the agent wants to do something that changes things (like editing a file), it will ask you first.

**Test it:** `python tests/run_tests.py` runs every test in `tests/test-cases.json` against your agent and writes `tests/test-report.md`. Add `--only T1,T3` to run some of them. Each run uses your API key and costs a little.
````

---

## HOW-TO-USE.md (overall shape)

```markdown
# <Display Name>

<One-sentence job.> Built with the Claude Agent Builder.

**What it does:** <2–4 bullets>
**What it won't do:** <key boundaries>

<One section per chosen destination, from above>

## Check it still works
<One line per destination: "Run the Agent Builder and say *run my tests*", or `python tests/run_tests.py` for the standalone app, or "Follow `tests/test-checklist.md`" for a Claude.ai Project.> Add your own tests by saying *add a test*.

## Try these first
- "<example request 1>"
- "<example request 2>"
- "<tricky example>" (watch how it handles this one)

## Changing it later
Your agent's behavior lives in its instructions (<file name>). Edit that text in any text editor, or run the Agent Builder again, say "update my agent", and share `agent-brief.md`. It remembers everything about how this agent was built.
```

---

## Final checklist (run silently before presenting files)

- [ ] No `<placeholder>` text remains anywhere.
- [ ] `name` / id is lowercase-hyphenated and identical across files.
- [ ] `description` says what it does **and** when to use it.
- [ ] Tools match the abilities chosen; nothing extra. Risky tools are never auto-approved.
- [ ] Instructions include the boundaries, handoff, and situation-specific additions from `writing-instructions.md`.
- [ ] Test-drive feedback is reflected in the instructions.
- [ ] HOW-TO-USE.md has steps for every chosen destination and 2–3 example requests.
- [ ] The "▶️ How to use it" block was shown in the chat with the exact first message to type, and the My Agents entry has a matching `usage.start` and `usage.examples`.
- [ ] No API keys, passwords, or personal data are written into any file (re-check imported context).
- [ ] `agent-brief.md` is included and matches the final instructions.
- [ ] The agent is registered in My Agents (`upsert` done, or `my-agents.json` handed back on claude.ai).
- [ ] `tests/test-cases.json` exists (6–8 generated cases plus any from the user), and the latest results are in `tests/test-report.md`.
- [ ] The Flow Preview was approved, and `agent-flow.html` (if files are possible) matches the final design.
- [ ] If installed: the file is in the right folder and you told the user the exact first thing to type.
- [ ] Workflow agents: `playbook.md` is included and also travels with the instructions for each destination; no business rule was invented (unknowns are ❓); every changing-data file has a "Last updated" date; expert checks appear in the instructions, playbook, and tests; `agent-brief.draft.md` is replaced by the final brief.
