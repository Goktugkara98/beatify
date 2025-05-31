# =============================================================================
# Ana Spotify Servis Fonksiyonları Modülü (Main Spotify Service Functions Module)
# =============================================================================
# Bu modül, Spotify entegrasyonuyla ilgili genel amaçlı servis fonksiyonlarını
# içerir. Bu fonksiyonlar, belirli bir servis sınıfına ait olmayan veya
# birden fazla alt servisin etkileşimini gerektirebilecek genel işlemleri kapsar.
# Örneğin, kullanıcıya ait Spotify Client ID/Secret bilgilerinin güncellenmesi
# ve genel profil verilerinin durumuna göre hazırlanması gibi işlevler burada yer alır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli veritabanı depoları ve alt Spotify servislerinin içe aktarılması.
# 2.0  SPOTIFY SERVİS FONKSİYONLARI (SPOTIFY SERVICE FUNCTIONS)
#      2.1. İstemci Bilgileri Yönetimi (Client Information Management)
#           2.1.1. update_client_id_and_secret_data(username, client_id, client_secret)
#                  : Kullanıcının Spotify Client ID ve Client Secret bilgilerini günceller.
#      2.2. Profil Verisi Alma (Profile Data Retrieval)
#           2.2.1. get_spotify_profile_data(username)
#                  : Kullanıcının Spotify profil verilerini alır ve bağlantı durumuna göre işler.
#           2.2.2. create_default_spotify_data(status)
#                  : Spotify verisi olmadığında veya hata durumunda varsayılan bir profil veri yapısı oluşturur.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging # Loglama için
from app.database.models.database import SpotifyRepository # Spotify veritabanı işlemleri için
from app.services.spotify_services.spotify_api_service import SpotifyApiService # Spotify API etkileşimleri için
from typing import Dict, Any, Optional, Union # Tip ipuçları için

