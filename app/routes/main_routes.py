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
# 2.0  SABİTLER & YARDIMCILAR (CONSTANTS & HELPERS)
#      2.1. logger
#      2.2. ALLOWED_EXTENSIONS
#      2.3. allowed_file(filename)
#
# 3.0  ROTA BAŞLATMA (ROUTE INITIALIZATION)
#      3.1. init_main_routes(app)
#           : Tüm ana rotaları Flask uygulamasına kaydeder.
#
# 4.0  ROTA TANIMLARI (ROUTE DEFINITIONS) [init_main_routes içinde]
#      4.1. Genel Rotalar (Public Routes)
#           4.1.1. index() -> @app.route('/', methods=['GET'])
#           4.1.2. homepage() -> @app.route('/homepage', methods=['GET'])
#           4.1.3. docs() -> @app.route('/docs', methods=['GET'])
#           4.1.4. changelog() -> @app.route('/changelog', methods=['GET'])
#      4.2. Kullanıcı Profili Rotaları (User Profile Routes)
#           4.2.1. profile() -> @app.route('/profile', methods=['GET', 'POST'])
#
# 5.0  PROFİL YARDIMCILARI (PROFILE HELPERS)
#      5.1. handle_profile_get_request(username)
#      5.2. handle_profile_post_request(username)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
import logging
import os
from typing import Any, Dict, Optional

# Üçüncü parti
from flask import Flask, Response, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# Uygulama içi: servisler ve yardımcılar
from app.services.auth_service import login_required, session_is_user_logged_in
from app.services.users.profile_service import handle_get_request

# Uygulama içi: veritabanı depoları (sadece POST/işlem tarafında gerekli)
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.database.repositories.user_repository import BeatifyUserRepository

