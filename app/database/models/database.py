# =============================================================================
# Veritabanı Yönetim Modülü (Database Management Module)
# =============================================================================
# Bu modül, Beatify uygulaması için veritabanı bağlantısı, tablo oluşturma
# ve veri erişim işlemlerini (repository pattern kullanarak) yönetir.
# MySQL veritabanı ile etkileşim kurar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
# 2.0 VERİTABANI BAĞLANTI SINIFI (DATABASE CONNECTION CLASS)
#     2.1. DatabaseConnection
#          2.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
#          2.1.2. Tablo Yönetimi (Table Management)
# 3.0 KULLANICI DEPO SINIFI (USER REPOSITORY CLASS)
#     3.1. UserRepository
#          3.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
#          3.1.2. Tablo Yönetimi (Table Management)
#          3.1.3. Kullanıcı Veri İşlemleri (User Data Operations)
#          3.1.4. Kimlik Doğrulama Token Yönetimi (Auth Token Management)
# 4.0 SPOTIFY DEPO SINIFI (SPOTIFY REPOSITORY CLASS)
#     4.1. SpotifyRepository
#          4.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
#          4.1.2. Tablo Yönetimi (Table Management)
#          4.1.3. Spotify Veri Yönetimi (Spotify Data Management)
#          4.1.4. Token Yönetimi (Spotify Token Management - Refresh Token)
#          4.1.5. Widget Yönetimi (Spotify Widget Management)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from app.config import DB_CONFIG # Uygulama yapılandırmasından veritabanı ayarlarını alır
from typing import Optional

