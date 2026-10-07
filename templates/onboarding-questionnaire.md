# Client onboarding questionnaire

The questions a signed client answers before the kickoff call, in their own words, without Jonathan on the line. Written 2026-09-24. It covers the facts `/kickoff` Blocks 1 and 2 would otherwise spend the 45 minutes on: what they sell, the brands they carry, where they work, the floor, the proof jobs. It does not ask about the website; that is `templates/asset-request-email.md`. It never asks for a password. Send Part 1 plus the one Part 2 block for the client's trade and delete the other four. Trade keys match the filenames in `context/trades/` and `verticals[].key` in `projects/crm/config.json`: `integrator`, `electrician`, `hvac`, `plumbing`, `roofing`. The brand tick lists in Part 2 mirror `context/trades/{key}.md` (integrators: `context/icp-brands.md`); edit the map first, then the block.

Rules: 15 shared items plus four for the trade, about 20 minutes. Short answers. Skip what does not apply. Where the prep already knows an answer from the site or the listing, it sits on the `draft:` line with where it was seen; the client confirms or overwrites. No em dashes, no hedges in anything the client reads. Nothing goes to the client without Jonathan reading it first.

## Cover note

Goes as its own email, or pasted under the kickoff invite from `templates/kickoff-recap-email.md`. Under 80 words. Jonathan sends; the AIOS never sends.

**Subject:** {Company}: 19 questions before we meet

{First name},

Below are the questions I build your site and your ads from. Short answers, your words, skip what does not apply. Nineteen items, about twenty minutes.

Back to me by {date}, before the kickoff on {Day, date}. Reply on this email or share a Google Doc to jonathan@monarcbuild.com.

Nothing on it asks for a password. If a question looks like it does, stop and tell me.

Jonathan

## Part 1: every trade

```
ONBOARDING: {company}
Trade: {trade label}. Back to jonathan@monarcbuild.com by {date}.
Short answers, your words. Skip what does not apply. Never write a password here.

A. THE BUSINESS

1. Company name as it should print on the site. Year you started. People on the crew today.
   draft:
   answer:

2. Owner, and the one person who can say yes to a web page. Name, phone, email for each. How fast can that person turn a page around: same day, two days?
   draft:
   answer:

3. Hours. Who picks up after hours. Do you run emergency calls, and what is the promise (same day, within the hour)?
   draft:
   answer:

4. The phone number and the email that should ring when a lead comes in, and who answers them.
   draft:
   answer:

B. WHERE YOU WORK

5. Cities and neighborhoods you want work in, best first. Ten at most.
   draft:
   answer:

6. What you turn down: towns too far, job types you do not want.
   draft:
   answer:

7. Farthest you will drive for a good job, in minutes from the shop.
   draft:
   answer:

C. WHAT YOU SELL (the tick list for your trade is in Part 2)

8. Smallest job you want a call for. A dollar number.
   draft:
   answer:

9. A typical job, and the biggest in the last two years. Dollars and what it was.
   draft:
   answer:

10. Homeowners, builders, designers, property managers: what share of your work is each, and which do you want more of?
    draft:
    answer:

11. Warranty you offer on your own work (years), manufacturer warranties you can register for a homeowner, and the financing company you use if any (GreenSky, Synchrony, Service Finance, Hearth, Wisetack, other).
    draft:
    answer:

D. PROOF

12. Three finished jobs you are proud of, one per top service if you can. For each: the town, what was in it, what it cost, photos yes or no, and whether the homeowner will let us use their name.
    draft:
    1.
    2.
    3.

13. Where your reviews live and how many: Google, Yelp, Angi, Houzz, Nextdoor, BBB. Paste the links.
    draft:
    answer:

E. LAST TWO

14. If we could rank you first for one search phrase in your area, which one? Say it the way a homeowner would type it.
    draft:
    answer:

15. Anything about the business we have not touched.
    answer:
```

Deliberately not in Part 1: license number and insurance (files, so the asset email), the existing site and domain (asset email), competitors (kickoff Q10 needs Jonathan probing), a separate "top three money makers" question (T1 below ranks them; asking twice yields two answers).

## Part 2: your trade

Send one block. Every block has the same four items so the mapping table below stays stable: T1 services, T2 brands, T3 programs, T4 one trade question. T3 rule: a tick prints on the page only when the certificate (asset email item 10) is in `projects/clients/{slug}/assets/` or the manufacturer's public locator lists the client. Same rule as kickoff Q7: never print a claim the client cannot show.

