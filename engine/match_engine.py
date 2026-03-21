"""Core match simulation engine for rugby union.

Factors in: player stats, tactical choices, style-player fit,
home advantage, fatigue accumulation, kick instructions,
offload frequency, ruck support, and playmaker influence.
"""
import random
from engine.commentary import generate_commentary
from engine.events import (
    ZONE_NAMES, EventType, resolve_scrum, resolve_lineout,
    resolve_phase_play, resolve_penalty, resolve_try_attempt,
    resolve_conversion, resolve_drop_goal, resolve_card_check,
    resolve_kick, resolve_penalty_kick,
)
from engine.tactics import (
    default_tactics, calculate_style_fit, apply_tactical_modifiers,
    KICK_TENDENCY, KICK_TYPE, KICK_ZONES, PLAY_OFF,
    OFFLOAD_FREQUENCY, RUCK_SUPPORT,
    ROLES_WITH_BALL, ROLES_WITHOUT_BALL, DROP_BEHIND_ROLES,
    default_role_for_position,
)


# ── Fatigue constants ──────────────────────────────────────────────
# Fatigue is 0-100 per side.  0 = fresh, 100 = exhausted.
BASE_FATIGUE_PER_MINUTE = 0.6          # ~48% by minute 80 for normal tempo
HIGH_TEMPO_FATIGUE_MULT = 1.35
CONTROL_TEMPO_FATIGUE_MULT = 0.75
HALF_TIME_RECOVERY = 15                # Flat recovery at half time
HOME_ADVANTAGE_BONUS = 3               # Stat points added to home side


