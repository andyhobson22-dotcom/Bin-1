"""Match event resolution — determines outcomes based on player stats,
tactics, fatigue, home advantage, and style-player fit."""
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


# ── Helpers ────────────────────────────────────────────────────────

def _avg_stat(players, stat):
    """Average of a stat across a list of players."""
    if not players:
        return 50
    return sum(p.get(stat, 50) for p in players) / len(players)


def _fatigue_modifier(fatigue_pct):
    """Convert a fatigue percentage (0-100) into a stat penalty.

    0% fatigue = 0 penalty
    50% fatigue = -5
    100% fatigue = -15
    """
    return -(fatigue_pct / 100) * 15


def _home_bonus():
    """Small home advantage stat bonus."""
    return 3


def _fit_modifier(fit_score):
    """Convert style-player fit (0.0-1.0) into a stat modifier.

    0.0 (terrible fit) = -8
    0.5 (neutral)      =  0
    1.0 (perfect fit)  = +8
    """
    return (fit_score - 0.5) * 16


def _context_modifier(ctx):
    """Extract the combined modifier from a context dict."""
    mod = 0
    mod += ctx.get('home_bonus', 0)
    mod += _fatigue_modifier(ctx.get('fatigue', 0))
    mod += _fit_modifier(ctx.get('style_fit', 0.5))
    return mod


# ── Scrum ──────────────────────────────────────────────────────────

def resolve_scrum(attacking_forwards, defending_forwards, atk_ctx=None, def_ctx=None):
    """Resolve a scrum.

    Returns dict with 'outcome': 'won', 'lost', 'penalty_won', 'penalty_against'
    """
    atk_ctx = atk_ctx or {}
    def_ctx = def_ctx or {}

    atk_scrum = _avg_stat(attacking_forwards, 'scrummaging')
    def_scrum = _avg_stat(defending_forwards, 'scrummaging')
    atk_strength = _avg_stat(attacking_forwards, 'strength')
    def_strength = _avg_stat(defending_forwards, 'strength')

    # Combined power with context modifiers
    atk_mod = _context_modifier(atk_ctx)
    def_mod = _context_modifier(def_ctx)

    atk_power = (atk_scrum * 0.6 + atk_strength * 0.4 + atk_mod +
                 random.randint(-15, 15))
    def_power = (def_scrum * 0.6 + def_strength * 0.4 + def_mod +
                 random.randint(-15, 15))

    diff = atk_power - def_power

    if diff > 15:
        return {'outcome': 'penalty_won'}
    elif diff > 0:
        return {'outcome': 'won'}
    elif diff > -10:
        return {'outcome': 'lost'}
    else:
        return {'outcome': 'penalty_against'}


# ── Lineout ────────────────────────────────────────────────────────

def resolve_lineout(attacking_forwards, defending_forwards, atk_ctx=None, def_ctx=None):
    """Resolve a lineout.

    Returns dict with 'outcome': 'won', 'lost', 'penalty_won', 'penalty_against'
    """
    atk_ctx = atk_ctx or {}
    def_ctx = def_ctx or {}

    atk_lineout = _avg_stat(attacking_forwards, 'lineout')
    def_lineout = _avg_stat(defending_forwards, 'lineout')

    atk_mod = _context_modifier(atk_ctx)
    def_mod = _context_modifier(def_ctx)

    atk_score = atk_lineout + atk_mod + random.randint(-12, 12)
    def_score = def_lineout + def_mod + random.randint(-12, 12)

    diff = atk_score - def_score

    if diff > 20:
        return {'outcome': 'penalty_won'}
    elif diff > -5:
        return {'outcome': 'won'}
    elif diff > -15:
        return {'outcome': 'lost'}
    else:
        return {'outcome': 'penalty_against'}


# ── Phase Play ─────────────────────────────────────────────────────

