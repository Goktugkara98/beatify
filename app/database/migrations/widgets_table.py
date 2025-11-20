from typing import Optional
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


def create_widgets_table(db_connection: Optional[DatabaseConnection] = None) -> None:
    """
    Kullanıcıların oluşturduğu widget'ları tutan genel `widgets` tablosunu oluşturur.

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


if __name__ == "__main__":
    create_widgets_table()