class MatchState:
    """Tracks the state of a match in progress."""

    def __init__(self, home_team, away_team, home_players, away_players,
                 home_tactics=None, away_tactics=None):
        self.home_team = home_team
        self.away_team = away_team
        self.home_players = home_players
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
        self.possession = 'home'
        self.zone = 2  # 0=own22, 1=own_half, 2=midfield, 3=opp_half, 4=opp22
        self.phase = 0
        self.events = []
        self.commentary = []
        self.half = 1

        # Fatigue (0-100 per side)
        self.home_fatigue = 0.0
        self.away_fatigue = 0.0

        # Pre-computed style fits (0.0-1.0)
        self.home_fit = calculate_style_fit(home_players[:15], self.home_tactics)
        self.away_fit = calculate_style_fit(away_players[:15], self.away_tactics)

        # Sin bin tracking: {player_id: return_minute}
        self.sin_bin = {}

    # ── Context builders ───────────────────────────────────────────

    def _get_role(self, position, side, with_ball=True):
        """Get the assigned role config for a position."""
        tactics = self.home_tactics if side == 'home' else self.away_tactics
        role_dict = 'roles_with_ball' if with_ball else 'roles_without_ball'
        role_key = tactics.get(role_dict, {}).get(position)
        if not role_key:
            defaults = default_role_for_position(position)
            role_key = defaults[0] if with_ball else defaults[1]
        source = ROLES_WITH_BALL if with_ball else ROLES_WITHOUT_BALL
        return source.get(role_key, {})

    def _aggregate_role_modifier(self, side, with_ball=True):
        """Aggregate role modifiers across all 15 players."""
        players = self.home_players[:15] if side == 'home' else self.away_players[:15]
        total_fatigue_mod = 0.0
        total_carry_freq = 0.0
        total_pass_tend = 0.0
        total_tackle_agg = 0.0
        total_discipline_mod = 0.0
        total_overlap_risk = 0.0
        count = 0

        for p in players:
            pos = p.get('position', '')
            role = self._get_role(pos, side, with_ball)
            if not role:
                continue
            count += 1
            total_fatigue_mod += role.get('fatigue_mod', 0)
            if with_ball:
                total_carry_freq += role.get('carry_frequency', 0.2)
                total_pass_tend += role.get('pass_tendency', 0.3)
            else:
                total_tackle_agg += role.get('tackle_aggression', 0.5)
                total_discipline_mod += role.get('discipline_mod', 0)
                total_overlap_risk += role.get('overlap_risk', 0)

        n = max(count, 1)
        return {
            'avg_fatigue_mod': total_fatigue_mod / n,
            'avg_carry_freq': total_carry_freq / n,
            'avg_pass_tend': total_pass_tend / n,
            'avg_tackle_agg': total_tackle_agg / n,
            'avg_discipline_mod': total_discipline_mod / n,
            'avg_overlap_risk': total_overlap_risk / n,
        }

    def _build_atk_context(self):
        """Build the attacking context dict passed to event resolvers."""
        side = self.possession
        tactics = self.home_tactics if side == 'home' else self.away_tactics
        fatigue = self.home_fatigue if side == 'home' else self.away_fatigue
        fit = self.home_fit if side == 'home' else self.away_fit

        # Play-off bonus: how good is the key playmaker
        play_off_cfg = PLAY_OFF.get(tactics.get('play_off', 'fly_half'), {})
        play_off_bonus = self._calc_play_off_bonus(side, play_off_cfg)

        # Offload settings
        offload_cfg = OFFLOAD_FREQUENCY.get(
            tactics.get('offload_frequency', 'medium'), {})

        # Ruck support
        ruck_cfg = RUCK_SUPPORT.get(tactics.get('ruck_support', 'normal'), {})

        # Position role aggregates
        role_mods = self._aggregate_role_modifier(side, with_ball=True)

        # Check for flair variance (fly half on full flair)
        flair_variance = 0
        fly_half_role = self._get_role('fly_half', side, with_ball=True)
        if fly_half_role.get('flair_variance'):
            flair_variance = fly_half_role['flair_variance']

        return {
            'home_bonus': HOME_ADVANTAGE_BONUS if side == 'home' else 0,
            'fatigue': fatigue,
            'style_fit': fit,
            'play_off_bonus': play_off_bonus,
            'offload_chance': offload_cfg.get('offload_chance', 0.15),
            'offload_turnover_mod': offload_cfg.get('turnover_risk_mod', 0),
            'offload_big_play_mod': offload_cfg.get('big_play_mod', 0),
            'ruck_speed_mod': ruck_cfg.get('ruck_speed_mod', 0),
            # Position role data
            'avg_carry_freq': role_mods['avg_carry_freq'],
            'avg_pass_tend': role_mods['avg_pass_tend'],
            'role_fatigue_mod': role_mods['avg_fatigue_mod'],
            'flair_variance': flair_variance,
        }

    def _build_def_context(self):
        """Build the defending context dict."""
        side = 'away' if self.possession == 'home' else 'home'
        tactics = self.home_tactics if side == 'home' else self.away_tactics
        fatigue = self.home_fatigue if side == 'home' else self.away_fatigue
        fit = self.home_fit if side == 'home' else self.away_fit

        # Position role aggregates (defence)
        role_mods = self._aggregate_role_modifier(side, with_ball=False)

        # Drop-behind system — how many players covering the backfield
        drop_behind = tactics.get('drop_behind', [{'position': 'fullback', 'role': 'full_cover'}])
        kick_cover_total = 0.0
        for db in drop_behind:
            db_role = DROP_BEHIND_ROLES.get(db.get('role', 'full_cover'), {})
            kick_cover_total += db_role.get('kick_cover', 0.2)

        # Jackal chance from any jacklers in the pack
        jackal_chance = 0.0
        players = self.home_players[:15] if side == 'home' else self.away_players[:15]
        for p in players:
            pos = p.get('position', '')
            role = self._get_role(pos, side, with_ball=False)
            if role.get('jackal_chance', 0) > 0:
                # Scale by player's actual tackling/game_sense
                player_skill = (p.get('tackling', 50) + p.get('game_sense', 50)) / 200
                jackal_chance += role['jackal_chance'] * player_skill

        return {
            'home_bonus': HOME_ADVANTAGE_BONUS if side == 'home' else 0,
            'fatigue': fatigue,
            'style_fit': fit,
            'avg_tackle_agg': role_mods['avg_tackle_agg'],
            'avg_discipline_mod': role_mods['avg_discipline_mod'],
            'avg_overlap_risk': role_mods['avg_overlap_risk'],
            'kick_cover': kick_cover_total,
            'jackal_chance': jackal_chance,
            'role_fatigue_mod': role_mods['avg_fatigue_mod'],
        }

    def _calc_play_off_bonus(self, side, play_off_cfg):
        """How much the designated playmaker boosts attack."""
        players = self.home_players[:15] if side == 'home' else self.away_players[:15]
        key_pos = play_off_cfg.get('key_position', 'fly_half')
        stat_weights = play_off_cfg.get('stat_weights', {})

        key_player = None
        for p in players:
            if p.get('position') == key_pos:
                key_player = p
                break

        if not key_player or not stat_weights:
            return 0

        score = sum(key_player.get(s, 50) * w for s, w in stat_weights.items())
        # Normalise to roughly -5 to +8
        return (score - 50) * 0.15

    # ── Properties ─────────────────────────────────────────────────

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

    def get_positional_kicker(self, side, position):
        """Get a kicker by position (e.g. scrum_half for box kicks)."""
        players = self.home_players[:15] if side == 'home' else self.away_players[:15]
        for p in players:
            if p.get('position') == position:
                return p
        return self.get_kicker(side)

    def get_avg_stat(self, players, stat, positions=None):
        if positions:
            filtered = [p for p in players if p.get('position', '') in positions]
            if not filtered:
                filtered = players
        else:
            filtered = players
        return sum(p.get(stat, 50) for p in filtered) / len(filtered)

    def swap_possession(self):
        self.possession = 'away' if self.possession == 'home' else 'home'
        self.zone = 4 - self.zone
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
        returned = []
        for pid, return_min in list(self.sin_bin.items()):
            if self.minute >= return_min:
                del self.sin_bin[pid]
                returned.append(pid)
        return returned

    # ── Fatigue ────────────────────────────────────────────────────

    def tick_fatigue(self):
        """Advance fatigue for one minute of play."""
        for side in ('home', 'away'):
            tactics = self.home_tactics if side == 'home' else self.away_tactics
            tempo = tactics.get('tempo', 'normal')
            ruck_cfg = RUCK_SUPPORT.get(tactics.get('ruck_support', 'normal'), {})

            # Base drain
            drain = BASE_FATIGUE_PER_MINUTE

            # Tempo modifier
            if tempo == 'high':
                drain *= HIGH_TEMPO_FATIGUE_MULT
            elif tempo == 'control':
                drain *= CONTROL_TEMPO_FATIGUE_MULT

            # Ruck support modifier
            stamina_save = ruck_cfg.get('stamina_save', 0)
            drain *= (1 - stamina_save)

            # Position role fatigue modifier (aggressive roles drain faster)
            role_mods = self._aggregate_role_modifier(side, with_ball=True)
            drain *= (1 + role_mods['avg_fatigue_mod'])

            # Squad stamina reduces fatigue accumulation
            players = self.home_players[:15] if side == 'home' else self.away_players[:15]
            avg_stamina = sum(p.get('stamina', 50) for p in players) / max(len(players), 1)
            stamina_factor = 1.0 - (avg_stamina - 50) / 200  # 50 stam=1.0, 90 stam=0.8
            drain *= max(0.5, stamina_factor)

            if side == 'home':
                self.home_fatigue = min(100, self.home_fatigue + drain)
            else:
                self.away_fatigue = min(100, self.away_fatigue + drain)

    def half_time_recovery(self):
        """Partial recovery at half time."""
        self.home_fatigue = max(0, self.home_fatigue - HALF_TIME_RECOVERY)
        self.away_fatigue = max(0, self.away_fatigue - HALF_TIME_RECOVERY)

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


