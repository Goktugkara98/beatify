# beatify_token_repository.py
# =============================================================================
# Beatify Kimlik Doğrulama Token Repository Modülü
# =============================================================================
# Bu modül, `beatify_auth_tokens` tablosu ile ilgili veritabanı
# işlemlerini (CRUD) yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BEATIFY TOKEN REPOSITORY SINIFI (BEATIFY TOKEN REPOSITORY CLASS)
#      2.1. BeatifyTokenRepository
#           2.1.1.  __init__
#           2.1.2.  _ensure_connection
#           2.1.3.  _close_if_owned
#           2.1.4.  beatify_insert_or_update_auth_token
#           2.1.5.  beatify_validate_auth_token
#           2.1.6.  beatify_deactivate_auth_token
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional
from datetime import datetime
from app.database.db_connection import DatabaseConnection

# =============================================================================
# 2.0 BEATIFY TOKEN REPOSITORY SINIFI (BEATIFY TOKEN REPOSITORY CLASS)
# =============================================================================
class BeatifyTokenRepository:
    """
    Kimlik doğrulama token'ları (`beatify_auth_tokens`) ile ilgili veritabanı işlemlerini yönetir.
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
    # 2.1.4. beatify_insert_or_update_auth_token : Kimlik doğrulama token'ı ekler veya günceller.
    # -------------------------------------------------------------------------
    def beatify_insert_or_update_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        self._ensure_connection()
        expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
        try:
            # Basit insert. Eğer bir kullanıcıya yeni token verilirken eski token'ı güncellemek
            # veya kullanıcı başına tek aktif token sağlamak isteniyorsa, bu mantık servis katmanında
            # veya daha karmaşık bir SQL sorgusu ile (örn: username üzerinde UNIQUE constraint ve ON DUPLICATE KEY UPDATE)
            # yönetilmelidir. Mevcut tabloda token UNIQUE.
            query = """
            INSERT INTO beatify_auth_tokens (username, token, expires_at)
            VALUES (%s, %s, %s)
            """
            # Eğer aynı token değeriyle bir kayıt varsa (çok düşük ihtimal) MySQLError: Duplicate entry fırlatır.
            # Eğer aynı kullanıcı için farklı tokenlar eklenecekse bu sorgu uygundur.
            # Eğer bir kullanıcı için sadece bir aktif token olmalıysa, önce deactivate_all_user_tokens(username)
            # çağrılabilir, ardından bu metot çağrılabilir.
            self.db.cursor.execute(query, (username, token, expires_at_str))
            self.db.connection.commit()
            return True
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.5. beatify_validate_auth_token : Verilen token'ın geçerliliğini doğrular.
    # -------------------------------------------------------------------------
    def beatify_validate_auth_token(self, token: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = """
                SELECT username
                FROM beatify_auth_tokens
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
            """
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            return result['username'] if result else None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.1.6. beatify_deactivate_auth_token : Belirli bir kullanıcıya ait token'ı geçersiz kılar.
    # -------------------------------------------------------------------------
    def beatify_deactivate_auth_token(self, username: str, token: str) -> bool:
        self._ensure_connection()
        try:
            # Sadece belirtilen token'ı ve kullanıcıyı eşleştirerek devre dışı bırakır.
            query = "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s AND expired_at IS NULL"
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
    # Ek Metot Önerisi: Bir kullanıcıya ait tüm aktif tokenları devre dışı bırakmak için.
    # Bu, yeni bir token oluşturulmadan önce çağrılabilir.
    # -------------------------------------------------------------------------
    def beatify_deactivate_all_user_tokens(self, username: str) -> bool:
        """Bir kullanıcıya ait tüm aktif tokenları geçersiz kılar."""
        self._ensure_connection()
        try:
            query = "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0 # Kaç token'ın etkilendiğini dönebilir.
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()
# =============================================================================
# Beatify Kimlik Doğrulama Token Repository Modülü Sonu
# =============================================================================
