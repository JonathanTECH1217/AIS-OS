# Electrician: services and brands

Draft by the AIOS 2026-09-24, not yet confirmed by Jonathan. Residential, high-end homes. Trade key `electrician`. Jonathan strikes and adds here; the electrician block in Part 2 of `templates/onboarding-questionnaire.md` mirrors this file (top names per row), so edit the map first, then the block. Same uses as `context/icp-brands.md`: the kickoff read-back (Q1, Q2, Q7), landing page terms (brand plus service plus city), prospect list filtering. Programs marked (confirm name) were written from memory. Never print a program on a client page without the certificate in `projects/clients/<slug>/assets/` or the manufacturer's public locator showing the client. The electrician vertical already exists in the CRM (`projects/crm/config.json`, added 2026-09-24).

## Services (one landing page category each)

Panel upgrades and service changes (200A, 400A), subpanels, smart panels; whole-home rewire; remodel and addition wiring; new construction wiring for custom homes; recessed and architectural lighting, lighting design, under-cabinet, cove; landscape and outdoor lighting; lighting control and smart switches; standby generators, transfer switches, generator service; EV charger installation; whole-home surge protection; battery storage and solar interconnect; pool, spa, hot tub, sauna, and outdoor kitchen wiring; electric heated floors and snow melt; ceiling fans, dedicated circuits, GFCI and AFCI; low-voltage prewire (network, AV, security, cameras); troubleshooting and repair; aluminum wiring and knob-and-tube remediation; home inspection repairs.

## Brands by category

### Panels and load centers
Square D (QO, Homeline), Eaton (CH, BR), Siemens, Leviton Load Center, ABB (GE), SPAN, Schneider Pulse, Lumin

### Generators and transfer switches
Generac, Kohler, Briggs & Stratton, Cummins, Champion; transfer switches: Reliance Controls

### EV chargers
Tesla (Wall Connector, Universal Wall Connector), ChargePoint Home Flex, Wallbox Pulsar Plus, Enel X JuiceBox, Emporia, Grizzl-E, Autel, Leviton

### Lighting control
Lutron (Caseta, RadioRA 3, HomeWorks, Maestro), Leviton Decora Smart, Legrand (radiant, adorne), Brilliant, Control4, Crestron, Savant

### Fixtures
WAC, DMF, Juno, Halo, Lithonia, Elco, Nora, USAI, Ketra, Lucifer, Element (Tech Lighting), Visual Comfort, Hinkley, Kichler

### Landscape lighting
FX Luminaire, Kichler, Vista, VOLT, Coastal Source, Unique Lighting, Hunza

### Devices and wire
Lutron, Leviton, Legrand Pass & Seymour, Hubbell, Eaton; wire: Southwire, Cerrowire; boxes and fittings: Arlington, Carlon

### Surge protection
Siemens FirstSurge, Eaton CHSPT2, Square D HEPD80, Leviton, Intermatic, Ditek

### Fans
Big Ass Fans (Haiku), Minka-Aire, Modern Forms, Hunter, Fanimation

### Battery storage and solar
Tesla Powerwall, Enphase IQ Battery, SolarEdge, Generac PWRcell, FranklinWH, Sol-Ark

### Heated floors and snow melt
WarmlyYours, Nuheat, SunTouch, Warmup, Heatizon

## Dealer and certification programs

| Program | Manufacturer | What it signals | Public locator |
|---|---|---|---|
| PowerPro Premier Dealer | Generac | Top tier: sales, install, and 24 hour service | yes, generac.com |
| PowerPro Elite Dealer | Generac | Second tier | yes |
| Authorized Sales and Service Dealer | Generac | Entry tier | yes |
| Authorized Generator Dealer (tiers, confirm name) | Kohler | Sales and service | yes, kohlerpower.com |
| Authorized Dealer | Cummins | Sales and service | yes |
| Premier Dealer (confirm name) | Briggs & Stratton | Sales and service | yes |
| Certified Installer | Tesla | Powerwall and Wall Connector | yes, tesla.com |
| Certified Installer (confirm name) | ChargePoint | Home Flex | confirm |
| Certified Installer | Qmerit | EV charger and storage referral network used by automakers | yes, qmerit.com |
| Caseta Pro, RadioRA 3 certified (confirm name) | Lutron | Lighting control, mid tier | yes, lutron.com |
| HomeWorks dealer | Lutron | Whole-home lighting control; the high-end signal | yes, lutron.com |
| Installer Network: Platinum, Gold, Silver | Enphase | Solar and storage | yes, enphase.com |
| Certified Installer (confirm name) | SPAN | Smart panel | confirm |
| Member | NECA | Trade association | yes |
| Member | IEC | Trade association | yes |
| Member | CEDIA | Low-voltage crossover; an integrator-adjacent shop | yes, cedia.net |
| Member | ESA (Electronic Security Association) | Security and low voltage | yes |

Licenses: Master Electrician or Journeyman class, state or county number. The number prints on the site and comes in on the asset email (item 3), not on the questionnaire.

## Warranty names a homeowner asks about

Generac 5, 7, and 10 year extended warranties sold at install; Kohler 5 year residential; Tesla Powerwall 10 year; Enphase IQ Battery 10 or 15 year (confirm terms); Lutron limited warranty by product line. Workmanship warranty is the electrician's own (questionnaire item 11).

## How the AIOS uses this (notes)

- High-end signals: Lutron HomeWorks dealer, 400A services, Ketra or Lucifer fixtures, generator plus battery on the same job, low voltage done in house.
- Crossover with Monarc's integrator base: an electrician who ticks low-voltage prewire and CEDIA is half an integrator; one who refers it out (T4) names a referral partner worth knowing.
- List building: Generac, Kohler, Lutron, Tesla, Qmerit, and Enphase publish installer locators searchable by zip.
- Landing pages: one page per service above. Brand names on the page are the ones the client ticked and starred in T2, with the program from T3 only when the certificate is on file.
- Kickoff Q7 for electricians: look up the Generac and Lutron locators before the call and confirm.
