from mysql.connector import Error as MySQLError
from typing import Optional

from app.database.db_connection import DatabaseConnection
from app.database.migrations.users_table import create_users_table
from app.database.migrations.auth_tokens_table import create_auth_tokens_table
from app.database.migrations.spotify_accounts_table import create_spotify_accounts_table
from app.database.migrations.widgets_table import create_widgets_table


class MigrationsRepository:
    """
    Uygulama açılışında tüm tabloların oluşturulmasını yöneten sınıf.

    Gerçek SQL migration'ları `app.database.migrations` paketindeki
    fonksiyonlara taşınmıştır.
    """

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    def _ensure_connection(self):
        self.db._ensure_connection()

    def _close_if_owned(self):
        if self.own_connection:
            self.db.close()

    def create_users_table(self):
        """`users` tablosunu oluşturur."""
        create_users_table(self.db)

    def create_auth_tokens_table(self):
        """`auth_tokens` tablosunu oluşturur."""
        create_auth_tokens_table(self.db)

    def create_spotify_accounts_table(self):
        """`spotify_accounts` tablosunu oluşturur."""
        create_spotify_accounts_table(self.db)

    def create_widgets_table(self):
        """`widgets` tablosunu oluşturur."""
        create_widgets_table(self.db)

    def create_all_tables(self):
        """Tüm tabloların oluşturulmasını sağlar."""
        self._ensure_connection()
        try:
            self.create_users_table()
            self.create_auth_tokens_table()
            self.create_spotify_accounts_table()
            self.create_widgets_table()
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()


