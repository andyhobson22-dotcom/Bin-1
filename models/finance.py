from database import get_db


def get_team_finances(team_id):
    db = get_db()
    team = db.execute("SELECT budget, wage_budget, reputation FROM teams WHERE id = ?",
                      (team_id,)).fetchone()
    players = db.execute("SELECT SUM(wage) as total_wages FROM players WHERE team_id = ?",
                         (team_id,)).fetchone()
    db.close()
    if team:
        result = dict(team)
        result['total_wages'] = players['total_wages'] or 0
        result['wage_remaining'] = result['wage_budget'] - result['total_wages']
        return result
    return None


def update_budget(team_id, amount):
    """Add or subtract from team budget."""
    db = get_db()
    db.execute("UPDATE teams SET budget = budget + ? WHERE id = ?", (amount, team_id))
    db.commit()
    db.close()
