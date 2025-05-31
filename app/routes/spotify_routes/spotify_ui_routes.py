# =============================================================================
# Spotify Kullanıcı Arayüzü Rotaları Modülü (Spotify UI Routes Module)
# =============================================================================
# Bu modül, Spotify entegrasyonu ile ilgili kullanıcı arayüzü (UI)
# sayfalarını sunan Flask rotalarını tanımlar. Şu anda sadece bir
# dashboard yönlendirmesi içermektedir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenlerinin içe aktarılması.
# 2.0 KULLANICI ARAYÜZÜ ROTALARI BAŞLATMA FONKSİYONU (UI ROUTES INITIALIZATION FUNCTION)
#     2.1. init_spotify_ui_routes(app)
#          : Tüm Spotify kullanıcı arayüzü rotalarını belirtilen Flask uygulamasına kaydeder.
#
#     İÇ ROTALAR (init_spotify_ui_routes içinde tanımlanır):
#     -------------------------------------------------------------------------
#     3.0 SPOTIFY DASHBOARD YÖNLENDİRMESİ (SPOTIFY DASHBOARD REDIRECT)
#         3.1. spotify_dashboard()
#              : Kullanıcıyı profil sayfasına yönlendirir.
#                Rota: /spotify/dashboard (GET)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import redirect, url_for, Flask # Flask tipi eklendi
from typing import Any # Tip ipuçları için

# =============================================================================
# 2.0 KULLANICI ARAYÜZÜ ROTALARI BAŞLATMA FONKSİYONU (UI ROUTES INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_spotify_ui_routes(app) : Spotify UI rotalarını kaydeder.
# -----------------------------------------------------------------------------
def init_spotify_ui_routes(app: Flask) -> None:
    """
    Spotify ile ilgili kullanıcı arayüzü (UI) rotalarını
    belirtilen Flask uygulamasına kaydeder.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    # print("Spotify Kullanıcı Arayüzü rotaları başlatılıyor...") # Geliştirme için log

    # =========================================================================
    # 3.0 SPOTIFY DASHBOARD YÖNLENDİRMESİ (SPOTIFY DASHBOARD REDIRECT)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 3.1. spotify_dashboard() : Kullanıcıyı profil sayfasına yönlendirir.
    #      Rota: /spotify/dashboard (GET)
    # -------------------------------------------------------------------------
    @app.route('/spotify/dashboard', methods=['GET'])
    def spotify_dashboard() -> Any: # redirect() Any döndürebilir
        """
        Spotify ile ilgili bir dashboard sayfası için bir endpoint.
        Mevcut implementasyonda, bu rota doğrudan kullanıcının
        profil sayfasına yönlendirme yapar.

        Gelecekte, bu rota gerçek bir Spotify dashboard sayfasını
        render etmek için genişletilebilir.

        Returns:
            Any: Profil sayfasına bir HTTP yönlendirmesi.
        """
        # print("API çağrısı: /spotify/dashboard, profil sayfasına yönlendiriliyor.") # Geliştirme için log
        # 'profile' endpoint'inin uygulamanızda tanımlı olduğunu varsayıyoruz.
        # Eğer farklı bir blueprint altında ise, örn: 'user_bp.profile_page'
        return redirect(url_for('user_bp.profile_page')) # Uygun profil sayfası endpoint'ine yönlendir

    # print("Spotify Kullanıcı Arayüzü rotaları başarıyla yüklendi.") # Geliştirme için log
# =============================================================================
# Spotify Kullanıcı Arayüzü Rotaları Modülü Sonu
# =============================================================================
