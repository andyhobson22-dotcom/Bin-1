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

# The 35 stats grouped for display
STAT_GROUPS = {
    'Physical': [
        ('stopping_power', 'Stopping Power'),
        ('explosiveness', 'Explosiveness'),
        ('leg_drive', 'Leg Drive'),
        ('pace', 'Pace'),
        ('acceleration', 'Acceleration'),
        ('agility', 'Agility'),
        ('strength', 'Strength'),
    ],
    'Mental': [
        ('aggression', 'Aggression'),
        ('composure', 'Composure'),
        ('concentration', 'Concentration'),
        ('awareness', 'Awareness'),
        ('running_lines', 'Running Lines'),
        ('discipline', 'Discipline'),
        ('tenacity', 'Tenacity'),
        ('scanning', 'Scanning'),
        ('positioning', 'Positioning'),
    ],
    'Technical': [
        ('long_passing', 'Long Passing'),
        ('handling', 'Handling'),
        ('high_ball', 'High Ball'),
        ('offload', 'Offload'),
        ('tackling', 'Tackling'),
        ('rucking', 'Rucking'),
        ('mauling', 'Mauling'),
        ('jackling', 'Jackling'),
        ('grubber', 'Grubber'),
        ('chipping', 'Chipping'),
        ('box_kicking', 'Box Kicking'),
        ('stepping', 'Stepping'),
        ('short_passing', 'Short Passing'),
    ],
    'Set Piece': [
        ('goal_kicking', 'Goal Kicking'),
        ('scrum_drive', 'Scrum Drive'),
        ('scrum_tech', 'Scrum Tech'),
        ('touch_finder', 'Touch Finder'),
        ('jumping', 'Jumping'),
        ('lifting', 'Lifting'),
    ],
}

# Which stats matter most for each position (weights for overall rating)
POSITION_WEIGHTS = {
    'loosehead_prop': {
        'scrum_drive': 3, 'scrum_tech': 3, 'strength': 3, 'leg_drive': 2,
        'tackling': 2, 'mauling': 2, 'stopping_power': 1,
    },
    'hooker': {
        'scrum_drive': 2, 'jumping': 2, 'lifting': 2, 'strength': 2,
        'tackling': 2, 'handling': 2, 'short_passing': 1,
    },
    'tighthead_prop': {
        'scrum_drive': 3, 'scrum_tech': 3, 'strength': 3, 'leg_drive': 2,
        'tackling': 2, 'mauling': 2, 'stopping_power': 1,
    },
    'lock_4': {
        'jumping': 3, 'lifting': 2, 'strength': 2, 'scrum_drive': 2,
        'tackling': 2, 'leg_drive': 1, 'mauling': 1,
    },
    'lock_5': {
        'jumping': 3, 'lifting': 2, 'strength': 2, 'scrum_drive': 2,
        'tackling': 2, 'leg_drive': 1, 'mauling': 1,
    },
    'blindside_flanker': {
        'tackling': 3, 'strength': 2, 'tenacity': 2, 'rucking': 2,
        'pace': 1, 'handling': 1, 'jackling': 1, 'mauling': 1,
    },
    'openside_flanker': {
        'tackling': 3, 'jackling': 3, 'tenacity': 2, 'pace': 2,
        'rucking': 2, 'awareness': 2, 'explosiveness': 1,
    },
    'number_eight': {
        'strength': 3, 'tackling': 2, 'handling': 2, 'rucking': 2,
        'pace': 1, 'leg_drive': 1, 'awareness': 1, 'offload': 1,
    },
    'scrum_half': {
        'short_passing': 3, 'long_passing': 2, 'pace': 2, 'scanning': 2,
        'awareness': 2, 'box_kicking': 1, 'tackling': 1, 'acceleration': 1,
    },
    'fly_half': {
        'goal_kicking': 3, 'long_passing': 3, 'scanning': 3, 'awareness': 2,
        'composure': 2, 'touch_finder': 1, 'short_passing': 1,
    },
    'inside_centre': {
        'tackling': 2, 'strength': 2, 'short_passing': 2, 'pace': 1,
        'handling': 1, 'awareness': 2, 'stepping': 1, 'stopping_power': 1,
    },
    'outside_centre': {
        'pace': 2, 'short_passing': 2, 'tackling': 2, 'handling': 1,
        'agility': 2, 'awareness': 1, 'stepping': 1, 'running_lines': 1,
    },
    'left_wing': {
        'pace': 3, 'acceleration': 2, 'agility': 2, 'handling': 2,
        'stepping': 2, 'high_ball': 1, 'tackling': 1,
    },
    'right_wing': {
        'pace': 3, 'acceleration': 2, 'agility': 2, 'handling': 2,
        'stepping': 2, 'high_ball': 1, 'tackling': 1,
    },
    'fullback': {
        'high_ball': 2, 'pace': 2, 'handling': 2, 'tackling': 1,
        'awareness': 2, 'agility': 1, 'goal_kicking': 1, 'touch_finder': 1,
        'positioning': 1,
    },
}

# ── Engine Compatibility Layer ────────────────────────────────────────
# Maps old stat names used by the match engine to averages of new stats.
# This lets the entire engine work without modification.

STAT_COMPAT = {
    'speed': ('pace', 'acceleration'),
    'stamina': ('leg_drive', 'tenacity'),
    'passing': ('short_passing', 'long_passing'),
    'kicking': ('goal_kicking', 'touch_finder', 'grubber', 'box_kicking'),
    'kick_chase': ('pace', 'explosiveness', 'tenacity'),
    'scrummaging': ('scrum_drive', 'scrum_tech'),
    'lineout': ('jumping', 'lifting'),
    'game_sense': ('awareness', 'scanning', 'positioning'),
    'leadership': ('composure', 'awareness'),
    # These map 1:1 (same name in old and new)
    'tackling': ('tackling',),
    'handling': ('handling',),
    'strength': ('strength',),
    'agility': ('agility',),
    'discipline': ('discipline',),
}


def compat_stat(player, old_stat, default=50):
    """Get an old-style stat value from a player using the new stat system.

    If the player already has the old stat (e.g. from a legacy DB), use it.
    Otherwise compute it as the average of the mapped new stats.
    """
    # If the old stat exists directly on the player, use it
    if old_stat in STAT_COMPAT:
        new_stats = STAT_COMPAT[old_stat]
        vals = [player.get(s, default) for s in new_stats]
        return int(sum(vals) / len(vals))
    return player.get(old_stat, default)


def inject_compat_stats(player):
    """Add computed old-style stats to a player dict for engine compatibility.

    Call this before passing players to the match engine.
    """
    for old_stat, new_stats in STAT_COMPAT.items():
        if old_stat not in player or old_stat in ('tackling', 'handling',
                                                    'strength', 'agility',
                                                    'discipline'):
            vals = [player.get(s, 50) for s in new_stats]
            player[old_stat] = int(sum(vals) / len(vals))
    return player


# ── Core Functions ────────────────────────────────────────────────────

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


def get_position_ratings(player):
    """Get ratings for primary and all secondary positions."""
    ratings = {}
    primary = player.get('position', '')
    ratings[primary] = get_position_rating(player, primary)

    secondary = json.loads(player.get('secondary_positions', '[]'))
    for pos in secondary:
        ratings[pos] = get_position_rating(player, pos)

    return ratings
