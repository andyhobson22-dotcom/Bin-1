"""Youth academy — generate young players each season."""
import random
from database import get_db
from data.generate_players import (
    FIRST_NAMES, LAST_NAMES, SQUAD_TEMPLATE,
    generate_player,
)


def generate_youth_intake(team_id):
    """Generate 2-3 youth players for a team's academy."""
    db = get_db()
    team = db.execute("SELECT reputation FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not team:
        db.close()
        return []

    reputation = team['reputation']
    num_players = random.randint(2, 3)

    # Get existing names to avoid duplicates
    existing = db.execute("SELECT name FROM players").fetchall()
    used_names = {row['name'] for row in existing}

    positions = list(SQUAD_TEMPLATE.keys())
    new_players = []

    for _ in range(num_players):
        position = random.choice(positions)
        player = generate_player(position, reputation, used_names)

        # Youth players are 17-19
        player['age'] = random.randint(17, 19)
        player['contract_end'] = 3
        player['wage'] = random.randint(500, 2000)

        # Lower current stats but potentially high ceiling
        for stat in ['speed', 'strength', 'stamina', 'agility', 'passing',
                     'kicking', 'tackling', 'handling', 'scrummaging',
                     'lineout', 'game_sense', 'leadership', 'discipline']:
            player[stat] = max(1, player[stat] - random.randint(10, 25))

        player['potential'] = random.randint(55, 95)

        # Insert into database
        sec_pos = str(player.pop('secondary_positions'))
        db.execute("""
            INSERT INTO players (name, age, team_id, position, secondary_positions,
                speed, strength, stamina, agility, passing, kicking, tackling,
                handling, scrummaging, lineout, game_sense, leadership, discipline,
                potential, form, morale, fitness, wage, contract_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player['name'], player['age'], team_id, player['position'], sec_pos,
            player['speed'], player['strength'], player['stamina'], player['agility'],
            player['passing'], player['kicking'], player['tackling'], player['handling'],
            player['scrummaging'], player['lineout'], player['game_sense'],
            player['leadership'], player['discipline'], player['potential'],
            player['form'], player['morale'], player['fitness'],
            player['wage'], player['contract_end'],
        ))

        new_players.append(player)

    db.commit()
    db.close()
    return new_players
