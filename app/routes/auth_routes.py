# =============================================================================
# Kimlik Doğrulama Rotaları Modülü (Authentication Routes Module)
# =============================================================================
# Bu modül, kullanıcı kaydı, giriş, çıkış ve parola sıfırlama (gelecekte)
# gibi temel kimlik doğrulama işlemlerini yöneten Flask rotalarını tanımlar.
# Kullanıcıların uygulama ile etkileşimde bulunabilmesi için gerekli
# temel güvenlik ve oturum yönetimi işlevlerini sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenleri ve uygulama servislerinin içe aktarılması.
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
#     2.1. init_auth_routes(app)
#          : Tüm kimlik doğrulama rotalarını belirtilen Flask uygulamasına kaydeder.
#          Servis örneklerini (bu durumda doğrudan auth_service modülü) kullanır
#          ve rota fonksiyonlarını tanımlar.
#
#     İÇ ROTALAR (init_auth_routes içinde tanımlanır):
#     -------------------------------------------------------------------------
#     3.0 KİMLİK DOĞRULAMA ROTALARI (AUTHENTICATION ROUTES)
#         3.1. register()
#              : Kullanıcı kayıt sayfasını gösterir ve kayıt işlemini gerçekleştirir.
#                Rota: /register (GET, POST)
#         3.2. login()
#              : Kullanıcı giriş sayfasını gösterir ve giriş işlemini gerçekleştirir.
#                Rota: /login (GET, POST)
#         3.3. logout()
#              : Kullanıcının oturumunu sonlandırır ve çıkış işlemini gerçekleştirir.
#                Rota: /logout (GET)
#         3.4. reset_password()
#              : Parola sıfırlama sayfasını gösterir (gelecekteki implementasyon).
#                Rota: /reset_password (GET, POST)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    Flask,  # Flask tipi için
    Response # Yanıt tipi için
)
from app.services import auth_service # Kimlik doğrulama iş mantığını içerir
from typing import Any, Optional # Tip ipuçları için

