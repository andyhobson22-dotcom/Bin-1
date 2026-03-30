"""Transfer market system."""
import random
from database import get_db
from models.player import get_overall_rating


def get_player_value(player):
    """Calculate a player's transfer value."""
    rating = get_overall_rating(player)
    age = player.get('age', 25)

    # Base value from rating
    base = rating * rating * 50  # Exponential scaling

    # Age modifier
    if age < 23:
        age_mod = 1.3  # Young with potential
    elif age < 27:
        age_mod = 1.2  # Peak years approaching
    elif age < 30:
        age_mod = 1.0  # Prime
    elif age < 33:
        age_mod = 0.6  # Declining
    else:
        age_mod = 0.3  # End of career

    # Potential modifier for young players
    potential = player.get('potential', 60)
    if age < 25:
        pot_mod = 1 + (potential - 60) / 100
    else:
        pot_mod = 1.0

    # Contract modifier (less contract = less value)
    contract = player.get('contract_end', 2)
    contract_mod = 0.5 + (contract * 0.25)

    value = int(base * age_mod * pot_mod * contract_mod)
    return max(50000, value)  # Minimum value


def get_available_players(exclude_team_id=None):
    """Get players available for transfer."""
    db = get_db()
    query = "SELECT * FROM players WHERE contract_end <= 1"
    params = []
    if exclude_team_id:
        query += " AND team_id != ?"
        params.append(exclude_team_id)
    query += " ORDER BY name"
    players = db.execute(query, params).fetchall()
    db.close()

    result = []
    for p in players:
        p = dict(p)
        p['value'] = get_player_value(p)
        result.append(p)
    return result


def make_transfer(player_id, from_team_id, to_team_id, fee):
    """Execute a player transfer."""
    db = get_db()

    # Move player
    db.execute("UPDATE players SET team_id = ?, contract_end = 3 WHERE id = ?",
               (to_team_id, player_id))

    # Update budgets
    db.execute("UPDATE teams SET budget = budget + ? WHERE id = ?",
               (fee, from_team_id))
    db.execute("UPDATE teams SET budget = budget - ? WHERE id = ?",
               (fee, to_team_id))

    db.commit()
    db.close()
    return True


def get_transfer_targets(team_id, position=None):
    """Get potential transfer targets for a team."""
    db = get_db()
    team = db.execute("SELECT budget FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not team:
        db.close()
        return []

    budget = team['budget']

    query = "SELECT * FROM players WHERE team_id != ?"
    params = [team_id]
    if position:
        query += " AND position = ?"
        params.append(position)

    players = db.execute(query, params).fetchall()
    db.close()

    targets = []
    for p in players:
        p = dict(p)
        value = get_player_value(p)
        if value <= budget:
            p['value'] = value
            p['rating'] = get_overall_rating(p)
            targets.append(p)

    targets.sort(key=lambda x: x['rating'], reverse=True)
    return targets[:30]  # Top 30 affordable targets
