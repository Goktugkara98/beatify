# =============================================================================
# Spotify Kimlik Doğrulama Rotaları Modülü (Spotify Auth Routes Module)
# =============================================================================
# Bu modül, Spotify OAuth2 kimlik doğrulama akışını yöneten Flask rotalarını
# tanımlar. Kullanıcıların Spotify hesaplarını uygulamaya bağlamalarını,
# bağlantıyı kesmelerini ve bu süreçteki geri çağrıları (callback) yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenleri, servisler ve diğer modüllerin içe aktarılması.
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
#     2.1. init_spotify_auth_routes(app)
#          : Tüm Spotify kimlik doğrulama rotalarını belirtilen Flask uygulamasına kaydeder.
#          Servis örneklerini başlatır ve rota fonksiyonlarını tanımlar.
#
#     İÇ ROTALAR (init_spotify_auth_routes içinde tanımlanır):
#     -------------------------------------------------------------------------
#     3.0 KİMLİK DOĞRULAMA ROTALARI (AUTHENTICATION ROUTES)
#         3.1. spotify_auth()
#              : Spotify OAuth kimlik doğrulama akışını başlatır.
#                Kullanıcıyı Spotify'ın yetkilendirme sayfasına yönlendirir.
#                Rota: /spotify/auth (GET)
#         3.2. spotify_callback()
#              : Spotify tarafından OAuth akışı sonrası çağrılan geri çağrı (callback) endpoint'i.
#                Yetkilendirme kodunu alır, token ile değiştirir ve kullanıcı bilgilerini saklar.
#                Rota: /spotify/callback (GET)
#         3.3. spotify_unlink()
#              : Kullanıcının bağlı Spotify hesabının bağlantısını keser.
#                Rota: /spotify/unlink (GET)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import request, redirect, url_for, session, flash, Flask # Flask tipi eklendi
import requests # HTTP istekleri için
from datetime import datetime, timedelta # Zaman işlemleri için
from app.services.spotify_services.spotify_auth_service import SpotifyAuthService
from app.database.spotify_user_repository import SpotifyUserRepository # Veritabanı etkileşimi için
from app.services.auth_service import session_is_user_logged_in # Oturum kontrolü için
from typing import Tuple, Dict, Any, Optional # Tip ipuçları için

