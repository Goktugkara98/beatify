"""
Ana Spotify Servis Modülü (spotify_service)

Spotify entegrasyonuyla ilgili genel amaçlı, üst seviye servis fonksiyonlarını
içerir. Kullanıcıların Spotify Client ID/Secret bilgilerini güncellemek ve
Spotify profil verilerini almak gibi işlemleri kapsar.
"""

import logging
from typing import Dict, Any

from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.services.spotify.api_service import SpotifyApiService

logger = logging.getLogger(__name__)


def update_client_id_and_secret_data(username: str, client_id: str, client_secret: str) -> bool:
    """
    Kullanıcının veritabanındaki Spotify Client ID ve Secret bilgilerini günceller.
    """
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
    """
    Kullanıcının Spotify profil verilerini alır, bağlantı durumuna göre işler.
    """
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
    """
    Varsayılan bir Spotify profil veri yapısı oluşturur.
    """
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

