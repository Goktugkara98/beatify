# =============================================================================
# Widget Token Servis Modülü (WidgetTokenService)
# =============================================================================
# Bu modül, uygulama içi widget'lar için güvenli token'lar oluşturma,
# doğrulama ve bu token'lardan bilgi çıkarma işlemlerini yöneten bir servis
# sınıfı içerir.
#
# =============================================================================
# İÇİNDEKİLER
# =============================================================================
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  WIDGET TOKEN SERVİS SINIFI (WidgetTokenService)
#
#      2.1  TEMEL METOTLAR (CORE METHODS)
#           2.1.1. __init__()
#                  : Başlatıcı metot.
#
#      2.2  TOKEN OLUŞTURMA VE YÖNETME (TOKEN CREATION & MANAGEMENT)
#           2.2.1. get_or_create_widget_token(username)
#                  : Kullanıcının token'ını alır veya yoksa yenisini oluşturur.
#           2.2.2. get_widget_token(username)
#                  : Kullanıcının mevcut widget token'ını veritabanından alır.
#           2.2.3. generate_and_insert_widget_token(username)
#                  : Yeni bir widget token oluşturur ve veritabanına kaydeder.
#           2.2.4. generate_widget_token(username, length=12)
#                  : Güvenli, rastgele bir widget token string'i üretir.
#
#      2.3  TOKEN DOĞRULAMA VE VERİ ÇIKARMA (TOKEN VALIDATION & DATA EXTRACTION)
#           2.3.1. get_username_from_token(token)
#                  : Geçerli bir token'dan kullanıcı adını çıkarır.
#           2.3.2. get_widget_config_from_token(token)
#                  : Geçerli bir token'dan widget yapılandırma bilgilerini çıkarır.
#           2.3.3. validate_widget_token(token)
#                  : Verilen token'ı veritabanında doğrular ve verisini döndürür.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import secrets
import string
import json
import logging
from typing import Dict, Any, Optional, Tuple
from app.database.spotify_user_repository import SpotifyUserRepository
from app.database.spotify_widget_repository import SpotifyWidgetRepository

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 WIDGET TOKEN SERVİS SINIFI (WidgetTokenService)
# =============================================================================
class WidgetTokenService:
    """
    Widget'lar için güvenli erişim token'ları oluşturma, doğrulama ve
    bu token'lardan bilgi çıkarma işlemlerini yönetir.
    """
    
    # -------------------------------------------------------------------------
    # 2.1 TEMEL METOTLAR (CORE METHODS)
    # -------------------------------------------------------------------------
    def __init__(self):
        """
        2.1.1. WidgetTokenService sınıfının başlatıcı metodu.
        """
        # Gelecekte token geçerlilik süresi gibi ayarlar buraya eklenebilir.
        pass

    # =========================================================================
    # 2.2 TOKEN OLUŞTURMA VE YÖNETME (TOKEN CREATION & MANAGEMENT)
    # =========================================================================
    def get_or_create_widget_token(self, username: str) -> Optional[str]:
        """
        2.2.1. Kullanıcı için mevcut widget token'ını alır veya yoksa yeni bir tane oluşturur.
        """
        existing_token = self.get_widget_token(username)
        if existing_token:
            return existing_token
        return self.generate_and_insert_widget_token(username)

    def get_widget_token(self, username: str) -> Optional[str]:
        """
        2.2.2. Belirtilen kullanıcı için mevcut widget token'ını veritabanından alır.
        """
        db = SpotifyWidgetRepository()
        return db.get_widget_token_by_username(username)

    def generate_and_insert_widget_token(self, username: str) -> Optional[str]:
        """
        2.2.3. Belirtilen kullanıcı için yeni bir widget token'ı oluşturur ve veritabanına kaydeder.
        """
        try:
            token = self.generate_widget_token(username)
            spotify_user_id = SpotifyUserRepository().get_spotify_user_data(username)['spotify_user_id']

            token_data = {
                "beatify_username": username,
                "widget_token": token,
                "widget_name": "Unknown",
                "widget_type": "Unknown",
                "config_data": "{}", # Varsayılan boş JSON
                "spotify_user_id": spotify_user_id
            }
            
            SpotifyWidgetRepository().store_widget_config(token_data)
            return token
        except (KeyError, TypeError):
            # spotify_get_user_data veya sonucu None/hatalı ise
            return None


    def generate_widget_token(self, username: str, length: int = 12) -> str:
        """
        2.2.4. Güvenli, rastgele bir base62 token string'i üretir.
        """
        if not username:
            raise ValueError("Token oluşturmak için kullanıcı adı gereklidir.")
        try:
            alphabet = string.digits + string.ascii_letters
            return ''.join(secrets.choice(alphabet) for _ in range(length))
        except Exception as e:
            raise RuntimeError(f"Token oluşturulamadı: {e}") from e

    # =========================================================================
    # 2.3 TOKEN DOĞRULAMA VE VERİ ÇIKARMA (TOKEN VALIDATION & DATA EXTRACTION)
    # =========================================================================
    def get_username_from_token(self, token: str) -> Optional[str]:
        """
        2.3.1. Geçerli bir widget token'ından kullanıcı adını çıkarır.
        """
        is_valid, payload = self.validate_widget_token(token)
        if is_valid and payload:
            return payload.get('beatify_username') # DB'deki sütun adı
        return None

    def get_widget_config_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        2.3.2. Geçerli bir widget token'ından widget yapılandırma bilgilerini çıkarır.
        """
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            return None
        
        widget_config_str = payload.get('config_data')
        if not widget_config_str:
            return {} # Boş yapılandırma
        
        try:
            return json.loads(widget_config_str)
        except json.JSONDecodeError:
            return None

    def validate_widget_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        2.3.3. Verilen token'ı veritabanında doğrular. Varsa, token ile ilişkili tüm veriyi döndürür.
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
                
            if not token_data.get('beatify_username'):
                logger.error(f"Token geçerli ancak kullanıcı adı eksik: {token}")
                return False, None
                
            logger.info(f"Token başarıyla doğrulandı: {token[:8]}... (Kullanıcı: {token_data['beatify_username']})")
            return True, token_data
            
        except Exception as e:
            logger.error(f"Token doğrulanırken beklenmeyen hata (Token: {token}): {e}", exc_info=True)
            return False, None
