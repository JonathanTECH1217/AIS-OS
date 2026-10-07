# Instagram feed pull

Workflow of the research skill. Status: written 2026-10-05, not run; waits on a Meta app and a first connected account.

One line: Reads a connected Instagram account's posts and its numbers.

Jonathan, 2026-10-05: "I want to pull Instagram photos and put them on the our work section in the website" and "let's work on the instagram feed pull. This should give access to analytics as well."

## Objective

For an account that has connected: its newest pictures and captions on file for the "Our work" section of its page, and its numbers on file for its report.

## What sets it off

An account that has connected and whose token is in `secrets.env` (`INSTAGRAM_TOKEN` for Monarc's own, `INSTAGRAM_TOKEN_<SLUG>` for a client's). Setup, his part and the client's: `references/instagram-api.md`.

## Who it cannot read

A prospect, or any account that has not connected. Checked 2026-10-05: a public Instagram page gives no post and no picture to a visitor who is not signed in, and Instagram's terms forbid collecting it by machine. For a prospect's page use the Google profile's photos, the site's own pictures, or post links he pastes.

## Procedure

1. `python scripts/instagram_api.py check --account <slug>`: prove whose token it is before anything is saved.
2. `python scripts/instagram_api.py feed --account <slug> --limit 12 --save`: the pictures land in `projects/research/<slug>/instagram/`, the captions and links in `instagram.json`.
3. Look at the pictures. For "Our work" pick the ones that show finished work: rooms, fixtures, the house. Leave out people, memes, holiday posts, and a maker's reposted ad.
4. `python scripts/instagram_api.py insights --account <slug>`: the account's numbers and each post's. Read which numbers the account does not have; do not report a missing one as zero.
5. Once a month: `refresh`, so the token does not lapse.

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
- How a carousel's later pictures come back; the script saves the first.
