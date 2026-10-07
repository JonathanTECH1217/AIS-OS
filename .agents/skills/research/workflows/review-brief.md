# Review brief

Workflow of the research skill. Status: written 2026-10-05, not run on a real lead yet (the hero check's first full run waits for his go).

One line: One page for Jonathan to read before he records a Loom review of a lead's page: what the first screen misses, what the company shows, and the page to open.

## Objective

He opens the lead's page with the brief beside it and records without hunting: the three misses in one line each, the company's real photos and reviews to point at, and the booking link he would propose.

## What sets it off

A lead from the hero check (`projects/outreach/hero-check-<date>.xlsx`, Verdict = lead), or his words: "brief me on <company>", "I'm recording <company> next".

## Procedure

1. Find the hero check row: the newest `projects/outreach/hero-cache-*.jsonl` holds the `hero` and `intent` records by domain; the xlsx holds the verdict and reason. Read the shot `projects/crm/shots/hero/<domain>-1440.jpg`.
2. If `projects/research/<slug>/site.json` is missing, run the site read (`workflows/site-read.md`): `python scripts/research.py site <url> --name <slug>`. If the Google profile pull is wanted for reviews and photos, ask first (about 4 cents).
3. Write `projects/research/<slug>/review-brief.md`:
   - **The page**: the URL, the shot, the headline, the eyebrow, the sub line, the button label.
   - **The three misses**, one line each, only the ones that fail: no booking form from the first screen (what the button does instead); headline not centered (where it sits); headline not in the buyer's words (what it lacks: service, place, homeowner words).
   - **What passes**, so he does not call out something that is fine.
   - **What they show**: the services named, the brands, the market (residential or mixed), the phone, the social links; the real photos (never a stock or maker's picture) and the rating and review count with two or three reviews, first name and last initial.
   - **The ask he would propose**: one service for the page, a headline in the buyer's words with the place, the button label, the four-step form (`projects/Landing Page Build/Style Guide.md` Copy 11).
   - **Hold**: whether this company is one he has said never to name, or has a deal open.
4. Say where each fact came from and the day it was read (the skill's rule).

## Rules

- For him, never for the prospect. It is not sent.
- Only what is public or already on file. No new paid read without his go.
- Names in reviews cut to a first name and a last initial.
- The brief does not write his script. It lists facts; he says what he says.

## Criteria for passing

- [ ] He can record from it without opening another file.
- [ ] Every miss named is one the hero check found, with its evidence.
- [ ] Every photo named is the company's own.
- [ ] Source and day on every section.
