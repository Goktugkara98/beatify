# =============================================================================
# Ana Rotalar Modülü (Main Routes Module)
# =============================================================================
# Bu modül, uygulamanın ana ve genel amaçlı kullanıcı arayüzü (UI) rotalarını
# tanımlar. Ana sayfa ve kullanıcı profili yönetimi gibi temel işlevler
# bu modül altında gruplanmıştır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenleri, veritabanı depoları ve servislerin içe aktarılması.
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
#     2.1. init_main_routes(app)
#          : Tüm ana rotaları belirtilen Flask uygulamasına kaydeder.
#          Depo (repository) ve servis örneklerini kullanır ve rota fonksiyonlarını tanımlar.
#
#     İÇ ROTALAR (init_main_routes içinde tanımlanır):
#     -------------------------------------------------------------------------
#     3.0 ANA SAYFA ROTALARI (HOMEPAGE ROUTES)
#         3.1. index()
#              : Uygulamanın kök URL'sini ('/') ana sayfaya yönlendirir veya ana sayfayı sunar.
#                Rota: / (GET)
#         3.2. homepage()
#              : Uygulamanın ana sayfasını ('/homepage') sunar.
#                Rota: /homepage (GET)
#     4.0 PROFİL YÖNETİMİ ROTASI (PROFILE MANAGEMENT ROUTE)
#         4.1. profile()
#              : Kullanıcı profil sayfasını gösterir (GET) ve profil bilgilerini
#                (örn: Spotify Client ID/Secret) günceller (POST).
#                Rota: /profile (GET, POST)
#                4.1.1. GET İsteği Yönetimi (GET Request Handling)
#                4.1.2. POST İsteği Yönetimi (POST Request Handling - Spotify Bilgileri)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session, # Session doğrudan kullanılmıyor gibi, auth_service üzerinden erişiliyor.
    flash,
    Flask # Flask tipi için
)
# Veritabanı erişimi için Repository sınıfları
from app.database.models.database import UserRepository, SpotifyRepository
# Kimlik doğrulama ve oturum kontrolü için servisler
from app.services.auth_service import session_is_user_logged_in
# Profil sayfası için özel servisler
from app.services.profile_services import handle_get_request # Profil GET isteği için
# Spotify Client ID/Secret güncelleme servisi (orijinalde import edilmiş ama kullanılmamış)
# from app.services.spotify_services.spotify_service import update_client_id_and_secret_data
from typing import Any, Optional, Tuple, Dict # Tip ipuçları için

