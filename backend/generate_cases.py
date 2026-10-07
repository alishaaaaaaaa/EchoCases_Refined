"""
EchoCases Test Data Generator
Generates realistic cold case data spread across North America
Focuses on serious crimes: homicides, shootings, kidnappings, etc.
"""

import csv
import random
from datetime import datetime, timedelta

# Major cities across North America with lat/lon
CITIES = [
    # USA - East Coast
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "state": "NY"},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589, "state": "MA"},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652, "state": "PA"},
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369, "state": "DC"},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918, "state": "FL"},
    {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880, "state": "GA"},
    {"name": "Baltimore", "lat": 39.2904, "lon": -76.6122, "state": "MD"},
    {"name": "Charlotte", "lat": 35.2271, "lon": -80.8431, "state": "NC"},
    
    # USA - Midwest
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "state": "IL"},
    {"name": "Detroit", "lat": 42.3314, "lon": -83.0458, "state": "MI"},
    {"name": "Cleveland", "lat": 41.4993, "lon": -81.6944, "state": "OH"},
    {"name": "Minneapolis", "lat": 44.9778, "lon": -93.2650, "state": "MN"},
    {"name": "St. Louis", "lat": 38.6270, "lon": -90.1994, "state": "MO"},
    {"name": "Kansas City", "lat": 39.0997, "lon": -94.5786, "state": "MO"},
    {"name": "Indianapolis", "lat": 39.7684, "lon": -86.1581, "state": "IN"},
    
    # USA - South
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "state": "TX"},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970, "state": "TX"},
    {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936, "state": "TX"},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431, "state": "TX"},
    {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715, "state": "LA"},
    {"name": "Memphis", "lat": 35.1495, "lon": -90.0490, "state": "TN"},
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816, "state": "TN"},
    
    # USA - West Coast
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "state": "CA"},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "state": "CA"},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611, "state": "CA"},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "state": "WA"},
    {"name": "Portland", "lat": 45.5152, "lon": -122.6784, "state": "OR"},
    {"name": "Las Vegas", "lat": 36.1699, "lon": -115.1398, "state": "NV"},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740, "state": "AZ"},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903, "state": "CO"},
    
    # Canada
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "state": "ON"},
    {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207, "state": "BC"},
    {"name": "Montreal", "lat": 45.5017, "lon": -73.5673, "state": "QC"},
    {"name": "Calgary", "lat": 51.0447, "lon": -114.0719, "state": "AB"},
    {"name": "Edmonton", "lat": 53.5461, "lon": -113.4938, "state": "AB"},
    {"name": "Ottawa", "lat": 45.4215, "lon": -75.6972, "state": "ON"},
]

