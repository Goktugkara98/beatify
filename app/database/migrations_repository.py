# =============================================================================
# Veritabanı Geçiş Deposu Modülü (Database Migrations Repository Module)
# =============================================================================
# Bu modül, veritabanı şemasının (tabloların) oluşturulması ve yönetilmesi
# için gerekli geçiş (migration) işlemlerini yürüten `MigrationsRepository`
# sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SINIF TANIMI: MigrationsRepository
#      2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
#           - __init__()
#           - _ensure_connection()
#           - _close_if_owned()
#      2.2. Şema Yönetimi (Schema Management)
#           - create_beatify_users_table()
#           - create_beatify_auth_tokens_table()
#           - create_spotify_users_table()
#           - create_spotify_widget_configs_table()
#           - create_all_tables()
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from mysql.connector import Error as MySQLError
from typing import Optional
from app.database.db_connection import DatabaseConnection

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 SINIF TANIMI: MigrationsRepository
# =============================================================================
class MigrationsRepository:
    """
    Veritabanı şemasını (tabloları) oluşturmak için geçiş işlemlerini yürütür.
    """

    # -------------------------------------------------------------------------
    # 2.1. Başlatma ve Bağlantı Yönetimi (Initialization & Connection)
    # -------------------------------------------------------------------------

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        MigrationsRepository sınıfını başlatır.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True
        logger.debug("MigrationsRepository başlatıldı.")

    def _ensure_connection(self):
        """Veritabanı bağlantısı kapalıysa yeniden kurar."""
        self.db._ensure_connection()

    def _close_if_owned(self):
        """Sınıfın kendisine ait olan veritabanı bağlantısını kapatır."""
        if self.own_connection:
            self.db.close()
            logger.debug("Sahip olunan veritabanı bağlantısı kapatıldı.")

    # -------------------------------------------------------------------------
    # 2.2. Şema Yönetimi (Schema Management)
    # -------------------------------------------------------------------------

    def create_beatify_users_table(self):
        """`beatify_users` tablosunu oluşturur."""
        self._ensure_connection()
        logger.info("`beatify_users` tablosu oluşturuluyor...")
        query = """
            CREATE TABLE IF NOT EXISTS beatify_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_spotify_connected BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.db.cursor.execute(query)
        self.db.connection.commit()
        logger.info("`beatify_users` tablosu başarıyla oluşturuldu/kontrol edildi.")

    def create_beatify_auth_tokens_table(self):
        """`beatify_auth_tokens` tablosunu oluşturur."""
        self._ensure_connection()
        logger.info("`beatify_auth_tokens` tablosu oluşturuluyor...")
        query = """
            CREATE TABLE IF NOT EXISTS beatify_auth_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                expired_at DATETIME DEFAULT NULL,
                FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.db.cursor.execute(query)
        self.db.connection.commit()
        logger.info("`beatify_auth_tokens` tablosu başarıyla oluşturuldu/kontrol edildi.")

    def create_spotify_users_table(self):
        """`spotify_users` tablosunu oluşturur."""
        self._ensure_connection()
        logger.info("`spotify_users` tablosu oluşturuluyor...")
        query = """
            CREATE TABLE IF NOT EXISTS spotify_users (
                username VARCHAR(255) PRIMARY KEY,
                spotify_user_id VARCHAR(255) UNIQUE,
                client_id VARCHAR(255) DEFAULT NULL,
                client_secret VARCHAR(255) DEFAULT NULL,
                refresh_token TEXT DEFAULT NULL,
                widget_token VARCHAR(255) DEFAULT NULL,
                short_token VARCHAR(50) DEFAULT NULL,
                design VARCHAR(50) DEFAULT 'standard',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.db.cursor.execute(query)
        self.db.connection.commit()
        logger.info("`spotify_users` tablosu başarıyla oluşturuldu/kontrol edildi.")

    def create_spotify_widget_configs_table(self):
        """`spotify_widget_configs` tablosunu oluşturur."""
        self._ensure_connection()
        logger.info("`spotify_widget_configs` tablosu oluşturuluyor...")
        query = """
            CREATE TABLE IF NOT EXISTS spotify_widget_configs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                beatify_username VARCHAR(255) NOT NULL,
                widget_token VARCHAR(255) UNIQUE NOT NULL,
                widget_name VARCHAR(255) DEFAULT NULL,
                widget_type VARCHAR(100) NOT NULL,
                config_data JSON NOT NULL,
                spotify_user_id VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (beatify_username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE,
                INDEX idx_widget_type (widget_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.db.cursor.execute(query)
        self.db.connection.commit()
        logger.info("`spotify_widget_configs` tablosu başarıyla oluşturuldu/kontrol edildi.")

    def create_all_tables(self):
        """Uygulama için gerekli olan tüm tabloları tek bir çağrıda oluşturur."""
        self._ensure_connection()
        try:
            self.create_beatify_users_table()
            self.create_beatify_auth_tokens_table()
            self.create_spotify_users_table()
            self.create_spotify_widget_configs_table()
        except MySQLError as e:
            logger.critical(f"Tablo oluşturma sırasında kritik bir hata oluştu: {e}", exc_info=True)
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            # Hatayı yeniden yükselterek uygulamanın başlamasını engelle
            raise
        finally:
            self._close_if_owned()
