import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gridguard-ai-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'gridguard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