# Serious crime series patterns (cold cases)
CRIME_SERIES = [
    {
        "name": "Highway Murders",
        "category": "homicide",
        "num_cases": 8,
        "description": "Bodies discovered along interstate highways, victims are hitchhikers and stranded motorists",
        "narratives": [
            "Remains of unidentified female discovered by highway maintenance crew in drainage ditch along I-{highway}. Victim appears to be 20-35 years old, deceased approximately 2-4 weeks. Cause of death: strangulation. No identification found. Possible hitchhiker or stranded motorist.",
            "Body of adult male found in wooded area 50 yards from highway rest stop off I-{highway}. Victim suffered blunt force trauma to head. Personal effects missing. Truck driver reported suspicious vehicle in area night before discovery.",
            "Skeletal remains recovered from embankment near mile marker {mile} on I-{highway}. Forensic analysis indicates female victim, 25-40 years old. Ligature marks on bones suggest binding. Death estimated 6-12 months prior.",
            "Unidentified male victim discovered in culvert near I-{highway} exit ramp. Multiple stab wounds to torso. No wallet or ID. Tattoo on right forearm: 'Maria 1987'. Fingerprints not in system.",
            "Partial remains found scattered along 2-mile stretch of I-{highway} median. DNA confirms single female victim. Evidence of animal activity. Original crime scene likely elsewhere. No missing persons match.",
            "Adult female body recovered from shallow grave near truck stop off I-{highway}. Victim identified through dental records as missing person from 3 states away. Last seen accepting ride from unknown male.",
            "Decomposed remains of male victim found in abandoned vehicle at highway rest area. Vehicle registered to victim - long-haul trucker reported missing 6 weeks prior. Signs of violent struggle in cab.",
            "Jane Doe discovered by joggers in ravine near I-{highway} overpass. Victim is female, late teens to early 20s. Clothing suggests possible sex worker. Cause of death: asphyxiation. No DNA matches in system."
        ],
        "weapons": ["ligature", "blunt object", "knife", "hands"],
        "spread_km": 800
    },
    {
        "name": "Home Invasion Killer",
        "category": "homicide",
        "num_cases": 6,
        "description": "Elderly victims killed during home invasions, minimal theft suggests different motive",
        "narratives": [
            "82-year-old female found deceased in her residence by mail carrier after newspapers accumulated. Victim suffered multiple blunt force injuries. Residence ransacked but valuable jewelry left untouched. No signs of forced entry - victim may have known assailant.",
            "Welfare check requested for 78-year-old male reveals homicide victim. Body discovered in kitchen with severe head trauma. Back door lock defeated with unknown tool. Neighbors report no suspicious activity. $400 cash left in bedroom.",
            "Double homicide at residence of elderly couple. 81-year-old male and 79-year-old female both deceased from strangulation. Home shows signs of prolonged search but only prescription medications taken. Fingerprints recovered but no database match.",
            "75-year-old widow found murdered in her home of 40 years. Cause of death: blunt force trauma. Antique collection valued at $50,000 undisturbed. Victim's vehicle missing - recovered abandoned 3 days later, wiped clean.",
            "Retired teacher, 80, discovered deceased by former student during regular visit. Victim bound with telephone cord, died of cardiac arrest during apparent torture. Safe opened but only personal documents taken. Motive unclear.",
            "88-year-old male, WWII veteran, found murdered in basement of his home. Severe beating preceded death. Military memorabilia and medals still in display case. Killer spent considerable time in home - ate food from refrigerator."
        ],
        "weapons": ["blunt object", "ligature", "hands"],
        "entry_methods": ["unlocked door", "picked lock", "unknown"],
        "spread_km": 400
    },
    {
        "name": "Riverside Strangler",
        "category": "homicide",
        "num_cases": 7,
        "description": "Bodies found near rivers and waterways, victims are young women",
        "narratives": [
            "Body of 23-year-old female recovered from riverbank by fishermen. Victim last seen leaving downtown bar alone. Cause of death: manual strangulation. Defensive wounds on hands. Partial DNA recovered from fingernails - no CODIS match.",
            "Unidentified female discovered in marsh near river confluence. Victim is 18-25 years old, deceased approximately 1 week. Strangulation with unknown ligature. Clothing suggests college student. Missing persons database search ongoing.",
            "22-year-old nursing student found deceased near jogging trail along river. Victim was reported missing 48 hours earlier. Manual strangulation. No sexual assault. Cell phone and purse missing. Last ping 5 miles upstream.",
            "Remains of young female recovered from dam spillway. Advanced decomposition hampers identification. Forensic analysis indicates strangulation. Age estimated 20-30. Distinctive ankle bracelet may aid identification.",
            "Body of 19-year-old discovered on riverbank near university campus. Victim was student reported missing after late night study session. Ligature strangulation with victim's own scarf. No witnesses. Security cameras show her walking alone.",
            "26-year-old waitress found deceased in reeds near river boat launch. Last seen closing restaurant 2 nights prior. Manual strangulation. Vehicle found in restaurant lot. Killer may have offered or forced ride.",
            "Jane Doe recovered from river, cause of death strangulation. Victim appears to be 20-25, athletic build. No matching missing persons. Unique tattoo: small butterfly on left shoulder blade. Reconstruction image distributed to media."
        ],
        "weapons": ["ligature", "hands"],
        "spread_km": 150
    },
    {
        "name": "Carjacking Murders",
        "category": "homicide",
        "num_cases": 5,
        "description": "Victims killed during carjackings, bodies found in vehicles or dumped",
        "narratives": [
            "45-year-old male found deceased in his vehicle in parking garage. Single gunshot wound to head. Vehicle still running, wallet and watch taken. Security footage shows masked suspect approaching victim as he entered vehicle.",
            "Woman, 34, discovered shot to death in her SUV at shopping center. Two gunshot wounds to chest. Purse and vehicle keys taken but vehicle not moved. Witness heard shots, saw suspect flee on foot. Shell casings recovered.",
            "Ride-share driver, 52, found murdered in his vehicle on residential street. Multiple stab wounds. Last fare was cash pickup - no app record. Phone and cash missing. Vehicle GPS shows erratic route before stopping.",
            "Businessman, 48, killed during apparent carjacking at gas station. Shot twice while pumping gas. Suspect fled in victim's luxury sedan. Vehicle recovered 2 states away, burned. Suspect believed to wear distinctive ring.",
            "Real estate agent, 41, found deceased in client's driveway. Showing appointment was fake - property was vacant. Single gunshot wound. Vehicle and personal effects missing. Phone traced to river - no recovery."
        ],
        "weapons": ["handgun", "knife"],
        "spread_km": 600
    },
    {
        "name": "Missing Hikers",
        "category": "homicide",
        "num_cases": 6,
        "description": "Hikers who vanished in national forests, some remains later discovered",
        "narratives": [
            "Partial remains of missing hiker discovered by search team in remote canyon. 28-year-old male had departed for solo day hike 8 months prior. Forensic evidence indicates foul play - skull shows gunshot trauma. No weapon recovered.",
            "Campsite of missing couple discovered intact - tent, supplies, vehicle all present. 31-year-old male and 29-year-old female never returned from weekend trip. Blood evidence in tent. No bodies recovered after extensive search.",
            "Skeletal remains found by hunters identified as missing backpacker. 24-year-old female vanished 2 years ago during thru-hike. Cause of death: blunt force trauma. Body moved post-mortem to remote location.",
            "Missing solo female hiker, 26, found deceased in abandoned mine shaft. Death ruled homicide - victim did not fall. Had been deceased approximately 3 weeks. Last seen by other hikers 20 miles from discovery site.",
            "Remains of 2 missing hikers discovered in same drainage. Male, 35, and female, 32, were strangers who vanished weeks apart. Both show signs of homicide. Possible serial predator targeting isolated hikers.",
            "33-year-old experienced mountaineer found deceased below cliff face. Initially thought to be fall, investigation reveals pre-mortem injuries inconsistent with fall. Evidence of struggle at cliff top. Camera and GPS missing."
        ],
        "weapons": ["handgun", "blunt object", "unknown"],
        "spread_km": 1000
    },
    {
        "name": "Nightclub Shootings",
        "category": "homicide",
        "num_cases": 5,
        "description": "Targeted shootings outside nightclubs and bars, gang-related suspected",
        "narratives": [
            "Three victims shot outside nightclub at closing time. One deceased at scene (male, 24), two critical. Suspect in dark sedan fired approximately 15 rounds. Victims believed to be targeted - no robbery attempt. Shell casings indicate 9mm.",
            "Single victim (male, 28) shot execution-style in parking lot behind club. Bouncer heard single shot at 2:15 AM. Victim had previous arrests but no known gang ties. Wallet and jewelry left on body. Professional hit suspected.",
            "Drive-by shooting outside bar leaves two dead. Male victims ages 22 and 25. Witnesses report black SUV, multiple shooters. 30+ shell casings recovered. Victims were attending birthday party. Retaliation suspected.",
            "26-year-old male shot multiple times outside lounge. Victim was waiting for ride-share when suspect approached on foot. No words exchanged before shooting. Suspect fled in waiting vehicle. Victim had no criminal history.",
            "Shooting in club parking garage kills 1, wounds 3. Deceased is 30-year-old male with prior drug arrests. Suspect described as male, 20s, wearing hoodie. Security cameras disabled prior to shooting. Targeted assassination suspected."
        ],
        "weapons": ["9mm handgun", "handgun", ".45 caliber"],
        "spread_km": 300
    },
    {
        "name": "Child Abductions",
        "category": "kidnapping",
        "num_cases": 6,
        "description": "Children abducted from various locations, some recovered, some still missing",
        "narratives": [
            "8-year-old female abducted from front yard while playing. Witness saw white van stop, child was pulled inside. Vehicle fled westbound. Amber Alert issued. Child's bicycle left at scene. No ransom demand received.",
            "12-year-old male disappeared during walk home from school. Normal 10-minute route, never arrived home. Backpack found in alley 2 blocks from school. Witness reports seeing boy talking to adult male in blue pickup.",
            "6-year-old female taken from bedroom during night. Parents discovered empty bed at 6 AM. No signs of forced entry - window screen removed from inside. Family has no known enemies. No note or communication.",
            "10-year-old male vanished from crowded fair. Parents lost sight for approximately 3 minutes. Extensive search found no trace. Security footage shows child walking with unidentified adult male toward exit.",
            "Sisters ages 7 and 9 abducted from bus stop. School bus driver reports they never boarded. Witness saw children enter dark SUV voluntarily - may have known suspect. No custody disputes. Parents frantic.",
            "14-year-old female missing after online contact with unknown person. Parents discovered messages from 'Mike, 16' who was actually adult male. Agreed to meet at mall. Never returned. Phone turned off."
        ],
        "weapons": ["none", "unknown"],
        "spread_km": 500
    },
    {
        "name": "Drug Deal Murders",
        "category": "homicide",
        "num_cases": 7,
        "description": "Bodies found in locations associated with drug transactions",
        "narratives": [
            "Two males found shot to death in motel room. Victims are 28 and 31, both with drug trafficking histories. Room was rented under false name. Large quantity of cocaine missing per informant. Execution-style wounds.",
            "Body discovered in trunk of burned vehicle in industrial area. Victim is male, 35, known mid-level dealer. Shot twice in head before car was torched. Rival organization suspected. No witnesses.",
            "25-year-old male found deceased in alley behind known drug house. Multiple gunshot wounds. Victim had $10,000 cash in backpack - not robbery. Believed to be enforcer for trafficking organization. Retaliation hit.",
            "Three bodies discovered in abandoned warehouse. Victims: 2 males (29, 33) and 1 female (27). All shot execution-style. Scene suggests drug transaction gone wrong. 5 kilos of heroin found nearby.",
            "Unidentified male found in dumpster behind strip mall. Shot once in head. Victim's hands bound with zip ties. No ID, no phone. Tattoos suggest cartel affiliation. Dumped post-mortem.",
            "Informant (male, 30) found murdered in his apartment. Tortured before death. Handler suspects cover was blown. Victim provided intel on trafficking routes. Message killing - sending warning to others.",
            "22-year-old female, believed to be drug courier, found deceased in rest area bathroom. Overdose initially suspected but autopsy reveals strangulation. Drugs she was carrying missing. Double-crossed by organization."
        ],
        "weapons": ["handgun", "9mm", ".45 caliber"],
        "spread_km": 400
    },
    {
        "name": "Campus Attacks",
        "category": "assault",
        "num_cases": 6,
        "description": "Violent attacks on university students, possibly connected",
        "narratives": [
            "Female student, 20, attacked while walking to dorm at 11 PM. Suspect grabbed victim from behind, attempted strangulation. Victim fought back, suspect fled when other students approached. Description: male, 6ft, dark hoodie.",
            "Graduate student, 24, found severely beaten in library parking garage. Victim in medically induced coma. No robbery - laptop and wallet present. Security camera shows suspect following victim from building.",
            "Two female students attacked in separate incidents same night. Both grabbed near athletic fields. First victim escaped with minor injuries. Second victim hospitalized with head trauma. Same suspect description.",
            "Male student, 22, stabbed multiple times while jogging on campus trail at dusk. Victim survived but cannot identify attacker who wore mask. Knife wound pattern matches previous unsolved campus assault.",
            "Female student, 19, abducted from sorority house parking lot. Forced into her own vehicle. Jumped from moving car 3 miles away. Treated for injuries, suspect fled in victim's car. Vehicle recovered abandoned.",
            "International student, 21, attacked in her apartment. Suspect entered through unlocked window. Victim fought back with knife, wounding suspect. Suspect fled leaving blood evidence. DNA in system - prior assault conviction."
        ],
        "weapons": ["hands", "knife", "blunt object"],
        "spread_km": 200
    },
    {
        "name": "Witness Eliminations",
        "category": "homicide", 
        "num_cases": 5,
        "description": "Witnesses and informants killed before trial testimony",
        "narratives": [
            "Key witness in upcoming RICO trial found shot in apartment. 42-year-old male was scheduled to testify in 2 weeks. US Marshals were arranging protection. Professional hit - suppressed weapon, no forensic evidence.",
            "Former gang member turned informant, 29, killed in drive-by outside cousin's home. Victim was living under assumed name. Location somehow leaked. 20+ rounds fired. Victim's testimony was crucial to prosecution.",
            "Witness to armored car robbery found deceased. 38-year-old female was only person who could identify shooter. Strangled in her home. No forced entry. Suspect had inside information about witness location.",
            "34-year-old male, witness to nightclub murder, shot while leaving work. Victim had reluctantly agreed to testify. Hit occurred despite changed work schedule. Suspect had surveillance on victim for days.",
            "Bookkeeper prepared to testify against employer found dead from apparent suicide. Family disputes finding. Victim had expressed fear for safety. Note appears coerced. Evidence of second person in home."
        ],
        "weapons": ["suppressed handgun", "handgun", "ligature"],
        "spread_km": 700
    }
]

