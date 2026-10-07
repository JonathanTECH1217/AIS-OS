# Gold Standard Integration (GSI, Jupiter, FL): the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `python scripts/prospect_page.py all gsi-florida` from `spec.json` (one photo in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/gsi-florida" --port 8800`, then http://127.0.0.1:8800/
- Renders: `projects/Landing Page Build/renders/2026-10-06/gsi-florida-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://www.gsi-fl.com/ (a Wix site; the services sit on one home page, no lighting page of its own).
- The Loom: https://www.loom.com/share/65e163700465418b8f6705154b8fe34d (7 minutes; silent from 1:58 to 3:51). Its file and word-timed transcript are in `media/looms/65e16370-increase-low-voltage-revenue-with-google/` (not in git).
- Site reads: `projects/research/gsi-florida/`, `gsi-florida-about/`, `gsi-florida-book/`, `gsi-florida-lighting/` (free, 2026-10-06).

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:38 | "Making segmented landing pages. So each service that you offer, lighting control, AV, security, networking, has an individual landing page." | One service: lighting control. Nothing else above the fold. |
| 0:49 | "Build out one landing page here, pretending that this right here is for lighting control. High ticket item in this industry." | This page is the lighting control page. |
| 1:04 | "Your header up at the top, about seventy pixels, put black text on that." | A white 80 px top bar, black words: the company name in type (they have no logo), the phone, the button. |
| 1:11 | "Below that in the hero section, high contrast dark background with white text." | Their own drone shot of a lit plaza at night, darkened, white words. Centered. |
| 1:21 | "See what your primary color is. Is this kind of blue? We'll just work with this blue for now. And we'll make that the book a meeting button." | Their blue, `#008AFC` (sampled from the services band on their home page), on every "Book a meeting" button, the card grounds, and the icons. |
| 1:28 | "The headline for this page would be lighting control installation in the area you're trying to target. Put an eyebrow section above that directly targeting the specific segment of person." | h1: "Lighting Control Installation in Palm Beach County". Eyebrow: "For Palm Beach County homeowners". The place is from their own title (Jupiter, FL) and description (Palm Beach County). |
| 1:44 | "A couple lines of copy right below that headline that just speaks to the service." | One sentence: keypads with scenes, phone and voice, light that warms and cools with the day. |
| 3:58 | "The services offered with lighting control... keypads that have customized lighting scenes... being able to design those keypads... access this through your phone, using your voice... controlled color temperature to really match your circadian rhythm." | Three cards with icons: Keypads with your scenes, Your phone and your voice, Light that follows your day. "Color temperature" is said as warm white and cool white. |
| 4:24 | "An about section, so a picture of you or your team, and then a brief description about what the company stands for." | About, with a marked empty box for the owner or team photo (no real one on the site). The words are theirs, shortened: family business, the best electrical contractor service in Palm Beach County. |
| 4:43 | "A Google Review section right below that call to action." | The reviews band sits above the secondary services and the last button. No rating line in the hero: their site states none. |
| 4:50 | "Four stage booking form. First name, email, phone number and a brief message... this disqualifies anybody that doesn't have serious intent." | The button opens a four-step form, one question a screen, in that order. The hint asks for the rooms, new build or an existing home. |
| 5:18 | "Our process. Talking about the design consultation towards the installation, this does a lot with B2B partners, so your architects, builders and designers." | A black band, eyebrow "For architects, builders, and designers", four numbered stages: design consultation, lighting plan, wiring, installation and programming. No button in it. |
| 5:42 | "Here's the impressive portfolio. I like this. Actual photos of the team members and talk about a little bit of your inspiration behind the work." | The "portfolio" on their site is four Wix placeholder client logos. The about band is where the team photo and the inspiration go; the photo box is marked empty. |
| 5:55 | "Portfolio as far as the work would be another good section. And then reviews alone would be a good section. Three a card there." | Our work: three marked empty boxes. What our clients say: three marked empty boxes (see the misses). |
| 6:07 | "Another services page would be great. Hyperlinks to other service landing pages, your other high ticket items like your whole home audio, media distribution, networking." | Four cards that link to the services their site does list: EV charging stations, panel upgrades, generator inspection, electrical wiring. Whole home audio, media distribution, and networking are not on their site, so they are not on the page. |
| 6:29 | "And then a secondary call to action." | The closing band: "Start with a design consultation", then the button. Not "free": their site sells the design consultation. |

## Where every fact came from

- Company name, "Electrical Contractor", Jupiter, FL, Palm Beach County, "Family Business", the service list, the phone (561-419-9449): their public site, read 2026-10-06. No street address is on it; the footer says Jupiter, FL.
- The blue: sampled from the live home page's services band (`#008AFC`); the darker `#0070CF` is the hover; `#5CB6FF` is the lighter accent on the process stages.
- The hero photo: their own DJI drone shot (file dated 2026-09-15, 4000 x 2250), the only real photo on the site, saved at 1600 px wide.
- Not used, on purpose: the header picture (an AI drawing of a plan room, 1024 x 1024; there is no logo, so the name is set in type), the ocean living room, the EV charger, the Siemens panel, the stage lights, the server room, and the generator (all 1024 x 1024 AI renders or Wix stock).
- Fonts: their nav is Playfair Display, sharper than his light serif rule, so headings keep Newsreader; Madefor and Helvetica are not Google fonts, so Manrope and Poppins.
- The card and process lines: his words in the Loom, in plain English. No brand of gear is named: their site names none for lighting.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **Nothing real to show.** One real photo on the whole site (a plaza at night), no team photo, no logo, and AI pictures for every service. The work boxes and the team box are empty until they send five photos of lit rooms and one of the team.
2. **The reviews are template text.** The four on their site are Wix's sample IT reviews with their name typed in ("chose gsIntegration.org for our IT needs", "cloud solutions"). None is about lighting, so none is on the page. Three real Google reviews from lighting clients would fill the boxes; their site states no rating either.
3. **The price is the wrong page.** Their site lists an "Initial Design Consultation" at $15,000 and a $212 server call next to a lighting install. A buyer looking for lighting control sees a price before a reason. The render takes every price off; the consultation should be the first call, not a line item.

## Not done

- The services he named (whole home audio, media distribution, networking) wait on the company saying they offer them.
- The Loom B and A cut and the email to the owner.
