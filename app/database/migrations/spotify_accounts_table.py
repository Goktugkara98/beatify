# =============================================================================
# Spotify Accounts Tablo Migration Modülü (spotify_accounts_table.py)
# =============================================================================
# Bu modül, `spotify_accounts` veritabanı tablosunun oluşturulmasını sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  FONKSİYONLAR (FUNCTIONS)
#      2.1. create_spotify_accounts_table(db_connection=None)
#
# 3.0  KOMUT SATIRI (CLI)
#      3.1. __main__ (doğrudan çalıştırma)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
from typing import Optional

# Üçüncü parti
from mysql.connector import Error as MySQLError

# Uygulama içi
from app.database.db_connection import DatabaseConnection


# =============================================================================
# 2.0 FONKSİYONLAR (FUNCTIONS)
# =============================================================================

def create_spotify_accounts_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """Spotify entegrasyon bilgilerini tutan `spotify_accounts` tablosunu oluşturur.

    Args:
        db_connection: Mevcut veritabanı bağlantısı.
    """
    own_connection = False
    db = db_connection

    if db is None:
        db = DatabaseConnection()
        own_connection = True

    try:
        db.ensure_connection()
        query = """
            CREATE TABLE IF NOT EXISTS spotify_accounts (
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
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        db.cursor.execute(query)
        db.connection.commit()
    except MySQLError:
        if db.connection and db.connection.is_connected():
            db.connection.rollback()
        raise
    finally:
        if own_connection:
            db.close()


# =============================================================================
# 3.0 KOMUT SATIRI (CLI)
# =============================================================================

if __name__ == "__main__":
    create_spotify_accounts_table()


# =============================================================================
# Spotify Accounts Tablo Migration Modülü Sonu
# =============================================================================
