# =============================================================================
# Veritabanı Bağlantı Modülü (Database Connection Module)
# =============================================================================
# Bu modül, MySQL veritabanı bağlantısını yönetmek için bir sarmalayıcı
# (wrapper) olan `DatabaseConnection` sınıfını içerir. Bağlantı kurma,
# sonlandırma ve bağlantının sürekliliğini sağlama işlemlerini merkezileştirir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SINIF TANIMI: DatabaseConnection
#      2.1. Başlatma (Initialization)
#           - __init__()
#      2.2. Bağlantı Yönetimi (Connection Management)
#           - connect()
#           - close()
#           - _ensure_connection()
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
import mysql.connector
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from app.config import DB_CONFIG

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: DatabaseConnection
# =============================================================================
class DatabaseConnection:
    """
    MySQL veritabanı bağlantısını yönetmek için bir sarmalayıcı (wrapper) sınıf.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma (Initialization)
    # -------------------------------------------------------------------------

    def __init__(self):
        """
        DatabaseConnection sınıfını başlatır.
        """
        self.connection: Optional[mysql.connector.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None
        self.db_config: Dict[str, Any] = DB_CONFIG
        logger.debug("DatabaseConnection nesnesi oluşturuldu.")

    # -------------------------------------------------------------------------
    # 2.2. Bağlantı Yönetimi (Connection Management)
    # -------------------------------------------------------------------------

    def connect(self):
        """
        Yapılandırma dosyasındaki bilgileri kullanarak veritabanına bağlanır.

        Raises:
            MySQLError: Veritabanı bağlantısı kurulamazsa.
        """
        try:
            logger.debug(f"Veritabanına bağlanılıyor: {self.db_config.get('host')}/{self.db_config.get('database')}")
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                # dictionary=True, sorgu sonuçlarını sözlük olarak döndürür.
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info("Veritabanı bağlantısı başarıyla kuruldu.")
            else:
                # Bu durum genellikle connect() bir istisna fırlattığı için nadiren tetiklenir.
                raise MySQLError("Veritabanı bağlantısı kuruldu ancak aktif değil.")
        except MySQLError as e:
            logger.critical(f"Veritabanı bağlantısı kurulamadı: {e}", exc_info=True)
            self.connection = None
            self.cursor = None
            raise

    def close(self):
        """Mevcut imleci ve veritabanı bağlantısını güvenli bir şekilde kapatır."""
        if self.cursor:
            try:
                self.cursor.close()
            except MySQLError as e:
                logger.warning(f"Cursor kapatılırken hata oluştu (yoksayılıyor): {e}")
            self.cursor = None

        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                logger.info("Veritabanı bağlantısı kapatıldı.")
            except MySQLError as e:
                logger.warning(f"Bağlantı kapatılırken hata oluştu (yoksayılıyor): {e}")
            self.connection = None

    def _ensure_connection(self):
        """
        Bağlantının veya imlecin aktif olup olmadığını kontrol eder. Değilse, yeniden bağlanır.
        """
        try:
            if not self.connection or not self.connection.is_connected() or not self.cursor:
                logger.info("Bağlantı kapalı veya mevcut değil. Yeniden bağlanılıyor...")
                self.connect()
        except MySQLError:
            # Connect metodu zaten hatayı loglayıp yükselteceği için burada tekrar loglamaya gerek yok.
            raise
