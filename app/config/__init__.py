# =============================================================================
# Configuration Package
# =============================================================================
# Contents:
# 1. Imports
# 2. Package Exports
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from app.config.spotify_config import SPOTIFY_CONFIG
from app.config.config import (
    DEBUG, SECRET_KEY, 
    COOKIE_SECURE, COOKIE_HTTPONLY, COOKIE_SAMESITE, COOKIE_MAX_AGE,
    DB_CONFIG, SSL_CONFIG
)

# -----------------------------------------------------------------------------
# 2. Package Exports
# -----------------------------------------------------------------------------
__all__ = [
    'SPOTIFY_CONFIG',
    'DEBUG', 
    'SECRET_KEY',
    'COOKIE_SECURE', 
    'COOKIE_HTTPONLY', 
    'COOKIE_SAMESITE', 
    'COOKIE_MAX_AGE',
    'DB_CONFIG', 
    'SSL_CONFIG'
]
