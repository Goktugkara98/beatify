# =============================================================================
# Database Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Database Connection
#    2.1. Initialization and Connection Management
#    2.2. Table Management
# 3. User Repository
#    3.1. Initialization and Connection Management
#    3.2. Table Management
#    3.3. User Data Operations
#    3.4. Authentication Operations
# 4. Spotify Repository
#    4.1. Initialization and Connection Management
#    4.2. Table Management
#    4.3. Credentials Management
#    4.4. Token Management
#    4.5. Account Management
#    4.6. Widget Management
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from app.config import DB_CONFIG

# -----------------------------------------------------------------------------
# 2. Database Connection
# -----------------------------------------------------------------------------
class DatabaseConnection:
    # -------------------------------------------------------------------------
    # 2.1. Initialization and Connection Management
    # -------------------------------------------------------------------------
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_config = DB_CONFIG
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
        except Error as e:
            raise
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None
    
    def _ensure_connection(self):
        if not self.connection or not self.cursor:
            self.connect()
    
    # -------------------------------------------------------------------------
    # 2.2. Table Management
    # -------------------------------------------------------------------------
    def create_all_tables(self):
        self._ensure_connection()
        
        user_repo = UserRepository(self)
        spotify_repo = SpotifyRepository(self)
        
        user_repo.create_beatify_users_table()
        user_repo.create_beatify_auth_tokens_table()
        spotify_repo.create_spotify_users_table()

