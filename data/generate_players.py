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

# Base stat profiles by position group
STAT_PROFILES = {
    'loosehead_prop': {
        'speed': (30, 50), 'strength': (70, 95), 'stamina': (50, 75),
        'agility': (25, 50), 'passing': (20, 45), 'kicking': (15, 35),
        'tackling': (55, 80), 'handling': (30, 55), 'scrummaging': (70, 95),
        'lineout': (15, 35), 'game_sense': (35, 60), 'leadership': (30, 70),
        'discipline': (40, 75), 'kick_chase': (15, 35),
    },
    'hooker': {
        'speed': (35, 55), 'strength': (65, 90), 'stamina': (55, 80),
        'agility': (35, 55), 'passing': (30, 55), 'kicking': (15, 35),
        'tackling': (60, 85), 'handling': (40, 65), 'scrummaging': (60, 85),
        'lineout': (65, 95), 'game_sense': (40, 65), 'leadership': (35, 75),
        'discipline': (45, 75), 'kick_chase': (30, 55),
    },
    'tighthead_prop': {
        'speed': (25, 45), 'strength': (75, 99), 'stamina': (50, 75),
        'agility': (20, 45), 'passing': (15, 40), 'kicking': (10, 30),
        'tackling': (55, 80), 'handling': (25, 50), 'scrummaging': (75, 99),
        'lineout': (15, 35), 'game_sense': (30, 55), 'leadership': (25, 65),
        'discipline': (40, 70), 'kick_chase': (15, 30),
    },
    'lock': {
        'speed': (35, 55), 'strength': (65, 90), 'stamina': (55, 80),
        'agility': (30, 50), 'passing': (25, 50), 'kicking': (15, 35),
        'tackling': (55, 80), 'handling': (35, 60), 'scrummaging': (55, 80),
        'lineout': (70, 95), 'game_sense': (40, 65), 'leadership': (40, 80),
        'discipline': (45, 75), 'kick_chase': (30, 55),
    },
    'flanker': {
        'speed': (50, 75), 'strength': (60, 85), 'stamina': (65, 90),
        'agility': (45, 70), 'passing': (35, 60), 'kicking': (15, 40),
        'tackling': (70, 95), 'handling': (40, 65), 'scrummaging': (45, 70),
        'lineout': (40, 70), 'game_sense': (50, 75), 'leadership': (40, 75),
        'discipline': (45, 75), 'kick_chase': (45, 75),
    },
    'number_eight': {
        'speed': (45, 70), 'strength': (65, 90), 'stamina': (60, 85),
        'agility': (40, 65), 'passing': (35, 60), 'kicking': (15, 40),
        'tackling': (60, 85), 'handling': (45, 70), 'scrummaging': (50, 75),
        'lineout': (35, 60), 'game_sense': (50, 75), 'leadership': (45, 80),
        'discipline': (45, 75), 'kick_chase': (40, 65),
    },
    'scrum_half': {
        'speed': (60, 85), 'strength': (30, 55), 'stamina': (60, 85),
        'agility': (60, 85), 'passing': (70, 95), 'kicking': (45, 75),
        'tackling': (40, 65), 'handling': (60, 85), 'scrummaging': (15, 30),
        'lineout': (15, 30), 'game_sense': (60, 85), 'leadership': (45, 80),
        'discipline': (50, 80), 'kick_chase': (40, 65),
    },
    'fly_half': {
        'speed': (50, 75), 'strength': (30, 55), 'stamina': (55, 80),
        'agility': (55, 80), 'passing': (70, 95), 'kicking': (70, 95),
        'tackling': (35, 60), 'handling': (60, 85), 'scrummaging': (10, 25),
        'lineout': (10, 25), 'game_sense': (70, 95), 'leadership': (50, 85),
        'discipline': (55, 85), 'kick_chase': (30, 55),
    },
    'centre': {
        'speed': (55, 80), 'strength': (50, 75), 'stamina': (55, 80),
        'agility': (55, 80), 'passing': (50, 80), 'kicking': (35, 65),
        'tackling': (55, 80), 'handling': (50, 75), 'scrummaging': (10, 25),
        'lineout': (10, 25), 'game_sense': (55, 80), 'leadership': (35, 70),
        'discipline': (50, 80), 'kick_chase': (40, 70),
    },
    'wing': {
        'speed': (70, 99), 'strength': (40, 65), 'stamina': (55, 80),
        'agility': (65, 90), 'passing': (35, 60), 'kicking': (30, 60),
        'tackling': (35, 65), 'handling': (50, 80), 'scrummaging': (10, 20),
        'lineout': (10, 25), 'game_sense': (45, 70), 'leadership': (25, 55),
        'discipline': (50, 80), 'kick_chase': (60, 95),
    },
    'fullback': {
        'speed': (60, 85), 'strength': (35, 60), 'stamina': (55, 80),
        'agility': (60, 85), 'passing': (45, 75), 'kicking': (60, 90),
        'tackling': (40, 70), 'handling': (55, 85), 'scrummaging': (10, 20),
        'lineout': (10, 25), 'game_sense': (60, 85), 'leadership': (35, 65),
        'discipline': (55, 85), 'kick_chase': (50, 80),
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

    return {
        'name': name,
        'age': age,
        'position': position,
        'secondary_positions': sec_pos,
        'potential': potential,
        'form': random.randint(40, 75),
        'morale': random.randint(55, 80),
        'fitness': random.randint(85, 100),
        'wage': wage,
        'contract_end': random.randint(1, 4),
        **stats,
    }


def generate_squad(team_reputation):
    """Generate a full squad of ~30 players."""
    used_names = set()
    players = []

    for position, count in SQUAD_TEMPLATE.items():
        for i in range(count):
            player = generate_player(position, team_reputation, used_names)
            # First player at each position is generally better (starter)
            if i == 0:
                for stat in ['speed', 'strength', 'stamina', 'agility', 'passing',
                             'kicking', 'tackling', 'handling', 'scrummaging',
                             'lineout', 'game_sense', 'kick_chase']:
                    player[stat] = min(99, player[stat] + random.randint(3, 8))
            players.append(player)

    return players


def generate_all_data():
    """Generate all teams and players."""
    data_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(data_dir, 'teams.json'), 'r') as f:
        teams = json.load(f)

    all_players = {}
    for team in teams:
        squad = generate_squad(team['reputation'])
        all_players[team['name']] = squad

    with open(os.path.join(data_dir, 'players.json'), 'w') as f:
        json.dump(all_players, f, indent=2)

    print(f"Generated {sum(len(s) for s in all_players.values())} players for {len(teams)} teams")
    return all_players


if __name__ == '__main__':
    random.seed(42)
    generate_all_data()
