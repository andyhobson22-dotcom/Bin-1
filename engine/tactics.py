"""Tactical options for rugby match simulation.

Includes team strategy (attacking style, defence, etc.) and
granular with-ball instructions (kick tendency, offload frequency, etc.).
Also provides a style-player fit calculator that rewards managers
for choosing tactics that suit their squad.
"""

# ── Team Strategy ──────────────────────────────────────────────────

ATTACKING_STYLES = {
    'expansive': {
        'name': 'Expansive',
        'description': 'Wide, running rugby with lots of passing and offloads',
        'modifiers': {'passing': 10, 'handling': 5, 'speed': 5, 'tackling': -5},
        # Stats the squad should be good at for this to work
        'fit_stats': {'passing': 0.3, 'handling': 0.25, 'speed': 0.25, 'agility': 0.2},
    },
    'structured': {
        'name': 'Structured',
        'description': 'Forward-dominated, pick-and-go, keep it tight',
        'modifiers': {'strength': 10, 'scrummaging': 5, 'tackling': 5, 'speed': -5},
        'fit_stats': {'strength': 0.35, 'scrummaging': 0.25, 'tackling': 0.2, 'stamina': 0.2},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Mix of forward power and back-line play',
        'modifiers': {},
        'fit_stats': {},  # Always a neutral fit
    },
}

KICKING_GAMES = {
    'kick_heavy': {
        'name': 'Kick Heavy',
        'description': 'Contest the air, kick for territory and pressure',
        'modifiers': {'kicking': 10, 'handling': -5},
        'fit_stats': {'kicking': 0.5, 'game_sense': 0.3, 'speed': 0.2},
    },
    'run_first': {
        'name': 'Run First',
        'description': 'Keep ball in hand, run from deep',
        'modifiers': {'speed': 5, 'handling': 5, 'kicking': -10},
        'fit_stats': {'speed': 0.3, 'handling': 0.3, 'agility': 0.2, 'passing': 0.2},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Mix of kicking and running',
        'modifiers': {},
        'fit_stats': {},
    },
}

DEFENSIVE_STYLES = {
    'rush': {
        'name': 'Rush Defence',
        'description': 'Aggressive rush off the line to close space',
        'modifiers': {'tackling': 10, 'speed': 5, 'discipline': -10},
        'fit_stats': {'tackling': 0.3, 'speed': 0.3, 'stamina': 0.2, 'discipline': 0.2},
    },
    'drift': {
        'name': 'Drift Defence',
        'description': 'Patient, drift across the field to cover space',
        'modifiers': {'game_sense': 5, 'discipline': 5},
        'fit_stats': {'game_sense': 0.4, 'tackling': 0.3, 'discipline': 0.3},
    },
    'blitz': {
        'name': 'Blitz Defence',
        'description': 'Target the playmaker, high risk high reward',
        'modifiers': {'tackling': 15, 'discipline': -15},
        'fit_stats': {'tackling': 0.35, 'speed': 0.25, 'agility': 0.2, 'discipline': 0.2},
    },
}

SET_PIECE_APPROACHES = {
    'maul_focused': {
        'name': 'Maul Focused',
        'description': 'Drive the maul from lineout, use forward power',
        'modifiers': {'strength': 10, 'lineout': 5},
        'fit_stats': {'strength': 0.35, 'lineout': 0.35, 'scrummaging': 0.15, 'stamina': 0.15},
    },
    'quick_ball': {
        'name': 'Quick Ball',
        'description': 'Win it fast at the set piece and get it to the backs',
        'modifiers': {'passing': 5, 'speed': 5},
        'fit_stats': {'passing': 0.3, 'speed': 0.3, 'handling': 0.2, 'agility': 0.2},
    },
    'conservative': {
        'name': 'Conservative',
        'description': "Secure ball, don't take risks at the set piece",
        'modifiers': {'scrummaging': 5, 'lineout': 5, 'handling': -5},
        'fit_stats': {'scrummaging': 0.35, 'lineout': 0.35, 'strength': 0.3},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Standard set piece approach',
        'modifiers': {},
        'fit_stats': {},
    },
}

