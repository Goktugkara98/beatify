# spotify_widget_repository.py
# =============================================================================
# Spotify Widget Repository Modülü
# =============================================================================
# Bu modül, `spotify_users` tablosu ile ilgili Spotify widget token
# ve tasarım veritabanı işlemlerini yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SPOTIFY WIDGET REPOSITORY SINIFI (SPOTIFY WIDGET REPOSITORY CLASS)
#      2.1. SpotifyWidgetRepository
#           2.1.1.  __init__
#           2.1.2.  _ensure_connection
#           2.1.3.  _close_if_owned
#           2.1.4.  spotify_store_widget_token_data
#           2.1.5.  spotify_get_widget_token_data
#           2.1.6.  spotify_get_widget_token_by_short_token
#           2.1.7.  spotify_get_username_by_widget_token_data
#           2.1.8.  spotify_update_widget_design
#           2.1.9.  spotify_clear_widget_data (Ek öneri)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional
from app.database.db_connection import DatabaseConnection

# =============================================================================
# 2.0 SPOTIFY WIDGET REPOSITORY SINIFI (SPOTIFY WIDGET REPOSITORY CLASS)
# =============================================================================
class SpotifyWidgetRepository:
    """
    Spotify widget token ve tasarım (`spotify_users` tablosu) ile ilgili
    veritabanı işlemlerini yönetir.
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
    # 2.1.4. spotify_store_widget_token : Spotify widget token'ını saklar/günceller.
    # -------------------------------------------------------------------------
    def spotify_store_widget_token(self, username: str, token: str) -> bool:
        self._ensure_connection()
        try:
            # Bu metot, kullanıcı için spotify_users tablosunda bir kayıt olduğunu varsayar.
            # Eğer kayıt yoksa, INSERT ... ON DUPLICATE KEY UPDATE kullanılmalı
            # veya SpotifyUserRepository.spotify_insert_or_update_client_info gibi bir metot
            # öncelikle çağrılmalıdır.
            # Şimdilik, var olan bir kaydı güncellediğini varsayıyoruz.
            query = "UPDATE spotify_users SET widget_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (token, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.5. spotify_get_widget_token : Spotify widget token'ını getirir.
    # -------------------------------------------------------------------------
    def spotify_get_widget_token(self, username: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = "SELECT widget_token FROM spotify_users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            return result['widget_token'] if result and result['widget_token'] else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()
            
    # -------------------------------------------------------------------------
    # 2.1.6. spotify_get_widget_token_by_short_token : Kısa token ile tam widget token'ını getirir.
    # -------------------------------------------------------------------------
    def spotify_get_widget_token_by_short_token(self, short_token: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = "SELECT widget_token FROM spotify_users WHERE short_token = %s"
            self.db.cursor.execute(query, (short_token,))
            result = self.db.cursor.fetchone()
            return result['widget_token'] if result and result['widget_token'] else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.7. spotify_get_username_by_widget_token_data : Widget token'ına sahip kullanıcının adını getirir.
    # Bu metot, widget_token'ın benzersiz olduğunu varsayar. Eğer değilse, birden fazla sonuç dönebilir.
    # Tablo tanımında widget_token UNIQUE değil, bu yüzden dikkatli olunmalı.
    # Genellikle bu tür bir arama short_token üzerinden yapılır ki o da UNIQUE olmalı (veya indexli).
    # -------------------------------------------------------------------------
    def spotify_get_username_by_widget_token_data(self, token: str) -> Optional[str]:
        self._ensure_connection()
        try:
            # widget_token TEXT olduğu için tam eşleşme yavaş olabilir.
            # Eğer bu sık kullanılacaksa, widget_token'ın bir hash'i veya kısa bir versiyonu
            # üzerinden arama yapmak daha performanslı olabilir.
            query = "SELECT username FROM spotify_users WHERE widget_token = %s"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone() # İlk eşleşeni alır
            return result['username'] if result else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.8. spotify_update_widget_design : Kullanıcının Spotify widget tasarım tercihini günceller.
    # -------------------------------------------------------------------------
    def spotify_update_widget_design(self, username: str, design: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE spotify_users SET design = %s WHERE username = %s"
            self.db.cursor.execute(query, (design, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.9. spotify_clear_widget_data (Ek Öneri) : Kullanıcının widget verilerini temizler.
    # -------------------------------------------------------------------------
    def spotify_clear_widget_data(self, username: str) -> bool:
        """Kullanıcının widget_token, short_token ve design bilgilerini sıfırlar."""
        self._ensure_connection()
        try:
            query = """
                UPDATE spotify_users 
                SET widget_token = NULL, short_token = NULL, design = 'standard' 
                WHERE username = %s
            """
            # design'ı varsayılan bir değere ('standard' gibi) ayarlamak mantıklı olabilir.
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# Spotify Widget Repository Modülü Sonu
# =============================================================================
