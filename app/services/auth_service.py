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
#      : Gerekli Flask bileşenleri, veritabanı depoları, yapılandırmalar ve
#        Python modüllerinin içe aktarılması.
# 2.0  KULLANICI YÖNETİMİ FONKSİYONLARI (USER MANAGEMENT FUNCTIONS)
#      2.1. beatify_register(username, email, password)
#           : Yeni bir kullanıcı kaydı oluşturur.
#      2.2. beatify_log_in(username, password, remember_me)
#           : Kullanıcıyı doğrular ve oturum açar, "beni hatırla" işlevini destekler.
#      2.3. beatify_log_out(username)
#           : Kullanıcının oturumunu sonlandırır ve token'ını geçersiz kılar.
#      2.4. beatify_check_user_password(username, password)
#           : Verilen parolanın kullanıcının kayıtlı parolasıyla eşleşip eşleşmediğini kontrol eder.
#
# 3.0  OTURUM YÖNETİMİ FONKSİYONLARI (SESSION MANAGEMENT FUNCTIONS)
#      3.1. session_log_in(username)
#           : Kullanıcı için Flask session'ını başlatır.
#      3.2. session_is_user_logged_in()
#           : Mevcut session'da bir kullanıcının oturum açıp açmadığını kontrol eder.
#      3.3. session_log_out(username)
#           : Kullanıcının oturumunu sonlandırır (beatify_log_out ile benzer,
#             ancak bu sadece session temizliğine odaklanabilir veya token
#             işlemini de içerebilir; mevcut implementasyonda token işlemini de içeriyor).
#
# 4.0  TOKEN YÖNETİMİ FONKSİYONLARI (TOKEN MANAGEMENT FUNCTIONS)
#      4.1. beatify_create_auth_token(username)
#           : "Beni hatırla" işlevi için kalıcı bir kimlik doğrulama token'ı oluşturur ve cookie olarak ayarlar.
#      4.2. beatify_validate_auth_token(token)
#           : Verilen kimlik doğrulama token'ının geçerliliğini kontrol eder.
#
# 5.0  GÜVENLİK FONKSİYONLARI VE DEKORATÖRLER (SECURITY FUNCTIONS AND DECORATORS)
#      5.1. redirect_to_https(request)
#           : Canlı (production) ortamda HTTP isteklerini HTTPS'e yönlendirir.
#      5.2. login_required(f)
#           : Belirli rotalara erişim için kullanıcı oturumunun veya geçerli token'ın
#             olmasını gerektiren bir dekoratör.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging # Loglama için
from functools import wraps # Dekoratorler için
from datetime import datetime, timedelta # Zaman ve süre işlemleri için
from secrets import token_hex # Güvenli token üretimi için
from typing import Optional, Any # Tip ipuçları için

from flask import (
    session,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    Response, # Yanıt tipi için
    Request  # İstek tipi için
)
from werkzeug.security import check_password_hash, generate_password_hash # Parola hashleme ve kontrolü
from app.database.beatify_user_repository import BeatifyUserRepository # Kullanıcı veritabanı işlemleri
from app.config import DEBUG # Uygulama hata ayıklama modu (örn: HTTPS yönlendirmesi, cookie güvenliği için)

