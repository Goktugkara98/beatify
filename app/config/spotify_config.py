# =============================================================================
# Spotify Configuration
# =============================================================================
# Contents:
# 1. Imports
# 2. Configuration Class
#    2.1. API Endpoints
#    2.2. OAuth Settings
#    2.3. Widget Settings
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import os
from typing import Dict, Any

# -----------------------------------------------------------------------------
# 2. Configuration Class
# -----------------------------------------------------------------------------
class SpotifyConfig:
    """Configuration settings for Spotify integration."""
    
    # 2.1. API Endpoints
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    PROFILE_URL = f"{API_BASE_URL}/me"
    

    # 2.2. OAuth Settings
    REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:5000/spotify/callback")
    SCOPES = " ".join([
        # Kullanıcı Bilgileri
        "user-read-private",          # Kullanıcının abonelik ve ülke bilgilerini okuma
        "user-read-email",            # Kullanıcının e-posta adresini okuma

        # Kütüphane ve Takip
        "user-library-read",          # Kullanıcının kütüphanesini okuma (kaydedilen şarkılar/albümler)
        "user-library-modify",        # Kütüphaneye ekleme/çıkarma yapma
        "user-follow-read",           # Takip edilen sanatçıları okuma
        "user-follow-modify",         # Sanatçı takip etme/bırakma

        # Çalma Geçmişi ve Durum
        "user-read-recently-played",  # Son çalınan parçaları okuma
        "user-read-playback-state",   # Çalma durumunu okuma (cihaz, parça vb.)
        "user-modify-playback-state", # Çalmayı kontrol etme (oynat, duraklat, geç)
        "user-read-currently-playing",# Şu anda çalan parçayı okuma

        # Çalma Listeleri
        "playlist-read-private",      # Özel çalma listelerini okuma
        "playlist-read-collaborative",# İşbirlikçi çalma listelerini okuma
        "playlist-modify-private",    # Özel çalma listelerini düzenleme
        "playlist-modify-public",     # Genel çalma listelerini düzenleme
    ])

    
    # 2.3. Widget Settings
    WIDGET_TOKEN_EXPIRY_DAYS = 30
    WIDGET_TYPES = {
        "now-playing": {
            "name": "Now Playing",
            "description": "Shows the currently playing track"
        },
        "recently-played": {
            "name": "Recently Played",
            "description": "Shows recently played tracks"
        }
    }
    WIDGET_SIZES = {
        "small": {
            "width": 300,
            "height": 80
        },
        "medium": {
            "width": 400,
            "height": 120
        },
        "large": {
            "width": 500,
            "height": 160
        }
    }
    WIDGET_THEMES = {
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
    
    @classmethod
    def get_widget_config(cls) -> Dict[str, Any]:
        """
        Returns the complete widget configuration.
        
        Returns:
            Dictionary with all widget configuration options
        """
        return {
            "types": cls.WIDGET_TYPES,
            "sizes": cls.WIDGET_SIZES,
            "themes": cls.WIDGET_THEMES
        }

# Create a singleton instance
SPOTIFY_CONFIG = SpotifyConfig()
