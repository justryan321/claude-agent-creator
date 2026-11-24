# Interactive Builder (page mode)

A calm, full-screen web page for the whole build: one question at a time, the Agent Card filling in beside it, and the Flow Preview, test drive, setup, and tests all on the same page. The user can **type or speak** their answers (speech is turned into text by their browser). **The builder only ever writes text; the page never speaks.**

You stay in charge of the interview. Every rule in SKILL.md still applies (golden rules, phases, never inventing business rules, the Agent Card as the single source of truth). Only the place the user sees it changes: instead of chat messages and `AskUserQuestion`, you send **messages** to the page and **wait** for the user's **events**.

`scripts/builder_server.py` carries the messages. It's standard-library Python, listens only on `127.0.0.1`, needs a random token that's part of the link, and saves everything in `~/.claude/agent-builder/sessions/<session-id>/builder-session.json`.

## 1. When to use it

- **Claude Code only** (you need a shell, and the user needs a browser on the same computer). On claude.ai, use chat as before.
- It's the **recommended** start in Claude Code. Offer it first in the Phase 1 welcome (see SKILL.md), with chat as the alternative.
- If the user's first message already describes the agent or includes files, still recommend the page. Carry over what you picked up by sending it as `card` updates and starting at the matching step.
- Don't use it if the user says they prefer chat, or if the page can't open (see §6).

## 2. Start

```bash
python3 <skill>/scripts/builder_server.py start --open
```

This prints JSON with the `url`, `session_id`, and `session_dir`. In chat, say one short line, with the link in case the browser didn't open:

> I've opened the builder in your browser: <url>. Type or talk your answers there. I'll keep this window quiet. If Claude Code asks for permission here, that's me saving files.

Then send the welcome and the first question (§3), and wait.

## 3. The loop

Every turn of the interview is: **send → wait → read the events → decide → send …**

```bash
python3 <skill>/scripts/builder_server.py send - --wait <<'EOF'
[
  {"type": "phase", "step": 1, "label": "Start"},
  {"type": "say", "text": "Hi! Let's build your agent together. About **5–10 minutes**, you'll get to try it before it's finished, and nothing is final."},
  {"type": "ask", "id": "start", "text": "How would you like to start?", "style": "cards", "allow_dont_know": false, "options": [
    {"emoji": "📎", "label": "I already have something", "description": "A past chat, documents, notes, or old instructions."},
    {"emoji": "📋", "label": "Start from a template", "description": "Pick a ready-made agent and adjust it."},
    {"emoji": "💬", "label": "Describe it in a sentence", "description": "Tell me what it should do; I'll ask only about the gaps.", "recommended": true},
    {"emoji": "⚡", "label": "Express: just build it", "description": "One sentence, and I fill in the rest."}]}
]
EOF
```

Pipe the JSON in with a quoted heredoc as above (`send - --wait <<'EOF'`), so apostrophes need no escaping. Short messages can also go inline with `--json '…'`, and a JSON file works too (`send <file> --wait`).

`--wait` blocks until the user answers, then prints their events. It waits up to 110 seconds by default, which fits Claude Code's default 2-minute command timeout. For fewer quiet re-waits, pass `--timeout 540` **and** give the shell command a 10-minute timeout (600000 ms). The output looks like this:

```json
{"events": [{"type": "answer", "id": "start", "text": "Describe it in a sentence", "choices": ["Describe it in a sentence"], "via": "chip", "seq": 4}],
 "page_open": true, "waiting_on_user_for": null, "timed_out": false}
```

- **`timed_out: true` and `page_open: true`:** the user is still thinking. Run `wait` again, quietly, as many times as needed. Don't comment on it in chat.
- **`timed_out: true` and `page_open: false`:** see §6.
- **Several events at once** (an answer plus a card edit): handle them all, in order.
- **The user types in the terminal instead:** treat it as an answer, and mirror anything important on the page with a `say`.

Keep your **chat output minimal** while page mode is on: the user is looking at the page. Put everything they should read into page messages. No progress narration in the terminal.

### What to send, phase by phase

