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
#     2.3. WIDGET AYARLARI (Widget Settings)
#     2.4. YARDIMCI METOD (HELPER METHOD)
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
    REDIRECT_URI: str = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:5000/spotify/callback")
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

    # 2.3. WIDGET AYARLARI (Widget Settings)
    # -----------------------------------------------------------------------------
    WIDGET_TOKEN_EXPIRY_DAYS: int = 30
    WIDGET_TYPES: Dict[str, Dict[str, str]] = {
        "now-playing": {
            "name": "Şu An Çalınan (Now Playing)",
            "description": "Spotify'da o anda çalmakta olan parçayı gösterir."
        },
        "recently-played": {
            "name": "Son Çalınanlar (Recently Played)",
            "description": "Spotify'da son dinlenen parçaları listeler."
        }
    }
    WIDGET_SIZES: Dict[str, Dict[str, int]] = {
        "small": {"width": 300, "height": 80},
        "medium": {"width": 400, "height": 120},
        "large": {"width": 500, "height": 160}
    }
    WIDGET_THEMES: Dict[str, Dict[str, str]] = {
        "dark": {
            "background": "#121212",
            "text": "#FFFFFF",
            "accent": "#1DB954"
        },
        "light": {
            "background": "#FFFFFF",
            "text": "#121212",
            "accent": "#1DB954"
        }
    }

    # 2.4. YARDIMCI METOD (HELPER METHOD)
    # -----------------------------------------------------------------------------
    @classmethod
    def get_widget_config(cls) -> Dict[str, Any]:
        return {
            "types": cls.WIDGET_TYPES,
            "sizes": cls.WIDGET_SIZES,
            "themes": cls.WIDGET_THEMES
        }

# 3.0 YAPILANDIRMA NESNESİ (CONFIGURATION INSTANCE)
# =============================================================================
SPOTIFY_CONFIG: SpotifyConfig = SpotifyConfig()
