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


# ── Position Roles — With Ball ─────────────────────────────────────

# Each role has stat weights that determine how effective it is for
# a given player, plus modifiers that feed into the match engine.

ROLES_WITH_BALL = {
    # ── Props (1, 3) ──
    'walking_pillar_wb': {
        'name': 'Walking Pillar',
        'description': "Minimal involvement beyond set pieces. Don't pass, lad.",
        'positions': ['loosehead_prop', 'tighthead_prop'],
        'fatigue_mod': -0.3,       # Saves energy
        'carry_frequency': 0.05,   # Barely carries
        'pass_tendency': 0.0,
        'fit_stats': {'scrummaging': 0.5, 'strength': 0.5},
    },
    'second_8_forward': {
        'name': 'Second 8',
        'description': 'Crash into the line wherever possible. Tiring but powerful.',
        'positions': [
            'loosehead_prop', 'tighthead_prop', 'hooker',
            'lock_4', 'lock_5', 'blindside_flanker', 'openside_flanker',
            'number_eight', 'inside_centre', 'left_wing', 'right_wing',
        ],
        'fatigue_mod': 0.4,        # Very tiring
        'carry_frequency': 0.45,   # Carries a lot
        'pass_tendency': 0.1,
        'fit_stats': {'strength': 0.4, 'stamina': 0.3, 'speed': 0.15, 'handling': 0.15},
    },
    'all_court_forward': {
        'name': 'All Court',
        'description': 'Passes more than usual, recycles quickly rather than making yards.',
        'positions': [
            'loosehead_prop', 'tighthead_prop', 'hooker',
            'lock_4', 'lock_5', 'blindside_flanker', 'openside_flanker',
            'number_eight',
        ],
        'fatigue_mod': 0.1,
        'carry_frequency': 0.15,
        'pass_tendency': 0.6,
        'fit_stats': {'handling': 0.3, 'passing': 0.3, 'game_sense': 0.2, 'stamina': 0.2},
    },
    # ── Back Row extra ──
    'wide_forward': {
        'name': 'Wide Forward',
        'description': 'Hangs out by the wings rather than playing off 9 or 10.',
        'positions': ['blindside_flanker', 'openside_flanker', 'number_eight'],
        'fatigue_mod': 0.2,
        'carry_frequency': 0.25,
        'pass_tendency': 0.3,
        'wide_runner': True,
        'fit_stats': {'speed': 0.3, 'handling': 0.25, 'agility': 0.25, 'stamina': 0.2},
    },
    # ── Scrum Half (9) ──
    'darter': {
        'name': 'Darter',
        'description': 'Sniping runs from the ruck — masked, darting, dangerous.',
        'positions': ['scrum_half'],
        'fatigue_mod': 0.25,
        'carry_frequency': 0.35,
        'pass_tendency': 0.3,
        'fit_stats': {'speed': 0.3, 'agility': 0.3, 'handling': 0.2, 'game_sense': 0.2},
    },
    'playmaker_9': {
        'name': 'Playmaker',
        'description': 'Controls tempo more than the 10. Wider passing range.',
        'positions': ['scrum_half'],
        'fatigue_mod': 0.1,
        'carry_frequency': 0.1,
        'pass_tendency': 0.8,
        'tempo_control': True,
        'fit_stats': {'passing': 0.35, 'game_sense': 0.3, 'kicking': 0.2, 'handling': 0.15},
    },
    'field_marshal': {
        'name': 'Field Marshal',
        'description': 'Uses box kicks frequently to contest territory.',
        'positions': ['scrum_half'],
        'fatigue_mod': 0.05,
        'carry_frequency': 0.05,
        'pass_tendency': 0.3,
        'box_kick_tendency': 0.5,
        'fit_stats': {'kicking': 0.4, 'game_sense': 0.3, 'kick_chase': 0.15, 'passing': 0.15},
    },
    # ── Fly Half (10) ──
    'to_the_line': {
        'name': 'To The Line',
        'description': 'Gets close to the defensive line before releasing the ball.',
        'positions': ['fly_half'],
        'fatigue_mod': 0.15,
        'carry_frequency': 0.25,
        'pass_tendency': 0.5,
        'flat_play': True,
        'fit_stats': {'game_sense': 0.3, 'passing': 0.25, 'speed': 0.2, 'handling': 0.25},
    },
    'full_flair': {
        'name': 'Full Flair',
        'description': 'Total licence — does whatever he wants. High variance.',
        'positions': ['fly_half'],
        'fatigue_mod': 0.2,
        'carry_frequency': 0.2,
        'pass_tendency': 0.5,
        'flair_variance': 0.3,  # Extra randomness in outcomes
        'fit_stats': {'game_sense': 0.25, 'agility': 0.25, 'passing': 0.25, 'handling': 0.25},
    },
    'territory_targeter': {
        'name': 'Territory Targeter',
        'description': 'Uses kicks to pin the opposition back and control territory.',
        'positions': ['fly_half'],
        'fatigue_mod': 0.05,
        'carry_frequency': 0.05,
        'pass_tendency': 0.3,
        'kick_tendency_boost': 0.4,
        'fit_stats': {'kicking': 0.4, 'game_sense': 0.3, 'kick_chase': 0.15, 'passing': 0.15},
    },
    'looper': {
        'name': 'Looper',
        'description': 'Loops around to play wider — creates overlaps out wide.',
        'positions': ['fly_half'],
        'fatigue_mod': 0.2,
        'carry_frequency': 0.15,
        'pass_tendency': 0.6,
        'wide_runner': True,
        'fit_stats': {'speed': 0.25, 'passing': 0.3, 'game_sense': 0.25, 'agility': 0.2},
    },
    # ── Wings (11, 14) ──
    'second_8_wing': {
        'name': 'Second 8',
        'description': 'Uses power not pace, comes infield often. Think heavy-duty winger.',
        'positions': ['left_wing', 'right_wing'],
        'fatigue_mod': 0.35,
        'carry_frequency': 0.4,
        'pass_tendency': 0.1,
        'fit_stats': {'strength': 0.35, 'stamina': 0.3, 'handling': 0.2, 'speed': 0.15},
    },
    'poacher': {
        'name': 'Poacher',
        'description': 'Bides his time, looking to exploit clear gaps when they appear.',
        'positions': ['left_wing', 'right_wing'],
        'fatigue_mod': -0.1,
        'carry_frequency': 0.15,
        'pass_tendency': 0.2,
        'opportunist': True,
        'fit_stats': {'game_sense': 0.3, 'speed': 0.25, 'agility': 0.25, 'handling': 0.2},
    },
    'flyer': {
        'name': 'Flyer',
        'description': 'Wants the ball in space to back his pace. Pure speed merchant.',
        'positions': ['left_wing', 'right_wing'],
        'fatigue_mod': 0.15,
        'carry_frequency': 0.3,
        'pass_tendency': 0.15,
        'fit_stats': {'speed': 0.4, 'agility': 0.25, 'handling': 0.2, 'kick_chase': 0.15},
    },
    # ── Centres (12, 13) ──
    'second_8_centre': {
        'name': 'Second 8',
        'description': 'Think Manu Tuilagi — power carrier who bends the defensive line.',
        'positions': ['inside_centre', 'outside_centre'],
        'fatigue_mod': 0.3,
        'carry_frequency': 0.4,
        'pass_tendency': 0.15,
        'fit_stats': {'strength': 0.35, 'speed': 0.25, 'stamina': 0.2, 'handling': 0.2},
    },
    'second_10': {
        'name': 'Second 10',
        'description': 'Think Owen Farrell — playmaker who distributes and organises.',
        'positions': ['inside_centre', 'outside_centre'],
        'fatigue_mod': 0.1,
        'carry_frequency': 0.1,
        'pass_tendency': 0.7,
        'playmaker': True,
        'fit_stats': {'passing': 0.3, 'game_sense': 0.3, 'kicking': 0.2, 'handling': 0.2},
    },
    'evader': {
        'name': 'Evader',
        'description': 'Quick and steppy — beats defenders with footwork.',
        'positions': ['inside_centre', 'outside_centre'],
        'fatigue_mod': 0.15,
        'carry_frequency': 0.3,
        'pass_tendency': 0.3,
        'fit_stats': {'agility': 0.35, 'speed': 0.25, 'handling': 0.2, 'game_sense': 0.2},
    },
    # ── Fullback (15) ──
    'counter_man': {
        'name': 'Counter Man',
        'description': 'Waits to catch kicks for his chance to attack from deep.',
        'positions': ['fullback'],
        'fatigue_mod': 0.0,
        'carry_frequency': 0.2,
        'pass_tendency': 0.3,
        'counter_attack': True,
        'fit_stats': {'speed': 0.25, 'handling': 0.25, 'kick_chase': 0.25, 'agility': 0.25},
    },
    'second_10_fb': {
        'name': 'Second 10',
        'description': 'Helps as an extra playmaker — inserts into the line to distribute.',
        'positions': ['fullback'],
        'fatigue_mod': 0.15,
        'carry_frequency': 0.15,
        'pass_tendency': 0.6,
        'playmaker': True,
        'fit_stats': {'passing': 0.3, 'game_sense': 0.3, 'handling': 0.2, 'kicking': 0.2},
    },
    'second_8_fb': {
        'name': 'Second 8',
        'description': 'Comes in for a crash ball now and then — surprise power runner.',
        'positions': ['fullback'],
        'fatigue_mod': 0.2,
        'carry_frequency': 0.3,
        'pass_tendency': 0.2,
        'fit_stats': {'strength': 0.3, 'speed': 0.25, 'handling': 0.25, 'stamina': 0.2},
    },
}


