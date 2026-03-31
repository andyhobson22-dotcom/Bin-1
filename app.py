"""Rugby Manager Game — Flask Application."""
import json
import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash, session

from config import Config
from database import init_db, get_db
from models.player import (
    get_team_players, get_player, get_overall_rating, get_position_ratings,
    POSITIONS, STAT_GROUPS, inject_compat_stats,
)
from models.team import get_all_teams, get_team, get_player_team, set_player_team
from models.match import get_match
from models.league import get_standings, get_fixtures, get_game_state
from models.finance import get_team_finances
from engine.tactics import get_all_tactical_options, default_tactics, calculate_style_fit, get_fit_description
from game.season import (
    init_new_game, advance_round, get_current_round_fixtures,
    get_player_fixture, play_single_match, generate_fixtures,
)
from game.training import (
    TRAINING_FOCUSES, get_training, set_training, apply_weekly_training,
)
from game.transfers import get_transfer_targets, make_transfer, get_player_value
from game.save_load import save_game, load_game, list_saves


app = Flask(__name__)
app.config.from_object(Config)


def _load_initial_data():
    """Load teams and players from JSON into the database."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    with open(os.path.join(data_dir, 'teams.json'), 'r') as f:
        teams = json.load(f)

    # Check if we need to generate players
    players_file = os.path.join(data_dir, 'players.json')
    if not os.path.exists(players_file):
        from data.generate_players import generate_all_data
        random.seed(42)
        generate_all_data()

    with open(players_file, 'r') as f:
        all_players = json.load(f)

    db = get_db()

    # Check if data already loaded
    existing = db.execute("SELECT COUNT(*) as c FROM teams").fetchone()
    if existing['c'] > 0:
        db.close()
        return

    # Insert teams
    for team in teams:
        db.execute("""
            INSERT INTO teams (name, city, stadium, stadium_capacity, budget,
                             wage_budget, reputation, home_color, away_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (team['name'], team['city'], team['stadium'],
              team['stadium_capacity'], team['budget'], team['wage_budget'],
              team['reputation'], team['home_color'], team['away_color']))

    db.commit()

    # Get team IDs
    db_teams = db.execute("SELECT id, name FROM teams").fetchall()
    team_id_map = {t['name']: t['id'] for t in db_teams}

    # Insert players
    for team_name, players in all_players.items():
        team_id = team_id_map.get(team_name)
        if not team_id:
            continue
        for p in players:
            sec_pos = json.dumps(p.get('secondary_positions', []))
            db.execute("""
                INSERT INTO players (name, age, team_id, position, secondary_positions,
                    nationality, height, weight,
                    stopping_power, explosiveness, leg_drive, pace, acceleration,
                    agility, strength,
                    aggression, composure, concentration, awareness, running_lines,
                    discipline, tenacity, scanning, positioning,
                    long_passing, handling, high_ball, offload, tackling, rucking,
                    mauling, jackling, grubber, chipping, box_kicking, stepping,
                    short_passing,
                    goal_kicking, scrum_drive, scrum_tech, touch_finder, jumping, lifting,
                    potential, form, morale, fitness, wage, contract_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?)
            """, (
                p['name'], p['age'], team_id, p['position'], sec_pos,
                p.get('nationality', 'England'),
                p.get('height', 183),
                p.get('weight', 95),
                # Physical
                p.get('stopping_power', 50), p.get('explosiveness', 50),
                p.get('leg_drive', 50), p.get('pace', 50),
                p.get('acceleration', 50), p.get('agility', 50),
                p.get('strength', 50),
                # Mental
                p.get('aggression', 50), p.get('composure', 50),
                p.get('concentration', 50), p.get('awareness', 50),
                p.get('running_lines', 50), p.get('discipline', 50),
                p.get('tenacity', 50), p.get('scanning', 50),
                p.get('positioning', 50),
                # Technical
                p.get('long_passing', 50), p.get('handling', 50),
                p.get('high_ball', 50), p.get('offload', 50),
                p.get('tackling', 50), p.get('rucking', 50),
                p.get('mauling', 50), p.get('jackling', 50),
                p.get('grubber', 50), p.get('chipping', 50),
                p.get('box_kicking', 50), p.get('stepping', 50),
                p.get('short_passing', 50),
                # Set Piece
                p.get('goal_kicking', 50), p.get('scrum_drive', 50),
                p.get('scrum_tech', 50), p.get('touch_finder', 50),
                p.get('jumping', 50), p.get('lifting', 50),
                # Meta
                p.get('potential', 60), p.get('form', 50),
                p.get('morale', 70), p.get('fitness', 100),
                p.get('wage', 5000), p.get('contract_end', 2),
            ))

    db.commit()
    db.close()