### integrator

```
PART 2: AV CONTRACTOR (HOME INTEGRATOR)

T1. Services. Tick what you sell. Put 1, 2, 3 next to your biggest money makers.
   [ ] Control and automation
   [ ] Lighting control
   [ ] Lighting fixtures and design
   [ ] Motorized shades
   [ ] Distributed audio, indoor and outdoor
   [ ] Home theater and media room
   [ ] Video distribution and displays
   [ ] Networking and wifi
   [ ] Security, surveillance, and access
   [ ] Power, racks, and surge
   [ ] Energy: backup power, solar, EV
   [ ] Prewire for new construction
   [ ] Service plans and remote support
   [ ] Commercial (tell me; it does not go on this site unless we decide it does)
   [ ] Other:

T2. Brands you install. Tick, and star the one you lead with in each row.
   Control: [ ] Crestron  [ ] Control4  [ ] Savant  [ ] Josh.ai  [ ] Lutron (HomeWorks, RadioRA 3)  [ ] Elan
   Lighting: [ ] Lutron  [ ] Ketra  [ ] DMF  [ ] USAI  [ ] Colorbeam  [ ] Environmental Lights
   Shades: [ ] Lutron  [ ] Somfy  [ ] Hunter Douglas PowerView  [ ] Crestron shades  [ ] Screen Innovations (Nano)  [ ] J Geiger
   Distributed audio: [ ] Sonos  [ ] Sonance  [ ] James Loudspeaker  [ ] Origin Acoustics  [ ] Triad  [ ] Episode
   Theater audio: [ ] Bowers & Wilkins  [ ] KEF  [ ] Focal  [ ] Paradigm  [ ] Anthem  [ ] MartinLogan
   Video: [ ] Sony  [ ] Samsung  [ ] LG  [ ] Séura  [ ] SunBriteTV  [ ] Neptune TV
   Networking: [ ] Araknis  [ ] Ubiquiti  [ ] Ruckus  [ ] Access Networks  [ ] Pakedge  [ ] Luxul
   Power and racks: [ ] Panamax  [ ] Furman  [ ] WattBox  [ ] SurgeX  [ ] Torus  [ ] Middle Atlantic
   Security: [ ] Luma  [ ] Alarm.com  [ ] Qolsys  [ ] DSC  [ ] Resideo  [ ] Ubiquiti Protect
   Wire: [ ] Wirepath  [ ] Liberty AV  [ ] Belden  [ ] Cleerline  [ ] Legrand On-Q  [ ] Leviton
   Energy: [ ] Savant Power  [ ] Span  [ ] Enphase  [ ] Generac  [ ] Delos DARWIN
   Seating: [ ] Fortress  [ ] Elite HTS  [ ] CinemaTech  [ ] Salamander
   Software you run on: [ ] D-Tools  [ ] Jetbuilt  [ ] Portal  [ ] Simpro  [ ] ProjX360
   Anything not listed:

T3. Programs and certifications you hold. Tick, write the tier.
   [ ] Crestron dealer   [ ] Control4 dealer   [ ] Savant dealer   [ ] Josh.ai dealer
   [ ] Lutron HomeWorks dealer   [ ] Lutron RadioRA 3   [ ] Kaleidescape dealer   [ ] Sonos   [ ] Sony ES
   [ ] CEDIA member   [ ] HTSA member   [ ] ProSource member
   [ ] Other:
   Warranties you can register for a homeowner:

T4. Showroom: address, and can a homeowner visit by appointment?
   answer:
```

### electrician

