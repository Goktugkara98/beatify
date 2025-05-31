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
from app.database.models.database import UserRepository, SpotifyRepository
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
    # print(f"ProfileService: handle_get_request çağrıldı - Kullanıcı={username}") # Geliştirme için log

    user_data: Optional[Dict[str, Any]] = None
    spotify_credentials: Optional[Dict[str, Any]] = None
    spotify_profile_display_data: Dict[str, Any]

    try:
        # Adım 1: Kullanıcının temel verilerini al
        user_repo = UserRepository()
        user_data = user_repo.beatify_get_user_data(username)

        if not user_data:
            logger.error(f"Kullanıcı verisi bulunamadı: {username}. Profil sayfası için varsayılan veri döndürülüyor.")
            # Kullanıcı bulunamazsa, diğer bilgileri de boş/varsayılan döndür
            return None, None, create_default_spotify_data('Veri Yok')

        # Adım 2: Kullanıcının Spotify kimlik bilgilerini (Client ID/Secret) al
        spotify_repo = SpotifyRepository()
        spotify_credentials = spotify_repo.spotify_get_user_data(username) # Bu metot Spotify tokenlarını vb. de içerir.

        if not spotify_credentials:
            logger.warning(f"Kullanıcı ({username}) için Spotify kimlik bilgisi (Client ID/Secret) bulunamadı.")
            # Kimlik bilgileri yoksa, Spotify'a bağlı olamaz.
            spotify_profile_display_data = create_default_spotify_data('Veri Yok') # Veya 'Kimlik Bilgisi Yok'
            return user_data, {}, spotify_profile_display_data # spotify_credentials için boş dict

        # Adım 3: Spotify API'sinden güncel profil verilerini al (eğer bağlıysa)
        # `is_spotify_connected` flag'i `user_data` içinde olmalı veya
        # `spotify_credentials` içinde `spotify_user_id` varlığı kontrol edilmeli.
        # Orijinal kodda `spotify_credentials.get('spotify_user_id')` kontrolü yapılıyor.
        
        is_actually_connected_via_oauth = bool(spotify_credentials.get('spotify_user_id') and spotify_credentials.get('refresh_token'))
        # `beatify_users` tablosundaki `is_spotify_connected` flag'i de kontrol edilebilir:
        # is_flagged_as_connected = user_data.get('is_spotify_connected', False)


        if is_actually_connected_via_oauth:
            logger.info(f"Kullanıcı ({username}) Spotify'a bağlı görünüyor. API'den profil verileri çekiliyor...")
            api_service = SpotifyApiService()
            # get_user_profile, geçerli token ile API isteği yapar.
            live_spotify_data: Optional[Dict[str, Any]] = api_service.get_user_profile(username)

            if live_spotify_data and not live_spotify_data.get("error"):
                logger.info(f"Kullanıcı ({username}) için Spotify API'den profil verisi başarıyla alındı.")
                spotify_profile_display_data = live_spotify_data
                spotify_profile_display_data['spotify_data_status'] = 'Bağlı'
                # Gelen verideki resim listesini kontrol et ve varsa ilkini kullan
                images = spotify_profile_display_data.get('images', [])
                spotify_profile_display_data['image_url'] = images[0]['url'] if images and isinstance(images, list) and images[0].get('url') else '/static/img/default_profile.png'

            else: # API'den veri alınamadı veya hata döndü
                logger.warning(f"Kullanıcı ({username}) Spotify'a bağlı olmasına rağmen API'den profil verisi alınamadı veya hata içeriyor. Yanıt: {live_spotify_data}")
                spotify_profile_display_data = create_default_spotify_data('Hata (API Erişimi)')
                # Bu durumda, kullanıcının bağlantısını kontrol etmesi için bir mesaj gösterilebilir.
        else: # Spotify'a OAuth ile bağlanmamış
            logger.info(f"Kullanıcı ({username}) Spotify'a OAuth ile bağlanmamış.")
            # Client ID/Secret girilmiş olabilir ama OAuth akışı tamamlanmamış olabilir.
            if spotify_credentials.get('client_id') and spotify_credentials.get('client_secret'):
                 spotify_profile_display_data = create_default_spotify_data('Bağlı Değil (OAuth Gerekli)')
            else: # Ne OAuth ne de Client ID/Secret var
                 spotify_profile_display_data = create_default_spotify_data('Veri Yok')


        return user_data, spotify_credentials, spotify_profile_display_data

    except Exception as e:
        logger.error(f"Profil verileri işlenirken genel bir hata oluştu (Kullanıcı: {username}): {str(e)}", exc_info=True)
        # Hata durumunda tüm veriler için varsayılan/boş değerler döndür
        return None, None, create_default_spotify_data('Hata (Genel)')

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
