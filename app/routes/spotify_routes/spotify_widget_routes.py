# =============================================================================
# Spotify Widget Rotaları Modülü (Spotify Widget Routes Module)
# =============================================================================
# Bu modül, Spotify entegrasyonu için gömülebilir widget'ların (örn: şu an
# çalan parça göstergesi) sunulması ve bu widget'lar için veri sağlanması
# amacıyla kullanılan Flask rotalarını tanımlar. Bir Blueprint kullanılarak
# bu rotalar gruplandırılır ve ana uygulamaya kaydedilir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenleri ve uygulama servislerinin içe aktarılması.
# 2.0 BLUEPRINT TANIMI (BLUEPRINT DEFINITION)
#     : Spotify widget rotaları için bir Flask Blueprint oluşturulması.
# 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
#     (Bu Blueprint'e bağlı rotalar)
#     3.1. widget_manager()
#          : Widget yönetim arayüzünü sunar.
#            Rota: /widget-manager (GET) (Blueprint'e göre /spotify/widget-manager)
#     3.2. spotify_widget(widget_token)
#          : Belirli bir widget token'ı için widget'ı render eder.
#            Rota: /widget/<widget_token> (GET) (Blueprint'e göre /spotify/widget/<widget_token>)
#     3.3. widget_data(widget_token)
#          : Belirli bir widget token'ı için widget'a veri sağlayan API endpoint'i.
#            Rota: /api/widget-data/<widget_token> (GET) (Blueprint'e göre /spotify/api/widget-data/<widget_token>)
# 4.0 BLUEPRINT KAYIT FONKSİYONU (BLUEPRINT REGISTRATION FUNCTION)
#     4.1. init_spotify_widget_routes(app)
#          : Tanımlanan Spotify widget Blueprint'ini ana Flask uygulamasına kaydeder.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session, # Session kullanılmıyor gibi görünüyor, ancak import edilmiş.
    url_for,
    Flask # Flask tipi için
)
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from typing import Dict, Any, Tuple, Optional # Tip ipuçları için

# =============================================================================
# 2.0 BLUEPRINT TANIMI (BLUEPRINT DEFINITION)
# =============================================================================
# Spotify widget'ları ile ilgili rotaları gruplamak için bir Blueprint oluşturuluyor.
# Bu Blueprint, ana uygulamaya '/spotify' URL öneki ile kaydedilecektir.
spotify_widget_bp = Blueprint(
    name='spotify_widget_bp',  # Blueprint için benzersiz bir ad
    import_name=__name__,      # Bu modülün adı
    template_folder='../templates', # Şablonların aranacağı klasör (app/templates varsayılır)
    # url_prefix='/spotify' -> Bu, register_blueprint sırasında belirtilecek.
)
# print("Spotify Widget Blueprint'i oluşturuldu.") # Geliştirme için log

# =============================================================================
# 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================
# Bu bölümde, `spotify_widget_bp` Blueprint'ine bağlı rota fonksiyonları tanımlanır.

# -----------------------------------------------------------------------------
# 3.1. widget_manager() : Widget yönetim arayüzünü sunar.
#      Rota: /widget-manager (GET)
#      Tam Rota (Blueprint ile): /spotify/widget-manager
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget-manager', methods=['GET'])
def widget_manager() -> str:
    """
    Kullanıcıların Spotify widget'larını yönetebileceği bir arayüzü sunar.
    Bu sayfa, widget oluşturma, yapılandırma ve mevcut widget'ları
    görüntüleme gibi işlevler içerebilir.

    Returns:
        str: Render edilmiş 'spotify/widget-manager.html' şablonu.
    """
    # print("API çağrısı: /spotify/widget-manager") # Geliştirme için log
    # Bu sayfanın kullanıcı oturumu gerektirip gerektirmediği kontrol edilebilir.
    # Örneğin:
    # username: Optional[str] = session.get('username')
    # if not username:
    #     flash("Widget yöneticisine erişmek için lütfen giriş yapın.", "warning")
    #     return redirect(url_for('auth_bp.login_page'))
    return render_template('widget-manager.html', title="Spotify Widget Yöneticisi")

