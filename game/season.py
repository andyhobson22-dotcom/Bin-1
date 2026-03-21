"""Season management — fixtures, advancing weeks, playoffs."""
import random
from database import get_db
from models.league import update_standings
from models.match import save_match
from models.player import get_team_players
from models.team import get_team
from engine.match_engine import simulate_match


def generate_fixtures(season=1):
    """Generate a full round-robin fixture list for the season.

    10 teams = 9 rounds home, 9 rounds away = 18 rounds total.
    Each round has 5 matches.
    """
    db = get_db()
    teams = db.execute("SELECT id FROM teams ORDER BY id").fetchall()
    team_ids = [t['id'] for t in teams]
    n = len(team_ids)

    fixtures = []

    # Round-robin scheduling
    # Use the circle method for balanced scheduling
    teams_list = team_ids[:]
    if n % 2 == 1:
        teams_list.append(None)  # Bye
        n += 1

    rounds_home = []
    rotation = teams_list[1:]

    for round_num in range(n - 1):
        round_matches = []
        first = teams_list[0]
        rotated = [first] + rotation

        for i in range(n // 2):
            home = rotated[i]
            away = rotated[n - 1 - i]
            if home is not None and away is not None:
                round_matches.append((home, away))

        rounds_home.append(round_matches)
        # Rotate
        rotation = rotation[1:] + rotation[:1]

    # First half of season: as generated
    for round_num, matches in enumerate(rounds_home, 1):
        for home, away in matches:
            fixtures.append((season, round_num, home, away))

    # Second half: reverse home/away
    for round_num, matches in enumerate(rounds_home, len(rounds_home) + 1):
        for home, away in matches:
            fixtures.append((season, round_num, away, home))

    # Insert into database
    db.executemany(
        "INSERT INTO fixtures (season, round, home_team_id, away_team_id) VALUES (?, ?, ?, ?)",
        fixtures
    )

    # Initialize standings
    for tid in team_ids:
        db.execute(
            "INSERT INTO standings (season, team_id) VALUES (?, ?)",
            (season, tid)
        )

    db.commit()
    db.close()

    return len(fixtures)


def init_new_game(player_team_id):
    """Initialize a new game state."""
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO game_state (id, season, current_round, total_rounds,
                                           player_team_id, phase)
        VALUES (1, 1, 1, 18, ?, 'regular_season')
    """, (player_team_id,))

    # Initialize training for all teams
    teams = db.execute("SELECT id FROM teams").fetchall()
    for team in teams:
        db.execute("""
            INSERT OR REPLACE INTO training (team_id, focus, intensity)
            VALUES (?, 'balanced', 'medium')
        """, (team['id'],))

    db.commit()
    db.close()

    generate_fixtures(season=1)


def advance_round():
    """Play all matches in the current round and advance."""
    db = get_db()
    state = db.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    if not state:
        db.close()
        return None

    current_round = state['current_round']
    season = state['season']
    total_rounds = state['total_rounds']

    # Get unplayed fixtures for this round
    fixtures = db.execute("""
        SELECT * FROM fixtures
        WHERE season = ? AND round = ? AND played = 0
    """, (season, current_round)).fetchall()

    results = []
    for fixture in fixtures:
        home_team = get_team(fixture['home_team_id'])
        away_team = get_team(fixture['away_team_id'])
        home_players = get_team_players(fixture['home_team_id'])
        away_players = get_team_players(fixture['away_team_id'])

        if not home_players or not away_players:
            continue

        # Simulate the match
        result = simulate_match(
            home_team, away_team,
            home_players[:15], away_players[:15],
            fixture_id=fixture['id']
        )

        # Save match result
        match_id = save_match(result)

        # Update standings
        update_standings(
            season, fixture['home_team_id'], fixture['away_team_id'],
            result['home_score'], result['away_score'],
            result['home_tries'], result['away_tries']
        )

        results.append({
            'match_id': match_id,
            'home_team': home_team['name'],
            'away_team': away_team['name'],
            'home_score': result['home_score'],
            'away_score': result['away_score'],
            'fixture_id': fixture['id'],
        })

    # Advance to next round
    if current_round < total_rounds:
        db.execute("UPDATE game_state SET current_round = ? WHERE id = 1",
                   (current_round + 1,))
    else:
        # Season complete — move to playoffs
        db.execute("UPDATE game_state SET phase = 'playoffs' WHERE id = 1")

    db.commit()
    db.close()

    return results


def play_single_match(fixture_id, player_tactics=None):
    """Play a specific match (for the player's team)."""
    db = get_db()
    fixture = db.execute("SELECT * FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    if not fixture or fixture['played']:
        db.close()
        return None

    state = db.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    season = state['season']
    player_team_id = state['player_team_id']

    home_team = get_team(fixture['home_team_id'])
    away_team = get_team(fixture['away_team_id'])
    home_players = get_team_players(fixture['home_team_id'])
    away_players = get_team_players(fixture['away_team_id'])

    if not home_players or not away_players:
        db.close()
        return None

    # Apply player tactics to the correct side
    home_tactics = None
    away_tactics = None
    if player_tactics:
        if fixture['home_team_id'] == player_team_id:
            home_tactics = player_tactics
        elif fixture['away_team_id'] == player_team_id:
            away_tactics = player_tactics

    result = simulate_match(
        home_team, away_team,
        home_players[:15], away_players[:15],
        home_tactics=home_tactics, away_tactics=away_tactics,
        fixture_id=fixture_id
    )

    match_id = save_match(result)

    update_standings(
        season, fixture['home_team_id'], fixture['away_team_id'],
        result['home_score'], result['away_score'],
        result['home_tries'], result['away_tries']
    )

    db.close()
    return match_id


def get_current_round_fixtures():
    """Get fixtures for the current round."""
    db = get_db()
    state = db.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    if not state:
        db.close()
        return []

    fixtures = db.execute("""
        SELECT f.*, ht.name as home_team_name, at.name as away_team_name,
               ht.is_player_team as home_is_player,
               at.is_player_team as away_is_player,
               m.home_score, m.away_score, m.id as match_id
        FROM fixtures f
        JOIN teams ht ON f.home_team_id = ht.id
        JOIN teams at ON f.away_team_id = at.id
        LEFT JOIN matches m ON f.match_id = m.id
        WHERE f.season = ? AND f.round = ?
        ORDER BY f.id
    """, (state['season'], state['current_round'])).fetchall()

    db.close()
    return [dict(f) for f in fixtures]


def get_player_fixture():
    """Get the player's fixture for the current round."""
    db = get_db()
    state = db.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    if not state or not state['player_team_id']:
        db.close()
        return None

    fixture = db.execute("""
        SELECT f.*, ht.name as home_team_name, at.name as away_team_name,
               m.home_score, m.away_score, m.id as match_id
        FROM fixtures f
        JOIN teams ht ON f.home_team_id = ht.id
        JOIN teams at ON f.away_team_id = at.id
        LEFT JOIN matches m ON f.match_id = m.id
        WHERE f.season = ? AND f.round = ?
          AND (f.home_team_id = ? OR f.away_team_id = ?)
    """, (state['season'], state['current_round'],
          state['player_team_id'], state['player_team_id'])).fetchone()

    db.close()
    return dict(fixture) if fixture else None