# -----------------------------------------------------------------------------
# 3. User Repository
# -----------------------------------------------------------------------------
class UserRepository:
    # -------------------------------------------------------------------------
    # 3.1. Initialization and Connection Management
    # -------------------------------------------------------------------------
    def __init__(self, db_connection=None):
        self.db = db_connection or DatabaseConnection()
        self.own_connection = db_connection is None
    
    def _ensure_connection(self):
        if not hasattr(self.db, '_ensure_connection'):
            if not self.db.connection or not self.db.cursor:
                self.db.connect()
        else:
            self.db._ensure_connection()
    
    def _close_if_owned(self):
        if self.own_connection:
            self.db.close()
    
    # -------------------------------------------------------------------------
    # 3.2. Table Management
    # -------------------------------------------------------------------------
    def create_beatify_users_table(self):
        self._ensure_connection()
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS beatify_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL, 
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_spotify_connected BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    
    def create_beatify_auth_tokens_table(self):
        self._ensure_connection()
        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS beatify_auth_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    expired_at DATETIME DEFAULT NULL,
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self.db.connection.commit()
        except Error as e:
            raise
    
    # -------------------------------------------------------------------------
    # 3.3. User Data Operations
    # -------------------------------------------------------------------------
    def beatify_insert_new_user_data(self, username, email, password_hash):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "INSERT INTO beatify_users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()
    
    def beatify_get_user_data(self, username):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                SELECT id, username, email, is_spotify_connected, created_at, updated_at 
                FROM beatify_users 
                WHERE username = %s
                """,
                (username,)
            )
            user_data = self.db.cursor.fetchone()
            
            if not user_data:
                return None
                
            return {
                "id": user_data[0],
                "username": user_data[1],
                "email": user_data[2],
                "is_spotify_connected": bool(user_data[3]),
                "created_at": user_data[4],
                "updated_at": user_data[5]
            }
        except Error as e:
            return None
        finally:
            self._close_if_owned()

    def beatify_get_username_or_email_data(self, username, email):
        try:
            self._ensure_connection()
            self.db.cursor.execute("SELECT username, email FROM beatify_users WHERE username = %s OR email = %s", 
                                (username, email))
            return self.db.cursor.fetchone()
        finally:
            self._close_if_owned()
    
    def beatify_get_password_hash_data(self, username):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT password_hash FROM beatify_users WHERE username = %s",
                (username,)
            )
            result = self.db.cursor.fetchone()
            
            if result:
                return result[0]
            return None
        except Error as e:
            return None
        finally:
            self._close_if_owned()
    
    # -------------------------------------------------------------------------
    # 3.4. Auth Token Management
    # -------------------------------------------------------------------------
    def beatify_insert_or_update_auth_token(self, username, token, expires_at):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                INSERT INTO beatify_auth_tokens (username, token, expires_at) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE token = %s, expires_at = %s
                """,
                (username, token, expires_at, token, expires_at)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
    
    def beatify_validate_auth_token(self, token):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                SELECT username 
                FROM beatify_auth_tokens 
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
                """,
                (token,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            return None
        finally:
            self._close_if_owned()
    
    def beatify_deactivate_auth_token(self, username, token):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s",
                (token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

# -----------------------------------------------------------------------------
# 4. Spotify Repository
# -----------------------------------------------------------------------------
class SpotifyRepository:
    # -------------------------------------------------------------------------
    # 4.1. Initialization and Connection Management
    # -------------------------------------------------------------------------
    def __init__(self, db_connection=None):
        self.db = db_connection or DatabaseConnection()
        self.own_connection = db_connection is None
    
    def _ensure_connection(self):
        if not hasattr(self.db, '_ensure_connection'):
            if not self.db.connection or not self.db.cursor:
                self.db.connect()
        else:
            self.db._ensure_connection()
    
    def _close_if_owned(self):
        if self.own_connection:
            self.db.close()
    
    # -------------------------------------------------------------------------
    # 4.2. Table Management
    # -------------------------------------------------------------------------
    def create_spotify_users_table(self):
        self._ensure_connection()
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS spotify_users (
                username VARCHAR(255) PRIMARY KEY,
                spotify_user_id VARCHAR(255),
                client_id VARCHAR(255),
                client_secret VARCHAR(255),
                refresh_token VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                widget_token TEXT,
                design VARCHAR(255) DEFAULT 'standard',
                FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE,
                UNIQUE (spotify_user_id, username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    
    # -------------------------------------------------------------------------
    # 4.3. Spotify Data Management
    # -------------------------------------------------------------------------
    def spotify_get_user_data(self, username):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """SELECT spotify_user_id, client_id, client_secret, refresh_token, created_at, updated_at, widget_token 
                FROM spotify_users 
                WHERE username = %s""",
                (username,)
            )
            creds = self.db.cursor.fetchone()
            
            if not creds:
                return None
                
            return {
                "spotify_user_id": creds[0],
                "client_id": creds[1],
                "client_secret": creds[2],
                "refresh_token": creds[3],
                "created_at": creds[4],
                "updated_at": creds[5],
                "widget_token": creds[6]
            }
        except Error as e:
            return None
        finally:
            self._close_if_owned()

    def spotify_insert_or_update_client_info(self, username, client_id, client_secret):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                INSERT INTO spotify_users (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = %s, client_secret = %s
                """,
                (username, client_id, client_secret, client_id, client_secret)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()

    def spotify_update_user_info(self, username, spotify_user_id, refresh_token):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                UPDATE spotify_users 
                SET spotify_user_id = %s, refresh_token = %s
                WHERE username = %s
                """,
                (spotify_user_id, refresh_token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
    
    def spotify_delete_linked_account_data(self, username):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "DELETE spotify_user_id, refresh_token FROM spotify_users WHERE username = %s",
                (username,)
            )
            
            self.db.cursor.execute(
                "UPDATE beatify_users SET is_spotify_connected = FALSE WHERE username = %s",
                (username,)
            )
            
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
    
    
    # -------------------------------------------------------------------------
    # 4.4. Token Management
    # -------------------------------------------------------------------------
    def spotify_update_refresh_token_data(self, username, refresh_token, expires_in):
        try:
            self._ensure_connection()
            token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            self.db.cursor.execute(
                """
                UPDATE spotify_users 
                SET refresh_token = %s
                WHERE username = %s
                """,
                (refresh_token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
    
    # -------------------------------------------------------------------------
    # 4.5. Widget Management
    # -------------------------------------------------------------------------
    def spotify_store_widget_token_data(self, username, token):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE spotify_users SET widget_token = %s WHERE username = %s",
                (token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            return False
        finally:
            self._close_if_owned()
    
    def spotify_get_widget_token_data(self, username):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT widget_token FROM spotify_users WHERE username = %s",
                (username,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            return None
        finally:
            self._close_if_owned()
    
    def spotify_get_username_by_widget_token_data(self, token):
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT username FROM spotify_users WHERE widget_token = %s",
                (token,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            return None
        finally:
            self._close_if_owned()
