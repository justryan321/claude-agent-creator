---
name: my-agents
description: Shows and manages every agent the user has built with the Agent Builder. It covers how many there are, what each one does, where each lives, and how its tests went, in a visual dashboard plus a chat table. It also lets users update, test, tag, add notes to, archive, or delete them. Use when the user says "my agents", asks to list, show, find, count, organize, or clean up their agents, asks what their agents do, or runs /agent-builder:my-agents.
---

# My Agents

You help a **non-technical** user keep track of the agents they've built: how many they have, what each one does, where it lives, and whether it's healthy. Use plain words, keep it short, and do the bookkeeping for them.

The list lives in a **registry** (`my-agents.json`) managed by the script `../create-agent/scripts/agent_registry.py`. Paths in this file are relative to this skill's folder. Never edit the registry by hand; always use the script, which validates entries and keeps a `.bak` backup.

## 1. Load the list

- **Claude Code** (you can run commands): the registry is at `~/.claude/agent-builder/my-agents.json`, the script's default. Run:
  ```bash
  python3 <create-agent-dir>/scripts/agent_registry.py list --all
  ```
  `<create-agent-dir>` is the `create-agent` folder next to this skill's folder. Run it from the user's current project folder: the list covers agents from **every** project, and the current folder is used to flag the ones that only work in a different project.
- **claude.ai / no file access between chats:** ask: "Do you have your **my-agents.json** file? Upload it here (it may be in your 'My Agents' Project)." If you can run code, save it and pass `--registry <path>` to every command. If you can't, read the JSON yourself and follow the same rules, then hand back an updated file (step 5).
- **No registry yet:** say they haven't built any agents with the builder yet (or the list was started on another device). Offer to build one with `/agent-builder:create-agent`. If they have agents built some other way, offer to add one to the list by running the builder's "update my agent" flow on its files.

### Personal vs project agents

The list includes every agent the user has built, from all their projects. Each one has a **scope**:
- **Works in every project** (personal): installed under `~/.claude/`, a standalone app, or a claude.ai Project ("On claude.ai").
- **Project only**: installed inside one project's `.claude/` folder. It only works when Claude Code is opened in that project. The list marks these `⛔ only works in <project>` when the user is somewhere else.
- **Where it works: unknown**: an older entry saved without full paths. Suggest "update <id>" to fix it, and don't move or delete its files automatically.

Explain this in one plain sentence when it matters, for example: "API Code Reviewer lives in your *acme-api* project, so it only works when you open that project." To show only the agents that work right here, add `--usable-here` to `list`.

## 2. Show the overview

Start with one line of totals, then a compact table:

```
🗂️ My Agents: 3 active · 1 archived · 1 needs attention

📄 Page Summarizer       Reviews a page, summarizes it…      Claude Code subagent   ✅ 7/7   #work
🥐 Bakery Help Desk      Answers customer questions…         Claude.ai Project      ❌ 5/7   #business
📝 Meeting Notes Helper  Turns notes into action items…      Claude skill           · not tested
```

"Needs attention" counts agents with failing tests, no tests, or no saved "how to start" (older agents; fix with "add how-to-use for all my agents"). Mention them in one helpful line, for example: "Bakery Help Desk failed 2 tests last time. Want to look at it?"

Then show the **visual dashboard**:
- **Artifacts available** (claude.ai, Claude Desktop): read `../create-agent/assets/dashboard-template.html`, replace everything between `/*AGENTS_DATA_START*/` and `/*AGENTS_DATA_END*/` with `{"generated": "<now>", "agents": [...]}` (escape `</` as `<\/`), and present it as an HTML artifact titled "My Agents". If you can't read the template (for example, this skill was uploaded to claude.ai on its own), build a simple HTML artifact with the same parts: totals, a search box, and one card per agent (emoji, name, what it does, where it lives, test status, tags).
- **Claude Code:** run
  ```bash
  python3 <create-agent-dir>/scripts/agent_registry.py dashboard ~/.claude/agent-builder/my-agents.html --open
  ```
  If the browser doesn't open (remote or headless machine), give the full path and say "open this file in your web browser".
  After that, any change made with the script (update, tests, tags, how-to-use, …) refreshes this page automatically; tell the user to **reload** it. On claude.ai, an artifact doesn't update itself: after any change, show a new dashboard artifact built from the updated `my-agents.json`.