def resolve_phase_play(attacking_players, defending_players, zone, phase_count,
                       atk_ctx=None, def_ctx=None):
    """Resolve a phase of open play.

    atk_ctx / def_ctx may contain:
        home_bonus, fatigue, style_fit,
        offload_chance, offload_turnover_mod, offload_big_play_mod,
        ruck_speed_mod, play_off_bonus
    """
    atk_ctx = atk_ctx or {}
    def_ctx = def_ctx or {}

    # Attacking effectiveness
    atk_handling = _avg_stat(attacking_players, 'handling')
    atk_passing = _avg_stat(attacking_players, 'passing')
    atk_speed = _avg_stat(attacking_players, 'speed')
    atk_strength = _avg_stat(attacking_players, 'strength')

    # Defensive effectiveness
    def_tackling = _avg_stat(defending_players, 'tackling')
    def_game_sense = _avg_stat(defending_players, 'game_sense')
    def_speed = _avg_stat(defending_players, 'speed')

    # Base attack score
    atk_score = (atk_handling * 0.25 + atk_passing * 0.25 +
                 atk_speed * 0.2 + atk_strength * 0.1)

    # Play-off bonus — if the key playmaker is good, attack gets a boost
    atk_score += atk_ctx.get('play_off_bonus', 0)

    # Ruck speed — faster rucks = quicker ball = harder to defend
    atk_score += atk_ctx.get('ruck_speed_mod', 0) * 30  # scaled

    # Offload chance — can create a line break but risks turnover
    offload_chance = atk_ctx.get('offload_chance', 0.15)
    if random.random() < offload_chance:
        # Attempted offload
        offload_skill = atk_handling * 0.5 + atk_passing * 0.3
        if random.randint(1, 100) < offload_skill:
            atk_score += 12  # Big gain from successful offload
            atk_score += atk_ctx.get('offload_big_play_mod', 0) * 40
        else:
            atk_score -= 10  # Failed offload = danger
            atk_score -= atk_ctx.get('offload_turnover_mod', 0) * 30

    # Context modifiers (home advantage, fatigue, style fit)
    atk_score += _context_modifier(atk_ctx)

    # Randomness
    atk_score += random.randint(-18, 18)

    # Defence score — gets stronger the more phases (attacking fatigue)
    fatigue_penalty = min(phase_count * 2, 15)
    def_score = (def_tackling * 0.35 + def_game_sense * 0.25 + def_speed * 0.15)
    def_score += _context_modifier(def_ctx)
    def_score += random.randint(-15, 15) - fatigue_penalty

    diff = atk_score - def_score

    if diff > 12:
        return {'outcome': 'gain'}
    elif diff > -5:
        return {'outcome': 'neutral'}
    else:
        return {'outcome': 'turnover'}


# ── Try Attempt ────────────────────────────────────────────────────

def resolve_try_attempt(attacking_players, defending_players, zone,
                        atk_ctx=None, def_ctx=None):
    """Resolve a try-scoring attempt.

    Returns dict with 'outcome': 'try', 'held_up', 'tackled'
    """
    atk_ctx = atk_ctx or {}
    def_ctx = def_ctx or {}

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
                 atk_handling * 0.15 + zone_bonus.get(zone, 0))

    # Play-off bonus — key playmaker creating the opportunity
    atk_score += atk_ctx.get('play_off_bonus', 0) * 0.5

    # Context modifiers
    atk_score += _context_modifier(atk_ctx)
    atk_score += random.randint(-20, 20)

    def_score = (def_tackling * 0.35 + def_speed * 0.25 + def_strength * 0.2)
    def_score += _context_modifier(def_ctx)
    def_score += random.randint(-15, 15)

    diff = atk_score - def_score

    if diff > 10:
        return {'outcome': 'try'}
    elif diff > 0:
        return {'outcome': 'held_up'}
    else:
        return {'outcome': 'tackled'}


# ── Kicks ──────────────────────────────────────────────────────────

