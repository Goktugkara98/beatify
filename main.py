# =============================================================================
# Flask Uygulaması - Ana Modül (Flask Application - Main Module)
# =============================================================================
# Bu modül, Flask web uygulamasının ana giriş noktasıdır.
# Uygulama oluşturma (create_app), veritabanı bağlantısı, güvenlik ayarları,
# Jinja2 filtreleri ve rota kayıtları gibi temel yapılandırma adımlarını içerir.
# Uygulamanın geliştirme sunucusunda çalıştırılması da bu modül üzerinden yapılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Flask, veritabanı, rota modülleri, yapılandırmalar ve
#        Python standart kütüphanelerinin içe aktarılması.
# 2.0  UYGULAMA OLUŞTURMA FONKSİYONU (APPLICATION CREATION FUNCTION)
#      2.1. create_app()
#           : Flask uygulama örneğini oluşturur ve yapılandırır.
#           2.1.1. Flask Uygulama Başlatma (Flask App Initialization)
#                  : Flask nesnesini oluşturur, statik ve şablon klasörlerini ayarlar.
#           2.1.2. Veritabanı Bağlantısı ve Tablo Oluşturma (Database Connection and Table Creation)
#                  : Veritabanı bağlantısını kurar ve gerekli tabloları oluşturur.
#           2.1.3. Güvenlik Ayarları (Security Settings)
#                  : Uygulamanın gizli anahtarını (SECRET_KEY) ayarlar.
#           2.1.4. Jinja2 Filtreleri (Jinja2 Filters)
#                  : Şablonlarda kullanılmak üzere özel Jinja2 filtreleri tanımlar (örn: tarih formatlama).
#           2.1.5. Rota Kayıtları (Route Registration)
#                  : Uygulamanın çeşitli bölümlerine ait rotaları (ana, kimlik doğrulama, Spotify) kaydeder.
#           2.1.6. Uygulama Kapatma İşleyicisi (Application Teardown Handler) - (Yeni Eklendi)
#                  : Her istek sonunda veritabanı oturumunu kapatmak için.
# 3.0  UYGULAMA ÇALIŞTIRMA (APPLICATION EXECUTION)
#      : Uygulamanın geliştirme sunucusunda çalıştırılması.
#      3.1. Geliştirme Sunucusu Yapılandırması (Development Server Configuration)
#           : Flask'ın dahili geliştirme sunucusunu başlatır.
#      3.2. SSL Yapılandırması (SSL Configuration - Yorumlu)
#           : HTTPS üzerinden çalıştırmak için SSL yapılandırma örneği (yorum satırı içinde).
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import os # İşletim sistemi etkileşimleri için (dosya yolları vb.)
import datetime # Tarih ve zaman işlemleri için
import logging # Loglama için
# import ssl # SSL yapılandırması için (şu an yorumlu)

from flask import Flask, request # Ana Flask sınıfı ve istek nesnesi
from app.database.db_connection import DatabaseConnection # Veritabanı bağlantı sınıfı
from app.database.migrations_repository import MigrationsRepository # Veritabanı migration sınıfı
# Rota başlatma fonksiyonları
from app.routes import main_routes, auth_routes # Blueprint'ler veya rota modülleri
from app.routes.spotify_routes import spotify_routes # Spotify rotaları için ana başlatıcı
# Uygulama yapılandırma değerleri
from app.config.general_config import DEBUG, SECRET_KEY, SSL_CONFIG # SSL_CONFIG eklendi (yorumlu kısım için)
from typing import Any, Optional # Tip ipuçları için

