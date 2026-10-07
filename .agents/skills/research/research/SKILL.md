---
name: research
description: Use when Jonathan says "research", "look up this company", "read their site", "pull their reviews", "pull their Google profile", "pull their photos", "Instagram feed", "Instagram pull", "their Instagram numbers", or before the clone builds a page, an email, or a short about a company it has not read yet. The researcher's role as one skill: it reads what a company shows in public and what a connected account hands over, and saves it once so nothing is read twice. Its workflows live under it (site read, Google profile pull, Instagram feed pull). It reads; it never posts, sends, or logs in as anyone.
argument-hint: "<site-read | google-profile-pull | instagram-feed-pull> <url | company name and address | account slug>"
---

# Research

One skill for the role a researcher fills. Jonathan, 2026-10-05: "Do we have the research skill and then a sub-skill in that would be the Instagram profile pull for photos, titles and captions?" and then "let's work on the instagram feed pull. This should give access to analytics as well."

It exists because the same reads were done by hand twice in one day (Momentum, then an Annapolis integrator): the page, the Google profile, the photos. Each read now lands in `projects/research/<slug>/` and the next skill picks it up there.

## Its workflows

Each is one file in `workflows/`. Read the one you are running before you start.

| Workflow | What it reads | Needs | File |
|---|---|---|---|
| Site read | One public page: headings, copy, colors, faces, phone, social links, every picture with a note when it is AI-made or a logo | Nothing. Free | `workflows/site-read.md` |
| Google profile pull | The Google Business Profile: rating, review count, five reviews at most, ten photos at most | `GOOGLE_MAPS_API_KEY`. About 4 cents, 12 with photos | `workflows/google-profile-pull.md` |
| Instagram feed pull | Monarc's own posts and numbers; another business account's public profile and posts by its handle, never its numbers (Jonathan: "I only pull analytics for my personal and I pull meta data on theirs") | Monarc's own sign-in, once. Nothing from the other company | `workflows/instagram-feed-pull.md` |

## Who uses what it finds

- `/landing-page`, before it builds a page for a company: the faces and colors, the real photos, the reviews and rating.
- `/sdr`, for a line that names something true about the company.
- `/social-content`, for the page on screen and for what the account's own posts did.

## Rules every workflow follows

- **Read once, save once.** Look in `projects/research/<slug>/` first. A read older than 30 days, or one he asks to refresh, is read again.
- **Say where a fact came from and the day it was read.** Every saved file carries both.
- **Only what is public, or what Meta hands over through Monarc's own sign-in.** No signing in as anyone else, no getting around a login wall, no collecting by machine where the site's terms forbid it. Another company's Instagram is read through Meta's Business Discovery with Monarc's token, which is the sanctioned way; its numbers are never read.
- **Names in reviews** are cut to a first name and a last initial (his rule, 2026-10-05).
- **Flag what is not theirs.** A maker's marketing picture, a stock photo, or an AI-made image is marked, so it does not end up in a section called "Our work".
- **Cost.** Say the cost before a paid read when it is more than a few cents, and never run a batch of companies without his go (`/list-building` holds that rule for lists).
- **A company he has said never to name** stays out of anything a third party sees. Research on it is kept, and marked.

## The record

`projects/research/<slug>/`: `site.json` and `site.html`, `google.json` with `photos/` and `photos-sheet.jpg`, `instagram.json` with `instagram/`, `instagram-insights.json`. One folder a company.
