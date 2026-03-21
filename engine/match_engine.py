"""Core match simulation engine for rugby union."""
import random
from engine.commentary import generate_commentary
from engine.events import (
    ZONE_NAMES, EventType, resolve_scrum, resolve_lineout,
    resolve_phase_play, resolve_penalty, resolve_try_attempt,
    resolve_conversion, resolve_drop_goal, resolve_card_check,
)


class MatchState:
    """Tracks the state of a match in progress."""

    def __init__(self, home_team, away_team, home_players, away_players,
                 home_tactics=None, away_tactics=None):
        self.home_team = home_team
        self.away_team = away_team
        self.home_players = home_players  # List of 23 player dicts (15 starters + 8 bench)
        self.away_players = away_players
        self.home_tactics = home_tactics or default_tactics()
        self.away_tactics = away_tactics or default_tactics()

        # Score
        self.home_score = 0
        self.away_score = 0
        self.home_tries = 0
        self.away_tries = 0
        self.home_conversions = 0
        self.away_conversions = 0
        self.home_penalties = 0
        self.away_penalties = 0
        self.home_drop_goals = 0
        self.away_drop_goals = 0
        self.home_yellow_cards = 0
        self.away_yellow_cards = 0
        self.home_red_cards = 0
        self.away_red_cards = 0

        # Match state
        self.minute = 0
        self.possession = 'home'  # 'home' or 'away'
        self.zone = 2  # 0=own22, 1=own_half, 2=midfield, 3=opp_half, 4=opp22
        self.phase = 0  # Current phase count in this passage
        self.events = []
        self.commentary = []
        self.half = 1

        # Sin bin tracking: {player_id: return_minute}
        self.sin_bin = {}

    @property
    def attacking_team(self):
        return self.home_team if self.possession == 'home' else self.away_team

    @property
    def defending_team(self):
        return self.away_team if self.possession == 'home' else self.home_team

    @property
    def attacking_players(self):
        return self.home_players[:15] if self.possession == 'home' else self.away_players[:15]

    @property
    def defending_players(self):
        return self.away_players[:15] if self.possession == 'home' else self.home_players[:15]

    def get_kicker(self, side):
        """Get the best kicker from the team on the field."""
        players = self.home_players[:15] if side == 'home' else self.away_players[:15]
        return max(players, key=lambda p: p.get('kicking', 50))

    def get_avg_stat(self, players, stat, positions=None):
        """Get average stat from players, optionally filtered by position group."""
        if positions:
            filtered = [p for p in players if p.get('position', '') in positions]
            if not filtered:
                filtered = players
        else:
            filtered = players
        return sum(p.get(stat, 50) for p in filtered) / len(filtered)

    def swap_possession(self):
        self.possession = 'away' if self.possession == 'home' else 'home'
        self.zone = 4 - self.zone  # Mirror field position
        self.phase = 0

    def add_score(self, side, points, score_type):
        if side == 'home':
            self.home_score += points
            if score_type == 'try':
                self.home_tries += 1
            elif score_type == 'conversion':
                self.home_conversions += 1
            elif score_type == 'penalty':
                self.home_penalties += 1
            elif score_type == 'drop_goal':
                self.home_drop_goals += 1
        else:
            self.away_score += points
            if score_type == 'try':
                self.away_tries += 1
            elif score_type == 'conversion':
                self.away_conversions += 1
            elif score_type == 'penalty':
                self.away_penalties += 1
            elif score_type == 'drop_goal':
                self.away_drop_goals += 1

    def add_card(self, side, card_type, player):
        if card_type == 'yellow':
            if side == 'home':
                self.home_yellow_cards += 1
            else:
                self.away_yellow_cards += 1
            self.sin_bin[player['id']] = self.minute + 10
        elif card_type == 'red':
            if side == 'home':
                self.home_red_cards += 1
            else:
                self.away_red_cards += 1

    def check_sin_bin_returns(self):
        """Return players from sin bin if their time is up."""
        returned = []
        for pid, return_min in list(self.sin_bin.items()):
            if self.minute >= return_min:
                del self.sin_bin[pid]
                returned.append(pid)
        return returned

    def to_result(self):
        """Convert match state to a result dict for saving."""
        return {
            'home_team_id': self.home_team['id'],
            'away_team_id': self.away_team['id'],
            'home_score': self.home_score,
            'away_score': self.away_score,
            'home_tries': self.home_tries,
            'away_tries': self.away_tries,
            'home_conversions': self.home_conversions,
            'away_conversions': self.away_conversions,
            'home_penalties': self.home_penalties,
            'away_penalties': self.away_penalties,
            'home_drop_goals': self.home_drop_goals,
            'away_drop_goals': self.away_drop_goals,
            'home_yellow_cards': self.home_yellow_cards,
            'away_yellow_cards': self.away_yellow_cards,
            'home_red_cards': self.home_red_cards,
            'away_red_cards': self.away_red_cards,
            'events': self.events,
            'commentary': self.commentary,
        }