# Logger kurulumu (modül seviyesinde)
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO if not DEBUG else logging.DEBUG,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# =============================================================================
# 2.0 UYGULAMA OLUŞTURMA FONKSİYONU (APPLICATION CREATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. create_app() : Flask uygulama örneğini oluşturur ve yapılandırır.
# -----------------------------------------------------------------------------
def create_app() -> Flask:
    """
    Flask uygulama örneğini oluşturur, yapılandırır ve döndürür.
    Bu "Application Factory" deseni, farklı yapılandırmalarla birden fazla
    uygulama örneği oluşturmayı veya testleri kolaylaştırmayı sağlar.

    Returns:
        Flask: Yapılandırılmış Flask uygulama örneği.
    """
    # logger.info("Flask uygulaması oluşturuluyor...")

    # -------------------------------------------------------------------------
    # 2.1.1. Flask Uygulama Başlatma (Flask App Initialization)
    # -------------------------------------------------------------------------
    # __name__ mevcut modülün adını alır.
    # static_folder ve template_folder yolları, projenizin dosya yapısına
    # göre ayarlanmalıdır. 'app' klasörü altında oldukları varsayılıyor.
    app = Flask(__name__,
                static_folder=os.path.join('app', 'static'),
                template_folder=os.path.join('app', 'templates'))
    # logger.info(f"Flask uygulaması '{__name__}' adıyla başlatıldı.")
    # logger.info(f"Statik klasör: {app.static_folder}")
    # logger.info(f"Şablon klasörü: {app.template_folder}")

    # -------------------------------------------------------------------------
    # 2.1.2. Veritabanı Bağlantısı ve Tablo Oluşturma (Database Connection and Table Creation)
    # -------------------------------------------------------------------------
    # Bu kısım, uygulamanın her başlatıldığında veritabanı bağlantısı kurmasını
    # ve tabloları (eğer yoksa) oluşturmasını sağlar.
    # Daha büyük uygulamalarda, bu işlem bir CLI komutu (örn: flask db init/migrate/upgrade)
    # ile yönetilebilir (Flask-Migrate gibi eklentilerle).
    try:
        database = DatabaseConnection() # Veritabanı bağlantı nesnesi
        # database.connect() # Bu, _ensure_connection içinde zaten çağrılıyor.
        # create_all_tables metodu kendi içinde bağlantıyı sağlayacaktır.
        migrations_repo = MigrationsRepository()
        migrations_repo.create_all_tables()
        # logger.info("Veritabanı bağlantısı kuruldu ve tablolar oluşturuldu/kontrol edildi.")
        # ÖNEMLİ NOT: DatabaseConnection örneği burada oluşturuluyor ve `database`
        # değişkeni lokal kalıyor. Eğer her istek sonunda bağlantıyı kapatmak
        # istiyorsak (ki bu iyi bir pratiktir), `app.teardown_appcontext` kullanmalıyız.
        # `database` nesnesini `app.extensions` veya `g` gibi bir yerde saklayabiliriz
        # ya da her repository kendi bağlantısını yönetebilir.
        # Mevcut `DatabaseConnection` yapısı, her repository'nin kendi bağlantısını
        # yönetmesine veya dışarıdan bir bağlantı almasına izin veriyor.
        # `create_all_tables` içinde repository'ler oluşturulurken mevcut bağlantı
        # iletiliyor, bu iyi bir yaklaşım.
    except Exception as e:
        # logger.error(f"Veritabanı başlatılırken hata oluştu: {str(e)}", exc_info=True)
        # Uygulamanın bu noktada devam etmesi sorunlu olabilir.
        # raise RuntimeError(f"Veritabanı başlatılamadı: {e}") from e
        pass # Hata durumunda devam etmesi için geçici olarak eklendi

    # -------------------------------------------------------------------------
    # 2.1.3. Güvenlik Ayarları (Security Settings)
    # -------------------------------------------------------------------------
    # SECRET_KEY, session yönetimi, flash mesajları ve diğer güvenlik
    # özellikleri için kullanılır. Güçlü ve gizli tutulmalıdır.
    app.secret_key = SECRET_KEY
    if not SECRET_KEY or SECRET_KEY == 'varsayilan-cok-gizli-bir-anahtar-buraya-yazin':
        # logger.warning("UYARI: Güvenli olmayan varsayılan SECRET_KEY kullanılıyor. Lütfen canlı ortam için değiştirin!")
        pass # Uyarıyı gösterme
    # logger.info("Uygulama gizli anahtarı ayarlandı.")

    # Diğer güvenlik ayarları eklenebilir (örn: CSRF koruması için Flask-WTF veya Flask-SeaSurf).
    # app.config['SESSION_COOKIE_SECURE'] = not DEBUG
    # app.config['SESSION_COOKIE_HTTPONLY'] = True
    # app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # -------------------------------------------------------------------------
    # 2.1.4. Jinja2 Filtreleri (Jinja2 Filters)
    # -------------------------------------------------------------------------
    # Şablonlarda kullanılmak üzere özel filtreler tanımlanabilir.
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(date_input: Any, fmt: Optional[str] = None) -> str:
        """
        Jinja2 şablonlarında tarih ve zaman string'lerini veya nesnelerini
        belirtilen formatta string'e çevirir.

        Args:
            date_input (Any): Formatlanacak tarih (datetime nesnesi veya '%Y-%m-%d %H:%M:%S' formatında string).
            fmt (Optional[str], optional): İstenen çıktı formatı (strftime formatı).
                                           Varsayılan '%H:%M:%S'.

        Returns:
            str: Formatlanmış tarih string'i veya hata durumunda boş string.
        """
        if fmt is None:
            fmt = '%Y-%m-%d %H:%M:%S' # Daha genel bir varsayılan format

        parsed_date: Optional[datetime.datetime] = None
        if isinstance(date_input, str):
            try:
                # Birden fazla formatı denemek gerekebilir veya belirli bir format beklenmeli.
                parsed_date = datetime.datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    parsed_date = datetime.datetime.fromisoformat(date_input)
                except ValueError:
                    # logger.warning(f"Jinja2 strftime filtresi: Geçersiz tarih string formatı '{date_input}'.")
                    return "" # Hata durumunda boş string
        elif isinstance(date_input, datetime.datetime):
            parsed_date = date_input
        
        if parsed_date:
            return parsed_date.strftime(fmt)
        else: # Eğer date_input ne string ne de datetime ise veya parse edilemediyse
            # logger.warning(f"Jinja2 strftime filtresi: Geçersiz tarih tipi '{type(date_input)}' veya parse edilemedi.")
            return str(date_input) # Orijinal değeri string olarak döndür veya boş string

    # logger.info("Jinja2 'strftime' filtresi kaydedildi.")

    # -------------------------------------------------------------------------
    # 2.1.5. Rota Kayıtları (Route Registration)
    # -------------------------------------------------------------------------
    # Uygulamanın farklı bölümlerine ait rotaları (veya Blueprint'leri) kaydet.
    # Bu `init_..._routes` fonksiyonları, ilgili rota modüllerinde tanımlanmış olmalı
    # ve Flask `app` nesnesini argüman olarak almalıdır.
    try:
        main_routes.init_main_routes(app)
        # logger.info("Ana rotalar (main_routes) kaydedildi.")
        auth_routes.init_auth_routes(app)
        # logger.info("Kimlik doğrulama rotaları (auth_routes) kaydedildi.")
        spotify_routes.init_spotify_routes(app) # Bu, tüm Spotify alt rotalarını kaydeder
        # logger.info("Spotify rotaları (spotify_routes) kaydedildi.")
        # Eğer admin_routes gibi başka Blueprint'ler varsa, onlar da burada kaydedilmeli.
        # from app.routes.admin_routes import admin_bp # Örnek
        # app.register_blueprint(admin_bp, url_prefix='/admin') # Örnek
    except Exception as e:
        # logger.error(f"Rotalar kaydedilirken hata oluştu: {str(e)}", exc_info=True)
        # Uygulamanın bu noktada devam etmesi sorunlu olabilir.
        # raise RuntimeError(f"Rotalar kaydedilemedi: {e}") from e
        pass # Hata durumunda devam etmesi için geçici olarak eklendi


    # -------------------------------------------------------------------------
    # 2.1.6. Uygulama Kapatma İşleyicisi (Application Teardown Handler) - (Yeni Eklendi)
    # -------------------------------------------------------------------------
    # Her HTTP isteği bittikten sonra (başarılı veya hatalı) çalışacak fonksiyonları kaydeder.
    # Veritabanı bağlantısını kapatmak için idealdir.
    # NOT: Eğer her repository kendi bağlantısını açıp kapatıyorsa (`_close_if_owned` ile),
    # bu global teardown'a gerek olmayabilir veya farklı bir şekilde yönetilebilir.
    # Ancak, `DatabaseConnection` sınıfının `create_all_tables` gibi metotları
    # bir bağlantı açıyorsa, bu bağlantının bir noktada kapatılması gerekir.
    # Şimdilik, bu yapının nasıl çalıştığına dair bir varsayım yapmadan ekliyorum.
    # Eğer `DatabaseConnection` her işlem için yeni bağlantı açıp kapatmıyorsa
    # ve global bir bağlantı tutuluyorsa bu gereklidir.
    # Mevcut `DatabaseConnection` yapısı, her repository'nin kendi bağlantısını
    # yönetmesine izin veriyor gibi görünüyor. Bu durumda bu teardown gereksiz olabilir.
    # Ancak, `create_app` içinde oluşturulan `database` nesnesinin bağlantısı
    # açık kalabilir. Bunu kapatmak için:
    
    # Bu global teardown, `DatabaseConnection`'ın nasıl kullanıldığına bağlı.
    # Eğer her repository kendi bağlantısını yönetiyorsa ve `create_app`'teki
    # `database` nesnesi sadece tablo oluşturma için kullanılıp sonra referansı
    # kayboluyorsa, bu özel teardown'a gerek olmayabilir.
    # Ancak, genel bir veritabanı oturum yönetimi için iyi bir pratiktir.
    # @app.teardown_appcontext
    # def shutdown_session(exception: Optional[Exception] = None) -> None:
    #     """Her istek sonunda veritabanı oturumunu (eğer varsa) kapatır."""
    #     # Bu, SQLAlchemy gibi ORM'ler için daha yaygındır.
    #     # Mevcut DatabaseConnection için, eğer global bir bağlantı tutulmuyorsa
    #     # ve her repository kendi bağlantısını kapatıyorsa, bu gereksiz olabilir.
    #     # db_session = getattr(g, '_database', None) # Eğer g'de saklanıyorsa
    #     # if db_session is not None:
    #     #     db_session.close()
    #     #     logger.info("Veritabanı oturumu istek sonunda kapatıldı.")
    #     pass # Şimdilik pasif bırakıldı, DatabaseConnection yapısına göre aktif edilebilir.


    # logger.info("Flask uygulaması başarıyla oluşturuldu ve yapılandırıldı.")
    return app

