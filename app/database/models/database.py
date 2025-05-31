# =============================================================================
# Veritabanı Yönetim Modülü (Database Management Module)
# =============================================================================
# Bu modül, uygulama için veritabanı bağlantısı, tablo oluşturma
# ve veri erişim işlemlerini (repository pattern kullanarak) yönetir.
# MySQL veritabanı ile etkileşim kurar ve kullanıcı, kimlik doğrulama
# tokenları ve Spotify entegrasyon verileri için depolar (repository) içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modüllerinin, tiplerinin ve yapılandırmaların içe aktarılması.
# 2.0  VERİTABANI BAĞLANTI SINIFI (DATABASE CONNECTION CLASS)
#      2.1. DatabaseConnection
#           : MySQL veritabanı ile bağlantı kurma ve yönetme işlemlerini üstlenir.
#           2.1.1. __init__                        : Başlatıcı metot, bağlantı ve cursor nesnelerini başlatır.
#           2.1.2. connect                         : Veritabanına bağlanır ve cursor oluşturur.
#           2.1.3. close                           : Açık cursor ve veritabanı bağlantısını kapatır.
#           2.1.4. _ensure_connection              : Bağlantının ve cursor'ın aktif olup olmadığını kontrol eder, gerekirse yeniden bağlanır.
#           2.1.5. create_all_tables               : Uygulama için gerekli tüm veritabanı tablolarını oluşturur.
# 3.0  KULLANICI DEPO SINIFI (USER REPOSITORY CLASS)
#      3.1. UserRepository
#           : Kullanıcı (beatify_users) ve kimlik doğrulama token'ları (beatify_auth_tokens)
#             ile ilgili veritabanı işlemlerini yönetir.
#           3.1.1.  __init__                               : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
#           3.1.2.  _ensure_connection                     : Bu depo için veritabanı bağlantısının aktif olmasını sağlar.
#           3.1.3.  _close_if_owned                        : Bağlantı bu sınıf tarafından oluşturulduysa kapatır.
#           3.1.4.  create_beatify_users_table             : `beatify_users` tablosunu oluşturur.
#           3.1.5.  create_beatify_auth_tokens_table       : `beatify_auth_tokens` tablosunu oluşturur.
#           3.1.6.  beatify_insert_new_user_data           : Yeni bir kullanıcı kaydı ekler.
#           3.1.7.  beatify_get_user_data                  : Kullanıcı verilerini (şifre hariç) getirir.
#           3.1.8.  beatify_get_username_or_email_data     : Kullanıcı adı veya e-posta ile eşleşen kullanıcıyı kontrol eder.
#           3.1.9.  beatify_get_password_hash_data         : Kullanıcının şifre hash'ini getirir.
#           3.1.10. beatify_update_spotify_connection_status : Kullanıcının Spotify bağlantı durumunu günceller.
#           3.1.11. beatify_insert_or_update_auth_token    : Kimlik doğrulama token'ı ekler veya günceller.
#           3.1.12. beatify_validate_auth_token            : Verilen token'ın geçerliliğini doğrular.
#           3.1.13. beatify_deactivate_auth_token          : Belirli bir kullanıcıya ait token'ı geçersiz kılar.
# 4.0  SPOTIFY DEPO SINIFI (SPOTIFY REPOSITORY CLASS)
#      4.1. SpotifyRepository
#           : Spotify kullanıcı verileri (spotify_users) ile ilgili veritabanı işlemlerini yönetir.
#           4.1.1.  __init__                                 : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
#           4.1.2.  _ensure_connection                       : Bu depo için veritabanı bağlantısının aktif olmasını sağlar.
#           4.1.3.  _close_if_owned                          : Bağlantı bu sınıf tarafından oluşturulduysa kapatır.
#           4.1.4.  create_spotify_users_table               : `spotify_users` tablosunu oluşturur.
#           4.1.5.  spotify_get_user_data                    : Belirli bir kullanıcının bağlı Spotify hesap bilgilerini getirir.
#           4.1.6.  spotify_insert_or_update_client_info     : Spotify Client ID ve Secret bilgilerini ekler/günceller.
#           4.1.7.  spotify_update_user_connection_info    : Kullanıcının Spotify bağlantı bilgilerini günceller.
#           4.1.8.  spotify_delete_linked_account_data       : Bağlı Spotify hesap bilgilerini siler/sıfırlar.
#           4.1.9.  spotify_update_refresh_token_data        : Spotify refresh token'ını günceller.
#           4.1.10. spotify_store_widget_token_data          : Spotify widget token'ını saklar/günceller.
#           4.1.11. spotify_get_widget_token_data            : Spotify widget token'ını getirir.
#           4.1.12. spotify_get_username_by_widget_token_data: Widget token'ına sahip kullanıcının adını getirir.
#           4.1.13. spotify_update_widget_design             : Kullanıcının Spotify widget tasarım tercihini günceller.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import mysql.connector
from mysql.connector import Error as MySQLError # Hata sınıfını daha belirgin hale getirelim
from datetime import datetime, timedelta
from app.config import DB_CONFIG # Uygulama yapılandırmasından veritabanı ayarlarını alır
from typing import Optional, Dict, Any, Tuple, List # Gerekli tipler

