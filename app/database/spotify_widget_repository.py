# =============================================================================
# Spotify Widget Veritabanı Deposu Modülü (Spotify Widget Repository Module)
# =============================================================================
# Bu modül, Spotify widget'ları ile ilgili tüm veritabanı işlemlerini
# yöneten `SpotifyWidgetRepository` sınıfını içerir. Widget yapılandırmalarını
# saklamak, sorgulamak ve güncellemek için kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SINIF TANIMI: SpotifyWidgetRepository
#      2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
#           - __init__()
#           - _ensure_connection()
#           - _close_if_owned()
#      2.2. Widget Konfigürasyon Sorguları (Read Operations)
#           - get_widget_token_by_username(self, username: str)
#           - get_widget_config_by_token(self, widget_token: str)
#           - get_username_by_widget_token(self, token: str)
#           - get_data_by_widget_token(self, token: str)
#      2.3. Widget Konfigürasyon Yönetimi (Write Operations)
#           - store_widget_config(self, config_data: Dict[str, Any])
#           - update_widget_design_for_user(self, username: str, design: str)
#           - clear_widget_data_for_user()
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
import json
from typing import Optional, Dict, Any
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: SpotifyWidgetRepository
# =============================================================================
class SpotifyWidgetRepository:
    """
    Spotify widget yapılandırmalarının veritabanı işlemlerini yönetir.
    Bu sınıf, widget oluşturma, sorgulama ve güncelleme işlemlerinden sorumludur.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
    # -------------------------------------------------------------------------

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        SpotifyWidgetRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut bir veritabanı bağlantısı.
                           Eğer sağlanmazsa, yeni bir bağlantı oluşturulur ve yönetilir.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self._own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self._own_connection: bool = True
        logger.debug("SpotifyWidgetRepository başlatıldı.")

    def _ensure_connection(self):
        """Veritabanı bağlantısı kapalıysa yeniden kurar."""
        self.db._ensure_connection()

    def _close_if_owned(self):
        """Sınıfın kendisine ait olan veritabanı bağlantısını kapatır."""
        if self._own_connection:
            self.db.close()
            logger.debug("Sahip olunan veritabanı bağlantısı kapatıldı.")

    # -------------------------------------------------------------------------
    # 2.2. Widget Konfigürasyon Sorguları (Read Operations)
    # -------------------------------------------------------------------------

    def get_widget_token_by_username(self, username: str) -> Optional[str]:
        """Kullanıcı adına göre widget token'ını getirir."""
        self._ensure_connection()
        try:
            query = "SELECT widget_token FROM spotify_widget_configs WHERE beatify_username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                logger.info(f"Kullanıcı '{username}' için widget token bulundu.")
                return result.get('widget_token')
            logger.info(f"Kullanıcı '{username}' için widget token bulunamadı.")
            return None
        except MySQLError as e:
            logger.error(f"Widget token alınırken hata oluştu (Kullanıcı: {username}): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_widget_config_by_token(self, widget_token: str) -> Optional[Dict[str, Any]]:
        """Widget token'ına göre tüm widget yapılandırma verilerini getirir."""
        self._ensure_connection()
        try:
            query = "SELECT config_data FROM spotify_widget_configs WHERE widget_token = %s"
            self.db.cursor.execute(query, (widget_token,))
            result = self.db.cursor.fetchone()
        
            if result:
                logger.info(f"Token '{widget_token[:8]}...' için widget yapılandırması bulundu.")
                # JSON string'ini Python sözlüğüne dönüştür
                if isinstance(result.get('config_data'), str):
                    return json.loads(result['config_data'])
                return result.get('config_data')
            else:
                logger.warning(f"Token '{widget_token[:8]}...' için widget yapılandırması bulunamadı.")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON dönüşüm hatası (Token: {widget_token[:8]}...): {e}", exc_info=True)
            return None
        except MySQLError as e:
            logger.error(f"Widget yapılandırması alınırken hata (Token: {widget_token[:8]}...): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_username_by_widget_token(self, token: str) -> Optional[str]:
        """Widget token'ını kullanarak token sahibinin kullanıcı adını bulur."""
        self._ensure_connection()
        try:
            query = "SELECT beatify_username FROM spotify_widget_configs WHERE widget_token = %s"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('beatify_username')
            return None
        except MySQLError as e:
            logger.error(f"Token'dan kullanıcı adı alınırken hata (Token: {token[:8]}...): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()
    
    def get_data_by_widget_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Widget token'ını kullanarak token sahibinin tüm verilerini bulur."""
        self._ensure_connection()
        try:
            query = "SELECT * FROM spotify_widget_configs WHERE widget_token = %s"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                return result
            return None
        except MySQLError as e:
            logger.error(f"Token'dan veri alınırken hata (Token: {token[:8]}...): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.3. Widget Konfigürasyon Yönetimi (Write Operations)
    # -------------------------------------------------------------------------
    
    def store_widget_config(self, config_data: Dict[str, Any]) -> bool:
        """Yeni bir widget yapılandırması kaydeder veya mevcut olanı günceller."""
        self._ensure_connection()
        username = config_data.get("beatify_username", "Bilinmeyen")
        try:
            query = """
            INSERT INTO spotify_widget_configs 
            (beatify_username, widget_token, widget_name, widget_type, config_data, spotify_user_id)
            VALUES (%(beatify_username)s, %(widget_token)s, %(widget_name)s, %(widget_type)s, %(config_data)s, %(spotify_user_id)s)
            ON DUPLICATE KEY UPDATE
                widget_token = VALUES(widget_token),
                widget_name = VALUES(widget_name),
                widget_type = VALUES(widget_type),
                config_data = VALUES(config_data);
            """
            self.db.cursor.execute(query, config_data)
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için widget yapılandırması başarıyla kaydedildi/güncellendi.")
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            logger.error(f"Widget yapılandırması kaydedilirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_widget_design_for_user(self, username: str, design: str) -> bool:
        """Kullanıcının widget tasarım ayarını 'spotify_users' tablosunda günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE spotify_users SET design = %s WHERE username = %s"
            self.db.cursor.execute(query, (design, username))
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için widget tasarımı '{design}' olarak güncellendi.")
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            logger.error(f"Widget tasarımı güncellenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def clear_widget_data_for_user(self, username: str) -> bool:
        """Kullanıcının 'spotify_users' tablosundaki widget ayarlarını temizler."""
        self._ensure_connection()
        try:
            query = "UPDATE spotify_users SET widget_token = NULL, short_token = NULL, design = 'standard' WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için widget verileri temizlendi.")
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            logger.error(f"Widget verileri temizlenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