```
PART 2: ELECTRICIAN

T1. Services. Tick what you sell. Put 1, 2, 3 next to your biggest money makers.
   [ ] Panel upgrades and service changes (200A, 400A), subpanels, smart panels
   [ ] Whole-home rewire
   [ ] Remodel and addition wiring
   [ ] New construction wiring for custom homes
   [ ] Recessed and architectural lighting, lighting design
   [ ] Landscape and outdoor lighting
   [ ] Lighting control and smart switches
   [ ] Standby generators and transfer switches
   [ ] EV chargers
   [ ] Whole-home surge protection
   [ ] Battery storage and solar interconnect
   [ ] Pool, spa, sauna, and outdoor kitchen wiring
   [ ] Electric heated floors and snow melt
   [ ] Ceiling fans, dedicated circuits, GFCI and AFCI
   [ ] Low-voltage prewire (network, AV, security, cameras)
   [ ] Troubleshooting and repair
   [ ] Aluminum wiring and knob-and-tube remediation
   [ ] Home inspection repairs
   [ ] Commercial (tell me; it does not go on this site unless we decide it does)
   [ ] Other:

T2. Brands you install. Tick, and star the one you lead with in each row.
   Panels: [ ] Square D  [ ] Eaton  [ ] Siemens  [ ] Leviton  [ ] SPAN  [ ] Schneider Pulse
   Generators: [ ] Generac  [ ] Kohler  [ ] Briggs & Stratton  [ ] Cummins  [ ] Champion
   EV chargers: [ ] Tesla  [ ] ChargePoint  [ ] Wallbox  [ ] Enel X JuiceBox  [ ] Emporia  [ ] Grizzl-E
   Lighting control: [ ] Lutron (Caseta, RadioRA 3, HomeWorks)  [ ] Leviton Decora Smart  [ ] Legrand  [ ] Brilliant  [ ] Control4  [ ] Crestron
   Fixtures: [ ] WAC  [ ] DMF  [ ] Juno  [ ] Halo  [ ] USAI  [ ] Ketra
   Landscape lighting: [ ] FX Luminaire  [ ] Kichler  [ ] Vista  [ ] VOLT  [ ] Coastal Source  [ ] Unique Lighting
   Devices and wire: [ ] Lutron  [ ] Leviton  [ ] Legrand Pass & Seymour  [ ] Hubbell  [ ] Eaton  [ ] Southwire
   Surge: [ ] Siemens FirstSurge  [ ] Eaton CHSPT2  [ ] Square D HEPD80  [ ] Leviton  [ ] Intermatic  [ ] Ditek
   Fans: [ ] Big Ass Fans  [ ] Minka-Aire  [ ] Modern Forms  [ ] Hunter
   Storage and solar: [ ] Tesla Powerwall  [ ] Enphase  [ ] SolarEdge  [ ] Generac PWRcell  [ ] FranklinWH  [ ] Sol-Ark
   Heated floors: [ ] WarmlyYours  [ ] Nuheat  [ ] SunTouch  [ ] Warmup
   Anything not listed:

T3. Programs and certifications you hold. Tick, write the tier.
   [ ] Generac PowerPro Premier   [ ] Generac PowerPro Elite   [ ] Generac Authorized Dealer
   [ ] Kohler Authorized Generator Dealer   [ ] Cummins Authorized Dealer   [ ] Briggs & Stratton Premier Dealer
   [ ] Tesla Certified Installer   [ ] ChargePoint Certified   [ ] Qmerit Certified Installer
   [ ] Lutron Certified (Caseta Pro, RadioRA 3)   [ ] Lutron HomeWorks dealer
   [ ] Enphase Installer Network (Platinum, Gold, Silver)   [ ] SPAN Certified Installer
   [ ] NECA member   [ ] IEC member   [ ] CEDIA member   [ ] ESA member
   [ ] Other:
   Warranties you can register for a homeowner:

T4. Low voltage (network, AV, security prewire): do you do it yourselves or refer it out? If you refer, to whom?
   answer:
```

### hvac

