Electrician call list, built 2026-09-24 by Monarc Build's AIOS.

WHAT IS IN THE ZIP
- electrician-list-2026-09-24.csv: the call list. One row per company. 7,900 companies.
- places-seed-2026-09-24-electricians.xlsx: the raw sweep behind it, every Google listing found, with the search that found it.
- this file.

HOW IT WAS BUILT
- Google Places text search over 213 US locations: the largest metros plus the towns where $2M to $25M homes cluster.
- Six searches per metro (four in the smaller towns): electrician, electrical contractor, residential electrician,
  lighting installation electrician, EV charger installation, home generator installation.
- Google returns at most 60 results per search, so this is the top of each market, not every electrician in it.

HOW THE CSV WAS CUT
- Duplicate listings of one company were collapsed (same website, else same phone); the listing with the most reviews stands.
- Rows with no phone number were dropped.
- DC, Maryland, and Virginia were dropped, the same rule as the integrator call list. Ask if you want them back.
- Order: most reviews first. The very top rows are heating, plumbing, and electric conglomerates; skip those.

COLUMNS
Name, City, State, Zip, County, Phone, Local time at noon ET (their clock when it is noon in Annapolis), Rating,
Review count, Reviews shown (yes when they have any), Listings (how many Google listings collapsed into this row),
Website, Status (blank, yours to fill), Source (cold).

BY STATE, TOP TEN
- CA: 1,005
- FL: 879
- TX: 697
- NY: 456
- NC: 341
- CO: 294
- CT: 223
- IL: 218
- OH: 206
- PA: 192