The dashboard has:
- totals
- a **Needs attention** strip: failing tests, no tests, missing files, unclear locations, no saved "how to start", each with a phrase to fix it
- search, a sort menu, and filters (active/archived, where it lives, tags)
- a System / Light / Dark theme switch, remembered in that browser
- a card per agent with one-click **Copy** buttons on the phrases to paste into the chat
- a **Start using it** box on each card with the exact first message to type (from the entry's `usage.start`)
- a **Details** panel per agent: **How to use it** (step by step for each place it lives, example requests, and a link to its `HOW-TO-USE.md`), full file paths, test history, a preview of its instructions, and links to its Flow Preview and test report.

Each card shows what the agent does, how to start using it, its abilities, test status, tags, and notes.

## 3. Offer actions

Ask what they'd like to do, offering only what makes sense, e.g. "Want to update one, run its tests, add a tag or note, or tidy up old ones?"

| They want to… | Do this |
|---|---|
| **See details** of one | `check <id>` (where it works, and each file's full path with ✅ / ❌ missing), then summarize it in plain words: job, where it lives, abilities, last test, notes. Use `show <id>` for the raw entry. |
| **Use it** ("how do I use…", "how do I start…") | Run `how <id>` and show the steps in plain words: where to go, the exact first message to type, and examples to try. If it lives in another project, say to open that project first. For setup details (knowledge files, API key, Project instructions), read the `HOW-TO-USE.md` path it prints. On claude.ai, build the same steps from the entry's `destinations` and `usage`. |
| **Add how-to-use** to older agents ("how to start" missing) | Hand off to the Agent Builder's "Adding how-to-use to an existing agent" (`/agent-builder:create-agent`), for one agent or all of them. It reads each agent's brief and saves the first message and examples with `set-usage`, without rebuilding anything. |
| **Change / improve** one | Hand off to the Agent Builder's "update my agent" flow (`/agent-builder:create-agent`), loading the agent from its `brief_path` (or the file at its destination). Full paths mean this works from any project. For a project-only agent, mention that testing it live works best from inside its project. The builder re-registers it afterwards. |
| **Run its tests** / **add a test** | Hand off to the Agent Builder's Phase 6 with that agent's `tests/test-cases.json` (in the folder holding `agent-brief.md`). Results are saved with `set-tests`. |
| **Tag** it | `tag <id> --add work clients` / `--remove old`. Suggest a few tags if they're unsure (work, personal, business, team, experiment). |
| **Add a note** | `note <id> "…"`. This replaces the note; read the current one first and combine them if they want to keep it. |
| **Archive** (hide, keep everything) | `archive <id>`. Explain it's reversible with "restore". For subagents/skills, offer to also move the file out of the active folder (e.g. into `~/.claude/agent-builder/archive/`) so Claude stops using it, but only with a yes. |
| **Restore** | `restore <id>`, and move any archived file back. |
| **Delete** | Follow "Deleting safely" below. |

Commands are `python3 <create-agent-dir>/scripts/agent_registry.py [--registry PATH] <command> …`. After any change, show the updated line for that agent, not the whole table.

### Deleting safely

1. Run `check <id>` and list **exactly** what would be deleted, using the full paths it prints: each file or folder on this computer marked ✅, plus the agent folder with `agent-brief.md` and its tests. Skip anything marked ❌ missing (already gone). Note things you *can't* delete for them (☁️ a claude.ai Project, an uploaded skill) and tell them where to remove those by hand. If `check` shows a path that isn't a full path (⚠️), **don't delete anything**. Explain that the location is unclear and offer to remove just the list entry.
2. Ask them to confirm by typing **"yes, delete <Name>"**. Anything else cancels. Suggest **archive** instead if they might want it back.
3. Delete only the confirmed paths, then run `remove <id>`. Confirm what was removed.

Never delete anything outside the listed full paths, never build a path yourself by joining it to the current folder, and never delete in bulk without confirming each agent. The same rules apply when archiving moves a file aside.

## 4. Keeping the list accurate

- The Agent Builder adds agents automatically when they're built, updates them when they change, and records test results. You don't need to add them by hand.
- If an entry's file is missing (for example, they deleted it manually), mention it and offer to archive or remove the entry.
- Entries flagged "location unclear" were saved before full paths were required. Running "update <id>" re-registers them with full paths and the right scope.

## 5. On claude.ai: hand the file back

Files don't persist between chats there, so after **any** change, give the user the updated `my-agents.json` (as a downloadable file, or a code block if downloads aren't available) and say: "Keep this file. Upload it to your **My Agents** Project (Project knowledge) so it's there next time, replacing the old one." Suggest creating that Project the first time.
