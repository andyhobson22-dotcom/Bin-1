"""Match event resolution — determines outcomes based on player stats."""
import random

ZONE_NAMES = {
    0: "own 22",
    1: "own half",
    2: "midfield",
    3: "opposition half",
    4: "opposition 22",
}


class EventType:
    PHASE = 'phase'
    SCRUM = 'scrum'
    LINEOUT = 'lineout'
    TRY = 'try'
    CONVERSION = 'conversion'
    PENALTY = 'penalty'
    DROP_GOAL = 'drop_goal'
    CARD = 'card'
    TURNOVER = 'turnover'


def _avg_stat(players, stat):
    """Average of a stat across a list of players."""
    if not players:
        return 50
    return sum(p.get(stat, 50) for p in players) / len(players)


def resolve_scrum(attacking_forwards, defending_forwards):
    """Resolve a scrum.

    Returns dict with 'outcome': 'won', 'lost', 'penalty_won', 'penalty_against'
    """
    atk_scrum = _avg_stat(attacking_forwards, 'scrummaging')
    def_scrum = _avg_stat(defending_forwards, 'scrummaging')
    atk_strength = _avg_stat(attacking_forwards, 'strength')
    def_strength = _avg_stat(defending_forwards, 'strength')

    # Combined power
    atk_power = atk_scrum * 0.6 + atk_strength * 0.4 + random.randint(-15, 15)
    def_power = def_scrum * 0.6 + def_strength * 0.4 + random.randint(-15, 15)

    diff = atk_power - def_power

    if diff > 15:
        return {'outcome': 'penalty_won'}
    elif diff > 0:
        return {'outcome': 'won'}
    elif diff > -10:
        return {'outcome': 'lost'}
    else:
        return {'outcome': 'penalty_against'}


def resolve_lineout(attacking_forwards, defending_forwards):
    """Resolve a lineout.

    Returns dict with 'outcome': 'won', 'lost', 'penalty_won', 'penalty_against'
    """
    # Find hooker (thrower) and locks/flankers (jumpers)
    atk_lineout = _avg_stat(attacking_forwards, 'lineout')
    def_lineout = _avg_stat(defending_forwards, 'lineout')

    atk_score = atk_lineout + random.randint(-12, 12)
    def_score = def_lineout + random.randint(-12, 12)

    diff = atk_score - def_score

    if diff > 20:
        return {'outcome': 'penalty_won'}  # Clean steal with penalty
    elif diff > -5:
        return {'outcome': 'won'}  # Attacking team should win most lineouts
    elif diff > -15:
        return {'outcome': 'lost'}
    else:
        return {'outcome': 'penalty_against'}


def resolve_phase_play(attacking_players, defending_players, zone, phase_count):
    """Resolve a phase of open play.

    Returns dict with 'outcome': 'gain', 'neutral', 'turnover'
    """
    # Attacking effectiveness
    atk_handling = _avg_stat(attacking_players, 'handling')
    atk_passing = _avg_stat(attacking_players, 'passing')
    atk_speed = _avg_stat(attacking_players, 'speed')

    # Defensive effectiveness
    def_tackling = _avg_stat(defending_players, 'tackling')
    def_game_sense = _avg_stat(defending_players, 'game_sense')

    # Attack score
    atk_score = (atk_handling * 0.3 + atk_passing * 0.3 + atk_speed * 0.2 +
                 random.randint(-20, 20))

    # Defence score - gets stronger the more phases there are (fatigue in attack)
    fatigue_penalty = min(phase_count * 2, 15)
    def_score = (def_tackling * 0.4 + def_game_sense * 0.3 +
                 random.randint(-15, 15) - fatigue_penalty)

    diff = atk_score - def_score

    if diff > 10:
        return {'outcome': 'gain'}
    elif diff > -5:
        return {'outcome': 'neutral'}
    else:
        return {'outcome': 'turnover'}


def resolve_try_attempt(attacking_players, defending_players, zone):
    """Resolve a try-scoring attempt.

    Returns dict with 'outcome': 'try', 'held_up', 'tackled'
    """
    # Attack
    atk_speed = _avg_stat(attacking_players, 'speed')
    atk_agility = _avg_stat(attacking_players, 'agility')
    atk_strength = _avg_stat(attacking_players, 'strength')
    atk_handling = _avg_stat(attacking_players, 'handling')

    # Defense
    def_tackling = _avg_stat(defending_players, 'tackling')
    def_speed = _avg_stat(defending_players, 'speed')
    def_strength = _avg_stat(defending_players, 'strength')

    # Zone bonus — closer to try line = better chance
    zone_bonus = {0: -30, 1: -20, 2: -10, 3: 5, 4: 15}

    atk_score = (atk_speed * 0.25 + atk_agility * 0.25 + atk_strength * 0.2 +
                 atk_handling * 0.15 + zone_bonus.get(zone, 0) +
                 random.randint(-20, 20))

    def_score = (def_tackling * 0.35 + def_speed * 0.25 + def_strength * 0.2 +
                 random.randint(-15, 15))

    diff = atk_score - def_score

    if diff > 10:
        return {'outcome': 'try'}
    elif diff > 0:
        return {'outcome': 'held_up'}
    else:
        return {'outcome': 'tackled'}


def resolve_conversion(kicker):
    """Resolve a conversion attempt."""
    kick_skill = kicker.get('kicking', 50)
    # Conversions are ~75% for a good kicker
    success = random.randint(1, 100) < (kick_skill * 0.85 + 10)
    return {'outcome': 'scored' if success else 'missed'}


def resolve_drop_goal(kicker):
    """Resolve a drop goal attempt."""
    kick_skill = kicker.get('kicking', 50)
    game_sense = kicker.get('game_sense', 50)
    # Drop goals are hard — ~30-40% success for a good kicker
    combined = kick_skill * 0.6 + game_sense * 0.4
    success = random.randint(1, 100) < (combined * 0.45)
    return {'outcome': 'scored' if success else 'missed'}


def resolve_penalty(defending_players):
    """Check if a penalty is awarded based on defensive discipline."""
    avg_discipline = _avg_stat(defending_players, 'discipline')
    # Higher discipline = fewer penalties
    # This is called when a penalty event is triggered, so it always results in a penalty
    return {'outcome': 'penalty'}


def resolve_card_check(defending_players):
    """Check if a card should be shown."""
    avg_discipline = _avg_stat(defending_players, 'discipline')

    roll = random.randint(1, 100)
    # Low discipline increases card chance
    card_threshold = avg_discipline * 0.8

    if roll > card_threshold + 30:
        return {'outcome': 'red'}
    elif roll > card_threshold + 10:
        return {'outcome': 'yellow'}
    else:
        return {'outcome': 'none'}