# =============================================================================
# 2.0 SABİTLER & YARDIMCILAR (CONSTANTS & HELPERS)
# =============================================================================

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename: str) -> bool:
    """Yüklenen dosya uzantısının izinli olup olmadığını kontrol eder."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# 3.0 ROTA BAŞLATMA (ROUTE INITIALIZATION)
# =============================================================================
def init_main_routes(app: Flask) -> None:
    """
    Ana uygulama rotalarını belirtilen Flask uygulamasına kaydeder.
    Bu fonksiyon, uygulama başlatıldığında çağrılır.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    
    # =========================================================================
    # 4.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 4.1. Genel Rotalar (Public Routes)
    # -------------------------------------------------------------------------

    @app.route('/', methods=['GET'])
    def index() -> str:
        """
        Uygulamanın kök URL'si (`/`). Ana sayfaya yönlendirir veya doğrudan
        ana sayfayı render eder.
        """
        logger.info("Yeni ana sayfa (index.html) render ediliyor.")
        return render_template('index.html', title="Ana Sayfa")

    @app.route('/homepage', methods=['GET'])
    def homepage() -> str:
        """
        Uygulamanın ana sayfasını (`/homepage`) render eder.
        """
        logger.info("Ana sayfa (homepage) render ediliyor.")
        return render_template('index.html', title="Ana Sayfa")

    @app.route('/docs', methods=['GET'])
    def docs() -> str:
        """
        Dokümantasyon sayfasını (`/docs`) render eder.
        (Şimdilik boş bir şablon kullanılır.)
        """
        logger.info("Dokümantasyon sayfası (docs.html) render ediliyor.")
        return render_template('docs.html', title="Dokümantasyon")

    @app.route('/changelog', methods=['GET'])
    def changelog() -> str:
        """
        Yenilikler / değişiklikler sayfasını (`/changelog`) render eder.
        (Şimdilik boş bir şablon kullanılır.)
        """
        logger.info("Yenilikler sayfası (changelog.html) render ediliyor.")
        return render_template('changelog.html', title="Yenilikler")

    # -------------------------------------------------------------------------
    # 4.2. Kullanıcı Profili Rotaları (User Profile Routes)
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
            else:  # GET isteği
                return handle_profile_get_request(username)
        except Exception as e:
            logger.error(f"Profil sayfasında beklenmeyen hata (Kullanıcı: {username}): {e}", exc_info=True)
            flash("Profil sayfası işlenirken beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
            return redirect(url_for('homepage'))

# =============================================================================
# 5.0 PROFİL YARDIMCILARI (PROFILE HELPERS)
# =============================================================================

def handle_profile_get_request(username: str) -> Response:
    """
    Profil sayfası için GET isteğini işler ve şablonu render eder.
    """
    logger.info(f"Profil sayfası için GET isteği işleniyor: Kullanıcı='{username}'")
    user_data, spotify_credentials, spotify_data = handle_get_request(username)

    if not user_data:
        flash("Kullanıcı bilgileriniz alınamadı. Lütfen tekrar giriş yapın.", "error")
        # auth_bp.logout_page'e yönlendirmek daha mantıklı olabilir
        return redirect(url_for('login'))
    
    # Spotify bağlantı durumu hakkında kullanıcıyı bilgilendir
    spotify_status = spotify_data.get('spotify_data_status', 'Bilinmiyor')
    if 'Hata' in spotify_status:
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
    Profil sayfasındaki POST isteğini işler.
    - action='update_profile': Kullanıcı bilgilerini günceller.
    - action='update_spotify_creds': Spotify kimlik bilgilerini günceller.
    """
    logger.info(f"Profil sayfası için POST isteği işleniyor: Kullanıcı='{username}'")
    
    action = request.form.get('action')

    # 1. Profil Güncelleme İşlemi
    if action == 'update_profile':
        new_email = request.form.get('email', '').strip()
        
        # Kullanıcı nesnesi oluştur
        user_repo = BeatifyUserRepository()
        
        # -- Profil Resmi Yükleme --
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    
                    # Benzersiz dosya adı oluştur (uuid4)
                    # Önbellek sorunlarını önlemek için bu yöntem tercih edilir
                    import uuid
                    unique_filename = f"{uuid.uuid4().hex}.{ext}"
                    
                    # Klasörün varlığından emin ol
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    upload_folder = os.path.join(base_dir, 'static', 'img', 'uploads', 'profiles')
                    
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    # Yeni dosyayı kaydet
                    try:
                        file_path = os.path.join(upload_folder, unique_filename)
                        file.save(file_path)
                        
                        # Veritabanını güncelle
                        if user_repo.update_profile_image(username, unique_filename):
                            logger.info(f"Kullanıcı '{username}' profil resmini güncelledi: {unique_filename}")
                            
                            # (Opsiyonel) Eski resmi silmek için veritabanından eski değeri okuyup silmek gerekirdi
                            # Şimdilik eski resimler kalıyor, bir temizlik scripti ile temizlenebilir.
                        else:
                             logger.error(f"Profil resmi veritabanına kaydedilemedi: {username}")
                             
                    except Exception as e:
                        logger.error(f"Dosya kaydedilirken hata oluştu: {e}")
                else:
                    # Geçersiz dosya formatı sessizce loglanabilir
                    logger.warning(f"Kullanıcı '{username}' geçersiz dosya yüklemeye çalıştı.")

        if not new_email:
            # E-posta boşsa işlem yapma, sessizce redirect
            return redirect(url_for('.profile'))
        
        if user_repo.update_user_email(username, new_email):
            # Eğer sadece resim güncellendiyse ve email değişmediyse bile burası çalışır ve sorun olmaz.
            logger.info(f"Kullanıcı '{username}' e-posta adresini güncelledi.")
        else:
            logger.error(f"Kullanıcı '{username}' profil güncelleme hatası.")
            
        return redirect(url_for('.profile', tab='account'))

    # 2. Spotify Credential Güncelleme İşlemi (Varsayılan veya 'update_spotify_creds')
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()

    if not client_id or not client_secret:
        flash("Spotify Client ID ve Client Secret alanları boş bırakılamaz.", "warning")
        # Hata durumunda da spotify sekmesinde kalması iyi olur
        return redirect(url_for('.profile', tab='spotify'))

    spotify_repo = SpotifyUserRepository()
    success = spotify_repo.store_client_info(username, client_id, client_secret)

    if success:
        logger.info(f"Kullanıcı '{username}' için Spotify kimlik bilgileri güncellendi.")
    else:
        logger.error(f"Kullanıcı '{username}' için Spotify kimlik bilgileri güncellenemedi.")

    # İşlem başarılı olsa da olmasa da Spotify sekmesine yönlendir
    return redirect(url_for('.profile', tab='spotify'))

# =============================================================================
# Ana Rota Modülü Sonu
# =============================================================================