# Background (unlinked) cases. Each narrative is assembled from independent
# random parts, so no two background cases share a narrative word for word.
# Earlier versions drew 150 cases from 20 fixed narratives, which created
# dozens of exact duplicates that any embedding model clusters together,
# making the clustering evaluation measure duplicate detection instead of
# series detection.
SEXES = ["male", "female"]

BACKGROUND_PARTS = {
    "homicide": {
        "found": [
            "discovered by a construction crew at a development site",
            "recovered from a drainage canal by city maintenance workers",
            "found in a vacant apartment after neighbors reported an odor",
            "located in a wooded lot behind a shopping plaza",
            "pulled from a river near a boat launch",
            "found in the trunk of a vehicle at an impound lot",
            "discovered in a storage unit after rent went unpaid",
            "found at the bottom of a stairwell in a parking structure",
            "located in a field by a farmer clearing brush",
            "found inside a motel room by housekeeping staff",
        ],
        "cause": [
            "Cause of death: single gunshot wound",
            "Cause of death: blunt force trauma to the head",
            "Autopsy found multiple stab wounds",
            "Medical examiner ruled death by asphyxiation",
            "Cause of death undetermined due to decomposition",
            "Death attributed to a fall, but injuries are inconsistent with that account",
            "Toxicology found a lethal dose of an unprescribed sedative",
        ],
        "detail": [
            "No identification was found on the body",
            "Wallet and phone were still present",
            "A distinctive tattoo is being circulated to the public",
            "Dental records were used to make the identification",
            "Victim had been reported missing by a sibling weeks earlier",
            "A business partner was questioned and released",
            "Surveillance footage from the area was overwritten before it could be pulled",
            "Victim had recently changed jobs and moved to the area",
            "Scene appeared to have been cleaned before discovery",
        ],
        "status": [
            "No suspect has been identified.",
            "Case went cold after initial leads were exhausted.",
            "A person of interest left the state shortly after.",
            "Evidence is awaiting modern DNA testing.",
            "Family continues to press for a review.",
            "Detectives believe the victim knew the offender.",
        ],
    },
    "missing person": {
        "last_seen": [
            "never returned home after a late shift",
            "was last seen leaving a grocery store",
            "disappeared after dropping children at school",
            "was last seen boarding a regional bus",
            "vanished after a family dinner",
            "did not show up for work on a Monday",
            "was last seen walking near a lakeside trail",
            "left a friend's apartment and was not heard from again",
            "was last seen at a gas station on camera",
        ],
        "evidence": [
            "Vehicle was found at the workplace with keys inside",
            "Phone was found switched off at home",
            "Bank accounts have not been accessed since",
            "A search of the surrounding area found no trace",
            "Last phone signal came from a tower several miles away",
            "Personal belongings were left behind, including medication",
            "A neighbor reported hearing an argument that night",
        ],
        "background": [
            "Family reports no known financial problems",
            "Had recently ended a relationship",
            "Had a history of short absences but always stayed in contact",
            "Was described as reliable and routine-driven",
            "Had moved to the area less than a year earlier",
            "Was caring for an elderly parent",
        ],
        "status": [
            "Foul play has not been ruled out.",
            "Family is offering a reward for information.",
            "Case remains open with no active leads.",
            "Investigators consider the disappearance suspicious.",
            "Tips received so far have not been confirmed.",
        ],
    },
    "robbery": {
        "event": [
            "Armed robbery of a convenience store late at night",
            "Robbery of a pharmacy shortly before closing",
            "Takeover robbery of a credit union branch",
            "Robbery of a delivery driver during a route stop",
            "Robbery of a jewelry store during business hours",
            "Robbery of a check-cashing business",
            "Robbery of a restaurant manager making a bank deposit",
            "Robbery of a cash-in-transit courier at a strip mall",
        ],
        "suspects": [
            "A single masked suspect displayed a handgun",
            "Two suspects in hooded sweatshirts were involved",
            "Three suspects wearing gloves and masks entered together",
            "Suspect passed a note demanding cash",
            "Suspect posed as a customer before drawing a weapon",
        ],
        "outcome": [
            "An employee was injured during the robbery",
            "No one was physically harmed",
            "A bystander was struck while the suspects fled",
            "A security guard was wounded",
            "The clerk was locked in a back room",
        ],
        "evidence": [
            "Getaway vehicle was found abandoned and burned",
            "Partial fingerprints were lifted from the counter",
            "Surveillance cameras had been disabled beforehand",
            "A discarded glove was recovered nearby",
            "Witnesses gave conflicting descriptions of the vehicle",
        ],
        "status": [
            "Inside information is suspected.",
            "No arrests have been made.",
            "Stolen property has not surfaced.",
            "Investigators have no named suspect.",
        ],
    },
    "sexual assault": {
        "event": [
            "Woman assaulted while walking to her car after work",
            "Assault reported after a victim accepted a ride home",
            "Victim assaulted in a stairwell of her apartment building",
            "Assault reported following a first date arranged online",
            "Victim attacked on a jogging path in the early morning",
            "Assault reported after a house party",
        ],
        "suspect": [
            "Suspect was described as a stranger wearing dark clothing",
            "Suspect used a false name and a prepaid phone",
            "Victim did not see the suspect's face",
            "Suspect fled when a passerby approached",
            "Suspect was known to the victim only by a nickname",
        ],
        "evidence": [
            "A forensic exam was completed and the kit was submitted for testing",
            "No DNA was recovered",
            "A partial DNA profile was developed but has no database match",
            "Nearby cameras were not working",
            "Phone records are under review",
        ],
        "status": [
            "Case remains open.",
            "Investigators are reviewing the case with new testing methods.",
            "No similar reports were found in the area.",
            "Victim continues to cooperate with detectives.",
        ],
    },
}