def default_tactics():
    return {
        'attacking_style': 'balanced',   # expansive, structured, balanced
        'kicking_game': 'balanced',      # kick_heavy, run_first, balanced
        'defensive_style': 'drift',      # rush, drift, blitz
        'set_piece': 'balanced',         # maul_focused, quick_ball, conservative
        'tempo': 'normal',               # high, normal, control
    }


def simulate_match(home_team, away_team, home_players, away_players,
                   home_tactics=None, away_tactics=None, fixture_id=None):
    """Simulate a full 80-minute rugby match."""
    state = MatchState(home_team, away_team, home_players, away_players,
                       home_tactics, away_tactics)

    # Kickoff
    state.possession = 'away'  # Receiving team gets possession from kickoff
    state.zone = 2
    state.commentary.append({
        'minute': 0,
        'text': f"Kick-off at {home_team['name']}'s {home_team.get('stadium', 'ground')}! "
                f"{home_team['name']} vs {away_team['name']}."
    })

    # Simulate 80 minutes
    for minute in range(1, 81):
        state.minute = minute

        # Half time
        if minute == 41 and state.half == 1:
            state.half = 2
            state.possession = 'home'
            state.zone = 2
            state.phase = 0
            state.commentary.append({
                'minute': 40,
                'text': f"HALF TIME: {home_team['name']} {state.home_score} - "
                        f"{state.away_score} {away_team['name']}"
            })

        # Check sin bin returns
        returned = state.check_sin_bin_returns()
        for pid in returned:
            state.commentary.append({
                'minute': minute,
                'text': "A player returns from the sin bin."
            })

        # Simulate this minute
        _simulate_minute(state)

    # Full time
    state.commentary.append({
        'minute': 80,
        'text': f"FULL TIME: {home_team['name']} {state.home_score} - "
                f"{state.away_score} {away_team['name']}"
    })

    result = state.to_result()
    result['fixture_id'] = fixture_id
    return result


def _simulate_minute(state):
    """Simulate one minute of play."""
    # Determine what happens this minute
    event_roll = random.random()
    tactics = state.home_tactics if state.possession == 'home' else state.away_tactics

    # Probability weights based on zone and tactics
    if state.zone <= 1:
        # In own territory - more likely to kick
        if event_roll < 0.25:
            _handle_kick(state)
        elif event_roll < 0.50:
            _handle_phase_play(state)
        elif event_roll < 0.65:
            _handle_set_piece(state, 'scrum')
        elif event_roll < 0.75:
            _handle_set_piece(state, 'lineout')
        elif event_roll < 0.85:
            _handle_turnover(state)
        else:
            _handle_penalty_event(state)

    elif state.zone == 2:
        # Midfield - balanced play
        if event_roll < 0.35:
            _handle_phase_play(state)
        elif event_roll < 0.50:
            _handle_kick(state)
        elif event_roll < 0.60:
            _handle_set_piece(state, 'scrum')
        elif event_roll < 0.70:
            _handle_set_piece(state, 'lineout')
        elif event_roll < 0.82:
            _handle_turnover(state)
        elif event_roll < 0.92:
            _handle_penalty_event(state)
        else:
            _handle_card_event(state)

    else:
        # In opposition territory - more attacking
        if event_roll < 0.30:
            _handle_phase_play(state)
        elif event_roll < 0.45:
            _handle_try_opportunity(state)
        elif event_roll < 0.55:
            _handle_set_piece(state, 'scrum')
        elif event_roll < 0.65:
            _handle_set_piece(state, 'lineout')
        elif event_roll < 0.75:
            _handle_penalty_event(state)
        elif event_roll < 0.82:
            _handle_turnover(state)
        elif event_roll < 0.88:
            _handle_drop_goal_attempt(state)
        else:
            _handle_card_event(state)


def _handle_phase_play(state):
    """Handle a phase of attacking play."""
    result = resolve_phase_play(
        state.attacking_players, state.defending_players,
        state.zone, state.phase
    )
    state.phase += 1

    atk_team = state.attacking_team
    commentary_text = generate_commentary('phase', {
        'team': atk_team['name'],
        'result': result['outcome'],
        'player': random.choice(state.attacking_players)['name'],
        'zone': ZONE_NAMES[state.zone],
    })

    if result['outcome'] == 'gain':
        if state.zone < 4:
            state.zone += 1
    elif result['outcome'] == 'turnover':
        state.swap_possession()
        commentary_text += f" Turnover! {state.attacking_team['name']} win the ball."

    state.commentary.append({'minute': state.minute, 'text': commentary_text})


