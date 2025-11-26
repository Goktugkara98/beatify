"""
MODÜL: auth_tokens_table.py

Bu modül, `auth_tokens` veritabanı tablosunun oluşturulmasını sağlar.

İÇİNDEKİLER:
    - create_auth_tokens_table: Tablo oluşturma fonksiyonu.
"""

from typing import Optional
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


def create_auth_tokens_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """
    Kullanıcı erişim token'larının tutulduğu `auth_tokens` tablosunu oluşturur.

    Args:
        db_connection (Optional[DatabaseConnection]): Mevcut veritabanı bağlantısı.
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


if __name__ == "__main__":
    create_auth_tokens_table()
