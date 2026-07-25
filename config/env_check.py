# config/env_check.py
"""Central environment validation, run once at application startup.

Fails fast with a clear error if a variable required for the current
environment is missing, instead of letting the app start in a broken or
insecure state and fail later at request time.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Vars the app can run without — each just disables one optional feature.
OPTIONAL_VARS = {
    'NEWS_API_KEY': 'NewsAPI.org results will be skipped; RSS sources still run.',
    'LINKEDIN_CLIENT_ID': 'LinkedIn posting (scripts/linkedin_auth.py) will be unavailable.',
    'LINKEDIN_CLIENT_SECRET': 'LinkedIn posting (scripts/linkedin_auth.py) will be unavailable.',
    'LINKEDIN_ACCESS_TOKEN': 'scripts/daily_linkedin_post.py cannot publish until this is set.',
    'LINKEDIN_PERSON_URN': 'scripts/daily_linkedin_post.py cannot publish until this is set.',
}

_LINKEDIN_APP_PAIR = ('LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET')


def is_production():
    return os.environ.get('APP_ENV', 'development').lower() == 'production'


def validate_environment():
    """Validate required/optional env vars. Raises RuntimeError in production
    if a required variable is missing; only warns for optional ones."""
    if is_production() and not os.environ.get('SECRET_KEY'):
        raise RuntimeError(
            "SECRET_KEY is not set. APP_ENV=production refuses to start with "
            "the insecure development default — set SECRET_KEY in the "
            "environment (see .env.example)."
        )

    for var, effect in OPTIONAL_VARS.items():
        if not os.environ.get(var):
            logger.warning("%s is not set. %s", var, effect)

    set_count = sum(1 for var in _LINKEDIN_APP_PAIR if os.environ.get(var))
    if set_count == 1:
        logger.warning(
            "Only one of %s is set — both are required together for "
            "LinkedIn OAuth to work.", ' / '.join(_LINKEDIN_APP_PAIR)
        )