# ── Position Roles — Without Ball ──────────────────────────────────

ROLES_WITHOUT_BALL = {
    # ── Forwards ──
    'walking_pillar_def': {
        'name': 'Walking Pillar',
        'description': "Nothing special — do your job and wait for the scrum, lad.",
        'positions': ['loosehead_prop', 'tighthead_prop', 'hooker', 'lock_4', 'lock_5'],
        'tackle_aggression': 0.3,
        'discipline_mod': 0.05,
        'fatigue_mod': -0.2,
        'fit_stats': {'scrummaging': 0.5, 'strength': 0.3, 'discipline': 0.2},
    },
    'destroyer': {
        'name': 'Destroyer',
        'description': 'Look for big hits and knock runners back. Risk of overlaps and ill discipline.',
        'positions': [
            'loosehead_prop', 'tighthead_prop', 'hooker',
            'lock_4', 'lock_5', 'blindside_flanker', 'openside_flanker',
            'number_eight',
        ],
        'tackle_aggression': 0.9,
        'discipline_mod': -0.15,   # More penalties
        'overlap_risk': 0.12,      # Can leave gaps
        'fatigue_mod': 0.2,
        'fit_stats': {'tackling': 0.35, 'strength': 0.3, 'speed': 0.2, 'discipline': 0.15},
    },
    'treacle': {
        'name': 'Treacle',
        'description': 'Hold carriers up and slow the game down. Bog them in treacle.',
        'positions': ['loosehead_prop', 'tighthead_prop', 'hooker', 'lock_4', 'lock_5'],
        'tackle_aggression': 0.4,
        'slow_ball_mod': 0.2,      # Slows opposition ruck
        'discipline_mod': 0.0,
        'fatigue_mod': 0.1,
        'fit_stats': {'strength': 0.35, 'tackling': 0.3, 'stamina': 0.2, 'game_sense': 0.15},
    },
    'jackler': {
        'name': 'Jackler',
        'description': 'Contest the breakdown — win turnovers at the ruck.',
        'positions': ['hooker', 'blindside_flanker', 'openside_flanker', 'number_eight'],
        'tackle_aggression': 0.5,
        'jackal_chance': 0.15,     # Chance to win turnover at each ruck
        'discipline_mod': -0.08,   # Risk of penalties at the breakdown
        'fatigue_mod': 0.15,
        'fit_stats': {'tackling': 0.25, 'strength': 0.25, 'speed': 0.25, 'game_sense': 0.25},
    },
    'work_horse': {
        'name': 'Work Horse',
        'description': 'Quantity of tackles — never stops working. Covers every blade.',
        'positions': [
            'lock_4', 'lock_5', 'blindside_flanker', 'openside_flanker',
            'number_eight',
        ],
        'tackle_aggression': 0.6,
        'tackle_volume': 0.3,      # Makes more tackles
        'discipline_mod': 0.05,
        'fatigue_mod': 0.25,
        'fit_stats': {'stamina': 0.35, 'tackling': 0.3, 'speed': 0.2, 'strength': 0.15},
    },
    # ── Scrum Half (9) ──
    'irritant': {
        'name': 'Irritant',
        'description': 'Runs ahead of the defensive line to disrupt the opposition.',
        'positions': ['scrum_half'],
        'tackle_aggression': 0.7,
        'disruption': 0.2,
        'discipline_mod': -0.1,
        'fatigue_mod': 0.2,
        'fit_stats': {'speed': 0.3, 'tackling': 0.25, 'agility': 0.25, 'stamina': 0.2},
    },
    'sweeper_9': {
        'name': 'Sweeper',
        'description': 'Guards against kicks behind the defensive line.',
        'positions': ['scrum_half'],
        'tackle_aggression': 0.3,
        'kick_cover': 0.3,
        'discipline_mod': 0.05,
        'fatigue_mod': 0.1,
        'fit_stats': {'game_sense': 0.3, 'speed': 0.25, 'kick_chase': 0.25, 'handling': 0.2},
    },
    'mixed_9': {
        'name': 'Mixed',
        'description': 'Uses game sense to judge whether to press up or sweep back.',
        'positions': ['scrum_half'],
        'tackle_aggression': 0.5,
        'kick_cover': 0.15,
        'disruption': 0.1,
        'discipline_mod': 0.0,
        'fatigue_mod': 0.15,
        'fit_stats': {'game_sense': 0.4, 'speed': 0.2, 'tackling': 0.2, 'handling': 0.2},
    },
    # ── Backs in line (10, centres) ──
    'drift_def': {
        'name': 'Drift',
        'description': 'Slide across the field — cover space patiently.',
        'positions': ['fly_half', 'inside_centre', 'outside_centre'],
        'tackle_aggression': 0.4,
        'discipline_mod': 0.05,
        'overlap_risk': 0.03,
        'fatigue_mod': 0.1,
        'fit_stats': {'game_sense': 0.35, 'tackling': 0.3, 'speed': 0.2, 'discipline': 0.15},
    },
    'blitz_def': {
        'name': 'Blitz',
        'description': 'Fly up aggressively on the attacker — high risk, high reward.',
        'positions': ['fly_half', 'inside_centre', 'outside_centre'],
        'tackle_aggression': 0.85,
        'discipline_mod': -0.12,
        'overlap_risk': 0.15,
        'fatigue_mod': 0.2,
        'fit_stats': {'tackling': 0.3, 'speed': 0.3, 'agility': 0.2, 'discipline': 0.2},
    },
    # ── Wings in line ──
    'kettle': {
        'name': 'Kettle',
        'description': 'Rush up from wide to squeeze and kettle the attack inward.',
        'positions': ['left_wing', 'right_wing'],
        'tackle_aggression': 0.7,
        'discipline_mod': -0.05,
        'overlap_risk': 0.10,
        'fatigue_mod': 0.15,
        'fit_stats': {'speed': 0.3, 'tackling': 0.25, 'game_sense': 0.25, 'stamina': 0.2},
    },
    'stay_wide': {
        'name': 'Stay Wide',
        'description': 'Hold position out wide — cover the touchline.',
        'positions': ['left_wing', 'right_wing'],
        'tackle_aggression': 0.4,
        'discipline_mod': 0.05,
        'overlap_risk': 0.02,
        'fatigue_mod': 0.05,
        'fit_stats': {'tackling': 0.3, 'speed': 0.25, 'game_sense': 0.25, 'discipline': 0.2},
    },
}


