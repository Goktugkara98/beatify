# =============================================================================
# Ana Rota Modülü (Main Routes Module)
# =============================================================================
# Bu modül, uygulamanın ana rotalarını (örneğin, ana sayfa, profil sayfası)
# içerir. Rotalar, kullanıcı arayüzünü render etmek, form verilerini işlemek
# ve servis katmanları ile etkileşim kurmak için kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Flask bileşenleri, servisler ve veritabanı depoları.
#
# 2.0  ROTA BAŞLATMA (ROUTE INITIALIZATION)
#      2.1. init_main_routes(app)
#           : Tüm ana rotaları Flask uygulamasına kaydeder.
#
# 3.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      3.1. Genel Rotalar (Public Routes)
#           3.1.1. index() -> @app.route('/')
#           3.1.2. homepage() -> @app.route('/homepage')
#      3.2. Kullanıcı Profili Rotaları (User Profile Routes)
#           3.2.1. profile() -> @app.route('/profile', methods=['GET', 'POST'])
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from typing import Any, Optional, Dict

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Flask,
    Response
)
# Servisler ve Yardımcılar
from app.services.auth_service import login_required, session_is_user_logged_in
from app.services.profile_services import handle_get_request
# Veritabanı Depoları (Sadece POST isteğinde gerekli)
from app.database.spotify_user_repository import SpotifyUserRepository

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 ROTA BAŞLATMA (ROUTE INITIALIZATION)
# =============================================================================
def init_main_routes(app: Flask) -> None:
    """
    Ana uygulama rotalarını belirtilen Flask uygulamasına kaydeder.
    Bu fonksiyon, uygulama başlatıldığında çağrılır.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    
    # =========================================================================
    # 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 3.1. Genel Rotalar (Public Routes)
    # -------------------------------------------------------------------------

    @app.route('/', methods=['GET'])
    def index() -> str:
        """
        Uygulamanın kök URL'si (`/`). Ana sayfaya yönlendirir veya doğrudan
        ana sayfayı render eder.
        """
        logger.info("Ana sayfa (index) render ediliyor.")
        return render_template('homepage.html', title="Ana Sayfa")

    @app.route('/homepage', methods=['GET'])
    def homepage() -> str:
        """
        Uygulamanın ana sayfasını (`/homepage`) render eder.
        """
        logger.info("Ana sayfa (homepage) render ediliyor.")
        return render_template('homepage.html', title="Ana Sayfa")

    # -------------------------------------------------------------------------
    # 3.2. Kullanıcı Profili Rotaları (User Profile Routes)
    # -------------------------------------------------------------------------
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required # Bu sayfaya erişim için giriş zorunludur
    def profile() -> Any:
        """
        Kullanıcı profil sayfasını yönetir.
        - GET: Kullanıcının profil bilgilerini ve Spotify verilerini gösterir.
        - POST: Spotify Client ID ve Secret bilgilerini günceller.
        """
        username = session_is_user_logged_in()
        # login_required dekoratörü sayesinde username'in None olma ihtimali yok,
        # ancak yine de kontrol eklemek güvenli bir yaklaşımdır.
        if not username:
             # Bu kod normalde çalışmaz çünkü login_required yönlendirme yapar.
            flash("Kullanıcı oturumu bulunamadı. Lütfen tekrar giriş yapın.", "error")
            return redirect(url_for('auth_bp.login_page'))

        try:
            if request.method == 'POST':
                return handle_profile_post_request(username)
            else: # GET isteği
                return handle_profile_get_request(username)
        except Exception as e:
            logger.error(f"Profil sayfasında beklenmeyen hata (Kullanıcı: {username}): {e}", exc_info=True)
            flash("Profil sayfası işlenirken beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
            return redirect(url_for('main_bp.homepage'))

def handle_profile_get_request(username: str) -> Response:
    """
    Profil sayfası için GET isteğini işler ve şablonu render eder.
    """
    logger.info(f"Profil sayfası için GET isteği işleniyor: Kullanıcı='{username}'")
    user_data, spotify_credentials, spotify_data = handle_get_request(username)

    if not user_data:
        flash("Kullanıcı bilgileriniz alınamadı. Lütfen tekrar giriş yapın.", "error")
        # auth_bp.logout_page'e yönlendirmek daha mantıklı olabilir
        return redirect(url_for('auth_bp.login_page'))
    
    # Spotify bağlantı durumu hakkında kullanıcıyı bilgilendir
    spotify_status = spotify_data.get('spotify_data_status', 'Bilinmiyor')
    if spotify_status == 'Veri Yok':
        flash("Spotify hesabınız bağlı değil. Müzik özelliklerini kullanmak için lütfen Spotify hesabınıza bağlanın.", "info")
    elif 'Hata' in spotify_status:
        flash(f"Spotify bağlantınızda bir sorun oluştu: {spotify_status}", "warning")
        
    return render_template(
        'profile.html',
        title="Profilim",
        user_data=user_data,
        spotify_credentials=spotify_credentials,
        spotify_data=spotify_data
    )

def handle_profile_post_request(username: str) -> Response:
    """
    Profil sayfasındaki POST isteğini işler (Spotify kimlik bilgileri güncelleme).
    """
    logger.info(f"Profil sayfası için POST isteği işleniyor: Kullanıcı='{username}'")
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()

    if not client_id or not client_secret:
        flash("Spotify Client ID ve Client Secret alanları boş bırakılamaz.", "warning")
        return redirect(url_for('.profile'))

    spotify_repo = SpotifyUserRepository()
    success = spotify_repo.spotify_insert_or_update_client_info(username, client_id, client_secret)

    if success:
        flash('Spotify Client ID ve Secret bilgileri başarıyla güncellendi.', 'success')
        logger.info(f"Kullanıcı '{username}' için Spotify kimlik bilgileri güncellendi.")
    else:
        flash('Spotify bilgileri güncellenirken bir sorun oluştu.', 'danger')
        logger.error(f"Kullanıcı '{username}' için Spotify kimlik bilgileri güncellenemedi.")

    return redirect(url_for('.profile'))

# =============================================================================
# Ana Rota Modülü Sonu
# =============================================================================