# ── Main Entry Point ───────────────────────────────────────────────

def simulate_match(home_team, away_team, home_players, away_players,
                   home_tactics=None, away_tactics=None, fixture_id=None):
    """Simulate a full 80-minute rugby match."""
    state = MatchState(home_team, away_team, home_players, away_players,
                       home_tactics, away_tactics)

    # Kickoff
    state.possession = 'away'
    state.zone = 2
    state.commentary.append({
        'minute': 0,
        'text': f"Kick-off at {home_team['name']}'s {home_team.get('stadium', 'ground')}! "
                f"{home_team['name']} vs {away_team['name']}."
    })

    for minute in range(1, 81):
        state.minute = minute

        # Half time
        if minute == 41 and state.half == 1:
            state.half = 2
            state.half_time_recovery()
            state.possession = 'home'
            state.zone = 2
            state.phase = 0
            state.commentary.append({
                'minute': 40,
                'text': f"HALF TIME: {home_team['name']} {state.home_score} - "
                        f"{state.away_score} {away_team['name']}"
            })

        # Sin bin returns
        returned = state.check_sin_bin_returns()
        for pid in returned:
            state.commentary.append({
                'minute': minute,
                'text': "A player returns from the sin bin."
            })

        # Fatigue ticks every minute
        state.tick_fatigue()

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


# ── Minute-by-Minute Simulation ───────────────────────────────────

