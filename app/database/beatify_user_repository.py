# =============================================================================
# Beatify Kullanıcı Veritabanı Deposu Modülü (Beatify User Repository Module)
# =============================================================================
# Bu modül, Beatify kullanıcıları ile ilgili tüm veritabanı işlemlerini
# yöneten `BeatifyUserRepository` sınıfını içerir. Kullanıcı oluşturma,
# sorgulama ve güncelleme işlemlerinden sorumludur.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SINIF TANIMI: BeatifyUserRepository
#      2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
#           - __init__()
#           - _ensure_connection()
#           - _close_if_owned()
#      2.2. Kullanıcı Verisi Sorgulama (Read Operations)
#           - get_user_data(username)
#           - get_user_by_username_or_email(username, email)
#           - get_password_hash(username)
#      2.3. Kullanıcı Verisi Yönetimi (Write Operations)
#           - create_new_user(username, email, password_hash)
#           - update_spotify_connection_status(username, status)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from datetime import datetime
from app.database.db_connection import DatabaseConnection

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: BeatifyUserRepository
# =============================================================================
class BeatifyUserRepository:
    """
    Kullanıcı verilerinin veritabanı işlemlerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
    # -------------------------------------------------------------------------

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        BeatifyUserRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut bir veritabanı bağlantısı.
                           Eğer sağlanmazsa, yeni bir bağlantı oluşturulur.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True
        logger.debug("BeatifyUserRepository başlatıldı.")

    def _ensure_connection(self):
        """Veritabanı bağlantısı kapalıysa yeniden kurar."""
        self.db._ensure_connection()

    def _close_if_owned(self):
        """Sınıfın kendisine ait olan veritabanı bağlantısını kapatır."""
        if self.own_connection:
            self.db.close()
            logger.debug("Sahip olunan veritabanı bağlantısı kapatıldı.")

    # -------------------------------------------------------------------------
    # 2.2. Kullanıcı Verisi Sorgulama (Read Operations)
    # -------------------------------------------------------------------------

    def beatify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı adına göre tüm kullanıcı verilerini getirir."""
        self._ensure_connection()
        try:
            query = """
                SELECT id, username, email, is_spotify_connected, created_at, updated_at
                FROM beatify_users WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            user = self.db.cursor.fetchone()

            if not user:
                logger.warning(f"Kullanıcı '{username}' bulunamadı.")
                return None

            logger.info(f"Kullanıcı '{username}' verisi başarıyla alındı.")
            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(user.get('updated_at'), datetime):
                user['updated_at'] = user['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            return user
        except MySQLError as e:
            logger.error(f"Kullanıcı verisi alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def get_user_by_username_or_email(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı adı veya e-posta adresine göre kullanıcı arar."""
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM beatify_users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user = self.db.cursor.fetchone()
            if user:
                logger.debug(f"Kullanıcı adı '{username}' veya email '{email}' ile eşleşen kayıt bulundu.")
            return user
        except MySQLError as e:
            logger.error(f"Kullanıcı adı/email kontrolü sırasında hata: {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    def beatify_get_password_hash_data(self, username: str) -> Optional[str]:
        """Kullanıcının şifre hash'ini veritabanından alır."""
        self._ensure_connection()
        try:
            query = "SELECT password_hash FROM beatify_users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('password_hash')
            return None
        except MySQLError as e:
            logger.error(f"Şifre hash'i alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.3. Kullanıcı Verisi Yönetimi (Write Operations)
    # -------------------------------------------------------------------------

    def create_new_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """Yeni bir kullanıcıyı veritabanına kaydeder ve yeni ID'yi döndürür."""
        self._ensure_connection()
        try:
            query = "INSERT INTO beatify_users (username, email, password_hash) VALUES (%s, %s, %s)"
            self.db.cursor.execute(query, (username, email, password_hash))
            self.db.connection.commit()
            user_id = self.db.cursor.lastrowid
            logger.info(f"Yeni kullanıcı '{username}' (ID: {user_id}) başarıyla oluşturuldu.")
            return user_id
        except MySQLError as e:
            logger.error(f"Yeni kullanıcı oluşturulurken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return None
        finally:
            self._close_if_owned()

    def update_spotify_connection_status(self, username: str, status: bool) -> bool:
        """Kullanıcının Spotify bağlantı durumunu günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE beatify_users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
            self.db.connection.commit()
            if self.db.cursor.rowcount > 0:
                logger.info(f"Kullanıcı '{username}' için Spotify bağlantı durumu '{status}' olarak güncellendi.")
                return True
            logger.warning(f"Bağlantı durumu güncellenirken kullanıcı '{username}' bulunamadı.")
            return False
        except MySQLError as e:
            logger.error(f"Spotify bağlantı durumu güncellenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
