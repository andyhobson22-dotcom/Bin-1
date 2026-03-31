"""Generate realistic player squads for all teams."""
import json
import random
import os

# Common English/Welsh/Irish/Scottish rugby first and last names
FIRST_NAMES = [
    "James", "Owen", "Ben", "Tom", "George", "Jack", "Harry", "Marcus",
    "Freddie", "Ellis", "Max", "Sam", "Charlie", "Ollie", "Finn",
    "Will", "Joe", "Dan", "Alex", "Luke", "Manu", "Kyle", "Maro",
    "Jamie", "Jonny", "Lewis", "Henry", "Alfie", "Bevan", "Cadan",
    "Dafydd", "Rhys", "Gareth", "Liam", "Connor", "Sean", "Patrick",
    "Tadhg", "Conor", "Bundee", "Hamish", "Rory", "Stuart", "Greig",
    "Cameron", "Blair", "Taulupe", "Billy", "Courtney", "Anthony",
    "Nick", "Matt", "Josh", "Toby", "Zach", "Noah", "Ethan",
    "Oscar", "Archie", "Leo", "Theo", "Arthur", "Adam", "Callum",
]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Wilson", "Davies",
    "Evans", "Thomas", "Johnson", "Roberts", "Walker", "Wright", "Thompson",
    "White", "Hall", "Green", "Harris", "Clark", "Robinson", "Mitchell",
    "Farrell", "Ford", "Itoje", "Lawes", "Curry", "Underhill", "Slade",
    "May", "Watson", "Daly", "Youngs", "Care", "Spencer", "Dombrandt",
    "Marchant", "Steward", "Arundell", "Freeman", "Ludlam", "Hill",
    "Ewels", "Isiekwe", "Stuart", "George", "Genge", "Sinckler",
    "Cowan-Dickie", "Earl", "Willis", "Shields", "Hartley", "Reid",
    "McConnochie", "Obano", "De Glanville", "Barbeary", "Van Poortvliet",
    "Heyes", "Wells", "Chessum", "Kelly", "Randall", "Lloyd", "Moroni",
]

NATIONALITIES = [
    ('England', 70), ('Wales', 10), ('Ireland', 8), ('Scotland', 7),
    ('South Africa', 2), ('New Zealand', 1), ('Australia', 1), ('Fiji', 1),
]
NATIONALITY_NAMES = [n for n, _ in NATIONALITIES]
NATIONALITY_WEIGHTS = [w for _, w in NATIONALITIES]

# Height (cm) and weight (kg) ranges by position group
BODY_PROFILES = {
    'loosehead_prop': {'height': (178, 188), 'weight': (110, 125)},
    'hooker': {'height': (175, 185), 'weight': (100, 115)},
    'tighthead_prop': {'height': (180, 190), 'weight': (115, 130)},
    'lock': {'height': (193, 205), 'weight': (105, 120)},
    'flanker': {'height': (183, 195), 'weight': (95, 112)},
    'number_eight': {'height': (185, 198), 'weight': (100, 118)},
    'scrum_half': {'height': (170, 182), 'weight': (78, 90)},
    'fly_half': {'height': (175, 188), 'weight': (82, 95)},
    'centre': {'height': (178, 192), 'weight': (88, 105)},
    'wing': {'height': (175, 190), 'weight': (80, 98)},
    'fullback': {'height': (178, 190), 'weight': (82, 95)},
}

# Squad template: position -> count of players needed
SQUAD_TEMPLATE = {
    'loosehead_prop': 2,
    'hooker': 2,
    'tighthead_prop': 2,
    'lock_4': 2,
    'lock_5': 2,
    'blindside_flanker': 2,
    'openside_flanker': 2,
    'number_eight': 2,
    'scrum_half': 2,
    'fly_half': 2,
    'left_wing': 2,
    'inside_centre': 2,
    'outside_centre': 2,
    'right_wing': 2,
    'fullback': 2,
}

