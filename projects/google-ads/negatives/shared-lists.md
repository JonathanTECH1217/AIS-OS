# Shared negative keyword lists

Account level. Each list below becomes one shared negative list in Google Ads ("Monarc: <name>"), attached to the campaigns on its "Applies to" line. Each campaign's own list is in `<service>.md` next to this file. Rebuilt 2026-09-28 from the six research files and the plan (Jonathan: "make the negative list thorough").

**How a line reads** (Google's rules; a negative never stretches to plurals, misspellings, or near words, so every form is written out):
- `plain words`: blocks any search that has every word, in any order.
- `"quoted words"`: blocks a search that has the words side by side, in that order.
- `[bracketed words]`: blocks only that exact search.

**Before pasting or publishing:** `python scripts/ads_negative_check.py` must say OK. It fails if any negative blocks one of a campaign's keywords, or if a single word on the "Never negative" list shows up as a negative. New terms from the weekly search-terms loop (`../search-terms-log.md`) are added with a date in the Log.

## Jobs and careers

People looking for work, not hiring.

Applies to: all

```
job
jobs
career
careers
salary
salaries
wage
wages
"pay scale"
"hourly pay"
resume
resumes
cv
intern
interns
internship
internships
apprentice
apprentices
apprenticeship
apprenticeships
recruiter
recruiters
recruiting
recruitment
staffing
employment
vacancy
vacancies
"job openings"
"now hiring"
"hiring near me"
"companies hiring"
"part time"
"full time"
"entry level"
"work from home"
"side hustle"
indeed
glassdoor
ziprecruiter
"how to become"
"become a"
"trade school"
journeyman
ibew
"license exam"
```

## Learn and do it yourself

People who want to learn it, not pay for it. Blog and article stay off: a contractor buying SEO content types them.

Applies to: all

```
"how to"
"how do"
"how does"
"how can"
"what is"
"what are"
"what does"
"why is"
"why are"
"why do"
tutorial
tutorials
course
courses
class
classes
lesson
lessons
training
certification
certifications
certificate
certificates
exam
exams
quiz
guide
guides
"step by step"
tips
tricks
hacks
ideas
example
examples
sample
samples
template
templates
checklist
checklists
"cheat sheet"
worksheet
diy
"do it yourself"
yourself
myself
"on my own"
pdf
ebook
ebooks
books
podcast
podcasts
youtube
webinar
webinars
reddit
quora
forum
forums
wiki
wikipedia
definition
meaning
"for dummies"
"for beginners"
beginner
beginners
learn
learning
statistics
stats
trends
benchmarks
glossary
udemy
coursera
skillshare
skillshop
"hubspot academy"
"chatgpt prompts"
```

## Cheap and free

Price hunters. The pages show no price and the retainer starts at $2,000 a month.

Applies to: all

```
free
freebie
freebies
cheap
cheaper
cheapest
"low cost"
budget
discount
discounts
coupon
coupons
"promo code"
"promo codes"
voucher
vouchers
groupon
deal
deals
"99 dollars"
```

## Software and tools

People shopping for a tool to run themselves. Not on 06: in the automation campaign "software" can still be a buyer (a watch term there).

Applies to: all except 06

```
software
softwares
tool
tools
app
apps
platform
platforms
saas
plugin
plugins
extension
extensions
api
script
scripts
download
downloads
crm
crms
"website builder"
"website builders"
"site builder"
"page builder"
generator
calculator
calculators
spreadsheet
excel
"google sheets"
zapier
hubspot
mailchimp
"constant contact"
klaviyo
activecampaign
sendgrid
wix
squarespace
godaddy
weebly
"wordpress theme"
"wordpress themes"
themeforest
elementor
divi
shopify
semrush
ahrefs
moz
ubersuggest
yoast
"rank math"
brightlocal
whitespark
birdeye
podium
jobber
servicetitan
"service titan"
"housecall pro"
housecallpro
gohighlevel
"go high level"
highlevel
vendasta
yext
canva
hootsuite
"sprout social"
quickbooks
xero
buildertrend
```

## Homeowner

A homeowner who wants the job done, not a contractor who wants customers. Trade words, "installer", and "residential" stay off this list because the good searches use them; so do "fix" and "replace" ("fix my google ads", "replace my marketing agency" are buyers).

Applies to: all

```
repair
repairs
repairing
replacement
replacements
install
installing
installed
installation
installations
"installer near me"
"installers near me"
"installation near me"
"electrician near me"
"electricians near me"
"plumber near me"
"plumbers near me"
"roofer near me"
"roofers near me"
"roofing near me"
"hvac near me"
"ac near me"
"contractor near me"
"contractors near me"
"handyman near me"
handyman
emergency
"24 hour"
"same day"
leak
leaks
leaking
clog
clogged
drain
drains
toilet
toilets
faucet
faucets
"water heater"
"water heaters"
tankless
furnace
furnaces
"ac unit"
"ac units"
"air conditioner"
"air conditioners"
"heat pump"
"heat pumps"
"mini split"
"mini splits"
ductwork
"duct cleaning"
thermostat
thermostats
"tune up"
"ac maintenance"
"hvac maintenance"
"furnace maintenance"
inspection
inspections
shingle
shingles
gutter
gutters
"metal roof"
"roof leak"
skylight
skylights
"sump pump"
sewer
septic
"panel upgrade"
"electrical panel"
breaker
breakers
outlet
outlets
"light fixture"
"light fixtures"
"ceiling fan"
"ceiling fans"
"ev charger"
"ev chargers"
"home generator"
"standby generator"
"tv mounting"
"tv mount"
"tv wall mount"
"home theater setup"
"speaker installation"
"sonos setup"
wifi
"mesh wifi"
"doorbell camera"
"ring doorbell"
nest
alexa
"google home"
homekit
"apple homekit"
smartthings
"philips hue"
wyze
arlo
simplisafe
vivint
adt
caseta
"lutron caseta"
"control4 price"
"control4 cost"
"control4 app"
"control4 remote"
"savant app"
"sonos app"
"for my house"
"for my home"
"in my house"
"in my home"
"my house"
homeowner
homeowners
"cost to install"
"price to install"
"roof estimate"
"roofing estimate"
"hvac quote"
"plumbing quote"
"electrical quote"
rent
rental
rentals
"for sale"
used
"home depot"
lowes
"best buy"
"geek squad"
```

## Other meanings of our words

The same words used for something else: government work, factory controls, audio gear rental, hobby smart homes, lighting parts, lead the metal, and more.

Applies to: all

```
"government contractor"
"government contractors"
"federal contractor"
"federal contractors"
"defense contractor"
"defense contractors"
"military contractor"
"independent contractor"
"independent contractors"
1099
"contractor license"
"contractors license"
"contractor insurance"
"contractor bond"
"contractors bond"
"contractor loan"
"contractor loans"
"contractor financing"
"contract template"
"contractor agreement"
"subcontractor agreement"
erp
salesforce
"sap integrator"
"it integrator"
plc
scada
robotics
robot
robots
industrial
manufacturing
factory
warehouse
"integrator calculator"
"integrator circuit"
"op amp"
"integral calculator"
"antelope valley"
"av club"
"av rental"
"av rentals"
"event av"
"av production"
"av receiver"
"av receivers"
"av cable"
"av cables"
"av equipment rental"
"av actress"
jav
"av idol"
"home assistant"
"raspberry pi"
arduino
zigbee
"z wave"
zwave
hubitat
homebridge
openhab
"node red"
esphome
"smart plug"
"smart plugs"
"smart bulb"
"smart bulbs"
"smart lock"
"smart locks"
"low voltage lighting"
"low voltage landscape lighting"
"low voltage transformer"
"low voltage wire"
"low voltage wiring"
"low voltage license"
"low voltage cable"
"low voltage outdoor lighting"
"lead paint"
"lead pipe"
"lead pipes"
"lead poisoning"
"lead abatement"
"lead time"
"lead times"
"lead testing"
"sensor leads"
"test leads"
"lead free"
mario
"super mario"
"plumber game"
"plumbers crack"
"roofing nails"
"roofing materials"
"roofing supply"
"roofing supplies"
"abc supply"
"roofing calculator"
"hvac school"
"hvac filter"
"hvac filters"
"hvac supply"
"hvac technician"
"hvac technicians"
"epa 608"
"electrician tools"
"electrical code"
nec
"electrical engineering"
```

## Lead buyers

People who want to buy leads from a marketplace or a list, not hire an agency.

Applies to: all

```
angi
"angies list"
"angie's list"
homeadvisor
"home advisor"
thumbtack
houzz
porch
networx
bark
yelp
nextdoor
"buy leads"
"buying leads"
"pay per lead"
"pay per call"
"exclusive leads"
"shared leads"
"lead list"
"lead lists"
"leads list"
"leads for sale"
"construction leads"
"contractor leads"
"roofing leads"
"hvac leads"
"plumbing leads"
"electrical leads"
"electrician leads"
"solar leads"
"permit data"
"permit leads"
"building permits"
```

## Labor shoppers

People who want a cheap freelancer, want to resell, or want to start an agency.

Applies to: all

```
"white label"
whitelabel
"white labeled"
reseller
resellers
resell
"private label"
freelancer
freelancers
freelance
upwork
fiverr
toptal
peopleperhour
affiliate
affiliates
"affiliate program"
"partner program"
"become a partner"
"agency partner"
"for agencies"
"start an agency"
"start a marketing agency"
"agency owner"
"agency owners"
"sell seo"
offshore
overseas
```

## Wrong country or language

Monarc targets US searchers, English only. Names that are also US places stay off, because a buyer adds the town to the search: Birmingham, Manchester, Melbourne, Bristol, Perth, Victoria, Hamilton, Mexico (New Mexico), England (New England), Wales (North Wales, PA), Britain (New Britain, CT), London (New London), Ontario (Ontario, CA).

Applies to: all

```
canada
canadian
uk
"united kingdom"
british
scotland
ireland
irish
australia
australian
"new zealand"
nz
india
pakistan
bangladesh
philippines
nigeria
kenya
"south africa"
uae
dubai
"abu dhabi"
"saudi arabia"
qatar
singapore
malaysia
indonesia
germany
france
spain
brazil
"hong kong"
toronto
vancouver
calgary
edmonton
montreal
ottawa
winnipeg
"british columbia"
alberta
quebec
"nova scotia"
halifax
saskatchewan
manitoba
mississauga
brampton
glasgow
edinburgh
cardiff
sydney
brisbane
adelaide
auckland
queensland
"new south wales"
mumbai
delhi
bangalore
bengaluru
hyderabad
chennai
pune
kolkata
noida
gurgaon
ahmedabad
optimisation
optimise
organisation
"gas engineer"
"gas engineers"
tradie
tradies
sparky
sparkies
"plumbers merchant"
postcode
spanish
espanol
"en espanol"
"cerca de mi"
"para contratistas"
```

## Other industries

Other kinds of business looking for the same services. Matters most once broad match turns on for 01. College, university, and church stay off (College Park, University Park, Falls Church).

Applies to: all

```
dentist
dentists
dental
orthodontist
lawyer
lawyers
attorney
attorneys
"law firm"
"law firms"
legal
restaurant
restaurants
"real estate"
realtor
realtors
mortgage
mortgages
"loan officer"
insurance
chiropractor
chiropractors
"med spa"
medspa
"medical spa"
medical
doctor
doctors
clinic
clinics
healthcare
"home health"
"home care"
salon
salons
gym
gyms
fitness
"personal trainer"
nonprofit
nonprofits
"non profit"
school
schools
ecommerce
"e commerce"
"online store"
amazon
etsy
ebay
"car dealership"
"auto dealer"
dealership
dealerships
"car wash"
hotel
hotels
"property management"
landscaping
landscaper
landscapers
"lawn care"
"pest control"
"cleaning company"
"cleaning services"
"maid service"
"carpet cleaning"
"moving company"
movers
"junk removal"
"pressure washing"
"pool service"
"tree service"
solar
startup
startups
b2b
crypto
cannabis
casino
casinos
```

## Account and support

People trying to reach a login or a help desk, or leave a service.

Applies to: all

```
login
"log in"
"sign in"
signin
"sign up"
signup
"customer service"
"customer support"
"support number"
"phone number"
"contact number"
"help center"
refund
refunds
cancel
unsubscribe
"delete account"
"account suspended"
"password reset"
"reset password"
"forgot password"
lawsuit
"class action"
```

## Compare words (launch only)

Comparison shoppers and price checkers. The pages show no price, so they bounce. This list comes off every campaign when the "compare" ad group opens at 15 conversions (campaign 01 brief).

Applies to: all

```
best
top
"top 10"
"top rated"
review
reviews
reviewed
rating
ratings
rated
vs
versus
compare
comparison
alternative
alternatives
cost
costs
price
prices
pricing
"how much"
fees
rates
"worth it"
"is it worth"
scam
scams
complaint
complaints
```

## Never negative

Never add one of these as a one-word negative, on any list: the good searches use them. The check script refuses them. A longer phrase that contains one is fine if the check passes.

```
integration
integrations
integrator
integrators
installer
installers
residential
commercial
certified
manager
managers
management
hire
hiring
quote
quotes
estimate
estimates
outsource
outsourced
book
booking
bookings
control4
lutron
savant
crestron
sonos
dealer
dealers
lead
leads
contractor
contractors
electrician
electricians
electrical
hvac
roofing
roofer
roofers
plumber
plumbers
plumbing
home
automation
agency
agencies
company
companies
service
services
marketing
near
me
```

## Watch list

Not negatives until the search terms show Monarc paying for them. Add a date and the search term that triggered it.

- Competitor agency names seen on the results pages: Hook Agency, Blue Corona, Scorpion, RYNO, One Firefly, Footbridge, Contractor Dynamics, WebFX, Thrive, Built Right Digital, Periscope, Relentless, Specifi.
- affordable (a small-budget buyer can still sign)
- construction, general contractor, remodeling (contractors, not the five trades)
- hosting (website management can include it)
- suspended (a suspended Google Business Profile is an SEO buyer)
- virtual assistant (adjacent to the back-office automation buyer)
- landscape lighting (integrators do outdoor lighting)
- lead generation company (a lead vendor, or an agency like Monarc)

## Log

- 2026-09-25: first lists drafted from the plan. Nothing pasted into the account.
- 2026-09-26: research negatives written per service to `../keywords/paste/`.
- 2026-09-28: rebuilt into twelve lists with every plural written out, a never-negative list, and a watch list. Removed from the old lists because they blocked good searches: hire, quote, estimate, installer, outsource, book, and "best electrician/plumber/roofer/hvac" (the compare list covers "best"). Campaign lists moved to `<service>.md`, checked by `scripts/ads_negative_check.py`.
