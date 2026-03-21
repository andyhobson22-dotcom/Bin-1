"""Tactical options for rugby match simulation."""

ATTACKING_STYLES = {
    'expansive': {
        'name': 'Expansive',
        'description': 'Wide, running rugby with lots of passing and offloads',
        'modifiers': {'passing': 10, 'handling': 5, 'speed': 5, 'tackling': -5},
    },
    'structured': {
        'name': 'Structured',
        'description': 'Forward-dominated, pick-and-go, keep it tight',
        'modifiers': {'strength': 10, 'scrummaging': 5, 'tackling': 5, 'speed': -5},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Mix of forward power and back-line play',
        'modifiers': {},
    },
}

KICKING_GAMES = {
    'kick_heavy': {
        'name': 'Kick Heavy',
        'description': 'Contest the air, kick for territory and pressure',
        'modifiers': {'kicking': 10, 'handling': -5},
    },
    'run_first': {
        'name': 'Run First',
        'description': 'Keep ball in hand, run from deep',
        'modifiers': {'speed': 5, 'handling': 5, 'kicking': -10},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Mix of kicking and running',
        'modifiers': {},
    },
}

DEFENSIVE_STYLES = {
    'rush': {
        'name': 'Rush Defence',
        'description': 'Aggressive rush off the line to close space',
        'modifiers': {'tackling': 10, 'speed': 5, 'discipline': -10},
    },
    'drift': {
        'name': 'Drift Defence',
        'description': 'Patient, drift across the field to cover space',
        'modifiers': {'game_sense': 5, 'discipline': 5},
    },
    'blitz': {
        'name': 'Blitz Defence',
        'description': 'Target the playmaker, high risk high reward',
        'modifiers': {'tackling': 15, 'discipline': -15},
    },
}

SET_PIECE_APPROACHES = {
    'maul_focused': {
        'name': 'Maul Focused',
        'description': 'Drive the maul from lineout, use forward power',
        'modifiers': {'strength': 10, 'lineout': 5},
    },
    'quick_ball': {
        'name': 'Quick Ball',
        'description': 'Win it fast at the set piece and get it to the backs',
        'modifiers': {'passing': 5, 'speed': 5},
    },
    'conservative': {
        'name': 'Conservative',
        'description': 'Secure ball, don\'t take risks at the set piece',
        'modifiers': {'scrummaging': 5, 'lineout': 5, 'handling': -5},
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'Standard set piece approach',
        'modifiers': {},
    },
}

TEMPO_OPTIONS = {
    'high': {
        'name': 'High Tempo',
        'description': 'Play fast, quick rucks, tire the opposition',
        'modifiers': {'speed': 5, 'stamina': -10},
    },
    'normal': {
        'name': 'Normal Tempo',
        'description': 'Standard game speed',
        'modifiers': {},
    },
    'control': {
        'name': 'Control Tempo',
        'description': 'Slow the game down, manage territory',
        'modifiers': {'game_sense': 5, 'kicking': 5, 'speed': -5},
    },
}


def get_all_tactical_options():
    """Return all tactical options for the frontend."""
    return {
        'attacking_style': ATTACKING_STYLES,
        'kicking_game': KICKING_GAMES,
        'defensive_style': DEFENSIVE_STYLES,
        'set_piece': SET_PIECE_APPROACHES,
        'tempo': TEMPO_OPTIONS,
    }
