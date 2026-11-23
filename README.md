# Claude Agent Creator

**Build your own Claude agent just by answering questions. No coding needed.**

Agent Creator is a Claude plugin. Once it's installed, run one command and Claude becomes your agent-building guide:

1. **Start your way:**
   - **Bring what you already have:** an existing Claude (or ChatGPT/Gemini) chat, documents, old instructions from a Project or custom GPT, or a Claude data export.
   - **Pick a template.**
   - **Describe it in a sentence.**
   - **⚡ Express:** one sentence, and Claude builds the rest.

   Claude asks only about the gaps.
2. **Agent Card:** review a one-screen summary of your agent's job, tone, abilities, and boundaries.
3. **Flow Preview:** before anything is built, see a visual diagram with icons of how your agent will handle a request, what it does when something goes wrong, and what happens next. Approve it or ask for changes.
4. **Test drive:** chat with your agent right away and give feedback until it behaves the way you want.
5. **Easy setup:** in Claude Code, the builder can **install the agent for you**. On claude.ai, you get one copy-ready block and click-by-click steps. Every agent comes with an `agent-brief.md` save file, so you can come back and say *"update my agent"* anytime.
6. **Tests:** the builder checks the finished agent with generated test cases and your own examples (input → expected answer), then helps fix anything that fails.

<p align="center"><img src="docs/flow-preview.png" alt="Example Flow Preview diagram for a Page Summarizer agent" width="720"></p>

### Testing your agent

After your agent is built, the builder writes **6–8 test cases** for it: everyday requests, tricky inputs, and things it should refuse or ask about first. It runs them against the real agent and shows ✅/❌ results with plain-language fixes. **You can add your own tests too:** give it something you'd ask and the answer you'd expect back. Tests are saved with your agent, so you can say *"run my tests"* after every change to make sure nothing broke.

### Keeping track of your agents

Every agent you build is added to **My Agents** automatically. Run `/agent-builder:my-agents`, or just say *"my agents"*, to see how many you have and what each one does, in a chat table and a visual dashboard (with a light/dark theme switch):

<p align="center"><img src="docs/my-agents.png" alt="My Agents dashboard showing agent cards with what each does, where it lives, and test status" width="720"></p>

From there you can update an agent, run its tests, tag it (#work, #personal), add notes, archive agents you don't use, or delete them (always with confirmation). In Claude Code the list is saved for you in `~/.claude/agent-builder/my-agents.json`. It covers **all your projects**: agents installed "only for this project" are labeled with their project, and flagged when you're working somewhere else. On claude.ai, the builder hands you an updated `my-agents.json` to keep in a "My Agents" Project.

### Reusing an existing chat

The easiest way to reuse a chat is the **Context Capture Prompt**. The builder gives you a short message to paste into your old chat. That chat writes an "Agent Brief" of everything you discussed, and you paste the brief back into the builder. You can also paste conversations directly, upload files, or upload a Claude/ChatGPT data export (the builder includes a tool that finds the right chat inside the export). In Claude Code, it can also reuse your past Claude Code sessions.

Your agent can be delivered as any of these:

| Format | Best for |
|---|---|
| **Claude.ai Project** instructions | The easiest option: chat with your agent on claude.ai, nothing to install |
| **Claude Code subagent** | A specialist helper that Claude Code can hand tasks to |
| **Claude skill** | A reusable task you start with a slash command (works in Claude Code and on claude.ai) |
| **Standalone Python app** | Running the agent on its own using the Claude Agent SDK |

## Install

### Claude Code

In Claude Code, run:

```
/plugin install agent-builder --marketplace justryan321/claude-agent-creator
```

On older versions of Claude Code, add the marketplace first, then install:

```
/plugin marketplace add justryan321/claude-agent-creator
/plugin install agent-builder@claude-agent-creator
```

### claude.ai (skill upload)

1. Download this repository (green **Code** button → **Download ZIP**) and unzip it.
2. Zip the folder `plugins/agent-builder/skills/create-agent` by itself. Optionally, zip `plugins/agent-builder/skills/my-agents` separately too, to get the *my agents* list.
3. On claude.ai, open **Settings → Capabilities → Skills** and upload that zip.
4. In any chat, say *"Help me create my own agent."*

## Use it

In Claude Code:

```
/agent-builder:create-agent
```

You can also just say *"I want to build an agent that…"* and Claude will pick up the skill.

## Example

See [`examples/page-summarizer`](examples/page-summarizer/) for a 5-minute walkthrough that builds an agent to review a web page, summarize it, and list its key items. You can also install the finished agent directly.

## Templates included

Customer Support Helper · Research Assistant · Writing Coach & Editor · Meeting Notes → Action Items · Spreadsheet & Data Explainer · Personal Tutor · Social Media Content Helper · Code Reviewer · Personal Organizer, or start from scratch.

## Repository layout

```
.claude-plugin/marketplace.json          # makes this repo installable as a plugin marketplace
plugins/agent-builder/
├── .claude-plugin/plugin.json           # plugin manifest
├── skills/my-agents/SKILL.md            # /agent-builder:my-agents: list, dashboard, tag, archive, delete
└── skills/create-agent/
    ├── SKILL.md                         # the builder's flow (interview → card → flow preview → test drive → files → tests)
    ├── references/
    │   ├── bring-your-own-context.md    # importing chats, files, old instructions, exports
    │   ├── templates.md                 # starter agent templates
    │   ├── interview-guide.md           # question wording and ability → tool mapping
    │   ├── writing-instructions.md      # how the agent's instructions are written
    │   ├── output-formats.md            # file formats, install locations, agent-brief.md
    │   ├── flow-preview.md              # the visual flow diagram step
    │   ├── test-cases.md                # generating, collecting, running, and grading tests
    │   └── glossary.md                  # plain-language explanations of technical terms
    ├── assets/
    │   ├── flow-template.html           # the Flow Preview diagram template
    │   └── dashboard-template.html      # the My Agents dashboard template
    └── scripts/
        ├── extract_conversations.py     # reads Claude/ChatGPT exports and Claude Code sessions
        ├── render_flow.py               # renders the Flow Preview to an HTML page
        ├── agent_registry.py            # the My Agents registry and dashboard
        └── run_tests_standalone.py      # test runner copied into standalone apps
```

## Contributing

To add a template, add a section to `references/templates.md`. To change the interview, edit `SKILL.md` or `references/interview-guide.md`. Before opening a PR, check your changes with:

```
claude plugin validate .
```

## License

[MIT](LICENSE)