TEMPO_OPTIONS = {
    'high': {
        'name': 'High Tempo',
        'description': 'Play fast, quick rucks, tire the opposition',
        'modifiers': {'speed': 5, 'stamina': -10},
        'fit_stats': {'stamina': 0.4, 'speed': 0.3, 'handling': 0.15, 'agility': 0.15},
    },
    'normal': {
        'name': 'Normal Tempo',
        'description': 'Standard game speed',
        'modifiers': {},
        'fit_stats': {},
    },
    'control': {
        'name': 'Control Tempo',
        'description': 'Slow the game down, manage territory',
        'modifiers': {'game_sense': 5, 'kicking': 5, 'speed': -5},
        'fit_stats': {'game_sense': 0.35, 'kicking': 0.35, 'discipline': 0.3},
    },
}


# ── With-Ball Instructions ─────────────────────────────────────────

KICK_TENDENCY = {
    'never': {
        'name': 'Never Kick',
        'description': 'Always keep ball in hand, never kick in open play',
        'kick_chance_mod': -0.8,  # Massive reduction to kick probability
    },
    'rarely': {
        'name': 'Rarely Kick',
        'description': 'Only kick when pinned deep in own territory',
        'kick_chance_mod': -0.4,
    },
    'sometimes': {
        'name': 'Sometimes Kick',
        'description': 'Kick when tactically appropriate',
        'kick_chance_mod': 0.0,
    },
    'often': {
        'name': 'Often Kick',
        'description': 'Kick regularly to contest territory',
        'kick_chance_mod': 0.3,
    },
    'always': {
        'name': 'Always Kick',
        'description': 'Kick at every opportunity to put pressure on',
        'kick_chance_mod': 0.6,
    },
}

KICK_TYPE = {
    'box_kick': {
        'name': 'Box Kick',
        'description': 'Scrum-half box kick to contest in the air',
        'primary_kicker': 'scrum_half',
        'contest_air': True,
        'territory_gain': 1,  # zones gained on success
        'turnover_risk': 0.15,
    },
    'up_and_under': {
        'name': 'Up and Under',
        'description': 'High ball to put pressure on the catcher',
        'primary_kicker': 'fly_half',
        'contest_air': True,
        'territory_gain': 1,
        'turnover_risk': 0.10,
    },
    'grubber': {
        'name': 'Grubber',
        'description': 'Low kick along the ground behind the defence',
        'primary_kicker': 'fly_half',
        'contest_air': False,
        'territory_gain': 2,
        'turnover_risk': 0.25,
    },
    'touch_finder': {
        'name': 'Touch Finder',
        'description': 'Kick to touch for a lineout — safe territory gain',
        'primary_kicker': 'fly_half',
        'contest_air': False,
        'territory_gain': 2,
        'turnover_risk': 0.05,
    },
    'cross_field': {
        'name': 'Cross-Field Kick',
        'description': 'Ambitious kick across the field to an unmarked winger',
        'primary_kicker': 'fly_half',
        'contest_air': True,
        'territory_gain': 1,
        'turnover_risk': 0.30,
    },
}

KICK_ZONES = {
    'own_22': {
        'name': 'Own 22 Only',
        'description': 'Only kick when inside your own 22',
        'active_zones': [0],
    },
    'own_half': {
        'name': 'Own Half',
        'description': 'Kick when anywhere in your own half',
        'active_zones': [0, 1],
    },
    'anywhere': {
        'name': 'Anywhere',
        'description': 'Kick from anywhere on the pitch',
        'active_zones': [0, 1, 2, 3, 4],
    },
    'deep_only': {
        'name': 'Deep Territory',
        'description': 'Kick from deep and from midfield',
        'active_zones': [0, 1, 2],
    },
}

