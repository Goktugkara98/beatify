# =============================================================================
# Profil Servisleri Modülü (Profile Services Module)
# =============================================================================
# Bu modül, kullanıcı profili sayfası için gerekli verileri hazırlama ve
# ilgili işlemleri yönetme gibi servis fonksiyonlarını içerir.
# Kullanıcı bilgilerini, Spotify kimlik bilgilerini ve Spotify'dan alınan
# profil verilerini bir araya getirerek profil sayfasının ihtiyaç duyduğu
# veriyi oluşturur.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli modüllerin ve bileşenlerin içe aktarılması.
#
# 2.0  PROFİL VERİ SERVİSİ (PROFILE DATA SERVICE)
#      2.1. handle_get_request(username)
#           : Kullanıcının profil sayfası için gerekli tüm verileri (kullanıcı bilgileri,
#             Spotify kimlik bilgileri ve Spotify API verileri) toplayıp birleştirir.
#
# 3.0  HARİCİ YARDIMCI FONKSİYONLAR (EXTERNAL HELPER FUNCTIONS)
#      : Bu modül, varsayılan Spotify veri yapısını oluşturmak için harici olarak
#        `app.services.spotify_services.spotify_service` modülündeki
#        `create_default_spotify_data` fonksiyonunu kullanır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from typing import Optional, Dict, Any, Tuple

from app.database.beatify_user_repository import BeatifyUserRepository
from app.database.spotify_user_repository import SpotifyUserRepository
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from app.services.spotify_services.spotify_service import create_default_spotify_data

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 PROFİL VERİ SERVİSİ (PROFILE DATA SERVICE)
# =============================================================================

def handle_get_request(username: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Kullanıcının profil sayfası için gerekli verileri toplar.
    
    Bu fonksiyon, kullanıcının temel bilgilerini, Spotify kimlik bilgilerini 
    (Client ID/Secret) ve Spotify API'sinden alınan güncel profil verilerini
    birleştirerek döndürür.

    Args:
        username (str): Profil verileri alınacak Beatify kullanıcısının adı.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
            - user_data: Kullanıcının veritabanındaki bilgileri.
            - spotify_credentials: Kullanıcının Spotify Client ID/Secret bilgileri.
            - spotify_profile_display_data: Görüntülenecek Spotify profil verileri.
    """
    logger.info(f"Profil sayfası için GET isteği işleniyor: Kullanıcı='{username}'")

    try:
        # 1. Kullanıcının temel verilerini al
        user_repo = BeatifyUserRepository()
        user_data = user_repo.beatify_get_user_data(username)
        if not user_data:
            logger.error(f"Kullanıcı verisi bulunamadı: {username}")
            return {}, {}, create_default_spotify_data('Veri Yok')

        # 2. Spotify kimlik bilgilerini (Client ID/Secret) al
        spotify_repo = SpotifyUserRepository()
        spotify_credentials = spotify_repo.spotify_get_user_data(username) or {}
        
        # 3. Spotify bağlantı durumuna göre görüntülenecek veriyi hazırla
        is_oauth_connected = bool(spotify_credentials.get('refresh_token'))
        has_client_credentials = bool(spotify_credentials.get('client_id'))

        if is_oauth_connected:
            # OAuth ile bağlıysa, API'den canlı veri çek
            logger.info(f"Kullanıcı '{username}' OAuth ile bağlı. API'den profil verileri çekiliyor.")
            api_service = SpotifyApiService()
            live_spotify_data = api_service.get_user_profile(username)
            
            if live_spotify_data and not live_spotify_data.get("error"):
                spotify_profile_display_data = live_spotify_data
                spotify_profile_display_data['spotify_data_status'] = 'Bağlı'
                images = spotify_profile_display_data.get('images', [])
                spotify_profile_display_data['image_url'] = images[0]['url'] if images else '/static/img/default_profile.png'
                logger.info(f"Kullanıcı '{username}' için Spotify API'den veri başarıyla alındı.")
            else:
                logger.warning(f"Kullanıcı '{username}' için Spotify API'sinden hata yanıtı alındı: {live_spotify_data}")
                spotify_profile_display_data = create_default_spotify_data('Hata (API Erişimi)')
        
        elif has_client_credentials:
            # Sadece kimlik bilgileri var, OAuth bağlantısı yok
            logger.info(f"Kullanıcı '{username}' kimlik bilgilerine sahip ama OAuth ile bağlı değil.")
            spotify_profile_display_data = create_default_spotify_data('Bağlı Değil (OAuth Gerekli)')
        
        else:
            # Hiçbir Spotify bilgisi yok
            logger.info(f"Kullanıcı '{username}' için Spotify bağlantısı bulunamadı.")
            spotify_profile_display_data = create_default_spotify_data('Veri Yok')

        return user_data, spotify_credentials, spotify_profile_display_data

    except Exception as e:
        logger.error(f"Profil verileri işlenirken genel bir hata oluştu (Kullanıcı: {username}): {e}", exc_info=True)
        # Hata durumunda boş ve varsayılan veri yapıları döndür
        return {}, {}, create_default_spotify_data('Hata (Genel)')

# =============================================================================
# 3.0 HARİCİ YARDIMCI FONKSİYONLAR (EXTERNAL HELPER FUNCTIONS)
# =============================================================================
# Bu modül, `create_default_spotify_data` fonksiyonunu harici bir servisten
# (`app.services.spotify_services.spotify_service`) import ederek kullanır.
# Bu nedenle, bu fonksiyonun tanımı bu dosya içinde yer almaz.

# =============================================================================
# Profil Servisleri Modülü Sonu
# =============================================================================