def resolve_kick(kicker, kick_type_cfg, atk_ctx=None):
    """Resolve a kick based on the kick type config.

    Returns dict with 'outcome': 'good', 'poor', 'turnover'
    and 'territory_gain': int (zones)
    """
    atk_ctx = atk_ctx or {}
    kick_skill = kicker.get('kicking', 50)

    # Fatigue reduces kicking accuracy
    kick_skill += _fatigue_modifier(atk_ctx.get('fatigue', 0)) * 0.5
    kick_skill += atk_ctx.get('home_bonus', 0)

    success_roll = random.randint(1, 100)

    if success_roll < kick_skill:
        # Good kick
        territory = kick_type_cfg.get('territory_gain', 1)
        return {'outcome': 'good', 'territory_gain': territory}
    elif random.random() < kick_type_cfg.get('turnover_risk', 0.1):
        # Bad kick that leads to a counter-attack
        return {'outcome': 'turnover', 'territory_gain': 0}
    else:
        # Poor kick — opponent gets decent position
        return {'outcome': 'poor', 'territory_gain': 0}


# ── Conversion / Penalty / Drop Goal ──────────────────────────────

def resolve_conversion(kicker, atk_ctx=None):
    """Resolve a conversion attempt."""
    atk_ctx = atk_ctx or {}
    kick_skill = kicker.get('kicking', 50)
    kick_skill += _fatigue_modifier(atk_ctx.get('fatigue', 0)) * 0.3
    kick_skill += atk_ctx.get('home_bonus', 0) * 0.5  # Crowd helps a bit

    success = random.randint(1, 100) < (kick_skill * 0.85 + 10)
    return {'outcome': 'scored' if success else 'missed'}


def resolve_drop_goal(kicker, atk_ctx=None):
    """Resolve a drop goal attempt."""
    atk_ctx = atk_ctx or {}
    kick_skill = kicker.get('kicking', 50)
    game_sense = kicker.get('game_sense', 50)

    # Fatigue makes it harder
    kick_skill += _fatigue_modifier(atk_ctx.get('fatigue', 0)) * 0.5
    kick_skill += atk_ctx.get('home_bonus', 0)

    combined = kick_skill * 0.6 + game_sense * 0.4
    success = random.randint(1, 100) < (combined * 0.45)
    return {'outcome': 'scored' if success else 'missed'}


def resolve_penalty_kick(kicker, zone, atk_ctx=None):
    """Resolve a penalty kick at goal with distance factor."""
    atk_ctx = atk_ctx or {}
    kick_skill = kicker.get('kicking', 50)
    kick_skill += _fatigue_modifier(atk_ctx.get('fatigue', 0)) * 0.3
    kick_skill += atk_ctx.get('home_bonus', 0) * 0.5

    distance_mod = {0: -30, 1: -20, 2: -5, 3: 5, 4: 10}
    success_chance = kick_skill + distance_mod.get(zone, 0)

    return {'outcome': 'scored' if random.randint(1, 100) < success_chance else 'missed'}


# ── Penalty / Card ─────────────────────────────────────────────────

def resolve_penalty(defending_players):
    """Check if a penalty is awarded based on defensive discipline."""
    return {'outcome': 'penalty'}


def resolve_card_check(defending_players, def_ctx=None):
    """Check if a card should be shown.

    Fatigue increases card risk (tired players make rash tackles).
    """
    def_ctx = def_ctx or {}
    avg_discipline = _avg_stat(defending_players, 'discipline')

    # Fatigue makes discipline worse
    fatigue_penalty = (def_ctx.get('fatigue', 0) / 100) * 10
    effective_discipline = avg_discipline - fatigue_penalty

    roll = random.randint(1, 100)
    card_threshold = effective_discipline * 0.8

    if roll > card_threshold + 30:
        return {'outcome': 'red'}
    elif roll > card_threshold + 10:
        return {'outcome': 'yellow'}
    else:
        return {'outcome': 'none'}
