# =============================================================================
# Spotify Entegrasyon Yapılandırma Modülü (Spotify Integration Configuration Module)
# =============================================================================
# Bu modül, Spotify API ile entegrasyon için gerekli yapılandırma
# ayarlarını ve sabitlerini içerir. API endpoint'leri, OAuth ayarları,
# widget yapılandırmaları ve ilgili metodlar burada tanımlanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Python modüllerinin ve tiplerinin içe aktarılması.
# 2.0 YAPILANDIRMA SINIFI (CONFIGURATION CLASS - SpotifyConfig)
#     : Spotify ile ilgili tüm yapılandırma ayarlarını içeren sınıf.
#     2.1. API ENDPOINT'LERİ (API Endpoints)
#          : Spotify API'sinin temel URL adresleri.
#     2.2. OAUTH AYARLARI (OAuth Settings)
#          : Spotify API kimlik doğrulaması için gerekli OAuth2 ayarları.
#     2.3. WIDGET AYARLARI (Widget Settings)
#          : Spotify widget'larının görünümü ve davranışı ile ilgili ayarlar.
#     2.4. YARDIMCI METOD (HELPER METHOD - get_widget_config)
#          : Widget yapılandırmasını toplu olarak döndüren metod.
# 3.0 YAPILANDIRMA NESNESİ (CONFIGURATION INSTANCE)
#     : SpotifyConfig sınıfından oluşturulan ve uygulama genelinde kullanılacak nesne.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import os
from typing import Dict, Any, List # Gerekli tipler eklendi

