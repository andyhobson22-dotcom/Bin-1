"""Training system for player development."""
import random
from database import get_db

TRAINING_FOCUSES = {
    'fitness': {
        'name': 'Fitness',
        'description': 'Improve stamina and recovery',
        'affected_stats': ['stamina', 'speed'],
        'injury_risk': 0.03,
    },
    'attack': {
        'name': 'Attack',
        'description': 'Work on attacking patterns and handling',
        'affected_stats': ['passing', 'handling', 'agility'],
        'injury_risk': 0.05,
    },
    'defence': {
        'name': 'Defence',
        'description': 'Improve tackling technique and defensive systems',
        'affected_stats': ['tackling', 'game_sense', 'strength'],
        'injury_risk': 0.04,
    },
    'set_piece': {
        'name': 'Set Piece',
        'description': 'Scrum and lineout drills',
        'affected_stats': ['scrummaging', 'lineout'],
        'injury_risk': 0.06,
    },
    'kicking': {
        'name': 'Kicking',
        'description': 'Improve kicking accuracy and variety',
        'affected_stats': ['kicking'],
        'injury_risk': 0.02,
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'General training across all areas',
        'affected_stats': ['stamina', 'tackling', 'handling', 'passing'],
        'injury_risk': 0.03,
    },
}


def set_training(team_id, focus, intensity='medium'):
    """Set training focus for a team."""
    db = get_db()
    db.execute("""
        UPDATE training SET focus = ?, intensity = ? WHERE team_id = ?
    """, (focus, intensity, team_id))
    db.commit()
    db.close()


def get_training(team_id):
    """Get current training settings."""
    db = get_db()
    t = db.execute("SELECT * FROM training WHERE team_id = ?", (team_id,)).fetchone()
    db.close()
    return dict(t) if t else {'focus': 'balanced', 'intensity': 'medium'}


def apply_weekly_training(team_id):
    """Apply weekly training effects to all players on a team."""
    db = get_db()
    training = db.execute("SELECT * FROM training WHERE team_id = ?",
                          (team_id,)).fetchone()
    if not training:
        db.close()
        return []

    focus = training['focus']
    focus_config = TRAINING_FOCUSES.get(focus, TRAINING_FOCUSES['balanced'])
    affected_stats = focus_config['affected_stats']
    injury_risk = focus_config['injury_risk']

    players = db.execute("SELECT * FROM players WHERE team_id = ?",
                         (team_id,)).fetchall()

    updates = []
    for player in players:
        player = dict(player)

        # Skip injured players
        if player['fitness'] < 100:
            # Recovery
            recovery = random.randint(10, 25)
            new_fitness = min(100, player['fitness'] + recovery)
            db.execute("UPDATE players SET fitness = ? WHERE id = ?",
                       (new_fitness, player['id']))
            updates.append({
                'player': player['name'],
                'type': 'recovery',
                'fitness': new_fitness,
            })
            continue

        # Training injury check
        if random.random() < injury_risk:
            injury_severity = random.randint(20, 60)
            new_fitness = max(0, 100 - injury_severity)
            db.execute("UPDATE players SET fitness = ? WHERE id = ?",
                       (new_fitness, player['id']))
            updates.append({
                'player': player['name'],
                'type': 'injury',
                'fitness': new_fitness,
            })
            continue

        # Stat improvement (mainly for younger players)
        for stat in affected_stats:
            current = player.get(stat, 50)
            potential = player.get('potential', 60)

            # Younger players improve more
            if player['age'] < 24 and current < potential:
                improvement = random.randint(0, 2)
            elif player['age'] < 28 and current < potential:
                improvement = random.randint(0, 1)
            elif player['age'] > 32:
                improvement = -random.randint(0, 1)  # Decline
            else:
                improvement = 0

            new_val = max(1, min(99, current + improvement))
            if new_val != current:
                db.execute(f"UPDATE players SET {stat} = ? WHERE id = ?",
                           (new_val, player['id']))

        # Form fluctuation
        form_change = random.randint(-5, 5)
        new_form = max(1, min(99, player['form'] + form_change))
        db.execute("UPDATE players SET form = ? WHERE id = ?",
                   (new_form, player['id']))

    db.commit()
    db.close()
    return updates
