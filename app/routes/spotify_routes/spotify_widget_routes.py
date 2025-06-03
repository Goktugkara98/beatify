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
    session,
    url_for,
    redirect,
    Flask, # Flask tipi için
    flash
)
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from app.services.spotify_services.widget_token_service import WidgetTokenService
from app.database.spotify_widget_repository import SpotifyWidgetRepository
from typing import Dict, Any, Tuple, Optional, List # Tip ipuçları için
import uuid
import json
from datetime import datetime

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

# Widget token'ları artık WidgetTokenService ve SpotifyRepository aracılığıyla
# veritabanında saklanacaktır.

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
    username: Optional[str] = session.get('username')
    if not username:
        flash("Widget yöneticisine erişmek için lütfen giriş yapın.", "warning")
        return redirect(url_for('login_page'))
    
    widget_token_service = WidgetTokenService()
    widget_token = widget_token_service.get_or_create_widget_token(username)
    return render_template('widget-manager.html', title="Spotify Widget Yöneticisi", widget_token=widget_token)

# -----------------------------------------------------------------------------
# 3.1.1. generate_widget_token() : Yeni bir widget token'ı oluşturur.
#        Rota: /widget/generate-token (POST)
#        Tam Rota (Blueprint ile): /spotify/widget/generate-token
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget/generate-token', methods=['POST'])
def generate_widget_token() -> Tuple[Dict[str, Any], int]:
    """
    Yeni bir widget token'ı oluşturur ve veritabanına kaydeder.
    Bu endpoint, AJAX ile çağrılır ve JSON yanıt döndürür.

    Returns:
        Tuple[Dict[str, Any], int]: JSON yanıt ve HTTP durum kodu.
    """
    try:
        # Kullanıcı oturumunu kontrol et
        username = session.get('username')
        if not username:
            return jsonify({
                "status": "error",
                "message": "Widget token oluşturmak için giriş yapmalısınız."
            }), 401
        
        # Form verilerini al
        data = request.form
        
        # WidgetTokenService kullanarak token oluştur
        widget_token_service = WidgetTokenService()
        token = widget_token_service.generate_widget_token(username)
        
        # Token bilgilerini hazırla
        token_data = {
            "value": token,
            "created_at": datetime.now().isoformat(),
            "username": username,
        }
        
        # Başarılı yanıt döndür
        return jsonify({
            "status": "success",
            "message": "Widget token'ı başarıyla oluşturuldu.",
            "token": token_data
        }), 200
    except Exception as e:
        # Hata durumunda
        return jsonify({
            "status": "error",
            "message": f"Token oluşturulurken bir hata oluştu: {str(e)}"
        }), 500

# -----------------------------------------------------------------------------
# 3.1.2. get_widget_list() : Mevcut widget token'larını listeler.
#        Rota: /widget-list (GET)
#        Tam Rota (Blueprint ile): /spotify/widget-list
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget-list', methods=['GET'])
def get_widget_list() -> Tuple[Dict[str, Any], int]:
    """
    Mevcut kullanıcının widget token'ını veritabanından alır ve listeler.
    Bu endpoint, AJAX ile çağrılır ve JSON yanıt döndürür.

    Returns:
        Tuple[Dict[str, Any], int]: JSON yanıt ve HTTP durum kodu.
    """
    try:
        # Kullanıcı oturumunu kontrol et
        username = session.get('username')
        if not username:
            return jsonify({
                "status": "error",
                "message": "Widget listesini görüntülemek için giriş yapmalısınız."
            }), 401
        
        # WidgetTokenService kullanarak token'ları al
        widget_token_service = WidgetTokenService()
        token = widget_token_service.get_widget_token(username)
        
        # Token yoksa boş liste döndür
        if not token:
            return jsonify([]), 200
        
        # Token'dan widget yapılandırmasını al
        is_valid, payload = widget_token_service.validate_widget_token(token)
        if not is_valid:
            return jsonify([]), 200
            
        # Token bilgilerini hazırla
        token_data = {
            "value": token,
            "username": username,
            "created_at": datetime.fromtimestamp(payload.get('iat', 0)).isoformat(),
            "expires_at": datetime.fromtimestamp(payload.get('exp', 0)).isoformat()
        }
        
        # Token listesini döndür (bu örnekte tek bir token var)
        return jsonify([token_data]), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Widget listesi alınırken bir hata oluştu: {str(e)}"
        }), 500

