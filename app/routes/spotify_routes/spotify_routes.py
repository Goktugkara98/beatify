# =============================================================================
# Ana Spotify Rota Başlatıcı Modülü (Main Spotify Routes Initializer Module)
# =============================================================================
# Bu modül, Spotify entegrasyonuyla ilgili tüm alt rota modüllerini
# merkezi bir noktadan başlatmaktan sorumludur. Uygulama başlatıldığında,
# bu dosyadaki `init_spotify_routes` fonksiyonu çağrılarak tüm Spotify
# endpoint'lerinin Flask uygulamasına kaydedilmesi sağlanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  ANA BAŞLATICI (MAIN INITIALIZER)
#      2.1. init_spotify_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from flask import Flask

# Alt rota modüllerinin başlatıcıları
from app.routes.spotify_routes.spotify_api_routes import init_spotify_api_routes
from app.routes.spotify_routes.spotify_auth_routes import init_spotify_auth_routes
from app.routes.spotify_routes.spotify_ui_routes import init_spotify_ui_routes
from app.routes.spotify_routes.spotify_widget_routes import init_spotify_widget_routes

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 ANA BAŞLATICI (MAIN INITIALIZER)
# =============================================================================
def init_spotify_routes(app: Flask) -> None:
    """
    Tüm Spotify ile ilgili rota gruplarını (auth, ui, widget, api) başlatır.
    
    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    logger.info("Spotify rota modülleri başlatılıyor...")
    try:
        init_spotify_auth_routes(app)
        init_spotify_ui_routes(app)
        init_spotify_api_routes(app)
        init_spotify_widget_routes(app)
        logger.info("Tüm Spotify rota modülleri başarıyla başlatıldı.")
    except Exception as e:
        logger.critical(f"Spotify rotaları başlatılırken kritik bir hata oluştu: {e}", exc_info=True)
        # Hatanın yukarıya fırlatılması, uygulamanın bu kritik hatayla
        # başlamasını engelleyebilir.
        raise e
