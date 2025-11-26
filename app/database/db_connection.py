"""
MODÜL: db_connection.py

Bu modül, MySQL veritabanı bağlantılarını yönetmek için kullanılan `DatabaseConnection`
sınıfını içerir.

İÇİNDEKİLER:
    - DatabaseConnection (Sınıf): Veritabanı bağlantı ve cursor yönetimini sağlar.
        - __init__: Yapılandırıcı metod.
        - ensure_connection: Bağlantıyı kontrol eder ve gerekirse yeniden başlatır.
        - close: Bağlantıyı ve cursor'ı kapatır.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import mysql.connector
from mysql.connector import MySQLConnection, Error as MySQLError

from app.config.config import DB_CONFIG


class DatabaseConnection:
    """
    MySQL veritabanı bağlantısını yöneten yardımcı sınıf.

    Bu sınıf, veritabanı bağlantısını başlatmak, açık tutmak ve kapatmak için
    gerekli yöntemleri sağlar.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        DatabaseConnection sınıfını başlatır.

        Args:
            config (Optional[Dict[str, Any]]): Veritabanı yapılandırma sözlüğü.
                                               Eğer verilmezse, varsayılan `DB_CONFIG` kullanılır.
        """
        self.config: Dict[str, Any] = {
            "host": (config or DB_CONFIG).get("host"),
            "user": (config or DB_CONFIG).get("user"),
            "password": (config or DB_CONFIG).get("password"),
            "database": (config or DB_CONFIG).get("database"),
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
        }
        self.connection: Optional[MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor_cext.CMySQLCursorDict] = None

    def ensure_connection(self) -> None:
        """
        Bağlantı yoksa veya kopmuşsa yeniden bağlanır ve cursor oluşturur.
        """
        if self.connection is None or not self.connection.is_connected():
            self.connection = mysql.connector.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset=self.config.get("charset", "utf8mb4"),
            )
            # Dict cursor: sonuçlara `row["kolon_adi"]` ile erişebilmek için
            self.cursor = self.connection.cursor(dictionary=True)

    def close(self) -> None:
        """
        Cursor ve bağlantıyı güvenli bir şekilde kapatır.
        """
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