```
PART 2: HVAC

T1. Services. Tick what you sell. Put 1, 2, 3 next to your biggest money makers.
   [ ] AC replacement
   [ ] Furnace replacement
   [ ] Heat pumps, cold-climate and dual fuel
   [ ] Ductless mini splits, single and multi zone
   [ ] Geothermal
   [ ] Boilers, radiant floor heat, hydronic snow melt
   [ ] Zoning and controls
   [ ] Smart thermostats
   [ ] Duct design, replacement, sealing, insulation
   [ ] Indoor air quality: filtration, UV, humidity, ERV and HRV
   [ ] New construction design for custom homes (Manual J, D, S)
   [ ] Wine cellar cooling
   [ ] Pool and spa heat pumps
   [ ] Maintenance plans
   [ ] Repair and emergency service
   [ ] Water heaters
   [ ] Standby generators
   [ ] Commercial (tell me; it does not go on this site unless we decide it does)
   [ ] Other:

T2. Brands you install. Tick, and star the one you lead with in each row.
   Central systems: [ ] Carrier  [ ] Bryant  [ ] Trane  [ ] American Standard  [ ] Lennox  [ ] Rheem  [ ] Daikin  [ ] York  [ ] Bosch
   Ductless and VRF: [ ] Mitsubishi Electric  [ ] Daikin  [ ] Fujitsu  [ ] LG  [ ] Bosch  [ ] Gree
   Geothermal: [ ] WaterFurnace  [ ] ClimateMaster  [ ] Bosch  [ ] Carrier  [ ] Enertech  [ ] Dandelion
   Boilers: [ ] Viessmann  [ ] Buderus  [ ] Weil-McLain  [ ] Navien  [ ] Lochinvar  [ ] IBC
   Radiant: [ ] Uponor  [ ] Warmboard  [ ] Rehau  [ ] Viega
   Air quality: [ ] Aprilaire  [ ] Honeywell Home  [ ] RGF REME HALO  [ ] IQAir  [ ] Santa Fe  [ ] RenewAire
   Thermostats: [ ] ecobee  [ ] Google Nest  [ ] Honeywell Home  [ ] Carrier Infinity  [ ] Lennox iComfort  [ ] Mitsubishi kumo cloud
   Zoning and duct sealing: [ ] Arzel  [ ] Honeywell  [ ] EWC Controls  [ ] Aeroseal
   Water heaters: [ ] Rheem  [ ] A. O. Smith  [ ] Bradford White  [ ] Navien  [ ] Rinnai  [ ] Noritz
   Wine cellar: [ ] WhisperKOOL  [ ] CellarPro  [ ] Wine Guardian  [ ] Breezaire
   Anything not listed:

T3. Programs and certifications you hold. Tick, write the tier.
   [ ] Carrier Factory Authorized Dealer   [ ] Carrier President's Award
   [ ] Bryant Factory Authorized Dealer   [ ] Bryant Medal of Excellence
   [ ] Trane Comfort Specialist   [ ] American Standard Customer Care Dealer
   [ ] Lennox Premier Dealer   [ ] Dave Lennox Award
   [ ] Rheem Pro Partner   [ ] Ruud Pro Partner   [ ] York Certified Comfort Expert   [ ] Daikin Comfort Pro
   [ ] Mitsubishi Electric Diamond Contractor   [ ] Mitsubishi Diamond Elite   [ ] Fujitsu Elite Contractor   [ ] LG Pro Dealer   [ ] Bosch Accredited
   [ ] WaterFurnace GeoPro Master Dealer   [ ] ClimateMaster GeoElite
   [ ] Navien Service Specialist   [ ] Aeroseal Certified Dealer
   [ ] NATE certified technicians (how many)   [ ] ACCA member   [ ] EPA 608
   [ ] Other:
   Warranties you can register for a homeowner:

T4. Maintenance plan: do you sell one? Name, price, what is in it.
   answer:
```

### plumbing