# =============================================================================
# 2.0 VERİTABANI BAĞLANTI SINIFI (DATABASE CONNECTION CLASS)
# =============================================================================
class DatabaseConnection:
    """
    MySQL veritabanı ile bağlantı kurma ve yönetme işlemlerini üstlenir.
    """
    # -------------------------------------------------------------------------
    # 2.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
    # -------------------------------------------------------------------------
    def __init__(self):
        """
        DatabaseConnection sınıfının başlatıcı metodu.
        Bağlantı ve cursor nesnelerini None olarak başlatır, veritabanı yapılandırmasını alır.
        """
        self.connection = None
        self.cursor = None
        self.db_config = DB_CONFIG

    def connect(self):
        """
        Yapılandırma bilgilerini kullanarak MySQL veritabanına bağlanır.
        Başarılı bağlantıda cursor oluşturur.
        Hata durumunda istisna fırlatır.
        """
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            # print("Veritabanına başarıyla bağlanıldı.") # Geliştirme için log
        except Error as e:
            # print(f"Veritabanı bağlantı hatası: {e}") # Geliştirme için log
            raise # Hatayı yukarı katmana ilet

    def close(self):
        """
        Açık olan cursor ve veritabanı bağlantısını kapatır.
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None
        # print("Veritabanı bağlantısı kapatıldı.") # Geliştirme için log

    def _ensure_connection(self):
        """
        Veritabanı bağlantısının ve cursor'ın aktif olup olmadığını kontrol eder.
        Eğer aktif değilse, yeni bir bağlantı kurar.
        """
        if not self.connection or not self.connection.is_connected() or not self.cursor:
            # print("Bağlantı yok veya kapalı, yeniden bağlanılıyor...") # Geliştirme için log
            self.connect()

    # -------------------------------------------------------------------------
    # 2.1.2. Tablo Yönetimi (Table Management)
    # -------------------------------------------------------------------------
    def create_all_tables(self):
        """
        Uygulama için gerekli olan tüm veritabanı tablolarını oluşturur.
        UserRepository ve SpotifyRepository sınıflarını kullanarak tablo oluşturma metotlarını çağırır.
        """
        self._ensure_connection() # Bağlantının olduğundan emin ol
        try:
            user_repo = UserRepository(self) # Mevcut bağlantıyı UserRepository'e ilet
            spotify_repo = SpotifyRepository(self) # Mevcut bağlantıyı SpotifyRepository'e ilet

            user_repo.create_beatify_users_table()
            user_repo.create_beatify_auth_tokens_table()
            spotify_repo.create_spotify_users_table()
            # print("Tüm tablolar başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except Error as e:
            # print(f"Tablo oluşturma sırasında hata: {e}") # Geliştirme için log
            raise
        # Bu metodun kendi bağlantısını kapatmaması gerekir,
        # çünkü bağlantı dışarıdan yönetiliyor olabilir veya başka işlemler için açık kalması gerekebilir.

# =============================================================================
# 3.0 KULLANICI DEPO SINIFI (USER REPOSITORY CLASS)
# =============================================================================
class UserRepository:
    """
    Kullanıcı (beatify_users) ve kimlik doğrulama token'ları (beatify_auth_tokens)
    ile ilgili veritabanı işlemlerini yönetir.
    """
    # -------------------------------------------------------------------------
    # 3.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        UserRepository sınıfının başlatıcı metodu.
        Eğer bir db_connection sağlanmazsa, kendi DatabaseConnection örneğini oluşturur.
        Args:
            db_connection (DatabaseConnection, optional): Kullanılacak veritabanı bağlantısı.
                                                        None ise yeni bir bağlantı oluşturulur.
        """
        if db_connection:
            self.db = db_connection
            self.own_connection = False # Bağlantı dışarıdan sağlandı, bu sınıf kapatmamalı.
        else:
            self.db = DatabaseConnection()
            self.own_connection = True # Bağlantı bu sınıf tarafından oluşturuldu, iş bitince kapatılmalı.

    def _ensure_connection(self):
        """
        Bu repository için veritabanı bağlantısının aktif olmasını sağlar.
        Eğer bağlantı bu sınıf tarafından yönetiliyorsa (own_connection=True) ve kapalıysa açar.
        """
        # self.db zaten DatabaseConnection örneği olduğu için kendi _ensure_connection'ını çağırır.
        self.db._ensure_connection()


    def _close_if_owned(self):
        """
        Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulduysa (own_connection=True),
        bağlantıyı kapatır.
        """
        if self.own_connection:
            self.db.close()

    # -------------------------------------------------------------------------
    # 3.1.2. Tablo Yönetimi (Table Management)
    # -------------------------------------------------------------------------
    def create_beatify_users_table(self):
        """
        `beatify_users` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, Beatify kullanıcılarının temel bilgilerini saklar.
        """
        self._ensure_connection()
        try:
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
            self.db.connection.commit() # Tablo oluşturma işlemi için commit gerekli.
            # print("'beatify_users' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except Error as e:
            # print(f"'beatify_users' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise

    def create_beatify_auth_tokens_table(self):
        """
        `beatify_auth_tokens` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, kullanıcıların kimlik doğrulama token'larını saklar.
        """
        self._ensure_connection()
        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS beatify_auth_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL, /* SQLAlchemy modelinde user_id (INT) idi, burası SQL tanımı */
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    expired_at DATETIME DEFAULT NULL,
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self.db.connection.commit()
            # print("'beatify_auth_tokens' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except Error as e:
            # print(f"'beatify_auth_tokens' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 3.1.3. Kullanıcı Veri İşlemleri (User Data Operations)
    # -------------------------------------------------------------------------
    def beatify_insert_new_user_data(self, username: str, email: str, password_hash: str) -> bool:
        """
        `beatify_users` tablosuna yeni bir kullanıcı kaydı ekler.
        Args:
            username (str): Kullanıcının kullanıcı adı.
            email (str): Kullanıcının e-posta adresi.
            password_hash (str): Kullanıcının şifresinin hashlenmiş hali.
        Returns:
            bool: İşlem başarılıysa True, değilse False (hata durumunda istisna fırlatılır).
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "INSERT INTO beatify_users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Yeni kullanıcı eklenirken hata: {e}") # Geliştirme için log
            if self.db.connection:
                self.db.connection.rollback()
            raise # Hatayı yukarıya fırlat, servis katmanı yakalasın.
        finally:
            self._close_if_owned()

    def beatify_get_user_data(self, username: str) -> Optional[dict]:
        """
        Verilen kullanıcı adına sahip kullanıcının verilerini (şifre hariç) getirir.
        Args:
            username (str): Getirilecek kullanıcının kullanıcı adı.
        Returns:
            Optional[dict]: Kullanıcı bulunursa verilerini içeren bir sözlük, bulunamazsa None.
        """
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
                "created_at": user_data[4].strftime('%Y-%m-%d %H:%M:%S') if isinstance(user_data[4], datetime) else user_data[4],
                "updated_at": user_data[5].strftime('%Y-%m-%d %H:%M:%S') if isinstance(user_data[5], datetime) else user_data[5]
            }
        except Error as e:
            # print(f"Kullanıcı verisi alınırken hata: {e}") # Geliştirme için log
            return None # Hata durumunda None dön, servis katmanı bunu uygun şekilde işleyebilir.
        finally:
            self._close_if_owned()

    def beatify_get_username_or_email_data(self, username: str, email: str) -> Optional[tuple]:
        """
        Verilen kullanıcı adı veya e-posta adresi ile eşleşen bir kullanıcı olup olmadığını kontrol eder.
        Args:
            username (str): Kontrol edilecek kullanıcı adı.
            email (str): Kontrol edilecek e-posta adresi.
        Returns:
            Optional[tuple]: Eşleşen kullanıcı bulunursa (username, email) demeti, bulunamazsa None.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute("SELECT username, email FROM beatify_users WHERE username = %s OR email = %s",
                                (username, email))
            return self.db.cursor.fetchone()
        except Error as e:
            # print(f"Kullanıcı adı/e-posta kontrolü sırasında hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def beatify_get_password_hash_data(self, username: str) -> Optional[str]:
        """
        Verilen kullanıcı adına sahip kullanıcının şifre hash'ini getirir.
        Args:
            username (str): Şifre hash'i getirilecek kullanıcının kullanıcı adı.
        Returns:
            Optional[str]: Kullanıcının şifre hash'i, kullanıcı bulunamazsa None.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT password_hash FROM beatify_users WHERE username = %s",
                (username,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            # print(f"Şifre hash'i alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def beatify_update_spotify_connection_status(self, username: str, status: bool) -> bool:
        """
        Kullanıcının Spotify bağlantı durumunu günceller.
        Args:
            username (str): Durumu güncellenecek kullanıcı.
            status (bool): Yeni bağlantı durumu (True: bağlı, False: bağlı değil).
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE beatify_users SET is_spotify_connected = %s WHERE username = %s",
                (status, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify bağlantı durumu güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()


    # -------------------------------------------------------------------------
    # 3.1.4. Kimlik Doğrulama Token Yönetimi (Auth Token Management)
    # -------------------------------------------------------------------------
    def beatify_insert_or_update_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        """
        Bir kullanıcı için kimlik doğrulama token'ı ekler veya mevcutsa günceller.
        Args:
            username (str): Token'ın ait olduğu kullanıcı adı.
            token (str): Oluşturulan benzersiz token.
            expires_at (datetime): Token'ın son geçerlilik tarihi.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            # expires_at datetime nesnesini MySQL DATETIME formatına çevir
            expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')

            self.db.cursor.execute(
                """
                INSERT INTO beatify_auth_tokens (username, token, expires_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE token = VALUES(token), expires_at = VALUES(expires_at), expired_at = NULL
                """, # expired_at'ı NULL yaparak token'ı yeniden aktif hale getiriyoruz.
                (username, token, expires_at_str)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Auth token eklenirken/güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection:
                self.db.connection.rollback()
            raise # Hatayı yukarıya fırlat
        finally:
            self._close_if_owned()

    def beatify_validate_auth_token(self, token: str) -> Optional[str]:
        """
        Verilen token'ın geçerli olup olmadığını ve hangi kullanıcıya ait olduğunu doğrular.
        Token'ın süresi dolmamış ve `expired_at` alanı NULL olmalıdır.
        Args:
            token (str): Doğrulanacak token.
        Returns:
            Optional[str]: Token geçerliyse kullanıcı adını, değilse None döner.
        """
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
            # print(f"Auth token doğrulanırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def beatify_deactivate_auth_token(self, username: str, token: str) -> bool:
        """
        Belirli bir kullanıcıya ait token'ı geçersiz kılar (`expired_at` alanını günceller).
        Args:
            username (str): Token'ı geçersiz kılınacak kullanıcı.
            token (str): Geçersiz kılınacak token.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s",
                (token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Auth token devre dışı bırakılırken hata: {e}") # Geliştirme için log
            if self.db.connection:
                self.db.connection.rollback()
            raise # Hatayı yukarıya fırlat
        finally:
            self._close_if_owned()

# =============================================================================
# 4.0 SPOTIFY DEPO SINIFI (SPOTIFY REPOSITORY CLASS)
# =============================================================================
class SpotifyRepository:
    """
    Spotify kullanıcı verileri (spotify_users) ile ilgili veritabanı işlemlerini yönetir.
    Bu tablo, Beatify kullanıcılarının bağlı Spotify hesap bilgilerini saklar.
    """
    # -------------------------------------------------------------------------
    # 4.1.1. Başlatıcı Metot ve Bağlantı Yönetimi (Initialization and Connection Management)
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        SpotifyRepository sınıfının başlatıcı metodu.
        Args:
            db_connection (DatabaseConnection, optional): Kullanılacak veritabanı bağlantısı.
                                                        None ise yeni bir bağlantı oluşturulur.
        """
        if db_connection:
            self.db = db_connection
            self.own_connection = False
        else:
            self.db = DatabaseConnection()
            self.own_connection = True

    def _ensure_connection(self):
        """ Bu repository için veritabanı bağlantısının aktif olmasını sağlar. """
        self.db._ensure_connection()

    def _close_if_owned(self):
        """ Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulduysa bağlantıyı kapatır. """
        if self.own_connection:
            self.db.close()

    # -------------------------------------------------------------------------
    # 4.1.2. Tablo Yönetimi (Table Management)
    # -------------------------------------------------------------------------
    def create_spotify_users_table(self):
        """
        `spotify_users` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, Beatify kullanıcılarının Spotify hesap bilgilerini ve token'larını saklar.
        """
        self._ensure_connection()
        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS spotify_users (
                    username VARCHAR(255) PRIMARY KEY, /* Beatify kullanıcısının adı, aynı zamanda yabancı anahtar */
                    spotify_user_id VARCHAR(255) UNIQUE, /* Spotify'daki kullanıcı ID'si, global olarak unique olmalı */
                    client_id VARCHAR(255),
                    client_secret VARCHAR(255),
                    refresh_token VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    widget_token TEXT,
                    design VARCHAR(255) DEFAULT 'standard',
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE
                    /* Orijinal SQL'deki UNIQUE (spotify_user_id, username) yerine spotify_user_id'yi UNIQUE yaptık.
                       Bir Spotify hesabı sadece bir Beatify hesabına bağlanabilmeli.
                       username zaten PK ve FK olduğu için (spotify_user_id, username) kombinasyonu da dolaylı olarak unique olur.
                    */
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self.db.connection.commit()
            # print("'spotify_users' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except Error as e:
            # print(f"'spotify_users' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 4.1.3. Spotify Veri Yönetimi (Spotify Data Management)
    # -------------------------------------------------------------------------
    def spotify_get_user_data(self, username: str) -> Optional[dict]:
        """
        Belirli bir Beatify kullanıcısının bağlı Spotify hesap bilgilerini getirir.
        Args:
            username (str): Bilgileri getirilecek Beatify kullanıcısının adı.
        Returns:
            Optional[dict]: Spotify kullanıcı verilerini içeren sözlük, bulunamazsa None.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """SELECT spotify_user_id, client_id, client_secret, refresh_token, created_at, updated_at, widget_token, design
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
                "created_at": creds[4].strftime('%Y-%m-%d %H:%M:%S') if isinstance(creds[4], datetime) else creds[4],
                "updated_at": creds[5].strftime('%Y-%m-%d %H:%M:%S') if isinstance(creds[5], datetime) else creds[5],
                "widget_token": creds[6],
                "design": creds[7]
            }
        except Error as e:
            # print(f"Spotify kullanıcı verisi alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def spotify_insert_or_update_client_info(self, username: str, client_id: str, client_secret: str) -> bool:
        """
        Bir Beatify kullanıcısı için Spotify Client ID ve Client Secret bilgilerini ekler veya günceller.
        Args:
            username (str): Bilgileri eklenecek/güncellenecek Beatify kullanıcısı.
            client_id (str): Spotify Client ID.
            client_secret (str): Spotify Client Secret.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                INSERT INTO spotify_users (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = VALUES(client_id), client_secret = VALUES(client_secret)
                """,
                (username, client_id, client_secret)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify client bilgileri eklenirken/güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    def spotify_update_user_connection_info(self, username: str, spotify_user_id: str, refresh_token: str) -> bool:
        """
        Kullanıcının Spotify bağlantı bilgilerini (spotify_user_id, refresh_token) günceller.
        Bu metot genellikle Spotify OAuth akışı tamamlandığında çağrılır.
        Aynı zamanda beatify_users tablosundaki is_spotify_connected durumunu True yapar.
        Args:
            username (str): Beatify kullanıcısının adı.
            spotify_user_id (str): Kullanıcının Spotify'daki ID'si.
            refresh_token (str): Spotify'dan alınan refresh token.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            # spotify_users tablosuna ekleme veya güncelleme
            self.db.cursor.execute(
                """
                INSERT INTO spotify_users (username, spotify_user_id, refresh_token)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spotify_user_id = VALUES(spotify_user_id), refresh_token = VALUES(refresh_token)
                """,
                (username, spotify_user_id, refresh_token)
            )

            # beatify_users tablosunda bağlantı durumunu güncelle
            user_repo = UserRepository(self.db) # Mevcut bağlantıyı kullan
            user_repo.beatify_update_spotify_connection_status(username, True)
            # user_repo._close_if_owned() çağrılmamalı çünkü bağlantı bu scope'a ait değil.

            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify kullanıcı bağlantı bilgileri güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned() # Sadece SpotifyRepository'nin kendi bağlantısı varsa kapatır.

    def spotify_delete_linked_account_data(self, username: str) -> bool:
        """
        Bir Beatify kullanıcısının bağlı Spotify hesap bilgilerini siler (refresh_token, spotify_user_id null yapılır).
        Ayrıca beatify_users tablosundaki is_spotify_connected durumunu False yapar.
        Args:
            username (str): Bağlantısı kesilecek Beatify kullanıcısının adı.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            # spotify_users tablosundaki ilgili alanları NULL yap
            self.db.cursor.execute(
                """
                UPDATE spotify_users
                SET spotify_user_id = NULL, refresh_token = NULL, widget_token = NULL
                WHERE username = %s
                """,
                (username,)
            )
            # Not: client_id ve client_secret bilgileri genellikle kullanıcı tarafından tekrar girilebileceği için silinmeyebilir.
            # Eğer tamamen silinmesi isteniyorsa: DELETE FROM spotify_users WHERE username = %s

            # beatify_users tablosunda bağlantı durumunu güncelle
            user_repo = UserRepository(self.db) # Mevcut bağlantıyı kullan
            user_repo.beatify_update_spotify_connection_status(username, False)

            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify bağlantısı kesilirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.4. Token Yönetimi (Spotify Token Management - Refresh Token)
    # -------------------------------------------------------------------------
    def spotify_update_refresh_token_data(self, username: str, new_refresh_token: str) -> bool:
        """
        Bir kullanıcının Spotify refresh token'ını günceller.
        Args:
            username (str): Token'ı güncellenecek Beatify kullanıcısı.
            new_refresh_token (str): Yeni Spotify refresh token.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                """
                UPDATE spotify_users
                SET refresh_token = %s
                WHERE username = %s
                """,
                (new_refresh_token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify refresh token güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.5. Widget Yönetimi (Spotify Widget Management)
    # -------------------------------------------------------------------------
    def spotify_store_widget_token_data(self, username: str, token: str) -> bool:
        """
        Kullanıcının Spotify widget token'ını veritabanında saklar/günceller.
        Args:
            username (str): Token'ı saklanacak Beatify kullanıcısı.
            token (str): Spotify widget token'ı.
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE spotify_users SET widget_token = %s WHERE username = %s",
                (token, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify widget token saklanırken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    def spotify_get_widget_token_data(self, username: str) -> Optional[str]:
        """
        Belirli bir Beatify kullanıcısının Spotify widget token'ını getirir.
        Args:
            username (str): Token'ı getirilecek Beatify kullanıcısı.
        Returns:
            Optional[str]: Widget token, bulunamazsa None.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT widget_token FROM spotify_users WHERE username = %s",
                (username,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            # print(f"Spotify widget token alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def spotify_get_username_by_widget_token_data(self, token: str) -> Optional[str]:
        """
        Verilen widget token'ına sahip Beatify kullanıcısının adını getirir.
        Args:
            token (str): Aranacak widget token.
        Returns:
            Optional[str]: Kullanıcı adı, bulunamazsa None.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "SELECT username FROM spotify_users WHERE widget_token = %s",
                (token,)
            )
            result = self.db.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            # print(f"Widget token ile kullanıcı adı alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    def spotify_update_widget_design(self, username: str, design: str) -> bool:
        """
        Kullanıcının Spotify widget tasarım tercihini günceller.
        Args:
            username (str): Tasarımı güncellenecek Beatify kullanıcısı.
            design (str): Yeni widget tasarımı (örn: 'standard', 'compact').
        Returns:
            bool: İşlem başarılıysa True.
        """
        try:
            self._ensure_connection()
            self.db.cursor.execute(
                "UPDATE spotify_users SET design = %s WHERE username = %s",
                (design, username)
            )
            self.db.connection.commit()
            return True
        except Error as e:
            # print(f"Spotify widget tasarımı güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection: self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()
