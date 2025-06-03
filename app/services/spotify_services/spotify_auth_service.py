# =============================================================================
# Spotify Kimlik Doğrulama Servis Modülü (Spotify Authentication Service Module)
# =============================================================================
# Bu modül, Spotify OAuth 2.0 kimlik doğrulama akışını yönetmek,
# erişim (access) ve yenileme (refresh) token'larını işlemek, kullanıcıların
# Spotify hesap bilgilerini kaydetmek ve bağlantıyı kesmek gibi işlemleri
# gerçekleştiren bir servis sınıfı (SpotifyAuthService) içerir.
# SpotifyRepository üzerinden veritabanı işlemleri yapar ve SpotifyConfig
# üzerinden yapılandırma ayarlarını kullanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modülleri, Flask session, yapılandırmalar ve depoların içe aktarılması.
# 2.0  SPOTIFY KİMLİK DOĞRULAMA SERVİS SINIFI (SPOTIFY AUTHENTICATION SERVICE CLASS)
#      2.1. SpotifyAuthService
#           : Spotify kimlik doğrulama işlemlerini yöneten ana servis sınıfı.
#           2.1.1.  __init__()
#                   : Başlatıcı metot. Gerekli yapılandırmaları ve depo örneğini ayarlar.
#
#           2.2. OAUTH AKIŞI METOTLARI (OAUTH FLOW METHODS)
#                2.2.1. get_authorization_url(username, client_id)
#                       : Spotify kullanıcı yetkilendirme URL'sini oluşturur.
#                2.2.2. exchange_code_for_token(code, client_id, client_secret)
#                       : Alınan yetkilendirme kodunu erişim ve yenileme token'ları ile değiştirir.
#
#           2.3. TOKEN YÖNETİMİ METOTLARI (TOKEN MANAGEMENT METHODS)
#                2.3.1. refresh_access_token(username)
#                       : Süresi dolmuş bir erişim token'ını yenileme token'ı kullanarak yeniler.
#                2.3.2. get_valid_access_token(username)
#                       : Kullanıcı için geçerli bir erişim token'ı alır (önce session'dan,
#                         gerekirse yenileyerek).
#
#           2.4. HESAP YÖNETİMİ METOTLARI (ACCOUNT MANAGEMENT METHODS)
#                2.4.1. save_spotify_user_info(username, access_token, refresh_token_to_save=None)
#                       : Spotify kullanıcı ID'sini alır ve token bilgilerini veritabanına kaydeder/günceller.
#                2.4.2. unlink_spotify_account(username)
#                       : Kullanıcının Spotify hesap bağlantısını kaldırır.
#
#           2.5. YARDIMCI METOTLAR (HELPER METHODS)
#                2.5.1. _ensure_datetime_naive(dt)
#                       : Verilen datetime nesnesini veya string'i saf (naive) datetime nesnesine dönüştürür.
#                       (Bu metot orijinal dosyada vardı, ancak bu servis içinde doğrudan kullanılmıyor gibi
#                        görünüyor. Eğer `get_valid_access_token` içinde `datetime.now()` ile karşılaştırma
#                        yapılıyorsa ve `session['token_expires_at']` aware ise gerekli olabilir.
#                        Şimdilik yerinde bırakıldı, gerekliliği gözden geçirilebilir.)
#                2.5.2. get_spotify_user_id_from_token(access_token)
#                       : Verilen erişim token'ını kullanarak Spotify kullanıcı ID'sini alır. (Yeni Eklendi)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import base64 # Token isteklerinde Basic Auth için
import requests # HTTP istekleri yapmak için
from datetime import datetime, timedelta # Zaman ve süre işlemleri için
from flask import session # Kullanıcı oturum bilgilerini saklamak için
from app.config.spotify_config import SpotifyConfig # Spotify API yapılandırma sabitleri
from app.database.spotify_user_repository import SpotifyUserRepository # Spotify veritabanı işlemleri için
from typing import Optional, Dict, Any, Union # Tip ipuçları için