```
PART 2: PLUMBING

T1. Services. Tick what you sell. Put 1, 2, 3 next to your biggest money makers.
   [ ] Bathroom and kitchen remodel plumbing, rough and finish
   [ ] Steam showers, freestanding tubs, body sprays
   [ ] Whole-home repipe (copper, PEX)
   [ ] New construction plumbing for custom homes
   [ ] Water heaters: tankless, tank, hybrid, recirculation
   [ ] Water treatment: softeners, whole-home filtration, reverse osmosis, well water
   [ ] Sewer and water line repair and replacement, trenchless, camera inspection
   [ ] Drain cleaning and hydro jetting
   [ ] Leak detection and smart shutoff valves
   [ ] Gas piping: ranges, fireplaces, grills, pool heaters, generators, outdoor kitchens
   [ ] Sump, ejector, and well pumps, battery backup
   [ ] Fixture installation and repair, bidets
   [ ] Radiant floor heat and boilers
   [ ] Outdoor kitchen and pool house plumbing, backflow
   [ ] Emergency service
   [ ] Membership plans
   [ ] Commercial (tell me; it does not go on this site unless we decide it does)
   [ ] Other:

T2. Brands you install. Tick, and star the one you lead with in each row.
   Fixtures: [ ] Kohler  [ ] Moen  [ ] Delta  [ ] Brizo  [ ] Toto  [ ] Grohe  [ ] Hansgrohe  [ ] American Standard
   Showroom fixtures: [ ] House of Rohl  [ ] Waterworks  [ ] Dornbracht  [ ] Newport Brass  [ ] California Faucets  [ ] Kallista
   Toilets and bidets: [ ] Toto  [ ] Kohler  [ ] Duravit  [ ] Brondell
   Steam: [ ] Mr. Steam  [ ] ThermaSol  [ ] Steamist  [ ] Kohler  [ ] Amerec
   Tankless: [ ] Navien  [ ] Rinnai  [ ] Noritz  [ ] Bosch  [ ] Rheem  [ ] A. O. Smith
   Tank and hybrid: [ ] A. O. Smith  [ ] Bradford White  [ ] Rheem  [ ] State  [ ] Ruud
   Water treatment: [ ] Kinetico  [ ] Pentair  [ ] Halo  [ ] Aquasana  [ ] Culligan  [ ] EcoWater
   Pipe: [ ] Uponor  [ ] Viega  [ ] Rehau  [ ] SharkBite  [ ] Zurn  [ ] Charlotte Pipe
   Gas: [ ] Gastite  [ ] TracPipe  [ ] HOME-FLEX  [ ] Ward
   Trenchless: [ ] Perma-Liner  [ ] Nu Flow  [ ] Picote  [ ] MaxLiner  [ ] HammerHead
   Pumps: [ ] Zoeller  [ ] Liberty  [ ] Wayne  [ ] Grundfos  [ ] Goulds  [ ] Little Giant
   Smart water: [ ] Moen Flo  [ ] Phyn  [ ] Flo-Logic  [ ] LeakSmart  [ ] Watts
   Anything not listed:

T3. Programs and certifications you hold. Tick, write the tier.
   [ ] Navien Service Specialist   [ ] Rinnai PRO Network   [ ] Noritz PROCard   [ ] Bosch Accredited   [ ] Rheem Pro Partner
   [ ] Kinetico Authorized Dealer   [ ] Halo Authorized Dealer   [ ] Pentair dealer
   [ ] Uponor trained installer   [ ] Viega ProPress trained
   [ ] Perma-Liner Certified Installer   [ ] Nu Flow Certified   [ ] Moen Flo Pro installer
   [ ] PHCC member   [ ] IAPMO member   [ ] WQA Certified Water Specialist
   [ ] Gas fitter license   [ ] Backflow tester certification
   [ ] Other:
   Warranties you can register for a homeowner:

T4. Membership or service plan: do you sell one? Name, price, what is in it.
   answer:
```

### roofing

```
PART 2: ROOFING

T1. Services. Tick what you sell. Put 1, 2, 3 next to your biggest money makers.
   [ ] Asphalt shingle roof replacement
   [ ] Designer shingles (Grand Sequoia, Presidential, Berkshire class)
   [ ] Standing seam metal
   [ ] Metal shingle or stone-coated steel
   [ ] Natural slate
   [ ] Synthetic slate or shake
   [ ] Cedar shake and shingle
   [ ] Clay or concrete tile
   [ ] Copper: bays, porches, accents
   [ ] Flat and low-slope (TPO, EPDM, modified bitumen)
   [ ] Roof repair and leak repair
   [ ] Storm damage and insurance claims
   [ ] Gutters, seamless and copper
   [ ] Gutter guards
   [ ] Skylights and sun tunnels
   [ ] Attic ventilation and insulation
   [ ] Chimney flashing and custom sheet metal
   [ ] Siding, soffit, fascia
   [ ] Solar roofing
   [ ] Roof inspections (real estate, maintenance)
   [ ] Commercial (tell me; it does not go on this site unless we decide it does)
   [ ] Other:

T2. Brands you install. Tick, and star the one you lead with in each row.
   Shingles: [ ] GAF  [ ] Owens Corning  [ ] CertainTeed  [ ] IKO  [ ] Malarkey  [ ] Atlas  [ ] TAMKO
   Metal: [ ] Englert  [ ] Drexel Metals  [ ] PAC-CLAD  [ ] ATAS  [ ] Sheffield Metals  [ ] McElroy  [ ] DECRA
   Slate and synthetic: [ ] Natural slate (Vermont, Buckingham)  [ ] DaVinci  [ ] Brava  [ ] EcoStar  [ ] Inspire  [ ] CeDUR
   Cedar: [ ] Certi-label  [ ] Watkins  [ ] Teal-Jones
   Tile: [ ] Ludowici  [ ] Westlake Royal (Boral)  [ ] Eagle  [ ] Santafe  [ ] MCA
   Low-slope: [ ] Carlisle  [ ] Holcim Elevate (Firestone)  [ ] GAF EverGuard  [ ] Johns Manville  [ ] Versico  [ ] Sika Sarnafil
   Gutters and guards: [ ] LeafGuard (Englert)  [ ] Gutter Helmet  [ ] K-Guard  [ ] MasterShield  [ ] Raytec  [ ] Gutterglove
   Skylights: [ ] VELUX  [ ] Solatube  [ ] Fakro
   Underlayment: [ ] GAF  [ ] Grace Ice & Water  [ ] Owens Corning  [ ] CertainTeed  [ ] Titanium  [ ] Sharkskin
   Anything not listed:

T3. Programs and certifications you hold. Tick, write the tier.
   [ ] GAF Master Elite   [ ] GAF Certified
   [ ] Owens Corning Platinum Preferred   [ ] Owens Corning Preferred
   [ ] CertainTeed SELECT ShingleMaster   [ ] CertainTeed ShingleMaster
   [ ] IKO ShieldPRO Plus   [ ] Malarkey Emerald Premium   [ ] Atlas Pro Plus   [ ] TAMKO Pro
   [ ] DaVinci Masterpiece Contractor   [ ] Brava Certified Installer   [ ] VELUX Certified Installer
   [ ] Carlisle Authorized Applicator   [ ] Englert Certified Installer
   [ ] NRCA member   [ ] Metal Roofing Alliance member   [ ] HAAG Certified Inspector
   [ ] Other:
   Warranties you can register for a homeowner (Golden Pledge, Platinum Protection, SureStart PLUS, other):

T4. Storm and insurance work: do you want it, and should the site say so?
   answer:
```

