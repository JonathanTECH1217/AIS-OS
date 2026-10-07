# Google profile pull

Workflow of the research skill. Status: works; run 2026-10-05 (rating, five reviews, ten photos).

One line: Reads a company's Google Business Profile: its rating, its reviews, and its photos.

Jonathan, 2026-10-05: "Reviews from the Google My Business profile and post them to the reviews section" and "the photo of all of their vans listed on the Google My Business profile."

## Objective

The clone has the company's real rating, real reviews, and real photos on file, with the day they were read, for a page or a message.

## What sets it off

A company's name and address. The address keeps Google from answering with a namesake.

## Procedure

1. Say the cost: about 4 cents for the rating and reviews, about 12 with the photos.
2. `python scripts/research.py google "<name, street, city, state>" --name <slug>`, with `--photos` when pictures are wanted. It writes `google.json`, and with photos `photos/` and `photos-sheet.jpg`.
3. Check the name and address it printed are the right company.
4. Look at `photos-sheet.jpg` once and pick by number.
5. Pick the reviews that fit the page's service first. Leave off one that is about a different kind of customer.

## What Google hands out

- Five reviews at most, of its own choosing, whatever the count. The full list is not available this way.
- Ten photos at most.
- Names come back in full; the script cuts them to a first name and a last initial before saving.

## Rules

- A review is shown word for word. A long one is shortened by leaving whole sentences out, never by rewording.
- On a live page, Google's terms for showing its reviews apply; say so when a render is about to become a real page.
- The rating and the count are dated. Read them again before a page goes live.

## Criteria for passing

- [ ] `google.json` exists with the day it was read and the right company's name and address.
- [ ] No last name appears anywhere the reviews are shown.
- [ ] Every photo used was looked at first.