def _handle_kick(state):
    """Handle a territorial or tactical kick."""
    kicker = state.get_kicker(state.possession)
    kick_skill = kicker.get('kicking', 50)

    atk_team = state.attacking_team

    # Good kick gains territory
    if random.randint(1, 100) < kick_skill:
        # Successful kick for territory
        state.swap_possession()
        # Kicking team loses possession but gains territory
        # After swap, zone is mirrored. A good kick means opponent gets ball in their own half
        if state.zone > 1:
            state.zone -= 1
        text = generate_commentary('kick_good', {
            'team': atk_team['name'],
            'kicker': kicker['name'],
            'zone': ZONE_NAMES[state.zone],
        })
    else:
        # Poor kick - opponent gets good position
        state.swap_possession()
        text = generate_commentary('kick_poor', {
            'team': atk_team['name'],
            'kicker': kicker['name'],
        })

    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_set_piece(state, set_piece_type):
    """Handle a scrum or lineout."""
    atk_forwards = [p for p in state.attacking_players
                    if p.get('position', '') in (
                        'loosehead_prop', 'hooker', 'tighthead_prop',
                        'lock_4', 'lock_5', 'blindside_flanker',
                        'openside_flanker', 'number_eight')]
    def_forwards = [p for p in state.defending_players
                    if p.get('position', '') in (
                        'loosehead_prop', 'hooker', 'tighthead_prop',
                        'lock_4', 'lock_5', 'blindside_flanker',
                        'openside_flanker', 'number_eight')]

    if not atk_forwards:
        atk_forwards = state.attacking_players[:8]
    if not def_forwards:
        def_forwards = state.defending_players[:8]

    if set_piece_type == 'scrum':
        result = resolve_scrum(atk_forwards, def_forwards)
    else:
        result = resolve_lineout(atk_forwards, def_forwards)

    atk_team = state.attacking_team
    text = generate_commentary(set_piece_type, {
        'team': atk_team['name'],
        'result': result['outcome'],
        'zone': ZONE_NAMES[state.zone],
    })

    if result['outcome'] == 'won':
        state.phase = 0  # Clean ball
        if state.zone < 4:
            state.zone += 1
    elif result['outcome'] == 'penalty_won':
        state.phase = 0
        # Penalty advantage
        if state.zone >= 3:
            _handle_penalty_kick(state)
            return
        elif state.zone < 4:
            state.zone += 1
    elif result['outcome'] == 'lost':
        state.swap_possession()
        text += f" {state.attacking_team['name']} steal the ball!"
    elif result['outcome'] == 'penalty_against':
        state.swap_possession()
        text += " Penalty conceded!"

    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_try_opportunity(state):
    """Handle a try-scoring opportunity."""
    result = resolve_try_attempt(
        state.attacking_players, state.defending_players, state.zone
    )

    atk_team = state.attacking_team
    scorer = random.choice(state.attacking_players)

    if result['outcome'] == 'try':
        state.add_score(state.possession, 5, 'try')
        text = generate_commentary('try', {
            'team': atk_team['name'],
            'scorer': scorer['name'],
        })
        state.commentary.append({'minute': state.minute, 'text': text})
        state.events.append({
            'minute': state.minute,
            'type': 'try',
            'team': state.possession,
            'team_name': atk_team['name'],
            'player': scorer['name'],
        })

        # Conversion attempt
        _handle_conversion(state)

        # Reset after try
        state.possession = 'away' if state.possession == 'home' else 'home'
        state.zone = 2
        state.phase = 0
    elif result['outcome'] == 'held_up':
        text = generate_commentary('held_up', {
            'team': atk_team['name'],
            'player': scorer['name'],
        })
        state.commentary.append({'minute': state.minute, 'text': text})
    else:
        text = generate_commentary('try_saved', {
            'team': atk_team['name'],
            'defender': random.choice(state.defending_players)['name'],
        })
        state.commentary.append({'minute': state.minute, 'text': text})
        state.swap_possession()


