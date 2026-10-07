# The builder search check: `/builder-check/`

The page the Meta ad lands on and the four-tile check that ends on the booking calendar. Spec written 2026-10-03 from the interview (`brainstorms/2026-10-03-meta-ads-builder-search-check.md`, Q4 to Q8, Q26, Q27). Built through `/landing-page` after Jonathan approves the style tile; the Style Guide and the Section Spec are read first, as always.

## The page

- Address `https://monarcbuild.com/builder-check/`. `noindex`. `mb-page-type` ad. `mb-theme` monarc (the `/av_marketing/` look of 2026-09-30: white, Roboto, the butterfly's four hues, butterfly blue buttons). Page label in the popup's post: `builder-check` (a hyphen, so the booking script reports the real path).
- Eyebrow "Marketing for AV integrators" (Copy 11: the eyebrow names the person).
- Blocks, in order, under 400 visible words outside the popup (6.16): brand mark; the hero (h1 "Can a builder in your county find you tonight?", sub "Thirty seconds. Four taps. Then the search, pulled before the call.", the hero button); the audit block ("On the call", "Fifteen minutes. You leave with the audit."); proof (the first-page line and the three cards, no figures, Copy 4); fit ("For" and "Not for", the `/av_marketing/` lists); FAQ (three: cost on the call; what happens on the call; what if it does not work); the final ask; footer with the privacy link; the floating pill. No brands ticker, no services block, no math block: this page has one job.
- Three button instances, the only exception to one label (6.2): the hero, the final ask, the pill. Label on this page: **"Start the check"** (the theme's hero label slot) and **"Start the check"** on the final ask; a saved theme override in `themes/monarc.json` if the build needs one, with Jonathan's word. Each opens the popup at tile 1.
- The head carries what every ad page carries: both gtag configs, the `?sent=1` guard with `book_appointment` and the conversion label, the hidden UTM, `gclid`, and `fbclid` fields, `_next` to its own `?sent=1`, `journey.js`, the LinkedIn Insight Tag, and the Meta Pixel (below).

## The popup: four tiles, the result, then the five steps

The popup of Style Guide 6.11 with the stepper of 6.10, extended in front. Tiles are the option tiles of 6.4 (form controls, the only bordered boxes, checked state in the theme), keys A to D, and a tile answer moves on by itself (the technicians step already works this way). Back arrows from tile 2 on (the 2026-10-01 amendment).

| Step | Question | Tiles |
|---|---|---|
| 1 | Which of these do you install? | A Lutron or Ketra · B Control4 · C Crestron or Savant · D None of these |
| 2 | How many technicians? | A 1 to 2 · B 3 to 5 · C 6 to 10 · D More than 10 |
| 3 | Where did your last five jobs come from? | A Referrals · B Builders we know · C They found us online · D Mixed |
| 4 | Are you running ads in your own account today? | A Yes · B We did once · C Never |
| R | The result (below) | one button: "See the times" |
| 5 | First name | the 6.10 step |
| 6 | Email | the 6.10 step |
| 7 | Phone | the 6.10 step |
| 8 | Technicians | the 6.10 step, pre-filled from tile 2 and skipped when filled |
| 9 | The calendar | the 6.10 step, "Confirm appointment" |

Nothing personal is asked before the result. The hidden fields `installs`, `last_five`, `ads_today` carry the tile answers (the tile's words, not the letter) into the booking post and the formsubmit email, beside `technicians`.

## The result lines

One line, true from the answers alone, chosen by tile 3 and tile 4. Then the constant second line. No score, no number we made up, no promise.

| Last five | Ads today | The line |
|---|---|---|
| Referrals | Never | Your last five came from referrals and you've never run ads. A builder searching your county tonight finds the integrators who do. |
| Referrals | We did once | Your last five came from referrals. You ran ads once. The builder searching tonight finds whoever is running them now. |
| Referrals | Yes | Your last five came from referrals while your ads ran. Either the ads reach homeowners only, or the page loses the builder. The call reads which. |
| Builders we know | Never | Your last five came from builders you know. The builders you don't know search. You've never been where they look. |
| Builders we know | We did once | Your last five came from builders you know. You ran ads once. The builders you don't know are still searching. |
| Builders we know | Yes | Your last five came from builders you know, with ads running. The call reads whether a builder who searches your county sees you. |
| They found us online | Never | Your last five found you online with no ads behind it. That is the strongest sign in this check. Ads put a floor under it. |
| They found us online | We did once | Your last five found you online. You ran ads once and stopped. The search is still there. |
| They found us online | Yes | Your last five found you online and your ads run. The call reads what the ads buy and what a builder's search returns. |
| Mixed | Never | Your last five came from a mix, none of it ads. A builder searching your county tonight finds the integrators who run them. |
| Mixed | We did once | Your last five came from a mix. You ran ads once. The call reads what they bought. |
| Mixed | Yes | Your last five came from a mix, with ads running. The call reads whether a builder who searches finds you or the next shop. |

Second line, always: **"Fifteen minutes. Before the call we pull your county's search results and show you who he finds."**

Tile 1 "None of these" adds a third line: "We work with shops that install Lutron, Control4, Crestron, or Savant. Book if you like; the call may say it's not a fit." The booking still goes through; the lead is flagged (below).

## Fit flag on the lead

- Not a fit: tile 1 "None of these", or tile 2 "1 to 2".
- The booking script writes the four answers to the Leads row (fields **Installs**, **Last five**, **Ads today**, beside **Technicians**, created 2026-10-03) and a Notes line: `Check: installs {a}; last five {b}; ads today {c}. Fit: ok` or `Fit: not a fit`.
- The CRM's lead page shows them; Jonathan reads the row before the call and can disqualify.

## The Meta Pixel on this page

Base code on every page of the site (the mirror; pushed on Jonathan's go), `PIXEL_ID` from Events Manager:

```html
<!-- Meta Pixel -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'PIXEL_ID');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=PIXEL_ID&ev=PageView&noscript=1"/></noscript>
```

Events on this page only:

| When | Call |
|---|---|
| Tile 1 answered | `fbq('trackCustom', 'CheckStarted')` |
| Tile 4 answered, the result shows | `fbq('track', 'Lead')` (the ad set's conversion event) |
| The booked state, `?sent=1&booked=1` | `fbq('track', 'Schedule')` (inside the existing `sent` guard, beside `book_appointment`) |

`scripts/page_shot.py` already blocks `connect.facebook.net`, so the CRM's page copies never fire it. The privacy page names the Pixel (two lines added to the mirror 2026-10-03, pending approval with the journey lines).

## The sent state

Under the hero, as on every ad page: "is booked" with the invite line, "is requested" when the booking failed, "We email you two times" when no time was picked. No name anywhere (6.10, amended 2026-10-01).

## Style Guide 6.12, the text to add at the build

> 12. **The check popup (Jonathan, 2026-10-03, `/builder-check/` only).** The popup of rule 11 opens on four option tiles before the five steps of rule 10: which of these do you install (Lutron or Ketra, Control4, Crestron or Savant, None of these); how many technicians (the rule 10 tiles); where did your last five jobs come from (Referrals, Builders we know, They found us online, Mixed); are you running ads in your own account today (Yes, We did once, Never). Keys A to D; a tile answer moves on by itself; back arrows from the second tile. After the fourth tile a result step shows one line chosen by the third and fourth answers (`projects/meta-ads/check.md`), the constant line "Fifteen minutes. Before the call we pull your county's search results and show you who he finds.", and one button, "See the times", which continues to first name, email, phone, the calendar (technicians is pre-filled from the second tile). The four answers post with the booking as `installs`, `technicians`, `last_five`, `ads_today`. Nothing personal is asked before the result. The word "quiz" never appears. The page's three button instances carry the label "Start the check".

## Section Spec entry, the text to add at the build

> ## Ad page /builder-check/ (added 2026-10-03, the Meta ads plan)
>
> The Meta ads destination (`projects/meta-ads/README.md`). The `/av_marketing/` look (the `monarc` theme, the eyebrow "Marketing for AV integrators"), `noindex`, page label `builder-check`. Blocks: brand mark; hero (h1 "Can a builder in your county find you tonight?", sub "Thirty seconds. Four taps. Then the search, pulled before the call.", button "Start the check"); the audit block; proof (no figures); fit; FAQ (three); final ask ("Start the check"); footer with the privacy link; the floating pill. Under 400 words outside the popup. The popup is Style Guide 6.12: four tiles, the result, then the five steps. The head carries both gtag configs, the `?sent=1` guard, the Insight Tag, `journey.js`, and the Meta Pixel with `CheckStarted`, `Lead`, and `Schedule`. Ad link: `?utm_source=facebook&utm_medium=paid-social&utm_campaign={{campaign.id}}&utm_content={{ad.id}}`.

## Verification at the build

- The popup opens at tile 1 from all three buttons; keys A to D answer; the result line matches the table for every one of the 12 pairs (a render per pair with `?step=R&t3=A&t4=B` or the build's equivalent).
- A test booking from a non-self address with the Meta labels: the Leads row carries Source meta-ads, the campaign by Platform id, Installs, Last five, Ads today, Technicians, and the Fit note; a deal at Booked; the confirmation, the day-before, and the one-hour reminder from Monarc Build.
- Events Manager, Test Events: PageView on load, CheckStarted at tile 1, Lead at the result, Schedule on the booked state. Nothing fires in `page_shot.py` copies.
- `drift.py --type ad` and `readability.py` pass; the word count is under 400 outside the popup; exactly three "Start the check" instances.
