# =============================================================================
# Beatify Token Veritabanı Deposu Modülü (Beatify Token Repository Module)
# =============================================================================
# Bu modül, kullanıcı kimlik doğrulama token'ları ile ilgili tüm veritabanı
# işlemlerini yöneten `BeatifyTokenRepository` sınıfını içerir. Token
# oluşturma, doğrulama ve geçersiz kılma işlemlerinden sorumludur.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli kütüphaneler ve modüller.
#
# 2.0  SINIF TANIMI: BeatifyTokenRepository
#      : Token veritabanı işlemlerini yürüten ana sınıf.
#      2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
#           - __init__()
#           - _ensure_connection()
#           - _close_if_owned()
#      2.2. Token Sorgulama (Read Operations)
#           - validate_auth_token(token)
#      2.3. Token Yönetimi (Write Operations)
#           - store_auth_token(username, token, expires_at)
#           - deactivate_auth_token(username, token)
#           - deactivate_all_user_tokens(username)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from mysql.connector import Error as MySQLError
from typing import Optional
from datetime import datetime
from app.database.db_connection import DatabaseConnection

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: BeatifyTokenRepository
# =============================================================================
class BeatifyTokenRepository:
    """
    Kullanıcı kimlik doğrulama token'larının veritabanı işlemlerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
    # -------------------------------------------------------------------------

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        BeatifyTokenRepository sınıfını başlatır.
        Eğer bir veritabanı bağlantısı sağlanmazsa, kendi bağlantısını oluşturur
        ve yönetir.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True
        logger.debug("BeatifyTokenRepository başlatıldı.")

    def _ensure_connection(self):
        """Veritabanı bağlantısının açık olduğundan emin olur."""
        self.db._ensure_connection()

    def _close_if_owned(self):
        """
        Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulmuşsa,
        işlem sonunda bağlantıyı kapatır.
        """
        if self.own_connection:
            self.db.close()
            logger.debug("Sahip olunan veritabanı bağlantısı kapatıldı.")

    # -------------------------------------------------------------------------
    # 2.2. Token Sorgulama (Read Operations)
    # -------------------------------------------------------------------------

    def validate_auth_token(self, token: str) -> Optional[str]:
        """
        Bir kimlik doğrulama token'ının geçerli, süresinin dolmamış ve aktif
        olduğunu kontrol eder. Geçerliyse, ilgili kullanıcı adını döndürür.
        """
        self._ensure_connection()
        try:
            query = """
                SELECT username FROM beatify_auth_tokens
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
            """
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()

            if result:
                logger.debug(f"Token başarıyla doğrulandı. Kullanıcı: {result.get('username')}")
                return result.get('username')

            logger.warning(f"Geçersiz veya süresi dolmuş token ile doğrulama denemesi: {token[:10]}...")
            return None
        except MySQLError as e:
            logger.error(f"Token doğrulanırken veritabanı hatası: {e}", exc_info=True)
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 2.3. Token Yönetimi (Write Operations)
    # -------------------------------------------------------------------------

    def store_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        """Verilen kullanıcı için yeni bir kimlik doğrulama token'ını veritabanına kaydeder."""
        self._ensure_connection()
        try:
            query = "INSERT INTO beatify_auth_tokens (username, token, expires_at) VALUES (%s, %s, %s)"
            expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
            self.db.cursor.execute(query, (username, token, expires_at_str))
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için yeni auth token başarıyla saklandı.")
            return True
        except MySQLError as e:
            logger.error(f"Auth token saklanırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def deactivate_auth_token(self, username: str, token: str) -> bool:
        """
        Kullanıcıya ait belirli bir token'ı geçersiz kılar (çıkış yapma).
        Token'ın `expired_at` alanını mevcut zamanla günceller.
        """
        self._ensure_connection()
        try:
            query = "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (token, username))
            self.db.connection.commit()

            if self.db.cursor.rowcount > 0:
                logger.info(f"Kullanıcı '{username}' için token başarıyla geçersiz kılındı.")
                return True

            logger.warning(f"Geçersiz kılınacak aktif token bulunamadı (Kullanıcı: {username}).")
            return False
        except MySQLError as e:
            logger.error(f"Token geçersiz kılınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def deactivate_all_user_tokens(self, username: str) -> bool:
        """
        Bir kullanıcıya ait tüm aktif token'ları geçersiz kılar. Genellikle
        parola değişikliği veya "tüm cihazlardan çıkış yap" işlevi için kullanılır.
        """
        self._ensure_connection()
        try:
            query = "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            logger.info(f"Kullanıcı '{username}' için {self.db.cursor.rowcount} adet token geçersiz kılındı.")
            return self.db.cursor.rowcount > 0
        except MySQLError as e:
            logger.error(f"Kullanıcının tüm token'ları geçersiz kılınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

# =============================================================================
# Beatify Token Veritabanı Deposu Modülü Sonu
# =============================================================================