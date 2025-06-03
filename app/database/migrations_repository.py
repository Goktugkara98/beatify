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
#           2.1.7. create_spotify_widget_configs_table  <-- YENİ
#           2.1.8. create_all_tables                    <-- GÜNCELLENDİ
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from mysql.connector import Error as MySQLError
from typing import Optional
# app.database.db_connection modülünün doğru yolda olduğundan emin olun.
# Eğer migrations_repository.py dosyası app/database/ klasöründeyse:
from .db_connection import DatabaseConnection
# Eğer app/ klasörünün bir üst dizinindeyse ve app bir paketse:
# from app.database.db_connection import DatabaseConnection

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
            print("`beatify_users` tablosu başarıyla oluşturuldu veya zaten mevcut.")
        except MySQLError as e:
            print(f"`beatify_users` tablosu oluşturulurken hata: {e}")
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
            # beatify_users tablosunda username UNIQUE olduğu için FOREIGN KEY (username) kullanılabilir.
            # Ancak genellikle ID üzerinden bağlantı kurulur. Eğer beatify_user_id INT ise,
            # beatify_user_id INT NOT NULL,
            # FOREIGN KEY (beatify_user_id) REFERENCES beatify_users(id) ON DELETE CASCADE ON UPDATE CASCADE
            # şeklinde olmalıdır. Mevcut yapıda username kullanılmış.
            self.db.cursor.execute(query)
            self.db.connection.commit()
            print("`beatify_auth_tokens` tablosu başarıyla oluşturuldu veya zaten mevcut.")
        except MySQLError as e:
            print(f"`beatify_auth_tokens` tablosu oluşturulurken hata: {e}")
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 2.1.6. create_spotify_users_table : `spotify_users` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_spotify_users_table(self):
        """
        `spotify_users` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, Beatify kullanıcılarının Spotify hesap bilgilerini saklar.
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        try:
            query = """
                CREATE TABLE IF NOT EXISTS spotify_users (
                    username VARCHAR(255) PRIMARY KEY, /* Beatify kullanıcısının username'i */
                    spotify_user_id VARCHAR(255) UNIQUE, /* Spotify kullanıcı ID'si */
                    access_token TEXT DEFAULT NULL, /* Spotify API erişim token'ı */
                    refresh_token TEXT DEFAULT NULL, /* Spotify API yenileme token'ı */
                    token_expires_at DATETIME DEFAULT NULL, /* Erişim token'ının son kullanma tarihi */
                    scopes TEXT DEFAULT NULL, /* İzin verilen Spotify kapsamları (virgülle ayrılmış) */
                    client_id VARCHAR(255) DEFAULT NULL, /* Geliştirici kendi client ID/Secret'ını girerse */
                    client_secret VARCHAR(255) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE  -- Corrected: Removed trailing comma
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            self.db.cursor.execute(query)
            self.db.connection.commit()
            print("`spotify_users` tablosu başarıyla oluşturuldu veya zaten mevcut.")
        except MySQLError as e:
            print(f"`spotify_users` tablosu oluşturulurken hata: {e}")
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 2.1.7. create_spotify_widget_configs_table : `spotify_widget_configs` tablosunu oluşturur. (YENİ)
    # -------------------------------------------------------------------------
    def create_spotify_widget_configs_table(self):
        """
        `spotify_widget_configs` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, kullanıcıların özelleştirilmiş Spotify widget yapılandırmalarını saklar.
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        try:
            query = """
                CREATE TABLE IF NOT EXISTS spotify_widget_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    beatify_username VARCHAR(255) NOT NULL,
                    widget_token VARCHAR(255) UNIQUE NOT NULL,
                    widget_name VARCHAR(255) DEFAULT NULL,
                    widget_type VARCHAR(100) NOT NULL,
                    config_data TEXT NOT NULL, /* JSON formatında widget ayarları */
                    spotify_user_id VARCHAR(255) DEFAULT NULL, /* Bu widget'ın hangi Spotify kullanıcısının verilerini göstereceği */
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (beatify_username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE,
                    INDEX idx_widget_type (widget_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            # widget_token zaten UNIQUE olduğu için otomatik olarak indekslenir,
            # ancak açıkça INDEX idx_widget_token (widget_token) de eklenebilir.
            self.db.cursor.execute(query)
            self.db.connection.commit()
            print("`spotify_widget_configs` tablosu başarıyla oluşturuldu veya zaten mevcut.")
        except MySQLError as e:
            print(f"`spotify_widget_configs` tablosu oluşturulurken hata: {e}")
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
            
    # -------------------------------------------------------------------------
    # 2.1.8. create_all_tables : Uygulama için gerekli tüm veritabanı tablolarını oluşturur. (GÜNCELLENDİ)
    # -------------------------------------------------------------------------
    def create_all_tables(self):
        """
        Uygulama için gerekli olan tüm veritabanı tablolarını oluşturur.
        İşlem sırasında bir hata oluşursa, istisna fırlatır.
        """
        self._ensure_connection()
        try:
            self.create_beatify_users_table()
            self.create_beatify_auth_tokens_table()
            self.create_spotify_users_table()
            self.create_spotify_widget_configs_table() # Yeni tabloyu ekledik
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

# Örnek Kullanım (Bu kısmı uygulamanızın ana başlatma noktasında çağırabilirsiniz):
# if __name__ == '__main__':
#     try:
#         migrations_repo = MigrationsRepository()
#         migrations_repo.create_all_tables()
#         print("Veritabanı migration işlemleri tamamlandı.")
#     except MySQLError as err:
#         print(f"Veritabanı migration hatası: {err}")
#     except Exception as general_err:
#         print(f"Beklenmedik bir hata oluştu: {general_err}")