# =============================================================================
# 2.0 VERİTABANI BAĞLANTI SINIFI (DATABASE CONNECTION CLASS)
# =============================================================================
class DatabaseConnection:
    """
    MySQL veritabanı ile bağlantı kurma ve yönetme işlemlerini üstlenir.
    Bu sınıf, bağlantı havuzu yerine doğrudan bağlantı açma ve kapama
    mantığıyla çalışır. Her repository sınıfı, bu sınıftan bir örnek
    kullanarak veya kendi örneğini oluşturarak veritabanı işlemlerini gerçekleştirir.
    """
    # -------------------------------------------------------------------------
    # 2.1.1. __init__ : Başlatıcı metot, bağlantı ve cursor nesnelerini başlatır.
    # -------------------------------------------------------------------------
    def __init__(self):
        """
        DatabaseConnection sınıfının başlatıcı metodu.
        Bağlantı ve cursor nesnelerini None olarak başlatır,
        veritabanı yapılandırmasını `DB_CONFIG` üzerinden alır.
        """
        self.connection: Optional[mysql.connector.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None
        self.db_config: Dict[str, Any] = DB_CONFIG
        # print(f"DatabaseConnection örneği oluşturuldu. Yapılandırma: {self.db_config}") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 2.1.2. connect : Veritabanına bağlanır ve cursor oluşturur.
    # -------------------------------------------------------------------------
    def connect(self):
        """
        Yapılandırma bilgilerini kullanarak MySQL veritabanına bağlanır.
        Başarılı bağlantıda bir cursor oluşturur.
        Hata durumunda `MySQLError` istisnası fırlatır.
        """
        try:
            # print("Veritabanına bağlanmaya çalışılıyor...") # Geliştirme için log
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True) # Sonuçları sözlük olarak almak için
                # print("Veritabanına başarıyla bağlanıldı ve cursor oluşturuldu.") # Geliştirme için log
            else:
                # print("Bağlantı kuruldu ancak aktif değil.") # Geliştirme için log
                raise MySQLError("Veritabanı bağlantısı kuruldu ancak aktif değil.")
        except MySQLError as e:
            # print(f"Veritabanı bağlantı hatası: {e}") # Geliştirme için log
            self.connection = None # Hata durumunda bağlantıyı None yap
            self.cursor = None     # Hata durumunda cursor'ı None yap
            raise # Hatayı yukarı katmana ilet

    # -------------------------------------------------------------------------
    # 2.1.3. close : Açık cursor ve veritabanı bağlantısını kapatır.
    # -------------------------------------------------------------------------
    def close(self):
        """
        Açık olan cursor ve veritabanı bağlantısını güvenli bir şekilde kapatır.
        """
        # print("Veritabanı bağlantısı kapatılıyor...") # Geliştirme için log
        if self.cursor:
            try:
                self.cursor.close()
                # print("Cursor kapatıldı.") # Geliştirme için log
            except MySQLError as e:
                # print(f"Cursor kapatılırken hata: {e}") # Geliştirme için log
                pass # Kapatma sırasında oluşabilecek hataları yoksayabiliriz
            self.cursor = None
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                # print("Veritabanı bağlantısı kapatıldı.") # Geliştirme için log
            except MySQLError as e:
                # print(f"Bağlantı kapatılırken hata: {e}") # Geliştirme için log
                pass # Kapatma sırasında oluşabilecek hataları yoksayabiliriz
            self.connection = None

    # -------------------------------------------------------------------------
    # 2.1.4. _ensure_connection : Bağlantının ve cursor'ın aktif olup olmadığını
    #                             kontrol eder, gerekirse yeniden bağlanır.
    # -------------------------------------------------------------------------
    def _ensure_connection(self):
        """
        Veritabanı bağlantısının ve cursor'ın aktif olup olmadığını kontrol eder.
        Eğer bağlantı yoksa, kapalıysa veya cursor yoksa, `connect` metodunu çağırarak
        yeni bir bağlantı kurar.
        """
        if not self.connection or not self.connection.is_connected() or not self.cursor:
            # print("Bağlantı yok veya kapalı/cursor yok, yeniden bağlanılıyor...") # Geliştirme için log
            self.connect() # Yeniden bağlanmayı dene

    # -------------------------------------------------------------------------
    # 2.1.5. create_all_tables : Uygulama için gerekli tüm veritabanı tablolarını oluşturur.
    # -------------------------------------------------------------------------
    def create_all_tables(self):
        """
        Uygulama için gerekli olan tüm veritabanı tablolarını oluşturur.
        Bu metot, `UserRepository` ve `SpotifyRepository` sınıflarının
        tablo oluşturma metotlarını çağırır.
        İşlem sırasında bir hata oluşursa, istisna fırlatır.
        """
        self._ensure_connection() # Bağlantının olduğundan emin ol
        # print("Tüm tablolar oluşturuluyor...") # Geliştirme için log
        try:
            # Bu metot içinde repository örnekleri oluşturulurken, mevcut bağlantıyı (self)
            # bu örneklere iletmek, aynı bağlantı üzerinden tüm işlemlerin yapılmasını sağlar.
            user_repo = UserRepository(db_connection=self)
            spotify_repo = SpotifyRepository(db_connection=self)

            # print("UserRepository tabloları oluşturuluyor...") # Geliştirme için log
            user_repo.create_beatify_users_table()
            user_repo.create_beatify_auth_tokens_table()

            # print("SpotifyRepository tabloları oluşturuluyor...") # Geliştirme için log
            spotify_repo.create_spotify_users_table()

            # print("Tüm tablolar başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except MySQLError as e:
            # print(f"Tablo oluşturma sırasında genel hata: {e}") # Geliştirme için log
            # Bu metot kendi bağlantısını yönetmediği için rollback burada yapılmaz,
            # çağıran yer veya repository kendi içinde rollback yapmalı.
            raise
        # Bu metot, global bir tablo oluşturma işlevi gördüğü için,
        # kendi bağlantısını kapatmamalıdır. Bağlantı yönetimi,
        # bu metodu çağıran veya DatabaseConnection örneğini oluşturan
        # üst katmana aittir.

