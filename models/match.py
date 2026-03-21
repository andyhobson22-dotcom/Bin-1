import json
from database import get_db


def save_match(match_data):
    """Save a completed match to the database."""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO matches (
            fixture_id, home_team_id, away_team_id,
            home_score, away_score, home_tries, away_tries,
            home_conversions, away_conversions,
            home_penalties, away_penalties,
            home_drop_goals, away_drop_goals,
            home_yellow_cards, away_yellow_cards,
            home_red_cards, away_red_cards,
            events, commentary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_data.get('fixture_id'),
        match_data['home_team_id'],
        match_data['away_team_id'],
        match_data['home_score'],
        match_data['away_score'],
        match_data['home_tries'],
        match_data['away_tries'],
        match_data.get('home_conversions', 0),
        match_data.get('away_conversions', 0),
        match_data.get('home_penalties', 0),
        match_data.get('away_penalties', 0),
        match_data.get('home_drop_goals', 0),
        match_data.get('away_drop_goals', 0),
        match_data.get('home_yellow_cards', 0),
        match_data.get('away_yellow_cards', 0),
        match_data.get('home_red_cards', 0),
        match_data.get('away_red_cards', 0),
        json.dumps(match_data.get('events', [])),
        json.dumps(match_data.get('commentary', [])),
    ))
    match_id = cursor.lastrowid

    # Update fixture as played
    if match_data.get('fixture_id'):
        db.execute(
            "UPDATE fixtures SET played = 1, match_id = ? WHERE id = ?",
            (match_id, match_data['fixture_id'])
        )

    db.commit()
    db.close()
    return match_id


def get_match(match_id):
    db = get_db()
    match = db.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    db.close()
    if match:
        m = dict(match)
        m['events'] = json.loads(m['events'])
        m['commentary'] = json.loads(m['commentary'])
        return m
    return None


def get_team_matches(team_id, season=None):
    db = get_db()
    query = """
        SELECT m.*, f.round, f.season
        FROM matches m
        JOIN fixtures f ON m.fixture_id = f.id
        WHERE (m.home_team_id = ? OR m.away_team_id = ?)
    """
    params = [team_id, team_id]
    if season:
        query += " AND f.season = ?"
        params.append(season)
    query += " ORDER BY f.round"
    matches = db.execute(query, params).fetchall()
    db.close()
    return [dict(m) for m in matches]