# =============================================================================
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_spotify_auth_routes(app) : Tüm Spotify kimlik doğrulama rotalarını kaydeder.
# -----------------------------------------------------------------------------
def init_spotify_auth_routes(app: Flask):
    """
    Spotify kimlik doğrulama ile ilgili tüm rotaları belirtilen Flask uygulamasına kaydeder.
    Bu fonksiyon içinde, API endpoint'leri olarak hizmet verecek olan
    iç içe fonksiyonlar tanımlanır ve Flask uygulamasına bağlanır.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    # print("Spotify kimlik doğrulama rotaları başlatılıyor...") # Geliştirme için log

    # Servis ve depo örneklerinin başlatılması
    spotify_auth_service = SpotifyAuthService()
    spotify_repo = SpotifyUserRepository() # Spotify kullanıcı verilerine erişim için

    # =========================================================================
    # 3.0 KİMLİK DOĞRULAMA ROTALARI (AUTHENTICATION ROUTES)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 3.1. spotify_auth() : Spotify OAuth akışını başlatır.
    #      Rota: /spotify/auth (GET)
    # -------------------------------------------------------------------------
    @app.route('/spotify/auth', methods=['GET'])
    def spotify_auth() -> Any: # redirect() Any döndürebilir
        """
        Kullanıcının Spotify hesabını bağlamak için OAuth 2.0 kimlik doğrulama
        akışını başlatır. Kullanıcıyı Spotify'ın yetkilendirme URL'sine yönlendirir.
        Kullanıcının uygulamada oturum açmış olması ve profil sayfasından
        Spotify Client ID ve Client Secret bilgilerini girmiş olması gerekir.
        """
        # print("API çağrısı: /spotify/auth") # Geliştirme için log
        username: Optional[str] = session_is_user_logged_in()

        if not username:
            flash("Spotify hesabınızı bağlamak için lütfen önce giriş yapın.", "warning")
            # print("Yetkisiz erişim denemesi: /spotify/auth (oturum yok)") # Geliştirme için log
            return redirect(url_for('auth_bp.login_page')) # auth_bp.login_page veya uygun giriş sayfası rotası

        try:
            # print(f"Spotify yetkilendirme isteği: Kullanıcı={username}") # Geliştirme için log
            # Kullanıcının Spotify Client ID ve Secret bilgilerini veritabanından al
            spotify_credentials: Optional[Dict[str, Any]] = spotify_repo.spotify_get_user_data(username)

            if not spotify_credentials or \
               not spotify_credentials.get('client_id') or \
               not spotify_credentials.get('client_secret') or \
               spotify_credentials['client_id'].strip() == "" or \
               spotify_credentials['client_secret'].strip() == "":
                flash("Lütfen profil sayfanızdan Spotify Client ID ve Client Secret bilgilerinizi girin.", "error")
                # print(f"Spotify kimlik bilgileri eksik veya geçersiz: {username}") # Geliştirme için log
                return redirect(url_for('profile')) # profile veya uygun profil sayfası rotası

            # SpotifyAuthService üzerinden yetkilendirme URL'sini al
            auth_url: str = spotify_auth_service.get_authorization_url(
                username,
                spotify_credentials['client_id'], # Servise client_id'yi ilet
                # REDIRECT_URI zaten serviste veya config'de tanımlı olmalı
            )
            # print(f"Spotify yetkilendirme URL'si oluşturuldu: {auth_url}") # Geliştirme için log
            return redirect(auth_url)

        except Exception as e:
            flash(f"Spotify bağlantısı sırasında bir hata oluştu: {str(e)}", "error")
            # print(f"Spotify yetkilendirme hatası ({username}): {str(e)}") # Geliştirme için log
            return redirect(url_for('profile')) # Hata durumunda profil sayfasına yönlendir

    # -------------------------------------------------------------------------
    # 3.2. spotify_callback() : Spotify OAuth geri çağrısını işler.
    #      Rota: /spotify/callback (GET)
    # -------------------------------------------------------------------------
    @app.route('/spotify/callback', methods=['GET'])
    def spotify_callback() -> Any: # redirect() Any döndürebilir
        """
        Spotify OAuth 2.0 akışının geri çağrı (callback) endpoint'i.
        Spotify tarafından yetkilendirme kodu ile çağrılır. Bu kod,
        erişim (access) ve yenileme (refresh) token'ları ile değiştirilir.
        Alınan token'lar ve kullanıcı bilgileri saklanır.
        """
        # print("API çağrısı: /spotify/callback") # Geliştirme için log
        error: Optional[str] = request.args.get('error')
        if error:
            flash(f"Spotify yetkilendirme hatası: {error}. Lütfen tekrar deneyin.", "error")
            # print(f"Spotify callback hatası (parametre): {error}") # Geliştirme için log
            return redirect(url_for('profile'))

        auth_code: Optional[str] = request.args.get('code')
        if not auth_code:
            flash("Spotify yetkilendirme kodu alınamadı. Bağlantı başarısız.", "error")
            # print("Spotify callback: Yetkilendirme kodu (code) eksik.") # Geliştirme için log
            return redirect(url_for('profile'))

        username: Optional[str] = session.get('username')
        if not username:
            flash("Kullanıcı oturumu zaman aşımına uğramış olabilir. Lütfen tekrar giriş yapın.", "warning")
            # print("Spotify callback: Kullanıcı oturumu bulunamadı.") # Geliştirme için log
            return redirect(url_for('login_page'))

        try:
            # print(f"Spotify callback: Kullanıcı={username}, Kod={auth_code[:10]}...") # Geliştirme için log
            # Kullanıcının Spotify Client ID ve Secret bilgilerini veritabanından al
            spotify_credentials: Optional[Dict[str, Any]] = spotify_repo.spotify_get_user_data(username)
            if not spotify_credentials or not spotify_credentials.get('client_id') or not spotify_credentials.get('client_secret'):
                flash("Spotify kimlik bilgileri (Client ID/Secret) bulunamadı. Lütfen profil sayfanızdan kontrol edin.", "error")
                # print(f"Spotify callback: Kimlik bilgileri eksik ({username}).") # Geliştirme için log
                return redirect(url_for('profile'))

            client_id: str = spotify_credentials['client_id']
            client_secret: str = spotify_credentials['client_secret']

            # Yetkilendirme kodunu token'larla değiştir
            token_info: Optional[Dict[str, Any]] = spotify_auth_service.exchange_code_for_token(
                auth_code, client_id, client_secret
            )
            if not token_info or 'access_token' not in token_info:
                flash("Spotify erişim token'ı alınamadı. Bağlantı başarısız.", "error")
                # print(f"Spotify callback: Token değişimi başarısız ({username}). Token info: {token_info}") # Geliştirme için log
                return redirect(url_for('profile'))

            access_token: str = token_info['access_token']
            # refresh_token her zaman gelmeyebilir, özellikle ilk yetkilendirmeden sonraki akışlarda.
            # Eğer refresh_token yoksa ve daha önce kaydedilmiş bir tane varsa, onu korumak gerekebilir.
            # SpotifyAuthService bu mantığı içermeli.
            new_refresh_token: Optional[str] = token_info.get('refresh_token')
            expires_in: int = token_info.get('expires_in', 3600) # Saniye cinsinden

            # print(f"Spotify callback: Tokenlar alındı. AccessToken: {access_token[:10]}..., RefreshToken: {new_refresh_token[:10] if new_refresh_token else 'Yok'}") # Geliştirme için log

            # Token bilgilerini session'a kaydet (isteğe bağlı, genellikle access token kısa ömürlüdür)
            # Uzun süreli işlemler için refresh token veritabanında saklanmalıdır.
            session['spotify_access_token'] = access_token
            session['spotify_token_expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            if new_refresh_token:
                 session['spotify_refresh_token'] = new_refresh_token # Sadece varsa güncelle

            # Spotify kullanıcı profil bilgilerini al
            # Bu bilgi genellikle spotify_user_id'yi almak için kullanılır.
            # PROFILE_URL config'den gelmeli. Örnek: SPOTIFY_CONFIG.PROFILE_URL
            # Geçici olarak sabit URL kullanıldı, config'e taşınmalı.
            # SPOTIFY_PROFILE_URL = "https://api.spotify.com/v1/me"
            # headers = {"Authorization": f"Bearer {access_token}"}
            # user_response = requests.get(SPOTIFY_PROFILE_URL, headers=headers)
            # user_response.raise_for_status() # Hata durumunda istisna fırlatır
            # spotify_user_profile: Dict[str, Any] = user_response.json()
            # spotify_user_id: Optional[str] = spotify_user_profile.get('id')

            # Servis katmanı Spotify kullanıcı ID'sini ve refresh token'ı kaydetmeli
            # SpotifyAuthService.save_spotify_user_info bu işlemi yapmalı ve gerekirse
            # Spotify API'den kullanıcı ID'sini almalı.
            # print(f"Spotify callback: Kullanıcı bilgileri kaydediliyor ({username})...") # Geliştirme için log
            spotify_user_id = spotify_auth_service.save_spotify_user_info(
                username=username,
                access_token=access_token, # Servis, bu token ile kullanıcı ID'sini alabilir
                refresh_token_to_save=new_refresh_token # Sadece yeni bir refresh token varsa güncelle
            )

            if not spotify_user_id:
                flash("Spotify kullanıcı ID'si alınamadı veya kaydedilemedi.", "error")
                # print(f"Spotify callback: Spotify kullanıcı ID'si alınamadı/kaydedilemedi ({username}).") # Geliştirme için log
                return redirect(url_for('profile'))

            flash("Spotify hesabınız başarıyla bağlandı!", "success")
            # print(f"Spotify callback: Hesap başarıyla bağlandı ({username}, SpotifyID: {spotify_user_id}).") # Geliştirme için log
            return redirect(url_for('profile'))

        except requests.exceptions.RequestException as req_err:
            flash(f"Spotify ile iletişim sırasında bir ağ hatası oluştu: {str(req_err)}", "error")
            # print(f"Spotify callback ({username}) ağ hatası: {str(req_err)}") # Geliştirme için log
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f"Spotify bağlantısı sırasında beklenmedik bir hata oluştu: {str(e)}", "error")
            # print(f"Spotify callback ({username}) genel hata: {str(e)}") # Geliştirme için log
            return redirect(url_for('profile'))

    # -------------------------------------------------------------------------
    # 3.3. spotify_unlink() : Kullanıcının Spotify hesap bağlantısını keser.
    #      Rota: /spotify/unlink (GET)
    # -------------------------------------------------------------------------
    @app.route('/spotify/unlink', methods=['GET']) # Genellikle POST olmalı ama basitlik için GET bırakılmış olabilir.
    def spotify_unlink() -> Any: # redirect() Any döndürebilir
        """
        Kullanıcının bağlı Spotify hesabının uygulama ile olan bağlantısını keser.
        Veritabanındaki ilgili tokenları ve bağlantı durumunu günceller.
        Kullanıcının oturum açmış olması gerekir.
        """
        # print("API çağrısı: /spotify/unlink") # Geliştirme için log
        username: Optional[str] = session_is_user_logged_in() # veya session.get('username')

        if not username: # Orijinal kodda session.get('logged_in') vardı, username daha doğru.
            flash("Bu işlemi yapmak için lütfen önce giriş yapın.", "warning")
            # print("Yetkisiz erişim denemesi: /spotify/unlink (oturum yok)") # Geliştirme için log
            return redirect(url_for('ogin'))

        try:
            # print(f"Spotify hesap bağlantısı kesiliyor: Kullanıcı={username}") # Geliştirme için log
            success: bool = spotify_auth_service.unlink_spotify_account(username)

            if success:
                flash("Spotify hesap bağlantınız başarıyla kaldırıldı.", "success")
                # Session'dan da Spotify ile ilgili bilgileri temizleyebiliriz.
                session.pop('spotify_access_token', None)
                session.pop('spotify_token_expires_at', None)
                session.pop('spotify_refresh_token', None)
                # print(f"Spotify hesap bağlantısı başarıyla kesildi ({username}).") # Geliştirme için log
            else:
                # Bu durum genellikle servis içinde bir hata oluştuğunda veya
                # zaten bağlı bir hesap olmadığında meydana gelebilir.
                flash("Spotify hesap bağlantısı kaldırılırken bir sorun oluştu veya zaten bağlı değildi.", "error")
                # print(f"Spotify hesap bağlantısı kesilemedi ({username}).") # Geliştirme için log

            return redirect(url_for('profile'))

        except Exception as e:
            flash(f"Spotify bağlantısı kesilirken bir hata oluştu: {str(e)}", "error")
            # print(f"Spotify bağlantısı kesme hatası ({username}): {str(e)}") # Geliştirme için log
            return redirect(url_for('profile'))

    # print("Spotify kimlik doğrulama rotaları başarıyla yüklendi.") # Geliştirme için log
# =============================================================================
# Spotify Kimlik Doğrulama Rotaları Modülü Sonu
# =============================================================================
