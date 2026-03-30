from database import get_db


def get_standings(season=1):
    db = get_db()
    standings = db.execute("""
        SELECT s.*, t.name as team_name
        FROM standings s
        JOIN teams t ON s.team_id = t.id
        WHERE s.season = ?
        ORDER BY s.points DESC, (s.points_for - s.points_against) DESC, s.tries_for DESC
    """, (season,)).fetchall()
    db.close()
    return [dict(s) for s in standings]


def update_standings(season, home_team_id, away_team_id, home_score, away_score,
                     home_tries, away_tries):
    """Update league standings after a match."""
    db = get_db()

    # Calculate bonus points
    # 4+ tries = 1 bonus point
    # Losing by 7 or fewer = 1 bonus point
    home_bp = 0
    away_bp = 0
    if home_tries >= 4:
        home_bp += 1
    if away_tries >= 4:
        away_bp += 1

    margin = home_score - away_score

    if margin > 0:
        # Home win
        home_w, home_d, home_l = 1, 0, 0
        away_w, away_d, away_l = 0, 0, 1
        home_pts = 4 + home_bp
        away_pts = away_bp
        if margin <= 7:
            away_pts += 1  # losing bonus point
            away_bp += 1
    elif margin < 0:
        # Away win
        home_w, home_d, home_l = 0, 0, 1
        away_w, away_d, away_l = 1, 0, 0
        away_pts = 4 + away_bp
        home_pts = home_bp
        if abs(margin) <= 7:
            home_pts += 1  # losing bonus point
            home_bp += 1
    else:
        # Draw
        home_w, home_d, home_l = 0, 1, 0
        away_w, away_d, away_l = 0, 1, 0
        home_pts = 2 + home_bp
        away_pts = 2 + away_bp

    # Update home team
    db.execute("""
        UPDATE standings SET
            played = played + 1,
            won = won + ?,
            drawn = drawn + ?,
            lost = lost + ?,
            points_for = points_for + ?,
            points_against = points_against + ?,
            tries_for = tries_for + ?,
            tries_against = tries_against + ?,
            bonus_points = bonus_points + ?,
            points = points + ?
        WHERE season = ? AND team_id = ?
    """, (home_w, home_d, home_l, home_score, away_score,
          home_tries, away_tries, home_bp, home_pts, season, home_team_id))

    # Update away team
    db.execute("""
        UPDATE standings SET
            played = played + 1,
            won = won + ?,
            drawn = drawn + ?,
            lost = lost + ?,
            points_for = points_for + ?,
            points_against = points_against + ?,
            tries_for = tries_for + ?,
            tries_against = tries_against + ?,
            bonus_points = bonus_points + ?,
            points = points + ?
        WHERE season = ? AND team_id = ?
    """, (away_w, away_d, away_l, away_score, home_score,
          away_tries, home_tries, away_bp, away_pts, season, away_team_id))

    db.commit()
    db.close()


def get_fixtures(season=1, round_num=None):
    db = get_db()
    query = """
        SELECT f.*, ht.name as home_team_name, at.name as away_team_name,
               m.home_score, m.away_score
        FROM fixtures f
        JOIN teams ht ON f.home_team_id = ht.id
        JOIN teams at ON f.away_team_id = at.id
        LEFT JOIN matches m ON f.match_id = m.id
        WHERE f.season = ?
    """
    params = [season]
    if round_num is not None:
        query += " AND f.round = ?"
        params.append(round_num)
    query += " ORDER BY f.round, f.id"
    fixtures = db.execute(query, params).fetchall()
    db.close()
    return [dict(f) for f in fixtures]


def get_game_state():
    db = get_db()
    state = db.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    db.close()
    return dict(state) if state else None
