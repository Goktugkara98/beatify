"""
Widget Token Servis Modülü (WidgetTokenService)

Uygulama içi widget'lar için güvenli token'lar oluşturma, doğrulama ve bu
token'lardan bilgi çıkarma işlemlerini yöneten servis sınıfını içerir.
"""

import secrets
import string
import json
import logging
from typing import Dict, Any, Optional, Tuple
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.database.repositories.widget_repository import SpotifyWidgetRepository

logger = logging.getLogger(__name__)


class WidgetTokenService:
    """
    Widget'lar için güvenli erişim token'ları oluşturma, doğrulama ve
    bu token'lardan bilgi çıkarma işlemlerini yönetir.
    """

    def __init__(self):
        """
        WidgetTokenService sınıfının başlatıcı metodu.
        Gelecekte token geçerlilik süresi gibi ayarlar buraya eklenebilir.
        """
        pass

    # -------------------------------------------------------------------------
    # TOKEN OLUŞTURMA VE YÖNETME (TOKEN CREATION & MANAGEMENT)
    # -------------------------------------------------------------------------
    def get_or_create_widget_token(self, username: str) -> Optional[str]:
        """Kullanıcı için mevcut widget token'ını alır veya yoksa yeni bir tane oluşturur."""
        existing_token = self.get_widget_token(username)
        if existing_token:
            return existing_token
        return self.generate_and_insert_widget_token(username)

    def get_widget_token(self, username: str) -> Optional[str]:
        """Belirtilen kullanıcı için mevcut widget token'ını veritabanından alır."""
        db = SpotifyWidgetRepository()
        return db.get_widget_token_by_username(username)

    def generate_and_insert_widget_token(self, username: str) -> Optional[str]:
        """Belirtilen kullanıcı için yeni bir widget token'ı oluşturur ve veritabanına kaydeder."""
        try:
            token = self.generate_widget_token(username)
            spotify_user_id = SpotifyUserRepository().get_spotify_user_data(username)["spotify_user_id"]

            token_data = {
                "beatify_username": username,
                "widget_token": token,
                "widget_name": "Unknown",
                "widget_type": "Unknown",
                "config_data": "{}",  # Varsayılan boş JSON
                "spotify_user_id": spotify_user_id,
            }

            SpotifyWidgetRepository().store_widget_config(token_data)
            return token
        except (KeyError, TypeError):
            # spotify_get_user_data veya sonucu None/hatalı ise
            return None

    def generate_widget_token(self, username: str, length: int = 12) -> str:
        """Güvenli, rastgele bir base62 token string'i üretir."""
        if not username:
            raise ValueError("Token oluşturmak için kullanıcı adı gereklidir.")
        try:
            alphabet = string.digits + string.ascii_letters
            return "".join(secrets.choice(alphabet) for _ in range(length))
        except Exception as e:
            raise RuntimeError(f"Token oluşturulamadı: {e}") from e

    # -------------------------------------------------------------------------
    # TOKEN DOĞRULAMA VE VERİ ÇIKARMA (TOKEN VALIDATION & DATA EXTRACTION)
    # -------------------------------------------------------------------------
    def get_username_from_token(self, token: str) -> Optional[str]:
        """Geçerli bir widget token'ından kullanıcı adını çıkarır."""
        is_valid, payload = self.validate_widget_token(token)
        if is_valid and payload:
            return payload.get("beatify_username")  # DB'deki sütun adı
        return None

    def get_widget_config_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Geçerli bir widget token'ından widget yapılandırma bilgilerini çıkarır."""
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            return None

        widget_config_str = payload.get("config_data")
        if not widget_config_str:
            return {}  # Boş yapılandırma

        try:
            return json.loads(widget_config_str)
        except json.JSONDecodeError:
            return None

    def validate_widget_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verilen token'ı veritabanında doğrular. Varsa, token ile ilişkili tüm
        veriyi döndürür.
        """
        if not token:
            logger.warning("Boş token ile doğrulama denemesi yapıldı.")
            return False, None

        try:
            db = SpotifyWidgetRepository()
            token_data = db.get_data_by_widget_token(token)

            if not token_data:
                logger.warning(f"Token bulunamadı: {token}")
                return False, None

            if not token_data.get("beatify_username"):
                logger.error(f"Token geçerli ancak kullanıcı adı eksik: {token}")
                return False, None

            logger.info(
                f"Token başarıyla doğrulandı: {token[:8]}... (Kullanıcı: {token_data['beatify_username']})"
            )
            return True, token_data

        except Exception as e:
            logger.error(f"Token doğrulanırken beklenmeyen hata (Token: {token}): {e}", exc_info=True)
            return False, None


__all__ = ["WidgetTokenService"]

