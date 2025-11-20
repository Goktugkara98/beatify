from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from datetime import datetime
from app.database.db_connection import DatabaseConnection


class BeatifyUserRepository:
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

    def beatify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = """
                SELECT id, username, email, is_spotify_connected, created_at, updated_at
                FROM users WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            user = self.db.cursor.fetchone()

            if not user:
                return None

            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(user.get('updated_at'), datetime):
                user['updated_at'] = user['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_user_by_username_or_email(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user = self.db.cursor.fetchone()
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def beatify_get_password_hash_data(self, username: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = "SELECT password_hash FROM users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('password_hash')
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def beatify_get_username_or_email_data(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = "SELECT id, username, email FROM users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user = self.db.cursor.fetchone()
            return user
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def create_new_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        self._ensure_connection()
        try:
            query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            self.db.cursor.execute(query, (username, email, password_hash))
            self.db.connection.commit()
            user_id = self.db.cursor.lastrowid
            return user_id
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return None
        finally:
            self._close_if_owned()

    def update_spotify_connection_status(self, username: str, status: bool) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
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