# =============================================================================
# 2.0 SPOTIFY KİMLİK DOĞRULAMA SERVİS SINIFI (SPOTIFY AUTHENTICATION SERVICE CLASS)
# =============================================================================
class SpotifyAuthService:
    """
    Spotify OAuth 2.0 kimlik doğrulama akışını yönetir, tokenları işler
    ve kullanıcıların Spotify hesap bilgilerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__() : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self):
        """
        SpotifyAuthService sınıfının başlatıcı metodu.
        Spotify API endpoint URL'lerini, yönlendirme URI'sini, izin kapsamlarını
        ve SpotifyRepository örneğini başlatır.
        """
        self.auth_url: str = SpotifyConfig.AUTH_URL
        self.token_url: str = SpotifyConfig.TOKEN_URL
        self.redirect_uri: str = SpotifyConfig.REDIRECT_URI
        self.scopes: str = SpotifyConfig.SCOPES
        self.spotify_repo: SpotifyUserRepository = SpotifyUserRepository()
        self.profile_url: str = SpotifyConfig.PROFILE_URL # Kullanıcı ID'si almak için
        # print("SpotifyAuthService örneği oluşturuldu.") # Geliştirme için log

    # =========================================================================
    # 2.2. OAUTH AKIŞI METOTLARI (OAUTH FLOW METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.2.1. get_authorization_url(username, client_id) : Yetkilendirme URL'sini oluşturur.
    # -------------------------------------------------------------------------
    def get_authorization_url(self, username: str, client_id: Optional[str]) -> Optional[str]:
        """
        Kullanıcıyı Spotify'da yetkilendirme yapması için yönlendirilecek URL'yi oluşturur.
        Bu URL, kullanıcının uygulamaya belirli izinleri (scopes) vermesini ister.

        Args:
            username (str): Yetkilendirme isteyen Beatify kullanıcısının adı.
                            (Bu argüman doğrudan URL oluşturmada kullanılmıyor gibi,
                             ancak gelecekte state parametresi için kullanılabilir.)
            client_id (Optional[str]): Kullanıcının Spotify Developer Dashboard'dan aldığı Client ID.
                                       Eğer None ise veya boşsa, URL oluşturulamaz.

        Returns:
            Optional[str]: Oluşturulan Spotify yetkilendirme URL'si.
                           Client ID eksikse veya bir hata oluşursa None döner.
        """
        # print(f"Spotify yetkilendirme URL'si isteniyor: Kullanıcı={username}, ClientID={client_id}") # Geliştirme için log
        if not client_id or not client_id.strip():
            # print("Client ID eksik, yetkilendirme URL'si oluşturulamıyor.") # Geliştirme için log
            # Bu durumda bir istisna fırlatmak daha iyi olabilir.
            raise ValueError("Spotify Client ID sağlanmadı veya geçersiz.")

        auth_params: Dict[str, str] = {
            "client_id": client_id,
            "response_type": "code", # OAuth akış türü
            "redirect_uri": self.redirect_uri, # Spotify'dan geri dönülecek adres
            "scope": self.scopes, # İstenen izinler
            "show_dialog": "true" # Her seferinde kullanıcıya onay penceresi göster (isteğe bağlı)
            # "state": generate_random_string() # CSRF koruması için state parametresi eklenebilir
        }

        # Parametreleri URL'ye uygun şekilde encode et
        url_args: str = "&".join([f"{key}={requests.utils.quote(str(val))}" for key, val in auth_params.items()])
        authorization_url: str = f"{self.auth_url}?{url_args}"
        # print(f"Oluşturulan yetkilendirme URL'si: {authorization_url}") # Geliştirme için log
        return authorization_url

    # -------------------------------------------------------------------------
    # 2.2.2. exchange_code_for_token(...) : Yetkilendirme kodunu token ile değiştirir.
    # -------------------------------------------------------------------------
    def exchange_code_for_token(self, code: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        Spotify'dan alınan yetkilendirme (`code`) kodunu kullanarak erişim (access)
        ve yenileme (refresh) token'larını alır.

        Args:
            code (str): Spotify OAuth callback'inden alınan yetkilendirme kodu.
            client_id (str): Uygulamanın Spotify Client ID'si.
            client_secret (str): Uygulamanın Spotify Client Secret'ı.

        Returns:
            Optional[Dict[str, Any]]: Token bilgilerini (access_token, refresh_token, expires_in vb.)
                                      içeren bir sözlük. Hata durumunda None döner.
        """
        # print(f"Yetkilendirme kodu token ile değiştiriliyor: Kod={code[:10]}...") # Geliştirme için log
        try:
            # Client ID ve Secret'ı Base64 formatında encode et (Basic Auth için)
            credentials: str = f"{client_id}:{client_secret}"
            base64_credentials: str = base64.b64encode(credentials.encode()).decode()

            payload: Dict[str, str] = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri # Yetkilendirme isteğindeki ile aynı olmalı
            }
            headers: Dict[str, str] = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            # print(f"Token isteği yapılıyor: URL={self.token_url}") # Geliştirme için log
            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status() # HTTP 4xx veya 5xx durumlarında istisna fırlatır

            token_info: Dict[str, Any] = response.json()
            # print(f"Token bilgileri alındı: AccessTokenVarMi={token_info.get('access_token') is not None}") # Geliştirme için log

            # Alınan token bilgilerini (özellikle access_token ve expires_at) session'a kaydetmek
            # genellikle rota (controller) katmanının sorumluluğundadır.
            # Ancak orijinal kodda burada yapılmış, bu yüzden şimdilik korunuyor.
            # Daha modüler bir yapıda, bu servis sadece token_info'yu döndürmeli.
            if 'access_token' in token_info:
                session['spotify_access_token'] = token_info['access_token']
                expires_in = token_info.get('expires_in', 3600) # Saniye cinsinden
                session['spotify_token_expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                if 'refresh_token' in token_info: # refresh_token her zaman gelmeyebilir
                    session['spotify_refresh_token'] = token_info['refresh_token']
            
            return token_info

        except requests.exceptions.RequestException as req_err:
            # print(f"Token değişimi sırasında ağ/HTTP hatası: {str(req_err)}") # Geliştirme için log
            # print(f"Yanıt içeriği (hata varsa): {req_err.response.text if req_err.response else 'Yanıt yok'}")
            return None
        except Exception as e:
            # print(f"Token değişimi sırasında genel bir hata oluştu: {str(e)}") # Geliştirme için log
            # import traceback
            # print(traceback.format_exc())
            return None

    # =========================================================================
    # 2.3. TOKEN YÖNETİMİ METOTLARI (TOKEN MANAGEMENT METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.3.1. refresh_access_token(username) : Erişim token'ını yeniler.
    # -------------------------------------------------------------------------
    def refresh_access_token(self, username: str) -> Optional[str]:
        """
        Süresi dolmuş bir Spotify erişim token'ını, kullanıcıya ait yenileme
        token'ını kullanarak yeniler. Yeni alınan token bilgilerini session'a
        ve gerekirse (yeni bir refresh_token geldiyse) veritabanına kaydeder.

        Args:
            username (str): Token'ı yenilenecek Beatify kullanıcısının adı.

        Returns:
            Optional[str]: Yeni alınan erişim token'ı. Hata durumunda None döner.
        """
        # print(f"Erişim token'ı yenileniyor: Kullanıcı={username}") # Geliştirme için log
        try:
            spotify_user_data: Optional[Dict[str, Any]] = self.spotify_repo.spotify_get_user_data(username)
            if not spotify_user_data:
                # print(f"Token yenileme için kullanıcı ({username}) Spotify verisi bulunamadı.") # Geliştirme için log
                return None

            client_id: Optional[str] = spotify_user_data.get('client_id')
            client_secret: Optional[str] = spotify_user_data.get('client_secret')
            current_refresh_token: Optional[str] = spotify_user_data.get('refresh_token')

            if not all([client_id, client_secret, current_refresh_token]):
                # print(f"Token yenileme için gerekli bilgiler eksik ({username}): ClientIDVar={client_id is not None}, ClientSecretVar={client_secret is not None}, RefreshTokenVar={current_refresh_token is not None}") # Geliştirme için log
                return None

            credentials: str = f"{client_id}:{client_secret}"
            base64_credentials: str = base64.b64encode(credentials.encode()).decode()

            payload: Dict[str, str] = {
                "grant_type": "refresh_token",
                "refresh_token": current_refresh_token
            }
            headers: Dict[str, str] = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            # print(f"Token yenileme isteği yapılıyor: URL={self.token_url}") # Geliştirme için log
            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status() # HTTP hatalarında istisna fırlat

            new_token_info: Dict[str, Any] = response.json()
            new_access_token: Optional[str] = new_token_info.get('access_token')

            if not new_access_token:
                # print(f"Token yenileme yanıtında access_token bulunamadı ({username}). Yanıt: {new_token_info}") # Geliştirme için log
                return None

            # print(f"Yeni erişim token'ı alındı ({username}): {new_access_token[:10]}...") # Geliştirme için log
            session['spotify_access_token'] = new_access_token
            expires_in = new_token_info.get('expires_in', 3600)
            session['spotify_token_expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            # Spotify bazen refresh_token isteğinde yeni bir refresh_token döndürebilir.
            # Eğer döndürdüyse, bunu veritabanında güncellemeliyiz.
            new_refresh_token_from_response: Optional[str] = new_token_info.get('refresh_token')
            refresh_token_to_save_in_db = new_refresh_token_from_response or current_refresh_token

            if new_refresh_token_from_response:
                session['spotify_refresh_token'] = new_refresh_token_from_response
                # print(f"Yeni refresh token alındı ve session'a kaydedildi ({username}): {new_refresh_token_from_response[:10]}...") # Geliştirme için log
            
            # Veritabanındaki refresh token'ı güncelle (yeni geldiyse yenisiyle, gelmediyse eskisiyle)
            # `spotify_update_user_info` metodu orijinalde `spotify_user_id` de istiyordu.
            # Bu metot `spotify_update_refresh_token_data` olarak değiştirilebilir veya
            # `spotify_user_id` `spotify_user_data`'dan alınabilir.
            # Orijinal koddaki `spotify_update_user_info` kullanılıyorsa:
            if spotify_user_data.get('spotify_user_id'):
                 self.spotify_repo.spotify_update_user_connection_info( # Bu metot daha uygun olabilir
                    username=username,
                    spotify_user_id=spotify_user_data['spotify_user_id'], # Mevcut ID'yi koru
                    refresh_token=refresh_token_to_save_in_db
                )
                # print(f"Veritabanındaki refresh token güncellendi ({username}).") # Geliştirme için log
            else:
                # print(f"Kullanıcı ({username}) için Spotify User ID bulunamadığından refresh token DB'de güncellenemedi.") # Geliştirme için log
                pass # Spotify User ID yoksa güncelleme yapma veya hata logla

            return new_access_token

        except requests.exceptions.RequestException as req_err:
            # print(f"Token yenileme sırasında ağ/HTTP hatası ({username}): {str(req_err)}") # Geliştirme için log
            # print(f"Yanıt içeriği (hata varsa): {req_err.response.text if req_err.response else 'Yanıt yok'}")
            # Token yenileme başarısız olursa, eski tokenları session'dan silmek iyi bir pratik olabilir.
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires_at', None)
            return None
        except Exception as e:
            # print(f"Token yenileme sırasında genel bir hata oluştu ({username}): {str(e)}") # Geliştirme için log
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires_at', None)
            return None

    # -------------------------------------------------------------------------
    # 2.3.2. get_valid_access_token(username) : Geçerli bir erişim token'ı alır.
    # -------------------------------------------------------------------------
    def get_valid_access_token(self, username: str) -> Optional[str]:
        """
        Kullanıcı için geçerli bir Spotify erişim token'ı döndürür.
        Öncelikle session'daki token'ı kontrol eder, süresi dolmuşsa veya
        yoksa `refresh_access_token` metodunu kullanarak yenisini alır.

        Args:
            username (str): Token'ı alınacak Beatify kullanıcısının adı.

        Returns:
            Optional[str]: Geçerli erişim token'ı. Hata durumunda veya token alınamazsa None.
        """
        # print(f"Geçerli erişim token'ı kontrol ediliyor: {username}") # Geliştirme için log
        access_token: Optional[str] = session.get('spotify_access_token')
        token_expires_at_iso: Optional[str] = session.get('spotify_token_expires_at')

        if access_token and token_expires_at_iso:
            try:
                token_expires_at_dt: datetime = self._ensure_datetime_naive(datetime.fromisoformat(token_expires_at_iso))
                now_naive: datetime = self._ensure_datetime_naive(datetime.now())

                # Token'ın süresinin dolmasına 5 dakikadan fazla varsa geçerli kabul et
                if token_expires_at_dt and now_naive and (token_expires_at_dt > now_naive + timedelta(minutes=5)):
                    # print(f"Session'dan geçerli token bulundu ({username}): {access_token[:10]}...") # Geliştirme için log
                    return access_token
                else:
                    # print(f"Session'daki token ({username}) süresi dolmuş veya dolmak üzere.") # Geliştirme için log
                    pass # Süresi dolmuş, yenilemeye devam et
            except ValueError:
                # print(f"Session'daki token bitiş tarihi ({token_expires_at_iso}) geçersiz formatta ({username}).") # Geliştirme için log
                pass # Geçersiz format, yenilemeye devam et
        else:
            # print(f"Session'da token veya bitiş tarihi bulunamadı ({username}).") # Geliştirme için log
            pass # Session'da token yok, yenilemeye devam et

        # print(f"Session'da geçerli token yok, yenisi deneniyor ({username})...") # Geliştirme için log
        return self.refresh_access_token(username)

    # =========================================================================
    # 2.4. HESAP YÖNETİMİ METOTLARI (ACCOUNT MANAGEMENT METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.5.2. get_spotify_user_id_from_token(access_token) : Token ile Spotify kullanıcı ID'sini alır. (Yeni Eklendi)
    # -------------------------------------------------------------------------
    def get_spotify_user_id_from_token(self, access_token: str) -> Optional[str]:
        """
        Verilen Spotify erişim token'ını kullanarak Spotify API'sinden
        kullanıcının profil bilgilerini ve dolayısıyla Spotify kullanıcı ID'sini alır.

        Args:
            access_token (str): Geçerli Spotify erişim token'ı.

        Returns:
            Optional[str]: Spotify kullanıcı ID'si. Hata durumunda None.
        """
        if not access_token:
            return None
        
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            # print(f"Token ile Spotify kullanıcı ID'si alınıyor: URL={self.profile_url}") # Geliştirme için log
            response = requests.get(self.profile_url, headers=headers, timeout=10)
            response.raise_for_status() # HTTP hatalarında istisna fırlat
            user_profile_data = response.json()
            spotify_user_id = user_profile_data.get('id')
            # print(f"Spotify kullanıcı ID'si alındı: {spotify_user_id}") # Geliştirme için log
            return spotify_user_id
        except requests.exceptions.RequestException as req_err:
            # print(f"Spotify kullanıcı ID'si alınırken ağ/HTTP hatası: {str(req_err)}") # Geliştirme için log
            return None
        except Exception as e:
            # print(f"Spotify kullanıcı ID'si alınırken genel hata: {str(e)}") # Geliştirme için log
            return None

    # -------------------------------------------------------------------------
    # 2.4.1. save_spotify_user_info(...) : Spotify kullanıcı bilgilerini kaydeder.
    # -------------------------------------------------------------------------
    def save_spotify_user_info(self, username: str, access_token: str, refresh_token_to_save: Optional[str]) -> Optional[str]:
        """
        Verilen erişim token'ı ile Spotify kullanıcı ID'sini alır ve bu ID'yi
        yenileme token'ı ile birlikte veritabanına kaydeder/günceller.
        Ayrıca `beatify_users` tablosundaki bağlantı durumunu günceller.

        Args:
            username (str): Bilgileri kaydedilecek Beatify kullanıcısının adı.
            access_token (str): Spotify'dan alınan geçerli erişim token'ı.
            refresh_token_to_save (Optional[str]): Kaydedilecek/güncellenecek yenileme token'ı.
                                                  Eğer None ise ve veritabanında zaten bir tane varsa, o korunur.

        Returns:
            Optional[str]: Başarıyla alınan ve kaydedilen Spotify Kullanıcı ID'si. Hata durumunda None.
        """
        # print(f"Spotify kullanıcı bilgileri kaydediliyor: {username}") # Geliştirme için log
        try:
            spotify_user_id: Optional[str] = self.get_spotify_user_id_from_token(access_token)

            if not spotify_user_id:
                # print(f"Spotify kullanıcı ID'si alınamadı, bilgiler kaydedilemiyor ({username}).") # Geliştirme için log
                return None

            # Eğer refresh_token_to_save None ise, mevcut refresh token'ı korumak isteyebiliriz.
            # SpotifyRepository.spotify_update_user_connection_info bu mantığı içerebilir
            # veya burada mevcut refresh token'ı çekip, None ise onu kullanabiliriz.
            
            # Orijinal kodda spotify_repo.spotify_update_user_info vardı, bu metot
            # SpotifyRepository'de spotify_update_user_connection_info olarak güncellenmişti.
            # Bu metot, client_id ve client_secret'ı güncellemez, sadece bağlantı bilgilerini.
            
            # Eğer refresh_token_to_save None ise ve DB'de varsa onu kullan
            final_refresh_token = refresh_token_to_save
            if not final_refresh_token:
                existing_data = self.spotify_repo.spotify_get_user_data(username)
                if existing_data and existing_data.get('refresh_token'):
                    final_refresh_token = existing_data['refresh_token']
                    # print(f"Yeni refresh token sağlanmadı, DB'deki mevcut token kullanılacak ({username}): {final_refresh_token[:10]}...") # Geliştirme için log

            if not final_refresh_token:
                # print(f"Kaydedilecek refresh token bulunamadı ({username}).") # Geliştirme için log
                # Bu durumda işlem başarısız sayılabilir veya sadece spotify_user_id güncellenebilir.
                # Spotify genellikle ilk yetkilendirmede refresh token verir.
                # Şimdilik, refresh token olmadan devam etmeyelim.
                # raise ValueError("Kaydedilecek refresh token bulunamadı.") # Veya None dön
                return None


            # print(f"Veritabanına kaydedilecek bilgiler ({username}): SpotifyID={spotify_user_id}, RefreshToken={final_refresh_token[:10] if final_refresh_token else 'Yok'}") # Geliştirme için log
            success: bool = self.spotify_repo.spotify_update_user_connection_info(
                username=username,
                spotify_user_id=spotify_user_id,
                refresh_token=final_refresh_token # type: ignore # final_refresh_token burada string olmalı
            )

            if not success:
                # print(f"Veritabanına Spotify kullanıcı bilgileri kaydedilemedi ({username}).") # Geliştirme için log
                return None
            
            # Session'a da güncel bilgileri kaydet (refresh token özellikle)
            if final_refresh_token:
                session['spotify_refresh_token'] = final_refresh_token
            session['spotify_user_id'] = spotify_user_id # Bu bilgi session'da tutulmayabilir.
            
            # print(f"Spotify kullanıcı bilgileri başarıyla kaydedildi ({username}), SpotifyID: {spotify_user_id}") # Geliştirme için log
            return spotify_user_id

        except Exception as e:
            # print(f"Spotify kullanıcı bilgileri kaydedilirken hata oluştu ({username}): {str(e)}") # Geliştirme için log
            # import traceback
            # print(traceback.format_exc())
            return None

    # -------------------------------------------------------------------------
    # 2.4.2. unlink_spotify_account(username) : Spotify hesap bağlantısını kaldırır.
    # -------------------------------------------------------------------------
    def unlink_spotify_account(self, username: str) -> bool:
        """
        Kullanıcının Beatify uygulaması ile olan Spotify hesap bağlantısını kaldırır.
        Bu işlem, session'daki Spotify tokenlarını ve veritabanındaki ilgili
        kayıtları (veya bağlantı bilgilerini) temizler/sıfırlar.

        Args:
            username (str): Spotify hesap bağlantısı kaldırılacak Beatify kullanıcısının adı.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"Spotify hesap bağlantısı kaldırılıyor: {username}") # Geliştirme için log
        try:
            # Session'dan Spotify ile ilgili verileri temizle
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires_at', None)
            session.pop('spotify_refresh_token', None)
            session.pop('spotify_user_id', None) # Eğer tutuluyorsa
            # print(f"Session'daki Spotify verileri temizlendi ({username}).") # Geliştirme için log

            # Veritabanından bağlantı bilgilerini sil/sıfırla
            # Bu metot, `beatify_users` tablosundaki `is_spotify_connected` flag'ini de false yapmalı.
            success: bool = self.spotify_repo.spotify_delete_linked_account_data(username)

            if not success:
                # print(f"Veritabanından Spotify bağlantı bilgileri kaldırılamadı ({username}).") # Geliştirme için log
                # Bu durumda bile session temizlendiği için kullanıcıya başarılı mesajı verilebilir
                # veya daha spesifik bir hata gösterilebilir.
                return False # Veya True dönüp sadece logla

            # print(f"Spotify hesap bağlantısı başarıyla kaldırıldı ({username}).") # Geliştirme için log
            return True

        except Exception as e:
            # print(f"Spotify hesap bağlantısı kaldırılırken hata oluştu ({username}): {str(e)}") # Geliştirme için log
            return False

    # =========================================================================
    # 2.5. YARDIMCI METOTLAR (HELPER METHODS)
    # =========================================================================
    # Bu metot, `get_valid_access_token` içinde kullanıldığı için burada kalabilir.

    # -------------------------------------------------------------------------
    # 2.5.1. _ensure_datetime_naive(dt) : Datetime'ı saf (naive) hale getirir.
    # -------------------------------------------------------------------------
    def _ensure_datetime_naive(self, dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """
        Verilen datetime nesnesini veya ISO formatındaki string'i,
        zaman dilimi bilgisi olmayan (naive) bir datetime nesnesine dönüştürür.

        Args:
            dt (Optional[Union[datetime, str]]): Dönüştürülecek datetime nesnesi veya ISO formatında string.

        Returns:
            Optional[datetime]: Zaman dilimi bilgisi olmayan (naive) datetime nesnesi veya None.
        """
        if dt is None:
            return None
        if isinstance(dt, str):
            try:
                # ISO formatından datetime'a çevirirken 'Z' (Zulu/UTC) varsa +00:00 ile değiştir.
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                # print(f"Yardımcı metot: Geçersiz ISO tarih string'i: {dt}") # Geliştirme için log
                return None
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            # print(f"Yardımcı metot: Beklenmeyen tarih tipi: {type(dt)}") # Geliştirme için log
            return None

        if dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None:
            # print(f"Yardımcı metot: Zaman dilimli tarih ({dt_obj}) naive yapılıyor.") # Geliştirme için log
            return dt_obj.replace(tzinfo=None) # Zaman dilimi bilgisini kaldır
        return dt_obj # Zaten naive ise veya tzinfo yoksa olduğu gibi döndür

# =============================================================================
# Spotify Kimlik Doğrulama Servis Modülü Sonu
# =============================================================================
