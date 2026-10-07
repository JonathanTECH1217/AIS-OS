# Asset request email for a website rebuild

The one email that asks a signed client for the files and the answers a website rebuild needs. Written 2026-09-24. Sent by Jonathan on the business day after the onboarding questionnaire (`templates/onboarding-questionnaire.md`); the AIOS never sends. One job: get the files moving, because photos are the long pole of the 14 day build (`.claude/skills/kickoff/assets/access-checklist.md` row 12 blocks the landing pages). Rules from `references/voice.md`: first name then the point, under 120 words above the signature, plain paragraphs, no hedges, no em dashes, sign-off "Jonathan". The list under the signature is plain text so it survives any mail client. Never ask for a password; every login item names the person to add or the fact to send instead. Files that arrive go to `projects/clients/{slug}/assets/`.

## Email

**Subject:** What I need to rebuild {domain}

{First name},

Below is what I need to rebuild {domain}. Seven items hold up the build: job photos, the logo, your license number, and the domain, hosting, builder, and email answers. The rest can trail in over the week.

Send everything to jonathan@monarcbuild.com or share a Google Drive folder to that address. Raw files, not screenshots. Phone photos are fine.

Never send me a password. Where a login exists, the list says who to add instead.

The first seven by {date} keep the {build deadline} go-live. If something is not yours to send, tell me who has it and I will chase it.

Jonathan

## The list (paste under the signature)

```
ASSET LIST: {company}

HOLDS UP THE BUILD

1. Job photos. Twenty or more from your best three to five jobs, the ones you named on the questionnaire. Before and after where you have it. One wide shot of the finished work, then close-ups of the detail: the flashing, the panel, the equipment pad, the fixture. Straight off the phone or camera at full size. Not screenshots, not pulled from Facebook. Put each job in its own folder named for the town.

2. Logo. The vector file (SVG, AI, EPS, or the PDF your designer sent) plus a PNG on a transparent background. If all you have is a JPG, send it and tell me who designed it.

3. License number(s) and the state or board that issued each, exactly as they should print. A photo of the license card if you have one handy.
   {what I see: license line on the current site, if any}

4. Domain. Where {domain} is registered (GoDaddy, Squarespace Domains, Namecheap, Network Solutions, Cloudflare, other) and the name of the person who has that login. If DNS lives somewhere else, name that too. Add jonathan@monarcbuild.com as a delegate or team member there if the registrar allows it (GoDaddy: Account Settings, Delegate Access. Cloudflare: Manage Account, Members). No password.
   {what I see: registrar and nameservers from the prep}

5. Hosting and builder. Where the site is hosted, what it was built on (WordPress, Wix, Squarespace, GoDaddy Website Builder, Duda, other), and the name and email of whoever built it. WordPress: an Administrator user for jonathan@monarcbuild.com. Wix or Squarespace: a contributor invite to that address. Anything else: the builder's contact and I take it from there.
   {what I see: platform fingerprint from the prep}

6. Email on the domain. Does anyone use an address like name@{domain}? Who hosts it: Google Workspace, Microsoft 365, GoDaddy email, the web host. This is so your email keeps working the day the site moves.
   {what I see: mail host from the prep}

7. Google Business Profile. Add jonathan@monarcbuild.com as a Manager: business.google.com, Settings, People and access. Skip if we did it on the kickoff call.

SEND THIS WEEK

8. Video. Any walkthrough or finished-job clip, phone quality is fine, horizontal if you have the choice. The raw file, not a link to a post.

9. Certificate of insurance. General liability and workers comp, the current COI PDF your agent sends builders. "Licensed and insured" goes on the site only with this on file.

10. Certifications and badges. Dealer or manufacturer certificates, the logo files the program gave you, a photo of any plaque.

11. Team photos. Owner headshot, the crew together, the trucks with the logo on them, the shop or showroom. Phone is fine, outdoors in daylight.

12. Existing content that must carry over. Pages, wording, warranty terms, financing language, PDFs, or an export from the builder. If nothing, say so and I pull what is worth keeping from the live site.

13. Brand bits. Company colors and fonts if you know them, the truck wrap file, business card or yard sign art, the tagline you use.

14. Warranty and financing paperwork. Your workmanship warranty as a PDF and the financing partner's application link, if you have them.
```

## What blocks the build

- Items 1, 2, 4, 5, 6: the landing pages and the takeover cannot start without them (`access-checklist.md`: rows 6 and 7 must be `granted` or `create`; row 12 blocks the pages).
- Item 3: a website is an advertisement, and many state contractor boards require the license number on every ad. Treated as blocking so the site never goes live without it. The rule is per state; confirm for each client's state.
- Item 7: blocks local SEO, not the pages. Usually done live on the kickoff call (Q18).
- Items 8 to 14 trail. Video is not blocking: the hero ships with stills and the "Video coming" slot from `templates/vsl-draft.md`. The COI is not blocking, but "licensed and insured" does not print until it is in `assets/`.

Reviews, warranty terms, and financing partner names are facts, not files, so they live in questionnaire items 11 and 13; this email asks only for the paperwork (item 14). The GBP grant stays on the list because the access clause in `context/offer.md` runs five business days from signing and the call may fall later than that.

## Return path

Files land in `projects/clients/{slug}/assets/{town-or-job}/`. The AIOS writes what arrived and the date into `access.md` row 12 (photos, logo, brand), rows 6 and 7 (domain, hosting), row 1 (GBP), and row 10 (email). The license number and the COI expiry go on the brief's "Credentials on the page" line; the COI PDF stays in `assets/` (it is the client's paper, not Monarc's `records/`). The wrap recap's "Still need from you" lists only items not yet in `assets/`.

## Blanks

- {First name}: the owner or the contact from the sales call.
- {domain}: bare, no scheme (example.com).
- {company}: the client's name as it should print.
- {slug}: the client folder name, `lowercase-hyphens`.
- {date}: five business days from signing, matching the access clause in `context/offer.md`.
- {build deadline}: from `projects/clients/{slug}/brief.md`, kickoff plus 14 days.
- {town-or-job}: one subfolder per job, named for the town.
- {what I see: license line on the current site, if any}: from the prep site read. Delete the line when nothing was found.
- {what I see: registrar and nameservers from the prep}: `Resolve-DnsName {domain} -Type NS`, plus the registrar from a WHOIS lookup. Delete when nothing was found.
- {what I see: platform fingerprint from the prep}: the platform from the prep fingerprint (kickoff prep step 2). Delete when nothing was found.
- {what I see: mail host from the prep}: `Resolve-DnsName {domain} -Type MX`. google.com means Workspace, outlook.com means Microsoft 365, secureserver.net means GoDaddy. Delete when nothing was found.
