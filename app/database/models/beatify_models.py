# Models/beatify_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # CURRENT_TIMESTAMP için
from datetime import datetime

# App.connection modülünden Base'i içe aktarıyoruz.
# Bu, tüm modellerimizin aynı declarative base'i kullanmasını sağlar.
from App.connection import Base

class BeatifyUser(Base):
    __tablename__ = "beatify_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_spotify_connected = Column(Boolean, default=False)
    # created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    created_at = Column(TIMESTAMP, server_default=func.now())
    # updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # İlişkiler
    auth_tokens = relationship("BeatifyAuthToken", back_populates="user")
    spotify_account = relationship("SpotifyUser", back_populates="beatify_user", uselist=False) # Bir Beatify kullanıcısının bir Spotify hesabı olur

    def __repr__(self):
        return f"<BeatifyUser(username='{self.username}', email='{self.email}')>"

class BeatifyAuthToken(Base):
    __tablename__ = "beatify_auth_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Orijinal yapıda username string idi, burada BeatifyUser'a ForeignKey ile bağlanıyoruz.
    user_id = Column(Integer, ForeignKey("beatify_users.id", ondelete="CASCADE"), nullable=False) # username yerine user_id
    token = Column(String(255), unique=True, nullable=False, index=True)
    # created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    expired_at = Column(DateTime, default=None, nullable=True) # Varsayılan olarak NULL olabilir

    # İlişkiler
    # BeatifyUser'daki username'e göre değil, user_id'ye göre ilişki kurulacak.
    # Orijinal Foreign Key: FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE
    # SQLAlchemy'de bu ilişki user_id üzerinden kurulacak.
    user = relationship("BeatifyUser", back_populates="auth_tokens")


    def __repr__(self):
        return f"<BeatifyAuthToken(user_id='{self.user_id}', token='{self.token[:10]}...')>"

