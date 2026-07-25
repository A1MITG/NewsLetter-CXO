# config/config.py
import os

class Config:
    """Base configuration.

    SECRET_KEY falls back to an insecure, clearly-labeled dev-only value so
    local development works without a .env file. In production this default
    is refused: config/env_check.py's validate_environment() raises before
    the app starts if APP_ENV=production and SECRET_KEY is unset.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key-do-not-use-in-production')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')
