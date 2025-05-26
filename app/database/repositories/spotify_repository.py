# Repositories/spotify_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Modelleri Models paketinden içe aktar
from App.Models.spotify_models import SpotifyUser
from App.Models.beatify_models import BeatifyUser # BeatifyUser'a referans için gerekebilir

class SpotifyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_spotify_user(
        self,
        beatify_user_id: int,
        spotify_user_id_on_spotify: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        widget_token: str | None = None,
        design: str | None = 'standard'
    ) -> SpotifyUser | None:
        """
        Bir Beatify kullanıcısı için Spotify kullanıcı bilgilerini oluşturur veya günceller.
        """
        db_spotify_user = self.db.query(SpotifyUser).filter(SpotifyUser.beatify_user_id == beatify_user_id).first()

        if db_spotify_user:
            # Güncelleme
            if spotify_user_id_on_spotify is not None:
                db_spotify_user.spotify_user_id_on_spotify = spotify_user_id_on_spotify
            if client_id is not None:
                db_spotify_user.client_id = client_id
            if client_secret is not None:
                db_spotify_user.client_secret = client_secret
            if refresh_token is not None:
                db_spotify_user.refresh_token = refresh_token
            if widget_token is not None:
                db_spotifya_user.widget_token = widget_token
            if design is not None:
                db_spotify_user.design = design
            # updated_at otomatik güncellenir (modelde onupdate=func.now() varsa)
        else:
            # Yeni kayıt oluştur
            # Beatify kullanıcısının varlığını kontrol et
            beatify_user = self.db.query(BeatifyUser).filter(BeatifyUser.id == beatify_user_id).first()
            if not beatify_user:
                # İlişkili Beatify kullanıcısı bulunamazsa işlem yapma
                return None
            
            db_spotify_user = SpotifyUser(
                beatify_user_id=beatify_user_id,
                spotify_user_id_on_spotify=spotify_user_id_on_spotify,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                widget_token=widget_token,
                design=design
            )
            self.db.add(db_spotify_user)
        
        try:
            self.db.commit()
            self.db.refresh(db_spotify_user)
            
            # BeatifyUser'ın is_spotify_connected durumunu güncelle
            # Bu işlemi burada yapmak yerine bir servis katmanında yapmak daha uygun olabilir.
            # Şimdilik repository içinde bırakıyorum.
            beatify_user_to_update = self.db.query(BeatifyUser).filter(BeatifyUser.id == beatify_user_id).first()
            if beatify_user_to_update:
                # Eğer refresh_token ve spotify_user_id_on_spotify varsa bağlı kabul edelim.
                # Bu mantık uygulamanızın gereksinimlerine göre değişebilir.
                is_connected = bool(db_spotify_user.refresh_token and db_spotify_user.spotify_user_id_on_spotify)
                if beatify_user_to_update.is_spotify_connected != is_connected:
                    beatify_user_to_update.is_spotify_connected = is_connected
                    self.db.commit() # İkinci commit
                    self.db.refresh(beatify_user_to_update)

            return db_spotify_user
        except IntegrityError: # unique constraint ihlali (örn: beatify_user_id)
            self.db.rollback()
            return None
        except Exception as e:
            self.db.rollback()
            # Hata loglama
            print(f"SpotifyRepository Hata: {e}")
            return None


    def get_spotify_user_by_beatify_user_id(self, beatify_user_id: int) -> SpotifyUser | None:
        """
        Beatify kullanıcı ID'sine göre Spotify kullanıcı bilgilerini getirir.
        """
        return self.db.query(SpotifyUser).filter(SpotifyUser.beatify_user_id == beatify_user_id).first()

    def get_spotify_user_by_widget_token(self, widget_token: str) -> SpotifyUser | None:
        """
        Widget token'ına göre Spotify kullanıcı bilgilerini getirir.
        """
        if not widget_token:
            return None
        return self.db.query(SpotifyUser).filter(SpotifyUser.widget_token == widget_token).first()

    def update_refresh_token(self, beatify_user_id: int, new_refresh_token: str) -> SpotifyUser | None:
        """
        Bir kullanıcının Spotify refresh token'ını günceller.
        """
        db_spotify_user = self.get_spotify_user_by_beatify_user_id(beatify_user_id)
        if db_spotify_user:
            db_spotify_user.refresh_token = new_refresh_token
            try:
                self.db.commit()
                self.db.refresh(db_spotify_user)
                return db_spotify_user
            except Exception:
                self.db.rollback()
                return None
        return None

    def update_widget_token(self, beatify_user_id: int, new_widget_token: str | None) -> SpotifyUser | None:
        """
        Bir kullanıcının widget token'ını günceller. None verilirse token silinir.
        """
        db_spotify_user = self.get_spotify_user_by_beatify_user_id(beatify_user_id)
        if db_spotify_user:
            db_spotify_user.widget_token = new_widget_token
            try:
                self.db.commit()
                self.db.refresh(db_spotify_user)
                return db_spotify_user
            except Exception:
                self.db.rollback()
                return None
        return None
    
    def update_design(self, beatify_user_id: int, new_design: str) -> SpotifyUser | None:
        """
        Bir kullanıcının widget tasarımını günceller.
        """
        db_spotify_user = self.get_spotify_user_by_beatify_user_id(beatify_user_id)
        if db_spotify_user:
            db_spotify_user.design = new_design
            try:
                self.db.commit()
                self.db.refresh(db_spotify_user)
                return db_spotify_user
            except Exception:
                self.db.rollback()
                return None
        return None

    def delete_spotify_connection(self, beatify_user_id: int) -> bool:
        """
        Bir kullanıcının Spotify bağlantısını ve ilgili verilerini siler.
        BeatifyUser'daki is_spotify_connected alanını False yapar.
        """
        db_spotify_user = self.get_spotify_user_by_beatify_user_id(beatify_user_id)
        if db_spotify_user:
            try:
                self.db.delete(db_spotify_user)
                
                # BeatifyUser'ın is_spotify_connected durumunu güncelle
                beatify_user_to_update = self.db.query(BeatifyUser).filter(BeatifyUser.id == beatify_user_id).first()
                if beatify_user_to_update:
                    if beatify_user_to_update.is_spotify_connected:
                        beatify_user_to_update.is_spotify_connected = False
                
                self.db.commit() # Tüm değişiklikleri tek seferde commit et
                return True
            except Exception:
                self.db.rollback()
                return False
        return False # Silinecek kayıt bulunamadı

