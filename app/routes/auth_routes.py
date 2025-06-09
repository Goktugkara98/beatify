# =============================================================================
# Kimlik Doğrulama Rota Modülü (Authentication Routes Module)
# =============================================================================
# Bu modül, kullanıcı kimlik doğrulama işlemlerini (kayıt, giriş, çıkış,
# parola sıfırlama) yöneten tüm rotaları içerir. Rotalar, kullanıcı
# arayüzünü render etmek, form verilerini işlemek ve auth_service ile
# etkileşim kurmak için kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Flask bileşenleri ve servis katmanı.
#
# 2.0  YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
#      : Rota içindeki karmaşık mantığı basitleştiren fonksiyonlar.
#      2.1. _handle_register_post(form_data)
#      2.2. _handle_login_post(form_data)
#
# 3.0  ROTA BAŞLATMA (ROUTE INITIALIZATION)
#      3.1. init_auth_routes(app)
#           : Tüm kimlik doğrulama rotalarını Flask uygulamasına kaydeder.
#
# 4.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      4.1. Kayıt (Register)
#           4.1.1. register() -> @app.route('/register', methods=['GET', 'POST'])
#      4.2. Giriş (Login)
#           4.2.1. login() -> @app.route('/login', methods=['GET', 'POST'])
#      4.3. Çıkış (Logout)
#           4.3.1. logout() -> @app.route('/logout', methods=['GET'])
#      4.4. Parola Sıfırlama (Password Reset)
#           4.4.1. reset_password() -> @app.route('/reset_password', methods=['GET', 'POST'])
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from typing import Any, Optional, Dict
from werkzeug.wrappers import Response as WerkzeugResponse
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    Flask,
    Response
)

# Servisler ve Yardımcılar
from app.services import auth_service

# Logger kurulumu
logger = logging.getLogger(__name__)


# =============================================================================
# 2.0 YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
# =============================================================================

def _handle_register_post(form_data: Dict[str, Any]) -> WerkzeugResponse:
    """
    Kullanıcı kayıt (register) POST isteğini işler.
    Form verilerini doğrular ve auth_service aracılığıyla kayıt işlemini yapar.
    """
    username = form_data.get('username')
    email = form_data.get('email')
    password = form_data.get('password')

    if not all([username, email, password]):
        flash('Lütfen tüm alanları doldurun.', 'danger')
        return render_template('auth/register.html', title="Kayıt Ol")

    if len(password) < 8:
        flash('Parola en az 8 karakter uzunluğunda olmalıdır.', 'danger')
        return render_template('auth/register.html', title="Kayıt Ol")

    try:
        logger.info(f"Yeni kullanıcı kaydı deneniyor: Kullanıcı Adı='{username}', Email='{email}'")
        auth_service.beatify_register(username, email, password)
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        logger.info(f"Kullanıcı '{username}' başarıyla kaydedildi.")
        return redirect(url_for('auth_bp.login'))
    except ValueError as ve:
        logger.warning(f"Kayıt hatası (ValueError): Kullanıcı='{username}', Hata: {ve}")
        flash(str(ve), 'danger')
        return render_template('auth/register.html', title="Kayıt Ol", username=username, email=email)
    except Exception as e:
        logger.error(f"Kayıt sırasında beklenmedik hata: Kullanıcı='{username}', Hata: {e}", exc_info=True)
        flash('Kayıt sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.', 'danger')
        return render_template('auth/register.html', title="Kayıt Ol", username=username, email=email)


def _handle_login_post(form_data: Dict[str, Any]) -> WerkzeugResponse:
    """
    Kullanıcı giriş (login) POST isteğini işler.
    Kullanıcıyı doğrular ve oturum açar.
    """
    username = form_data.get('username')
    password = form_data.get('password')
    remember_me = form_data.get('remember') == 'on'

    if not all([username, password]):
        flash('Lütfen kullanıcı adı ve parola girin.', 'danger')
        return render_template('auth/login.html', title="Giriş Yap")

    try:
        logger.info(f"Kullanıcı giriş denemesi: Kullanıcı Adı='{username}'")
        response = auth_service.beatify_log_in(username, password, remember_me)
        flash('Başarıyla giriş yaptınız.', 'success')
        logger.info(f"Kullanıcı '{username}' başarıyla giriş yaptı.")
        
        # Servis bir response döndürürse (örn. set_cookie) onu kullan
        if response:
            return response
        
        return redirect(url_for('main_bp.homepage'))

    except ValueError as ve:
        logger.warning(f"Giriş hatası (ValueError): Kullanıcı='{username}', Hata: {ve}")
        flash(str(ve), 'danger')
        return render_template('auth/login.html', title="Giriş Yap", username=username)
    except Exception as e:
        logger.error(f"Giriş sırasında beklenmedik hata: Kullanıcı='{username}', Hata: {e}", exc_info=True)
        flash('Giriş sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.', 'danger')
        return render_template('auth/login.html', title="Giriş Yap", username=username)


