# Repositories/beatify_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

# Modelleri Models paketinden içe aktar
from app.models.beatify_models import BeatifyUser, BeatifyAuthToken
# Şifreleme işlemleri için (gerçek uygulamada auth.py veya benzeri bir yerden gelmeli)
# from App.auth import hash_password, verify_password # Örnek, kendi auth modülünüze göre uyarlayın

# Bu repoyu doğrudan çalıştırmak veya test etmek için geçici şifreleme fonksiyonları
# GERÇEK UYGULAMADA BUNLARI KULLANMAYIN, GÜVENLİ BİR AUTH MODÜLÜ KULLANIN!
def temp_hash_password(password: str) -> str:
    # Bu sadece bir yer tutucudur, asla üretimde kullanmayın!
    # bcrypt veya argon2 gibi güçlü bir kütüphane kullanın.
    return f"hashed_{password}"

def temp_verify_password(plain_password: str, hashed_password: str) -> bool:
    # Bu sadece bir yer tutucudur.
    return hashed_password == f"hashed_{plain_password}"


class BeatifyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str, password: str) -> BeatifyUser | None:
        """
        Yeni bir Beatify kullanıcısı oluşturur.
        Username veya email zaten varsa None döner.
        """
        # Gerçek uygulamada auth modülünüzden hash_password kullanın
        hashed_password = temp_hash_password(password)
        db_user = BeatifyUser(username=username, email=email, password_hash=hashed_password)
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError: # Username veya email unique constraint ihlali
            self.db.rollback()
            return None

    def get_user_by_username(self, username: str) -> BeatifyUser | None:
        """
        Kullanıcı adına göre bir kullanıcıyı getirir.
        """
        return self.db.query(BeatifyUser).filter(BeatifyUser.username == username).first()

    def get_user_by_email(self, email: str) -> BeatifyUser | None:
        """
        E-posta adresine göre bir kullanıcıyı getirir.
        """
        return self.db.query(BeatifyUser).filter(BeatifyUser.email == email).first()

    def get_user_by_id(self, user_id: int) -> BeatifyUser | None:
        """
        Kullanıcı ID'sine göre bir kullanıcıyı getirir.
        """
        return self.db.query(BeatifyUser).filter(BeatifyUser.id == user_id).first()
    
    def check_username_or_email_exists(self, username: str, email: str) -> bool:
        """
        Verilen username veya email'in zaten kayıtlı olup olmadığını kontrol eder.
        """
        return self.db.query(BeatifyUser).filter(
            (BeatifyUser.username == username) | (BeatifyUser.email == email)
        ).first() is not None

    def update_user_spotify_connection_status(self, user_id: int, status: bool) -> BeatifyUser | None:
        """
        Kullanıcının Spotify bağlantı durumunu günceller.
        """
        db_user = self.get_user_by_id(user_id)
        if db_user:
            db_user.is_spotify_connected = status
            db_user.updated_at = datetime.utcnow() # Veya func.now() kullanılıyorsa otomatik güncellenir
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        return None

    # --- Auth Token Yönetimi ---

    def create_auth_token(self, user_id: int, token: str, expires_delta: timedelta) -> BeatifyAuthToken:
        """
        Kullanıcı için yeni bir kimlik doğrulama token'ı oluşturur veya günceller.
        Eğer kullanıcı için aktif bir token varsa, onu günceller.
        """
        expires_at = datetime.utcnow() + expires_delta
        
        # Kullanıcının mevcut, süresi dolmamış token'ını bul
        db_token = self.db.query(BeatifyAuthToken).filter(
            BeatifyAuthToken.user_id == user_id,
            BeatifyAuthToken.expires_at > datetime.utcnow(), # Sadece hala geçerli olanları kontrol et
            BeatifyAuthToken.expired_at == None
        ).first()

        if db_token:
            # Mevcut token'ı güncelle
            db_token.token = token
            db_token.expires_at = expires_at
            db_token.created_at = datetime.utcnow() # Ya da func.now()
        else:
            # Yeni token oluştur
            db_token = BeatifyAuthToken(
                user_id=user_id, 
                token=token, 
                expires_at=expires_at
            )
            self.db.add(db_token)
        
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_auth_token(self, token_str: str) -> BeatifyAuthToken | None:
        """
        Verilen token string'ine göre geçerli bir token getirir.
        Token bulunamazsa veya süresi dolmuşsa None döner.
        """
        return self.db.query(BeatifyAuthToken).filter(
            BeatifyAuthToken.token == token_str,
            BeatifyAuthToken.expires_at > datetime.utcnow(),
            BeatifyAuthToken.expired_at == None # Manuel olarak sonlandırılmamış
        ).first()

    def get_user_by_auth_token(self, token_str: str) -> BeatifyUser | None:
        """
        Geçerli bir auth token string'i ile ilişkili kullanıcıyı getirir.
        """
        auth_token = self.get_auth_token(token_str)
        if auth_token:
            return auth_token.user # İlişki üzerinden kullanıcıyı al
        return None

    def deactivate_auth_token(self, token_str: str) -> bool:
        """
        Verilen token string'ine ait token'ı manuel olarak sonlandırır (geçersiz kılar).
        """
        db_token = self.db.query(BeatifyAuthToken).filter(BeatifyAuthToken.token == token_str).first()
        if db_token:
            db_token.expired_at = datetime.utcnow()
            db_token.expires_at = datetime.utcnow() # Süresini de geçmişe ayarla
            self.db.commit()
            return True
        return False
    
    def deactivate_all_user_tokens(self, user_id: int) -> int:
        """
        Belirli bir kullanıcıya ait tüm aktif token'ları sonlandırır.
        Kaç adet token'ın sonlandırıldığını döner.
        """
        tokens_to_deactivate = self.db.query(BeatifyAuthToken).filter(
            BeatifyAuthToken.user_id == user_id,
            BeatifyAuthToken.expires_at > datetime.utcnow(),
            BeatifyAuthToken.expired_at == None
        ).all()

        count = 0
        for token in tokens_to_deactivate:
            token.expired_at = datetime.utcnow()
            token.expires_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            self.db.commit()
        return count