# ── Defensive Drop-Behind System ──────────────────────────────────
# Manager picks 1-3 players to drop behind the defensive line.
# At least 1 must be "full_cover". Others can be "watcher".

DROP_BEHIND_ROLES = {
    'full_cover': {
        'name': 'Full Cover',
        'description': 'Stays deep permanently — covers the backfield against kicks.',
        'kick_cover': 0.4,
        'counter_attack_chance': 0.2,
        'in_line': False,
        'fit_stats': {'speed': 0.25, 'handling': 0.25, 'kick_chase': 0.25, 'game_sense': 0.25},
    },
    'watcher': {
        'name': 'Watcher',
        'description': 'Uses game sense to decide — drop back or stay in the line.',
        'kick_cover': 0.2,
        'counter_attack_chance': 0.1,
        'in_line': 'sometimes',  # Game sense determines
        'fit_stats': {'game_sense': 0.4, 'speed': 0.25, 'kick_chase': 0.2, 'handling': 0.15},
    },
}

# Which positions CAN be dropped behind
DROP_BEHIND_ELIGIBLE = [
    'fullback', 'fly_half', 'left_wing', 'right_wing',
    'inside_centre', 'outside_centre', 'scrum_half',
]


def get_roles_for_position(position):
    """Get available with-ball and without-ball roles for a position."""
    with_ball = {}
    for key, role in ROLES_WITH_BALL.items():
        if position in role['positions']:
            with_ball[key] = role

    without_ball = {}
    for key, role in ROLES_WITHOUT_BALL.items():
        if position in role['positions']:
            without_ball[key] = role

    can_drop = position in DROP_BEHIND_ELIGIBLE

    return {
        'with_ball': with_ball,
        'without_ball': without_ball,
        'can_drop_behind': can_drop,
    }