# --- Context processor ---
@app.context_processor
def inject_game_state():
    """Inject game state into all templates."""
    state = get_game_state()
    return {
        'game_state': state,
        'positions': POSITIONS,
    }


# --- Routes ---

@app.route('/')
def index():
    """Landing page — setup or dashboard."""
    state = get_game_state()
    if state:
        return redirect(url_for('dashboard'))
    teams = get_all_teams()
    if not teams:
        # First run — initialize data
        init_db()
        _load_initial_data()
        teams = get_all_teams()
    return render_template('setup.html', teams=teams)


@app.route('/new-game')
def new_game():
    """Start a fresh game (re-initialize)."""
    # Remove existing database
    if os.path.exists(Config.DATABASE):
        os.remove(Config.DATABASE)
    init_db()
    _load_initial_data()
    teams = get_all_teams()
    return render_template('setup.html', teams=teams)


@app.route('/select-team/<int:team_id>')
def select_team(team_id):
    """Select a team and start the game."""
    set_player_team(team_id)
    init_new_game(team_id)
    flash(f"Welcome to {get_team(team_id)['name']}! Your management career begins.", 'success')
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    state = get_game_state()
    standings = get_standings(state['season'])
    round_fixtures = get_current_round_fixtures()
    player_fixture = get_player_fixture()

    all_played = all(f.get('played') or f.get('match_id') for f in round_fixtures)

    return render_template('dashboard.html',
                           team=team,
                           standings=standings,
                           round_fixtures=round_fixtures,
                           player_fixture=player_fixture,
                           all_played=all_played)


@app.route('/squad')
def squad():
    """Squad management page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    players = get_team_players(team['id'])
    for p in players:
        p['overall'] = get_overall_rating(p)

    return render_template('squad.html', team=team, players=players)


@app.route('/player/<int:player_id>')
def player_profile(player_id):
    """Individual player profile."""
    player = get_player(player_id)
    if not player:
        flash('Player not found.', 'error')
        return redirect(url_for('squad'))

    player['overall'] = get_overall_rating(player)
    team = get_team(player['team_id'])
    team_name = team['name'] if team else 'Free Agent'
    player_value = get_player_value(player)
    position_ratings = get_position_ratings(player)

    return render_template('player_profile.html',
                           player=player,
                           team_name=team_name,
                           team=team,
                           player_value=player_value,
                           position_ratings=position_ratings,
                           stat_groups=STAT_GROUPS)


@app.route('/tactics')
def tactics():
    """Tactics page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    tactical_options = get_all_tactical_options()
    current_tactics = session.get('tactics', default_tactics())

    # Calculate style-player fit
    players = get_team_players(team['id'])
    fit_score = calculate_style_fit(players[:15], current_tactics)
    fit_label = get_fit_description(fit_score)
    fit_pct = int(fit_score * 100)

    return render_template('tactics.html',
                           team=team,
                           tactical_options=tactical_options,
                           current_tactics=current_tactics,
                           fit_score=fit_pct,
                           fit_label=fit_label,
                           positions=POSITIONS)