# =============================================================================
# 3.0 UYGULAMA ÇALIŞTIRMA (APPLICATION EXECUTION)
# =============================================================================
if __name__ == '__main__':
    # Bu blok, dosya doğrudan çalıştırıldığında (`python main.py`) devreye girer.
    # Bir WSGI sunucusu (Gunicorn, uWSGI) tarafından çalıştırıldığında bu blok çalışmaz.
    
    flask_app = create_app() # Uygulama örneğini oluştur
    # logger.info("Uygulama çalıştırılmak üzere hazırlanıyor...")

    # -------------------------------------------------------------------------
    # 3.1. Geliştirme Sunucusu Yapılandırması (Development Server Configuration)
    # -------------------------------------------------------------------------
    # Flask'ın dahili geliştirme sunucusu. Canlı (production) ortamlar için uygun değildir.
    # DEBUG=True ise, otomatik yeniden yükleyici (reloader) ve hata ayıklayıcı aktif olur.
    # host="0.0.0.0" tüm ağ arayüzlerinden erişime izin verir (örn: aynı ağdaki başka cihazlardan).
    # threaded=True birden fazla isteği aynı anda işleyebilmek için (geliştirme için).
    try:
        # logger.info(f"Geliştirme sunucusu başlatılıyor: http://0.0.0.0:5000/ (DEBUG={DEBUG})")
        flask_app.run(
            debug=DEBUG,
            host="0.0.0.0",
            port=5000,
            threaded=True
            # use_reloader=DEBUG # debug=True zaten reloader'ı aktif eder.
        )
    except Exception as run_err:
        # logger.critical(f"Uygulama çalıştırılırken kritik bir hata oluştu: {str(run_err)}", exc_info=True)
        pass # Hata durumunda devam etmesi için geçici olarak eklendi


    # -------------------------------------------------------------------------
    # 3.2. SSL Yapılandırması (SSL Configuration - Yorumlu)
    # -------------------------------------------------------------------------
    # Canlı ortamda veya HTTPS testi için SSL yapılandırması.
    # Gerçek sertifika dosyalarının yolları `SSL_CONFIG` içinde tanımlı olmalıdır.
    # Genellikle canlıda bu işi Nginx, Apache gibi bir ters proxy veya load balancer yapar.
    """
    if not DEBUG: # Sadece canlıda SSL ile çalıştır (veya DEBUG=False ise)
        try:
            # SSL bağlamını (context) oluştur
            # Python 3.6+ için ssl.PROTOCOL_TLS_SERVER önerilir.
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                certfile=SSL_CONFIG.CERTFILE, # Sertifika dosyasının yolu
                keyfile=SSL_CONFIG.KEYFILE    # Özel anahtar dosyasının yolu
            )
            # logger.info(f"SSL yapılandırması yüklendi. Sunucu HTTPS üzerinden başlatılıyor: https://0.0.0.0:5000/")
            flask_app.run(
                debug=DEBUG,
                host="0.0.0.0",
                port=5000, # HTTPS için genellikle 443 portu kullanılır, ancak geliştirme için 5000 olabilir.
                ssl_context=ssl_context,
                threaded=True
            )
        except FileNotFoundError:
            # logger.error(f"SSL sertifika veya anahtar dosyaları bulunamadı. Yollar: Cert='{SSL_CONFIG.CERTFILE}', Key='{SSL_CONFIG.KEYFILE}'")
            # logger.warning("SSL hatası nedeniyle HTTP üzerinden devam ediliyor...")
            flask_app.run(debug=DEBUG, host="0.0.0.0", port=5000, threaded=True)
        except ssl.SSLError as ssl_err:
            # logger.error(f"SSL yapılandırma hatası: {str(ssl_err)}", exc_info=True)
            # logger.warning("SSL hatası nedeniyle HTTP üzerinden devam ediliyor...")
            flask_app.run(debug=DEBUG, host="0.0.0.0", port=5000, threaded=True)
        except Exception as e:
            # logger.critical(f"SSL ile uygulama çalıştırılırken beklenmedik bir hata oluştu: {str(e)}", exc_info=True)
            # logger.warning("SSL hatası nedeniyle HTTP üzerinden devam ediliyor...")
            flask_app.run(debug=DEBUG, host="0.0.0.0", port=5000, threaded=True)
    else: # DEBUG True ise HTTP üzerinden çalıştır
        # logger.info(f"Geliştirme sunucusu (HTTP) başlatılıyor: http://0.0.0.0:5000/ (DEBUG={DEBUG})")
        flask_app.run(debug=DEBUG, host="0.0.0.0", port=5000, threaded=True)
    """
# =============================================================================
# Flask Uygulaması - Ana Modül Sonu
# =============================================================================
