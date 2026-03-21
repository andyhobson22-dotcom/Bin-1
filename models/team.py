from database import get_db


def get_team(team_id):
    db = get_db()
    team = db.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    db.close()
    return dict(team) if team else None


def get_all_teams():
    db = get_db()
    teams = db.execute("SELECT * FROM teams ORDER BY name").fetchall()
    db.close()
    return [dict(t) for t in teams]


def get_player_team():
    db = get_db()
    team = db.execute("SELECT * FROM teams WHERE is_player_team = 1").fetchone()
    db.close()
    return dict(team) if team else None


def set_player_team(team_id):
    db = get_db()
    db.execute("UPDATE teams SET is_player_team = 0")
    db.execute("UPDATE teams SET is_player_team = 1 WHERE id = ?", (team_id,))
    db.execute("UPDATE game_state SET player_team_id = ? WHERE id = 1", (team_id,))
    db.commit()
    db.close()
