# Plain-language glossary

Use these explanations the first time a term comes up or whenever the user asks "what does that mean?". One or two sentences, then return to where you were.

| Term | Plain explanation |
|---|---|
| **Agent** | A version of Claude set up for one job, with its own instructions, knowledge, and abilities. Like hiring an assistant and giving them a briefing. |
| **Instructions / system prompt** | The agent's standing briefing: who it is, what it does, how it talks, and what it must not do. It reads this before every conversation. |
| **Knowledge** | Documents the agent can look things up in, like your FAQ, price list, or policies. |
| **Abilities / tools** | Things the agent can *do* beyond chatting, such as searching the web, reading files, or editing documents. |
| **App connector (MCP server)** | A plug that lets the agent use another app, like Gmail, Slack, Notion, or Google Drive. It needs a one-time connection setup. |
| **Claude.ai Project** | A workspace on claude.ai with its own instructions and uploaded files. Every chat inside it uses them. The easiest home for an agent. |
| **Claude Code** | A version of Claude that works directly with files on your computer, used from a terminal window or the Claude desktop app. |
| **Subagent** | A specialist helper inside Claude Code. Claude can hand it tasks, or you can call it by name. |
| **Skill** | A saved, reusable ability ("turn meeting notes into action items") that Claude uses when the task comes up. It works in Claude Code and on claude.ai. |
| **Slash command** | A shortcut you type starting with `/`, such as `/agent-builder:create-agent`, to start something. |
| **Plugin** | A bundle of skills and helpers you install into Claude Code in one step. This Agent Builder is a plugin. |
| **Standalone app** | A small program that runs your agent on its own, outside Claude's apps. It needs a bit of setup and an API key. |
| **API key** | A private password-like code that lets a program use Claude. You get it at platform.claude.com, and use is billed. Never share it or paste it into a chat. |
| **Terminal** | The text window where you type commands (Terminal on Mac, PowerShell on Windows). |
| **Python** | A popular programming language. The standalone app is written in it, but you don't need to know it to run the app. |
| **`.env` file** | A small private settings file where your API key is stored so the program can find it. |
| **Folder paths** (`~/.claude/agents/`) | Where a file lives on your computer. `~` means your home folder. |
| **Data export** | A download of all your past Claude chats that you can request in Settings. Useful for reusing old conversations. |
| **Model** | Which Claude "brain" the agent uses. Bigger models are smarter, smaller ones are faster and cheaper. The default is fine for most people. |
