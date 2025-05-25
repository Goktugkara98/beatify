# app/database/connection.py
import mysql.connector
from mysql.connector import Error
from app.config import DB_CONFIG # app.config'den import edildiğini varsayıyorum

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_config = DB_CONFIG # DB_CONFIG'in doğru import edildiğinden emin olun

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            print("Veritabanı bağlantısı başarılı.") # Bağlantı durumunu kontrol için eklendi
        except Error as e:
            print(f"Veritabanı bağlantı hatası: {e}") # Hata mesajını yazdır
            raise # Hatanın yukarıya fırlatılması önemli

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None
        print("Veritabanı bağlantısı kapatıldı.")

    def _ensure_connection(self):
        if not self.connection or not self.cursor or not self.connection.is_connected():
            print("Bağlantı yok veya kapalı, yeniden bağlanılıyor.")
            self.connect()

    def create_all_tables(self, app_context=None): # app_context import döngülerini kırmak için eklenebilir
        """
        Veritabanındaki tüm uygulama tablolarını oluşturur.
        Bu fonksiyon, import döngülerini önlemek için repository'leri doğrudan burada import edebilir
        veya app_context üzerinden dolaylı yoldan erişebilir.
        """
        self._ensure_connection()
        print("Tablolar oluşturuluyor...")

        # Doğrudan import (eğer döngü oluşturmuyorsa):
        from app.repositories.beatify_repository import BeatifyUserRepository
        from app.repositories.spotify_repository import SpotifyUserRepository

        beatify_user_repo = BeatifyUserRepository(self)
        spotify_user_repo = SpotifyUserRepository(self)

        beatify_user_repo.create_beatify_users_table()
        beatify_user_repo.create_beatify_auth_tokens_table()
        spotify_user_repo.create_spotify_users_table() # Bu metot SpotifyUserRepository içinde olmalı

        print("Tablolar başarıyla oluşturuldu veya zaten mevcut.")
        if self.connection: # Commit sadece bağlantı varsa yapılmalı
            self.connection.commit()