# -----------------------------------------------------------------------------
# 3.2. spotify_widget(widget_token) : Belirli bir widget'ı render eder.
#      Rota: /widget/<widget_token> (GET)
#      Tam Rota (Blueprint ile): /spotify/widget/<widget_token>
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
def spotify_widget(widget_token: str) -> Any: # render_template str veya Response döndürebilir
    """
    Belirtilen `widget_token` ile ilişkili Spotify widget'ını render eder.
    Widget türü (örn: 'now-playing') ve diğer yapılandırma ayarları
    URL parametreleri veya veritabanından alınarak widget şablonuna iletilir.

    Args:
        widget_token (str): Render edilecek widget'a ait benzersiz token.

    Returns:
        Any: Render edilmiş widget HTML sayfası veya hata mesajı.
    """
    # print(f"API çağrısı: /spotify/widget/{widget_token}") # Geliştirme için log
    try:
        # TODO: Gerçek token doğrulama ve yapılandırma yükleme mekanizması implemente edilmeli.
        # Veritabanından widget_token'a göre widget yapılandırması çekilmeli.
        # Örnek: widget_config_from_db = spotify_widget_service.get_widget_config_by_token(widget_token)
        # if not widget_config_from_db:
        #     return "Geçersiz widget token", 404

        # Geçici test amaçlı token ve yapılandırma:
        if widget_token == 'abcd': # Bu kısım gerçek token doğrulama ile değiştirilmeli.
            widget_type: str = request.args.get('type', 'now-playing') # Varsayılan widget türü
            
            # Gerçek yapılandırma veritabanından veya servisten gelmeli.
            # Bu değerler, widget oluşturulurken kullanıcı tarafından belirlenmiş olmalı.
            widget_config: Dict[str, Any] = {
                'type': widget_type,
                'theme': request.args.get('theme', 'dark'), # 'dark' veya 'light'
                'show_album_art': request.args.get('albumart', 'true').lower() == 'true',
                # 'background_color': '#121212', # Temadan gelmeli
                # 'text_color': '#ffffff',       # Temadan gelmeli
                # 'accent_color': '#1DB954',     # Temadan gelmeli
                'font_size': request.args.get('fontsize', 'medium'),
                # Veri API endpoint'i, widget'ın veriyi çekeceği yer.
                'dataEndpoint': url_for('spotify_widget_bp.widget_data', widget_token=widget_token, _external=True),
                'widgetToken': widget_token # Şablonun token'ı bilmesi gerekebilir
            }
            # print(f"Widget render ediliyor: Token={widget_token}, Config={widget_config}") # Geliştirme için log

            # Widget türüne göre uygun şablonu seç
            # Şablon yolu: app/templates/spotify/widgets/<widget_type>.html
            template_name: str = f"spotify/widgets/{widget_config['type']}.html"
            
            return render_template(template_name, config=widget_config, title=f"Spotify Widget - {widget_type.replace('-', ' ').title()}")
        else:
            # print(f"Geçersiz widget token denemesi: {widget_token}") # Geliştirme için log
            return "Geçersiz widget token", 404 # HTTP 404 Not Found
    except Exception as e:
        # print(f"Spotify widget render edilirken hata oluştu (Token: {widget_token}): {str(e)}") # Geliştirme için log
        # import traceback
        # print(traceback.format_exc()) # Detaylı hata için
        # Kullanıcıya daha genel bir hata mesajı gösterilebilir.
        return "Widget render edilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.", 500 # HTTP 500 Internal Server Error

