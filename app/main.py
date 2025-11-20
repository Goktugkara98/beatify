import os
import datetime
from typing import Any, Optional

from flask import Flask

from app.database.migrations_repository import MigrationsRepository
from app.routes import main_routes, auth_routes
from app.routes.spotify_routes import spotify_routes
from app.config.config import (
    DEBUG,
    SECRET_KEY,
    COOKIE_SECURE,
    COOKIE_HTTPONLY,
    COOKIE_SAMESITE,
)


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

    # Flask uygulamasını başlat
    # Bu dosya `app` paketinin içinde olduğu için, statik ve template klasörleri
    # paket köküne göre sadece "static" ve "templates" olarak verilmelidir.
    # (Gerçek yollar: <proje_kökü>/app/static ve <proje_kökü>/app/templates)
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # Veritabanı tablolarını oluştur (migrations)
    try:
        migrations_repo = MigrationsRepository()
        migrations_repo.create_all_tables()
    except Exception:
        # Migration hatası durumunda uygulamanın tamamen çökmesini istemiyoruz;
        # loglama altyapısı eklendiğinde burada loglanabilir.
        pass

    # Güvenlik ayarları
    app.secret_key = SECRET_KEY
    # Session cookie ayarları:
    # - HTTP'de (DEBUG=True) yerel geliştirme rahat çalışsın
    # - Prod'da (DEBUG=False) HTTPS zorunlu olsun
    app.config["SESSION_COOKIE_SECURE"] = COOKIE_SECURE and not DEBUG
    app.config["SESSION_COOKIE_HTTPONLY"] = COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = COOKIE_SAMESITE

    # Jinja2 filtreleri
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

    # Rotaları kaydet
    try:
        main_routes.init_main_routes(app)
        auth_routes.init_auth_routes(app)
        spotify_routes.init_spotify_routes(app)
    except Exception:
        # Rota kaydında bir hata olursa uygulamanın tamamen çökmesini istemiyoruz;
        # loglama altyapısı eklendiğinde burada loglanabilir.
        pass

    return app


# WSGI için hazır `app` nesnesi (Gunicorn: `gunicorn app.main:app`)
app = create_app()


