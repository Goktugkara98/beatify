"""
MODÜL: widget_repository.py

Bu modül, `widgets` tablosu üzerindeki işlemleri yürüten
`SpotifyWidgetRepository` sınıfını içerir.

İÇİNDEKİLER:
    - SpotifyWidgetRepository (Sınıf): Widget konfigürasyonlarını yönetir.
        - __init__: Sınıfı başlatır.
        - store_widget_config: Widget ayarlarını kaydeder veya günceller.
        - get_widgets_by_username: Kullanıcının tüm widget'larını getirir.
        - get_widget_config_by_token: Token ile widget ayarlarını getirir.
        - get_widget_token_by_username: Kullanıcının widget token'ını getirir.
        - get_username_by_widget_token: Widget token'dan kullanıcı adını bulur.
        - get_data_by_widget_token: Widget'ın tüm verilerini getirir.
        - update_widget_design_for_user: Widget tasarımını günceller.
        - clear_widget_data_for_user: Kullanıcının widget verilerini temizler.
"""

import json
import logging
from typing import Optional, Dict, Any
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SpotifyWidgetRepository:
    """
    Spotify widget konfigürasyonlarını yöneten repository sınıfı.
    """

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """
        SpotifyWidgetRepository sınıfını başlatır.

        Args:
            db_connection (Optional[DatabaseConnection]): Mevcut veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self._own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self._own_connection: bool = True

    def store_widget_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Widget konfigürasyonunu veritabanına kaydeder.
        """
        self._ensure_connection()
        try:
            logger.debug(
                "store_widget_config(): veritabanına yazılıyor: username='%s', token='%s', widget_name='%s', widget_type='%s'",
                config_data.get("beatify_username"),
                config_data.get("widget_token"),
                config_data.get("widget_name"),
                config_data.get("widget_type"),
            )
            query = """
            INSERT INTO widgets 
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
            success = self.db.cursor.rowcount > 0
            logger.info(
                "store_widget_config(): işlem tamamlandı. success=%s, rowcount=%s",
                success,
                self.db.cursor.rowcount,
            )
            return success
        except MySQLError as e:
            logger.error("store_widget_config(): MySQLError: %s", e, exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def get_widgets_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Belirtilen kullanıcı için tüm Spotify widget'larını döndürür.
        """
        self._ensure_connection()
        try:
            logger.debug("get_widgets_by_username(): username='%s'", username)
            query = """
                SELECT *
                FROM widgets
                WHERE beatify_username = %s AND platform = 'spotify'
                ORDER BY created_at DESC
            """
            self.db.cursor.execute(query, (username,))
            results = self.db.cursor.fetchall()
            logger.debug(
                "get_widgets_by_username(): username='%s', bulunan_widget_sayisi=%s",
                username,
                len(results or []),
            )
            return results or []
        except MySQLError as e:
            logger.error("get_widgets_by_username(): MySQLError: %s", e, exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_widget_config_by_token(self, widget_token: str) -> Optional[Dict[str, Any]]:
        """
        Widget token'ına göre widget konfigürasyon verisini döndürür.
        """
        self._ensure_connection()
        try:
            logger.debug("get_widget_config_by_token(): token='%s'", widget_token)
            query = "SELECT config_data FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (widget_token,))
            result = self.db.cursor.fetchone()

            if result:
                logger.debug("get_widget_config_by_token(): ham config_data alındı, tip=%s", type(result.get("config_data")))
                if isinstance(result.get('config_data'), str):
                    parsed = json.loads(result['config_data'])
                    logger.debug("get_widget_config_by_token(): JSON parse başarılı, anahtarlar=%s", list(parsed.keys()))
                    return parsed
                logger.debug("get_widget_config_by_token(): dict config_data döndürüldü")
                return result.get('config_data')
            else:
                logger.warning("get_widget_config_by_token(): token bulunamadı veya platform=spotify değil: token='%s'", widget_token)
                return None
        except json.JSONDecodeError as e:
            logger.error("get_widget_config_by_token(): JSONDecodeError: %s", e, exc_info=True)
            return None
        except MySQLError as e:
            logger.error("get_widget_config_by_token(): MySQLError: %s", e, exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_widget_token_by_username(self, username: str) -> Optional[str]:
        """
        Kullanıcı adına göre widget token'ını döndürür.
        """
        self._ensure_connection()
        try:
            logger.debug("get_widget_token_by_username(): username='%s'", username)
            query = """
                SELECT widget_token
                FROM widgets
                WHERE beatify_username = %s AND platform = 'spotify'
            """
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                token = result.get('widget_token')
                logger.debug("get_widget_token_by_username(): username='%s', token='%s'", username, token)
                return token
            logger.debug("get_widget_token_by_username(): username='%s', token bulunamadı", username)
            return None
        except MySQLError as e:
            logger.error("get_widget_token_by_username(): MySQLError: %s", e, exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_username_by_widget_token(self, token: str) -> Optional[str]:
        """
        Widget token'ına göre kullanıcı adını döndürür.
        """
        self._ensure_connection()
        try:
            query = "SELECT beatify_username FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('beatify_username')
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_data_by_widget_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Widget token'ına göre tüm widget satır verisini döndürür.
        """
        self._ensure_connection()
        try:
            logger.debug("get_data_by_widget_token(): token='%s'", token)
            query = "SELECT * FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                logger.debug(
                    "get_data_by_widget_token(): token='%s' için kayıt bulundu. beatify_username='%s'",
                    token,
                    result.get("beatify_username"),
                )
                return result
            logger.warning("get_data_by_widget_token(): token bulunamadı veya platform=spotify değil: token='%s'", token)
            return None
        except MySQLError as e:
            logger.error("get_data_by_widget_token(): MySQLError: %s", e, exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def update_widget_design_for_user(self, username: str, design: str) -> bool:
        """
        Kullanıcının widget tasarım tercihini günceller.
        (Not: Bu metod şu an spotify_accounts tablosunu güncelliyor gibi görünüyor,
         ancak widget repository içinde. Tasarım bilgisi neredeyse orayı güncellemeli.)
        """
        self._ensure_connection()
        try:
            query = "UPDATE spotify_accounts SET design = %s WHERE username = %s"
            self.db.cursor.execute(query, (design, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def clear_widget_data_for_user(self, username: str) -> bool:
        """
        Kullanıcının widget verilerini temizler.
        """
        self._ensure_connection()
        try:
            query = "UPDATE spotify_accounts SET widget_token = NULL, short_token = NULL, design = 'standard' WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    # ---------------------------------------------------------------------
    # DEBUG / YARDIMCI METOTLAR
    # ---------------------------------------------------------------------
    def debug_get_all_widgets(self) -> list[Dict[str, Any]]:
        """
        DEBUG AMAÇLI:
        widgets tablosundaki TÜM satırları (platform filtresi olmadan) döndürür.
        """
        self._ensure_connection()
        try:
            logger.debug("debug_get_all_widgets(): widgets tablosundaki tüm satırlar isteniyor")
            query = "SELECT * FROM widgets"
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall() or []
            logger.debug("debug_get_all_widgets(): toplam %s satır bulundu", len(results))
            return results
        except MySQLError as e:
            logger.error("debug_get_all_widgets(): MySQLError: %s", e, exc_info=True)
            return []
        finally:
            self._close_if_owned()

    def _ensure_connection(self) -> None:
        """Veritabanı bağlantısını kontrol eder."""
        self.db.ensure_connection()

    def _close_if_owned(self) -> None:
        """Bağlantıyı bu sınıf oluşturduysa kapatır."""
        if self._own_connection:
            self.db.close()
