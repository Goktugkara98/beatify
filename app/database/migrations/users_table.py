"""
MODÜL: users_table.py

Bu modül, `users` veritabanı tablosunun oluşturulmasını sağlar.

İÇİNDEKİLER:
    - create_users_table: Tablo oluşturma fonksiyonu.
"""

from typing import Optional
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


def create_users_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """
    Uygulamanın ana kullanıcı tablosu olan `users` tablosunu oluşturur.

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
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                profile_image VARCHAR(255) DEFAULT NULL,
                is_spotify_connected BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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
    create_users_table()
