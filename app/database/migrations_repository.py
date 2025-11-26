"""
MODÜL: migrations_repository.py

Bu modül, veritabanı tablolarının oluşturulmasını ve yönetilmesini sağlayan
`MigrationsRepository` sınıfını içerir.

İÇİNDEKİLER:
    - MigrationsRepository (Sınıf): Tablo oluşturma işlemlerini yönetir.
        - __init__: Başlatıcı metod.
        - create_all_tables: Tüm tabloları sırasıyla oluşturur.
        - create_users_table: Kullanıcılar tablosunu oluşturur.
        - create_auth_tokens_table: Kimlik doğrulama tokenları tablosunu oluşturur.
        - create_spotify_accounts_table: Spotify hesapları tablosunu oluşturur.
        - create_widgets_table: Widget tablosunu oluşturur.
"""

from typing import Optional
from mysql.connector import Error as MySQLError

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

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """
        MigrationsRepository sınıfını başlatır.

        Args:
            db_connection (Optional[DatabaseConnection]): Mevcut bir veritabanı bağlantısı.
                                                          Verilmezse yeni bir tane oluşturulur.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True

    def create_all_tables(self) -> None:
        """
        Tüm veritabanı tablolarının oluşturulmasını sağlar.
        """
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

    def create_users_table(self) -> None:
        """`users` tablosunu oluşturur."""
        create_users_table(self.db)

    def create_auth_tokens_table(self) -> None:
        """`auth_tokens` tablosunu oluşturur."""
        create_auth_tokens_table(self.db)

    def create_spotify_accounts_table(self) -> None:
        """`spotify_accounts` tablosunu oluşturur."""
        create_spotify_accounts_table(self.db)

    def create_widgets_table(self) -> None:
        """`widgets` tablosunu oluşturur."""
        create_widgets_table(self.db)

    def _ensure_connection(self) -> None:
        """Veritabanı bağlantısının açık olduğundan emin olur."""
        self.db.ensure_connection()

    def _close_if_owned(self) -> None:
        """Eğer bağlantı bu sınıf tarafından oluşturulduysa kapatır."""
        if self.own_connection:
            self.db.close()
