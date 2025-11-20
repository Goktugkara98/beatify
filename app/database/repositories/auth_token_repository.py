from mysql.connector import Error as MySQLError
from typing import Optional
from datetime import datetime
from app.database.db_connection import DatabaseConnection


class BeatifyTokenRepository:
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

    def validate_auth_token(self, token: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = """
                SELECT username FROM auth_tokens
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
            """
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()

            if result:
                return result.get('username')

            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def store_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        self._ensure_connection()
        try:
            query = "INSERT INTO auth_tokens (username, token, expires_at) VALUES (%s, %s, %s)"
            expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
            self.db.cursor.execute(query, (username, token, expires_at_str))
            self.db.connection.commit()
            return True
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def deactivate_auth_token(self, username: str, token: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (token, username))
            self.db.connection.commit()

            if self.db.cursor.rowcount > 0:
                return True

            return False
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def deactivate_all_user_tokens(self, username: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE auth_tokens SET expired_at = NOW() WHERE username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()



