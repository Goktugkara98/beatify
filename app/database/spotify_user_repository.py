# spotify_user_repository.py
# =============================================================================
# Spotify Kullanıcı Repository Modülü
# =============================================================================
# Bu modül, `spotify_users` tablosu ile ilgili genel Spotify kullanıcı
# veritabanı işlemlerini yönetir (widget token ve tasarım hariç).
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SPOTIFY KULLANICI REPOSITORY SINIFI (SPOTIFY USER REPOSITORY CLASS)
#      2.1. SpotifyUserRepository
#           2.1.1.  __init__
#           2.1.2.  _ensure_connection
#           2.1.3.  _close_if_owned
#           2.1.4.  spotify_get_user_data
#           2.1.5.  spotify_insert_or_update_client_info
#           2.1.6.  spotify_update_user_connection_info
#           2.1.7.  spotify_delete_linked_account_data
#           2.1.8.  spotify_update_refresh_token_data
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from datetime import datetime
from app.database.db_connection import DatabaseConnection
# BeatifyUserRepository'ye, is_spotify_connected durumunu güncellemek için ihtiyaç duyulacak.
from app.database.beatify_user_repository import BeatifyUserRepository

# =============================================================================
# 2.0 SPOTIFY KULLANICI REPOSITORY SINIFI (SPOTIFY USER REPOSITORY CLASS)
# =============================================================================
class SpotifyUserRepository:
    """
    Spotify kullanıcı verileri (`spotify_users`) ile ilgili veritabanı işlemlerini yönetir
    (widget token ve tasarım hariç).
    """
    # -------------------------------------------------------------------------
    # 2.1.1. __init__ : Başlatıcı metot.
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
    # 2.1.4. spotify_get_user_data : Bağlı Spotify hesap bilgilerini getirir.
    # -------------------------------------------------------------------------
    def spotify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            # Widget token ve design hariç alanları seçiyoruz.
            query = """
                SELECT username, spotify_user_id, client_id, client_secret,
                       refresh_token, created_at, updated_at
                FROM spotify_users
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            spotify_data = self.db.cursor.fetchone()

            if not spotify_data:
                return None
            
            if isinstance(spotify_data.get('created_at'), datetime):
                spotify_data['created_at'] = spotify_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(spotify_data.get('updated_at'), datetime):
                spotify_data['updated_at'] = spotify_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')

            return spotify_data
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.5. spotify_insert_or_update_client_info : Client ID ve Secret bilgilerini ekler/günceller.
    # -------------------------------------------------------------------------
    def spotify_insert_or_update_client_info(self, username: str, client_id: str, client_secret: str) -> bool:
        self._ensure_connection()
        try:
            # Bu metot, spotify_users tablosunda bir kayıt yoksa oluşturur, varsa günceller.
            # widget_token, design gibi alanlar bu işlemden etkilenmez, varsayılan değerlerini korur
            # veya mevcut değerlerini korur.
            query = """
                INSERT INTO spotify_users (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = VALUES(client_id), client_secret = VALUES(client_secret)
            """
            self.db.cursor.execute(query, (username, client_id, client_secret))
            self.db.connection.commit()
            return True # Etkilenen satır sayısını kontrol etmek daha iyi olabilir (rowcount).
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.6. spotify_update_user_connection_info : Kullanıcının Spotify bağlantı bilgilerini günceller.
    # -------------------------------------------------------------------------
    def spotify_update_user_connection_info(self, username: str, spotify_user_id: str, refresh_token: str) -> bool:
        self._ensure_connection()
        try:
            # Adım 1: spotify_users tablosuna ekleme veya güncelleme
            # spotify_user_id ve refresh_token güncellenir/eklenir.
            # client_id, client_secret, widget_token, design gibi alanlar etkilenmez.
            spotify_query = """
                INSERT INTO spotify_users (username, spotify_user_id, refresh_token)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spotify_user_id = VALUES(spotify_user_id), 
                                        refresh_token = VALUES(refresh_token)
            """
            self.db.cursor.execute(spotify_query, (username, spotify_user_id, refresh_token))

            # Adım 2: beatify_users tablosunda bağlantı durumunu güncelle
            # ÖNEMLİ: Aynı db_connection'ı kullanarak transaction bütünlüğünü koruyoruz.
            user_repo = BeatifyUserRepository(db_connection=self.db)
            user_repo.beatify_update_spotify_connection_status(username, True)
            # user_repo kendi bağlantısını kapatmayacak çünkü dışarıdan verildi.

            self.db.connection.commit()
            return True
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned() # Sadece bu repo kendi bağlantısını oluşturduysa kapatır.

    # -------------------------------------------------------------------------
    # 2.1.7. spotify_delete_linked_account_data : Bağlı Spotify hesap bilgilerini siler/sıfırlar.
    # -------------------------------------------------------------------------
    def spotify_delete_linked_account_data(self, username: str) -> bool:
        self._ensure_connection()
        try:
            # Adım 1: spotify_users tablosundaki ilgili alanları NULL yap
            # Sadece spotify_user_id ve refresh_token sıfırlanır.
            # client_id, client_secret, widget_token, design gibi alanlar korunur.
            # Eğer widget_token da sıfırlanmak isteniyorsa, o zaman SpotifyWidgetRepository'den
            # bir metot çağrılmalı veya bu sorguya widget_token = NULL eklenmeli.
            # Şimdilik sadece temel bağlantı bilgilerini sıfırlıyoruz.
            spotify_query = """
                UPDATE spotify_users
                SET spotify_user_id = NULL, refresh_token = NULL 
                WHERE username = %s 
            """
            # widget_token = NULL, short_token = NULL da eklenebilir eğer isteniyorsa.
            # Bu durumda SpotifyWidgetRepository'deki delete metodu da düşünülmeli.
            # Şimdilik sadece bu repoyu ilgilendiren kısımlar.
            self.db.cursor.execute(spotify_query, (username,))

            # Adım 2: beatify_users tablosunda bağlantı durumunu güncelle
            user_repo = BeatifyUserRepository(db_connection=self.db)
            user_repo.beatify_update_spotify_connection_status(username, False)

            self.db.connection.commit()
            return True # Etkilenen satır kontrolü eklenebilir.
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.8. spotify_update_refresh_token_data : Spotify refresh token'ını günceller.
    # -------------------------------------------------------------------------
    def spotify_update_refresh_token_data(self, username: str, new_refresh_token: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE spotify_users SET refresh_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (new_refresh_token, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# Spotify Kullanıcı Repository Modülü Sonu
# =============================================================================
