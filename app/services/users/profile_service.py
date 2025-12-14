# =============================================================================
# Kullanıcı Profil Servis Modülü (profile_service.py)
# =============================================================================
# Bu modül, kullanıcı profil sayfası için gerekli verileri hazırlayan yüksek
# seviye servis fonksiyonlarını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SABİTLER & LOGGER (CONSTANTS & LOGGER)
#      2.1. logger
#
# 3.0  SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
#      3.1. handle_get_request(username)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
import logging
from typing import Any, Dict, Tuple

# Üçüncü parti
from flask import url_for

# Uygulama içi
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.database.repositories.user_repository import BeatifyUserRepository
from app.services.spotify.account_service import create_default_spotify_data
from app.services.spotify.api_service import SpotifyApiService


# =============================================================================
# 2.0 SABİTLER & LOGGER (CONSTANTS & LOGGER)
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# 3.0 SERVİS FONKSİYONLARI (SERVICE FUNCTIONS)
# =============================================================================

def handle_get_request(username: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Kullanıcının profil sayfası için gerekli verileri toplar.

    Bu fonksiyon, kullanıcının temel bilgilerini, Spotify kimlik bilgilerini
    (Client ID/Secret) ve Spotify API'sinden alınan güncel profil verilerini
    birleştirerek döndürür.
    """
    logger.info(f"Profil sayfası için GET isteği işleniyor: Kullanıcı='{username}'")

    try:
        # 1. Kullanıcının temel verilerini al
        user_repo = BeatifyUserRepository()
        user_data = user_repo.get_user_details(username)
        if not user_data:
            logger.error(f"Kullanıcı verisi bulunamadı: {username}")
            return {}, {}, create_default_spotify_data('Veri Yok')

        # 2. Spotify kimlik bilgilerini (Client ID/Secret) al
        spotify_repo = SpotifyUserRepository()
        spotify_credentials = spotify_repo.get_spotify_user_data(username) or {}

        # 3. Spotify bağlantı durumuna göre görüntülenecek veriyi hazırla
        is_oauth_connected = bool(spotify_credentials.get('refresh_token'))
        has_client_credentials = bool(spotify_credentials.get('client_id'))

        # -- Profil Resmi Belirleme Mantığı --
        # Öncelik 1: Kullanıcının yüklediği özel resim (Veritabanından)
        # Öncelik 2: Spotify profil resmi (varsa)
        # Öncelik 3: Varsayılan anonim resim
        
        profile_image_url = None
        
        # Veritabanında kayıtlı profil resmi var mı?
        if user_data.get('profile_image'):
            # Dosya adını veritabanından alıyoruz
            filename = user_data['profile_image']
            profile_image_url = url_for('static', filename=f'img/uploads/profiles/{filename}')
        
        # Varsayılan resim
        default_image_url = url_for('static', filename='img/photo/profile_pic_anonymous_male.png')

        if is_oauth_connected:
            # OAuth ile bağlıysa, API'den canlı veri çek
            logger.info(f"Kullanıcı '{username}' OAuth ile bağlı. API'den profil verileri çekiliyor.")
            api_service = SpotifyApiService()
            live_spotify_data = api_service.get_user_profile(username)

            if live_spotify_data and not live_spotify_data.get("error"):
                spotify_profile_display_data = live_spotify_data
                spotify_profile_display_data['spotify_data_status'] = 'Bağlı'
                
                if not profile_image_url:
                    images = spotify_profile_display_data.get('images', [])
                    spotify_profile_display_data['image_url'] = images[0]['url'] if images else default_image_url
                else:
                    # Kullanıcı özel resim yüklediyse Spotify resmini ez
                    spotify_profile_display_data['image_url'] = profile_image_url
                    
                logger.info(f"Kullanıcı '{username}' için Spotify API'den veri başarıyla alındı.")
            else:
                logger.warning(f"Kullanıcı '{username}' için Spotify API'sinden hata yanıtı alındı: {live_spotify_data}")
                spotify_profile_display_data = create_default_spotify_data('Hata (API Erişimi)')
                spotify_profile_display_data['image_url'] = profile_image_url if profile_image_url else default_image_url

        elif has_client_credentials:
            # Sadece kimlik bilgileri var, OAuth bağlantısı yok
            logger.info(f"Kullanıcı '{username}' kimlik bilgilerine sahip ama OAuth ile bağlı değil.")
            spotify_profile_display_data = create_default_spotify_data('Bağlı Değil (OAuth Gerekli)')
            spotify_profile_display_data['image_url'] = profile_image_url if profile_image_url else default_image_url

        else:
            # Hiçbir Spotify bilgisi yok
            logger.info(f"Kullanıcı '{username}' için Spotify bağlantısı bulunamadı.")
            spotify_profile_display_data = create_default_spotify_data('Veri Yok')
            spotify_profile_display_data['image_url'] = profile_image_url if profile_image_url else default_image_url

        return user_data, spotify_credentials, spotify_profile_display_data

    except Exception as e:
        logger.error(f"Profil verileri işlenirken genel bir hata oluştu (Kullanıcı: {username}): {e}", exc_info=True)
        # Hata durumunda boş ve varsayılan veri yapıları döndür
        return {}, {}, create_default_spotify_data('Hata (Genel)')


__all__ = ["handle_get_request"]

