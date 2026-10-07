"""Query grid for places_seed.py. Data only.

LOCATIONS: the largest US metros plus the enclaves where $2M to $25M homes cluster (the Monarc ICP's
job sites). The 29 metros behind Integrator_List_2026-09-05.xlsx are all here, so the new seed is a superset.
QUERIES: text-search templates. The first four plus "lutron dealer" match the templates recorded in that
workbook's Extras sheet; "control4 dealer" is new. Edit here, not in the script.
"""

# --- 29 metros from the 2026-09-05 harvest (kept first so a --limit-locations smoke test hits known ground)
ORIGINAL_METROS = [
    "San Francisco, CA", "San Jose, CA", "Los Angeles, CA", "San Diego, CA", "Sacramento, CA",
    "Seattle, WA", "Portland, OR", "Las Vegas, NV", "Phoenix, AZ", "Denver, CO",
    "Dallas, TX", "Houston, TX", "Austin, TX", "San Antonio, TX", "Kansas City, MO",
    "Minneapolis, MN", "Chicago, IL", "Columbus, OH", "Nashville, TN", "Atlanta, GA",
    "Charlotte, NC", "Miami, FL", "Orlando, FL", "Tampa, FL", "Washington, DC",
    "Philadelphia, PA", "New York, NY", "Boston, MA", "Boston, MA",
]

# --- remaining large metros (rounding out the top ~100 by population)
MORE_METROS = [
    "Oakland, CA", "Fresno, CA", "Riverside, CA", "Irvine, CA", "Long Beach, CA", "Bakersfield, CA",
    "Santa Rosa, CA", "Walnut Creek, CA", "Palo Alto, CA", "Pasadena, CA", "Thousand Oaks, CA",
    "Tacoma, WA", "Spokane, WA", "Boise, ID", "Salt Lake City, UT", "Reno, NV", "Tucson, AZ",
    "Albuquerque, NM", "Colorado Springs, CO", "Fort Collins, CO", "Omaha, NE", "Des Moines, IA",
    "Oklahoma City, OK", "Tulsa, OK", "Fort Worth, TX", "Plano, TX", "Frisco, TX", "El Paso, TX",
    "McAllen, TX", "Corpus Christi, TX", "New Orleans, LA", "Baton Rouge, LA", "Little Rock, AR",
    "Memphis, TN", "Knoxville, TN", "Chattanooga, TN", "Birmingham, AL", "Huntsville, AL",
    "Jackson, MS", "Louisville, KY", "Lexington, KY", "Cincinnati, OH", "Cleveland, OH", "Dayton, OH",
    "Indianapolis, IN", "Fort Wayne, IN", "Detroit, MI", "Grand Rapids, MI", "Ann Arbor, MI",
    "Milwaukee, WI", "Madison, WI", "St. Louis, MO", "Wichita, KS", "Naperville, IL",
    "Pittsburgh, PA", "Harrisburg, PA", "Buffalo, NY", "Rochester, NY", "Albany, NY", "Long Island, NY",
    "Westchester County, NY", "Newark, NJ", "Princeton, NJ", "Morristown, NJ", "Hartford, CT",
    "Stamford, CT", "New Haven, CT", "Providence, RI", "Portsmouth, NH", "Portland, ME", "Burlington, VT",
    "Baltimore, MD", "Bethesda, MD", "Annapolis, MD", "Richmond, VA", "Virginia Beach, VA",
    "Northern Virginia, VA", "Raleigh, NC", "Durham, NC", "Greensboro, NC", "Asheville, NC",
    "Wilmington, NC", "Columbia, SC", "Greenville, SC", "Charleston, SC", "Savannah, GA",
    "Augusta, GA", "Jacksonville, FL", "Fort Lauderdale, FL", "West Palm Beach, FL", "Fort Myers, FL",
    "Pensacola, FL", "Tallahassee, FL", "Gainesville, FL", "Daytona Beach, FL", "Honolulu, HI",
    "Anchorage, AK", "Charlotte, NC",
]

# --- high-net-worth enclaves: where the $2M to $25M residential work happens
ENCLAVES = [
    "Naples, FL", "Palm Beach, FL", "Boca Raton, FL", "Sarasota, FL", "Jupiter, FL", "Vero Beach, FL",
    "Key Largo, FL", "Destin, FL", "Santa Rosa Beach, FL",
    "Scottsdale, AZ", "Paradise Valley, AZ", "Sedona, AZ",
    "Aspen, CO", "Vail, CO", "Telluride, CO", "Steamboat Springs, CO", "Cherry Hills Village, CO",
    "Park City, UT", "Jackson, WY", "Sun Valley, ID", "Big Sky, MT", "Whitefish, MT",
    "Napa, CA", "Carmel-by-the-Sea, CA", "Montecito, CA", "Santa Barbara, CA", "Newport Beach, CA",
    "La Jolla, CA", "Rancho Santa Fe, CA", "Malibu, CA", "Beverly Hills, CA", "Atherton, CA",
    "Los Altos, CA", "Palm Springs, CA", "Palm Desert, CA", "South Lake Tahoe, CA", "Truckee, CA",
    "Incline Village, NV", "Bellevue, WA", "Mercer Island, WA", "Bainbridge Island, WA", "Bend, OR",
    "Lake Oswego, OR", "Boulder, CO",
    "Greenwich, CT", "Westport, CT", "Darien, CT", "Southampton, NY", "East Hampton, NY",
    "Rye, NY", "Scarsdale, NY", "Short Hills, NJ", "Alpine, NJ", "Cape Cod, MA", "Nantucket, MA",
    "Martha's Vineyard, MA", "Wellesley, MA", "Newport, RI", "Kennebunkport, ME",
    "Hilton Head Island, SC", "Kiawah Island, SC", "Sea Island, GA", "Highlands, NC", "Cashiers, NC",
    "Lake Norman, NC", "Pinehurst, NC", "Lake Geneva, WI", "Lake Minnetonka, MN", "Barrington, IL",
    "Lake Forest, IL", "Hinsdale, IL", "Ladue, MO", "Leawood, KS", "Franklin, TN", "Brentwood, TN",
    "Alpharetta, GA", "Buckhead, GA", "The Woodlands, TX", "Southlake, TX", "Highland Park, TX",
    "Westlake, TX", "Horseshoe Bay, TX", "Fredericksburg, TX", "Great Falls, VA", "McLean, VA",
    "Potomac, MD", "Easton, MD", "St. Michaels, MD",
]


def _dedup(seq):
    seen, out = set(), []
    for s in seq:
        k = s.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(s.strip())
    return out


LOCATIONS = _dedup(ORIGINAL_METROS + MORE_METROS + ENCLAVES)

QUERIES = [
    "home automation installer in {loc}",
    "home theater installation in {loc}",
    "audio video integrator in {loc}",
    "smart home integrator in {loc}",
    "lutron dealer in {loc}",
    "control4 dealer in {loc}",
]

if __name__ == "__main__":
    print(f"{len(LOCATIONS)} locations, {len(QUERIES)} queries, "
          f"{len(LOCATIONS) * len(QUERIES)} text searches, up to {len(LOCATIONS) * len(QUERIES) * 3} requests")