BACKGROUND_CATEGORIES = list(BACKGROUND_PARTS)


def random_background_narrative(category):
    p = BACKGROUND_PARTS[category]
    age = random.randint(19, 74)
    sex = random.choice(SEXES)
    if category == "homicide":
        return (f"Body of {sex} victim, approximately {age} years old, {random.choice(p['found'])}. "
                f"{random.choice(p['cause'])}. {random.choice(p['detail'])}. {random.choice(p['status'])}")
    if category == "missing person":
        return (f"{age}-year-old {sex} {random.choice(p['last_seen'])}. {random.choice(p['evidence'])}. "
                f"{random.choice(p['background'])}. {random.choice(p['status'])}")
    if category == "robbery":
        return (f"{random.choice(p['event'])}. {random.choice(p['suspects'])}. "
                f"{random.choice(p['outcome'])}. {random.choice(p['evidence'])}. {random.choice(p['status'])}")
    return (f"{random.choice(p['event'])}. Victim is {age} years old. {random.choice(p['suspect'])}. "
            f"{random.choice(p['evidence'])}. {random.choice(p['status'])}")


def random_location_near_city(city, spread_km=50):
    """Generate random coordinates near a city"""
    # Convert km to approximate degrees (rough approximation)
    spread_lat = spread_km / 111  # 1 degree lat ≈ 111 km
    spread_lon = spread_km / (111 * abs(cos(radians(city["lat"]))))
    
    lat = city["lat"] + random.uniform(-spread_lat, spread_lat)
    lon = city["lon"] + random.uniform(-spread_lon, spread_lon)
    return round(lat, 4), round(lon, 4)