# Logger kurulumu (modül seviyesinde)
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 KULLANICI YÖNETİMİ FONKSİYONLARI (USER MANAGEMENT FUNCTIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1. beatify_register(username, email, password) : Yeni kullanıcı kaydı.
# -----------------------------------------------------------------------------
def beatify_register(username: str, email: str, password: str) -> None:
    """
    Yeni bir kullanıcıyı sisteme kaydeder.
    Kullanıcı adı veya e-posta zaten mevcutsa hata mesajı gösterir.
    Başarılı kayıt sonrası kullanıcıyı bilgilendirir.

    Args:
        username (str): Kaydedilecek kullanıcının adı.
        email (str): Kaydedilecek kullanıcının e-posta adresi.
        password (str): Kaydedilecek kullanıcının parolası (hash'lenecek).

    Raises:
        ValueError: Eğer kullanıcı adı veya e-posta zaten kullanımdaysa.
                    (Orijinal kod flash mesajı kullanıyor ve None dönüyor,
                     bu yapı korunabilir veya istisna fırlatılabilir.)
    """
    # print(f"AuthService: beatify_register çağrıldı - KullanıcıAdı='{username}', Email='{email}'") # Geliştirme için log
    user_repo = BeatifyUserRepository()
    existing_user_details: Optional[tuple] = user_repo.beatify_get_username_or_email_data(username, email)

    if existing_user_details:
        # Orijinal kodda flash mesajları kullanılıyor. Servis katmanında flash mesajı
        # göstermek yerine, bir istisna fırlatmak veya özel bir sonuç nesnesi döndürmek
        # daha yaygın bir yaklaşımdır. Rota katmanı bu sonucu/istisnayı yakalayıp
        # kullanıcıya uygun mesajı gösterebilir. Şimdilik orijinal yapı korunuyor.
        # Ancak, daha test edilebilir ve modüler olması için istisna fırlatmak önerilir.
        # Örneğin: raise ValueError("Bu kullanıcı adı zaten kullanılıyor.")
        existing_username = existing_user_details[0] # type: ignore
        existing_email = existing_user_details[1] # type: ignore

        if existing_username == username and existing_email == email:
            logger.warning(f"Kayıt denemesi başarısız: Kullanıcı adı '{username}' ve e-posta '{email}' zaten kullanımda.")
            raise ValueError('Bu kullanıcı adı ve e-posta zaten kullanılıyor.')
        elif existing_username == username:
            logger.warning(f"Kayıt denemesi başarısız: Kullanıcı adı '{username}' zaten kullanımda.")
            raise ValueError('Bu kullanıcı adı zaten kullanılıyor.')
        elif existing_email == email:
            logger.warning(f"Kayıt denemesi başarısız: E-posta '{email}' zaten kullanımda.")
            raise ValueError('Bu e-posta adresi zaten kullanılıyor.')
        # Bu return None yapısı, rota katmanında None kontrolü gerektirir.
        # return None # Orijinal kodda bu vardı, ValueError fırlatmak daha iyi.

    # Parolayı hash'le ve yeni kullanıcıyı veritabanına ekle
    hashed_password = generate_password_hash(password)
    user_repo.beatify_insert_new_user_data(username, email, hashed_password)
    logger.info(f"Yeni kullanıcı '{username}' başarıyla kaydedildi.")
    # flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success') # Flash mesajı rota katmanında olmalı.
    return # Başarılı durumda None (veya True) dönebilir.

# -----------------------------------------------------------------------------
# 2.2. beatify_log_in(username, password, remember_me) : Kullanıcı girişi.
# -----------------------------------------------------------------------------
def beatify_log_in(username: str, password: str, remember_me: bool) -> Optional[Response]:
    """
    Kullanıcıyı verilen kullanıcı adı ve parola ile doğrular ve oturum açar.
    "Beni Hatırla" seçeneği aktifse, kalıcı bir kimlik doğrulama token'ı oluşturur
    ve cookie olarak ayarlar.

    Args:
        username (str): Giriş yapmaya çalışan kullanıcının adı.
        password (str): Kullanıcının girdiği parola.
        remember_me (bool): "Beni Hatırla" seçeneğinin işaretli olup olmadığı.

    Returns:
        Optional[Response]: "Beni Hatırla" aktifse ve token oluşturulduysa,
                            cookie içeren bir Flask Response nesnesi.
                            Giriş başarılı ama "Beni Hatırla" aktif değilse None.
                            Giriş başarısızsa ValueError fırlatır.
    Raises:
        ValueError: Kullanıcı adı veya parola geçersizse.
    """
    # print(f"AuthService: beatify_log_in çağrıldı - KullanıcıAdı='{username}', BeniHatırla={remember_me}") # Geliştirme için log
    user_repo = BeatifyUserRepository()
    # Veritabanından kullanıcının hash'lenmiş parolasını al
    database_password_hash: Optional[str] = user_repo.beatify_get_password_hash_data(username)

    if not database_password_hash:
        logger.warning(f"Giriş denemesi başarısız: Kullanıcı adı '{username}' bulunamadı.")
        raise ValueError('Geçersiz kullanıcı adı veya parola.')

    # Parolaları karşılaştır
    if beatify_check_user_password(username, password): # Bu zaten database_password_hash'i tekrar alıyor, optimize edilebilir.
    # Alternatif: if check_password_hash(database_password_hash, password):
        session_log_in(username) # Flask session'ını başlat
        logger.info(f"Kullanıcı '{username}' başarıyla giriş yaptı.")
        if remember_me:
            logger.info(f"Kullanıcı '{username}' için 'Beni Hatırla' token'ı oluşturuluyor.")
            return beatify_create_auth_token(username) # Token oluştur ve cookie ile Response döndür
        return None # "Beni Hatırla" yoksa sadece session yeterli
    else:
        logger.warning(f"Giriş denemesi başarısız: Kullanıcı adı '{username}' için geçersiz parola.")
        raise ValueError('Geçersiz kullanıcı adı veya parola.')

# -----------------------------------------------------------------------------
# 2.3. beatify_log_out(username) : Kullanıcı çıkışı.
# -----------------------------------------------------------------------------
def beatify_log_out(username: str) -> None:
    """
    Kullanıcının oturumunu sonlandırır. Eğer "Beni Hatırla" token'ı varsa
    veritabanında bu token'ı geçersiz kılar ve cookie'yi silmek için
    bir Response nesnesi döndürmez (bu rota katmanında yapılmalı).
    Flask session'ını temizler.

    Args:
        username (str): Oturumu sonlandırılacak kullanıcının adı.
                        (Token deaktivasyonu için gerekli).
    """
    # print(f"AuthService: beatify_log_out çağrıldı - KullanıcıAdı='{username}'") # Geliştirme için log
    auth_token_cookie: Optional[str] = request.cookies.get('auth_token')
    if auth_token_cookie:
        user_repo = BeatifyUserRepository()
        try:
            # Token'ı veritabanında geçersiz kıl
            user_repo.beatify_deactivate_auth_token(username, auth_token_cookie)
            logger.info(f"Kullanıcı '{username}' için auth_token ({auth_token_cookie[:10]}...) devre dışı bırakıldı.")
        except Exception as e:
            logger.error(f"Kullanıcı '{username}' için auth_token devre dışı bırakılırken hata: {str(e)}", exc_info=True)
            # Hata olsa bile session temizlenmeli.
    
    session.clear() # Flask session'ını temizle
    logger.info(f"Kullanıcı '{username}' için session temizlendi, çıkış yapıldı.")
    # Cookie silme işlemi rota katmanında, response nesnesi üzerinden yapılmalı.
    # Örn: response = make_response(redirect(url_for('homepage')))
    #      response.delete_cookie('auth_token')

# -----------------------------------------------------------------------------
# 2.4. beatify_check_user_password(username, password) : Parola doğrulaması.
# -----------------------------------------------------------------------------
def beatify_check_user_password(username: str, password_to_check: str) -> bool:
    """
    Verilen düz metin parolanın, veritabanında saklanan hash'lenmiş parola
    ile eşleşip eşleşmediğini kontrol eder.

    Args:
        username (str): Parolası kontrol edilecek kullanıcının adı.
        password_to_check (str): Kontrol edilecek düz metin parola.

    Returns:
        bool: Parolalar eşleşiyorsa True, aksi halde False.
    """
    # print(f"AuthService: beatify_check_user_password çağrıldı - KullanıcıAdı='{username}'") # Geliştirme için log
    user_repo = BeatifyUserRepository()
    stored_password_hash: Optional[str] = user_repo.beatify_get_password_hash_data(username)

    if not stored_password_hash:
        logger.debug(f"Parola kontrolü: Kullanıcı '{username}' için hash bulunamadı.")
        return False # Kullanıcı bulunamadı veya hash yok

    is_match: bool = check_password_hash(stored_password_hash, password_to_check)
    # if is_match:
        # print(f"Parola kontrolü başarılı: {username}") # Geliştirme için log
    # else:
        # print(f"Parola kontrolü başarısız: {username}") # Geliştirme için log
    return is_match

# =============================================================================
# 3.0 OTURUM YÖNETİMİ FONKSİYONLARI (SESSION MANAGEMENT FUNCTIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# 3.1. session_log_in(username) : Flask session'ını başlatır.
# -----------------------------------------------------------------------------
def session_log_in(username: str) -> None:
    """
    Belirtilen kullanıcı için Flask session'ını başlatır.
    `logged_in`, `username` ve `user_id` (eğer bulunursa) anahtarlarını session'a ekler.

    Args:
        username (str): Oturumu başlatılacak kullanıcının adı.
    """
    # print(f"AuthService: session_log_in çağrıldı - KullanıcıAdı='{username}'") # Geliştirme için log
    session['logged_in'] = True
    session['username'] = username

    # Kullanıcı ID'sini de session'a ekleyebiliriz, bazı işlemler için faydalı olabilir.
    user_repo = BeatifyUserRepository()
    user_data: Optional[Dict[str, Any]] = user_repo.beatify_get_user_data(username)
    if user_data and 'id' in user_data:
        session['user_id'] = user_data['id']
        logger.info(f"Kullanıcı '{username}' (ID: {user_data['id']}) için session başlatıldı.")
    else:
        logger.warning(f"Kullanıcı '{username}' için session başlatıldı ancak veritabanından ID alınamadı.")


# -----------------------------------------------------------------------------
# 3.2. session_is_user_logged_in() : Kullanıcının oturum durumunu kontrol eder.
# -----------------------------------------------------------------------------
def session_is_user_logged_in() -> Optional[str]:
    """
    Mevcut Flask session'ında bir kullanıcının oturum açıp açmadığını kontrol eder.

    Returns:
        Optional[str]: Eğer kullanıcı oturum açmışsa kullanıcı adını döndürür,
                       aksi halde None döndürür.
    """
    # print("AuthService: session_is_user_logged_in çağrıldı.") # Geliştirme için log
    if session.get('logged_in') and session.get('username'):
        # print(f"Session kontrolü: Kullanıcı '{session.get('username')}' giriş yapmış.") # Geliştirme için log
        return session.get('username')
    # print("Session kontrolü: Giriş yapmış kullanıcı yok.") # Geliştirme için log
    return None

# -----------------------------------------------------------------------------
# 3.3. session_log_out(username) : Oturumu sonlandırır (beatify_log_out ile aynı).
# -----------------------------------------------------------------------------
# Bu fonksiyon, orijinal `auth_service.py` dosyasında `beatify_log_out` ile
# neredeyse aynı işi yapıyordu. Genellikle tek bir çıkış fonksiyonu yeterlidir.
# Eğer farklı bir amaç güdülüyorsa (örn: sadece session temizleme), ona göre düzenlenmeli.
# Şimdilik `beatify_log_out`'un bir kopyası gibi duruyor.
# Eğer sadece session temizleme amaçlıysa, token deaktivasyon kısmı çıkarılmalı.
# Mevcut haliyle, `beatify_log_out` çağrılması daha doğru olur.
# Bu fonksiyonu yorum satırına alıyorum veya `beatify_log_out`'a yönlendirme yapıyorum.
# def session_log_out(username: str) -> None:
#     """
#     Kullanıcının Flask session'ını ve varsa kimlik doğrulama token'ını temizler.
#     NOT: Bu fonksiyon `beatify_log_out` ile çok benzer. Tek bir çıkış fonksiyonu
#     kullanmak daha iyi olabilir.
#     """
#     print(f"AuthService: session_log_out çağrıldı - KullanıcıAdı='{username}'") # Geliştirme için log
#     beatify_log_out(username) # beatify_log_out'u çağırarak tekrarı önle

# =============================================================================
# 4.0 TOKEN YÖNETİMİ FONKSİYONLARI (TOKEN MANAGEMENT FUNCTIONS)
# =============================================================================
# Bu token'lar genellikle "Beni Hatırla" işlevi için kullanılır.

# -----------------------------------------------------------------------------
# 4.1. beatify_create_auth_token(username) : "Beni Hatırla" token'ı oluşturur.
# -----------------------------------------------------------------------------
def beatify_create_auth_token(username: str) -> Response:
    """
    "Beni Hatırla" işlevi için kalıcı bir kimlik doğrulama token'ı oluşturur,
    veritabanına kaydeder ve kullanıcıya HTTP cookie olarak gönderir.

    Args:
        username (str): Token'ın oluşturulacağı kullanıcı adı.

    Returns:
        Response: Token'ı cookie olarak içeren bir Flask Response nesnesi
                  (genellikle bir redirect response'u sarmalar).
    """
    # print(f"AuthService: beatify_create_auth_token çağrıldı - KullanıcıAdı='{username}'") # Geliştirme için log
    token: str = token_hex(32) # Güvenli, rastgele bir token oluştur (32 byte = 64 hex karakter)
    # Token geçerlilik süresi (örn: 30 gün)
    expires_at: datetime = datetime.now() + timedelta(days=30)

    user_repo = BeatifyUserRepository()
    try:
        user_repo.beatify_insert_or_update_auth_token(username, token, expires_at)
        logger.info(f"Kullanıcı '{username}' için yeni auth_token ({token[:10]}...) oluşturuldu ve DB'ye kaydedildi.")
    except Exception as e:
        logger.error(f"Auth token DB'ye kaydedilirken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
        # Hata durumunda token'ı cookie olarak göndermemek daha iyi olabilir.
        # Veya kullanıcıyı bilgilendirip normal bir redirect yapılabilir.
        # Şimdilik, hata olsa bile redirect yapılıyor (orijinal davranış).
        flash("Beni hatırla özelliği ayarlanırken bir sorun oluştu.", "warning")
        return make_response(redirect(url_for('user_bp.profile_page'))) # Hata durumunda da yönlendir


    # Cookie'yi içeren bir response oluştur ve döndür.
    # Genellikle bu, bir redirect response'u üzerine kurulur.
    # Rota katmanında `make_response(redirect(...))` yapılıp sonra cookie set edilebilir.
    # Bu servis fonksiyonunun doğrudan Response döndürmesi, katman ayrımını biraz esnetir.
    # Orijinal kodda `url_for('profile')` vardı, blueprint'e göre güncellenmeli.
    response: Response = make_response(redirect(url_for('user_bp.profile_page'))) # Uygun profil sayfası
    
    response.set_cookie(
        key='auth_token',
        value=token,
        expires=expires_at,
        httponly=True,  # JavaScript tarafından erişilemez
        secure=not DEBUG, # Sadece HTTPS üzerinden gönderilir (canlıda)
        samesite='Lax'  # CSRF koruması için 'Lax' veya 'Strict'
    )
    logger.info(f"Auth_token cookie'si kullanıcı '{username}' için ayarlandı.")
    return response

# -----------------------------------------------------------------------------
# 4.2. beatify_validate_auth_token(token) : "Beni Hatırla" token'ını doğrular.
# -----------------------------------------------------------------------------
def beatify_validate_auth_token(token: str) -> Optional[str]:
    """
    Verilen "Beni Hatırla" kimlik doğrulama token'ının geçerliliğini
    veritabanı üzerinden kontrol eder.

    Args:
        token (str): Doğrulanacak token.

    Returns:
        Optional[str]: Token geçerliyse ilişkili kullanıcı adını döndürür,
                       aksi halde None döndürür.
    """
    # print(f"AuthService: beatify_validate_auth_token çağrıldı - Token='{token[:10]}...'") # Geliştirme için log
    if not token:
        return None

    user_repo = BeatifyUserRepository()
    username: Optional[str] = user_repo.beatify_validate_auth_token(token)
    # if username:
        # print(f"Auth_token geçerli. Kullanıcı: {username}") # Geliştirme için log
    # else:
        # print("Auth_token geçersiz veya süresi dolmuş.") # Geliştirme için log
    return username

# =============================================================================
# 5.0 GÜVENLİK FONKSİYONLARI VE DEKORATÖRLER (SECURITY FUNCTIONS AND DECORATORS)
# =============================================================================

# -----------------------------------------------------------------------------
# 5.1. redirect_to_https(request) : HTTP'yi HTTPS'e yönlendirir.
# -----------------------------------------------------------------------------
def redirect_to_https(current_request: Request) -> Optional[Response]:
    """
    Eğer uygulama canlı (production) moddaysa (DEBUG=False) ve gelen istek
    güvenli değilse (HTTP), isteği HTTPS'e yönlendirir.
    Proxy arkasında çalışıyorsa 'X-Forwarded-Proto' başlığını da dikkate alır.

    Args:
        current_request (Request): Mevcut Flask request nesnesi.

    Returns:
        Optional[Response]: Eğer yönlendirme gerekliyse bir Redirect Response nesnesi,
                            aksi halde None.
    """
    # print("AuthService: redirect_to_https çağrıldı.") # Geliştirme için log
    if DEBUG: # Geliştirme ortamında HTTPS yönlendirmesi yapma
        # print("DEBUG modu aktif, HTTPS yönlendirmesi yapılmayacak.") # Geliştirme için log
        return None
    if current_request.is_secure: # Zaten HTTPS ise bir şey yapma
        # print("İstek zaten HTTPS.") # Geliştirme için log
        return None
    # Ters proxy (örn: Nginx, ELB) arkasında çalışıyorsa, bu başlık SSL sonlandırmasını gösterir.
    if current_request.headers.get('X-Forwarded-Proto') == 'https':
        # print("X-Forwarded-Proto HTTPS, yönlendirme yapılmayacak.") # Geliştirme için log
        return None

    # HTTP'den HTTPS'e yönlendir
    https_url: str = current_request.url.replace('http://', 'https://', 1)
    logger.info(f"Güvenli olmayan istek ({current_request.url}) HTTPS'e yönlendiriliyor: {https_url}")
    return redirect(https_url, code=301) # 301 Kalıcı Yönlendirme

# -----------------------------------------------------------------------------
# 5.2. login_required(f) : Giriş gerektiren rotalar için dekoratör.
# -----------------------------------------------------------------------------
def login_required(f: Any) -> Any:
    """
    Bir Flask rota fonksiyonunu sarmalayarak, o rotaya erişim için kullanıcının
    oturum açmış olmasını veya geçerli bir "Beni Hatırla" token'ına sahip
    olmasını gerektiren bir dekoratör.
    Eğer kullanıcı doğrulanmazsa, giriş sayfasına yönlendirilir.

    Args:
        f (Any): Sarmalanacak rota fonksiyonu.

    Returns:
        Any: Sarmalanmış ve kimlik doğrulama kontrolü eklenmiş fonksiyon.
    """
    @wraps(f) # Orijinal fonksiyonun metadata'sını korur (isim, docstring vb.)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # print(f"AuthService: login_required dekoratörü çalıştı - Rota: {f.__name__}") # Geliştirme için log
        # Önce Flask session'ını kontrol et
        current_username: Optional[str] = session_is_user_logged_in()
        if current_username:
            # print(f"Kullanıcı '{current_username}' session ile doğrulanmış.") # Geliştirme için log
            return f(*args, **kwargs) # Kullanıcı zaten giriş yapmış

        # Session yoksa, "Beni Hatırla" cookie'sini kontrol et
        auth_token_cookie: Optional[str] = request.cookies.get('auth_token')
        if auth_token_cookie:
            # print(f"Auth_token cookie'si bulundu: {auth_token_cookie[:10]}...") # Geliştirme için log
            validated_username: Optional[str] = beatify_validate_auth_token(auth_token_cookie)
            if validated_username:
                # Token geçerliyse, session'ı yeniden başlat ve devam et
                session_log_in(validated_username)
                logger.info(f"Kullanıcı '{validated_username}' auth_token ile doğrulandı ve session başlatıldı.")
                return f(*args, **kwargs)
            else:
                # Geçersiz veya süresi dolmuş token, cookie'yi silmek iyi bir pratik olabilir.
                # Ancak bu, response nesnesi gerektirir ve dekoratör içinde karmaşıklaşabilir.
                # Rota katmanında veya bir middleware'de yapılabilir.
                logger.warning(f"Geçersiz auth_token cookie'si bulundu: {auth_token_cookie[:10]}...")
                pass # Giriş sayfasına yönlendirmeye devam et

        # Kullanıcı doğrulanmazsa giriş sayfasına yönlendir
        flash('Bu sayfayı görüntülemek için giriş yapmanız gerekmektedir.', 'warning')
        logger.info(f"Giriş gerektiren sayfa ({f.__name__}) için kullanıcı giriş sayfasına yönlendiriliyor.")
        return redirect(url_for('auth_bp.login_page')) # Uygun giriş sayfası endpoint'i
    return decorated_function

# =============================================================================
# Kimlik Doğrulama Servis Modülü Sonu
# =============================================================================
