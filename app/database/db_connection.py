# =============================================================================
# Veritabanı Bağlantı Modülü (db_connection.py)
# =============================================================================
# Bu modül, MySQL veritabanı bağlantılarını yönetmek için kullanılan
# `DatabaseConnection` sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Standart kütüphane, üçüncü parti paketler ve uygulama içi modüller.
#
# 2.0  SINIFLAR (CLASSES)
#      2.1. DatabaseConnection
#           2.1.1. __init__(config=None)
#           2.1.2. ensure_connection()
#           2.1.3. close()
# =============================================================================

from __future__ import annotations

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
from typing import Any, Dict, Optional

# Üçüncü parti
import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector import MySQLConnection

# Uygulama içi
from app.config.config import DB_CONFIG


# =============================================================================
# 2.0 SINIFLAR (CLASSES)
# =============================================================================

class DatabaseConnection:
    """MySQL veritabanı bağlantısını yöneten yardımcı sınıf."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """DatabaseConnection sınıfını başlatır.

        Args:
            config: Veritabanı yapılandırma sözlüğü. Verilmezse `DB_CONFIG` kullanılır.
        """
        effective_config = config or DB_CONFIG
        self.config: Dict[str, Any] = {
            "host": effective_config.get("host"),
            "user": effective_config.get("user"),
            "password": effective_config.get("password"),
            "database": effective_config.get("database"),
            "port": effective_config.get("port"),
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
        }

        self.connection: Optional[MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor_cext.CMySQLCursorDict] = None

    def ensure_connection(self) -> None:
        """Bağlantı yoksa veya kopmuşsa yeniden bağlanır ve cursor oluşturur."""
        if self.connection is None or not self.connection.is_connected():
            self.connection = mysql.connector.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                port=self.config.get("port") or 3306,
                charset=self.config.get("charset", "utf8mb4"),
            )
            # Dict cursor: sonuçlara `row["kolon_adi"]` ile erişebilmek için
            self.cursor = self.connection.cursor(dictionary=True)

    def close(self) -> None:
        """Cursor ve bağlantıyı güvenli bir şekilde kapatır."""
        if self.cursor is not None:
            try:
                self.cursor.close()
            except MySQLError:
                pass
            finally:
                self.cursor = None

        if self.connection is not None:
            try:
                if self.connection.is_connected():
                    self.connection.close()
            except MySQLError:
                pass
            finally:
                self.connection = None


# =============================================================================
# Veritabanı Bağlantı Modülü Sonu
# =============================================================================
