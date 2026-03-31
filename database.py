import sqlite3
from config import Config


def get_db():
    db = sqlite3.connect(Config.DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    stadium TEXT NOT NULL,
    stadium_capacity INTEGER DEFAULT 15000,
    budget INTEGER DEFAULT 5000000,
    wage_budget INTEGER DEFAULT 100000,
    reputation INTEGER DEFAULT 50,
    home_color TEXT DEFAULT '#003366',
    away_color TEXT DEFAULT '#FFFFFF',
    is_player_team INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    team_id INTEGER,
    position TEXT NOT NULL,
    secondary_positions TEXT DEFAULT '[]',
    nationality TEXT DEFAULT 'England',
    height INTEGER DEFAULT 183,
    weight INTEGER DEFAULT 95,
    -- Physical (7)
    stopping_power INTEGER DEFAULT 50,
    explosiveness INTEGER DEFAULT 50,
    leg_drive INTEGER DEFAULT 50,
    pace INTEGER DEFAULT 50,
    acceleration INTEGER DEFAULT 50,
    agility INTEGER DEFAULT 50,
    strength INTEGER DEFAULT 50,
    -- Mental (9)
    aggression INTEGER DEFAULT 50,
    composure INTEGER DEFAULT 50,
    concentration INTEGER DEFAULT 50,
    awareness INTEGER DEFAULT 50,
    running_lines INTEGER DEFAULT 50,
    discipline INTEGER DEFAULT 50,
    tenacity INTEGER DEFAULT 50,
    scanning INTEGER DEFAULT 50,
    positioning INTEGER DEFAULT 50,
    -- Technical (13)
    long_passing INTEGER DEFAULT 50,
    handling INTEGER DEFAULT 50,
    high_ball INTEGER DEFAULT 50,
    offload INTEGER DEFAULT 50,
    tackling INTEGER DEFAULT 50,
    rucking INTEGER DEFAULT 50,
    mauling INTEGER DEFAULT 50,
    jackling INTEGER DEFAULT 50,
    grubber INTEGER DEFAULT 50,
    chipping INTEGER DEFAULT 50,
    box_kicking INTEGER DEFAULT 50,
    stepping INTEGER DEFAULT 50,
    short_passing INTEGER DEFAULT 50,
    -- Set Piece (6)
    goal_kicking INTEGER DEFAULT 50,
    scrum_drive INTEGER DEFAULT 50,
    scrum_tech INTEGER DEFAULT 50,
    touch_finder INTEGER DEFAULT 50,
    jumping INTEGER DEFAULT 50,
    lifting INTEGER DEFAULT 50,
    -- Meta
    potential INTEGER DEFAULT 60,
    form INTEGER DEFAULT 50,
    morale INTEGER DEFAULT 70,
    fitness INTEGER DEFAULT 100,
    wage INTEGER DEFAULT 5000,
    contract_end INTEGER DEFAULT 2,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER DEFAULT 1,
    round INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    played INTEGER DEFAULT 0,
    match_id INTEGER,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id INTEGER,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    home_tries INTEGER DEFAULT 0,
    away_tries INTEGER DEFAULT 0,
    home_conversions INTEGER DEFAULT 0,
    away_conversions INTEGER DEFAULT 0,
    home_penalties INTEGER DEFAULT 0,
    away_penalties INTEGER DEFAULT 0,
    home_drop_goals INTEGER DEFAULT 0,
    away_drop_goals INTEGER DEFAULT 0,
    home_yellow_cards INTEGER DEFAULT 0,
    away_yellow_cards INTEGER DEFAULT 0,
    home_red_cards INTEGER DEFAULT 0,
    away_red_cards INTEGER DEFAULT 0,
    events TEXT DEFAULT '[]',
    commentary TEXT DEFAULT '[]',
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id),
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER DEFAULT 1,
    team_id INTEGER NOT NULL,
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    drawn INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    points_for INTEGER DEFAULT 0,
    points_against INTEGER DEFAULT 0,
    tries_for INTEGER DEFAULT 0,
    tries_against INTEGER DEFAULT 0,
    bonus_points INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS game_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    season INTEGER DEFAULT 1,
    current_round INTEGER DEFAULT 1,
    total_rounds INTEGER DEFAULT 18,
    player_team_id INTEGER,
    phase TEXT DEFAULT 'pre_season',
    transfer_window_open INTEGER DEFAULT 1,
    FOREIGN KEY (player_team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    focus TEXT DEFAULT 'balanced',
    intensity TEXT DEFAULT 'medium',
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
"""