# -----------------------------------------------------------------------------
# 3.3. widget_data(widget_token) : Widget için veri sağlayan API endpoint'i.
#      Rota: /api/widget-data/<widget_token> (GET)
#      Tam Rota (Blueprint ile): /spotify/api/widget-data/<widget_token>
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/api/widget-data/<string:widget_token>', methods=['GET'])
def widget_data(widget_token: str) -> Tuple[Dict[str, Any], int]:
    """
    Belirtilen `widget_token` ile ilişkili Spotify widget'ı için
    gerekli verileri (örn: şu an çalan parça bilgisi) JSON formatında sağlar.
    Bu endpoint, widget tarafından periyodik olarak çağrılır.

    Args:
        widget_token (str): Verisi talep edilen widget'a ait benzersiz token.

    Returns:
        Tuple[Dict[str, Any], int]: JSON formatında widget verisi ve HTTP durum kodu.
    """
    # print(f"API çağrısı (widget verisi): /spotify/api/widget-data/{widget_token}") # Geliştirme için log
    try:
        # TODO: Gerçek token doğrulama ve kullanıcıya bağlı Spotify API servisi kullanımı.
        # 1. widget_token'ı doğrula ve hangi Beatify kullanıcısına ait olduğunu bul.
        #    (örn: user_widget_config = spotify_widget_service.get_user_by_widget_token(widget_token))
        # 2. O kullanıcıya ait SpotifyApiService örneğini kullanarak veri çek.
        #    (örn: beatify_username = user_widget_config.username)
        #    (örn: playback_data = spotify_api_service.get_currently_playing(beatify_username))

        # Geçici test amaçlı token ve kullanıcı adı:
        if widget_token != 'abcd': # Bu kısım gerçek token doğrulama ile değiştirilmeli.
            # print(f"Geçersiz widget token (veri API): {widget_token}") # Geliştirme için log
            return jsonify({"error": "Geçersiz widget token"}), 404

        # Test için sabit bir kullanıcı adı veya token'dan çözümlenen kullanıcı adı kullanılmalı.
        # `SpotifyApiService` örneği, kullanıcıya özel tokenları yönetebilmeli.
        # Şu anki `SpotifyApiService` muhtemelen global veya tekil bir yapılandırma kullanıyor.
        # Bu, çok kullanıcılı bir sistemde sorun yaratır. Servislerin kullanıcı bazlı olması gerekir.
        
        # GELIŞTIRME AMAÇLI: API çağrısını atlayıp test verisi döndürüyoruz
        # Gerçek uygulamada bu kısım kaldırılmalı ve gerçek API çağrısı yapılmalı
        
        # Test verisi oluştur
        playback_data = {
            "is_playing": True,
            "item": {
                "name": "Test Şarkısı",
                "artists": [{"name": "Test Sanatçı", "external_urls": {"spotify": "https://open.spotify.com/artist/test"}}],
                "album": {
                    "images": [{"url": "https://i.scdn.co/image/ab67616d0000b273c5716278abba6a77916d0fe7"}],
                    "external_urls": {"spotify": "https://open.spotify.com/album/test"}
                },
                "duration_ms": 180000,  # 3 dakika
                "external_urls": {"spotify": "https://open.spotify.com/track/test"}
            },
            "progress_ms": 45000  # 45 saniye
        }
        
        # Gerçek API çağrısı (şu an devre dışı)
        '''
        beatify_username_for_widget: str = "serseriyim1" # Bu, token'dan çözümlenmeli.
        spotify_api_service = SpotifyApiService() # Bu servis kullanıcıya özel olmalı.
        # print(f"Widget verisi için Spotify API çağrısı yapılıyor. Kullanıcı: {beatify_username_for_widget}, Token: {widget_token}") # Geliştirme için log
        
        playback_data: Optional[Dict[str, Any]] = None
        try:
            # `get_currently_playing` metodu, belirtilen Beatify kullanıcısının
            # Spotify token'larını kullanarak API isteği yapmalı.
            playback_data = spotify_api_service.get_currently_playing(beatify_username_for_widget)
            # print(f"Spotify API'den alınan çalma verisi (Token: {widget_token}): {playback_data}") # Geliştirme için log
        except Exception as api_call_error:
            # print(f"Spotify API'den veri alınırken hata (Token: {widget_token}, Kullanıcı: {beatify_username_for_widget}): {str(api_call_error)}") # Geliştirme için log
            # API'den hata gelirse veya bağlantı kurulamazsa, "bir şey çalmıyor" durumu döndür.
            pass # Hata durumunda playback_data None kalacak ve aşağıda işlenecek.
        '''

        # Test verisi için her zaman True olacak, gerçek API için kontrol gerekli
        if playback_data and playback_data.get("item"):
            item: Dict[str, Any] = playback_data.get("item", {})
            artists: List[Dict[str, Any]] = item.get("artists", [{}])
            album_images: List[Dict[str, Any]] = item.get("album", {}).get("images", [{}])

            response_data: Dict[str, Any] = {
                "is_playing": playback_data.get("is_playing", False),
                "track_name": item.get("name", "Bilinmeyen Parça"),
                "artist_name": artists[0].get("name", "Bilinmeyen Sanatçı") if artists else "Bilinmeyen Sanatçı",
                "album_image_url": album_images[0].get("url", "") if album_images else "",
                "progress_ms": playback_data.get("progress_ms", 0),
                "duration_ms": item.get("duration_ms", 0),
                "track_url": item.get("external_urls", {}).get("spotify"),
                "artist_url": artists[0].get("external_urls", {}).get("spotify") if artists else None,
                "album_url": item.get("album", {}).get("external_urls", {}).get("spotify"),
                "source": "Spotify API" # Verinin kaynağını belirtmek iyi bir pratik.
            }
            # print(f"Widget için hazırlanan yanıt verisi (Token: {widget_token}): {response_data}") # Geliştirme için log
            return jsonify(response_data), 200
        else:
            # Bir şey çalmıyorsa veya veri alınamadıysa
            # print(f"Widget için çalma verisi yok veya 'item' bulunamadı (Token: {widget_token}). 'Çalmıyor' durumu döndürülüyor.") # Geliştirme için log
            not_playing_response: Dict[str, Any] = {
                "is_playing": False,
                "track_name": "Bir Şey Çalmıyor",
                "artist_name": "-",
                "album_image_url": "", # Varsayılan bir resim gösterilebilir.
                "progress_ms": 0,
                "duration_ms": 0,
                "source": "Spotify API"
            }
            return jsonify(not_playing_response), 200

    except Exception as e:
        # print(f"Widget veri API'sinde genel hata (Token: {widget_token}): {str(e)}") # Geliştirme için log
        # import traceback
        # print(traceback.format_exc()) # Detaylı hata için
        return jsonify({"error": "Widget verisi alınırken sunucu hatası oluştu."}), 500

# =============================================================================
# 4.0 BLUEPRINT KAYIT FONKSİYONU (BLUEPRINT REGISTRATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 4.1. init_spotify_widget_routes(app) : Spotify widget Blueprint'ini kaydeder.
# -----------------------------------------------------------------------------
def init_spotify_widget_routes(app: Flask) -> None:
    """
    `spotify_widget_bp` Blueprint'ini belirtilen Flask uygulamasına kaydeder.
    Bu işlem, Blueprint içinde tanımlanan tüm rotaların uygulama tarafından
    erişilebilir olmasını sağlar. Rotalar '/spotify' URL öneki altında yer alır.

    Args:
        app (Flask): Blueprint'in kaydedileceği Flask uygulama nesnesi.
    """
    app.register_blueprint(spotify_widget_bp, url_prefix='/spotify')
    # print("Spotify Widget Blueprint'i '/spotify' öneki ile uygulamaya kaydedildi.") # Geliştirme için log

# =============================================================================
# Spotify Widget Rotaları Modülü Sonu
# =============================================================================
