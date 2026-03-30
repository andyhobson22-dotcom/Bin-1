"""Save and load game state."""
import sqlite3
import shutil
import os
from config import Config


SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saves')


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(slot_name='autosave'):
    """Save the current game by copying the database."""
    ensure_save_dir()
    save_path = os.path.join(SAVE_DIR, f'{slot_name}.db')
    shutil.copy2(Config.DATABASE, save_path)
    return save_path


def load_game(slot_name='autosave'):
    """Load a saved game by restoring the database."""
    save_path = os.path.join(SAVE_DIR, f'{slot_name}.db')
    if os.path.exists(save_path):
        shutil.copy2(save_path, Config.DATABASE)
        return True
    return False


def list_saves():
    """List available save files."""
    ensure_save_dir()
    saves = []
    for f in os.listdir(SAVE_DIR):
        if f.endswith('.db'):
            path = os.path.join(SAVE_DIR, f)
            saves.append({
                'name': f[:-3],
                'path': path,
                'modified': os.path.getmtime(path),
            })
    saves.sort(key=lambda s: s['modified'], reverse=True)
    return saves


def delete_save(slot_name):
    """Delete a save file."""
    save_path = os.path.join(SAVE_DIR, f'{slot_name}.db')
    if os.path.exists(save_path):
        os.remove(save_path)
        return True
    return False
