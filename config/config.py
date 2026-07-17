# config/config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_secret_key')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///../instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
