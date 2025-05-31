# =============================================================================
# Ana Spotify Rotaları Başlatma Modülü (Main Spotify Routes Initialization Module)
# =============================================================================
# Bu modül, Spotify ile ilgili tüm alt rota modüllerini (Widget, Kimlik Doğrulama,
# Kullanıcı Arayüzü, API) Flask uygulamasına kaydetmek için merkezi bir
# başlatma fonksiyonu içerir. Uygulamanın Spotify özelliklerine ait tüm
# endpoint'lerin kaydedilmesini sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli alt rota başlatma fonksiyonlarının içe aktarılması.
# 2.0 ANA ROTA BAŞLATMA FONKSİYONU (MAIN ROUTE INITIALIZATION FUNCTION)
#     2.1. init_spotify_routes(app)
#          : Tüm Spotify alt rota modüllerini çağırarak Flask uygulamasına kaydeder.
#          2.1.1. Widget Rotalarının Başlatılması (Widget Routes Initialization)
#          2.1.2. Kimlik Doğrulama Rotalarının Başlatılması (Authentication Routes Initialization)
#          2.1.3. Kullanıcı Arayüzü Rotalarının Başlatılması (UI Routes Initialization)
#          2.1.4. API Rotalarının Başlatılması (API Routes Initialization)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
# Spotify özelliklerine ait farklı rota gruplarını başlatan fonksiyonlar.
from flask import Flask # Flask tipi için
from app.routes.spotify_routes.spotify_auth_routes import init_spotify_auth_routes
from app.routes.spotify_routes.spotify_ui_routes import init_spotify_ui_routes
from app.routes.spotify_routes.spotify_widget_routes import init_spotify_widget_routes
from app.routes.spotify_routes.spotify_api_routes import init_spotify_api_routes
from typing import Any # Tip ipuçları için

# =============================================================================
# 2.0 ANA ROTA BAŞLATMA FONKSİYONU (MAIN ROUTE INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_spotify_routes(app) : Tüm Spotify alt rotalarını kaydeder.
# -----------------------------------------------------------------------------
def init_spotify_routes(app: Flask) -> None:
    """
    Tüm Spotify ile ilgili rota gruplarını (widget, kimlik doğrulama, UI, API)
    belirtilen Flask uygulamasına kaydeder.

    Bu fonksiyon, uygulamanın Spotify entegrasyonuyla ilgili tüm endpoint'lerinin
    merkezi bir noktadan yönetilmesini ve başlatılmasını sağlar.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.

    Raises:
        Exception: Rota başlatma sırasında bir hata oluşursa fırlatılır.
                   Bu, genellikle içe aktarılan modüllerdeki sorunlardan kaynaklanabilir.
    """
    # print("Ana Spotify rotaları başlatılıyor...") # Geliştirme için log
    try:
        # ---------------------------------------------------------------------
        # 2.1.1. Widget Rotalarının Başlatılması (Widget Routes Initialization)
        #          Spotify widget'ları için gerekli endpoint'leri kaydeder.
        # ---------------------------------------------------------------------
        # print("Spotify Widget rotaları başlatılıyor...") # Geliştirme için log
        init_spotify_widget_routes(app)
        # print("Spotify Widget rotaları başarıyla yüklendi.") # Geliştirme için log

        # ---------------------------------------------------------------------
        # 2.1.2. Kimlik Doğrulama Rotalarının Başlatılması (Authentication Routes Initialization)
        #          Spotify OAuth2 kimlik doğrulama akışını yöneten endpoint'leri kaydeder.
        # ---------------------------------------------------------------------
        # print("Spotify Kimlik Doğrulama rotaları başlatılıyor...") # Geliştirme için log
        init_spotify_auth_routes(app)
        # print("Spotify Kimlik Doğrulama rotaları başarıyla yüklendi.") # Geliştirme için log

        # ---------------------------------------------------------------------
        # 2.1.3. Kullanıcı Arayüzü Rotalarının Başlatılması (UI Routes Initialization)
        #          Spotify ile ilgili kullanıcı arayüzü sayfalarını sunan endpoint'leri kaydeder.
        # ---------------------------------------------------------------------
        # print("Spotify Kullanıcı Arayüzü rotaları başlatılıyor...") # Geliştirme için log
        init_spotify_ui_routes(app)
        # print("Spotify Kullanıcı Arayüzü rotaları başarıyla yüklendi.") # Geliştirme için log

        # ---------------------------------------------------------------------
        # 2.1.4. API Rotalarının Başlatılması (API Routes Initialization)
        #          Spotify API'si ile etkileşim kuran ve JSON yanıtları döndüren
        #          arka uç endpoint'lerini kaydeder.
        # ---------------------------------------------------------------------
        # print("Spotify API rotaları başlatılıyor...") # Geliştirme için log
        init_spotify_api_routes(app)
        # print("Spotify API rotaları başarıyla yüklendi.") # Geliştirme için log

        # print("Tüm Spotify rotaları başarıyla yüklendi.") # Geliştirme için log

    except Exception as e:
        # print(f"Spotify rotaları başlatılırken kritik bir hata oluştu: {str(e)}") # Geliştirme için log
        # Hatanın loglanması ve uygulamanın uygun şekilde sonlandırılması veya
        # hata durumunu işlemesi önemlidir. Şimdilik hatayı yukarı fırlatıyoruz.
        raise # Hatayı, uygulamanın ana başlatma kısmının yakalaması için tekrar fırlat

# =============================================================================
# Ana Spotify Rotaları Başlatma Modülü Sonu
# =============================================================================
