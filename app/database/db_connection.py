# db_connection.py
# =============================================================================
# Veritabanı Bağlantı Modülü (Database Connection Module)
# =============================================================================
# Bu modül, MySQL veritabanı ile bağlantı kurma ve yönetme
# işlemlerini üstlenen DatabaseConnection sınıfını içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  VERİTABANI BAĞLANTI SINIFI (DATABASE CONNECTION CLASS)
#      2.1. DatabaseConnection
#           2.1.1. __init__
#           2.1.2. connect
#           2.1.3. close
#           2.1.4. _ensure_connection
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import mysql.connector
from mysql.connector import Error as MySQLError
from typing import Optional, Dict, Any
from app.config import DB_CONFIG # Uygulama yapılandırmasından veritabanı ayarlarını alır

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

# =============================================================================
# Veritabanı Bağlantı Modülü Sonu
# =============================================================================
