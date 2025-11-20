import json
from typing import Optional, Dict, Any
from mysql.connector import Error as MySQLError
from app.database.db_connection import DatabaseConnection


class SpotifyWidgetRepository:
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self._own_connection: bool = False
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self._own_connection: bool = True

    def _ensure_connection(self):
        self.db._ensure_connection()

    def _close_if_owned(self):
        if self._own_connection:
            self.db.close()

    def get_widget_token_by_username(self, username: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = """
                SELECT widget_token
                FROM widgets
                WHERE beatify_username = %s AND platform = 'spotify'
            """
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('widget_token')
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_widget_config_by_token(self, widget_token: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = "SELECT config_data FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (widget_token,))
            result = self.db.cursor.fetchone()

            if result:
                if isinstance(result.get('config_data'), str):
                    return json.loads(result['config_data'])
                return result.get('config_data')
            else:
                return None
        except json.JSONDecodeError:
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_username_by_widget_token(self, token: str) -> Optional[str]:
        self._ensure_connection()
        try:
            query = "SELECT beatify_username FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                return result.get('beatify_username')
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_data_by_widget_token(self, token: str) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        try:
            query = "SELECT * FROM widgets WHERE widget_token = %s AND platform = 'spotify'"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            if result:
                return result
            return None
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def get_widgets_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Belirtilen kullanıcı için tüm Spotify widget'larını döndürür.
        """
        self._ensure_connection()
        try:
            query = """
                SELECT *
                FROM widgets
                WHERE beatify_username = %s AND platform = 'spotify'
                ORDER BY created_at DESC
            """
            self.db.cursor.execute(query, (username,))
            results = self.db.cursor.fetchall()
            return results or []
        except MySQLError:
            return None
        finally:
            self._close_if_owned()

    def store_widget_config(self, config_data: Dict[str, Any]) -> bool:
        self._ensure_connection()
        try:
            query = """
            INSERT INTO widgets 
            (beatify_username, widget_token, widget_name, widget_type, config_data, spotify_user_id)
            VALUES (%(beatify_username)s, %(widget_token)s, %(widget_name)s, %(widget_type)s, %(config_data)s, %(spotify_user_id)s)
            ON DUPLICATE KEY UPDATE
                widget_token = VALUES(widget_token),
                widget_name = VALUES(widget_name),
                widget_type = VALUES(widget_type),
                config_data = VALUES(config_data);
            """
            self.db.cursor.execute(query, config_data)
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def update_widget_design_for_user(self, username: str, design: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE spotify_accounts SET design = %s WHERE username = %s"
            self.db.cursor.execute(query, (design, username))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def clear_widget_data_for_user(self, username: str) -> bool:
        self._ensure_connection()
        try:
            query = "UPDATE spotify_accounts SET widget_token = NULL, short_token = NULL, design = 'standard' WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
        except MySQLError:
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()



