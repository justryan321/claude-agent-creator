# Workflow mode: agents that need the user's expertise

Most agents do one job: summarize a page, answer FAQ questions, polish an email. The standard flow handles those in 5–10 minutes.

Some agents carry a **business process with judgment at every step**: a general contractor's intake → site visit → estimate → bid → change orders, a bookkeeper's month-end close, a recruiter's screen → interview → offer. The value of these agents is the owner's know-how: their rules of thumb, thresholds, exceptions, and "that's when I call someone". That know-how is rarely written down, Claude can't guess it, and a wrong guess (a markup, a permit threshold, a payment term) is worse than no agent.

Workflow mode changes the standard flow so it captures that know-how, keeps it safe through updates, and checks it properly. Everything in SKILL.md still applies unless this file says otherwise.

## 1. When to switch on

Switch on when **two or more** of these show up in the user's description, imported context, or template:

- **Stages:** the work moves through distinct steps over time ("first we… then… once the client signs…").
- **Judgment words:** "it depends", "usually", "unless", "case by case", "I decide based on…".
- **Numbers and thresholds:** prices, markups, percentages, deadlines, limits, sizes.
- **Regulated or high-stakes work:** construction, trades, legal, finance, insurance, healthcare admin, HR, real estate, anything with licenses, codes, contracts, or money owed.
- **Several people involved:** clients, subcontractors, suppliers, inspectors, staff.
- **Tracking things over time:** jobs, cases, clients, orders, projects that last weeks.

The **🏗️ Trade & Service Business Ops** template (`templates.md`) always uses workflow mode.

Tell the user in one or two sentences, and set expectations honestly:

> "This is a bigger agent than most: it needs to make decisions the way *you* would at each step of a job. I'll switch to **workflow mode**: we'll walk through one real job together so I can capture your rules of thumb. Plan on 30–45 minutes, and I'll save your progress as we go so nothing is lost."

If they'd rather go fast, offer to build **just one stage first** ("Let's start with estimates; we can add the other stages later"). A single stage done well beats five stages full of guesses.

## 2. What changes from the standard flow

| Standard flow | In workflow mode |
|---|---|
| "I don't know" / "you decide" → pick a default | Still fine for tone, format, and name. For **business rules** (prices, thresholds, policies, legal/safety calls), never invent a value. Mark it **❓ needs your answer** and keep going; the agent will ask the user at that point instead of guessing. |
| Express mode fills everything | Express is not offered. If the user asked for it, explain in one line why this agent needs their input and offer "one stage first" instead. |
| Purpose is one sentence | Purpose is one sentence **plus a stage list** (section 3). |
| Knowledge = documents to look up | Knowledge splits into **rules** (the playbook), **reference facts**, and **changing data** (section 5). |
| Instructions are 150–600 words | Core instructions stay 150–600 words. The rules live in `playbook.md`, which has no length limit and always travels with the instructions. |
| Flow Preview: 4–7 steps | Two levels: a stage overview, then each stage's steps and decision rules (`flow-preview.md`, "Workflow agents"). |
| "Asks first" = risky actions | Also **expert checks**: judgment calls the agent flags for a human instead of deciding (section 6). |
| Test drive: single messages | Walk one realistic job through several stages (section 8). |
| 6–8 single-message tests | Adds **scenario tests** (a job across several turns) and marks domain answers **👀 needs your check** (`test-cases.md`). |
| Files saved at the end | A draft brief is saved after each stage of the interview (section 9). |

## 3. Map the stages

Ask: "Walk me through what happens from the moment a new <job/client/case> comes in until it's finished. Just the big steps." Then propose a stage list for them to correct, for example:

```
1. 📞 Intake: new lead calls or emails
2. 📐 Site visit and scope
3. 🧮 Estimate
4. 📄 Bid / proposal
5. 🔁 Change orders during the job
6. ✅ Closeout and final invoice
```

