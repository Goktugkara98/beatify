# beatify_user_repository.py
# =============================================================================
# Beatify Kullanıcı Repository Modülü
# =============================================================================
# Bu modül, `beatify_users` tablosu ile ilgili veritabanı
# işlemlerini (CRUD) yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BEATIFY KULLANICI REPOSITORY SINIFI (BEATIFY USER REPOSITORY CLASS)
#      2.1. BeatifyUserRepository
#           2.1.1.  __init__
#           2.1.2.  _ensure_connection
#           2.1.3.  _close_if_owned
#           2.1.4.  beatify_insert_new_user_data
#           2.1.5.  beatify_get_user_data
#           2.1.6.  beatify_get_username_or_email_data
#           2.1.7.  beatify_get_password_hash_data
#           2.1.8.  beatify_update_spotify_connection_status
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from datetime import datetime
from app.database.db_connection import DatabaseConnection

# =============================================================================
# 2.0 BEATIFY KULLANICI REPOSITORY SINIFI (BEATIFY USER REPOSITORY CLASS)
# =============================================================================
class BeatifyUserRepository:
    """
    Kullanıcı (`beatify_users`) ile ilgili veritabanı işlemlerini yönetir.
    """
    # -------------------------------------------------------------------------
    # 2.1.1. __init__ : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    # -------------------------------------------------------------------------
    # 2.1.2. _ensure_connection : Bağlantıyı kontrol eder.
    # -------------------------------------------------------------------------
    def _ensure_connection(self):
        self.db._ensure_connection()

    # -------------------------------------------------------------------------
    # 2.1.3. _close_if_owned : Sahip olunan bağlantıyı kapatır.
    # -------------------------------------------------------------------------
    def _close_if_owned(self):
        if self.own_connection:
            self.db.close()

    # -------------------------------------------------------------------------
    # 2.1.4. beatify_insert_new_user_data : Yeni bir kullanıcı kaydı ekler.
    # -------------------------------------------------------------------------
    def beatify_insert_new_user_data(self, username: str, email: str, password_hash: str) -> int:
        self._ensure_connection()
        try:
            query = "INSERT INTO beatify_users (username, email, password_hash) VALUES (%s, %s, %s)"
            values = (username, email, password_hash)
            self.db.cursor.execute(query, values)
            self.db.connection.commit()
            user_id = self.db.cursor.lastrowid
            return user_id
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.5. beatify_get_user_data : Kullanıcı verilerini (şifre hariç) getirir.
    # -------------------------------------------------------------------------
    def beatify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = """
                SELECT id, username, email, is_spotify_connected, created_at, updated_at
                FROM beatify_users
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            user_data_row = self.db.cursor.fetchone()

            if not user_data_row:
                return None
            
            if isinstance(user_data_row.get('created_at'), datetime):
                user_data_row['created_at'] = user_data_row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(user_data_row.get('updated_at'), datetime):
                user_data_row['updated_at'] = user_data_row['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return user_data_row
        except MySQLError:
            # Hata durumunda loglama yapılabilir, şimdilik None dönüyoruz.
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.6. beatify_get_username_or_email_data : Kullanıcı adı veya e-posta ile eşleşen kullanıcıyı kontrol eder.
    # -------------------------------------------------------------------------
    def beatify_get_username_or_email_data(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM beatify_users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user_data = self.db.cursor.fetchone()
            return user_data
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.7. beatify_get_password_hash_data : Kullanıcının şifre hash'ini getirir.
    # -------------------------------------------------------------------------
    def beatify_get_password_hash_data(self, username: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = "SELECT password_hash FROM beatify_users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            return result['password_hash'] if result else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.8. beatify_update_spotify_connection_status : Kullanıcının Spotify bağlantı durumunu günceller.
    # -------------------------------------------------------------------------
    def beatify_update_spotify_connection_status(self, username: str, status: bool) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE beatify_users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# Beatify Kullanıcı Repository Modülü Sonu
# =============================================================================