def cos(x):
    import math
    return math.cos(x)


def radians(x):
    import math
    return math.radians(x)


def generate_case_id(index):
    """Generate a realistic case ID"""
    year = random.randint(1995, 2024)
    state = random.choice(["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "AZ", "CO", "OR", "NV"])
    return f"{state}-{year}-{str(index).zfill(5)}"


def generate_timestamp(years_back_min=1, years_back_max=25):
    """Generate a random timestamp for cold case"""
    days_back = random.randint(years_back_min * 365, years_back_max * 365)
    date = datetime.now() - timedelta(days=days_back)
    # Random hour, weighted toward night for crimes
    if random.random() < 0.6:
        hour = random.randint(20, 23) if random.random() < 0.5 else random.randint(0, 5)
    else:
        hour = random.randint(6, 19)
    date = date.replace(hour=hour, minute=random.randint(0, 59))
    return date.isoformat()


def generate_cases():
    """Generate all test cases"""
    cases = []
    case_index = 1
    
    print("Generating cold case data spread across North America...")
    
    # Generate series cases
    for series in CRIME_SERIES:
        print(f"  Generating series: {series['name']} ({series['num_cases']} cases)")
        
        # Pick 2-4 cities for this series to operate in
        series_cities = random.sample(CITIES, min(4, len(CITIES)))
        
        # Generate base date for series
        base_date = datetime.now() - timedelta(days=random.randint(365, 365*15))
        
        for i in range(series['num_cases']):
            # Pick a city from series cities
            city = random.choice(series_cities)
            lat, lon = random_location_near_city(city, spread_km=series['spread_km'] / 10)
            
            # Generate timestamp with some progression
            days_offset = i * random.randint(14, 120)  # Cases spread over time
            timestamp = (base_date + timedelta(days=days_offset)).replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59)
            )
            
            # Get narrative
            narrative_template = random.choice(series['narratives'])
            narrative = narrative_template.format(
                highway=random.randint(5, 95),
                mile=random.randint(10, 300)
            )
            
            case = {
                "case_id": generate_case_id(case_index),
                "timestamp": timestamp.isoformat(),
                "lat": lat,
                "lon": lon,
                "narrative": narrative,
                "category": series['category'],
                "weapon": random.choice(series.get('weapons', ['unknown'])),
                "entry_method": random.choice(series.get('entry_methods', [''])),
                "tool_used": "",
                "tags": f"{series['name'].lower().replace(' ', '_')},cold_case,unsolved",
                "city": city['name'],
                "state": city['state']
            }
            cases.append(case)
            case_index += 1
    
    # Generate random unconnected cases to fill out dataset
    num_random = 150  # Fewer random cases
    print(f"  Generating {num_random} additional random cold cases...")
    
    for i in range(num_random):
        city = random.choice(CITIES)
        lat, lon = random_location_near_city(city, spread_km=30)
        
        category = random.choice(BACKGROUND_CATEGORIES)
        narrative = random_background_narrative(category)
        
        case = {
            "case_id": generate_case_id(case_index),
            "timestamp": generate_timestamp(),
            "lat": lat,
            "lon": lon,
            "narrative": narrative,
            "category": category,
            "weapon": random.choice(["handgun", "knife", "blunt object", "ligature", "unknown", ""]),
            "entry_method": random.choice(["forced entry", "unlocked", "window", "picked lock", "unknown", ""]),
            "tool_used": random.choice(["pry bar", "lock picks", "cutting tool", ""]),
            "tags": "cold_case,unsolved",
            "city": city['name'],
            "state": city['state']
        }
        cases.append(case)
        case_index += 1
    
    return cases


def main():
    # Optional seed for a reproducible dataset: python generate_cases.py 42
    import sys
    if len(sys.argv) > 1:
        random.seed(int(sys.argv[1]))
    cases = generate_cases()
    
    # Write to CSV
    fieldnames = ["case_id", "timestamp", "lat", "lon", "narrative", "category", 
                  "weapon", "entry_method", "tool_used", "tags", "city", "state"]
    
    with open("cases.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cases)
    
    print(f"\nGenerated {len(cases)} cold cases")
    print(f"Saved to cases.csv")
    
    # Print summary
    categories = {}
    for case in cases:
        cat = case['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCase breakdown by category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
