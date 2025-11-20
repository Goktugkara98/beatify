from typing import Optional
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


def create_spotify_accounts_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """
    Spotify entegrasyon bilgilerini tutan `spotify_accounts` tablosunu oluşturur.

    - Program açılışında MigrationsRepository üzerinden çağrılabilir.
    - Doğrudan bu dosya çalıştırıldığında da tabloyu oluşturur.
    """
    own_connection = False
    db = db_connection

    if db is None:
        db = DatabaseConnection()
        own_connection = True

    try:
        db._ensure_connection()
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


if __name__ == "__main__":
    create_spotify_accounts_table()