def _simulate_minute(state):
    """Simulate one minute of play.

    Event probabilities are influenced by:
    - Zone on the pitch
    - Tactics (kick tendency, kick zones, tempo)
    - Fatigue (tired teams make more errors / kick more)
    """
    tactics = state.home_tactics if state.possession == 'home' else state.away_tactics
    event_roll = random.random()

    # ── Dynamic kick probability ──────────────────────────────────
    # Base kick chance varies by zone
    base_kick = {0: 0.30, 1: 0.22, 2: 0.15, 3: 0.08, 4: 0.03}
    kick_chance = base_kick.get(state.zone, 0.15)

    # Kick tendency modifier
    kick_tend = KICK_TENDENCY.get(tactics.get('kick_tendency', 'sometimes'), {})
    kick_chance += kick_chance * kick_tend.get('kick_chance_mod', 0)

    # Kick zones — if current zone is not in the active kick zones, reduce drastically
    kick_zones_cfg = KICK_ZONES.get(tactics.get('kick_zones', 'own_half'), {})
    active_zones = kick_zones_cfg.get('active_zones', [0, 1])
    if state.zone not in active_zones:
        kick_chance *= 0.15  # Almost never kick from non-active zones

    # Fatigue increases kicking tendency (tired legs = kick it away)
    fatigue = state.home_fatigue if state.possession == 'home' else state.away_fatigue
    kick_chance += (fatigue / 100) * 0.08

    kick_chance = max(0.02, min(0.50, kick_chance))

    # ── Event distribution ────────────────────────────────────────
    if state.zone <= 1:
        # Own territory
        if event_roll < kick_chance:
            _handle_kick(state)
        elif event_roll < kick_chance + 0.25:
            _handle_phase_play(state)
        elif event_roll < kick_chance + 0.40:
            _handle_set_piece(state, 'scrum')
        elif event_roll < kick_chance + 0.50:
            _handle_set_piece(state, 'lineout')
        elif event_roll < kick_chance + 0.60:
            _handle_turnover(state)
        else:
            _handle_penalty_event(state)

    elif state.zone == 2:
        # Midfield
        if event_roll < kick_chance:
            _handle_kick(state)
        elif event_roll < kick_chance + 0.32:
            _handle_phase_play(state)
        elif event_roll < kick_chance + 0.42:
            _handle_set_piece(state, 'scrum')
        elif event_roll < kick_chance + 0.52:
            _handle_set_piece(state, 'lineout')
        elif event_roll < kick_chance + 0.64:
            _handle_turnover(state)
        elif event_roll < kick_chance + 0.74:
            _handle_penalty_event(state)
        else:
            _handle_card_event(state)

    else:
        # Opposition territory (zones 3-4)
        try_chance = 0.15 if state.zone == 4 else 0.10
        if event_roll < kick_chance:
            _handle_kick(state)
        elif event_roll < kick_chance + 0.25:
            _handle_phase_play(state)
        elif event_roll < kick_chance + 0.25 + try_chance:
            _handle_try_opportunity(state)
        elif event_roll < kick_chance + 0.35 + try_chance:
            _handle_set_piece(state, 'scrum')
        elif event_roll < kick_chance + 0.45 + try_chance:
            _handle_set_piece(state, 'lineout')
        elif event_roll < kick_chance + 0.55 + try_chance:
            _handle_penalty_event(state)
        elif event_roll < kick_chance + 0.62 + try_chance:
            _handle_turnover(state)
        elif event_roll < kick_chance + 0.68 + try_chance:
            _handle_drop_goal_attempt(state)
        else:
            _handle_card_event(state)


# ── Event Handlers ─────────────────────────────────────────────────