@app.route('/save-tactics', methods=['POST'])
def save_tactics():
    """Save tactical selections."""
    tactics = {
        # Strategy
        'attacking_style': request.form.get('attacking_style', 'balanced'),
        'kicking_game': request.form.get('kicking_game', 'balanced'),
        'defensive_style': request.form.get('defensive_style', 'drift'),
        'set_piece': request.form.get('set_piece', 'balanced'),
        'tempo': request.form.get('tempo', 'normal'),
        # With-ball team instructions
        'kick_tendency': request.form.get('kick_tendency', 'sometimes'),
        'kick_type': request.form.get('kick_type', 'touch_finder'),
        'kick_zones': request.form.get('kick_zones', 'own_half'),
        'play_off': request.form.get('play_off', 'fly_half'),
        'offload_frequency': request.form.get('offload_frequency', 'medium'),
        'ruck_support': request.form.get('ruck_support', 'normal'),
    }

    # Position roles (with ball)
    roles_wb = {}
    for pos_key in POSITIONS:
        val = request.form.get(f'role_wb_{pos_key}')
        if val:
            roles_wb[pos_key] = val
    tactics['roles_with_ball'] = roles_wb

    # Position roles (without ball)
    roles_wob = {}
    for pos_key in POSITIONS:
        val = request.form.get(f'role_wob_{pos_key}')
        if val:
            roles_wob[pos_key] = val
    tactics['roles_without_ball'] = roles_wob

    # Drop behind system
    drop_behind = []
    for i in range(3):
        pos = request.form.get(f'drop_pos_{i}')
        role = request.form.get(f'drop_role_{i}')
        if pos and role:
            drop_behind.append({'position': pos, 'role': role})
    if not drop_behind:
        drop_behind = [{'position': 'fullback', 'role': 'full_cover'}]
    tactics['drop_behind'] = drop_behind

    session['tactics'] = tactics
    flash('Tactics saved.', 'success')
    return redirect(url_for('tactics'))


@app.route('/match')
def play_match_page():
    """Match day page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    fixture = get_player_fixture()
    home_players = []
    away_players = []

    if fixture and not fixture.get('played'):
        home_players = get_team_players(fixture['home_team_id'])
        away_players = get_team_players(fixture['away_team_id'])
        for p in home_players + away_players:
            p['overall'] = get_overall_rating(p)

    return render_template('match.html',
                           team=team,
                           fixture=fixture,
                           home_players=home_players,
                           away_players=away_players)


@app.route('/play-match', methods=['POST'])
def play_match_action():
    """Simulate the player's match."""
    fixture_id = request.form.get('fixture_id', type=int)
    if not fixture_id:
        flash('No fixture specified.', 'error')
        return redirect(url_for('dashboard'))

    player_tactics = session.get('tactics', default_tactics())
    match_id = play_single_match(fixture_id, player_tactics=player_tactics)
    if match_id:
        return redirect(url_for('match_result', match_id=match_id))
    else:
        flash('Could not play match.', 'error')
        return redirect(url_for('dashboard'))


@app.route('/match-result/<int:match_id>')
def match_result(match_id):
    """Display match result and commentary."""
    match = get_match(match_id)
    if not match:
        flash('Match not found.', 'error')
        return redirect(url_for('dashboard'))

    home_team = get_team(match['home_team_id'])
    away_team = get_team(match['away_team_id'])

    return render_template('match_result.html',
                           match=match,
                           home_team=home_team,
                           away_team=away_team)


@app.route('/table')
def league_table():
    """League table page."""
    state = get_game_state()
    if not state:
        return redirect(url_for('index'))

    standings = get_standings(state['season'])
    team = get_player_team()

    return render_template('league_table.html',
                           standings=standings,
                           player_team_id=team['id'] if team else None)


@app.route('/fixtures')
def fixtures():
    """All fixtures page."""
    state = get_game_state()
    if not state:
        return redirect(url_for('index'))

    all_fixtures = get_fixtures(state['season'])
    team = get_player_team()

    return render_template('fixtures.html',
                           all_fixtures=all_fixtures,
                           player_team_id=team['id'] if team else None)


