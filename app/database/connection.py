# App/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Veritabanı bağlantı URL'si.
# Örnek olarak SQLite kullanılmıştır. Kendi veritabanınıza göre düzenleyin.
# MySQL için: "mysql+mysqlconnector://user:password@host/dbname"
# PostgreSQL için: "postgresql://user:password@host/dbname"
# DB_CONFIG'i app.config dosyanızdan almanız gerekecek.
# Şimdilik sabit bir değerle devam edelim veya config dosyanızın yapısına göre güncelleyelim.
# from app.config import DB_CONFIG # Eğer DB_CONFIG burada tanımlıysa

# Örnek DB_CONFIG (kendi config dosyanızdan almalısınız)
# DB_CONFIG = {
# 'host': 'localhost',
# 'user': 'your_user',
# 'password': 'your_password',
# 'database': 'your_database'
# }
# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"

# Geçici olarak SQLite kullanalım, DB_CONFIG entegrasyonunu sonra yapabilirsiniz.
SQLALCHEMY_DATABASE_URL = "sqlite:///./beatify_app.db"
# Eğer MySQL kullanmaya devam edecekseniz ve DB_CONFIG app.config'de ise:
# from app.config import DB_CONFIG # Bu satırı aktif edin
# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"


# SQLAlchemy motorunu (engine) oluştur.
# `echo=True` ile SQL sorgularını konsolda görebilirsiniz (geliştirme için faydalı).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # connect_args={"check_same_thread": False} # Sadece SQLite için gereklidir.
    echo=True 
)

# Veritabanı oturumları (sessions) oluşturmak için bir SessionLocal sınıfı tanımla.
# - autocommit=False: Oturumları manuel olarak commit etmeniz gerekir.
# - autoflush=False: Sorgu yapmadan önce oturumdaki değişiklikleri veritabanına göndermez.
# - bind=engine: Bu oturumların hangi veritabanı motorunu kullanacağını belirtir.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modellerin (veritabanı tablolarının Python temsilleri) miras alacağı temel sınıf.
Base = declarative_base()

def get_db():
    """
    Dependency injector for database sessions.
    Her istek için bir veritabanı oturumu oluşturur ve istek bittiğinde kapatır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_tables():
    """
    Veritabanında tanımlı tüm tabloları oluşturur.
    Bu fonksiyon, Base metadata'sını kullanarak tabloları oluşturur.
    """
    # Modellerinizin (beatify_models.py, spotify_models.py) Base'i miras aldığından emin olun.
    # Modellerin bu dosyada import edilmesi gerekebilir ya da Base'in modeller tarafından
    # paylaşıldığı bir yapı kurulabilir.
    # Örnek:
    # from App.Models import beatify_models, spotify_models # Modellerinizi import edin
    Base.metadata.create_all(bind=engine)
    print("Veritabanı tabloları oluşturuldu (eğer yoksa).")

# Uygulama başlangıcında tabloları oluşturmak için bu fonksiyonu çağırabilirsiniz.
# if __name__ == "__main__":
#     create_database_tables()