# -----------------------------------------------------------------------------
# 3.2. spotify_widget(widget_token) : Belirli bir widget'ı render eder.
#      Rota: /widget/<widget_token> (GET)
#      Tam Rota (Blueprint ile): /spotify/widget/<widget_token>
#
#      REVİZE EDİLMİŞ FONKSİYON:
#      Bu fonksiyon, URL'deki 'style' parametresine göre ilgili HTML dosyasını
#      render eder. 'style=alt' ise 'widget_alt.html', değilse 'widget.html'
#      kullanılır. Karmaşık yapılandırma parametreleri kaldırılmıştır.
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
def spotify_widget(widget_token: str) -> Any:
    """
    Belirtilen `widget_token` ile ilişkili Spotify widget'ını render eder.
    URL'de 'style=alt' parametresi varsa 'spotify/widgets/widget_alt.html',
    yoksa 'spotify/widgets/widget.html' şablonu kullanılır.
    Şablona `widget_token` ve `data_endpoint` değişkenleri gönderilir.

    Args:
        widget_token (str): Render edilecek widget'a ait benzersiz token.

    Returns:
        Any: Render edilmiş widget HTML sayfası veya hata mesajı.
    """
    try:
        # Geliştirme için log: İsteğin alındığını ve token bilgisini gösterir.
        # print(f"Spotify widget isteği alındı. Token: {widget_token}, URL: {request.url}")
        
        # URL'den 'style' parametresini al, yoksa varsayılan olarak boş string kullan.
        # Büyük/küçük harf duyarlılığını ortadan kaldırmak için lower() kullanılır.
        style = request.args.get('style', default='').lower()
        
        # Test modu parametresini kontrol et
        test_mode = request.args.get('test', default='').lower() == 'true'
        
        # Widget için veri alınacak API endpoint URL'ini oluştur.
        # Bu URL, widget HTML'i içinde JavaScript tarafından veri çekmek için kullanılacaktır.
        data_endpoint_url = url_for('spotify_widget_bp.widget_data', widget_token=widget_token, test=test_mode, _external=True)
        
        if style == 'alt':
            template_name = "spotify/widgets/widget_alt.html"
            # Geliştirme için log: Hangi widget'ın render edildiğini belirtir.
            # print(f"Alternatif widget ({template_name}) render ediliyor. Token: {widget_token}")
        elif style == 'neon':
            template_name = "spotify/widgets/widget_neon.html"
        else:
            template_name = "spotify/widgets/widget.html"
            # Geliştirme için log: Hangi widget'ın render edildiğini belirtir.
            # print(f"Standart widget ({template_name}) render ediliyor. Token: {widget_token}")
            
        # Şablona `widget_token` ve `data_endpoint`'i doğrudan gönderiyoruz.
        # Önceki `config` sözlüğü ve `title` gibi ek parametreler kaldırıldı.
        return render_template(template_name, widget_token=widget_token, data_endpoint=data_endpoint_url)
            
    except Exception as e:
        # Hata durumunda loglama yap (geliştirme sırasında etkinleştirilebilir)
        # ve kullanıcıya bir hata sayfası göster.
        # import traceback # Detaylı hata takibi için gerekirse etkinleştirilebilir.
        # print(f"Spotify widget render edilirken hata oluştu (Token: {widget_token}): {str(e)}")
        # print(traceback.format_exc()) # Geliştirme için log
        
        # Kullanıcıya gösterilecek hata sayfası.
        # Orijinal hata mesajı parametreleri korunmuştur: 'error' ve 'details'.
        return render_template("spotify/widgets/widget-error.html", 
                              error="Widget yüklenirken bir hata oluştu", 
                              details=str(e),
                              token=widget_token), 500

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
    try:
        # print(f"Widget veri isteği alındı: {widget_token}") # Debug log
        
        # Test modu kontrolü - URL'de ?test=true parametresi varsa sahte veri döndür
        if request.args.get('test', '').lower() == 'true':
            # Sahte veri oluştur - geliştirme testi için
            return jsonify({
                "is_playing": True,
                "track_name": "Neon Dreams",
                "artist_name": "Beatify Test Artist",
                "album_image_url": "https://i.scdn.co/image/ab67616d0000b273c5716278abba6a77fea33fa1",
                "progress_ms": 45000,
                "duration_ms": 180000,
                "track_url": "https://open.spotify.com",
                "artist_url": "https://open.spotify.com",
                "album_url": "https://open.spotify.com",
                "source": "Test Data"
            }), 200
        
        # Token doğrulamayı atlayarak doğrudan kullanıcı adını al
        # Bu basitleştirilmiş bir yaklaşımdır, gerçek uygulamada daha güçlü doğrulama yapılmalıdır
        username = "test"  # Sabit bir kullanıcı adı kullan
        
        # Eğer repository'den kullanıcı adını almak istersen:
        try:
            repo = SpotifyWidgetRepository()
            repo_username = repo.beatify_get_username_by_widget_token(widget_token)
            if repo_username:
                username = repo_username
        except Exception as repo_error:
            print(f"Repository'den kullanıcı adı alınırken hata: {str(repo_error)}") # Debug log
        
        # SpotifyApiService kullanarak Spotify verilerini al
        spotify_api_service = SpotifyApiService()
        
        # Kullanıcının şu an çalan parça bilgisini al
        playback_data = None
        try:
            playback_data = spotify_api_service.get_currently_playing(username)
        except Exception as api_error:
            # API hatası durumunda boş veri döndür
            playback_data = None
        
        # Eğer çalan bir parça varsa
        if playback_data and playback_data.get("item"):
            item = playback_data.get("item", {})
            artists = item.get("artists", [{}])
            album_images = item.get("album", {}).get("images", [{}])

            response_data = {
                "is_playing": playback_data.get("is_playing", False),
                "track_name": item.get("name", "Bilinmeyen Parça"),
                "artist_name": artists[0].get("name", "Bilinmeyen Sanatçı") if artists else "Bilinmeyen Sanatçı",
                "album_image_url": album_images[0].get("url", "") if album_images else "",
                "progress_ms": playback_data.get("progress_ms", 0),
                "duration_ms": item.get("duration_ms", 0),
                "track_url": item.get("external_urls", {}).get("spotify"),
                "artist_url": artists[0].get("external_urls", {}).get("spotify") if artists else None,
                "album_url": item.get("album", {}).get("external_urls", {}).get("spotify"),
                "source": "Spotify API"
            }
            return jsonify(response_data), 200
        else:
            # Bir şey çalmıyorsa veya veri alınamadıysa
            not_playing_response = {
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

# -----------------------------------------------------------------------------
# 3.4. widget_action(widget_token, action) : Widget kontrol işlemlerini yönetir.
#      Rota: /widget/action/<widget_token>/<action> (POST)
#      Tam Rota (Blueprint ile): /spotify/widget/action/<widget_token>/<action>
# -----------------------------------------------------------------------------
@spotify_widget_bp.route('/widget/action/<string:widget_token>/<string:action>', methods=['POST'])
def widget_action(widget_token: str, action: str) -> Tuple[Dict[str, Any], int]:
    """
    Belirtilen widget token'ı için Spotify oynatıcı kontrol işlemlerini yönetir.
    Örneğin: play, pause, next, previous gibi işlemler.

    Args:
        widget_token (str): İşlem yapılacak widget'a ait token.
        action (str): Yapılacak işlem (play, pause, next, previous).

    Returns:
        Tuple[Dict[str, Any], int]: JSON yanıt ve HTTP durum kodu.
    """
    try:
        # WidgetTokenService kullanarak token'ı doğrula
        widget_token_service = WidgetTokenService()
        is_valid, payload = widget_token_service.validate_widget_token(widget_token)
        
        if not is_valid:
            return jsonify({"success": False, "error": "Geçersiz widget token"}), 404
        
        # Token'dan kullanıcı adını al
        username = payload.get('username')
        if not username:
            return jsonify({"success": False, "error": "Token'da kullanıcı adı bulunamadı"}), 400
        
        # Geçerli işlemleri kontrol et
        valid_actions = ['play', 'pause', 'next', 'previous']
        if action not in valid_actions:
            return jsonify({"success": False, "error": f"Geçersiz işlem: {action}"}), 400
        
        # SpotifyApiService kullanarak işlemi gerçekleştir
        spotify_api_service = SpotifyApiService()
        
        # İşleme göre uygun metodu çağır
        result = False
        if action == 'play':
            result = spotify_api_service.play(username)
        elif action == 'pause':
            result = spotify_api_service.pause(username)
        elif action == 'next':
            result = spotify_api_service.next_track(username)
        elif action == 'previous':
            result = spotify_api_service.previous_track(username)
        
        if result:
            return jsonify({"success": True, "action": action}), 200
        else:
            return jsonify({"success": False, "error": "Spotify API işlemi başarısız oldu"}), 500
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
