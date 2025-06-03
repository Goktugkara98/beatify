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
#      : Gerekli Python modülleri, veritabanı depoları ve diğer servislerin
#        içe aktarılması.
# 2.0  PROFİL VERİ FONKSİYONLARI (PROFILE DATA FUNCTIONS)
#      2.1. GET İsteği İşleyici (GET Request Handler)
#           2.1.1. handle_get_request(username)
#                  : Kullanıcının profil sayfası için gerekli tüm verileri toplar ve döndürür.
# 3.0  YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
#      : Bu modül, varsayılan Spotify veri oluşturma işlevi için
#        `app.services.spotify_services.spotify_service` modülündeki
#        `create_default_spotify_data` fonksiyonunu kullanır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging # Hata ve bilgi loglaması için
from typing import Optional, Dict, Any, Tuple # Tip ipuçları için

# Veritabanı etkileşimi için Repository sınıfları
from app.database.beatify_user_repository import BeatifyUserRepository
from app.database.spotify_user_repository import SpotifyUserRepository
# Spotify API'si ile etkileşim için servis
from app.services.spotify_services.spotify_api_service import SpotifyApiService
# Varsayılan Spotify veri yapısını oluşturmak için yardımcı fonksiyon
# Bu import, profile_services.py dosyasındaki yerel create_default_spotify_data
# tanımı yerine kullanılacaktır.
from app.services.spotify_services.spotify_service import create_default_spotify_data