# =============================================================================
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_auth_routes(app) : Tüm kimlik doğrulama rotalarını kaydeder.
# -----------------------------------------------------------------------------
def init_auth_routes(app: Flask) -> None:
    """
    Temel kimlik doğrulama (kayıt, giriş, çıkış) rotalarını
    belirtilen Flask uygulamasına kaydeder.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    # print("Kimlik doğrulama rotaları başlatılıyor...") # Geliştirme için log

    # =========================================================================
    # 3.0 KİMLİK DOĞRULAMA ROTALARI (AUTHENTICATION ROUTES)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 3.1. register() : Kullanıcı kayıt sayfasını gösterir ve işlemi yapar.
    #      Rota: /register (GET, POST)
    # -------------------------------------------------------------------------
    @app.route('/register', methods=['GET', 'POST'])
    def register() -> Any: # render_template veya redirect Response döndürür
        """
        Kullanıcı kayıt sayfasını görüntüler (GET) veya yeni bir kullanıcı
        kaydı oluşturur (POST).
        Eğer kullanıcı zaten oturum açmışsa, profil sayfasına yönlendirilir.
        Form verileri doğrulanır ve `auth_service` kullanılarak kayıt işlemi yapılır.
        """
        # print("API çağrısı: /register") # Geliştirme için log
        if auth_service.session_is_user_logged_in():
            # print("Kullanıcı zaten giriş yapmış, profil sayfasına yönlendiriliyor.") # Geliştirme için log
            return redirect(url_for('user_bp.profile_page')) # Uygun profil sayfası endpoint'i

        if request.method == 'POST':
            username: Optional[str] = request.form.get('username')
            email: Optional[str] = request.form.get('email')
            password: Optional[str] = request.form.get('password')
            # print(f"Kayıt isteği (POST): KullanıcıAdı='{username}', Email='{email}'") # Geliştirme için log

            # Temel form doğrulama
            if not all([username, email, password]):
                flash('Lütfen tüm alanları doldurun.', 'danger')
                # print("Kayıt hatası: Tüm alanlar doldurulmadı.") # Geliştirme için log
                return render_template('auth/register.html', title="Kayıt Ol")

            # Parola uzunluk kontrolü (auth_service içinde daha detaylı kontrol olabilir)
            if len(password) < 8:
                flash('Parola en az 8 karakter uzunluğunda olmalıdır.', 'danger')
                # print("Kayıt hatası: Parola çok kısa.") # Geliştirme için log
                return render_template('auth/register.html', title="Kayıt Ol")

            try:
                auth_service.beatify_register(username, email, password)
                flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
                # print(f"Kullanıcı '{username}' başarıyla kaydedildi.") # Geliştirme için log
                return redirect(url_for('login')) # login_page veya uygun giriş sayfası
            except ValueError as ve: # Servis tarafından fırlatılan beklenen hatalar (örn: kullanıcı adı mevcut)
                flash(str(ve), 'danger')
                # print(f"Kayıt sırasında beklenen hata ({username}): {str(ve)}") # Geliştirme için log
                return render_template('register.html', title="Kayıt Ol", username=username, email=email)
            except Exception as e: # Beklenmedik diğer hatalar
                flash(f'Kayıt sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.', 'danger')
                # print(f"Kayıt sırasında beklenmedik hata ({username}): {str(e)}") # Geliştirme için log
                # import traceback
                # print(traceback.format_exc()) # Detaylı hata için
                return render_template('register.html', title="Kayıt Ol", username=username, email=email)

        # GET isteği - kayıt formunu göster
        return render_template('register.html', title="Kayıt Ol")

    # -------------------------------------------------------------------------
    # 3.2. login() : Kullanıcı giriş sayfasını gösterir ve işlemi yapar.
    #      Rota: /login (GET, POST)
    # -------------------------------------------------------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login() -> Any: # render_template, redirect veya Response döndürür
        """
        Kullanıcı giriş sayfasını görüntüler (GET) veya kullanıcıyı doğrular
        ve oturum açar (POST).
        Eğer kullanıcı zaten oturum açmışsa, profil sayfasına yönlendirilir.
        'Beni Hatırla' seçeneği desteklenir.
        """
        # print("API çağrısı: /login") # Geliştirme için log
        if auth_service.session_is_user_logged_in():
            # print("Kullanıcı zaten giriş yapmış, profil sayfasına yönlendiriliyor.") # Geliştirme için log
            return redirect(url_for('profile')) # Uygun profil sayfası

        if request.method == 'POST':
            username: Optional[str] = request.form.get('username')
            password: Optional[str] = request.form.get('password')
            remember_me: bool = request.form.get('remember') == 'on'
            # print(f"Giriş isteği (POST): KullanıcıAdı='{username}', BeniHatırla={remember_me}") # Geliştirme için log

            if not all([username, password]):
                flash('Lütfen kullanıcı adı ve parola girin.', 'danger')
                # print("Giriş hatası: Kullanıcı adı veya parola eksik.") # Geliştirme için log
                return render_template('login.html', title="Giriş Yap")

            try:
                # auth_service.beatify_log_in, başarılı olursa None veya Response (beni hatırla çerezi için) döndürür.
                response: Optional[Response] = auth_service.beatify_log_in(username, password, remember_me)
                flash('Başarıyla giriş yaptınız.', 'success')
                # print(f"Kullanıcı '{username}' başarıyla giriş yaptı.") # Geliştirme için log

                # Eğer auth_service bir Response nesnesi döndürdüyse (örn: set-cookie için),
                # bu Response nesnesini döndürerek tarayıcıya gönder.
                if response:
                    # print("Giriş sonrası özel yanıt (örn: çerez) döndürülüyor.") # Geliştirme için log
                    return response
                
                # Varsayılan yönlendirme (ana sayfa veya profil)
                # print("Giriş sonrası ana sayfaya yönlendiriliyor.") # Geliştirme için log
                return redirect(url_for('general_bp.homepage')) # general_bp.homepage veya uygun ana sayfa

            except ValueError as ve: # Servis tarafından fırlatılan beklenen hatalar (örn: yanlış parola)
                flash(str(ve), 'danger')
                # print(f"Giriş sırasında beklenen hata ({username}): {str(ve)}") # Geliştirme için log
                return render_template('auth/login.html', title="Giriş Yap", username=username)
            except Exception as e: # Beklenmedik diğer hatalar
                flash(f'Giriş sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.', 'danger')
                # print(f"Giriş sırasında beklenmedik hata ({username}): {str(e)}") # Geliştirme için log
                return render_template('auth/login.html', title="Giriş Yap", username=username)

        # GET isteği - giriş formunu göster
        return render_template('auth/login.html', title="Giriş Yap")

    # -------------------------------------------------------------------------
    # 3.3. logout() : Kullanıcının oturumunu sonlandırır.
    #      Rota: /logout (GET)
    # -------------------------------------------------------------------------
    @app.route('/logout', methods=['GET']) # Genellikle POST olmalı ama basitlik için GET bırakılmış olabilir.
    def logout() -> Any: # redirect Response döndürür
        """
        Kullanıcının mevcut oturumunu sonlandırır (çıkış yapar).
        Oturumdaki kullanıcı bilgilerini ve ilgili tokenları temizler.
        Kullanıcıyı ana sayfaya yönlendirir.
        """
        # print("API çağrısı: /logout") # Geliştirme için log
        username: Optional[str] = auth_service.session_is_user_logged_in()

        if not username:
            # print("Çıkış isteği: Kullanıcı zaten giriş yapmamış.") # Geliştirme için log
            # Zaten çıkış yapmışsa veya oturum yoksa ana sayfaya yönlendir
            return redirect(url_for('general_bp.homepage'))

        try:
            # print(f"Kullanıcı '{username}' çıkış yapıyor...") # Geliştirme için log
            auth_service.beatify_log_out(username) # Bu metot session.clear() ve db'deki token'ı deaktive etmeli.
            flash('Başarıyla çıkış yaptınız.', 'success')
            # print(f"Kullanıcı '{username}' başarıyla çıkış yaptı.") # Geliştirme için log
        except Exception as e:
            # print(f"Çıkış sırasında hata ({username}): {str(e)}. Session yine de temizleniyor.") # Geliştirme için log
            # Serviste bir hata olsa bile session'ı temizlemeye çalış
            session.clear()
            flash('Başarıyla çıkış yaptınız (hata oluştu, oturum temizlendi).', 'info')
        
        return redirect(url_for('general_bp.homepage'))

    # -------------------------------------------------------------------------
    # 3.4. reset_password() : Parola sıfırlama sayfasını gösterir (gelecekte).
    #      Rota: /reset_password (GET, POST)
    # -------------------------------------------------------------------------
    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password() -> str:
        """
        Parola sıfırlama işlemleri için bir endpoint (şu anda sadece bir şablon render eder).
        Gelecekte, e-posta ile token gönderme, token doğrulama ve yeni parola
        belirleme gibi işlevler eklenecektir.
        """
        # print("API çağrısı: /reset_password (gelecekteki implementasyon)") # Geliştirme için log
        # TODO: Parola sıfırlama mantığını implemente et.
        # 1. E-posta al (POST)
        # 2. E-postaya özel bir token gönder
        # 3. Token ile yeni bir sayfa aç (GET /reset_password/<token>)
        # 4. Yeni parolayı al ve güncelle (POST /reset_password/<token>)
        if request.method == 'POST':
            email: Optional[str] = request.form.get('email')
            if email:
                flash(f"Eğer '{email}' adresi sistemimizde kayıtlıysa, parola sıfırlama talimatları gönderilecektir.", "info")
                # print(f"Parola sıfırlama isteği alındı: Email='{email}'") # Geliştirme için log
                # auth_service.send_password_reset_email(email)
                return redirect(url_for('auth_bp.login_page'))
            else:
                flash("Lütfen e-posta adresinizi girin.", "danger")
        
        return render_template('auth/reset_password.html', title="Parola Sıfırla")

    # print("Kimlik doğrulama rotaları başarıyla yüklendi.") # Geliştirme için log
# =============================================================================
# Kimlik Doğrulama Rotaları Modülü Sonu
# =============================================================================
