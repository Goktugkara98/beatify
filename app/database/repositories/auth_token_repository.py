"""
MODÜL: auth_token_repository.py

Bu modül, `auth_tokens` tablosu üzerindeki işlemleri yürüten
`BeatifyTokenRepository` sınıfını içerir.

İÇİNDEKİLER:
    - BeatifyTokenRepository (Sınıf): Token doğrulama, saklama ve geçersiz kılma işlemlerini yönetir.
        - __init__: Sınıfı başlatır.
        - store_auth_token: Yeni bir token kaydeder.
        - validate_auth_token: Token'ın geçerliliğini kontrol eder.
        - deactivate_auth_token: Belirli bir token'ı geçersiz kılar.
        - deactivate_all_user_tokens: Kullanıcının tüm tokenlarını geçersiz kılar.
"""

from typing import Optional
from datetime import datetime
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


class BeatifyTokenRepository:
    """
    Kullanıcı kimlik doğrulama token'larını yöneten repository sınıfı.
    """

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """
        BeatifyTokenRepository sınıfını başlatır.

        Args:
            db_connection (Optional[DatabaseConnection]): Mevcut veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    def store_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        """
        Yeni bir kimlik doğrulama token'ını veritabanına kaydeder.
        """
        self._ensure_connection()
        try:
            query = "INSERT INTO auth_tokens (username, token, expires_at) VALUES (%s, %s, %s)"
            expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
            self.db.cursor.execute(query, (username, token, expires_at_str))
            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def validate_auth_token(self, token: str) -> Optional[str]:
        """
        Verilen token'ın geçerli olup olmadığını kontrol eder.
        Geçerliyse kullanıcı adını döndürür.
        """
        self._ensure_connection()
        try:
            query = """
                SELECT username FROM auth_tokens
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
            """
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()

            if result:
                return result.get('username')

            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def deactivate_auth_token(self, username: str, token: str) -> bool:
        """
        Belirli bir kullanıcının belirli bir token'ını geçersiz kılar (logout).
        """
        self._ensure_connection()
        try:
            query = "UPDATE auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (token, username))
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

    def deactivate_all_user_tokens(self, username: str) -> bool:
        """
        Bir kullanıcının tüm aktif token'larını geçersiz kılar (tüm cihazlardan çıkış).
        """
        self._ensure_connection()
        try:
            query = "UPDATE auth_tokens SET expired_at = NOW() WHERE username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
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
