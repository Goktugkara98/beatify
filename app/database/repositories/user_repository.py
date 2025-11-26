"""
MODÜL: user_repository.py

Bu modül, `users` tablosu üzerindeki işlemleri yürüten
`BeatifyUserRepository` sınıfını içerir.

İÇİNDEKİLER:
    - BeatifyUserRepository (Sınıf): Kullanıcı işlemlerini yönetir.
        - __init__: Sınıfı başlatır.
        - create_new_user: Yeni kullanıcı oluşturur.
        - get_user_details: Kullanıcı detaylarını getirir.
        - get_user_by_username_or_email: Kullanıcı adı veya e-posta ile kullanıcı arar.
        - get_password_hash: Kullanıcının parola hash'ini getirir.
        - update_spotify_connection_status: Spotify bağlantı durumunu günceller.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


class BeatifyUserRepository:
    """
    Kullanıcı veritabanı işlemlerini yöneten repository sınıfı.
    """

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """
        BeatifyUserRepository sınıfını başlatır.

        Args:
            db_connection (Optional[DatabaseConnection]): Mevcut veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    def create_new_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """
        Yeni bir kullanıcı oluşturur.
        """
        self._ensure_connection()
        try:
            query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            self.db.cursor.execute(query, (username, email, password_hash))
            self.db.connection.commit()
            user_id = self.db.cursor.lastrowid
            return user_id
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return None
        finally:
            self._close_if_owned()

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı detaylarını (id, username, email, spotify durumu, tarihler) getirir.
        Eski ad: beatify_get_user_data
        """
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

            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(user.get('updated_at'), datetime):
                user['updated_at'] = user['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_user_by_username_or_email(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı adı veya e-posta adresine göre kullanıcıyı bulur.
        Kayıt işlemi sırasında çakışma kontrolü için kullanılır.
        """
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user = self.db.cursor.fetchone()
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_password_hash(self, username: str) -> Optional[str]:
        """
        Kullanıcının parola hash'ini getirir.
        Eski ad: beatify_get_password_hash_data
        """
        self._ensure_connection()
        try:
            query = "SELECT password_hash FROM users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('password_hash')
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def update_spotify_connection_status(self, username: str, status: bool) -> bool:
        """
        Kullanıcının Spotify bağlantı durumunu günceller.
        """
        self._ensure_connection()
        try:
            query = "UPDATE users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
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

    def update_user_email(self, username: str, new_email: str) -> bool:
        """
        Kullanıcının e-posta adresini günceller.
        """
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
        """
        Kullanıcının profil resmi dosya adını günceller.
        """
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

    def _ensure_connection(self) -> None:
        """Veritabanı bağlantısını kontrol eder."""
        self.db.ensure_connection()

    def _close_if_owned(self) -> None:
        """Bağlantıyı bu sınıf oluşturduysa kapatır."""
        if self.own_connection:
            self.db.close()