# All 35 stats grouped
ALL_STATS = [
    # Physical (7)
    'stopping_power', 'explosiveness', 'leg_drive', 'pace', 'acceleration',
    'agility', 'strength',
    # Mental (9)
    'aggression', 'composure', 'concentration', 'awareness', 'running_lines',
    'discipline', 'tenacity', 'scanning', 'positioning',
    # Technical (13)
    'long_passing', 'handling', 'high_ball', 'offload', 'tackling',
    'rucking', 'mauling', 'jackling', 'grubber', 'chipping',
    'box_kicking', 'stepping', 'short_passing',
    # Set Piece (6)
    'goal_kicking', 'scrum_drive', 'scrum_tech', 'touch_finder',
    'jumping', 'lifting',
]

# Base stat profiles by position group — ranges for each of the 35 stats
STAT_PROFILES = {
    'loosehead_prop': {
        # Physical
        'stopping_power': (65, 90), 'explosiveness': (30, 55), 'leg_drive': (70, 95),
        'pace': (25, 45), 'acceleration': (25, 45), 'agility': (20, 42),
        'strength': (75, 99),
        # Mental
        'aggression': (55, 80), 'composure': (35, 60), 'concentration': (40, 65),
        'awareness': (30, 55), 'running_lines': (15, 35), 'discipline': (40, 70),
        'tenacity': (55, 80), 'scanning': (25, 45), 'positioning': (40, 65),
        # Technical
        'long_passing': (10, 30), 'handling': (25, 50), 'high_ball': (10, 25),
        'offload': (20, 45), 'tackling': (55, 80), 'rucking': (55, 80),
        'mauling': (65, 90), 'jackling': (15, 35), 'grubber': (5, 15),
        'chipping': (5, 15), 'box_kicking': (5, 10), 'stepping': (10, 30),
        'short_passing': (25, 50),
        # Set Piece
        'goal_kicking': (5, 15), 'scrum_drive': (70, 95), 'scrum_tech': (65, 90),
        'touch_finder': (10, 25), 'jumping': (15, 35), 'lifting': (50, 75),
    },
    'hooker': {
        'stopping_power': (55, 80), 'explosiveness': (35, 60), 'leg_drive': (55, 80),
        'pace': (35, 55), 'acceleration': (35, 58), 'agility': (30, 52),
        'strength': (65, 88),
        'aggression': (55, 80), 'composure': (40, 65), 'concentration': (50, 75),
        'awareness': (40, 65), 'running_lines': (25, 45), 'discipline': (40, 70),
        'tenacity': (55, 80), 'scanning': (35, 60), 'positioning': (45, 70),
        'long_passing': (15, 35), 'handling': (40, 65), 'high_ball': (15, 35),
        'offload': (25, 50), 'tackling': (60, 85), 'rucking': (55, 80),
        'mauling': (55, 80), 'jackling': (25, 50), 'grubber': (5, 15),
        'chipping': (5, 15), 'box_kicking': (5, 10), 'stepping': (15, 35),
        'short_passing': (35, 60),
        'goal_kicking': (5, 15), 'scrum_drive': (55, 80), 'scrum_tech': (50, 75),
        'touch_finder': (10, 25), 'jumping': (35, 60), 'lifting': (45, 70),
    },
    'tighthead_prop': {
        'stopping_power': (70, 95), 'explosiveness': (25, 50), 'leg_drive': (75, 99),
        'pace': (20, 40), 'acceleration': (20, 40), 'agility': (15, 38),
        'strength': (78, 99),
        'aggression': (55, 85), 'composure': (35, 60), 'concentration': (40, 65),
        'awareness': (25, 50), 'running_lines': (10, 30), 'discipline': (35, 65),
        'tenacity': (60, 85), 'scanning': (20, 40), 'positioning': (35, 60),
        'long_passing': (5, 25), 'handling': (20, 45), 'high_ball': (5, 20),
        'offload': (15, 40), 'tackling': (55, 78), 'rucking': (55, 78),
        'mauling': (68, 92), 'jackling': (10, 30), 'grubber': (5, 12),
        'chipping': (5, 12), 'box_kicking': (5, 10), 'stepping': (8, 25),
        'short_passing': (20, 45),
        'goal_kicking': (5, 12), 'scrum_drive': (75, 99), 'scrum_tech': (72, 95),
        'touch_finder': (8, 22), 'jumping': (15, 35), 'lifting': (50, 75),
    },
    'lock': {
        'stopping_power': (55, 80), 'explosiveness': (35, 58), 'leg_drive': (55, 80),
        'pace': (35, 55), 'acceleration': (30, 52), 'agility': (25, 48),
        'strength': (65, 90),
        'aggression': (55, 82), 'composure': (40, 65), 'concentration': (45, 70),
        'awareness': (40, 65), 'running_lines': (25, 45), 'discipline': (40, 72),
        'tenacity': (60, 85), 'scanning': (35, 58), 'positioning': (45, 70),
        'long_passing': (10, 30), 'handling': (30, 55), 'high_ball': (35, 60),
        'offload': (25, 50), 'tackling': (55, 80), 'rucking': (55, 80),
        'mauling': (55, 82), 'jackling': (20, 45), 'grubber': (5, 15),
        'chipping': (5, 15), 'box_kicking': (5, 10), 'stepping': (12, 30),
        'short_passing': (25, 50),
        'goal_kicking': (5, 15), 'scrum_drive': (50, 75), 'scrum_tech': (45, 70),
        'touch_finder': (10, 25), 'jumping': (70, 95), 'lifting': (60, 85),
    },
    'flanker': {
        'stopping_power': (55, 80), 'explosiveness': (55, 80), 'leg_drive': (55, 80),
        'pace': (50, 75), 'acceleration': (52, 78), 'agility': (45, 70),
        'strength': (60, 85),
        'aggression': (65, 92), 'composure': (45, 70), 'concentration': (55, 80),
        'awareness': (55, 80), 'running_lines': (40, 65), 'discipline': (40, 72),
        'tenacity': (70, 95), 'scanning': (50, 75), 'positioning': (55, 80),
        'long_passing': (15, 40), 'handling': (40, 65), 'high_ball': (25, 50),
        'offload': (35, 60), 'tackling': (70, 95), 'rucking': (65, 90),
        'mauling': (45, 70), 'jackling': (55, 85), 'grubber': (5, 20),
        'chipping': (5, 18), 'box_kicking': (5, 12), 'stepping': (25, 50),
        'short_passing': (35, 60),
        'goal_kicking': (5, 15), 'scrum_drive': (45, 70), 'scrum_tech': (40, 65),
        'touch_finder': (10, 30), 'jumping': (45, 72), 'lifting': (40, 65),
    },
    'number_eight': {
        'stopping_power': (60, 85), 'explosiveness': (50, 75), 'leg_drive': (55, 82),
        'pace': (45, 70), 'acceleration': (48, 72), 'agility': (40, 65),
        'strength': (65, 90),
        'aggression': (60, 85), 'composure': (45, 70), 'concentration': (50, 75),
        'awareness': (50, 78), 'running_lines': (45, 70), 'discipline': (40, 70),
        'tenacity': (60, 88), 'scanning': (45, 70), 'positioning': (50, 75),
        'long_passing': (20, 45), 'handling': (45, 70), 'high_ball': (25, 50),
        'offload': (40, 68), 'tackling': (60, 85), 'rucking': (58, 82),
        'mauling': (55, 80), 'jackling': (35, 60), 'grubber': (8, 25),
        'chipping': (8, 22), 'box_kicking': (5, 12), 'stepping': (30, 55),
        'short_passing': (35, 62),
        'goal_kicking': (5, 18), 'scrum_drive': (55, 80), 'scrum_tech': (45, 72),
        'touch_finder': (12, 30), 'jumping': (40, 65), 'lifting': (35, 60),
    },
    'scrum_half': {
        'stopping_power': (20, 45), 'explosiveness': (60, 85), 'leg_drive': (30, 55),
        'pace': (60, 85), 'acceleration': (65, 90), 'agility': (62, 88),
        'strength': (28, 52),
        'aggression': (45, 72), 'composure': (55, 82), 'concentration': (55, 80),
        'awareness': (60, 85), 'running_lines': (45, 72), 'discipline': (50, 80),
        'tenacity': (55, 80), 'scanning': (60, 85), 'positioning': (55, 80),
        'long_passing': (60, 88), 'handling': (60, 85), 'high_ball': (25, 50),
        'offload': (30, 55), 'tackling': (40, 65), 'rucking': (35, 60),
        'mauling': (10, 25), 'jackling': (20, 45), 'grubber': (35, 62),
        'chipping': (30, 58), 'box_kicking': (55, 85), 'stepping': (50, 78),
        'short_passing': (65, 92),
        'goal_kicking': (15, 45), 'scrum_drive': (10, 25), 'scrum_tech': (10, 25),
        'touch_finder': (35, 62), 'jumping': (15, 35), 'lifting': (10, 25),
    },
    'fly_half': {
        'stopping_power': (20, 45), 'explosiveness': (50, 75), 'leg_drive': (25, 50),
        'pace': (50, 75), 'acceleration': (52, 78), 'agility': (55, 82),
        'strength': (30, 55),
        'aggression': (35, 60), 'composure': (60, 88), 'concentration': (60, 85),
        'awareness': (65, 92), 'running_lines': (50, 78), 'discipline': (55, 85),
        'tenacity': (40, 65), 'scanning': (65, 92), 'positioning': (60, 85),
        'long_passing': (60, 90), 'handling': (60, 85), 'high_ball': (40, 68),
        'offload': (30, 55), 'tackling': (35, 60), 'rucking': (20, 42),
        'mauling': (10, 22), 'jackling': (10, 28), 'grubber': (50, 80),
        'chipping': (50, 78), 'box_kicking': (25, 50), 'stepping': (45, 75),
        'short_passing': (62, 90),
        'goal_kicking': (55, 92), 'scrum_drive': (8, 20), 'scrum_tech': (8, 20),
        'touch_finder': (55, 85), 'jumping': (20, 42), 'lifting': (10, 25),
    },
    'centre': {
        'stopping_power': (45, 72), 'explosiveness': (52, 78), 'leg_drive': (40, 65),
        'pace': (55, 80), 'acceleration': (55, 82), 'agility': (55, 80),
        'strength': (50, 75),
        'aggression': (45, 72), 'composure': (50, 78), 'concentration': (50, 75),
        'awareness': (55, 80), 'running_lines': (55, 82), 'discipline': (48, 78),
        'tenacity': (50, 75), 'scanning': (50, 75), 'positioning': (50, 78),
        'long_passing': (40, 68), 'handling': (50, 78), 'high_ball': (35, 62),
        'offload': (40, 68), 'tackling': (55, 80), 'rucking': (30, 55),
        'mauling': (15, 35), 'jackling': (15, 38), 'grubber': (25, 52),
        'chipping': (25, 52), 'box_kicking': (10, 25), 'stepping': (50, 78),
        'short_passing': (50, 78),
        'goal_kicking': (15, 45), 'scrum_drive': (10, 25), 'scrum_tech': (10, 22),
        'touch_finder': (25, 55), 'jumping': (25, 48), 'lifting': (15, 35),
    },
    'wing': {
        'stopping_power': (25, 50), 'explosiveness': (65, 92), 'leg_drive': (25, 50),
        'pace': (72, 99), 'acceleration': (70, 98), 'agility': (65, 92),
        'strength': (35, 62),
        'aggression': (35, 60), 'composure': (45, 72), 'concentration': (45, 70),
        'awareness': (45, 72), 'running_lines': (50, 78), 'discipline': (48, 78),
        'tenacity': (40, 68), 'scanning': (40, 65), 'positioning': (50, 78),
        'long_passing': (20, 45), 'handling': (52, 80), 'high_ball': (45, 75),
        'offload': (35, 62), 'tackling': (35, 62), 'rucking': (15, 35),
        'mauling': (8, 20), 'jackling': (8, 25), 'grubber': (25, 55),
        'chipping': (30, 58), 'box_kicking': (5, 15), 'stepping': (60, 90),
        'short_passing': (30, 58),
        'goal_kicking': (10, 40), 'scrum_drive': (5, 15), 'scrum_tech': (5, 12),
        'touch_finder': (20, 50), 'jumping': (35, 62), 'lifting': (10, 25),
    },
    'fullback': {
        'stopping_power': (28, 55), 'explosiveness': (55, 82), 'leg_drive': (28, 52),
        'pace': (60, 85), 'acceleration': (60, 85), 'agility': (58, 85),
        'strength': (35, 58),
        'aggression': (35, 58), 'composure': (55, 82), 'concentration': (55, 80),
        'awareness': (60, 85), 'running_lines': (52, 80), 'discipline': (52, 82),
        'tenacity': (42, 68), 'scanning': (58, 85), 'positioning': (60, 85),
        'long_passing': (35, 62), 'handling': (55, 82), 'high_ball': (60, 88),
        'offload': (30, 58), 'tackling': (40, 68), 'rucking': (15, 35),
        'mauling': (8, 20), 'jackling': (8, 22), 'grubber': (35, 65),
        'chipping': (35, 62), 'box_kicking': (15, 35), 'stepping': (48, 78),
        'short_passing': (40, 68),
        'goal_kicking': (35, 72), 'scrum_drive': (5, 15), 'scrum_tech': (5, 12),
        'touch_finder': (45, 78), 'jumping': (40, 65), 'lifting': (10, 25),
    },
}