# Logger kurulumu (modül seviyesinde)
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SPOTIFY SERVİS FONKSİYONLARI (SPOTIFY SERVICE FUNCTIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1. İstemci Bilgileri Yönetimi (Client Information Management)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 2.1.1. update_client_id_and_secret_data(...) : Client ID/Secret günceller.
# -----------------------------------------------------------------------------
def update_client_id_and_secret_data(username: str, client_id: str, client_secret: str) -> bool:
    """
    Kullanıcının veritabanında saklanan Spotify Client ID ve Client Secret bilgilerini
    ekler veya günceller. Bu bilgiler, kullanıcının kendi Spotify Developer
    hesabından aldığı ve uygulamanın o kullanıcı adına API istekleri yapabilmesi
    için gerekli olan bilgilerdir.

    Args:
        username (str): Bilgileri güncellenecek Beatify kullanıcısının adı.
        client_id (str): Kullanıcının Spotify Client ID'si.
        client_secret (str): Kullanıcının Spotify Client Secret'ı.

    Returns:
        bool: Güncelleme işlemi başarılıysa True, aksi halde False.
    """
    # print(f"Servis: update_client_id_and_secret_data çağrıldı - Kullanıcı={username}") # Geliştirme için log
    try:
        if not username or not client_id or not client_secret:
            logger.warning(f"Client ID/Secret güncelleme için eksik parametre: Kullanıcı={username}, ClientIDVarMi={bool(client_id)}, ClientSecretVarMi={bool(client_secret)}")
            return False

        spotify_repo = SpotifyRepository()
        # Veritabanı şemasındaki `spotify_insert_or_update_client_info` metodu kullanılıyor.
        # Orijinal koddaki `spotify_add_or_update_client_info` bir yazım hatası olabilir.
        success: bool = spotify_repo.spotify_insert_or_update_client_info(
            username,
            client_id.strip(),
            client_secret.strip()
        )
        if success:
            logger.info(f"Kullanıcı ({username}) için Spotify Client ID/Secret başarıyla güncellendi.")
        else:
            logger.error(f"Kullanıcı ({username}) için Spotify Client ID/Secret güncellenemedi (repo False döndürdü).")
        return success
    except Exception as e:
        logger.error(f"Client ID/Secret güncellenirken hata oluştu (Kullanıcı: {username}): {str(e)}", exc_info=True)
        return False

# -----------------------------------------------------------------------------
# 2.2. Profil Verisi Alma (Profile Data Retrieval)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 2.2.1. get_spotify_profile_data(username) : Spotify profil verilerini alır.
# -----------------------------------------------------------------------------
def get_spotify_profile_data(username: str) -> Dict[str, Any]:
    """
    Belirtilen Beatify kullanıcısının Spotify profil verilerini alır.
    Eğer kullanıcı Spotify'a bağlıysa, API üzerinden güncel verileri çeker.
    Bağlı değilse ancak kimlik bilgileri (Client ID/Secret) girilmişse
    "Bağlı Değil" durumuyla varsayılan veri döndürür. Kimlik bilgileri de yoksa
    "Veri Yok" durumuyla varsayılan veri döndürür. Hata durumunda "Hata"
    durumuyla varsayılan veri döndürür.

    Args:
        username (str): Profil verileri alınacak Beatify kullanıcısının adı.

    Returns:
        Dict[str, Any]: Kullanıcının Spotify profil verilerini ve bağlantı durumunu
                        içeren bir sözlük.
    """
    # print(f"Servis: get_spotify_profile_data çağrıldı - Kullanıcı={username}") # Geliştirme için log
    try:
        # SpotifyApiService, kullanıcıya özel tokenları yönetebilmeli.
        # Bu fonksiyonun çağrıldığı yerde bir SpotifyApiService örneği oluşturuluyor,
        # bu örnek, get_user_profile çağrısında token yönetimini (gerekirse yenileme) yapacaktır.
        api_service = SpotifyApiService() # Her çağrıda yeni örnek oluşturmak yerine,
                                          # dependency injection ile sağlanabilir.
        spotify_data: Optional[Dict[str, Any]] = api_service.get_user_profile(username)

        if spotify_data and not spotify_data.get("error"): # API'den başarılı yanıt ve hata yoksa
            logger.info(f"Kullanıcı ({username}) için Spotify API'den profil verisi başarıyla alındı.")
            spotify_data['spotify_data_status'] = 'Bağlı' # Durum bilgisi ekle
            # Gelen verideki resim listesini kontrol et ve varsa ilkini kullan
            images = spotify_data.get('images', [])
            spotify_data['image_url'] = images[0]['url'] if images and isinstance(images, list) and images[0].get('url') else '/static/img/default_profile.png'
            return spotify_data
        else:
            logger.warning(f"Kullanıcı ({username}) için Spotify API'den profil verisi alınamadı veya hata içeriyor. Yanıt: {spotify_data}")
            # API'den veri alınamadı, veritabanındaki kimlik bilgilerini kontrol et
            spotify_repo = SpotifyRepository()
            credentials: Optional[Dict[str, Any]] = spotify_repo.spotify_get_user_data(username)

            if credentials and credentials.get('client_id') and credentials.get('client_secret'):
                logger.info(f"Kullanıcı ({username}) Spotify'a bağlı değil ama kimlik bilgileri mevcut.")
                return create_default_spotify_data('Bağlı Değil') # "Not Connected" yerine Türkçe
            else:
                logger.info(f"Kullanıcı ({username}) için Spotify kimlik bilgileri de bulunamadı.")
                return create_default_spotify_data('Veri Yok') # "No Data" yerine Türkçe
    except Exception as e:
        logger.error(f"Spotify profil verileri alınırken genel bir hata oluştu (Kullanıcı: {username}): {str(e)}", exc_info=True)
        return create_default_spotify_data('Hata') # "Error" yerine Türkçe

# -----------------------------------------------------------------------------
# 2.2.2. create_default_spotify_data(status) : Varsayılan profil verisi oluşturur.
# -----------------------------------------------------------------------------
def create_default_spotify_data(status: str) -> Dict[str, Any]:
    """
    Spotify profil verisi alınamadığında veya kullanıcı bağlı olmadığında
    kullanılmak üzere varsayılan bir veri yapısı oluşturur.

    Args:
        status (str): Profil verisinin durumunu belirten bir string
                      (örn: 'Bağlı Değil', 'Veri Yok', 'Hata').

    Returns:
        Dict[str, Any]: Varsayılan Spotify profil bilgilerini içeren bir sözlük.
    """
    # print(f"Servis: create_default_spotify_data çağrıldı - Durum={status}") # Geliştirme için log
    default_image_url = '/static/img/default_profile.png' # Varsayılan profil resmi yolu
    return {
        'display_name': 'Bağlı Değil', # Varsayılan görünen ad
        'id': None, # Spotify kullanıcı ID'si
        'email': None, # E-posta (genellikle API'den alınır)
        'country': None, # Ülke (genellikle API'den alınır)
        'images': [{'url': default_image_url, 'height': None, 'width': None}], # Resim listesi formatına uygun
        'image_url': default_image_url, # Kolay erişim için ayrı bir anahtar
        'product': None, # Abonelik türü (örn: "premium", "free")
        'followers': {'total': 0, 'href': None}, # Takipçi bilgisi
        'external_urls': {'spotify': '#'}, # Spotify profil linki
        'uri': None,
        'spotify_data_status': status # Verinin genel durumu
    }

# =============================================================================
# Ana Spotify Servis Fonksiyonları Modülü Sonu
# =============================================================================