Then ask which stages the agent should actually help with. **3–6 stages** is the sweet spot. If they list more than 8, suggest starting with the 3–4 that take the most of their time, and note the rest under "Later ideas" in the brief.

For each chosen stage, record: what comes in, what the agent produces, and who sees the result (the user only, or a client/sub/supplier).

## 4. Capture the decisions (walk through a real job)

This is the heart of workflow mode. People describe their rules poorly in the abstract but very well when telling the story of a real job. So:

1. Ask: "Think of a recent job that went fairly typically. Can you walk me through it, stage by stage?" (If they'd rather not use a real one, ask them to make up a typical one.)
2. At each stage, ask up to 3 of these, choosing the ones that fit:
   - **Look at:** "What did you look at or ask about to decide what to do here?"
   - **Rule of thumb:** "Is there a number or rule you usually go by?" (markup, contingency, minimum job size, turnaround time)
   - **Exceptions:** "When do you break that rule?" ("older homes get 15% contingency instead of 10%")
   - **Red flags:** "What makes you walk away, slow down, or charge more?"
   - **Call someone:** "When would you stop and call someone (engineer, inspector, lawyer, your bookkeeper) instead of deciding yourself?"
   - **Who signs off:** "Does anything here need your OK before it goes out?"
3. Then ask about **one job that went wrong** or was unusual: "What happened, and what would you want the agent to catch next time?" This is where the most valuable rules hide.
4. After each stage, play back what you captured as rules in their words and ask "Did I get that right?" before moving on.

Write each rule as **When → Do → Why** (the "why" helps the agent handle cases the rule doesn't quite cover). Keep the user's own numbers and wording. Anything they couldn't answer gets **❓ needs your answer**. Don't fill it in.

Also ask once, early: **"Where do you work?"** (state/province, city or county). Codes, permits, licensing, lien rules, and tax all vary by place. If the agent ever touches those, its instructions must name the place and say to check local rules rather than assume.

## 5. Sort knowledge into three kinds

| Kind | Examples | Where it goes |
|---|---|---|
| **Rules** (how decisions are made) | Markup by job type, when to require a change order, which jobs to turn down, when to call an engineer | `playbook.md`. Always loaded with the instructions. |
| **Reference facts** (stable) | Services offered, service area, license number, standard contract clauses, warranty terms, sub/supplier contacts | Short ones go in the instructions; longer ones become knowledge files |
| **Changing data** (goes out of date) | Material prices, sub rates, lead times, current workload, schedule | A separate knowledge file per item with an **"Last updated: <date>"** line at the top. The instructions say: "If the date is more than <N> weeks old, warn that prices may be out of date and ask before using them." Ask the user how often each one changes and who updates it. |

Never put changing data into the playbook or the instructions. It would silently go stale.

## 6. Expert checks (judgment the agent must not make alone)

Separately from "asks first" actions, ask: "Which calls should always come back to you, or to a professional, no matter what?" Propose sensible ones for the trade. For a general contractor, for example:

- Anything structural (removing walls, beams, foundations) → flag for the user / an engineer.
- Whether work needs a permit or meets code → say what to check and with whom; never state that something is code-compliant.
- Contract language, liens, disputes, insurance claims → draft for the user's review only; suggest a lawyer for anything unusual.
- Safety hazards (asbestos, lead paint, electrical, gas) → stop and flag.
- Final prices sent to a client → always the user's OK.

These become a **guard** step or branch in the Flow Preview, the **Expert checks** line on the Agent Card, a section in the playbook, and boundary tests.

## 7. Playbook format (`playbook.md`)

One section per stage, then the cross-cutting rules. Use the user's words. Example:

```markdown
# Playbook: <Display Name>
_The rules <Display Name> follows at each stage. Captured from <user/business> on <date>. Edit freely; run "update my agent" after big changes so the tests are re-run._

Works in: <place>. Local rules (permits, codes, licensing, tax) differ by place: check, don't assume.

## Stage 1 · 📞 Intake
Goal: decide whether the lead is worth a site visit, and book it.
| When | Do | Why |
|---|---|---|
| Job is under $2,500 | Politely decline and refer to <handyman contact> | Not worth a site visit at our size |
| Caller mentions water damage or mold | Book within 48 hours, flag as urgent | Damage gets worse fast |
| Outside <service area> | Decline kindly | Travel time kills the margin |
| ❓ Commercial work | needs your answer: do we take it? | |

## Stage 3 · 🧮 Estimate
| When | Do | Why |
|---|---|---|
| Any job | Materials from `price-sheet.md` + labor at $<rate>/hr, then 18% markup | Covers overhead and profit |
| House built before 1978 | Add 15% contingency (10% otherwise) and flag possible lead paint | Older houses hide surprises |
| Price sheet more than 4 weeks old | Warn and ask before using it | Lumber prices move |

## Expert checks (always flagged, never decided alone)
- Structural changes → "This needs an engineer's review before pricing."
- …

## Hand-offs between stages
- Intake → Site visit: client name, address, contact, job type, urgency, notes.
- Estimate → Bid: line items, assumptions, exclusions, contingency used.

## Still needs your answer
- Commercial work: do we take it? (Stage 1)
```

The **Hand-offs** section says exactly what information moves from one stage to the next. It's what keeps a multi-step job consistent.

## 8. Test drive in workflow mode

Run one realistic job through at least 3 stages in a row, using the job the user described in section 4 (or a close variation). Show the hand-off between stages explicitly ("📋 Passing to Estimate: …"). Include one moment that should trigger an expert check or a ❓ item, so the user sees the agent ask instead of guess. Every rule correction becomes a playbook edit, not an instruction edit.

## 9. Save progress as you go

Long interviews get interrupted. After the stage map, and after each stage's rules are confirmed:

- **Claude Code:** write `./<agent-id>/agent-brief.draft.md` (the Agent Card so far, stage list, and `playbook.md` content so far). Mention it once: "I'm saving your progress in `<path>`. If we get cut off, start the builder again and say *continue my agent*."
- **claude.ai:** every two stages, offer a **progress snapshot**: one copy-ready block with everything captured so far, titled "Agent Builder progress: <Display Name>". Say they can paste it into a new chat with the builder to pick up where they left off.

When resuming from a draft or snapshot, rebuild the card, show which stages are done, and continue at the next one. Replace the draft with the final `agent-brief.md` when the agent is built.

## 10. One agent or a team?

Default to **one agent that knows every stage**. It's simpler to set up and the hand-offs stay in one place. Suggest a **team** (one coordinator plus one specialist per stage, as Claude Code subagents) only when:

- different people use different stages (the office manager handles intake, the owner handles estimates), or
- one stage needs much more powerful abilities than the others (for example, only the scheduler can edit the calendar), or
- the playbook for a single stage is very large.

For a team, each specialist gets the core instructions plus only its stage's playbook section and the hand-off rules; the coordinator gets the stage map and hand-off rules. See "Workflow agents" in `output-formats.md`.

## 11. Remembering each job

Multi-stage work often spans weeks. Ask: "Should the agent keep track of each job between conversations?"

- **Claude Code / standalone app:** yes, with a `jobs/` folder. The agent keeps one file per job (`jobs/<short-job-name>.md`) with status, stage, key facts, decisions made, and open items, and updates it at the end of each stage. It reads that file first when the user mentions the job.
- **Claude.ai Project:** no shared memory between chats is guaranteed, so the agent ends each stage with a **Job summary** block. The user starts one chat per job and pastes the latest summary into the next chat, or adds it to the Project's knowledge.

Job files contain client information, so mention that they stay on the user's computer, and keep them out of anything shared (see the privacy step in `bring-your-own-context.md`).
