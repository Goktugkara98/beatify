# =============================================================================
# Config Paket Tanımı (app.config)
# =============================================================================
# Bu paket, uygulamanın yapılandırma değerlerini merkezi olarak sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      1.1. Spotify config exports
#      1.2. Genel config exports
#
# 2.0  DIŞA AKTARIMLAR (EXPORTS)
#      2.1. __all__
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Uygulama içi
from app.config.config import (
    COOKIE_HTTPONLY,
    COOKIE_MAX_AGE,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    DB_CONFIG,
    DEBUG,
    SECRET_KEY,
    SSL_CONFIG,
)
from app.config.spotify_config import SPOTIFY_CONFIG


# =============================================================================
# 2.0 DIŞA AKARIMLAR (EXPORTS)
# =============================================================================

__all__ = [
    "SPOTIFY_CONFIG",
    "DEBUG",
    "SECRET_KEY",
    "COOKIE_SECURE",
    "COOKIE_HTTPONLY",
    "COOKIE_SAMESITE",
    "COOKIE_MAX_AGE",
    "DB_CONFIG",
    "SSL_CONFIG",
]