PLAY_OFF = {
    'fly_half': {
        'name': 'Fly Half (10)',
        'description': 'Primary playmaker — classic first receiver',
        'key_position': 'fly_half',
        'stat_weights': {'passing': 0.3, 'kicking': 0.2, 'game_sense': 0.3, 'handling': 0.2},
    },
    'inside_centre': {
        'name': 'Inside Centre (12)',
        'description': 'Second playmaker — crash ball or distribute',
        'key_position': 'inside_centre',
        'stat_weights': {'passing': 0.25, 'strength': 0.25, 'game_sense': 0.25, 'handling': 0.25},
    },
    'number_eight': {
        'name': 'Number Eight (8)',
        'description': 'Ball-carrying forward — pick and go from the base',
        'key_position': 'number_eight',
        'stat_weights': {'strength': 0.3, 'handling': 0.25, 'speed': 0.2, 'stamina': 0.25},
    },
    'scrum_half': {
        'name': 'Scrum Half (9)',
        'description': 'Snipe around the ruck — quick, direct play',
        'key_position': 'scrum_half',
        'stat_weights': {'passing': 0.3, 'speed': 0.3, 'game_sense': 0.2, 'agility': 0.2},
    },
    'fullback': {
        'name': 'Fullback (15)',
        'description': 'Insert fullback into the line as an extra attacker',
        'key_position': 'fullback',
        'stat_weights': {'speed': 0.25, 'handling': 0.25, 'game_sense': 0.25, 'agility': 0.25},
    },
}

OFFLOAD_FREQUENCY = {
    'low': {
        'name': 'Keep It Tight',
        'description': 'Rarely offload — secure the ruck, recycle safely',
        'offload_chance': 0.05,
        'turnover_risk_mod': -0.05,  # Safer
        'big_play_mod': -0.05,  # Fewer highlight moments
    },
    'medium': {
        'name': 'Normal',
        'description': 'Offload when the opportunity is on',
        'offload_chance': 0.15,
        'turnover_risk_mod': 0.0,
        'big_play_mod': 0.0,
    },
    'high': {
        'name': 'Offload Everything',
        'description': 'Look for the offload in every contact — high risk, high reward',
        'offload_chance': 0.30,
        'turnover_risk_mod': 0.10,  # More turnovers
        'big_play_mod': 0.10,  # More line breaks
    },
}

RUCK_SUPPORT = {
    'slow': {
        'name': 'Slow Ruck',
        'description': 'Commit fewer bodies — conserve energy but slower ball',
        'ruck_speed_mod': -0.15,
        'stamina_save': 0.3,  # 30% less fatigue drain
        'turnover_risk_mod': 0.08,
    },
    'normal': {
        'name': 'Normal Ruck',
        'description': 'Standard ruck commitment',
        'ruck_speed_mod': 0.0,
        'stamina_save': 0.0,
        'turnover_risk_mod': 0.0,
    },
    'quick': {
        'name': 'Quick Ruck',
        'description': 'Flood the breakdown — fast ball but tiring',
        'ruck_speed_mod': 0.15,
        'stamina_save': -0.3,  # 30% more fatigue drain
        'turnover_risk_mod': -0.06,
    },
}


# ── Default Tactics ────────────────────────────────────────────────

def default_tactics():
    """Full default tactical setup."""
    return {
        # Strategy
        'attacking_style': 'balanced',
        'kicking_game': 'balanced',
        'defensive_style': 'drift',
        'set_piece': 'balanced',
        'tempo': 'normal',
        # With-ball instructions
        'kick_tendency': 'sometimes',
        'kick_type': 'touch_finder',
        'kick_zones': 'own_half',
        'play_off': 'fly_half',
        'offload_frequency': 'medium',
        'ruck_support': 'normal',
    }


# ── Style-Player Fit Calculator ───────────────────────────────────

def _avg_stat(players, stat):
    """Average of a stat across players."""
    if not players:
        return 50
    return sum(p.get(stat, 50) for p in players) / len(players)


