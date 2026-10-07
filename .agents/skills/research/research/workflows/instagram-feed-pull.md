# Instagram feed pull

Workflow of the research skill. Status: written 2026-10-05, not run; waits on a Meta app and a first connected account.

One line: Reads a connected Instagram account's posts and its numbers.

Jonathan, 2026-10-05: "I want to pull Instagram photos and put them on the our work section in the website" and "let's work on the instagram feed pull. This should give access to analytics as well."

## Objective

For an account that has connected: its newest pictures and captions on file for the "Our work" section of its page, and its numbers on file for its report.

## What sets it off

An account that has connected and whose token is in `secrets.env` (`INSTAGRAM_TOKEN` for Monarc's own, `INSTAGRAM_TOKEN_<SLUG>` for a client's). Setup, his part and the client's: `references/instagram-api.md`.

## Two kinds of read

Jonathan, 2026-10-05: "I only pull analytics for my personal and I pull meta data on theirs."

- **Monarc's own account:** the feed and the numbers.
- **Another company's account:** its public profile and posts, read through Monarc's token by its handle (Meta's Business Discovery). No sign-in from them. Never their numbers. A personal or private account cannot be read; a public page with no sign-in gives nothing either (checked 2026-10-05), and the clone does not get around a login.

## Procedure

For Monarc's own account:
1. `python scripts/instagram_api.py check`: prove whose token it is before anything is saved.
2. `python scripts/instagram_api.py feed --limit 12 --save`: the pictures land in `projects/research/monarc-build/instagram/`, the captions and links in `instagram.json`.
3. `python scripts/instagram_api.py insights`: the account's numbers and each post's. Read which numbers the account does not have; do not report a missing one as zero.
4. Once a month: `refresh`, so the token does not lapse.

For another company:
1. The handle, from the site read (`site.json` lists the Instagram link) or from him.
2. `python scripts/instagram_api.py discover <handle> --limit 12 --save --name <slug>`: profile and posts into `projects/research/<slug>/`.
3. Look at the pictures. For "Our work" pick the ones that show finished work: rooms, fixtures, the house. Leave out people, memes, holiday posts, and a maker's reposted ad.

## What comes back

- A post: date, kind (feed, reel), caption, link, likes, comments, and its picture. Posts have a caption and no title; a first line of the caption can stand in for a title.
- Numbers: reach, views, likes, comments, shares, saves, total interactions per post; reach, views, accounts engaged, profile views, followers for the account. Meta renames these; the script lists what was not there.

## Rules

- Read only. Nothing is posted, liked, or sent.
- A client's posts and numbers go on that client's page and in that client's report only.
- A picture goes on a live page only after the owner has seen which ones.

## Criteria for passing

- [ ] `check` names the expected account.
- [ ] `instagram.json` and the pictures are saved with the day they were read.
- [ ] The numbers file lists what was not available, apart from what was.
- [ ] The token's refresh is on the monthly list.

## Not settled, to find out on the first real run

- The exact names of the numbers Meta returns today.
- Whether the dashboard's token is the 60-day kind.
- Whether Business Discovery answers on the Instagram Login route; the fallback is the Facebook Login route (`references/instagram-api.md`).
- How a carousel's later pictures come back; the script saves the first.
