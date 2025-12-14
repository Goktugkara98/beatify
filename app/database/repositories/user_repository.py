# =============================================================================
# Kullanıcı Repository Modülü (user_repository.py)
# =============================================================================
# Bu modül, `users` tablosu üzerindeki işlemleri yürüten `BeatifyUserRepository`
# sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SINIFLAR (CLASSES)
#      2.1. BeatifyUserRepository
#           2.1.1. __init__(db_connection=None)
#           2.1.2. create_new_user(username, email, password_hash)
#           2.1.3. get_user_details(username)
#           2.1.4. get_user_by_username_or_email(username, email)
#           2.1.5. get_password_hash(username)
#           2.1.6. update_spotify_connection_status(username, status)
#           2.1.7. update_user_email(username, new_email)
#           2.1.8. update_profile_image(username, image_filename)
#           2.1.9. _ensure_connection()
#           2.1.10. _close_if_owned()
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


# =============================================================================
# 2.0 SINIFLAR (CLASSES)
# =============================================================================

class BeatifyUserRepository:
    """Kullanıcı veritabanı işlemlerini yöneten repository sınıfı."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """BeatifyUserRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db = DatabaseConnection()
            self.own_connection = True

    # -------------------------------------------------------------------------
    # 2.1. Kullanıcı CRUD / Query metotları
    # -------------------------------------------------------------------------

    def create_new_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """Yeni bir kullanıcı oluşturur."""
        self._ensure_connection()
        try:
            query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            self.db.cursor.execute(query, (username, email, password_hash))
            self.db.connection.commit()
            return self.db.cursor.lastrowid
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return None
        finally:
            self._close_if_owned()

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı detaylarını (id, username, email, spotify durumu, tarihler) getirir."""
        self._ensure_connection()
        try:
            query = """
                SELECT id, username, email, password_hash, profile_image, is_spotify_connected, created_at, updated_at
                FROM users WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            user = self.db.cursor.fetchone()

            if not user:
                return None

            if isinstance(user.get("created_at"), datetime):
                user["created_at"] = user["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(user.get("updated_at"), datetime):
                user["updated_at"] = user["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_user_by_username_or_email(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı adı veya e-posta adresine göre kullanıcıyı bulur."""
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            return self.db.cursor.fetchone()
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_password_hash(self, username: str) -> Optional[str]:
        """Kullanıcının parola hash'ini getirir."""
        self._ensure_connection()
        try:
            query = "SELECT password_hash FROM users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            return result.get("password_hash") if result else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def update_spotify_connection_status(self, username: str, status: bool) -> bool:
        """Kullanıcının Spotify bağlantı durumunu günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_user_email(self, username: str, new_email: str) -> bool:
        """Kullanıcının e-posta adresini günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE users SET email = %s, updated_at = NOW() WHERE username = %s"
            self.db.cursor.execute(query, (new_email, username))
            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_profile_image(self, username: str, image_filename: str) -> bool:
        """Kullanıcının profil resmi dosya adını günceller."""
        self._ensure_connection()
        try:
            query = "UPDATE users SET profile_image = %s, updated_at = NOW() WHERE username = %s"
            self.db.cursor.execute(query, (image_filename, username))
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
# Kullanıcı Repository Modülü Sonu
# =============================================================================
