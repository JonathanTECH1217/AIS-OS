# Site read

Workflow of the research skill. Status: works; run 2026-10-05 on two companies' pages.

One line: Reads one public page of a company and saves what it says and shows.

## Objective

Before a page, an email, or a short is made about a company, the clone knows what the company's own page says, how it looks, and which of its pictures are real.

## What sets it off

A company's page address. Usually the page being reviewed, not the homepage.

## Procedure

1. `python scripts/research.py site <url> --name <slug>`. It writes `projects/research/<slug>/site.json` and `site.html`.
2. Read the summary line: the title, the word count, the headings, how many pictures and how many of them are AI-named or logos, the faces, the phone.
3. Open `site.json` for the rest: the headings in order, the top colors, the social links (the Instagram and Facebook addresses matter for the other workflows), each picture with its note.
4. For the brand color, read it off the logo, not off the page's style sheet: a site builder's sheet is full of colors the brand never uses.
5. For a second page of the same company (About, Gallery), run it again with the same `--name`; keep the first file by renaming it if both are needed.

## What it cannot tell

- Whether an unmarked picture is the company's own work. A maker's marketing photo often carries no sign in its name. Look at the pictures before using one as proof.
- Anything behind a login or loaded only after a click.

## Criteria for passing

- [ ] `site.json` exists with the day it was read.
- [ ] The clone has looked at the pictures it means to use, not only their names.
- [ ] No fact about the company is used that is not on the page or in another saved read.