# =============================================================================
# 3.0 KULLANICI DEPO SINIFI (USER REPOSITORY CLASS)
# =============================================================================
class UserRepository:
    """
    Kullanıcı (`beatify_users`) ve kimlik doğrulama token'ları (`beatify_auth_tokens`)
    ile ilgili veritabanı işlemlerini yönetir (CRUD operasyonları).
    Repository pattern'ı uygular.
    """
    # -------------------------------------------------------------------------
    # 3.1.1. __init__ : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        UserRepository sınıfının başlatıcı metodu.
        Eğer bir `db_connection` sağlanırsa onu kullanır, aksi takdirde
        yeni bir `DatabaseConnection` örneği oluşturur ve yönetir.

        Args:
            db_connection (DatabaseConnection, optional): Kullanılacak veritabanı bağlantısı.
                                                        None ise yeni bir bağlantı oluşturulur.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False # Bağlantı dışarıdan sağlandı, bu sınıf kapatmamalı.
            # print("UserRepository dışarıdan sağlanan DatabaseConnection kullanıyor.") # Geliştirme için log
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True # Bağlantı bu sınıf tarafından oluşturuldu, iş bitince kapatılmalı.
            # print("UserRepository kendi DatabaseConnection örneğini oluşturdu.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 3.1.2. _ensure_connection : Bu depo için veritabanı bağlantısının aktif olmasını sağlar.
    # -------------------------------------------------------------------------
    def _ensure_connection(self):
        """
        Bu repository için veritabanı bağlantısının aktif olmasını sağlar.
        `self.db` (DatabaseConnection örneği) üzerinden `_ensure_connection` metodunu çağırır.
        """
        # print("UserRepository: Bağlantı kontrol ediliyor...") # Geliştirme için log
        self.db._ensure_connection()

    # -------------------------------------------------------------------------
    # 3.1.3. _close_if_owned : Bağlantı bu sınıf tarafından oluşturulduysa kapatır.
    # -------------------------------------------------------------------------
    def _close_if_owned(self):
        """
        Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulduysa (`self.own_connection` True ise),
        bağlantıyı kapatır. Dışarıdan sağlanan bağlantıları kapatmaz.
        """
        if self.own_connection:
            # print("UserRepository: Kendine ait bağlantı kapatılıyor.") # Geliştirme için log
            self.db.close()
        # else:
            # print("UserRepository: Dışarıdan sağlanan bağlantı, kapatılmayacak.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 3.1.4. create_beatify_users_table : `beatify_users` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_beatify_users_table(self):
        """
        `beatify_users` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, Beatify kullanıcılarının temel bilgilerini saklar.
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        # print("`beatify_users` tablosu oluşturuluyor/kontrol ediliyor...") # Geliştirme için log
        try:
            query = """
                CREATE TABLE IF NOT EXISTS beatify_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_spotify_connected BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            self.db.cursor.execute(query)
            self.db.connection.commit() # Tablo oluşturma işlemi için commit gerekli.
            # print("'beatify_users' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except MySQLError as e:
            # print(f"'beatify_users' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback() # Hata durumunda işlemi geri al
            raise

    # -------------------------------------------------------------------------
    # 3.1.5. create_beatify_auth_tokens_table : `beatify_auth_tokens` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_beatify_auth_tokens_table(self):
        """
        `beatify_auth_tokens` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, kullanıcıların kimlik doğrulama token'larını saklar.
        Hata durumunda `MySQLError` fırlatır.
        """
        self._ensure_connection()
        # print("`beatify_auth_tokens` tablosu oluşturuluyor/kontrol ediliyor...") # Geliştirme için log
        try:
            query = """
                CREATE TABLE IF NOT EXISTS beatify_auth_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    expired_at DATETIME DEFAULT NULL,
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            self.db.cursor.execute(query)
            self.db.connection.commit()
            # print("'beatify_auth_tokens' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except MySQLError as e:
            # print(f"'beatify_auth_tokens' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 3.1.6. beatify_insert_new_user_data : Yeni bir kullanıcı kaydı ekler.
    # -------------------------------------------------------------------------
    def beatify_insert_new_user_data(self, username: str, email: str, password_hash: str) -> int:
        """
        `beatify_users` tablosuna yeni bir kullanıcı kaydı ekler.

        Args:
            username (str): Kullanıcının kullanıcı adı.
            email (str): Kullanıcının e-posta adresi.
            password_hash (str): Kullanıcının şifresinin hashlenmiş hali.

        Returns:
            int: Eklenen kullanıcının ID'si.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Yeni kullanıcı ekleniyor: {username}, {email}") # Geliştirme için log
        try:
            query = "INSERT INTO beatify_users (username, email, password_hash) VALUES (%s, %s, %s)"
            values = (username, email, password_hash)
            self.db.cursor.execute(query, values)
            self.db.connection.commit()
            user_id = self.db.cursor.lastrowid # Eklenen son satırın ID'sini al
            # print(f"Yeni kullanıcı başarıyla eklendi. ID: {user_id}") # Geliştirme için log
            return user_id
        except MySQLError as e:
            # print(f"Yeni kullanıcı eklenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.7. beatify_get_user_data : Kullanıcı verilerini (şifre hariç) getirir.
    # -------------------------------------------------------------------------
    def beatify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Verilen kullanıcı adına sahip kullanıcının verilerini (şifre hash'i hariç) getirir.

        Args:
            username (str): Getirilecek kullanıcının kullanıcı adı.

        Returns:
            Optional[Dict[str, Any]]: Kullanıcı bulunursa verilerini içeren bir sözlük,
                                      bulunamazsa None.
        """
        self._ensure_connection()
        # print(f"Kullanıcı verisi alınıyor: {username}") # Geliştirme için log
        try:
            query = """
                SELECT id, username, email, is_spotify_connected, created_at, updated_at
                FROM beatify_users
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            user_data_row = self.db.cursor.fetchone() # fetchone() zaten sözlük dönecek (dictionary=True)

            if not user_data_row:
                # print(f"Kullanıcı bulunamadı: {username}") # Geliştirme için log
                return None
            
            # Tarih alanlarını string formatına çevirme (isteğe bağlı, API yanıtları için kullanışlı olabilir)
            if isinstance(user_data_row.get('created_at'), datetime):
                user_data_row['created_at'] = user_data_row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(user_data_row.get('updated_at'), datetime):
                user_data_row['updated_at'] = user_data_row['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # print(f"Kullanıcı verisi başarıyla alındı: {user_data_row}") # Geliştirme için log
            return user_data_row
        except MySQLError as e:
            # print(f"Kullanıcı verisi alınırken hata ({username}): {e}") # Geliştirme için log
            return None # Hata durumunda None dön, servis katmanı bunu uygun şekilde işleyebilir.
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.8. beatify_get_username_or_email_data : Kullanıcı adı veya e-posta ile
    #                                             eşleşen kullanıcıyı kontrol eder.
    # -------------------------------------------------------------------------
    def beatify_get_username_or_email_data(self, username: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Verilen kullanıcı adı veya e-posta adresi ile eşleşen bir kullanıcı olup olmadığını kontrol eder.
        Sadece varlık kontrolü için değil, eşleşen kullanıcının temel bilgilerini de döndürür.

        Args:
            username (str): Kontrol edilecek kullanıcı adı.
            email (str): Kontrol edilecek e-posta adresi.

        Returns:
            Optional[Dict[str, Any]]: Eşleşen kullanıcı bulunursa verilerini içeren bir sözlük,
                                      bulunamazsa None.
        """
        self._ensure_connection()
        # print(f"Kullanıcı adı ({username}) veya e-posta ({email}) kontrol ediliyor...") # Geliştirme için log
        try:
            query = "SELECT id, username, email FROM beatify_users WHERE username = %s OR email = %s"
            self.db.cursor.execute(query, (username, email))
            user_data = self.db.cursor.fetchone()
            # if user_data:
                # print(f"Eşleşen kullanıcı bulundu: {user_data}") # Geliştirme için log
            # else:
                # print("Eşleşen kullanıcı bulunamadı.") # Geliştirme için log
            return user_data
        except MySQLError as e:
            # print(f"Kullanıcı adı/e-posta kontrolü sırasında hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.9. beatify_get_password_hash_data : Kullanıcının şifre hash'ini getirir.
    # -------------------------------------------------------------------------
    def beatify_get_password_hash_data(self, username: str) -> Optional[str]:
        """
        Verilen kullanıcı adına sahip kullanıcının şifre hash'ini getirir.

        Args:
            username (str): Şifre hash'i getirilecek kullanıcının kullanıcı adı.

        Returns:
            Optional[str]: Kullanıcının şifre hash'i, kullanıcı bulunamazsa None.
        """
        self._ensure_connection()
        # print(f"Şifre hash'i alınıyor: {username}") # Geliştirme için log
        try:
            query = "SELECT password_hash FROM beatify_users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            password_hash = result['password_hash'] if result else None
            # if password_hash:
                # print(f"Şifre hash'i bulundu.") # Geliştirme için log (hash'i loglama)
            # else:
                # print(f"Kullanıcı ({username}) için şifre hash'i bulunamadı.") # Geliştirme için log
            return password_hash
        except MySQLError as e:
            # print(f"Şifre hash'i ({username}) alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.10. beatify_update_spotify_connection_status : Kullanıcının Spotify
    #                                                   bağlantı durumunu günceller.
    # -------------------------------------------------------------------------
    def beatify_update_spotify_connection_status(self, username: str, status: bool) -> bool:
        """
        Kullanıcının `beatify_users` tablosundaki Spotify bağlantı durumunu (`is_spotify_connected`) günceller.

        Args:
            username (str): Durumu güncellenecek kullanıcı.
            status (bool): Yeni bağlantı durumu (True: bağlı, False: bağlı değil).

        Returns:
            bool: İşlem başarılıysa True, etkilenen satır yoksa False.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify bağlantı durumu güncelleniyor: {username}, Durum: {status}") # Geliştirme için log
        try:
            query = "UPDATE beatify_users SET is_spotify_connected = %s WHERE username = %s"
            self.db.cursor.execute(query, (status, username))
            self.db.connection.commit()
            updated_rows = self.db.cursor.rowcount
            # print(f"Spotify bağlantı durumu güncellendi. Etkilenen satır sayısı: {updated_rows}") # Geliştirme için log
            return updated_rows > 0
        except MySQLError as e:
            # print(f"Spotify bağlantı durumu ({username}) güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            # Bu metot genellikle başka bir repository metodu içinden çağrılır (SpotifyRepository),
            # bu yüzden bağlantıyı burada kapatmamak daha doğru olabilir eğer dışarıdan yönetiliyorsa.
            # Ancak _close_if_owned zaten bu kontrolü yapıyor.
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.11. beatify_insert_or_update_auth_token : Kimlik doğrulama token'ı ekler veya günceller.
    # -------------------------------------------------------------------------
    def beatify_insert_or_update_auth_token(self, username: str, token: str, expires_at: datetime) -> bool:
        """
        Bir kullanıcı için `beatify_auth_tokens` tablosuna kimlik doğrulama token'ı ekler
        veya mevcutsa günceller (ON DUPLICATE KEY UPDATE kullanarak).

        Args:
            username (str): Token'ın ait olduğu kullanıcı adı.
            token (str): Oluşturulan benzersiz token.
            expires_at (datetime): Token'ın son geçerlilik tarihi.

        Returns:
            bool: İşlem başarılıysa True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S') # MySQL DATETIME formatı
        # print(f"Auth token ekleniyor/güncelleniyor: Kullanıcı: {username}, Token: {token[:10]}..., Bitiş: {expires_at_str}") # Geliştirme için log
        try:
            # Eğer aynı kullanıcı için eski bir token varsa, onu güncellemek yerine
            # ON DUPLICATE KEY UPDATE token = VALUES(token) ... daha mantıklı.
            # Eğer token UNIQUE olduğu için farklı bir kullanıcı aynı token'ı alamaz.
            # Bir kullanıcı için birden fazla aktif token olmaması için,
            # username üzerinde UNIQUE bir kısıtlama yoksa, bu mantık bir kullanıcıya
            # birden fazla token atayabilir. Mevcut tabloda token UNIQUE.
            # Bu durumda, eğer kullanıcı için zaten bir token varsa ve yeni bir token
            # veriliyorsa, eski token'ın `expired_at` alanı güncellenerek pasifize edilebilir
            # veya bu metot sadece yeni token ekleyip/güncelleyebilir.
            # Mevcut SQL: Eğer aynı `token` değeri varsa günceller, bu pek olası değil.
            # Eğer aynı `username` için yeni bir token veriliyorsa, eski token'ı silip yenisini eklemek
            # veya `ON DUPLICATE KEY UPDATE` ile `username`'i primary/unique key yapıp
            # o kullanıcıya ait token'ı güncellemek gerekir.
            # Mevcut `beatify_auth_tokens` tablosunda `token` UNIQUE. Bu yüzden
            # `ON DUPLICATE KEY UPDATE` `token` üzerinden çalışır.
            # Eğer amaç kullanıcı başına tek aktif token ise, `username` üzerinde de bir
            # unique kısıtlama (veya primary key olarak `username`) ve `ON DUPLICATE KEY UPDATE`
            # bu anahtar üzerinden yapılmalı.
            # Şimdiki haliyle, eğer aynı token değeriyle (çok düşük ihtimal) bir kayıt varsa onu günceller.
            # Asıl senaryo yeni bir token eklemek.
            query = """
                INSERT INTO beatify_auth_tokens (username, token, expires_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE expires_at = VALUES(expires_at), expired_at = NULL
            """
            # Yukarıdaki ON DUPLICATE KEY UPDATE, eğer token (UNIQUE) zaten varsa,
            # o token'ın expires_at ve expired_at alanlarını günceller.
            # Bu genellikle istenen davranış değildir. Genelde yeni bir token oluşturulur.
            # Eğer amaç, bir kullanıcıya yeni bir token verildiğinde eskisini geçersiz kılmaksa,
            # bu işlem servis katmanında yönetilmeli (önce deactivate, sonra insert).
            # Veya `username`'i UNIQUE yapıp, ON DUPLICATE KEY UPDATE ile o kullanıcıya ait token'ı
            # ve expires_at'ı güncellemek daha mantıklı olabilir.
            # Şimdilik basit insert yapalım, çakışma olursa hata verecektir (token UNIQUE olduğu için).
            # Eğer bir kullanıcıya yeni token verilirken eski token'ı güncellemek isteniyorsa:
            # Önce eski token'ı bulup `expired_at` set et, sonra yeni token'ı insert et.
            # Ya da, `username`'i `beatify_auth_tokens`'da UNIQUE yapıp:
            # INSERT INTO beatify_auth_tokens (username, token, expires_at) VALUES (%s, %s, %s)
            # ON DUPLICATE KEY UPDATE token = VALUES(token), expires_at = VALUES(expires_at), expired_at = NULL;
            # Bu, her kullanıcı için sadece bir aktif token olmasını sağlar.
            # Mevcut tablo tanımında `username` FOREIGN KEY ama UNIQUE değil.
            # Bu yüzden `ON DUPLICATE KEY` `token` üzerinden çalışır.

            # Basit insert:
            simple_insert_query = """
            INSERT INTO beatify_auth_tokens (username, token, expires_at)
            VALUES (%s, %s, %s)
            """
            self.db.cursor.execute(simple_insert_query, (username, token, expires_at_str))
            self.db.connection.commit()
            # print("Auth token başarıyla eklendi.") # Geliştirme için log
            return True
        except MySQLError as e:
            # print(f"Auth token eklenirken/güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.12. beatify_validate_auth_token : Verilen token'ın geçerliliğini doğrular.
    # -------------------------------------------------------------------------
    def beatify_validate_auth_token(self, token: str) -> Optional[str]:
        """
        Verilen token'ın `beatify_auth_tokens` tablosunda geçerli olup olmadığını
        (süresi dolmamış ve `expired_at` alanı NULL) ve hangi kullanıcıya ait olduğunu doğrular.

        Args:
            token (str): Doğrulanacak token.

        Returns:
            Optional[str]: Token geçerliyse kullanıcı adını (`username`), değilse None döner.
        """
        self._ensure_connection()
        # print(f"Auth token doğrulanıyor: {token[:10]}...") # Geliştirme için log
        try:
            query = """
                SELECT username
                FROM beatify_auth_tokens
                WHERE token = %s AND expires_at > NOW() AND expired_at IS NULL
            """
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            username = result['username'] if result else None
            # if username:
                # print(f"Auth token geçerli. Kullanıcı: {username}") # Geliştirme için log
            # else:
                # print("Auth token geçersiz veya süresi dolmuş.") # Geliştirme için log
            return username
        except MySQLError as e:
            # print(f"Auth token doğrulanırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 3.1.13. beatify_deactivate_auth_token : Belirli bir kullanıcıya ait token'ı geçersiz kılar.
    # -------------------------------------------------------------------------
    def beatify_deactivate_auth_token(self, username: str, token: str) -> bool:
        """
        Belirli bir kullanıcıya ait token'ı geçersiz kılar (`expired_at` alanını şu anki zamanla günceller).

        Args:
            username (str): Token'ı geçersiz kılınacak kullanıcı.
            token (str): Geçersiz kılınacak token.

        Returns:
            bool: İşlem başarılıysa ve en az bir satır etkilendiyse True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Auth token devre dışı bırakılıyor: Kullanıcı: {username}, Token: {token[:10]}...") # Geliştirme için log
        try:
            query = "UPDATE beatify_auth_tokens SET expired_at = NOW() WHERE token = %s AND username = %s AND expired_at IS NULL"
            self.db.cursor.execute(query, (token, username))
            self.db.connection.commit()
            updated_rows = self.db.cursor.rowcount
            # print(f"Auth token devre dışı bırakıldı. Etkilenen satır: {updated_rows}") # Geliştirme için log
            return updated_rows > 0
        except MySQLError as e:
            # print(f"Auth token ({username}, {token[:10]}) devre dışı bırakılırken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# 4.0 SPOTIFY DEPO SINIFI (SPOTIFY REPOSITORY CLASS)
# =============================================================================
class SpotifyRepository:
    """
    Spotify kullanıcı verileri (`spotify_users`) ile ilgili veritabanı işlemlerini yönetir.
    Bu tablo, Beatify kullanıcılarının bağlı Spotify hesap bilgilerini (tokenlar, widget ayarları vb.) saklar.
    Repository pattern'ı uygular.
    """
    # -------------------------------------------------------------------------
    # 4.1.1. __init__ : Başlatıcı metot, veritabanı bağlantısını alır veya oluşturur.
    # -------------------------------------------------------------------------
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """
        SpotifyRepository sınıfının başlatıcı metodu.
        Eğer bir `db_connection` sağlanırsa onu kullanır, aksi takdirde
        yeni bir `DatabaseConnection` örneği oluşturur ve yönetir.

        Args:
            db_connection (DatabaseConnection, optional): Kullanılacak veritabanı bağlantısı.
        """
        if db_connection:
            self.db: DatabaseConnection = db_connection
            self.own_connection: bool = False
            # print("SpotifyRepository dışarıdan sağlanan DatabaseConnection kullanıyor.") # Geliştirme için log
        else:
            self.db: DatabaseConnection = DatabaseConnection()
            self.own_connection: bool = True
            # print("SpotifyRepository kendi DatabaseConnection örneğini oluşturdu.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 4.1.2. _ensure_connection : Bu depo için veritabanı bağlantısının aktif olmasını sağlar.
    # -------------------------------------------------------------------------
    def _ensure_connection(self):
        """ Bu repository için veritabanı bağlantısının aktif olmasını sağlar. """
        # print("SpotifyRepository: Bağlantı kontrol ediliyor...") # Geliştirme için log
        self.db._ensure_connection()

    # -------------------------------------------------------------------------
    # 4.1.3. _close_if_owned : Bağlantı bu sınıf tarafından oluşturulduysa kapatır.
    # -------------------------------------------------------------------------
    def _close_if_owned(self):
        """ Eğer veritabanı bağlantısı bu sınıf tarafından oluşturulduysa bağlantıyı kapatır. """
        if self.own_connection:
            # print("SpotifyRepository: Kendine ait bağlantı kapatılıyor.") # Geliştirme için log
            self.db.close()
        # else:
            # print("SpotifyRepository: Dışarıdan sağlanan bağlantı, kapatılmayacak.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 4.1.4. create_spotify_users_table : `spotify_users` tablosunu oluşturur.
    # -------------------------------------------------------------------------
    def create_spotify_users_table(self):
        """
        `spotify_users` tablosunu oluşturur (eğer mevcut değilse).
        Bu tablo, Beatify kullanıcılarının Spotify hesap bilgilerini ve token'larını saklar.
        `username` (Beatify kullanıcısı) PRIMARY KEY ve `beatify_users` tablosuna FOREIGN KEY'dir.
        `spotify_user_id` (Spotify kullanıcısı) UNIQUE olmalıdır.

        Raises:
            MySQLError: Tablo oluşturma sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print("`spotify_users` tablosu oluşturuluyor/kontrol ediliyor...") # Geliştirme için log
        try:
            query = """
                CREATE TABLE IF NOT EXISTS spotify_users (
                    username VARCHAR(255) PRIMARY KEY,
                    spotify_user_id VARCHAR(255) UNIQUE,
                    client_id VARCHAR(255) DEFAULT NULL,
                    client_secret VARCHAR(255) DEFAULT NULL,
                    refresh_token TEXT DEFAULT NULL, /* Refresh token uzun olabilir */
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    widget_token TEXT DEFAULT NULL, /* Widget token da uzun olabilir */
                    design VARCHAR(255) DEFAULT 'standard',
                    FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            self.db.cursor.execute(query)
            self.db.connection.commit()
            # print("'spotify_users' tablosu başarıyla oluşturuldu veya zaten mevcut.") # Geliştirme için log
        except MySQLError as e:
            # print(f"'spotify_users' tablosu oluşturulurken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise

    # -------------------------------------------------------------------------
    # 4.1.5. spotify_get_user_data : Belirli bir kullanıcının bağlı
    #                                Spotify hesap bilgilerini getirir.
    # -------------------------------------------------------------------------
    def spotify_get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Belirli bir Beatify kullanıcısının (`username`) bağlı Spotify hesap bilgilerini getirir.

        Args:
            username (str): Bilgileri getirilecek Beatify kullanıcısının adı.

        Returns:
            Optional[Dict[str, Any]]: Spotify kullanıcı verilerini içeren sözlük,
                                      kullanıcı bulunamazsa veya Spotify bağlantısı yoksa None.
        """
        self._ensure_connection()
        # print(f"Spotify kullanıcı verisi alınıyor: {username}") # Geliştirme için log
        try:
            query = """
                SELECT username, spotify_user_id, client_id, client_secret,
                       refresh_token, created_at, updated_at, widget_token, design
                FROM spotify_users
                WHERE username = %s
            """
            self.db.cursor.execute(query, (username,))
            spotify_data = self.db.cursor.fetchone()

            if not spotify_data:
                # print(f"Kullanıcı ({username}) için Spotify verisi bulunamadı.") # Geliştirme için log
                return None
            
            # Tarih alanlarını string formatına çevirme
            if isinstance(spotify_data.get('created_at'), datetime):
                spotify_data['created_at'] = spotify_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(spotify_data.get('updated_at'), datetime):
                spotify_data['updated_at'] = spotify_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')

            # print(f"Spotify kullanıcı verisi ({username}) başarıyla alındı: {spotify_data}") # Geliştirme için log
            return spotify_data
        except MySQLError as e:
            # print(f"Spotify kullanıcı verisi ({username}) alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.6. spotify_insert_or_update_client_info : Spotify Client ID ve
    #                                               Secret bilgilerini ekler/günceller.
    # -------------------------------------------------------------------------
    def spotify_insert_or_update_client_info(self, username: str, client_id: str, client_secret: str) -> bool:
        """
        Bir Beatify kullanıcısı için Spotify Client ID ve Client Secret bilgilerini
        `spotify_users` tablosuna ekler veya günceller.
        Eğer kullanıcı için bir kayıt yoksa oluşturur, varsa günceller.

        Args:
            username (str): Bilgileri eklenecek/güncellenecek Beatify kullanıcısı.
            client_id (str): Spotify Client ID.
            client_secret (str): Spotify Client Secret.

        Returns:
            bool: İşlem başarılıysa True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify client bilgileri ekleniyor/güncelleniyor: {username}") # Geliştirme için log
        try:
            query = """
                INSERT INTO spotify_users (username, client_id, client_secret)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE client_id = VALUES(client_id), client_secret = VALUES(client_secret)
            """
            self.db.cursor.execute(query, (username, client_id, client_secret))
            self.db.connection.commit()
            # print(f"Spotify client bilgileri ({username}) başarıyla eklendi/güncellendi.") # Geliştirme için log
            return True
        except MySQLError as e:
            # print(f"Spotify client bilgileri ({username}) eklenirken/güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.7. spotify_update_user_connection_info : Kullanıcının Spotify
    #                                              bağlantı bilgilerini günceller.
    # -------------------------------------------------------------------------
    def spotify_update_user_connection_info(self, username: str, spotify_user_id: str, refresh_token: str) -> bool:
        """
        Kullanıcının Spotify bağlantı bilgilerini (`spotify_user_id`, `refresh_token`)
        `spotify_users` tablosunda günceller veya yeni kayıt oluşturur.
        Aynı zamanda `beatify_users` tablosundaki `is_spotify_connected` durumunu True yapar.

        Args:
            username (str): Beatify kullanıcısının adı.
            spotify_user_id (str): Kullanıcının Spotify'daki ID'si.
            refresh_token (str): Spotify'dan alınan refresh token.

        Returns:
            bool: İşlem başarılıysa True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify kullanıcı bağlantı bilgileri güncelleniyor: {username}, Spotify ID: {spotify_user_id}") # Geliştirme için log
        try:
            # Adım 1: spotify_users tablosuna ekleme veya güncelleme
            spotify_query = """
                INSERT INTO spotify_users (username, spotify_user_id, refresh_token)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE spotify_user_id = VALUES(spotify_user_id), refresh_token = VALUES(refresh_token)
            """
            self.db.cursor.execute(spotify_query, (username, spotify_user_id, refresh_token))
            # print(f"spotify_users tablosu güncellendi ({username}).") # Geliştirme için log

            # Adım 2: beatify_users tablosunda bağlantı durumunu güncelle
            # Bu işlemi yapmak için UserRepository'den bir metot çağırmak daha modüler olur.
            # UserRepository'e mevcut db bağlantısını (self.db) iletmek önemli.
            user_repo = UserRepository(db_connection=self.db) # Dışarıdan bağlantı veriyoruz, user_repo bunu kapatmayacak.
            user_repo.beatify_update_spotify_connection_status(username, True)
            # print(f"beatify_users.is_spotify_connected durumu güncellendi ({username}).") # Geliştirme için log

            self.db.connection.commit() # Tüm işlemler başarılıysa commit et
            # print(f"Spotify kullanıcı bağlantı bilgileri ({username}) başarıyla güncellendi ve commit edildi.") # Geliştirme için log
            return True
        except MySQLError as e:
            # print(f"Spotify kullanıcı bağlantı bilgileri ({username}) güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback() # Herhangi bir adımda hata olursa tüm işlemleri geri al
            raise
        finally:
            # UserRepository kendi bağlantısını yönetmediği için kapatmayacak.
            # SpotifyRepository kendi bağlantısını yönetiyorsa (own_connection=True) kapatacak.
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.8. spotify_delete_linked_account_data : Bağlı Spotify hesap bilgilerini siler/sıfırlar.
    # -------------------------------------------------------------------------
    def spotify_delete_linked_account_data(self, username: str) -> bool:
        """
        Bir Beatify kullanıcısının bağlı Spotify hesap bilgilerini `spotify_users` tablosundan siler
        (aslında `spotify_user_id`, `refresh_token`, `widget_token` alanlarını NULL yapar).
        Ayrıca `beatify_users` tablosundaki `is_spotify_connected` durumunu False yapar.
        Client ID ve Secret bilgileri genellikle kullanıcı tarafından tekrar girilebileceği için silinmez.

        Args:
            username (str): Bağlantısı kesilecek Beatify kullanıcısının adı.

        Returns:
            bool: İşlem başarılıysa True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify bağlantısı kesiliyor: {username}") # Geliştirme için log
        try:
            # Adım 1: spotify_users tablosundaki ilgili alanları NULL yap
            spotify_query = """
                UPDATE spotify_users
                SET spotify_user_id = NULL, refresh_token = NULL, widget_token = NULL
                WHERE username = %s
            """
            self.db.cursor.execute(spotify_query, (username,))
            # print(f"spotify_users tablosundaki tokenlar sıfırlandı ({username}).") # Geliştirme için log

            # Adım 2: beatify_users tablosunda bağlantı durumunu güncelle
            user_repo = UserRepository(db_connection=self.db)
            user_repo.beatify_update_spotify_connection_status(username, False)
            # print(f"beatify_users.is_spotify_connected durumu güncellendi ({username}).") # Geliştirme için log

            self.db.connection.commit()
            # print(f"Spotify bağlantısı ({username}) başarıyla kesildi ve commit edildi.") # Geliştirme için log
            return True
        except MySQLError as e:
            # print(f"Spotify bağlantısı ({username}) kesilirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.9. spotify_update_refresh_token_data : Spotify refresh token'ını günceller.
    # -------------------------------------------------------------------------
    def spotify_update_refresh_token_data(self, username: str, new_refresh_token: str) -> bool:
        """
        Bir kullanıcının `spotify_users` tablosundaki Spotify refresh token'ını günceller.

        Args:
            username (str): Token'ı güncellenecek Beatify kullanıcısı.
            new_refresh_token (str): Yeni Spotify refresh token.

        Returns:
            bool: İşlem başarılıysa ve en az bir satır etkilendiyse True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify refresh token güncelleniyor: {username}") # Geliştirme için log
        try:
            query = "UPDATE spotify_users SET refresh_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (new_refresh_token, username))
            self.db.connection.commit()
            updated_rows = self.db.cursor.rowcount
            # print(f"Spotify refresh token ({username}) güncellendi. Etkilenen satır: {updated_rows}") # Geliştirme için log
            return updated_rows > 0
        except MySQLError as e:
            # print(f"Spotify refresh token ({username}) güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.10. spotify_store_widget_token_data : Spotify widget token'ını saklar/günceller.
    # -------------------------------------------------------------------------
    def spotify_store_widget_token_data(self, username: str, token: str) -> bool:
        """
        Kullanıcının Spotify widget token'ını `spotify_users` tablosunda saklar/günceller.
        Eğer kullanıcı için kayıt yoksa, bu metot hata vermez ancak bir şey de yapmaz
        (UPDATE sorgusu olduğu için). Genellikle widget token, kullanıcı Spotify'a
        bağlandıktan sonra oluşturulur ve saklanır, yani kayıt zaten var olur.

        Args:
            username (str): Token'ı saklanacak Beatify kullanıcısı.
            token (str): Spotify widget token'ı.

        Returns:
            bool: İşlem başarılıysa ve en az bir satır etkilendiyse True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify widget token saklanıyor/güncelleniyor: {username}, Token: {token[:10]}...") # Geliştirme için log
        try:
            # Eğer username için spotify_users'da kayıt yoksa, bu sorgu bir şey yapmaz.
            # Önce kayıt olduğundan emin olmak gerekebilir veya INSERT ... ON DUPLICATE KEY UPDATE kullanılabilir.
            # Şimdilik sadece UPDATE varsayalım.
            query = "UPDATE spotify_users SET widget_token = %s WHERE username = %s"
            self.db.cursor.execute(query, (token, username))
            self.db.connection.commit()
            updated_rows = self.db.cursor.rowcount
            # print(f"Spotify widget token ({username}) saklandı/güncellendi. Etkilenen satır: {updated_rows}") # Geliştirme için log
            return updated_rows > 0
        except MySQLError as e:
            # print(f"Spotify widget token ({username}) saklanırken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.11. spotify_get_widget_token_data : Spotify widget token'ını getirir.
    # -------------------------------------------------------------------------
    def spotify_get_widget_token_data(self, username: str) -> Optional[str]:
        """
        Belirli bir Beatify kullanıcısının `spotify_users` tablosundaki Spotify widget token'ını getirir.

        Args:
            username (str): Token'ı getirilecek Beatify kullanıcısı.

        Returns:
            Optional[str]: Widget token, bulunamazsa None.
        """
        self._ensure_connection()
        # print(f"Spotify widget token alınıyor: {username}") # Geliştirme için log
        try:
            query = "SELECT widget_token FROM spotify_users WHERE username = %s"
            self.db.cursor.execute(query, (username,))
            result = self.db.cursor.fetchone()
            widget_token = result['widget_token'] if result else None
            # if widget_token:
                # print(f"Spotify widget token ({username}) bulundu.") # Geliştirme için log
            # else:
                # print(f"Spotify widget token ({username}) bulunamadı.") # Geliştirme için log
            return widget_token
        except MySQLError as e:
            # print(f"Spotify widget token ({username}) alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.12. spotify_get_username_by_widget_token_data : Widget token'ına sahip
    #                                                     kullanıcının adını getirir.
    # -------------------------------------------------------------------------
    def spotify_get_username_by_widget_token_data(self, token: str) -> Optional[str]:
        """
        Verilen widget token'ına sahip Beatify kullanıcısının adını (`username`) getirir.

        Args:
            token (str): Aranacak widget token.

        Returns:
            Optional[str]: Kullanıcı adı, bulunamazsa None.
        """
        self._ensure_connection()
        # print(f"Widget token ({token[:10]}...) ile kullanıcı adı alınıyor...") # Geliştirme için log
        try:
            query = "SELECT username FROM spotify_users WHERE widget_token = %s"
            self.db.cursor.execute(query, (token,))
            result = self.db.cursor.fetchone()
            username = result['username'] if result else None
            # if username:
                # print(f"Widget token ile kullanıcı adı bulundu: {username}") # Geliştirme için log
            # else:
                # print("Verilen widget token ile eşleşen kullanıcı bulunamadı.") # Geliştirme için log
            return username
        except MySQLError as e:
            # print(f"Widget token ({token[:10]}) ile kullanıcı adı alınırken hata: {e}") # Geliştirme için log
            return None
        finally:
            self._close_if_owned()

    # -------------------------------------------------------------------------
    # 4.1.13. spotify_update_widget_design : Kullanıcının Spotify widget tasarım tercihini günceller.
    # -------------------------------------------------------------------------
    def spotify_update_widget_design(self, username: str, design: str) -> bool:
        """
        Kullanıcının `spotify_users` tablosundaki Spotify widget tasarım (`design`) tercihini günceller.

        Args:
            username (str): Tasarımı güncellenecek Beatify kullanıcısı.
            design (str): Yeni widget tasarımı (örn: 'standard', 'compact').

        Returns:
            bool: İşlem başarılıysa ve en az bir satır etkilendiyse True.

        Raises:
            MySQLError: Veritabanı işlemi sırasında bir hata oluşursa.
        """
        self._ensure_connection()
        # print(f"Spotify widget tasarımı güncelleniyor: {username}, Tasarım: {design}") # Geliştirme için log
        try:
            query = "UPDATE spotify_users SET design = %s WHERE username = %s"
            self.db.cursor.execute(query, (design, username))
            self.db.connection.commit()
            updated_rows = self.db.cursor.rowcount
            # print(f"Spotify widget tasarımı ({username}) güncellendi. Etkilenen satır: {updated_rows}") # Geliştirme için log
            return updated_rows > 0
        except MySQLError as e:
            # print(f"Spotify widget tasarımı ({username}) güncellenirken hata: {e}") # Geliştirme için log
            if self.db.connection and self.db.connection.is_connected():
                self.db.connection.rollback()
            raise
        finally:
            self._close_if_owned()

# =============================================================================
# Veritabanı Modülü Sonu
# =============================================================================
