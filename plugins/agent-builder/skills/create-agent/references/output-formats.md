# Output formats

Generate the files for every destination the user chose. Put all of them in one folder named `<agent-id>/`, with a `HOW-TO-USE.md` and an `agent-brief.md` at the top level. Replace every `<placeholder>`; none may remain in the final files.

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

## "Install it for me" (Claude Code only)

When the user picks install, write the agent directly to its live location instead of (or in addition to) `./<agent-id>/`, after checking that nothing with that name exists there:

| Format | Just for me, all projects | Only this project |
|---|---|---|
| Subagent | `~/.claude/agents/<agent-id>.md` | `.claude/agents/<agent-id>.md` |
| Skill | `~/.claude/skills/<agent-id>/SKILL.md` | `.claude/skills/<agent-id>/SKILL.md` |
| Knowledge files | `~/.claude/agents/knowledge/<agent-id>/` | `.claude/agents/knowledge/<agent-id>/` |

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

# Built-in tools this agent may use at all (empty list = chat only).
TOOLS = [<e.g. "Read", "Glob", "Grep", "WebSearch", "WebFetch", "Write", "Edit">]

# Tools that run without asking (keep these to safe, read-only ones).
AUTO_APPROVED = [<e.g. "Read", "Glob", "Grep", "WebSearch", "WebFetch">]

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


async def main() -> None:
    options = ClaudeAgentOptions(
        system_prompt=INSTRUCTIONS,
        tools=TOOLS,
        allowed_tools=AUTO_APPROVED,
        mcp_servers=MCP_SERVERS,
        can_use_tool=ask_before_acting,
        cwd=str(HERE),          # the agent works inside this folder
        setting_sources=[],     # ignore any personal Claude Code settings
        model="claude-opus-5-5",
    )

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
````

---

## HOW-TO-USE.md (overall shape)

```markdown
# <Display Name>

<One-sentence job.> Built with the Claude Agent Builder.

**What it does:** <2–4 bullets>
**What it won't do:** <key boundaries>

<One section per chosen destination, from above>

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
- [ ] No API keys, passwords, or personal data are written into any file (re-check imported context).
- [ ] `agent-brief.md` is included and matches the final instructions.
- [ ] If installed: the file is in the right folder and you told the user the exact first thing to type.
