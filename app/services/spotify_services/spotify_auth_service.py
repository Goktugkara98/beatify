# =============================================================================
# Spotify Kimlik Doğrulama Servis Modülü (SpotifyAuthService)
# =============================================================================
# Bu modül, Spotify OAuth 2.0 kimlik doğrulama akışını yönetmek,
# erişim ve yenileme token'larını işlemek, kullanıcıların Spotify hesap
# bilgilerini kaydetmek ve bağlantıyı kesmek için bir servis sınıfı içerir.
#
# =============================================================================
# İÇİNDEKİLER
# =============================================================================
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SPOTIFY KİMLİK DOĞRULAMA SERVİS SINIFI (SpotifyAuthService)
#
#      2.1  TEMEL METOTLAR (CORE METHODS)
#           2.1.1. __init__()
#                  : Başlatıcı metot.
#
#      2.2  OAUTH AKIŞI METOTLARI (OAUTH FLOW METHODS)
#           2.2.1. get_authorization_url(username, client_id)
#                  : Spotify kullanıcı yetkilendirme URL'sini oluşturur.
#           2.2.2. exchange_code_for_token(code, client_id, client_secret)
#                  : Yetkilendirme kodunu token'lar ile değiştirir.
#
#      2.3  TOKEN YÖNETİMİ METOTLARI (TOKEN MANAGEMENT METHODS)
#           2.3.1. get_valid_access_token(username)
#                  : Kullanıcı için geçerli bir erişim token'ı alır (gerekirse yeniler).
#           2.3.2. refresh_access_token(username)
#                  : Süresi dolmuş bir erişim token'ını yeniler.
#
#      2.4  HESAP VE VERİ YÖNETİMİ (ACCOUNT & DATA MANAGEMENT)
#           2.4.1. save_spotify_user_info(username, access_token, refresh_token_to_save)
#                  : Spotify kullanıcı bilgilerini veritabanına kaydeder/günceller.
#           2.4.2. unlink_spotify_account(username)
#                  : Kullanıcının Spotify hesap bağlantısını kaldırır.
#           2.4.3. get_spotify_user_id_from_token(access_token)
#                  : Erişim token'ı kullanarak Spotify kullanıcı ID'sini alır.
#
#      2.5  YARDIMCI METOTLAR (HELPER METHODS)
#           2.5.1. _ensure_datetime_naive(dt)
#                  : Datetime nesnesini zaman dilimi bilgisi olmayan (naive) hale getirir.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import base64
import requests
from datetime import datetime, timedelta
from flask import session
from app.config.spotify_config import SpotifyConfig
from app.database.spotify_user_repository import SpotifyUserRepository
from typing import Optional, Dict, Any, Union

