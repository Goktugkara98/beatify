# =============================================================================
# Auth Tokens Tablo Migration Modülü (auth_tokens_table.py)
# =============================================================================
# Bu modül, `auth_tokens` veritabanı tablosunun oluşturulmasını sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  FONKSİYONLAR (FUNCTIONS)
#      2.1. create_auth_tokens_table(db_connection=None)
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

def create_auth_tokens_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """Kullanıcı erişim token'larının tutulduğu `auth_tokens` tablosunu oluşturur.

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
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                expired_at DATETIME DEFAULT NULL,
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
    create_auth_tokens_table()


# =============================================================================
# Auth Tokens Tablo Migration Modülü Sonu
# =============================================================================
