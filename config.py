import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rugby-manager-dev-key')
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game.db')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
