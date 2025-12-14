# =============================================================================
# Spotify Account Servis Modülü (account_service.py)
# =============================================================================
# Bu modül, Spotify entegrasyonunda hesap seviyesindeki işlemler için yüksek
# seviye servis fonksiyonlarını içerir. Örn:
# - Kullanıcının Spotify Client ID / Client Secret bilgilerini güncelleme
# - Spotify profil verisini çekme ve bağlantı durumuna göre normalize etme
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SABİTLER & LOGGER (CONSTANTS & LOGGER)
#      2.1. logger
#
# 3.0  SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
#      3.1. update_client_id_and_secret_data(username, client_id, client_secret)
#      3.2. get_spotify_profile_data(username)
#      3.3. create_default_spotify_data(status)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
import logging
from typing import Any, Dict

# Uygulama içi
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.services.spotify.api_service import SpotifyApiService


# =============================================================================
# 2.0 SABİTLER & LOGGER (CONSTANTS & LOGGER)
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# 3.0 SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
# =============================================================================

def update_client_id_and_secret_data(username: str, client_id: str, client_secret: str) -> bool:
    """Kullanıcının veritabanındaki Spotify Client ID ve Secret bilgilerini günceller."""
    try:
        if not all([username, client_id, client_secret]):
            logger.warning("Client ID/Secret güncelleme için eksik parametre.")
            return False

        spotify_repo = SpotifyUserRepository()
        return spotify_repo.store_client_info(
            username,
            client_id.strip(),
            client_secret.strip(),
        )
    except Exception as e:
        logger.error(f"Client ID/Secret güncellenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
        return False


def get_spotify_profile_data(username: str) -> Dict[str, Any]:
    """Kullanıcının Spotify profil verilerini alır, bağlantı durumuna göre işler."""
    try:
        api_service = SpotifyApiService()
        spotify_data = api_service.get_user_profile(username)

        if spotify_data and not spotify_data.get("error"):
            images = spotify_data.get("images", [])
            spotify_data["image_url"] = images[0]["url"] if images else "/static/img/default_profile.png"
            spotify_data["spotify_data_status"] = "Bağlı"
            return spotify_data
        else:
            spotify_repo = SpotifyUserRepository()
            credentials = spotify_repo.get_spotify_user_data(username)
            if credentials and credentials.get("client_id") and credentials.get("client_secret"):
                return create_default_spotify_data("Bağlı Değil")
            else:
                return create_default_spotify_data("Veri Yok")
    except Exception as e:
        logger.error(f"Spotify profil verileri alınırken genel hata (Kullanıcı: {username}): {e}", exc_info=True)
        return create_default_spotify_data("Hata")


def create_default_spotify_data(status: str) -> Dict[str, Any]:
    """Varsayılan bir Spotify profil veri yapısı oluşturur."""
    default_image_url = "/static/img/default_profile.png"
    return {
        "display_name": "Bağlı Değil",
        "id": None,
        "email": None,
        "country": None,
        "images": [{"url": default_image_url, "height": None, "width": None}],
        "image_url": default_image_url,
        "product": None,
        "followers": {"total": 0},
        "external_urls": {"spotify": "#"},
        "uri": None,
        "spotify_data_status": status,
    }


__all__ = [
    "update_client_id_and_secret_data",
    "get_spotify_profile_data",
    "create_default_spotify_data",
]

