import json
from database import get_db

POSITIONS = {
    'loosehead_prop': {'number': 1, 'name': 'Loosehead Prop', 'group': 'forward'},
    'hooker': {'number': 2, 'name': 'Hooker', 'group': 'forward'},
    'tighthead_prop': {'number': 3, 'name': 'Tighthead Prop', 'group': 'forward'},
    'lock_4': {'number': 4, 'name': 'Lock', 'group': 'forward'},
    'lock_5': {'number': 5, 'name': 'Lock', 'group': 'forward'},
    'blindside_flanker': {'number': 6, 'name': 'Blindside Flanker', 'group': 'forward'},
    'openside_flanker': {'number': 7, 'name': 'Openside Flanker', 'group': 'forward'},
    'number_eight': {'number': 8, 'name': 'Number Eight', 'group': 'forward'},
    'scrum_half': {'number': 9, 'name': 'Scrum Half', 'group': 'back'},
    'fly_half': {'number': 10, 'name': 'Fly Half', 'group': 'back'},
    'left_wing': {'number': 11, 'name': 'Left Wing', 'group': 'back'},
    'inside_centre': {'number': 12, 'name': 'Inside Centre', 'group': 'back'},
    'outside_centre': {'number': 13, 'name': 'Outside Centre', 'group': 'back'},
    'right_wing': {'number': 14, 'name': 'Right Wing', 'group': 'back'},
    'fullback': {'number': 15, 'name': 'Fullback', 'group': 'back'},
}

# Which stats matter most for each position (weights for overall rating)
POSITION_WEIGHTS = {
    'loosehead_prop': {'scrummaging': 3, 'strength': 3, 'tackling': 2, 'stamina': 1, 'handling': 1},
    'hooker': {'scrummaging': 2, 'lineout': 3, 'strength': 2, 'tackling': 2, 'handling': 1},
    'tighthead_prop': {'scrummaging': 3, 'strength': 3, 'tackling': 2, 'stamina': 1, 'handling': 1},
    'lock_4': {'lineout': 3, 'strength': 2, 'scrummaging': 2, 'tackling': 2, 'stamina': 1},
    'lock_5': {'lineout': 3, 'strength': 2, 'scrummaging': 2, 'tackling': 2, 'stamina': 1},
    'blindside_flanker': {'tackling': 3, 'strength': 2, 'stamina': 2, 'speed': 1, 'handling': 1, 'lineout': 1},
    'openside_flanker': {'tackling': 3, 'speed': 2, 'stamina': 2, 'handling': 1, 'game_sense': 2},
    'number_eight': {'strength': 3, 'tackling': 2, 'handling': 2, 'speed': 1, 'stamina': 1, 'game_sense': 1},
    'scrum_half': {'passing': 3, 'speed': 2, 'game_sense': 2, 'kicking': 1, 'tackling': 1, 'handling': 1},
    'fly_half': {'kicking': 3, 'passing': 3, 'game_sense': 3, 'handling': 1, 'tackling': 1},
    'inside_centre': {'tackling': 2, 'strength': 2, 'passing': 2, 'speed': 1, 'handling': 1, 'game_sense': 2},
    'outside_centre': {'speed': 2, 'passing': 2, 'tackling': 2, 'handling': 1, 'agility': 2, 'game_sense': 1},
    'left_wing': {'speed': 3, 'agility': 2, 'handling': 2, 'tackling': 1, 'kicking': 1, 'kick_chase': 2},
    'right_wing': {'speed': 3, 'agility': 2, 'handling': 2, 'tackling': 1, 'kicking': 1, 'kick_chase': 2},
    'fullback': {'kicking': 2, 'speed': 2, 'handling': 2, 'tackling': 1, 'game_sense': 2, 'agility': 1, 'kick_chase': 1},
}


def get_player(player_id):
    db = get_db()
    player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    db.close()
    return dict(player) if player else None


def get_team_players(team_id):
    db = get_db()
    players = db.execute(
        "SELECT * FROM players WHERE team_id = ? ORDER BY position, name",
        (team_id,)
    ).fetchall()
    db.close()
    return [dict(p) for p in players]


def get_position_rating(player, position):
    """Calculate how well a player performs in a given position."""
    weights = POSITION_WEIGHTS.get(position, {})
    if not weights:
        return 0
    total_weight = sum(weights.values())
    score = sum(player.get(stat, 50) * w for stat, w in weights.items())
    base_rating = score / total_weight

    # Penalty for playing out of position
    primary = player.get('position', '')
    if primary == position:
        return int(base_rating)
    secondary = json.loads(player.get('secondary_positions', '[]'))
    if position in secondary:
        return int(base_rating * 0.9)
    # Same group (forward/back) = less penalty
    if POSITIONS.get(primary, {}).get('group') == POSITIONS.get(position, {}).get('group'):
        return int(base_rating * 0.75)
    return int(base_rating * 0.5)


def get_overall_rating(player):
    """Overall rating in the player's primary position."""
    return get_position_rating(player, player.get('position', ''))
