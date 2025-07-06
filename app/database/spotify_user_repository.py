# =============================================================================
# Spotify Kullanıcı Veritabanı Deposu Modülü (Spotify User Repository Module)
# =============================================================================
# Bu modül, kullanıcıların Spotify verileriyle ilgili tüm veritabanı
# işlemlerini yöneten `SpotifyUserRepository` sınıfını içerir. Kullanıcıların
# Spotify API anahtarlarını, token'larını ve bağlantı durumlarını yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SINIF TANIMI: SpotifyUserRepository
#      2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
#           - __init__()
#           - _ensure_connection()
#           - _close_if_owned()
#      2.2. Kullanıcı Verisi Sorgulama (Read Operations)
#           - get_spotify_user_data(username)
#      2.3. Kullanıcı Verisi Yönetimi (Write Operations)
#           - store_client_info(username, client_id, client_secret)
#           - update_user_connection(username, spotify_user_id, refresh_token)
#           - update_refresh_token(username, new_refresh_token)
#           - delete_linked_account(username)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from datetime import datetime
from app.database.db_connection import DatabaseConnection
from app.database.beatify_user_repository import BeatifyUserRepository

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: SpotifyUserRepository
# =============================================================================
class SpotifyUserRepository:
    """
    Kullanıcıların Spotify verilerinin veritabanı işlemlerini yönetir.
    Bu sınıf, Spotify API bilgileri ve token'larının yönetilmesinden sorumludur.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
    # -------------------------------------------------------------------------

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        SpotifyUserRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut bir veritabanı bağlantısı.
                           Eğer sağlanmazsa, yeni bir bağlantı oluşturulur ve yönetilir.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True
        logger.debug("SpotifyUserRepository başlatıldı.")

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

    def get_spotify_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Verilen kullanıcı adına ait Spotify verilerini veritabanından çeker.

        Args:
            username (str): Verileri alınacak kullanıcının adı.

        Returns:
            Kullanıcının Spotify verilerini içeren bir sözlük veya kullanıcı bulunamazsa None.
        """
        self._ensure_connection()
        try:
            query = """
                SELECT username, spotify_user_id, client_id, client_secret,
                       refresh_token, created_at, updated_at
                FROM spotify_users
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            spotify_data = self.db.cursor.fetchone()

            if not spotify_data:
                logger.warning(f"Kullanıcı '{username}' için Spotify verisi bulunamadı.")
                return None

            logger.info(f"Kullanıcı '{username}' için Spotify verisi başarıyla alındı.")
            if isinstance(spotify_data.get('created_at'), datetime):
                spotify_data['created_at'] = spotify_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(spotify_data.get('updated_at'), datetime):
                spotify_data['updated_at'] = spotify_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')

            return spotify_data
        except MySQLError as e:
            logger.error(f"Spotify kullanıcı verisi alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.3. Kullanıcı Verisi Yönetimi (Write Operations)
    # -------------------------------------------------------------------------

    def store_client_info(self, username: str, client_id: str, client_secret: str) -> bool:
        """
        Bir kullanıcı için Spotify client_id ve client_secret bilgilerini kaydeder veya günceller.

        Args:
            username (str): Bilgileri güncellenecek kullanıcı.
            client_id (str): Spotify uygulama Client ID'si.
            client_secret (str): Spotify uygulama Client Secret'ı.

        Returns:
            İşlem başarılı olursa True, aksi takdirde False döner.
        """
        self._ensure_connection()
        try:
            query = """
                INSERT INTO spotify_users (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = VALUES(client_id), client_secret = VALUES(client_secret)
            """
            self.db.cursor.execute(query, (username, client_id, client_secret))
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için Spotify Client bilgileri kaydedildi/güncellendi.")
            return True
        except MySQLError as e:
            logger.error(f"Client bilgileri kaydedilirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_user_connection(self, username: str, spotify_user_id: str, refresh_token: str) -> bool:
        """
        Kullanıcının Spotify hesap bağlantısını kurar ve `beatify_users` tablosundaki durumu günceller.

        Args:
            username (str): Bilgileri güncellenecek kullanıcı.
            spotify_user_id (str): Kullanıcının Spotify ID'si.
            refresh_token (str): Spotify tarafından sağlanan yenileme token'ı.

        Returns:
            İşlem başarılı olursa True, aksi takdirde False döner.
        """
        logger.info(f"[DEBUG] update_user_connection called for user: {username}")
        logger.info(f"[DEBUG] Spotify User ID: {spotify_user_id}")
        logger.info(f"[DEBUG] Refresh token: {refresh_token[:10]}..." if refresh_token else "[DEBUG] No refresh token")
        
        self._ensure_connection()
        try:
            # `spotify_users` tablosunu güncelle
            spotify_query = """
                INSERT INTO spotify_users (username, spotify_user_id, refresh_token)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spotify_user_id = VALUES(spotify_user_id),
                                        refresh_token = VALUES(refresh_token)
            """
            logger.info("[DEBUG] Executing SQL query to update spotify_users table")
            logger.info(f"[DEBUG] Query: {spotify_query}")
            logger.info(f"[DEBUG] Params: username={username}, spotify_user_id={spotify_user_id}, refresh_token={'[HIDDEN]' if refresh_token else 'None'}")
            
            self.db.cursor.execute(spotify_query, (username, spotify_user_id, refresh_token))
            logger.info(f"[DEBUG] Rows affected: {self.db.cursor.rowcount}")

            # `beatify_users` tablosundaki bağlantı durumunu güncelle
            logger.info("[DEBUG] Updating beatify_users table...")
            user_repo = BeatifyUserRepository(db_connection=self.db)
            update_result = user_repo.update_spotify_connection_status(username, True)
            logger.info(f"[DEBUG] Update beatify_users result: {update_result}")

            self.db.connection.commit()
            logger.info("[DEBUG] Database changes committed successfully")
            logger.info(f"[DEBUG] Successfully updated Spotify connection for user: {username}")
            return True
        except MySQLError as e:
            error_msg = f"[ERROR] Database error in update_user_connection (User: {username}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                logger.info("[DEBUG] Rolling back database changes due to error")
                self.db.connection.rollback()
            return False
        except Exception as e:
            error_msg = f"[ERROR] Unexpected error in update_user_connection (User: {username}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                logger.info("[DEBUG] Rolling back database changes due to error")
                self.db.connection.rollback()
            return False
        finally:
            # `_close_if_owned` user_repo'nun işi bittikten sonra çağrılmalı
            logger.info("[DEBUG] Cleaning up database connection")
            self._close_if_owned()

    def update_refresh_token(self, username: str, new_refresh_token: str) -> bool:
        """
        Mevcut bir kullanıcının Spotify yenileme token'ını günceller.

        Args:
            username (str): Token'ı güncellenecek kullanıcı.
            new_refresh_token (str): Yeni yenileme token'ı.

        Returns:
            İşlem başarılı olursa ve en az bir satır etkilenirse True döner.
        """
        self._ensure_connection()
        try:
            query = "UPDATE spotify_users SET refresh_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (new_refresh_token, username))
            self.db.connection.commit()
            if self.db.cursor.rowcount > 0:
                logger.info(f"Kullanıcı '{username}' için refresh token güncellendi.")
                return True
            logger.warning(f"Kullanıcı '{username}' için refresh token güncellenirken etkilenecek satır bulunamadı.")
            return False
        except MySQLError as e:
            logger.error(f"Refresh token güncellenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def delete_linked_account(self, username: str) -> bool:
        """
        Kullanıcının Spotify hesap bağlantısını ve ilgili verilerini kaldırır.

        Args:
            username (str): Bağlantısı kaldırılacak kullanıcı.

        Returns:
            İşlem başarılı olursa True, aksi takdirde False döner.
        """
        self._ensure_connection()
        try:
            # `spotify_users` tablosundaki hassas verileri temizle
            spotify_query = """
                UPDATE spotify_users
                SET spotify_user_id = NULL, refresh_token = NULL
                WHERE username = %s
            """
            self.db.cursor.execute(spotify_query, (username,))

            # `beatify_users` tablosundaki bağlantı durumunu güncelle
            user_repo = BeatifyUserRepository(db_connection=self.db)
            user_repo.update_spotify_connection_status(username, False)

            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için Spotify hesap bağlantısı kaldırıldı.")
            return True
        except MySQLError as e:
            logger.error(f"Spotify bağlantısı kaldırılırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()