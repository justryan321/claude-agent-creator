# Claude Agent Creator

**Build your own Claude agent just by answering questions. No coding needed.**

Agent Creator is a Claude plugin. Once it's installed, run one command and Claude becomes your agent-building guide:

1. **Interview:** start from a template, describe your idea in your own words, or go step by step.
2. **Agent Card:** review a one-screen summary of your agent's job, tone, abilities, and boundaries.
3. **Test drive:** chat with your agent right away and give feedback until it behaves the way you want.
4. **Files:** get everything you need to use it, with plain-language setup steps.

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
2. Zip the folder `plugins/agent-builder/skills/create-agent` by itself.
3. On claude.ai, open **Settings → Capabilities → Skills** and upload that zip.
4. In any chat, say *"Help me create my own agent."*

## Use it

In Claude Code:

```
/agent-builder:create-agent
```

You can also just say *"I want to build an agent that…"* and Claude will pick up the skill.

## Templates included

Customer Support Helper · Research Assistant · Writing Coach & Editor · Meeting Notes → Action Items · Spreadsheet & Data Explainer · Personal Tutor · Social Media Content Helper · Code Reviewer · Personal Organizer, or start from scratch.

## Repository layout

```
.claude-plugin/marketplace.json          # makes this repo installable as a plugin marketplace
plugins/agent-builder/
├── .claude-plugin/plugin.json           # plugin manifest
└── skills/create-agent/
    ├── SKILL.md                         # the builder's flow (interview → card → test drive → files)
    └── references/
        ├── templates.md                 # starter agent templates
        ├── interview-guide.md           # question wording and ability → tool mapping
        ├── writing-instructions.md      # how the agent's instructions are written
        └── output-formats.md            # exact file formats for each destination
```

## Contributing

To add a template, add a section to `references/templates.md`. To change the interview, edit `SKILL.md` or `references/interview-guide.md`. Before opening a PR, check your changes with:

```
claude plugin validate .
```
