# =============================================================================
# Ana Spotify Servis Modülü (spotify_service)
# =============================================================================
# Bu modül, Spotify entegrasyonuyla ilgili genel amaçlı, üst seviye servis
# fonksiyonlarını içerir. Bu fonksiyonlar, birden fazla alt servisin
# etkileşimini gerektirebilecek işlemleri yönetir.
#
# =============================================================================
# İÇİNDEKİLER
# =============================================================================
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
#
#      2.1  HESAP YÖNETİMİ (ACCOUNT MANAGEMENT)
#           2.1.1. update_client_id_and_secret_data(username, client_id, client_secret)
#                  : Kullanıcının Spotify Client ID ve Secret bilgilerini günceller.
#           2.1.2. get_spotify_profile_data(username)
#                  : Kullanıcının genel Spotify profil verilerini alır ve durumunu işler.
#
#      2.2  YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
#           2.2.1. create_default_spotify_data(status)
#                  : Hata veya veri yokluğu durumunda varsayılan bir profil yapısı oluşturur.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from app.database.spotify_user_repository import SpotifyUserRepository
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1 HESAP YÖNETİMİ (ACCOUNT MANAGEMENT)
# -----------------------------------------------------------------------------
def update_client_id_and_secret_data(username: str, client_id: str, client_secret: str) -> bool:
    """
    2.1.1. Kullanıcının veritabanındaki Spotify Client ID ve Secret bilgilerini günceller.
    """
    try:
        if not all([username, client_id, client_secret]):
            logger.warning("Client ID/Secret güncelleme için eksik parametre.")
            return False

        spotify_repo = SpotifyUserRepository()
        return spotify_repo.spotify_insert_or_update_client_info(
            username,
            client_id.strip(),
            client_secret.strip()
        )
    except Exception as e:
        logger.error(f"Client ID/Secret güncellenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
        return False

def get_spotify_profile_data(username: str) -> Dict[str, Any]:
    """
    2.1.2. Kullanıcının Spotify profil verilerini alır, bağlantı durumuna göre işler.
    """
    try:
        api_service = SpotifyApiService()
        spotify_data = api_service.get_user_profile(username)

        if spotify_data and not spotify_data.get("error"):
            images = spotify_data.get('images', [])
            spotify_data['image_url'] = images[0]['url'] if images else '/static/img/default_profile.png'
            spotify_data['spotify_data_status'] = 'Bağlı'
            return spotify_data
        else:
            spotify_repo = SpotifyUserRepository()
            credentials = spotify_repo.spotify_get_user_data(username)
            if credentials and credentials.get('client_id') and credentials.get('client_secret'):
                return create_default_spotify_data('Bağlı Değil')
            else:
                return create_default_spotify_data('Veri Yok')
    except Exception as e:
        logger.error(f"Spotify profil verileri alınırken genel hata (Kullanıcı: {username}): {e}", exc_info=True)
        return create_default_spotify_data('Hata')

# -----------------------------------------------------------------------------
# 2.2 YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
# -----------------------------------------------------------------------------
def create_default_spotify_data(status: str) -> Dict[str, Any]:
    """
    2.2.1. Varsayılan bir Spotify profil veri yapısı oluşturur.
    """
    default_image_url = '/static/img/default_profile.png'
    return {
        'display_name': 'Bağlı Değil',
        'id': None,
        'email': None,
        'country': None,
        'images': [{'url': default_image_url, 'height': None, 'width': None}],
        'image_url': default_image_url,
        'product': None,
        'followers': {'total': 0},
        'external_urls': {'spotify': '#'},
        'uri': None,
        'spotify_data_status': status
    }
