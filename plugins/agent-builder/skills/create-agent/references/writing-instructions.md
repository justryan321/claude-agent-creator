# Writing the agent's instructions (system prompt)

The instructions are the heart of the agent. Every output format embeds the same instructions, so write them once, well.

## Principles

1. **Second person, natural prose.** "You are Penny, the help desk assistant for Sunrise Bakery…" Address the agent directly.
2. **Explain the why.** "Keep replies under 4 sentences, because customers read these on their phones" works better than "BE BRIEF!!!". Avoid ALL-CAPS, "CRITICAL", and stacks of "NEVER". Calm, clear guidance is followed better and more sensibly.
3. **Be specific, not exhaustive.** Concrete facts, names, contact details and examples beat long lists of generic rules. Don't tell a capable model things it already does well ("be helpful", "use correct grammar").
4. **Say what to do, not only what to avoid.** Pair each boundary with the alternative behavior ("If asked about refunds, explain that our team handles them and share orders@…").
5. **Ground it in the user's examples.** Include 1–3 short example exchanges built from the Phase 2 example requests, wrapped in `<example>` tags, and say they illustrate style rather than being scripts to copy.
6. **Keep it readable.** Aim for 150–600 words. Use a few short headed sections. Simple agents need fewer.

## Skeleton

Use only the sections that apply:

```markdown
You are <Display Name>, <one-sentence role> for <who>. <One sentence on the goal and why it matters.>

## What you help with
- <task 1>
- <task 2>
- <task 3>
<What's out of scope, and what to do instead.>

## How you communicate
<Tone, reading level, reply length and why, formatting preferences, words to use/avoid.>

## What you know
<Key facts inline. If there are knowledge files: "Reference documents are in <location>. Check them before answering questions about X. If they don't cover it, say so rather than guessing.">

## Tools and actions
<Only for agents with abilities. When to use each ability, and which actions need the user's confirmation first.>

## Boundaries
<Never-do items, each paired with what to do instead. Handoff instructions.>

## Examples
<example>
User: <realistic request>
You: <ideal reply in the right tone and length>
</example>
```

## Required additions by situation

- **Public/customer-facing:** "If someone asks whether you're a person, tell them you're an AI assistant." · No promises about refunds, exceptions, pricing, legal/medical/financial matters beyond what's written in your instructions · A clear human handoff path.
- **Can edit files / run commands / send messages:** "Before deleting, overwriting, sending, publishing, or anything that's hard to undo, describe what you're about to do and wait for a yes."
- **Uses web search:** "Cite sources with links. If sources disagree or are outdated, say so."
- **Uses knowledge documents:** "Base answers on the documents. If they don't cover the question, say so instead of guessing."
- **Learners/children:** age-appropriate language, encourage thinking before giving answers (if the user chose that).

## Workflow agents: core instructions + playbook

For workflow-mode agents (`workflow-mode.md`), keep the 150–600 word core instructions about identity, tone, stage overview, and boundaries, and put the decision rules in `playbook.md`. Don't compress the rules to fit the word limit; that's how know-how gets lost. Add these sections to the core instructions:

```markdown
## How a job flows
You help with these stages: 1 <stage> → 2 <stage> → 3 <stage>. Work out which stage a request belongs to before answering. At the end of each stage, list what passes to the next one (see "Hand-offs" in the playbook).

## Your playbook
Your playbook (below / in `playbook.md`) holds <Name>'s rules for each stage. Follow it over your own general knowledge, because it reflects how this business actually works. When a rule is marked ❓, or a situation isn't covered, don't guess: say what you'd need to know and ask <Name>.

## Expert checks
<the expert-check list>. For these, flag the issue, explain what to check and with whom, and never state that something is compliant, legal, or safe.

## Up-to-date information
<changing-data files>. Check the "Last updated" date before using one. If it's older than <N> weeks, say so and ask before using the numbers.
```

Plus **Works in: <place>** in "What you know", and, if the agent remembers jobs, how to read and update job files (or end each stage with a Job summary block).

## Description line (for subagents and skills)

Subagents and skills also need a one-to-two-sentence **description** that tells Claude *when* to use them. Write it as: what it does + "Use when …" with concrete trigger phrases. Example:
`Turns meeting notes or transcripts into a summary, decisions, and an action-item table. Use when the user shares meeting notes, a transcript, or asks for action items or minutes.`