# =============================================================================
# 3.0 ROTA BAŞLATMA (ROUTE INITIALIZATION)
# =============================================================================

def init_auth_routes(app: Flask) -> None:
    """
    Temel kimlik doğrulama (kayıt, giriş, çıkış) rotalarını
    belirtilen Flask uygulamasına kaydeder.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    
    # =========================================================================
    # 4.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 4.1. Kayıt (Register)
    # -------------------------------------------------------------------------

    @app.route('/register', methods=['GET', 'POST'])
    def register() -> Any:
        """
        Kullanıcı kayıt sayfasını yönetir.
        - GET: Kayıt formunu gösterir.
        - POST: Yeni bir kullanıcı kaydı oluşturur.
        Eğer kullanıcı zaten oturum açmışsa, profil sayfasına yönlendirilir.
        """
        if auth_service.session_is_user_logged_in():
            return redirect(url_for('main_bp.profile'))

        if request.method == 'POST':
            return _handle_register_post(request.form)
        
        # GET isteği
        return render_template('auth/register.html', title="Kayıt Ol")

    # -------------------------------------------------------------------------
    # 4.2. Giriş (Login)
    # -------------------------------------------------------------------------

    @app.route('/login', methods=['GET', 'POST'])
    def login() -> Any:
        """
        Kullanıcı giriş sayfasını yönetir.
        - GET: Giriş formunu gösterir.
        - POST: Kullanıcıyı doğrular ve oturum açar.
        Eğer kullanıcı zaten oturum açmışsa, profil sayfasına yönlendirilir.
        """
        if auth_service.session_is_user_logged_in():
            return redirect(url_for('main_bp.profile'))

        if request.method == 'POST':
            return _handle_login_post(request.form)

        # GET isteği
        return render_template('auth/login.html', title="Giriş Yap")

    # -------------------------------------------------------------------------
    # 4.3. Çıkış (Logout)
    # -------------------------------------------------------------------------

    @app.route('/logout', methods=['GET'])
    def logout() -> Any:
        """
        Kullanıcının mevcut oturumunu sonlandırır (çıkış yapar).
        Oturumdaki kullanıcı bilgilerini temizler ve ana sayfaya yönlendirir.
        """
        username: Optional[str] = auth_service.session_is_user_logged_in()

        if not username:
            return redirect(url_for('main_bp.homepage'))

        try:
            logger.info(f"Kullanıcı çıkış yapıyor: Kullanıcı='{username}'")
            auth_service.beatify_log_out(username)
            flash('Başarıyla çıkış yaptınız.', 'success')
            logger.info(f"Kullanıcı '{username}' başarıyla çıkış yaptı.")
        except Exception as e:
            logger.error(f"Çıkış sırasında hata oluştu, oturum zorla temizleniyor. Hata: {e}", exc_info=True)
            session.clear()
            flash('Başarıyla çıkış yaptınız (hata oluştu, oturum temizlendi).', 'info')
        
        return redirect(url_for('main_bp.homepage'))

    # -------------------------------------------------------------------------
    # 4.4. Parola Sıfırlama (Password Reset)
    # -------------------------------------------------------------------------

    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password() -> Any:
        """
        Parola sıfırlama sayfasını yönetir.
        - GET: Parola sıfırlama formunu gösterir.
        - POST: Sıfırlama talebini işler (şu an için sadece bilgilendirme).
        """
        if request.method == 'POST':
            email: Optional[str] = request.form.get('email')
            if email:
                logger.info(f"Parola sıfırlama talebi alındı: Email='{email}'")
                flash(f"Eğer '{email}' adresi sistemimizde kayıtlıysa, parola sıfırlama talimatları gönderilecektir.", "info")
                return redirect(url_for('auth_bp.login'))
            else:
                flash("Lütfen e-posta adresinizi girin.", "danger")
        
        return render_template('auth/reset_password.html', title="Parola Sıfırla")

# =============================================================================
# Kimlik Doğrulama Rota Modülü Sonu
# =============================================================================