# =============================================================================
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_main_routes(app) : Tüm ana rotaları kaydeder.
# -----------------------------------------------------------------------------
def init_main_routes(app: Flask) -> None:
    """
    Ana uygulama rotalarını (ana sayfa, profil vb.)
    belirtilen Flask uygulamasına kaydeder.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    # print("Ana rotalar başlatılıyor...") # Geliştirme için log

    # =========================================================================
    # 3.0 ANA SAYFA ROTALARI (HOMEPAGE ROUTES)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 3.1. index() : Uygulamanın kök URL'sini yönetir.
    #      Rota: / (GET)
    # -------------------------------------------------------------------------
    @app.route('/', methods=['GET'])
    def index() -> str:
        """
        Uygulamanın kök URL'si (`/`) için ana sayfayı render eder.
        Genellikle `homepage` rotasıyla aynı içeriği sunar.
        """
        # print("API çağrısı: / (Ana Sayfa)") # Geliştirme için log
        return render_template('homepage.html', title="Ana Sayfa")

    # -------------------------------------------------------------------------
    # 3.2. homepage() : Uygulamanın ana sayfasını sunar.
    #      Rota: /homepage (GET)
    # -------------------------------------------------------------------------
    @app.route('/homepage', methods=['GET'])
    def homepage() -> str:
        """
        Uygulamanın ana sayfasını (`/homepage`) render eder.
        """
        # print("API çağrısı: /homepage (Ana Sayfa)") # Geliştirme için log
        return render_template('homepage.html', title="Ana Sayfa")

    # =========================================================================
    # 4.0 PROFİL YÖNETİMİ ROTASI (PROFILE MANAGEMENT ROUTE)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 4.1. profile() : Kullanıcı profil sayfasını yönetir.
    #      Rota: /profile (GET, POST)
    # -------------------------------------------------------------------------
    @app.route('/profile', methods=['GET', 'POST'])
    def profile() -> Any: # render_template veya redirect Response döndürür
        """
        Kullanıcı profil sayfasını görüntüler (GET) ve kullanıcı tarafından
        sağlanan Spotify Client ID ve Client Secret gibi bilgileri günceller (POST).
        Bu sayfaya erişim için kullanıcının oturum açmış olması gerekir.
        """
        # print("API çağrısı: /profile") # Geliştirme için log
        username: Optional[str] = session_is_user_logged_in()
        if not username:
            flash("Profil sayfanıza erişmek için lütfen giriş yapın.", "warning")
            # print("Yetkisiz erişim denemesi: /profile (oturum yok)") # Geliştirme için log
            return redirect(url_for('auth_bp.login_page')) # Uygun giriş sayfası endpoint'i

        # Her istek için (GET veya POST) depo örnekleri gerekebilir.
        # Ancak, POST isteği için zaten oluşturuluyor. GET için profile_services içinde yönetiliyor olabilir.
        # Eğer profile_services kendi depo örneklerini oluşturuyorsa, burada tekrar oluşturmaya gerek yok.
        # Orijinal kodda POST için spotify_repo örneği oluşturuluyor.
        
        # ---------------------------------------------------------------------
        # 4.1.1. GET İsteği Yönetimi (GET Request Handling)
        #        Kullanıcı ve Spotify verilerini alıp profil şablonunu render eder.
        # ---------------------------------------------------------------------
        if request.method == 'GET':
            # print(f"Profil sayfası (GET) isteniyor: Kullanıcı={username}") # Geliştirme için log
            try:
                # `handle_get_request` servisi kullanıcı verilerini, Spotify kimlik bilgilerini
                # ve diğer Spotify verilerini (eğer bağlıysa) alır.
                user_data: Optional[Dict[str, Any]]
                spotify_credentials: Optional[Dict[str, Any]]
                spotify_link_status: bool # Spotify bağlantı durumu
                
                # handle_get_request muhtemelen (user_data, spotify_credentials, spotify_link_status) döndürüyor
                # Orijinal kodda spotify_data diye bir değişken vardı, bu muhtemelen bağlantı durumu veya daha fazlası.
                # Servis tanımına göre bu kısmı ayarlamak gerekebilir.
                # Şimdilik orijinal koddaki gibi bırakıyorum, ancak spotify_data'nın içeriği belirsiz.
                # handle_get_request'in ne döndürdüğüne bağlı olarak bu kısım güncellenmeli.
                # Varsayım: handle_get_request -> (user_data, spotify_credentials, is_spotify_connected_flag)
                
                user_data, spotify_credentials, is_spotify_connected = handle_get_request(username)
                
                # print(f"Profil sayfası için veriler alındı: Kullanıcı={username}") # Geliştirme için log
                return render_template('profile.html',
                                     title=f"{username} - Profil",
                                     user_data=user_data,
                                     spotify_credentials=spotify_credentials,
                                     is_spotify_connected=is_spotify_connected) # Şablona bağlantı durumu iletiliyor

            except Exception as e:
                flash(f"Profil bilgileri yüklenirken bir veritabanı hatası oluştu: {str(e)}", "danger")
                # print(f"Profil sayfası (GET) yüklenirken hata ({username}): {str(e)}") # Geliştirme için log
                # import traceback
                # print(traceback.format_exc()) # Detaylı hata için
                return redirect(url_for('homepage')) # Ana sayfaya yönlendir

        # ---------------------------------------------------------------------
        # 4.1.2. POST İsteği Yönetimi (POST Request Handling - Spotify Bilgileri)
        #        Kullanıcının girdiği Spotify Client ID ve Secret bilgilerini günceller.
        # ---------------------------------------------------------------------
        elif request.method == 'POST':
            # print(f"Profil sayfası (POST) isteği alındı: Kullanıcı={username}") # Geliştirme için log
            # Bu POST isteği özellikle Spotify Client ID/Secret güncellemesi için.
            # Formda başka alanlar varsa, hangi formun gönderildiğini ayırt etmek için
            # bir 'action' veya 'submit_button_name' kontrolü eklenebilir.
            
            client_id: Optional[str] = request.form.get('client_id')
            client_secret: Optional[str] = request.form.get('client_secret')
            # print(f"Alınan Spotify kimlik bilgileri: ClientID='{client_id}', ClientSecret='{client_secret is not None}'") # Geliştirme için log

            # SpotifyRepository örneği, Spotify bilgilerini güncellemek için gereklidir.
            spotify_repo = SpotifyRepository()

            try:
                # Temel doğrulama: Her iki alan da dolu olmalı.
                if not client_id or not client_secret or not client_id.strip() or not client_secret.strip():
                    flash("Spotify Client ID ve Client Secret alanları boş bırakılamaz.", "warning")
                    # print("Spotify kimlik bilgileri güncelleme hatası: Alanlar boş.") # Geliştirme için log
                    return redirect(url_for('user_bp.profile_page')) # user_bp.profile_page veya uygun profil sayfası

                # Servis katmanı veya doğrudan repository kullanarak güncelleme.
                # Orijinal kodda doğrudan repository kullanılıyor.
                # `update_client_id_and_secret_data` servisi import edilmiş ama kullanılmamış.
                # Eğer bu servis kullanılacaksa, çağrı ona göre değiştirilmeli.
                # Örn: success = update_client_id_and_secret_data(username, client_id, client_secret)
                
                success: bool = spotify_repo.spotify_insert_or_update_client_info(username, client_id.strip(), client_secret.strip())

                if success:
                    flash('Spotify Client ID ve Secret bilgileri başarıyla güncellendi.', 'success')
                    # print(f"Spotify kimlik bilgileri başarıyla güncellendi: {username}") # Geliştirme için log
                else:
                    # Bu durum, repository metodunun False döndürmesiyle oluşabilir (örn: kullanıcı bulunamadı).
                    flash('Spotify bilgileri güncellenirken bir sorun oluştu. Lütfen tekrar deneyin.', 'danger')
                    # print(f"Spotify kimlik bilgileri güncellenemedi (repo False döndürdü): {username}") # Geliştirme için log

                return redirect(url_for('user_bp.profile_page'))
            except Exception as e:
                flash(f"Spotify kimlik bilgileri güncellenirken bir hata oluştu: {str(e)}", "danger")
                # print(f"Spotify kimlik bilgileri güncellenirken beklenmedik hata ({username}): {str(e)}") # Geliştirme için log
                # import traceback
                # print(traceback.format_exc()) # Detaylı hata için
                return redirect(url_for('user_bp.profile_page'))
        
        # Eğer ne GET ne de POST ise (teorik olarak olmamalı ama Flask esnek)
        return redirect(url_for('general_bp.homepage'))


    # print("Ana rotalar başarıyla yüklendi.") # Geliştirme için log
# =============================================================================
# Ana Rotalar Modülü Sonu
# =============================================================================
