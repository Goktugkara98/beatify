"""
Spotify Kimlik Doğrulama Servis Modülü (SpotifyAuthService)

Spotify OAuth 2.0 kimlik doğrulama akışını yönetmek, erişim ve yenileme
token'larını işlemek, kullanıcıların Spotify hesap bilgilerini kaydetmek
ve bağlantıyı kesmek için servis sınıfı içerir.
"""

import base64
import json
import logging
import os
import requests
from datetime import datetime, timedelta
from flask import session
from app.config.spotify_config import SpotifyConfig
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from typing import Optional, Dict, Any, Union


class SpotifyAuthService:
    """
    Spotify OAuth 2.0 kimlik doğrulama akışını yönetir, tokenları işler
    ve kullanıcıların Spotify hesap bilgilerini yönetir.
    """

    def __init__(self):
        """
        SpotifyAuthService sınıfının başlatıcı metodu.
        """
        self.auth_url: str = SpotifyConfig.AUTH_URL
        self.token_url: str = SpotifyConfig.TOKEN_URL
        self.redirect_uri: str = SpotifyConfig.REDIRECT_URI
        self.scopes: str = SpotifyConfig.SCOPES
        self.spotify_repo: SpotifyUserRepository = SpotifyUserRepository()
        self.profile_url: str = SpotifyConfig.PROFILE_URL

    # -------------------------------------------------------------------------
    # OAUTH AKIŞI METOTLARI (OAUTH FLOW METHODS)
    # -------------------------------------------------------------------------
    def get_authorization_url(self, username: str, client_id: Optional[str]) -> str:
        """
        Kullanıcıyı Spotify'da yetkilendirme yapması için yönlendirilecek URL'yi oluşturur.
        """
        if not client_id or not client_id.strip():
            raise ValueError("Spotify Client ID sağlanmadı veya geçersiz.")

        auth_params: Dict[str, str] = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "show_dialog": "true",
        }
        url_args: str = "&".join([f"{key}={requests.utils.quote(str(val))}" for key, val in auth_params.items()])
        return f"{self.auth_url}?{url_args}"

    def exchange_code_for_token(self, code: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        Spotify'dan alınan yetkilendirme kodunu erişim ve yenileme token'larını almak için kullanır.
        """
        try:
            credentials: str = f"{client_id}:{client_secret}"
            base64_credentials: str = base64.b64encode(credentials.encode()).decode()

            payload: Dict[str, str] = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            }
            headers: Dict[str, str] = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()

            token_info: Dict[str, Any] = response.json()
            if "access_token" in token_info:
                session["spotify_access_token"] = token_info["access_token"]
                expires_in = token_info.get("expires_in", 3600)
                session["spotify_token_expires_at"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                if "refresh_token" in token_info:
                    session["spotify_refresh_token"] = token_info["refresh_token"]

            return token_info
        except requests.exceptions.RequestException:
            return None

    # -------------------------------------------------------------------------
    # TOKEN YÖNETİMİ METOTLARI (TOKEN MANAGEMENT METHODS)
    # -------------------------------------------------------------------------
    def get_valid_access_token(self, username: str) -> Optional[str]:
        """
        Geçerli bir Spotify erişim token'ı döndürür. Gerekirse yeniler.
        """
        access_token: Optional[str] = session.get("spotify_access_token")
        token_expires_at_iso: Optional[str] = session.get("spotify_token_expires_at")

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
        Süresi dolmuş bir erişim token'ını yenileme token'ı kullanarak yeniler.
        """
        try:
            spotify_user_data = self.spotify_repo.get_spotify_user_data(username)
            if not spotify_user_data:
                return None

            client_id = spotify_user_data.get("client_id")
            client_secret = spotify_user_data.get("client_secret")
            current_refresh_token = spotify_user_data.get("refresh_token")

            if not all([client_id, client_secret, current_refresh_token]):
                return None

            credentials = f"{client_id}:{client_secret}"
            base64_credentials = base64.b64encode(credentials.encode()).decode()

            payload = {"grant_type": "refresh_token", "refresh_token": current_refresh_token}
            headers = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()

            new_token_info = response.json()
            new_access_token = new_token_info.get("access_token")

            if not new_access_token:
                return None

            session["spotify_access_token"] = new_access_token
            expires_in = new_token_info.get("expires_in", 3600)
            session["spotify_token_expires_at"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            new_refresh_token = new_token_info.get("refresh_token")
            if new_refresh_token and spotify_user_data.get("spotify_user_id"):
                session["spotify_refresh_token"] = new_refresh_token
                self.spotify_repo.update_user_connection(
                    username=username,
                    spotify_user_id=spotify_user_data["spotify_user_id"],
                    refresh_token=new_refresh_token,
                )
            return new_access_token
        except requests.exceptions.RequestException:
            session.pop("spotify_access_token", None)
            session.pop("spotify_token_expires_at", None)
            return None

    # -------------------------------------------------------------------------
    # HESAP VE VERİ YÖNETİMİ (ACCOUNT & DATA MANAGEMENT)
    # -------------------------------------------------------------------------
    def save_spotify_user_info(
        self,
        username: str,
        access_token: str,
        refresh_token_to_save: Optional[str],
    ) -> Optional[str]:
        """
        Spotify kullanıcı ID'sini alır ve token bilgilerini veritabanına kaydeder/günceller.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] save_spotify_user_info called for user: {username}")
        logger.info(f"[DEBUG] Access token: {'Exists' if access_token else 'Missing'}")
        logger.info(f"[DEBUG] Refresh token provided: {'Yes' if refresh_token_to_save else 'No'}")

        try:
            logger.info("[DEBUG] Getting Spotify user ID from token...")
            spotify_user_id = self.get_spotify_user_id_from_token(access_token)
            logger.info(f"[DEBUG] Spotify user ID: {spotify_user_id}")

            if not spotify_user_id:
                logger.error("[DEBUG] Failed to get Spotify user ID from token")
                return None

            final_refresh_token = refresh_token_to_save
            if not final_refresh_token:
                logger.info("[DEBUG] No refresh token provided, checking existing data...")
                existing_data = self.spotify_repo.get_spotify_user_data(username)
                if existing_data:
                    final_refresh_token = existing_data.get("refresh_token")
                    logger.info(f"[DEBUG] Found existing refresh token: {bool(final_refresh_token)}")

            if not final_refresh_token:
                logger.error("[DEBUG] No refresh token available")
                return None

            logger.info("[DEBUG] Updating user connection in database...")
            logger.info(f"[DEBUG] Username: {username}")
            logger.info(f"[DEBUG] Spotify User ID: {spotify_user_id}")
            logger.info(
                f"[DEBUG] Using refresh token: {final_refresh_token[:10]}..."
                if final_refresh_token
                else "[DEBUG] No refresh token"
            )

            success = self.spotify_repo.update_user_connection(
                username=username,
                spotify_user_id=spotify_user_id,
                refresh_token=final_refresh_token,
            )

            logger.info(f"[DEBUG] Update user connection result: {success}")

            if not success:
                logger.error("[DEBUG] Failed to update user connection in database")
                return None

            logger.info("[DEBUG] Updating session data...")
            session["spotify_refresh_token"] = final_refresh_token
            session["spotify_user_id"] = spotify_user_id
            logger.info("[DEBUG] Session data updated successfully")

            return spotify_user_id
        except Exception as e:
            logger.error(f"[DEBUG] Error in save_spotify_user_info: {str(e)}", exc_info=True)
            return None

    def unlink_spotify_account(self, username: str) -> bool:
        """
        Kullanıcının Spotify hesap bağlantısını kaldırır (session ve DB'den temizler).
        """
        try:
            session.pop("spotify_access_token", None)
            session.pop("spotify_token_expires_at", None)
            session.pop("spotify_refresh_token", None)
            session.pop("spotify_user_id", None)

            return self.spotify_repo.delete_linked_account(username)
        except Exception:
            return False

    def get_spotify_user_id_from_token(self, access_token: str) -> Optional[str]:
        """
        Verilen erişim token'ı ile Spotify kullanıcı ID'sini alır.
        """
        if not access_token:
            return None

        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(self.profile_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("id")
        except requests.exceptions.RequestException:
            return None

    # -------------------------------------------------------------------------
    # Yardımcı metotlar
    # -------------------------------------------------------------------------
    def _ensure_datetime_naive(self, dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """
        Datetime nesnesini veya ISO string'ini naive datetime nesnesine dönüştürür.
        """
        if dt is None:
            return None
        if isinstance(dt, str):
            try:
                dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except ValueError:
                return None
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            return None

        if dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None:
            return dt_obj.replace(tzinfo=None)
        return dt_obj


__all__ = ["SpotifyAuthService"]

