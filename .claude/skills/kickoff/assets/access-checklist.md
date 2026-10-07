# Access checklist

Run top to bottom during block 4 of the kickoff, on the client's shared screen. Record the ID and the status in `projects/clients/{slug}/access.md`. Statuses: `requested`, `granted`, `verified` (Jonathan opened it), `n/a`, `create` (Monarc creates it). Never record a password, token, or recovery code. Shared logins that cannot be avoided go to Jonathan's password manager; the table says "in password manager" and the date.

Grant target for every Google product: `jonathan@monarcbuild.com`.

| # | Tool | Required for | What to ask the client | How the client grants it | Record |
|---|---|---|---|---|---|
| 1 | Google Business Profile | Local SEO, maps, reviews, GBP posts | "Open business.google.com, Settings, People and access." | Add Jonathan as Manager (Owner only if the client wants Monarc to own it; default Manager). | Listing name, location ID, status |
| 2 | Google Ads | Managed ads, conversion tracking, weekly spend | "Read me the 10-digit customer ID, top right." | Monarc sends a link request from its manager account; client accepts in Tools, Access and security, Managers. Billing stays on the client's card. | Customer ID (xxx-xxx-xxxx), manager link status, billing owner |
| 3 | Google Analytics 4 | Event tracking, funnel report, attribution | "Do you have a GA4 property? Admin, Property access management." | Add Jonathan as Editor. If none, Monarc creates the property under its own account and grants the client Viewer. | Property ID, measurement ID (G-...), status |
| 4 | Search Console | Technical SEO audit, query data | "search.google.com/search-console, Settings, Users and permissions." | Verified owner adds Jonathan as Full user. If unverified, Monarc verifies through DNS or the GA4 tag once it has access. | Property URL, status |
| 5 | Google Tag Manager | GA4 tag, Ads conversion tag, form and call events | "tagmanager.google.com, Admin, User management." | Add Jonathan with Publish on the container. If none, Monarc creates the container and installs it. | Container ID (GTM-...), status |
| 6 | Domain registrar and DNS | Site takeover, Search Console verification, email records | "Where is the domain registered, and who has the login?" | Preferred: registrar delegate access (GoDaddy Delegate, Cloudflare member, Namecheap sub-user). Else shared login to the password manager. | Registrar, DNS host, expiry date, status |
| 7 | Hosting or site source | Takeover onto Monarc hosting, landing pages | "Who built the site? Do you have the files or an export?" | HTML export or repo access, or the builder's contact. WordPress: an admin user for Jonathan. Wix, Squarespace, GoDaddy: contributor invite, then plan the rebuild. | Platform, builder contact, what was received, status |
| 8 | Booking calendar | First Responder books appointments | "Share the calendar with jonathan@monarcbuild.com, make changes to events." | Google Calendar share, Outlook delegate, or a shared appointment schedule. | Calendar owner, calendar type, status |
| 9 | Phone provider | Call tracking, after-hours routing | "Who is your phone on, and who administers it?" | No access yet; record for the call tracking build. If a tracking number was approved, note the forwarding target. | Provider, admin, tracking number approved yes/no |
| 10 | Email for leads | Form notifications, weekly report | "Which address should form leads and the weekly report go to?" | None. Monarc points the form and the report there. | Lead inbox, report recipients |
| 11 | Social and directories | Optional: GBP-adjacent citations, proof posts | "Facebook, Instagram, Houzz, LinkedIn page admin?" | Page role invite to Jonathan's account. | Handles, status |
| 12 | Photos, logo, brand | Landing pages, GBP, ads | "Send the three project photo sets and your logo file today." | Email or Drive share to jonathan@monarcbuild.com. Files land in `projects/clients/{slug}/assets/`. | What arrived, date |

## Before the build starts

Rows 1, 2, 6, 7, 8 must be `granted` or `create`. Rows 3, 4, 5 can be `create`. Row 12 blocks the landing pages, not the ads.

## Verify within 24 hours

Jonathan opens each granted tool once and the AIOS flips the status to `verified` in `access.md`. Anything still `requested` after 48 hours becomes a `tasks.md` line with the client contact as owner.