# =============================================================================
# 2.0 YAPILANDIRMA SINIFI (CONFIGURATION CLASS - SpotifyConfig)
# =============================================================================
class SpotifyConfig:
    """
    Spotify API entegrasyonu için yapılandırma ayarlarını ve sabitlerini barındırır.
    Bu sınıf, API endpoint'leri, OAuth kimlik doğrulama detayları ve
    uygulamada kullanılabilecek Spotify widget'larının özelliklerini tanımlar.
    """

    # -----------------------------------------------------------------------------
    # 2.1. API ENDPOINT'LERİ (API Endpoints)
    #      Spotify API'sinin çeşitli işlevleri için temel URL adresleri.
    # -----------------------------------------------------------------------------
    # AUTH_URL: Spotify kullanıcı kimlik doğrulama (authorization) uç noktası.
    AUTH_URL: str = "https://accounts.spotify.com/authorize"

    # TOKEN_URL: Erişim (access) ve yenileme (refresh) token'larını almak için kullanılan uç nokta.
    TOKEN_URL: str = "https://accounts.spotify.com/api/token"

    # API_BASE_URL: Spotify Web API'sinin temel adresi.
    API_BASE_URL: str = "https://api.spotify.com/v1"

    # PROFILE_URL: Mevcut kullanıcının profil bilgilerini almak için API uç noktası.
    PROFILE_URL: str = f"{API_BASE_URL}/me"

    # -----------------------------------------------------------------------------
    # 2.2. OAUTH AYARLARI (OAuth Settings)
    #      Spotify API'si ile güvenli kimlik doğrulama için OAuth2 parametreleri.
    # -----------------------------------------------------------------------------
    # CLIENT_ID: Spotify Developer Dashboard'dan alınan uygulama İstemci ID'si.
    #            Ortam değişkeninden okunması güvenlik açısından önemlidir.
    CLIENT_ID: str | None = os.environ.get("SPOTIFY_CLIENT_ID")

    # CLIENT_SECRET: Spotify Developer Dashboard'dan alınan uygulama İstemci Sırrı.
    #                Ortam değişkeninden okunması güvenlik açısından çok önemlidir.
    CLIENT_SECRET: str | None = os.environ.get("SPOTIFY_CLIENT_SECRET")

    # REDIRECT_URI: Spotify kimlik doğrulamasından sonra kullanıcının yönlendirileceği URI.
    #               Spotify Developer Dashboard'da tanımlanmış olmalıdır.
    REDIRECT_URI: str = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:5000/spotify/callback")

    # SCOPES: Uygulamanın kullanıcı adına erişmek istediği Spotify API izinleri.
    #         İzinler boşlukla ayrılarak birleştirilir.
    SCOPES: str = " ".join([
        # Kullanıcı Bilgileri (User Information)
        "user-read-private",          # Kullanıcının abonelik türü ve ülke gibi özel bilgilerini okuma
        "user-read-email",            # Kullanıcının kayıtlı e-posta adresini okuma

        # Kütüphane ve Takip (Library and Following)
        "user-library-read",          # Kullanıcının kaydettiği şarkıları ve albümleri okuma
        "user-library-modify",        # Kullanıcının kütüphanesine şarkı/albüm ekleme veya çıkarma
        "user-follow-read",           # Kullanıcının takip ettiği sanatçıları ve kullanıcıları okuma
        "user-follow-modify",         # Sanatçıları veya kullanıcıları takip etme/bırakma

        # Çalma Geçmişi ve Durum (Playback History and State)
        "user-read-recently-played",  # Kullanıcının son dinlediği parçaları okuma
        "user-read-playback-state",   # Mevcut çalma durumunu (cihaz, parça, ilerleme) okuma
        "user-modify-playback-state", # Çalmayı kontrol etme (oynat, duraklat, sonraki, önceki, ses ayarı)
        "user-read-currently-playing",# O anda çalmakta olan parçayı okuma

        # Çalma Listeleri (Playlists)
        "playlist-read-private",      # Kullanıcının özel çalma listelerini okuma
        "playlist-read-collaborative",# Kullanıcının işbirlikçi olduğu çalma listelerini okuma
        "playlist-modify-private",    # Kullanıcının özel çalma listelerini düzenleme (şarkı ekleme/çıkarma)
        "playlist-modify-public",     # Kullanıcının herkese açık çalma listelerini düzenleme
    ])

    # -----------------------------------------------------------------------------
    # 2.3. WIDGET AYARLARI (Widget Settings)
    #      Uygulama içinde gösterilebilecek Spotify widget'larının yapılandırması.
    # -----------------------------------------------------------------------------
    # WIDGET_TOKEN_EXPIRY_DAYS: Widget için oluşturulan token'ların geçerlilik süresi (gün).
    WIDGET_TOKEN_EXPIRY_DAYS: int = 30

    # WIDGET_TYPES: Kullanılabilir widget türleri ve açıklamaları.
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

    # WIDGET_SIZES: Widget'lar için önceden tanımlanmış boyut seçenekleri.
    WIDGET_SIZES: Dict[str, Dict[str, int]] = {
        "small": {"width": 300, "height": 80},
        "medium": {"width": 400, "height": 120},
        "large": {"width": 500, "height": 160}
    }

    # WIDGET_THEMES: Widget'lar için önceden tanımlanmış tema seçenekleri.
    WIDGET_THEMES: Dict[str, Dict[str, str]] = {
        "dark": {
            "background": "#121212", # Koyu arka plan rengi
            "text": "#FFFFFF",       # Açık metin rengi
            "accent": "#1DB954"      # Spotify yeşili vurgu rengi
        },
        "light": {
            "background": "#FFFFFF", # Açık arka plan rengi
            "text": "#121212",       # Koyu metin rengi
            "accent": "#1DB954"      # Spotify yeşili vurgu rengi
        }
    }

    # -----------------------------------------------------------------------------
    # 2.4. YARDIMCI METOD (HELPER METHOD - get_widget_config)
    #      Widget yapılandırmasını toplu olarak döndürür.
    # -----------------------------------------------------------------------------
    @classmethod
    def get_widget_config(cls) -> Dict[str, Any]:
        """
        Tüm widget yapılandırma seçeneklerini içeren bir sözlük döndürür.
        Bu metod, widget ayarlarını (türler, boyutlar, temalar) tek bir
        yerden almayı kolaylaştırır.

        Returns:
            Dict[str, Any]: Widget türlerini, boyutlarını ve temalarını içeren sözlük.
        """
        return {
            "types": cls.WIDGET_TYPES,
            "sizes": cls.WIDGET_SIZES,
            "themes": cls.WIDGET_THEMES
        }

# =============================================================================
# 3.0 YAPILANDIRMA NESNESİ (CONFIGURATION INSTANCE)
# =============================================================================
# SPOTIFY_CONFIG: SpotifyConfig sınıfından oluşturulan ve uygulama genelinde
#                 Spotify yapılandırma ayarlarına erişmek için kullanılacak olan nesne.
SPOTIFY_CONFIG: SpotifyConfig = SpotifyConfig()

# =============================================================================
# Yapılandırma Dosyası Sonu
# =============================================================================
