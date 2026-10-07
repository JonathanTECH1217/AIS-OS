---
name: relevance
description: A standing rule, not a role. Applied before the clone reads any .md file for a task (context, references, brainstorms, templates, skills, workflows, decisions, audits). Picks what to read, reads only the parts that answer the task, and stops at 35% of the remaining context window. Jonathan, 2026-10-05: "Relevance should be a skill used whenever prompting so I don't load too much context from .md files into the responses. It should only fill around 35% max of the remaining window at a time."
---

# Relevance

The clone reads before it writes. Left alone it reads whole files to find one fact, and the window fills with words that do no work. This rule sets the budget.

## The budget

- At most **35% of what is left of the window** goes to `.md` reads in one turn. One token is about four characters. When the fill is not known, assume half the window is left.
- CLAUDE.md, AGENTS.md, and the memory index are loaded by the harness before the turn starts. They are not in the budget, and they are already in the window, so nothing from them is read again.
- A file he pastes, attaches, or points at with "read this" is read as asked. It still counts toward the 35%.

## Pick before reading

1. Name the question the task needs answered. One line.
2. Find candidates with Grep on the task's own words (company name, skill name, rule, date). Rank them by how directly they answer the question.
3. Read sections, not files: `Read` with `offset` and `limit`, or Grep with `-C 5`. A whole file is read only when it is short or the task is the file itself.
4. Keep a running count of characters read. Stop at the budget. Say what was not read in one line ("not read: X, Y") so he can ask for it.

## Order of worth when the budget is tight

1. The file the task names outright.
2. The skill or workflow being run (`.claude/skills/<skill>/SKILL.md`, its `workflows/<name>.md`).
3. The `context/` page the task touches (offer, priorities, a trade).
4. The `references/` file that holds a rule the output must follow (voice, mycopy, a style guide, an API guide).
5. `brainstorms/` only for the exact day or topic named.
6. `audits/`, `archives/`, `decisions/log.md` only when asked.

## What this is not

- Not a reason to skip a rule file the output must obey. A voice or style rule is read, in its relevant section.
- Not a cap on code reads. A script the task edits is read as the Edit tool needs.
- Not a cap on what he reads back; it is a cap on what the clone pulls in on its own.

## Trade-off he should know

The largest `.md` cost of every session is CLAUDE.md itself, loaded every time. This rule cannot shrink it. Slimming CLAUDE.md into pointers (the detail already lives in the skills and `references/`) is his decision, not the clone's.
