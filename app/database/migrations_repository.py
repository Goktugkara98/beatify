# migrations_repository.py
# =============================================================================
# Migrations (Tablo Oluşturma) Repository Modülü
# =============================================================================
# Bu modül, uygulama için gerekli tüm veritabanı tablolarının
# oluşturulmasını yönetir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  MIGRATIONS REPOSITORY SINIFI (MIGRATIONS REPOSITORY CLASS)
#      2.1. MigrationsRepository
#           2.1.1. __init__
#           2.1.2. _ensure_connection
#           2.1.3. _close_if_owned
#           2.1.4. create_beatify_users_table
#           2.1.5. create_beatify_auth_tokens_table
#           2.1.6. create_spotify_users_table
#           2.1.7. create_all_tables
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional
from app.database.db_connection import DatabaseConnection # Bir üst dizindeki db_connection modülünden import

# =============================================================================
# 2.0 MIGRATIONS REPOSITORY SINIFI (MIGRATIONS REPOSITORY CLASS)
# =============================================================================
class MigrationsRepository:
    """
    Veritabanı tablolarının oluşturulması ve şema yönetimi ile ilgili işlemleri yönetir.
    """
    # -------------------------------------------------------------------------
    # 2.1.1. __init__ : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        MigrationsRepository sınıfının başlatıcı metodu.
        Eğer bir `db_connection` sağlanırsa onu kullanır, aksi takdirde
        yeni bir `DatabaseConnection` örneği oluşturur ve yönetir.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    # -------------------------------------------------------------------------
    # 2.1.2. _ensure_connection : Bu depo için veritabanı bağlantısının aktif olmasını sağlar.
    # -------------------------------------------------------------------------
    def _ensure_connection(self):
        """ Bu repository için veritabanı bağlantısının aktif olmasını sağlar. """
        self.db._ensure_connection()

    # -------------------------------------------------------------------------
    # 2.1.3. _close_if_owned : Bağlantı bu sınıf tarafından oluşturulduysa kapatır.
    # -------------------------------------------------------------------------
    def _close_if_owned(self):
        """ Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulduysa bağlantıyı kapatır. """
        if self.own_connection:
            self.db.close()

    # -------------------------------------------------------------------------
    # 2.1.4. create_beatify_users_table : `beatify_users` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_beatify_users_table(self):
        """
        `beatify_users` tablosunu oluşturur (eğer mevcut değilse).
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        try:
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
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 2.1.5. create_beatify_auth_tokens_table : `beatify_auth_tokens` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_beatify_auth_tokens_table(self):
        """
        `beatify_auth_tokens` tablosunu oluşturur (eğer mevcut değilse).
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        try:
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
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 2.1.6. create_spotify_users_table : `spotify_users` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_spotify_users_table(self):
        """
        `spotify_users` tablosunu oluşturur (eğer mevcut değilse).
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        try:
            query = """
                CREATE TABLE IF NOT EXISTS spotify_users (
                    username VARCHAR(255) PRIMARY KEY,
                    spotify_user_id VARCHAR(255) UNIQUE,
                    client_id VARCHAR(255) DEFAULT NULL,
                    client_secret VARCHAR(255) DEFAULT NULL,
                    refresh_token TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    widget_token TEXT DEFAULT NULL,
                    short_token VARCHAR(20) DEFAULT NULL,
                    design VARCHAR(255) DEFAULT 'standard',
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE,
                    INDEX idx_short_token (short_token)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            self.db.cursor.execute(query)
            self.db.connection.commit()
        except MySQLError as e:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 2.1.7. create_all_tables : Uygulama için gerekli tüm veritabanı tablolarını oluşturur.
    # -------------------------------------------------------------------------
    def create_all_tables(self):
        """
        Uygulama için gerekli olan tüm veritabanı tablolarını oluşturur.
        İşlem sırasında bir hata oluşursa, istisna fırlatır.
        """
        self._ensure_connection()
        try:
            print("beatify_users tablosu oluşturuluyor...")
            self.create_beatify_users_table()
            print("beatify_auth_tokens tablosu oluşturuluyor...")
            self.create_beatify_auth_tokens_table()
            print("spotify_users tablosu oluşturuluyor...")
            self.create_spotify_users_table()
            print("Tüm tablolar başarıyla oluşturuldu veya zaten mevcut.")
        except MySQLError as e:
            print(f"Tablo oluşturma sırasında genel hata: {e}")
            # Rollback burada yapılmaz, her create_table metodu kendi içinde yapar.
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# Migrations Repository Modülü Sonu
# =============================================================================
