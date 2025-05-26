# Models/spotify_models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # CURRENT_TIMESTAMP için

# App.connection modülünden Base'i içe aktarıyoruz.
from App.connection import Base

class SpotifyUser(Base):
    __tablename__ = "spotify_users"

    # Orijinalde username PRIMARY KEY idi ve beatify_users.username'e FOREIGN KEY idi.
    # SQLAlchemy'de genellikle ayrı bir id kolonu tercih edilir ve ilişki user_id üzerinden kurulur.
    # Eğer username'i PK olarak kullanmak isterseniz:
    # username = Column(String(255), ForeignKey("beatify_users.username", ondelete="CASCADE"), primary_key=True)
    # Ancak, best practice olarak integer bir PK ve user_id ile ilişki daha yaygındır.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # Yeni eklenen PK
    beatify_user_id = Column(Integer, ForeignKey("beatify_users.id", ondelete="CASCADE"), unique=True, nullable=False) # username yerine beatify_user_id

    spotify_user_id_on_spotify = Column(String(255), name="spotify_user_id") # Orijinal 'spotify_user_id' kolon adı, karışıklığı önlemek için yeniden adlandırıldı.
    client_id = Column(String(255), nullable=True) # Nullable olabilir, kullanıcı ilk başta girmeyebilir
    client_secret = Column(String(255), nullable=True) # Nullable olabilir
    refresh_token = Column(String(255), nullable=True) # Nullable olabilir
    # created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    created_at = Column(TIMESTAMP, server_default=func.now())
    # updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    widget_token = Column(Text, nullable=True) # TEXT tipi için
    design = Column(String(255), default='standard') # Varsayılan değer

    # İlişkiler
    # FOREIGN KEY (username) REFERENCES beatify_users(username) ON DELETE CASCADE
    # Bu ilişki beatify_user_id üzerinden kurulacak.
    beatify_user = relationship("BeatifyUser", back_populates="spotify_account")

    # Orijinal yapıda UNIQUE (spotify_user_id, username) vardı.
    # SQLAlchemy'de bu __table_args__ ile tanımlanır.
    # Eğer username'i PK olarak kullanmıyorsanız ve beatify_user_id kullanıyorsanız,
    # unique constraint'i (spotify_user_id_on_spotify, beatify_user_id) şeklinde olmalı.
    __table_args__ = (
        # UniqueConstraint('spotify_user_id_on_spotify', 'beatify_user_id', name='uq_spotify_user_id_beatify_user_id'),
        # Spotify kullanıcı ID'si tek başına unique olabilir veya beatify kullanıcısı başına unique olabilir.
        # Orijinaldeki UNIQUE (spotify_user_id, username) mantığına göre,
        # bir beatify kullanıcısının bağladığı spotify_user_id unique olmalı.
        # Ancak spotify_user_id'nin kendisi de global olarak unique olabilir.
        # Şimdilik beatify_user_id zaten unique olduğu için (one-to-one ilişki) ekstra bir constraint'e gerek olmayabilir.
        # Eğer spotify_user_id_on_spotify'nin tüm tablo genelinde unique olmasını istiyorsanız:
        # UniqueConstraint('spotify_user_id_on_spotify', name='uq_spotify_user_id_on_spotify')
    )

    def __repr__(self):
        return f"<SpotifyUser(beatify_user_id='{self.beatify_user_id}', spotify_user_id_on_spotify='{self.spotify_user_id_on_spotify}')>"