POSITION_TO_PROFILE = {
    'loosehead_prop': 'loosehead_prop',
    'hooker': 'hooker',
    'tighthead_prop': 'tighthead_prop',
    'lock_4': 'lock',
    'lock_5': 'lock',
    'blindside_flanker': 'flanker',
    'openside_flanker': 'flanker',
    'number_eight': 'number_eight',
    'scrum_half': 'scrum_half',
    'fly_half': 'fly_half',
    'inside_centre': 'centre',
    'outside_centre': 'centre',
    'left_wing': 'wing',
    'right_wing': 'wing',
    'fullback': 'fullback',
}

# Secondary position mappings
SECONDARY_POSITIONS = {
    'loosehead_prop': ['tighthead_prop'],
    'hooker': [],
    'tighthead_prop': ['loosehead_prop'],
    'lock_4': ['lock_5', 'blindside_flanker'],
    'lock_5': ['lock_4', 'blindside_flanker'],
    'blindside_flanker': ['openside_flanker', 'number_eight', 'lock_5'],
    'openside_flanker': ['blindside_flanker', 'number_eight'],
    'number_eight': ['blindside_flanker', 'openside_flanker'],
    'scrum_half': [],
    'fly_half': ['inside_centre', 'fullback'],
    'inside_centre': ['outside_centre', 'fly_half'],
    'outside_centre': ['inside_centre', 'left_wing', 'right_wing'],
    'left_wing': ['right_wing', 'fullback'],
    'right_wing': ['left_wing', 'fullback'],
    'fullback': ['fly_half', 'left_wing', 'right_wing'],
}

