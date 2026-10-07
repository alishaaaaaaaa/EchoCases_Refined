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

# Additional random cold case templates for variety
RANDOM_CASE_TEMPLATES = [
    {
        "category": "homicide",
        "narratives": [
            "Unidentified remains discovered by construction crew at development site. Victim appears to be male, 30-50 years old. Skeletal condition indicates death occurred 5-15 years ago. Cause of death: gunshot wound to chest. No matching missing persons.",
            "Body of male, approximately 45 years old, recovered from water treatment facility. Victim weighted down with concrete blocks. Death estimated 1-2 months prior. No identification. Distinctive surgical scar on abdomen.",
            "Female victim found in abandoned building by urban explorers. Deceased appears to be 25-35, death occurred 1-2 weeks prior. Multiple stab wounds. Scene staged to look like overdose. Identity unknown.",
            "Remains discovered in shallow grave at closed campground. Victim is male, 20-30 years old. Blunt force trauma to skull. Personal effects recovered include class ring from out-of-state university.",
            "Burned remains found in industrial incinerator. Dental records identify victim as missing businessman, 52. Declared missing 6 months ago. Insurance investigation ongoing. Partner of interest."
        ]
    },
    {
        "category": "missing person",
        "narratives": [
            "32-year-old female never returned from late shift. Vehicle found at workplace, purse inside. No signs of struggle. Extensive search of surrounding area found no trace. Cell phone last pinged 2 miles south.",
            "Father of three, 41, vanished during morning jog. Running shoes found on trail but no other evidence. No financial or marital problems known. Family offers $50,000 reward. Case active but no leads.",
            "Teenager, 17, disappeared after leaving for friend's house. Friend claims he never arrived. Phone and wallet left at home. No history of running away. Family suspects foul play.",
            "Elderly woman with dementia, 79, walked away from care facility. Last seen on security camera heading toward woods. Extensive search found no trace. Foul play not ruled out due to missing woman in past.",
            "Truck driver, 38, last seen at weigh station. Truck found abandoned 200 miles away, cargo intact. No use of credit cards or phone. Wife reports no problems at home. Voluntarily missing or foul play unknown."
        ]
    },
    {
        "category": "robbery",
        "narratives": [
            "Armed robbery of jewelry store leaves owner in critical condition. Three masked suspects with handguns. $500,000 in merchandise taken. Getaway vehicle found burned. Professional crew suspected.",
            "Bank robbery results in death of security guard. Lone suspect demanded cash, shot guard when he reached for alarm. $45,000 taken. Suspect fled in stolen vehicle. DNA recovered from discarded mask.",
            "Armored car ambushed during ATM service. Two guards killed, one wounded. $2.3 million taken. Suspects used spike strips and heavy weapons. Inside information suspected. FBI involved.",
            "Home invasion robbery of known drug dealer leaves 3 dead. Victims were dealer, girlfriend, and associate. Large quantity of cash and drugs taken. Rival gang or robbery crew unknown.",
            "Casino employee robbed and murdered while transporting chips. Body found in parking garage, $200,000 in chips missing. Inside job suspected. Employee had gambling debts."
        ]
    },
    {
        "category": "sexual assault",
        "narratives": [
            "Woman attacked while walking dog in park at dusk. Suspect wore mask, fled when victim screamed. Partial DNA recovered. Similar attacks reported in neighboring counties over past 2 years.",
            "Home invasion sexual assault. Suspect entered through basement window while victim slept alone. Attacked victim in bedroom. Fled when motion light activated. Left behind glove with DNA.",
            "Multiple victims report attacks by suspect using dating app. Victims drugged then assaulted. 4 victims in 6 months. Same suspect description. App account traced to burner phone.",
            "College student assaulted at off-campus party. Victim was drugged. Woke in unfamiliar location. Limited memory of attack. Suspect may have recorded assault. Investigation ongoing.",
            "Serial assailant targeting women in apartment complex. 3 attacks in 4 months. Suspect has key or picks locks. Attacks occur when victims are alone. No DNA left at scenes."
        ]
    }
]


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
        
        template_group = random.choice(RANDOM_CASE_TEMPLATES)
        narrative = random.choice(template_group['narratives'])
        
        case = {
            "case_id": generate_case_id(case_index),
            "timestamp": generate_timestamp(),
            "lat": lat,
            "lon": lon,
            "narrative": narrative,
            "category": template_group['category'],
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
