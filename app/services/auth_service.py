# =============================================================================
# Kimlik Doğrulama Servis Modülü (Authentication Service Module)
# =============================================================================
# Bu modül, kullanıcı kimlik doğrulama, oturum yönetimi, token işlemleri
# ve güvenlikle ilgili temel servis fonksiyonlarını içerir. Kullanıcı kaydı,
# giriş, çıkış, parola doğrulama, oturum oluşturma/doğrulama/sonlandırma,
# kimlik doğrulama token'ı oluşturma/doğrulama ve güvenlik önlemleri
# (HTTPS yönlendirmesi, login_required dekoratörü) gibi işlevleri sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli modüllerin ve bileşenlerin içe aktarılması.
#
# 2.0  KULLANICI YÖNETİMİ (USER MANAGEMENT)
#      2.1. beatify_register(username, email, password)
#           : Yeni bir kullanıcı kaydı oluşturur.
#      2.2. beatify_log_in(username, password, remember_me)
#           : Kullanıcıyı doğrular ve oturum açar.
#      2.3. beatify_log_out(username)
#           : Kullanıcının oturumunu sonlandırır ve token'ını geçersiz kılar.
#      2.4. beatify_check_user_password(username, password_to_check)
#           : Verilen parolanın doğruluğunu kontrol eder.
#
# 3.0  OTURUM YÖNETİMİ (SESSION MANAGEMENT)
#      3.1. session_log_in(username)
#           : Kullanıcı için Flask oturumunu başlatır.
#      3.2. session_is_user_logged_in()
#           : Mevcut oturumda bir kullanıcının giriş yapıp yapmadığını kontrol eder.
#
# 4.0  TOKEN YÖNETİMİ (TOKEN MANAGEMENT)
#      4.1. beatify_create_auth_token(username)
#           : "Beni Hatırla" özelliği için kalıcı bir kimlik doğrulama token'ı oluşturur.
#      4.2. beatify_validate_auth_token(token)
#           : Verilen kimlik doğrulama token'ının geçerliliğini kontrol eder.
#
# 5.0  GÜVENLİK YARDIMCILARI (SECURITY HELPERS)
#      5.1. redirect_to_https(current_request)
#           : HTTP isteklerini güvenli HTTPS'e yönlendirir.
#      5.2. login_required(f)
#           : Rotalara erişim için giriş zorunluluğu getiren bir dekoratördür.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from functools import wraps
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Optional, Any