# Real players to inject into specific teams
REAL_PLAYERS = {
    "Sale Sharks": [
        {
            "name": "Tom Curry", "age": 26, "position": "openside_flanker",
            "secondary_positions": ["blindside_flanker", "number_eight"],
            "nationality": "England", "height": 185, "weight": 110,
            "potential": 90, "form": 72, "morale": 75, "fitness": 95,
            "wage": 12000, "contract_end": 3,
            # Physical
            "stopping_power": 78, "explosiveness": 80, "leg_drive": 76,
            "pace": 74, "acceleration": 78, "agility": 68, "strength": 82,
            # Mental
            "aggression": 85, "composure": 72, "concentration": 78,
            "awareness": 80, "running_lines": 68, "discipline": 72,
            "tenacity": 92, "scanning": 78, "positioning": 82,
            # Technical
            "long_passing": 42, "handling": 65, "high_ball": 55,
            "offload": 58, "tackling": 92, "rucking": 88,
            "mauling": 68, "jackling": 90, "grubber": 18,
            "chipping": 15, "box_kicking": 10, "stepping": 52,
            "short_passing": 55,
            # Set Piece
            "goal_kicking": 10, "scrum_drive": 62, "scrum_tech": 55,
            "touch_finder": 22, "jumping": 65, "lifting": 55,
        },
    ],
}


