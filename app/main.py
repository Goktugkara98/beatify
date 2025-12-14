# =============================================================================
# Uygulama Başlatma Modülü (main.py)
# =============================================================================
# Bu modül, Flask uygulamasını oluşturmak ve yapılandırmak için uygulamanın
# giriş noktası olan `create_app()` fonksiyonunu içerir. Ayrıca WSGI sunucuları
# için hazır `app` nesnesini üretir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  UYGULAMA FABRİKASI (APP FACTORY)
#      2.1. create_app()
#           2.1.1. Flask app oluşturma
#           2.1.2. Migration (tablo oluşturma) akışı
#           2.1.3. Session/Cookie güvenlik ayarları
#           2.1.4. Jinja2 filtreleri
#           2.1.5. Route kayıtları
#
# 3.0  WSGI GİRİŞİ (WSGI ENTRYPOINT)
#      3.1. app (create_app çıktısı)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
import datetime
from typing import Any, Optional

# Üçüncü parti
from flask import Flask

# Uygulama içi
from app.config.config import COOKIE_HTTPONLY, COOKIE_SAMESITE, COOKIE_SECURE, DEBUG, SECRET_KEY
from app.database.migrations_repository import MigrationsRepository
from app.routes import auth_routes, main_routes
from app.routes.spotify_routes import spotify_routes


def create_app() -> Flask:
    """
    Flask uygulama örneğini oluşturur, yapılandırır ve döndürür.

    Bu fonksiyon:
    - Flask uygulamasını başlatır
    - Veritabanı tablolarını (migrations) kontrol eder/oluşturur
    - Güvenlik ve temel ayarları yükler
    - Jinja2 filtrelerini kaydeder
    - Rotaları (routes) uygular
    """

    # -------------------------------------------------------------------------
    # 2.1.1. Flask uygulamasını başlat
    # -------------------------------------------------------------------------
    # Bu dosya `app` paketinin içinde olduğu için, statik ve template klasörleri
    # paket köküne göre sadece "static" ve "templates" olarak verilmelidir.
    # (Gerçek yollar: <proje_kökü>/app/static ve <proje_kökü>/app/templates)
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # -------------------------------------------------------------------------
    # 2.1.2. Veritabanı tablolarını oluştur (migrations)
    # -------------------------------------------------------------------------
    try:
        migrations_repo = MigrationsRepository()
        migrations_repo.create_all_tables()
    except Exception:
        # Migration hatası durumunda uygulamanın tamamen çökmesini istemiyoruz;
        # loglama altyapısı eklendiğinde burada loglanabilir.
        pass

    # -------------------------------------------------------------------------
    # 2.1.3. Güvenlik ayarları (session/cookie)
    # -------------------------------------------------------------------------
    app.secret_key = SECRET_KEY
    # Session cookie ayarları:
    # - HTTP'de (DEBUG=True) yerel geliştirme rahat çalışsın
    # - Prod'da (DEBUG=False) HTTPS zorunlu olsun
    app.config["SESSION_COOKIE_SECURE"] = COOKIE_SECURE and not DEBUG
    app.config["SESSION_COOKIE_HTTPONLY"] = COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = COOKIE_SAMESITE

    # -------------------------------------------------------------------------
    # 2.1.4. Jinja2 filtreleri
    # -------------------------------------------------------------------------
    @app.template_filter("strftime")
    def _jinja2_filter_datetime(
        date_input: Any, fmt: Optional[str] = None
    ) -> str:
        """
        Jinja2 şablonlarında tarih ve zaman string'lerini veya nesnelerini
        belirtilen formatta string'e çevirir.
        """
        if fmt is None:
            fmt = "%Y-%m-%d %H:%M:%S"

        parsed_date: Optional[datetime.datetime] = None
        if isinstance(date_input, str):
            try:
                parsed_date = datetime.datetime.strptime(
                    date_input, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                try:
                    parsed_date = datetime.datetime.fromisoformat(date_input)
                except ValueError:
                    return ""
        elif isinstance(date_input, datetime.datetime):
            parsed_date = date_input

        if parsed_date:
            return parsed_date.strftime(fmt)
        return str(date_input)

    # -------------------------------------------------------------------------
    # 2.1.5. Rotaları kaydet
    # -------------------------------------------------------------------------
    try:
        main_routes.init_main_routes(app)
        auth_routes.init_auth_routes(app)
        spotify_routes.init_spotify_routes(app)
    except Exception:
        # Rota kaydında bir hata olursa uygulamanın tamamen çökmesini istemiyoruz;
        # loglama altyapısı eklendiğinde burada loglanabilir.
        pass

    return app


# =============================================================================
# 3.0 WSGI GİRİŞİ (WSGI ENTRYPOINT)
# =============================================================================

# WSGI için hazır `app` nesnesi (Gunicorn: `gunicorn app.main:app`)
app = create_app()


