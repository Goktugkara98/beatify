# =============================================================================
# Widgets Tablo Migration Modülü (widgets_table.py)
# =============================================================================
# Bu modül, `widgets` veritabanı tablosunun oluşturulmasını sağlar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  FONKSİYONLAR (FUNCTIONS)
#      2.1. create_widgets_table(db_connection=None)
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

def create_widgets_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """Kullanıcıların oluşturduğu widget'ları tutan genel `widgets` tablosunu oluşturur.

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
            CREATE TABLE IF NOT EXISTS widgets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                beatify_username VARCHAR(255) NOT NULL,
                widget_token VARCHAR(255) UNIQUE NOT NULL,
                widget_name VARCHAR(255) DEFAULT NULL,
                widget_type VARCHAR(100) NOT NULL,
                config_data JSON NOT NULL,
                spotify_user_id VARCHAR(255) DEFAULT NULL,
                platform VARCHAR(50) NOT NULL DEFAULT 'spotify',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (beatify_username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
                INDEX idx_widget_type (widget_type),
                INDEX idx_widgets_platform (platform)
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
    create_widgets_table()


# =============================================================================
# Widgets Tablo Migration Modülü Sonu
# =============================================================================