def _handle_phase_play(state):
    """Handle a phase of attacking play."""
    atk_ctx = state._build_atk_context()
    def_ctx = state._build_def_context()

    result = resolve_phase_play(
        state.attacking_players, state.defending_players,
        state.zone, state.phase, atk_ctx, def_ctx
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
    """Handle a tactical kick based on kick type instructions."""
    tactics = state.home_tactics if state.possession == 'home' else state.away_tactics
    kick_type_key = tactics.get('kick_type', 'touch_finder')
    kick_type_cfg = KICK_TYPE.get(kick_type_key, KICK_TYPE['touch_finder'])

    # Get the right kicker based on kick type
    primary_pos = kick_type_cfg.get('primary_kicker', 'fly_half')
    kicker = state.get_positional_kicker(state.possession, primary_pos)

    atk_ctx = state._build_atk_context()
    def_ctx = state._build_def_context()
    result = resolve_kick(kicker, kick_type_cfg, atk_ctx, def_ctx)

    atk_team = state.attacking_team

    if result['outcome'] == 'regather':
        # Kick chase wins the ball back — attacking team keeps possession!
        territory = result.get('territory_gain', 1)
        for _ in range(territory):
            if state.zone < 4:
                state.zone += 1
        text = f"Brilliant kick chase! {kicker['name']} puts it up and {atk_team['name']} regather in the {ZONE_NAMES[state.zone]}!"
    elif result['outcome'] == 'good':
        state.swap_possession()
        territory = result.get('territory_gain', 1)
        for _ in range(territory):
            if state.zone > 0:
                state.zone -= 1
        text = generate_commentary('kick_good', {
            'team': atk_team['name'],
            'kicker': kicker['name'],
            'zone': ZONE_NAMES[state.zone],
        })
    elif result['outcome'] == 'turnover':
        # Kick goes wrong — opponent counters from good position
        state.swap_possession()
        if state.zone < 4:
            state.zone += 1
        text = generate_commentary('kick_poor', {
            'team': atk_team['name'],
            'kicker': kicker['name'],
        })
        text += f" {state.attacking_team['name']} counter-attack from a great position!"
    else:
        # Poor kick
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

    atk_ctx = state._build_atk_context()
    def_ctx = state._build_def_context()

    if set_piece_type == 'scrum':
        result = resolve_scrum(atk_forwards, def_forwards, atk_ctx, def_ctx)
    else:
        result = resolve_lineout(atk_forwards, def_forwards, atk_ctx, def_ctx)

    atk_team = state.attacking_team
    text = generate_commentary(set_piece_type, {
        'team': atk_team['name'],
        'result': result['outcome'],
        'zone': ZONE_NAMES[state.zone],
    })

    if result['outcome'] == 'won':
        state.phase = 0
        if state.zone < 4:
            state.zone += 1
    elif result['outcome'] == 'penalty_won':
        state.phase = 0
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
    atk_ctx = state._build_atk_context()
    def_ctx = state._build_def_context()

    result = resolve_try_attempt(
        state.attacking_players, state.defending_players, state.zone,
        atk_ctx, def_ctx
    )

    atk_team = state.attacking_team

    # Pick a likely try scorer based on position
    scorer = _pick_try_scorer(state.attacking_players)

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

        _handle_conversion(state)

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


def _pick_try_scorer(players):
    """Weighted random selection for try scorer — wings/centres more likely."""
    weights = {
        'left_wing': 5, 'right_wing': 5, 'fullback': 3,
        'inside_centre': 3, 'outside_centre': 3,
        'number_eight': 2, 'scrum_half': 2, 'fly_half': 2,
        'blindside_flanker': 1, 'openside_flanker': 1,
        'hooker': 1, 'lock_4': 1, 'lock_5': 1,
        'loosehead_prop': 0.5, 'tighthead_prop': 0.5,
    }
    weighted = [(p, weights.get(p.get('position', ''), 1)) for p in players]
    total = sum(w for _, w in weighted)
    r = random.uniform(0, total)
    cumulative = 0
    for p, w in weighted:
        cumulative += w
        if r <= cumulative:
            return p
    return random.choice(players)


def _handle_conversion(state):
    """Handle a conversion attempt after a try."""
    kicker = state.get_kicker(state.possession)
    atk_ctx = state._build_atk_context()
    result = resolve_conversion(kicker, atk_ctx)

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

    offender = random.choice(state.defending_players)
    text = generate_commentary('penalty_awarded', {
        'team': atk_team['name'],
        'offender': offender['name'],
        'offending_team': def_team['name'],
        'zone': ZONE_NAMES[state.zone],
    })
    state.commentary.append({'minute': state.minute, 'text': text})

    # Decision: kick at goal or kick for touch
    if state.zone >= 2:
        kicker = state.get_kicker(state.possession)
        if kicker.get('kicking', 50) > 55 or state.zone >= 3:
            _handle_penalty_kick(state)
        else:
            if state.zone < 4:
                state.zone = min(4, state.zone + 1)
            text = f"{atk_team['name']} kick for touch and find a good lineout position."
            state.commentary.append({'minute': state.minute, 'text': text})
    else:
        state.zone = min(4, state.zone + 2)
        text = f"{atk_team['name']} kick for touch deep into opposition territory."
        state.commentary.append({'minute': state.minute, 'text': text})


def _handle_penalty_kick(state):
    """Handle a penalty kick at goal."""
    kicker = state.get_kicker(state.possession)
    atk_team = state.attacking_team
    atk_ctx = state._build_atk_context()

    result = resolve_penalty_kick(kicker, state.zone, atk_ctx)

    if result['outcome'] == 'scored':
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
        state.swap_possession()
        state.zone = 2
        state.phase = 0
    else:
        text = generate_commentary('penalty_kick_missed', {
            'kicker': kicker['name'],
        })
        state.swap_possession()
        state.zone = 1

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

    atk_ctx = state._build_atk_context()
    result = resolve_drop_goal(fly_half, atk_ctx)
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
    def_ctx = state._build_def_context()
    result = resolve_card_check(state.defending_players, def_ctx)

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
        _handle_penalty_event(state)
