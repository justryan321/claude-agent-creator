# Example: Page Summarizer

A sample run of the Agent Builder that creates an agent which **reviews a page, summarizes it, and lists the important key items**. Use it to test your install, or to see what the builder produces.

`page-summarizer.md` in this folder is the finished subagent file the builder generates for this example. You can also install it directly to skip the walkthrough.

## Try it yourself (about 5 minutes)

### 1. Install the plugin
In Claude Code:
```
/plugin install agent-builder --marketplace justryan321/claude-agent-creator
```
(On older versions: `/plugin marketplace add justryan321/claude-agent-creator`, then `/plugin install agent-builder@claude-agent-creator`.)

### 2. Start the builder
```
/agent-builder:create-agent
```

### 3. Answer like this
Your conversation will look roughly like the one below. Exact wording varies. Answer naturally.

| The builder asks | You answer |
|---|---|
| How do you want to start? | **Describe it in a sentence** |
| What should your agent do, and for whom? | *"Review a web page I give it, summarize it, and list the important key items. It's just for me."* |
| Tone and length? | **Short & to the point** |
| Abilities? (it proposes some) | Accept **Read web pages** and **Read files I give it** |
| Boundaries? (it proposes some) | Accept: stick to what the page says, and say so if the page can't be loaded |
| Output style? | **Bullet points** |
| Where should it live? | **Claude Code helper (subagent)** |
| Name? | **Page Summarizer** (id `page-summarizer`) |

Then it shows an **Agent Card** like this:
```
🪪 Agent Card: Page Summarizer  (id: page-summarizer)
Job:          Review a web page, summarize it, and list its key items
For:          Me
Tone:         Plain and concise, about 300 words max
Knows about:  General knowledge only
Can:          Read web pages, read files, search the web when asked
Won't:        Add facts that aren't on the page, or summarize a page it couldn't load
Asks first:   Nothing (it's read-only)
Answers as:   Title line → 3–5 sentence summary → 5–10 key-item bullets → "Worth noting"
Lives in:     Claude Code subagent
```
Next comes the **Flow Preview**, a diagram of how the agent will work. In Claude Code it opens in your browser; on claude.ai it appears as an artifact. You can open the finished one for this example, [`agent-flow.html`](agent-flow.html), in any browser. Its source is [`flow.json`](flow.json).

Reply **"looks good"**.

### 4. Test drive
The builder role-plays your agent. Try:
```
Summarize https://en.wikipedia.org/wiki/Photosynthesis
```
Then try the tricky case: a page that needs a login. The agent should say it couldn't read the page instead of guessing.

To adjust something, type for example `feedback: put the key items before the summary`. When you're happy, type `done`.

### 5. Install
When asked, choose **"Install it for me"** → **"Just for me, everywhere"**. The builder writes `~/.claude/agents/page-summarizer.md` and saves `agent-brief.md` and `HOW-TO-USE.md` to `./page-summarizer/`.

### 6. Test it
The builder generates test cases and offers: *"Want to add your own test?"* Try giving it one:
```
Input: Summarize this: The quarterly all-hands is moved from Friday to Thursday, Nov 12 at 3pm in Room B. Please submit questions by Tuesday.
I expect: the new date and time, the room, and the Tuesday deadline.
```
It runs every test against the installed agent and reports something like:
```
🧪 Test results: Page Summarizer   ✅ 7 passed · ❌ 0 failed
```
See [`tests/test-cases.json`](tests/test-cases.json) for this example's tests: 6 generated, plus 1 user-provided case with an expected answer. Later, say *"run my tests"* to re-check after changes.

### 7. Use it
In Claude Code, any project:
```
Use the page-summarizer agent to review https://www.anthropic.com/news
```
or type `@` and pick **page-summarizer**.

**What a good result looks like:** a title line, a short plain-language summary, 5–10 bolded key items (dates, numbers, decisions, actions), and a "Worth noting" section only when something needs caution.

## Skip the builder: install this example directly
```bash
mkdir -p ~/.claude/agents
curl -fsSL https://raw.githubusercontent.com/justryan321/claude-agent-creator/main/examples/page-summarizer/page-summarizer.md \
  -o ~/.claude/agents/page-summarizer.md
```

## Use it on claude.ai instead
Create a Project, paste everything **below the second `---` line** of `page-summarizer.md` into the Project instructions, and turn on web search in your chats. Then paste a link and say "summarize this".
