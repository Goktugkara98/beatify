# =============================================================================
# Spotify Account Repository Modülü (spotify_account_repository.py)
# =============================================================================
# Bu modül, `spotify_accounts` tablosu üzerindeki işlemleri yürüten
# `SpotifyUserRepository` sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SINIFLAR (CLASSES)
#      2.1. SpotifyUserRepository
#           2.1.1. __init__(db_connection=None)
#           2.1.2. store_client_info(username, client_id, client_secret)
#           2.1.3. update_user_connection(username, spotify_user_id, refresh_token)
#           2.1.4. update_refresh_token(username, new_refresh_token)
#           2.1.5. get_spotify_user_data(username)
#           2.1.6. delete_linked_account(username)
#           2.1.7. _ensure_connection()
#           2.1.8. _close_if_owned()
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
from datetime import datetime
from typing import Any, Dict, Optional

# Üçüncü parti
from mysql.connector import Error as MySQLError

# Uygulama içi
from app.database.db_connection import DatabaseConnection
from app.database.repositories.user_repository import BeatifyUserRepository


# =============================================================================
# 2.0 SINIFLAR (CLASSES)
# =============================================================================

class SpotifyUserRepository:
    """Spotify entegrasyon bilgilerini yöneten repository sınıfı."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """SpotifyUserRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db = DatabaseConnection()
            self.own_connection = True

    def store_client_info(self, username: str, client_id: str, client_secret: str) -> bool:
        """Kullanıcının Spotify Client ID ve Secret bilgilerini kaydeder."""
        self._ensure_connection()
        try:
            query = """
                INSERT INTO spotify_accounts (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = VALUES(client_id), client_secret = VALUES(client_secret)
            """
            self.db.cursor.execute(query, (username, client_id, client_secret))
            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_user_connection(self, username: str, spotify_user_id: str, refresh_token: str) -> bool:
        """Kullanıcının Spotify bağlantı bilgilerini (ID, refresh token) günceller.

        Ayrıca user tablosundaki bağlantı durumunu aktif eder.
        """
        self._ensure_connection()
        try:
            spotify_query = """
                INSERT INTO spotify_accounts (username, spotify_user_id, refresh_token)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spotify_user_id = VALUES(spotify_user_id),
                                        refresh_token = VALUES(refresh_token)
            """
            self.db.cursor.execute(spotify_query, (username, spotify_user_id, refresh_token))

            # Kullanıcı tablosunu güncelle
            user_repo = BeatifyUserRepository(db_connection=self.db)
            user_repo.update_spotify_connection_status(username, True)

            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        except Exception:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_refresh_token(self, username: str, new_refresh_token: str) -> bool:
        """Süresi dolan veya yenilenen refresh token'ı günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE spotify_accounts SET refresh_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (new_refresh_token, username))
            self.db.connection.commit()
            if self.db.cursor.rowcount > 0:
                return True
            return False
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def get_spotify_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcının Spotify hesap verilerini döndürür."""
        self._ensure_connection()
        try:
            query = """
                SELECT username, spotify_user_id, client_id, client_secret,
                       refresh_token, created_at, updated_at
                FROM spotify_accounts
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            spotify_data = self.db.cursor.fetchone()

            if not spotify_data:
                return None

            if isinstance(spotify_data.get("created_at"), datetime):
                spotify_data["created_at"] = spotify_data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(spotify_data.get("updated_at"), datetime):
                spotify_data["updated_at"] = spotify_data["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

            return spotify_data
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def delete_linked_account(self, username: str) -> bool:
        """Spotify bağlantısını kaldırır (verileri siler) ve user tablosunu günceller."""
        self._ensure_connection()
        try:
            spotify_query = """
                UPDATE spotify_accounts
                SET spotify_user_id = NULL, refresh_token = NULL
                WHERE username = %s
            """
            self.db.cursor.execute(spotify_query, (username,))

            user_repo = BeatifyUserRepository(db_connection=self.db)
            user_repo.update_spotify_connection_status(username, False)

            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.2. Dahili yardımcılar (Internal helpers)
    # -------------------------------------------------------------------------

    def _ensure_connection(self) -> None:
        """Veritabanı bağlantısını kontrol eder."""
        self.db.ensure_connection()

    def _close_if_owned(self) -> None:
        """Bağlantıyı bu sınıf oluşturduysa kapatır."""
        if self.own_connection:
            self.db.close()


# =============================================================================
# Spotify Account Repository Modülü Sonu
# =============================================================================