def generate_stat(low, high, reputation_modifier):
    """Generate a stat with some randomness and team quality modifier."""
    base = random.randint(low, high)
    modified = base + reputation_modifier
    return max(1, min(99, modified))


def generate_player(position, team_reputation, used_names):
    """Generate a single player for a given position."""
    profile = STAT_PROFILES[POSITION_TO_PROFILE[position]]
    rep_mod = (team_reputation - 65) // 5  # -3 to +4 range

    # Generate unique name
    while True:
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in used_names:
            used_names.add(name)
            break

    # Age distribution: mostly 22-30 with some young and old
    age_weights = list(range(19, 37))
    age_probs = [1, 2, 3, 5, 7, 8, 9, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1]
    age = random.choices(age_weights, weights=age_probs, k=1)[0]

    # Younger players have lower current stats but higher potential
    age_modifier = 0
    if age < 22:
        age_modifier = -10
    elif age < 24:
        age_modifier = -5
    elif age > 32:
        age_modifier = -3
    elif age > 34:
        age_modifier = -8

    stats = {}
    for stat, (low, high) in profile.items():
        stats[stat] = generate_stat(low, high, rep_mod + age_modifier)

    # Potential based on age
    if age < 23:
        potential = random.randint(65, 95)
    elif age < 27:
        potential = random.randint(55, 85)
    else:
        potential = max(stats.values())  # Potential = current peak for older players

    # Wage based on overall quality
    avg_stat = sum(stats.values()) / len(stats)
    base_wage = int(1000 + (avg_stat / 99) * 12000)
    wage = base_wage + random.randint(-500, 500)

    # Secondary positions (50% chance for each possible secondary)
    sec_pos = [p for p in SECONDARY_POSITIONS.get(position, [])
               if random.random() > 0.5]

    # Nationality
    nationality = random.choices(NATIONALITY_NAMES, weights=NATIONALITY_WEIGHTS, k=1)[0]

    # Height and weight from position profile
    body = BODY_PROFILES[POSITION_TO_PROFILE[position]]
    height = random.randint(*body['height'])
    weight = random.randint(*body['weight'])

    return {
        'name': name,
        'age': age,
        'position': position,
        'secondary_positions': sec_pos,
        'nationality': nationality,
        'height': height,
        'weight': weight,
        'potential': potential,
        'form': random.randint(40, 75),
        'morale': random.randint(55, 80),
        'fitness': random.randint(85, 100),
        'wage': wage,
        'contract_end': random.randint(1, 4),
        **stats,
    }


