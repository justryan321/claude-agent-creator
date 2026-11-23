# Interview guide

Question wording and options for Phase 2. Adapt them to what you already know; never read these out mechanically. Keep options concrete, and always allow "something else".

## 1. Purpose
- "What's the main job you want your agent to do?"
- If the answer is broad ("help with my business"), narrow it: "If it could take one thing off your plate this week, what would it be?"
- Good purpose = **verb + object + for whom** ("Answer customer questions about our bakery's orders and opening hours").

## 2. Who uses it
Options: **Just me** · **My team / coworkers** · **Customers or the public** · **A student / learner**
- Public-facing → apply the extra safety defaults from SKILL.md (says it's an AI when asked, no unapproved promises, human handoff).

## 3. Example requests
- "Give me 2–3 things someone would actually type to it." If they're stuck, offer 3 drafted examples based on the purpose and let them pick or edit.
- Also capture one **tricky** example (out of scope, angry user, missing info). You'll use it in the test drive.

## 4. Personality & tone
Tone options: **Friendly & warm** · **Professional & polished** · **Short & to the point** · **Playful & fun**
Length options: **Very short (1–3 sentences)** · **Medium (a short paragraph or list)** · **Detailed when needed**
- Optional: "Any words, phrases, or habits it should use or avoid?" (for example "never say 'per my last email'", "use British spelling", "emoji are OK").

## 5. Knowledge
Options: **General knowledge is enough** · **My own documents (FAQ, policies, notes…)** · **A website** · **Info in an app (Notion, Google Drive…)**
- For documents: ask what they are, roughly how big, and how often they change. Explain where they'll go:
  - Claude.ai Project → upload to the Project's knowledge.
  - Subagent / skill → put files in a folder the agent reads (`knowledge/`), referenced in the instructions.
  - Standalone app → a `knowledge/` folder next to the program.
- Short, stable facts (opening hours, contact email) can go straight into the instructions. Put them there.

## 6. Abilities
Ask as a multi-select in plain words, then map each to settings using the table below.

| Plain-language ability | Claude Code tools | Agent SDK `allowed_tools` | Risk note to tell the user |
|---|---|---|---|
| Search the web | `WebSearch, WebFetch` | `"WebSearch", "WebFetch"` | none |
| Read files I give it | `Read, Glob, Grep` | `"Read", "Glob", "Grep"` | none |
| Create or edit files | `Write, Edit` (+ read tools) | `"Write", "Edit"` | "It can change files, so I'll have it confirm before overwriting." |
| Run code or commands | `Bash` | `"Bash"` | "Powerful. I'll make it explain and ask before anything risky." |
| Connect to apps (Gmail, Slack, Notion, Drive, GitHub…) | MCP server tools | `mcp_servers` | "Needs a one-time connection setup; I'll include steps." |
| Just chat (no tools) | `tools:` limited to read-only or none | `allowed_tools=[]` | none |

Notes:
- On a **Claude.ai Project**, abilities come from claude.ai's own settings (web search toggle, connectors). List what to turn on in `HOW-TO-USE.md` instead of tool names.
- For app connections, explain in plain words: "an app connector (called an MCP server) is a plug that lets the agent use another app." Include the official connector setup steps for their app in `HOW-TO-USE.md` when you know them. Otherwise tell them where to look (the app's or Claude's connector directory) rather than inventing a URL or package name.

## 7. Boundaries
- "Is there anything it should **never** do or talk about?"
- "Is there anything it should **ask you before** doing?" (sending, deleting, buying, publishing, editing files)
- "When it can't help, what should it say or where should it send people?"
- If they have no ideas, propose 3 sensible ones for this agent type and let them accept or edit.

## 8. Output style
Options: **Bullet points** · **Short paragraphs** · **Step-by-step instructions** · **Tables** · **Ready-to-send emails/messages**
- Ask for a sample of output they like if they have one. It's the best guide you can get.

## 9. Where it will live
See the "Easy setup" table in SKILL.md Phase 5. You usually already know the answer from the environment (Claude Code vs. claude.ai), so propose it rather than asking from scratch: "Since you're using claude.ai, I'll set it up as a Project you can chat with. Sound good?" For the standalone app, confirm they're comfortable installing Python and getting an Anthropic API key. If not, steer to the other options.

## 10. Name
Offer 2–3 names: one descriptive ("Bakery Help Desk"), one friendly ("Penny"), one functional ("support-bot"). The id is lowercase letters, digits and hyphens only, max 64 characters.

## Turning vague answers into settings

| User says | You set |
|---|---|
| "Make it smart" | Ask for one example of a great answer; otherwise default to "Detailed when needed" + cite sources |
| "Friendly but not cheesy" | Warm, plain language, no exclamation-mark spam, no emoji unless the user uses them |
| "It should know everything about my business" | Ask for the 3–5 most important documents to start with |
| "Do whatever it takes" | Push back gently: pick specific abilities, and require confirmation for irreversible actions |
| "I don't know" | Choose the template default, state it in one line, move on |