def _handle_conversion(state):
    """Handle a conversion attempt after a try."""
    kicker = state.get_kicker(state.possession)
    result = resolve_conversion(kicker)

    if result['outcome'] == 'scored':
        state.add_score(state.possession, 2, 'conversion')
        text = generate_commentary('conversion_good', {
            'kicker': kicker['name'],
            'team': state.attacking_team['name'],
        })
        state.events.append({
            'minute': state.minute,
            'type': 'conversion',
            'team': state.possession,
            'team_name': state.attacking_team['name'],
            'player': kicker['name'],
        })
    else:
        text = generate_commentary('conversion_missed', {
            'kicker': kicker['name'],
        })

    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_penalty_event(state):
    """Handle a penalty being awarded."""
    result = resolve_penalty(state.defending_players)
    def_team = state.defending_team
    atk_team = state.attacking_team

    # Who committed the penalty
    offender = random.choice(state.defending_players)
    text = generate_commentary('penalty_awarded', {
        'team': atk_team['name'],
        'offender': offender['name'],
        'offending_team': def_team['name'],
        'zone': ZONE_NAMES[state.zone],
    })
    state.commentary.append({'minute': state.minute, 'text': text})

    # Decision: kick at goal or kick for touch
    if state.zone >= 2:  # In range
        kicker = state.get_kicker(state.possession)
        if kicker.get('kicking', 50) > 55 or state.zone >= 3:
            _handle_penalty_kick(state)
        else:
            # Kick for touch
            if state.zone < 4:
                state.zone = min(4, state.zone + 1)
            text = f"{atk_team['name']} kick for touch and find a good lineout position."
            state.commentary.append({'minute': state.minute, 'text': text})
    else:
        # Too far, kick for touch
        state.zone = min(4, state.zone + 2)
        text = f"{atk_team['name']} kick for touch deep into opposition territory."
        state.commentary.append({'minute': state.minute, 'text': text})


def _handle_penalty_kick(state):
    """Handle a penalty kick at goal."""
    kicker = state.get_kicker(state.possession)
    kick_skill = kicker.get('kicking', 50)
    atk_team = state.attacking_team

    # Distance factor based on zone
    distance_mod = {0: -30, 1: -20, 2: -5, 3: 5, 4: 10}
    success_chance = kick_skill + distance_mod.get(state.zone, 0)

    if random.randint(1, 100) < success_chance:
        state.add_score(state.possession, 3, 'penalty')
        text = generate_commentary('penalty_kick_good', {
            'kicker': kicker['name'],
            'team': atk_team['name'],
        })
        state.events.append({
            'minute': state.minute,
            'type': 'penalty_goal',
            'team': state.possession,
            'team_name': atk_team['name'],
            'player': kicker['name'],
        })
        # Reset
        state.swap_possession()
        state.zone = 2
        state.phase = 0
    else:
        text = generate_commentary('penalty_kick_missed', {
            'kicker': kicker['name'],
        })
        state.swap_possession()
        state.zone = 1  # Opponent gets 22 dropout

    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_drop_goal_attempt(state):
    """Handle a drop goal attempt."""
    fly_half = None
    for p in state.attacking_players:
        if p.get('position') == 'fly_half':
            fly_half = p
            break
    if not fly_half:
        fly_half = state.get_kicker(state.possession)

    result = resolve_drop_goal(fly_half)
    atk_team = state.attacking_team

    if result['outcome'] == 'scored':
        state.add_score(state.possession, 3, 'drop_goal')
        text = generate_commentary('drop_goal_good', {
            'kicker': fly_half['name'],
            'team': atk_team['name'],
        })
        state.events.append({
            'minute': state.minute,
            'type': 'drop_goal',
            'team': state.possession,
            'team_name': atk_team['name'],
            'player': fly_half['name'],
        })
        state.swap_possession()
        state.zone = 2
    else:
        text = generate_commentary('drop_goal_missed', {
            'kicker': fly_half['name'],
        })
        state.swap_possession()
        state.zone = 1

    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_turnover(state):
    """Handle a turnover."""
    atk_team = state.attacking_team
    def_team = state.defending_team
    defender = random.choice(state.defending_players)

    text = generate_commentary('turnover', {
        'team': def_team['name'],
        'player': defender['name'],
        'attacking_team': atk_team['name'],
    })
    state.swap_possession()
    state.commentary.append({'minute': state.minute, 'text': text})


def _handle_card_event(state):
    """Handle a potential card event."""
    result = resolve_card_check(state.defending_players)

    if result['outcome'] == 'yellow':
        offender = random.choice(state.defending_players)
        def_team = state.defending_team
        state.add_card(
            'away' if state.possession == 'home' else 'home',
            'yellow', offender
        )
        text = generate_commentary('yellow_card', {
            'player': offender['name'],
            'team': def_team['name'],
        })
        state.events.append({
            'minute': state.minute,
            'type': 'yellow_card',
            'team': 'away' if state.possession == 'home' else 'home',
            'team_name': def_team['name'],
            'player': offender['name'],
        })
        state.commentary.append({'minute': state.minute, 'text': text})
    elif result['outcome'] == 'red':
        offender = random.choice(state.defending_players)
        def_team = state.defending_team
        state.add_card(
            'away' if state.possession == 'home' else 'home',
            'red', offender
        )
        text = generate_commentary('red_card', {
            'player': offender['name'],
            'team': def_team['name'],
        })
        state.events.append({
            'minute': state.minute,
            'type': 'red_card',
            'team': 'away' if state.possession == 'home' else 'home',
            'team_name': def_team['name'],
            'player': offender['name'],
        })
        state.commentary.append({'minute': state.minute, 'text': text})
    else:
        # No card, just a penalty
        _handle_penalty_event(state)