| Phase | Send |
|---|---|
| Every phase change | `phase` (1 Start · 2 Design · 3 Card & Flow · 4 Test drive · 5 Build · 6 Tests) |
| 1 Start | `say` welcome → `ask` with `style: "cards"` for the four starts |
| 1b Bring your own context | `collect` (files + paste box) → read the files from the paths in the `collected` event → `extracted` ("Here's what I picked up", each item with its `source`, plus `gaps`) → `ask` for the gaps |
| 2 Interview | One `ask` per question (2–4 options, recommended first, always allows free text). After each answer, send `card` updates for what you learned **before** the next `ask`, so the card fills in as they talk. Use `say` for one-line acknowledgements and explanations |
| 3 Agent Card | Final `card` (with `name`, `id`, `emoji`) → `review_card` |
| 3b Flow Preview | Run `render_flow.py` as usual (with `--previous` on later versions), then `flow` with `html_path` and `changes` |
| 4 Test drive | `test_drive` → for each `test_message`, reply in character with `agent` → after `feedback`, step out with a `say` (1–3 bullets of what you'll change) → on `test_done`, `test_drive_end` |
| 5 Build | `ask` for "Install it for me" vs "Just save the files" (and personal vs this project) → `notice` that Claude Code may ask for permission in the terminal → `progress` (update the same `id` as each file is written) → `how_to_use` |
| 6 Tests | `tests` (update in place as each runs) → `report` with the rendered `test-report.html` → `test_case_form` for their own tests → `done` |
| Wrap-up | `done` with the summary lines → `end` once the user has nothing else to do |

Workflow mode adds `stages` (send it again whenever a stage starts or finishes) and one `rule` per captured When → Do → Why. Mark open business rules with `needs_answer: true`. Also keep saving `agent-brief.draft.md` as `workflow-mode.md` §9 says.

### Meaning of the user's events

| Event | What happened | Do this |
|---|---|---|
| `answer` | They answered the open question (`id`), with `text` and `choices`, `via: "chip" \| "typed" \| "voice"` | Continue. Spoken answers can be rough: read for meaning, and confirm odd details in your next `say` |
| `answer` with `dont_know: true` | "You decide" / "skip" | Pick the default, say what you picked in one `say` line, update the `card` with `guess: true`. **Business rules:** mark `needs_answer: true` instead of guessing |
| `edit_answer` | They changed an earlier answer (`id` = the question, `ref` = the old event's `seq`) | Update whatever depended on it, `card` the change, and say so in one line. Don't re-ask later questions unless the change breaks them |
| `edit_card` | They edited a card line (`field`, `value`) directly | Accept it (it's already shown). Update the instructions. No reply needed, unless it conflicts with something |
| `approve` | "Looks good" on `card` or `flow` | Move on |
| `change` | "Change something" on `card` / `flow`, with `text` | Apply, then show the updated `review_card` or a new `flow` (with `--previous`) |
| `collected` | Files (saved to `files[].path` in the session folder) and/or pasted `text` | Read them, like Phase 1b |
| `extracted` | Kept (`accepted`) and dropped (`rejected`) item ids, optional `note` | Drop the rejected items from the draft |
| `test_message` | A message to the agent during the test drive | Reply in character with `agent`. Follow the drafted instructions exactly |
| `feedback` | "Something's off" (or "feedback: …") during the test drive | Step out of character: `say` the 1–3 changes, apply them, then let them keep testing |
| `test_done` | "Done testing" | `test_drive_end`, then Phase 5 |
| `test_case` | Their own test (`input`, `expected`) | Add it to the test cases, then send another `test_case_form` (or move on if they say no more) |
| `command` `switch_to_chat` | They want to continue in chat | Send `end` ("Continue in your Claude Code window"), run `transcript`, `stop`, and continue in chat from where they were |
| `command` `save_and_exit` | They'll finish later | Save the draft (`agent-brief.draft.md` in workflow mode), send `end` ("Saved. Start the builder and say *continue my agent* to pick up here."), and `stop` |

## 4. Messages you can send

All messages are JSON objects with a `type`. Text fields take light formatting: `**bold**`, `*italic*`, `` `code` ``, `- bullets`, `1. lists`, `[links](https://…)`.

| Type | Fields | Shows |
|---|---|---|
| `phase` | `step` (1–6), `label` | Updates the progress bar and adds a quiet divider |
| `say` | `text` | A paragraph from the builder (a side note during the test drive) |
| `notice` | `text` | A small centered line |
| `thinking` | `text` | A "working on it" line until your next message ("Writing your agent's files…") |
| `ask` | `id`, `text`, `sub`, `options` (strings or `{label, description, emoji, recommended, value}`), `multi`, `style` (`"cards"`), `placeholder`, `allow_dont_know` (default true), `dont_know_label` | A large question. Options with descriptions show as cards, otherwise as chips (number keys 1–9 pick them). The text box is always available for their own words |
| `card` | `name`, `id`, `emoji`, `fields: {key: {value, guess, needs_answer, source, label} \| null}` | Merges into the Agent Card panel; changed lines softly highlight. Keys: `job`, `for`, `tone`, `knows`, `can`, `wont`, `asks_first`, `answers_as`, `lives_in`; workflow: `workflow`, `decides_by`, `expert_checks`, `works_in`, `keeps_current`, `remembers`. Other keys get a `label`. `value` can be a list. `null` removes a line |
| `review_card` | `text` | The full card in the stream, with **Looks good** / **Change something**; each line can be edited |
| `collect` | `id`, `text`, `sub`, `paste_placeholder` | A drop zone for files and a paste box |
| `extracted` | `id`, `text`, `items: [{id, text, source, guess}]`, `gaps` | "Here's what I picked up" with Keep/Drop per item |
| `flow` | `html_path` (or `html`), `text`, `changes`, `approve_label` | The rendered Flow Preview inline, with **Looks good** / **Change something** |
| `test_drive` | `name`, `emoji`, `text` | Switches to test-drive mode (top bar, chat bubbles) |
| `agent` | `text` | An in-character reply during the test drive |
| `test_drive_end` | `text` | Leaves test-drive mode |
| `stages` | `stages: [{title, emoji, status: "done" \| "active"}]` | Workflow stage map along the top |
| `rule` | `stage` (title or number), `when`, `do`, `why`, `needs_answer`, `id` | A captured rule, shown inline and in the card panel's playbook (same `id` replaces) |
| `progress` | `id`, `title`, `items: [{label, status: "todo" \| "active" \| "done" \| "error", detail}]` | A checklist that updates in place for the same `id` |
| `how_to_use` | `where`, `first_message`, `examples`, `guide_path` | The ▶️ How to use it card, with Copy buttons |
| `tests` | `title`, `summary`, `cases: [{id, name, status: "pending" \| "running" \| "pass" \| "fail" \| "review" \| "skip", detail}]` | Test tiles that update in place |
| `report` | `html_path` (or `html`), `text` | The visual test report inline |
| `test_case_form` | `id`, `text`, `sub`, `skip_label` | Two boxes: "something you'd ask" and "the answer you'd expect" |
| `done` | `title`, `text`, `items` | A quiet check mark and summary |
| `end` | `text` | Closes the page's input; the session is kept |

`html_path` is read by the `send` command and inlined, so the page can show pages made by `render_flow.py` and `render_test_report.py` without serving files.

## 5. Voice

- The page uses the browser's speech recognition (Chrome, Edge, Safari). **Hold the mic button** (or hold **Space** when not typing) to talk; a quick click starts hands-free listening until the next click. A ring around the mic follows their voice level.
- Words appear in the text box as they talk, and **nothing is sent until they press Enter**, so they can fix mistakes first.
- Spoken shortcuts (typed works too): "skip" / "you decide" / "I don't know" → `dont_know`; "go back" → edit the last answer; "looks good" → approve the open card or flow; during the test drive, "done" → `test_done` and "feedback: …" → `feedback`.
- No speech support (Firefox) or a blocked microphone: the page says so in one line and typing works as usual. You don't need to do anything.
- Events from speech have `via: "voice"`. Expect run-on sentences and misheard words; never quote a spoken answer back as if it were exact wording for the agent's instructions without tidying it.

## 6. When the page isn't there

- **The page never opened** (`page_ever_opened: false` after the first `wait`; use `--timeout 120` for that first one). The browser may not be able to open on this computer (for example, a remote session). In chat: "It looks like the page didn't open. You can open <url> yourself, or we can just continue here in chat." If they choose chat, `stop` and run the interview in chat.
- **The page was closed mid-build** (`page_open: false`, and still nothing after one more wait). Say once in chat: "The builder page is closed. Reopen it here: <url>, or reply here to continue in chat." Then wait for either.
- **The server stopped** (`send` or `wait` says it isn't running): `start --resume --open`. The page replays the whole session, so nothing is lost.

## 7. Resuming ("continue my agent")

1. `builder_server.py status`. If a session exists and hasn't ended, run `start --resume --open`.
2. Run `transcript` to rebuild your picture of the interview (the card so far, every question and answer, test-drive turns, rules).
3. If the transcript ends on an unanswered question, just `wait`. Otherwise, `say` "Welcome back. Here's where we were:" with one line, and continue at the next step.

If they'd rather continue in chat, use the `transcript` output the same way and carry on there.

## 8. Privacy and safety

- The server only listens on this computer (`127.0.0.1`). The link's token is required for every request, and links to other hosts are refused.
- Uploaded files are saved in the session folder's `uploads/`. Apply the same privacy check as Phase 1b before anything goes into the agent's files.
- The session folder holds the whole interview. Mention it once at wrap-up: "Your builder session is saved in `<session_dir>`. Delete it anytime."
