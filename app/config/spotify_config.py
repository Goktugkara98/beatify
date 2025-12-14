# =============================================================================
# Spotify Entegrasyon Yapılandırması
# =============================================================================
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
# 2.0 YAPILANDIRMA SINIFI (CONFIGURATION CLASS - SpotifyConfig)
#     2.1. API ENDPOINT'LERİ (API Endpoints)
#     2.2. OAUTH AYARLARI (OAuth Settings)
# 3.0 YAPILANDIRMA NESNESİ (CONFIGURATION INSTANCE)
# =============================================================================

# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import os
from typing import Dict, Any, List

# 2.0 YAPILANDIRMA SINIFI (CONFIGURATION CLASS - SpotifyConfig)
# =============================================================================
class SpotifyConfig:
    # 2.1. API ENDPOINT'LERİ (API Endpoints)
    # -----------------------------------------------------------------------------
    AUTH_URL: str = "https://accounts.spotify.com/authorize"
    TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    API_BASE_URL: str = "https://api.spotify.com/v1"
    PROFILE_URL: str = f"{API_BASE_URL}/me"

    # 2.2. OAUTH AYARLARI (OAuth Settings)
    # -----------------------------------------------------------------------------
    CLIENT_ID: str | None = os.environ.get("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET: str | None = os.environ.get("SPOTIFY_CLIENT_SECRET")
    # Spotify güvenlik politikası gereği `localhost` yerine loopback IP kullanmak gerekir.
    # Geliştirme için önerilen: http://127.0.0.1:5000/spotify/callback
    # Prod için env ile HTTPS bir domain ver: SPOTIFY_REDIRECT_URI=https://your-domain/spotify/callback
    REDIRECT_URI: str = os.environ.get(
        "SPOTIFY_REDIRECT_URI",
        "http://127.0.0.1:5000/spotify/callback",
    )
    SCOPES: str = " ".join([
        "user-read-private",
        "user-read-email",
        "user-library-read",
        "user-library-modify",
        "user-follow-read",
        "user-follow-modify",
        "user-read-recently-played",
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-private",
        "playlist-modify-public",
    ])

# 3.0 YAPILANDIRMA NESNESİ (CONFIGURATION INSTANCE)
# =============================================================================
SPOTIFY_CONFIG: SpotifyConfig = SpotifyConfig()
