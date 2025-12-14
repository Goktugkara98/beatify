# =============================================================================
# Migration Yönetim Modülü (migrations_repository.py)
# =============================================================================
# Bu modül, uygulama açılışında veritabanı tablolarının oluşturulmasını yöneten
# `MigrationsRepository` sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SINIFLAR (CLASSES)
#      2.1. MigrationsRepository
#           2.1.1. __init__(db_connection=None)
#           2.1.2. create_all_tables()
#           2.1.3. create_users_table()
#           2.1.4. create_auth_tokens_table()
#           2.1.5. create_spotify_accounts_table()
#           2.1.6. create_widgets_table()
#           2.1.7. _ensure_connection()
#           2.1.8. _close_if_owned()
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
from app.database.migrations.auth_tokens_table import create_auth_tokens_table
from app.database.migrations.spotify_accounts_table import create_spotify_accounts_table
from app.database.migrations.users_table import create_users_table
from app.database.migrations.widgets_table import create_widgets_table


# =============================================================================
# 2.0 SINIFLAR (CLASSES)
# =============================================================================

class MigrationsRepository:
    """Uygulama açılışında tüm tabloların oluşturulmasını yöneten sınıf."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None) -> None:
        """MigrationsRepository sınıfını başlatır.

        Args:
            db_connection: Mevcut bir veritabanı bağlantısı. Verilmezse yeni oluşturulur.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
        else:
            self.db = DatabaseConnection()
            self.own_connection = True

    def create_all_tables(self) -> None:
        """Tüm veritabanı tablolarının oluşturulmasını sağlar."""
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

    # -------------------------------------------------------------------------
    # 2.2. Dahili yardımcılar (Internal helpers)
    # -------------------------------------------------------------------------

    def _ensure_connection(self) -> None:
        """Veritabanı bağlantısının açık olduğundan emin olur."""
        self.db.ensure_connection()

    def _close_if_owned(self) -> None:
        """Eğer bağlantı bu sınıf tarafından oluşturulduysa kapatır."""
        if self.own_connection:
            self.db.close()


# =============================================================================
# Migration Yönetim Modülü Sonu
# =============================================================================