# Logger kurulumu (modül seviyesinde)
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 PROFİL VERİ FONKSİYONLARI (PROFILE DATA FUNCTIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1. GET İsteği İşleyici (GET Request Handler)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 2.1.1. handle_get_request(username) : Profil sayfası verilerini toplar.
# -----------------------------------------------------------------------------
def handle_get_request(username: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Kullanıcının profil sayfası için gerekli verileri toplar. Bu veriler arasında
    kullanıcının temel bilgileri, Spotify kimlik bilgileri (Client ID/Secret)
    ve eğer Spotify'a bağlıysa Spotify'dan alınan profil verileri bulunur.

    Args:
        username (str): Profil verileri alınacak Beatify kullanıcısının adı.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Dict[str, Any]]:
            - user_data: Kullanıcının veritabanındaki bilgileri veya None.
            - spotify_credentials: Kullanıcının Spotify Client ID/Secret bilgileri veya None.
            - spotify_profile_display_data: Spotify profil verileri veya varsayılan yapı.
                                            Bu veri, `create_default_spotify_data` ile
                                            oluşturulmuş ve bağlantı durumunu içerir.
    """
    logger.info(f"Profil sayfası için GET isteği işleniyor: Kullanıcı={username}")
    print(f"[DEBUG] ProfileService: handle_get_request çağrıldı - Kullanıcı={username}")

    # Varsayılan değerler
    user_data: Dict[str, Any] = {}
    spotify_credentials: Dict[str, Any] = {}
    spotify_profile_display_data: Dict[str, Any] = {}

    try:
        # Adım 1: Kullanıcının temel verilerini al
        user_repo = BeatifyUserRepository()
        user_data = user_repo.beatify_get_user_data(username)

        if not user_data:
            error_msg = f"Kullanıcı verisi bulunamadı: {username}"
            logger.error(error_msg)
            # Kullanıcı bulunamazsa, boş bir kullanıcı sözlüğü ve varsayılan spotify verisi döndür
            return ({}, {}, create_default_spotify_data('Veri Yok'))

        # Adım 2: Kullanıcının Spotify kimlik bilgilerini (Client ID/Secret) al
        spotify_repo = SpotifyUserRepository()
        spotify_credentials = spotify_repo.spotify_get_user_data(username) or {}
        
        # Spotify kimlik bilgileri yoksa veya boşsa
        if not spotify_credentials:
            logger.warning(f"Kullanıcı ({username}) için Spotify kimlik bilgisi (Client ID/Secret) bulunamadı.")
            # Varsayılan kimlik bilgisi yapısını oluştur
            spotify_credentials = {
                'client_id': None,
                'client_secret': None,
                'spotify_user_id': None,
                'access_token': None,
                'refresh_token': None,
                'token_expires_at': None,
                'spotify_data_status': 'Veri Yok'
            }
            spotify_profile_display_data = create_default_spotify_data('Veri Yok')
            return user_data, spotify_credentials, spotify_profile_display_data

        # Adım 3: Spotify bağlantı durumunu kontrol et ve uygun veriyi hazırla
        is_actually_connected_via_oauth = bool(
            spotify_credentials.get('spotify_user_id') and 
            spotify_credentials.get('refresh_token')
        )
        
        # Kullanıcının Client ID/Secret bilgileri var mı kontrol et
        has_credentials = bool(
            spotify_credentials.get('client_id') and 
            spotify_credentials.get('client_secret')
        )
        
        print(f"[DEBUG] Spotify bağlantı durumu - OAuth: {is_actually_connected_via_oauth}, Kimlik Bilgileri: {has_credentials}")
        
        if is_actually_connected_via_oauth:
            # Kullanıcı Spotify'a bağlı, API'den güncel verileri al
            logger.info(f"Kullanıcı ({username}) Spotify'a bağlı görünüyor. API'den profil verileri çekiliyor...")
            try:
                api_service = SpotifyApiService()
                live_spotify_data = api_service.get_user_profile(username) or {}
                
                if not live_spotify_data.get("error"):
                    logger.info(f"Kullanıcı ({username}) için Spotify API'den profil verisi başarıyla alındı.")
                    spotify_profile_display_data = live_spotify_data
                    spotify_profile_display_data['spotify_data_status'] = 'Bağlı'
                    
                    # Profil resmini ayarla
                    images = spotify_profile_display_data.get('images', [])
                    if images and isinstance(images, list) and images[0].get('url'):
                        spotify_profile_display_data['image_url'] = images[0]['url']
                    else:
                        spotify_profile_display_data['image_url'] = '/static/img/default_profile.png'
                else:
                    # API'den hata döndü
                    logger.warning(f"Spotify API'sinden hata yanıtı alındı: {live_spotify_data}")
                    spotify_profile_display_data = create_default_spotify_data('Hata (API Erişimi)')
                    
            except Exception as api_error:
                logger.error(f"Spotify API'sine bağlanırken hata oluştu: {str(api_error)}", exc_info=True)
                spotify_profile_display_data = create_default_spotify_data('Hata (API Bağlantısı)')
                
        elif has_credentials:
            # Kullanıcının kimlik bilgileri var ama OAuth bağlantısı yok
            logger.info(f"Kullanıcı ({username}) Spotify kimlik bilgilerine sahip ama OAuth ile bağlı değil.")
            spotify_profile_display_data = create_default_spotify_data('Bağlı Değil (OAuth Gerekli)')
        else:
            # Hiçbir bağlantı yok
            logger.info(f"Kullanıcı ({username}) için Spotify bağlantısı bulunamadı.")
            spotify_profile_display_data = create_default_spotify_data('Veri Yok')


        print(f"[DEBUG] Profil verileri başarıyla hazırlandı: user_data={bool(user_data)}, spotify_credentials={bool(spotify_credentials)}")
        return (user_data or {}, 
                spotify_credentials or {}, 
                spotify_profile_display_data or create_default_spotify_data('Veri Yok'))

    except Exception as e:
        error_msg = f"Profil verileri işlenirken genel bir hata oluştu (Kullanıcı: {username}): {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"[ERROR] {error_msg}")
        # Hata durumunda boş veri yapıları döndür
        return ({}, {}, create_default_spotify_data('Hata (Genel)'))

# =============================================================================
# 3.0 YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
# =============================================================================
# Bu modüldeki `create_default_spotify_data` fonksiyonu, `app.services.spotify_services.spotify_service`
# modülünden import edildiği için burada tekrar tanımlanmasına gerek yoktur.
# Orijinal dosyada yerel bir tanım vardı, ancak tutarlılık için import edilenin
# kullanılması tercih edilir. Eğer bu modüle özel farklı bir varsayılan veri yapısı
# gerekiyorsa, o zaman burada farklı bir isimle tanımlanabilir.
# Mevcut durumda, import edilen fonksiyonun kullanıldığı varsayılmaktadır.

# =============================================================================
# Profil Servisleri Modülü Sonu
# =============================================================================