def calculate_style_fit(players, tactics):
    """Calculate how well the chosen tactics fit the squad.

    Returns a float from 0.0 (terrible fit) to 1.0 (perfect fit).
    A 'balanced' / neutral choice always returns 0.5 (no bonus, no penalty).

    The fit is a weighted average across all tactical dimensions.
    """
    if not players:
        return 0.5

    STRATEGY_CONFIGS = {
        'attacking_style': ATTACKING_STYLES,
        'kicking_game': KICKING_GAMES,
        'defensive_style': DEFENSIVE_STYLES,
        'set_piece': SET_PIECE_APPROACHES,
        'tempo': TEMPO_OPTIONS,
    }

    fit_scores = []

    for category, options in STRATEGY_CONFIGS.items():
        choice = tactics.get(category, 'balanced')
        option = options.get(choice, {})
        fit_stats = option.get('fit_stats', {})

        if not fit_stats:
            # Neutral choice — 0.5
            fit_scores.append(0.5)
            continue

        # Weighted average of relevant stats, normalised to 0-1
        weighted_sum = 0.0
        for stat, weight in fit_stats.items():
            avg = _avg_stat(players, stat)
            # Normalise: 40 = poor (0.0), 70 = good (1.0), 90+ = excellent (capped 1.0)
            normalised = max(0.0, min(1.0, (avg - 40) / 50))
            weighted_sum += normalised * weight

        fit_scores.append(weighted_sum)

    # Also factor in the "play off" choice — is that player actually good?
    play_off_choice = tactics.get('play_off', 'fly_half')
    play_off_cfg = PLAY_OFF.get(play_off_choice, {})
    key_pos = play_off_cfg.get('key_position', 'fly_half')
    stat_weights = play_off_cfg.get('stat_weights', {})

    # Find the player in that position
    key_player = None
    for p in players:
        if p.get('position') == key_pos:
            key_player = p
            break

    if key_player and stat_weights:
        player_fit = 0.0
        for stat, weight in stat_weights.items():
            val = key_player.get(stat, 50)
            normalised = max(0.0, min(1.0, (val - 40) / 50))
            player_fit += normalised * weight
        fit_scores.append(player_fit)
    else:
        fit_scores.append(0.5)

    return sum(fit_scores) / len(fit_scores) if fit_scores else 0.5


def get_fit_description(fit_score):
    """Human-readable description of the fit score."""
    if fit_score >= 0.8:
        return "Excellent"
    elif fit_score >= 0.65:
        return "Good"
    elif fit_score >= 0.5:
        return "Average"
    elif fit_score >= 0.35:
        return "Poor"
    else:
        return "Terrible"


# ── Tactical Modifier Application ─────────────────────────────────

def apply_tactical_modifiers(base_stats, tactics):
    """Apply tactical modifiers to a dict of average stats.

    Returns a new dict with modified values.
    """
    stats = dict(base_stats)

    STRATEGY_CONFIGS = {
        'attacking_style': ATTACKING_STYLES,
        'kicking_game': KICKING_GAMES,
        'defensive_style': DEFENSIVE_STYLES,
        'set_piece': SET_PIECE_APPROACHES,
        'tempo': TEMPO_OPTIONS,
    }

    for category, options in STRATEGY_CONFIGS.items():
        choice = tactics.get(category, 'balanced')
        option = options.get(choice, {})
        for stat, mod in option.get('modifiers', {}).items():
            stats[stat] = stats.get(stat, 50) + mod

    return stats


# ── Public API ─────────────────────────────────────────────────────

def get_all_tactical_options():
    """Return all tactical options for the frontend."""
    return {
        'strategy': {
            'attacking_style': ATTACKING_STYLES,
            'kicking_game': KICKING_GAMES,
            'defensive_style': DEFENSIVE_STYLES,
            'set_piece': SET_PIECE_APPROACHES,
            'tempo': TEMPO_OPTIONS,
        },
        'with_ball': {
            'kick_tendency': KICK_TENDENCY,
            'kick_type': KICK_TYPE,
            'kick_zones': KICK_ZONES,
            'play_off': PLAY_OFF,
            'offload_frequency': OFFLOAD_FREQUENCY,
            'ruck_support': RUCK_SUPPORT,
        },
    }