def generate_squad(team_reputation, team_name=None):
    """Generate a full squad of ~30 players."""
    used_names = set()
    players = []

    # Track positions filled by real players
    real_position_counts = {}
    real_players = REAL_PLAYERS.get(team_name, [])
    for rp in real_players:
        players.append(rp)
        used_names.add(rp['name'])
        pos = rp['position']
        real_position_counts[pos] = real_position_counts.get(pos, 0) + 1

    for position, count in SQUAD_TEMPLATE.items():
        already_filled = real_position_counts.get(position, 0)
        remaining = count - already_filled
        for i in range(remaining):
            player = generate_player(position, team_reputation, used_names)
            # First player at each position is generally better (starter)
            if i == 0 and already_filled == 0:
                for stat in ALL_STATS:
                    if stat in player:
                        player[stat] = min(99, player[stat] + random.randint(2, 6))
            players.append(player)

    return players


def generate_all_data():
    """Generate all teams and players."""
    data_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(data_dir, 'teams.json'), 'r') as f:
        teams = json.load(f)

    all_players = {}
    for team in teams:
        squad = generate_squad(team['reputation'], team['name'])
        all_players[team['name']] = squad

    with open(os.path.join(data_dir, 'players.json'), 'w') as f:
        json.dump(all_players, f, indent=2)

    print(f"Generated {sum(len(s) for s in all_players.values())} players for {len(teams)} teams")
    return all_players


if __name__ == '__main__':
    random.seed(42)
    generate_all_data()