@app.route('/training')
def training_page():
    """Training page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    current_training = get_training(team['id'])
    updates = session.pop('training_updates', None)

    return render_template('training.html',
                           team=team,
                           training_focuses=TRAINING_FOCUSES,
                           current_training=current_training,
                           updates=updates)


@app.route('/set-training', methods=['POST'])
def set_training_focus():
    """Set training focus."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    focus = request.form.get('focus', 'balanced')
    set_training(team['id'], focus)
    flash(f'Training focus set to: {TRAINING_FOCUSES[focus]["name"]}', 'success')
    return redirect(url_for('training_page'))


@app.route('/transfers')
def transfers_page():
    """Transfer market page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    selected_position = request.args.get('position', '')
    targets = get_transfer_targets(team['id'], selected_position or None)

    # Add team names to targets
    for t in targets:
        t_team = get_team(t['team_id'])
        t['team_name'] = t_team['name'] if t_team else 'Unknown'

    return render_template('transfers.html',
                           team=team,
                           targets=targets,
                           selected_position=selected_position)


@app.route('/make-transfer', methods=['POST'])
def make_transfer_action():
    """Execute a transfer."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    player_id = request.form.get('player_id', type=int)
    from_team_id = request.form.get('from_team_id', type=int)
    fee = request.form.get('fee', type=int)

    if not all([player_id, from_team_id, fee]):
        flash('Invalid transfer details.', 'error')
        return redirect(url_for('transfers_page'))

    if fee > team['budget']:
        flash('Insufficient budget for this transfer.', 'error')
        return redirect(url_for('transfers_page'))

    player = get_player(player_id)
    make_transfer(player_id, from_team_id, team['id'], fee)
    flash(f"Signed {player['name']} for £{fee:,}!", 'success')
    return redirect(url_for('transfers_page'))


@app.route('/finances')
def finances():
    """Club finances page."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    finance = get_team_finances(team['id'])
    players = get_team_players(team['id'])

    return render_template('finances.html',
                           team=team,
                           finance=finance,
                           players=players)


@app.route('/advance')
def advance_week():
    """Advance to next round — simulate all matches."""
    team = get_player_team()
    if not team:
        return redirect(url_for('index'))

    # Apply training for player's team
    updates = apply_weekly_training(team['id'])
    if updates:
        session['training_updates'] = [u for u in updates
                                       if u['type'] in ('injury', 'recovery')]

    # Simulate all matches for this round
    results = advance_round()
    if results:
        player_match = None
        for r in results:
            if r.get('fixture_id'):
                # Check if this involves the player's team
                db = get_db()
                f = db.execute("SELECT * FROM fixtures WHERE id = ?",
                               (r['fixture_id'],)).fetchone()
                db.close()
                if f and (f['home_team_id'] == team['id'] or
                          f['away_team_id'] == team['id']):
                    player_match = r

        if player_match:
            flash(f"Round complete! Your result: {player_match['home_team']} "
                  f"{player_match['home_score']} - {player_match['away_score']} "
                  f"{player_match['away_team']}", 'info')
        else:
            flash('Round complete! All matches simulated.', 'info')
    else:
        flash('Season complete!', 'success')

    return redirect(url_for('dashboard'))


@app.route('/save')
def save_game_route():
    """Save the game."""
    save_game('autosave')
    flash('Game saved!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/load')
def load_game_route():
    """Load a saved game."""
    if load_game('autosave'):
        flash('Game loaded!', 'success')
    else:
        flash('No save file found.', 'error')
    return redirect(url_for('dashboard'))


# --- Startup ---

def setup_app():
    """Initialize the app on first run."""
    if not os.path.exists(Config.DATABASE):
        init_db()
        _load_initial_data()


if __name__ == '__main__':
    setup_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