# =============================================================================
# 2.0 SPOTIFY KİMLİK DOĞRULAMA SERVİS SINIFI (SpotifyAuthService)
# =============================================================================
class SpotifyAuthService:
    """
    Spotify OAuth 2.0 kimlik doğrulama akışını yönetir, tokenları işler
    ve kullanıcıların Spotify hesap bilgilerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1 TEMEL METOTLAR (CORE METHODS)
    # -------------------------------------------------------------------------
    def __init__(self):
        """
        2.1.1. SpotifyAuthService sınıfının başlatıcı metodu.
        """
        self.auth_url: str = SpotifyConfig.AUTH_URL
        self.token_url: str = SpotifyConfig.TOKEN_URL
        self.redirect_uri: str = SpotifyConfig.REDIRECT_URI
        self.scopes: str = SpotifyConfig.SCOPES
        self.spotify_repo: SpotifyUserRepository = SpotifyUserRepository()
        self.profile_url: str = SpotifyConfig.PROFILE_URL

    # =========================================================================
    # 2.2 OAUTH AKIŞI METOTLARI (OAUTH FLOW METHODS)
    # =========================================================================
    def get_authorization_url(self, username: str, client_id: Optional[str]) -> str:
        """
        2.2.1. Kullanıcıyı Spotify'da yetkilendirme yapması için yönlendirilecek URL'yi oluşturur.
        """
        if not client_id or not client_id.strip():
            raise ValueError("Spotify Client ID sağlanmadı veya geçersiz.")

        auth_params: Dict[str, str] = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "show_dialog": "true"
        }
        url_args: str = "&".join([f"{key}={requests.utils.quote(str(val))}" for key, val in auth_params.items()])
        return f"{self.auth_url}?{url_args}"

    def exchange_code_for_token(self, code: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        2.2.2. Spotify'dan alınan yetkilendirme kodunu erişim ve yenileme token'larını almak için kullanır.
        """
        try:
            credentials: str = f"{client_id}:{client_secret}"
            base64_credentials: str = base64.b64encode(credentials.encode()).decode()

            payload: Dict[str, str] = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            headers: Dict[str, str] = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()

            token_info: Dict[str, Any] = response.json()
            if 'access_token' in token_info:
                session['spotify_access_token'] = token_info['access_token']
                expires_in = token_info.get('expires_in', 3600)
                session['spotify_token_expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                if 'refresh_token' in token_info:
                    session['spotify_refresh_token'] = token_info['refresh_token']
            
            return token_info
        except requests.exceptions.RequestException:
            return None

    # =========================================================================
    # 2.3 TOKEN YÖNETİMİ METOTLARI (TOKEN MANAGEMENT METHODS)
    # =========================================================================
    def get_valid_access_token(self, username: str) -> Optional[str]:
        """
        2.3.1. Geçerli bir Spotify erişim token'ı döndürür. Gerekirse yeniler.
        """
        access_token: Optional[str] = session.get('spotify_access_token')
        token_expires_at_iso: Optional[str] = session.get('spotify_token_expires_at')

        if access_token and token_expires_at_iso:
            try:
                token_expires_at_dt = self._ensure_datetime_naive(datetime.fromisoformat(token_expires_at_iso))
                now_naive = self._ensure_datetime_naive(datetime.now())

                if token_expires_at_dt and now_naive and (token_expires_at_dt > now_naive + timedelta(minutes=5)):
                    return access_token
            except ValueError:
                pass 
        
        return self.refresh_access_token(username)

    def refresh_access_token(self, username: str) -> Optional[str]:
        """
        2.3.2. Süresi dolmuş bir erişim token'ını yenileme token'ı kullanarak yeniler.
        """
        try:
            spotify_user_data = self.spotify_repo.get_spotify_user_data(username)
            if not spotify_user_data:
                return None

            client_id = spotify_user_data.get('client_id')
            client_secret = spotify_user_data.get('client_secret')
            current_refresh_token = spotify_user_data.get('refresh_token')

            if not all([client_id, client_secret, current_refresh_token]):
                return None

            credentials = f"{client_id}:{client_secret}"
            base64_credentials = base64.b64encode(credentials.encode()).decode()

            payload = {"grant_type": "refresh_token", "refresh_token": current_refresh_token}
            headers = {"Authorization": f"Basic {base64_credentials}", "Content-Type": "application/x-www-form-urlencoded"}

            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()

            new_token_info = response.json()
            new_access_token = new_token_info.get('access_token')

            if not new_access_token:
                return None

            session['spotify_access_token'] = new_access_token
            expires_in = new_token_info.get('expires_in', 3600)
            session['spotify_token_expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            new_refresh_token = new_token_info.get('refresh_token')
            if new_refresh_token and spotify_user_data.get('spotify_user_id'):
                session['spotify_refresh_token'] = new_refresh_token
                self.spotify_repo.spotify_update_user_connection_info(
                    username=username,
                    spotify_user_id=spotify_user_data['spotify_user_id'],
                    refresh_token=new_refresh_token
                )
            return new_access_token
        except requests.exceptions.RequestException:
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires_at', None)
            return None

    # =========================================================================
    # 2.4 HESAP VE VERİ YÖNETİMİ (ACCOUNT & DATA MANAGEMENT)
    # =========================================================================
    def save_spotify_user_info(self, username: str, access_token: str, refresh_token_to_save: Optional[str]) -> Optional[str]:
        """
        2.4.1. Spotify kullanıcı ID'sini alır ve token bilgilerini veritabanına kaydeder/günceller.
        """
        try:
            spotify_user_id = self.get_spotify_user_id_from_token(access_token)
            if not spotify_user_id:
                return None

            final_refresh_token = refresh_token_to_save
            if not final_refresh_token:
                existing_data = self.spotify_repo.get_spotify_user_data(username)
                if existing_data:
                    final_refresh_token = existing_data.get('refresh_token')
            
            if not final_refresh_token:
                return None

            success = self.spotify_repo.spotify_update_user_connection_info(
                username=username,
                spotify_user_id=spotify_user_id,
                refresh_token=final_refresh_token
            )
            if not success:
                return None
            
            session['spotify_refresh_token'] = final_refresh_token
            session['spotify_user_id'] = spotify_user_id
            return spotify_user_id
        except Exception:
            return None

    def unlink_spotify_account(self, username: str) -> bool:
        """
        2.4.2. Kullanıcının Spotify hesap bağlantısını kaldırır (session ve DB'den temizler).
        """
        try:
            session.pop('spotify_access_token', None)
            session.pop('spotify_token_expires_at', None)
            session.pop('spotify_refresh_token', None)
            session.pop('spotify_user_id', None)
            
            return self.spotify_repo.spotify_delete_linked_account_data(username)
        except Exception:
            return False

    def get_spotify_user_id_from_token(self, access_token: str) -> Optional[str]:
        """
        2.4.3. Verilen erişim token'ı ile Spotify kullanıcı ID'sini alır.
        """
        if not access_token:
            return None
        
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(self.profile_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get('id')
        except requests.exceptions.RequestException:
            return None

    # =========================================================================
    # 2.5 YARDIMCI METOTLAR (HELPER METHODS)
    # =========================================================================
    def _ensure_datetime_naive(self, dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """
        2.5.1. Datetime nesnesini veya ISO string'ini naive datetime nesnesine dönüştürür.
        """
        if dt is None:
            return None
        if isinstance(dt, str):
            try:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return None
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            return None

        if dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None:
            return dt_obj.replace(tzinfo=None)
        return dt_obj