def default_role_for_position(position):
    """Return sensible default roles for each position."""
    defaults = {
        'loosehead_prop': ('walking_pillar_wb', 'walking_pillar_def'),
        'tighthead_prop': ('walking_pillar_wb', 'walking_pillar_def'),
        'hooker': ('walking_pillar_wb', 'walking_pillar_def'),
        'lock_4': ('all_court_forward', 'work_horse'),
        'lock_5': ('all_court_forward', 'work_horse'),
        'blindside_flanker': ('all_court_forward', 'destroyer'),
        'openside_flanker': ('all_court_forward', 'jackler'),
        'number_eight': ('second_8_forward', 'destroyer'),
        'scrum_half': ('playmaker_9', 'mixed_9'),
        'fly_half': ('to_the_line', 'drift_def'),
        'inside_centre': ('second_10', 'drift_def'),
        'outside_centre': ('evader', 'drift_def'),
        'left_wing': ('flyer', 'stay_wide'),
        'right_wing': ('flyer', 'stay_wide'),
        'fullback': ('counter_man', None),  # None = dropped behind
    }
    return defaults.get(position, ('walking_pillar_wb', 'walking_pillar_def'))


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
        # Position roles (position -> role_key)
        'roles_with_ball': {},     # Empty = use defaults
        'roles_without_ball': {},  # Empty = use defaults
        # Defensive drop-behind (list of {position, role})
        'drop_behind': [
            {'position': 'fullback', 'role': 'full_cover'},
        ],
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
    from models.player import POSITIONS
    # Build per-position role options
    position_roles = {}
    for pos_key in POSITIONS:
        position_roles[pos_key] = get_roles_for_position(pos_key)

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
        'position_roles': position_roles,
        'drop_behind_roles': DROP_BEHIND_ROLES,
        'drop_behind_eligible': DROP_BEHIND_ELIGIBLE,
    }