from flask import (
    session,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    Request,
    Response as FlaskResponse
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.database.beatify_user_repository import BeatifyUserRepository
from app.config import DEBUG

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 KULLANICI YÖNETİMİ (USER MANAGEMENT)
# =============================================================================

def beatify_register(username: str, email: str, password: str) -> None:
    """
    Yeni bir kullanıcıyı sisteme kaydeder.
    Kullanıcı adı veya e-posta zaten mevcutsa ValueError fırlatır.
    """
    user_repo = BeatifyUserRepository()
    existing_user_details = user_repo.beatify_get_username_or_email_data(username, email)

    if existing_user_details:
        existing_username, existing_email = existing_user_details
        if existing_username == username:
            logger.warning(f"Kayıt denemesi başarısız: Kullanıcı adı '{username}' zaten kullanımda.")
            raise ValueError('Bu kullanıcı adı zaten kullanılıyor.')
        if existing_email == email:
            logger.warning(f"Kayıt denemesi başarısız: E-posta '{email}' zaten kullanımda.")
            raise ValueError('Bu e-posta adresi zaten kullanılıyor.')

    hashed_password = generate_password_hash(password)
    user_repo.create_new_user(username, email, hashed_password)
    logger.info(f"Yeni kullanıcı '{username}' başarıyla kaydedildi.")


def beatify_log_in(username: str, password: str, remember_me: bool) -> Optional[FlaskResponse]:
    """
    Kullanıcıyı doğrular, oturum açar ve "Beni Hatırla" seçiliyse token oluşturur.
    Başarısız olursa ValueError fırlatır.
    """
    if beatify_check_user_password(username, password):
        session_log_in(username)
        logger.info(f"Kullanıcı '{username}' başarıyla giriş yaptı.")
        if remember_me:
            logger.info(f"Kullanıcı '{username}' için 'Beni Hatırla' token'ı oluşturuluyor.")
            return beatify_create_auth_token(username)
        return None
    else:
        logger.warning(f"Giriş denemesi başarısız: Kullanıcı adı '{username}' için geçersiz parola.")
        raise ValueError('Geçersiz kullanıcı adı veya parola.')


def beatify_log_out(username: str) -> None:
    """
    Kullanıcının oturumunu sonlandırır, token'ı geçersiz kılar ve session'ı temizler.
    """
    auth_token_cookie = request.cookies.get('auth_token')
    if auth_token_cookie:
        user_repo = BeatifyUserRepository()
        try:
            user_repo.beatify_deactivate_auth_token(username, auth_token_cookie)
            logger.info(f"Kullanıcı '{username}' için auth_token devre dışı bırakıldı.")
        except Exception as e:
            logger.error(f"Kullanıcı '{username}' için auth_token devre dışı bırakılırken hata: {e}", exc_info=True)
    
    session.clear()
    logger.info(f"Kullanıcı '{username}' için session temizlendi, çıkış yapıldı.")


def beatify_check_user_password(username: str, password_to_check: str) -> bool:
    """
    Verilen parolanın, veritabanındaki hash ile eşleşip eşleşmediğini kontrol eder.
    """
    user_repo = BeatifyUserRepository()
    stored_password_hash = user_repo.beatify_get_password_hash_data(username)
    if not stored_password_hash:
        logger.debug(f"Parola kontrolü: Kullanıcı '{username}' için hash bulunamadı.")
        return False
    return check_password_hash(stored_password_hash, password_to_check)


# =============================================================================
# 3.0 OTURUM YÖNETİMİ (SESSION MANAGEMENT)
# =============================================================================

def session_log_in(username: str) -> None:
    """
    Belirtilen kullanıcı için Flask session'ını başlatır.
    """
    session['logged_in'] = True
    session['username'] = username
    user_repo = BeatifyUserRepository()
    user_data = user_repo.beatify_get_user_data(username)
    if user_data and 'id' in user_data:
        session['user_id'] = user_data['id']
        logger.info(f"Kullanıcı '{username}' (ID: {user_data['id']}) için session başlatıldı.")
    else:
        logger.warning(f"Kullanıcı '{username}' için session başlatıldı ancak ID alınamadı.")


def session_is_user_logged_in() -> Optional[str]:
    """
    Mevcut Flask session'ında bir kullanıcının oturum açıp açmadığını kontrol eder.
    """
    if session.get('logged_in') and session.get('username'):
        return session.get('username')
    return None


# =============================================================================
# 4.0 TOKEN YÖNETİMİ (TOKEN MANAGEMENT)
# =============================================================================

def beatify_create_auth_token(username: str) -> FlaskResponse:
    """
    "Beni Hatırla" için kalıcı bir token oluşturur, DB'ye kaydeder ve cookie olarak ayarlar.
    """
    token = token_hex(32)
    expires_at = datetime.now() + timedelta(days=30)
    user_repo = BeatifyUserRepository()
    try:
        user_repo.beatify_insert_or_update_auth_token(username, token, expires_at)
        logger.info(f"Kullanıcı '{username}' için auth_token oluşturuldu ve DB'ye kaydedildi.")
    except Exception as e:
        logger.error(f"Auth token DB'ye kaydedilirken hata (Kullanıcı: {username}): {e}", exc_info=True)
        flash("Beni hatırla özelliği ayarlanırken bir sorun oluştu.", "warning")
        return make_response(redirect(url_for('user_bp.profile_page')))

    response = make_response(redirect(url_for('user_bp.profile_page')))
    response.set_cookie(
        key='auth_token',
        value=token,
        expires=expires_at,
        httponly=True,
        secure=not DEBUG,
        samesite='Lax'
    )
    logger.info(f"Auth_token cookie'si kullanıcı '{username}' için ayarlandı.")
    return response


def beatify_validate_auth_token(token: str) -> Optional[str]:
    """
    Verilen "Beni Hatırla" token'ının geçerliliğini DB üzerinden kontrol eder.
    """
    if not token:
        return None
    user_repo = BeatifyUserRepository()
    return user_repo.beatify_validate_auth_token(token)


# =============================================================================
# 5.0 GÜVENLİK YARDIMCILARI (SECURITY HELPERS)
# =============================================================================

def redirect_to_https(current_request: Request) -> Optional[FlaskResponse]:
    """
    Canlı ortamda (DEBUG=False) HTTP isteklerini HTTPS'e yönlendirir.
    """
    if DEBUG or current_request.is_secure or current_request.headers.get('X-Forwarded-Proto') == 'https':
        return None
    
    https_url = current_request.url.replace('http://', 'https://', 1)
    logger.info(f"Güvenli olmayan istek ({current_request.url}) HTTPS'e yönlendiriliyor: {https_url}")
    return redirect(https_url, code=301)


def login_required(f: Any) -> Any:
    """
    Bir rotaya erişim için kullanıcının giriş yapmış olmasını gerektiren dekoratör.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session_is_user_logged_in():
            return f(*args, **kwargs)

        auth_token_cookie = request.cookies.get('auth_token')
        if auth_token_cookie:
            validated_username = beatify_validate_auth_token(auth_token_cookie)
            if validated_username:
                session_log_in(validated_username)
                logger.info(f"Kullanıcı '{validated_username}' auth_token ile doğrulandı ve session başlatıldı.")
                return f(*args, **kwargs)
            else:
                logger.warning(f"Geçersiz auth_token cookie'si bulundu: {auth_token_cookie[:10]}...")
        
        flash('Bu sayfayı görüntülemek için giriş yapmanız gerekmektedir.', 'warning')
        logger.info(f"Giriş gerektiren sayfa ({f.__name__}) için kullanıcı giriş sayfasına yönlendiriliyor.")
        return redirect(url_for('login'))
    return decorated_function

# =============================================================================
# Kimlik Doğrulama Servis Modülü Sonu
# =============================================================================