## Where each answer goes

Fill `.claude/skills/kickoff/templates/client-brief.md` from this table at wrap. Every item has one home; nothing is written twice.

| Item | `client-brief.md` section | Pre-fills kickoff |
|---|---|---|
| 1 | Header (client name); About copy on the site | prep step 1 |
| 2 | Contact: Owner / approver; Page approver and turnaround | Q17 |
| 3 | Qualification: after-hours rule; GBP hours | Q6 |
| 4 | Contact: Lead inbox; Lead handling baseline | Q12 (arrival only), access row 10 |
| 5, 6, 7 | Service area: ordered city list, exclusions, drive-time limit | Q3 |
| 8 | Qualification: Pricing floor | Q4 (Jonathan still offers a suggestion on the call if blank) |
| 9 | Services and brands: Avg ticket; Biggest project | Q5 |
| 10 | Qualification: qualifying questions | Q14 |
| 11 | Services and brands: Warranty and financing | none today |
| 12 | Proof table | Q8 |
| 13 | Proof: Reviews | Q9 |
| 14 | Build: Primary term | Q32 |
| 15 | Capture: Open flags | Q33 |
| T1 | Services and brands: Rank, Service | Q1 |
| T2 | Services and brands: Brands specced | Q2 |
| T3 | Proof: Credentials on the page | Q7 |
| T4 | roofing: Build blockers note; electrician: Proof referral sources; hvac and plumbing: a Services row; integrator: Contact | Q11 or Q1 |

## Return path

The filled questionnaire arrives as a reply or a shared Doc. In kickoff prep the AIOS copies each answer into the capture's "Already known" block, one line per item number, and lists the blanks as the call's open questions; the call confirms in one line instead of re-asking. At wrap it fills `brief.md` from the table above. Nothing the client wrote is edited; wording is kept where the brief says "their words".

## Blanks

- {Company}, {company}: the client's name as it should print, from item 1 once answered, else from the CRM deal.
- {First name}: the owner or the contact from the sales call.
- {trade label}: Roofer, Electrician, HVAC contractor, Plumber, or AV contractor (home integrator).
- {date}: three business days before the kickoff.
- {Day, date}: the kickoff, from the calendar event the AIOS creates.
- {key}: the trade key, one of integrator, electrician, hvac, plumbing, roofing.
- {slug}: the client folder name, `lowercase-hyphens`, from kickoff prep step 1.
- draft: lines: from the prep site read (kickoff prep step 2), with where it was seen in parentheses. Leave blank when nothing was found.
