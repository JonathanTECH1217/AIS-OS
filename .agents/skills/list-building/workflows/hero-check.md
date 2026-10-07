# Hero check

Workflow of the list-building skill. Status: built 2026-10-05; fixtures and the first 40 rows read right; the full run waits for his go on the Lutron question and the quote.

One line: Finds the residential integrators whose first screen misses the ask, the centering, or the buyer's words.

Jonathan, 2026-10-05: "filter my seed list, make it a skill, and we want to be monitoring for a call to action in a booking form in the hero section, centered text, a headline that matches buyer intent. And if it doesn't have that, that's our leads." And: "a repeatable skill for filtering a niche which takes into account the lack of signals that it is a Lutron installer and not a commercial-targeting company."

## Objective

Every residential integrator on the list has a yes or no for the three hero rules and a picture of its first screen. The ones that miss are the call list, each with the reason in one line and the picture his Loom review opens on.

## What sets it off

A qualified list CSV in `projects/outreach/` (the integrators' is `qualified-list-2026-09-11.csv`, 887 companies), or his words: "filter the seed list", "hero check", "which ones have no booking form", "run it on the roofers".

## The three rules

Each is one of his page rules (`projects/Landing Page Build/Taste Log.md`, Style Guide Copy 11):

1. **The ask opens a form from the first screen.** A button in the hero that opens a modal form, a booking widget (Calendly, HubSpot meetings, Google Calendar appointments, Housecall Pro and the like), or an inline form. A button that goes to a contact page, a phone link, or nothing is a miss.
2. **The headline is centered.** The words sit at the middle of the width. A centered headline in a half column is a miss.
3. **The headline is in the buyer's words.** It names the service, the place, and speaks to the homeowner. A company name alone is a miss. "Your neighborhood specialist" is a miss.

The niche gate comes first: a company whose site reads commercial-led, not an integrator, or on One Firefly is dropped before any browser or model runs. Lutron is a column and a sort key by default; `--require-lutron` makes it a gate.

## Procedure

1. **Quote.** `python scripts/hero_check.py --dry-run`: rows in, dropped before the browser, renders due, gap-fill reads due, Lutron named, the model estimate. Say the number. He says go. (2026-10-05: 887 rows, 366 dropped, 521 to render, about $6.40.)
2. **Fixtures**, free of the list: `--urls <five pages> --no-batch --date <date>-fixtures`. Include one page that passes everything (monarcbuild.com/av_marketing), one with no button, one with a contact-page button, one with a modal form. Open the five shots in `projects/crm/shots/hero/` and compare by eye. A wrong read is a fix to the script, not a note on the row.
3. **The first 40 rows, sync**: `--limit 40 --no-batch`. Open `projects/outreach/hero-check-<date>.xlsx` and the shots. 23 of 25 rendered rows right before going on.
4. **The full run, batch**: `python scripts/hero_check.py` (add `--require-lutron` if he chose the gate). About 15 minutes in the browser at five pages at a time, then the batch comes back inside an hour. `--no-wait` submits and exits; the same command later collects.
5. **His 20-row check.** Twenty leads at random with their shots. 18 or more right.
6. **The write.** `python scripts/hero_check.py --build-only --write-list`: `qualified-list-<date>.csv`, leads only, which the CRM's integrator glob picks up on its next start (`pythonw scripts/crm_boot.pyw --no-open`). `--all-rows` writes every row instead. The old list stays in place as the record. Ask before this step: replace the integrator call list, or add a vertical row in `projects/crm/config.json` so both dial.
7. **The method sheet** in the xlsx says: rows in = leads + not a lead + held; dropped by reason; held by reason; leads by which rule fails; Lutron and residential counts; the spend.

## What the script never does

- Types into or submits any form. One click at most per site, on the first-screen button, to see what opens.
- Counts a visit: tracking hosts are blocked in the browser.
- Spends past `--max-cost` (default $20) or runs the model on a row dropped by the niche gate.
- Writes the CSV the CRM dials from without `--write-list`.

## Held rows

Never leads. A row is held when the site answered 403 or 500 to a headless browser, the first screen was blank, no headline words were found even in the picture, or its residential read is still unknown. He can open the shot (when there is one) and decide by hand.

## Criteria for passing

- [ ] The five fixtures read right by eye.
- [ ] 23 of 25 rendered rows right in the first sync pass.
- [ ] 18 of 20 random leads right in his check.
- [ ] The method sheet adds up and the spend is at or under the quote.
- [ ] Every lead has a shot and a one-line reason that names which rule fails.
- [ ] No form was submitted anywhere.

## Never without a go

- The model spend (the quote first).
- Writing the CSV the CRM dials from.
- Running it on another vertical's list.
- Any Loom on a lead: that is his recording, with the brief from `/research review-brief`.

## Outputs

- `projects/outreach/hero-check-<date>.xlsx`: Leads, Not a lead, Held, All, Method.
- `projects/outreach/qualified-list-<date>.csv` (with `--write-list`): the call list's columns plus Hero CTA, Hero form, Centered, Intent headline, Lutron, Residential, Verdict, Reason, Checked, Headline, Button label, Shot.
- `projects/crm/shots/hero/<domain>-1440.jpg`: the first screen, served by the CRM at `/shots/hero/`.
- `projects/outreach/hero-cache-<date>.jsonl`: every read, so a crash resumes. Gitignored.

## Known misses, to tune on the next pass

- A site that blocks headless browsers (403) is held; its static text still fills Lutron and residential.
- A slider's first slide is the hero; the script measures twice and notes "slider" when the words changed.
- A headline baked into a picture is read from the picture; its Reason says so and Centered says "(visual)".
