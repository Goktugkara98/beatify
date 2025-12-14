# =============================================================================
# Spotify Widget Rota Modülü (Spotify Widget Routes Module)
# =============================================================================
# Bu modül, gömülebilir Spotify widget'larının yönetimi, render edilmesi
# ve veri sağlaması için gerekli tüm rotaları içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  SABİTLER & LOGGER (CONSTANTS & LOGGER)
#      2.1. logger
#
# 3.0  BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
#      3.1. spotify_widget_bp
#      3.2. widget_token_service
#      3.3. spotify_player_service
#      3.4. widget_repo
#
# 4.0  YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
#      4.1. _get_widget_playback_data(username)
#
# 5.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      5.1. Arayüz Rotaları (UI Routes)
#           5.1.1. widget_manager(theme=None) -> @spotify_widget_bp.route('/widget-manager[/<theme>]', methods=['GET'])
#           5.1.2. update_widget_config() -> @spotify_widget_bp.route('/widget/update-config', methods=['POST'])
#           5.1.3. create_widget() -> @spotify_widget_bp.route('/widget/create', methods=['POST'])
#           5.1.4. delete_widget() -> @spotify_widget_bp.route('/widget/delete', methods=['POST'])
#           5.1.5. debug_widgets() -> @spotify_widget_bp.route('/debug/widgets', methods=['GET'])
#           5.1.6. spotify_widget(widget_token) -> @spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
#      5.2. API Rotaları (API Routes)
#           5.2.1. get_widget_list() -> @spotify_widget_bp.route('/widget-list', methods=['GET'])
#           5.2.2. widget_data(widget_token) -> @spotify_widget_bp.route('/api/widget-data/<string:widget_token>', methods=['GET'])
#
# 6.0  ROTA KAYDI (ROUTE REGISTRATION)
#      6.1. init_spotify_widget_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import datetime
import json
import logging
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, Flask, jsonify, render_template, request

# Servisler ve Depolar
from app.services.auth_service import login_required, session_is_user_logged_in
from app.services.spotify.player_service import SpotifyPlayerService
from app.services.spotify.widget.token_service import WidgetTokenService
from app.database.repositories.widget_repository import SpotifyWidgetRepository

# =============================================================================
# 2.0 SABİTLER & LOGGER (CONSTANTS & LOGGER)
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# 3.0 BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# =============================================================================
spotify_widget_bp = Blueprint('spotify_widget_bp', __name__, template_folder='../templates')
widget_token_service = WidgetTokenService()
spotify_player_service = SpotifyPlayerService()
widget_repo = SpotifyWidgetRepository()

# =============================================================================
# 4.0 YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
# =============================================================================

def _get_widget_playback_data(username: str) -> Dict[str, Any]:
    """Kullanıcının şu an çalan parça bilgilerini getirir."""
    try:
        logger.debug("_get_widget_playback_data(): username='%s' için playback verisi isteniyor", username)
        playback_data = spotify_player_service.get_playback_state(username)
        if not playback_data:
            logger.info("_get_widget_playback_data(): aktif çalma durumu bulunamadı: username='%s'", username)
            return {"is_playing": False, "error": "No active device or playback"}
        logger.info(
            "_get_widget_playback_data(): veri alındı: username='%s', is_playing=%s, track_id=%s",
            username,
            playback_data.get("is_playing"),
            (playback_data.get("item") or {}).get("id"),
        )
        return playback_data
    except Exception as e:
        logger.error("Playback verisi alınırken hata (Kullanıcı: %s): %s", username, e, exc_info=True)
        return {"is_playing": False, "error": str(e)}
# =============================================================================
# 5.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================

# -------------------------------------------------------------------------
# 5.1. Arayüz Rotaları (UI Routes)
# -------------------------------------------------------------------------

@spotify_widget_bp.route('/widget-manager', defaults={'theme': None}, methods=['GET'])
@spotify_widget_bp.route('/widget-manager/<string:theme>', methods=['GET'])
@login_required
def widget_manager(theme: Optional[str] = None) -> Any:
    """
    Kullanıcıların Spotify widget'larını yönetebileceği arayüzü sunar.
    
    Aşamalı akış:
    - /spotify/widget-manager           -> Sadece hazır widget (tema) kartlarını gösteren galeri görünümü
    - /spotify/widget-manager/<theme>   -> Seçilen tema için önizleme + ayar editörü bulunan detay görünüm
    """
    username = session_is_user_logged_in()
    logger.info("Kullanıcı widget yöneticisine erişti: username='%s', requested_theme='%s'", username, theme)
    
    # Desteklenen widget tipleri
    supported_types = ['modern', 'classic']
    widgets_data = {}
    
    # Her tip için widget'ı getir veya oluştur
    for w_type in supported_types:
        token = widget_token_service.get_or_create_widget_token(username, widget_type=w_type)
        config = widget_repo.get_widget_config_by_token(token)
        
        # Config içinde theme name yoksa veya yanlışsa düzelt
        if not config:
            config = {}
        
        if 'theme' not in config:
            config['theme'] = {}
        config['theme']['name'] = w_type
            
        widgets_data[w_type] = {
            'token': token,
            'config': config
        }

    # ------------------------------------------------------------------
    # Tema seçimi (galeri / detay modu)
    # ------------------------------------------------------------------
    current_theme: Optional[str] = None
    current_widget: Optional[Dict[str, Any]] = None

    # Eğer URL'de geçerli bir tema verilmişse, detay görünümüne geç
    if theme and theme in widgets_data:
        current_theme = theme
        current_widget = widgets_data[theme]
    else:
        # Tema yoksa veya geçersizse: sadece galeri görünümü (current_theme None kalır)
        current_theme = None
        current_widget = None
    
    logger.info(
        "Widget yöneticisi için veriler hazır: username='%s', types=%s, current_theme='%s'",
        username,
        list(widgets_data.keys()),
        current_theme,
    )
    
    widget_token = current_widget['token'] if current_widget else None
    current_config = current_widget['config'] if current_widget else None
    
    return render_template('spotify/widget-manager.html', 
                           title="Spotify Widget Yöneticisi", 
                           widgets_data=widgets_data,
                           current_theme=current_theme,
                           widget_token=widget_token,  # Detay görünüm yoksa None
                           config=current_config)       # Detay görünüm yoksa None

@spotify_widget_bp.route('/widget/update-config', methods=['POST'])
@login_required
def update_widget_config() -> Any:
    """Widget konfigürasyonunu günceller (tema seçimi vb.)."""
    username = session_is_user_logged_in()
    try:
        data = request.get_json()
        widget_token = data.get('widget_token')
        theme = data.get('theme')
        config_data = data.get('config')
        widget_name = data.get('widget_name')
        
        # Token her zaman zorunlu.
        # Theme, Config veya widget_name'den en az biri olmalı.
        if not widget_token or (not theme and not config_data and not widget_name):
            return jsonify({"error": "Eksik parametreler"}), 400
            
        # Token'ın kullanıcıya ait olup olmadığını kontrol et
        token_owner = widget_repo.get_username_by_widget_token(widget_token)
        if token_owner != username:
            return jsonify({"error": "Yetkisiz işlem"}), 403
            
        # Mevcut konfigürasyonu al
        current_config = widget_repo.get_widget_config_by_token(widget_token) or {}
        if not isinstance(current_config, dict):
            current_config = {}
        
        # Senaryo 1: Tema Değişimi
        if 'theme' in data and isinstance(data['theme'], str):
             if 'theme' not in current_config: current_config['theme'] = {}
             current_config['theme']['name'] = data['theme']
        
        # Senaryo 2: Full Config Güncellemesi (Animasyon ayarları vb.)
        if 'config' in data and isinstance(data['config'], dict):
            new_config = data['config']
            
            # Mevcut tema bilgisini güvenli bir şekilde al
            current_theme_obj = current_config.get('theme')
            if not isinstance(current_theme_obj, dict):
                current_theme_obj = {'name': 'modern'}
            
            # Yeni config'de tema yoksa veya bozuksa, mevcut/varsayılan temayı ekle
            if 'theme' not in new_config or not isinstance(new_config['theme'], dict):
                new_config['theme'] = current_theme_obj
            else:
                # Tema objesi var ama name yoksa
                if 'name' not in new_config['theme']:
                    new_config['theme']['name'] = current_theme_obj.get('name', 'modern')
            
            current_config = new_config

        # Senaryo 3: Sadece widget adı güncellemesi
        # (Config/theme değiştirmeden isim güncellemesine izin ver)
        new_widget_name: Optional[str] = None
        if 'widget_name' in data and isinstance(data['widget_name'], str):
            candidate = data['widget_name'].strip()
            if candidate:
                # DB alanı 255, UI tarafı 80; güvenli tarafta kısalt
                new_widget_name = candidate[:255]
        
        # Kayıt için veriyi hazırla
        # Mevcut widget kaydından diğer bilgileri alalım
        full_widget = widget_repo.get_data_by_widget_token(widget_token)

        # Widget tipi: DB varsa oradan, yoksa config.theme.name'den
        inferred_type = None
        if isinstance(current_config.get('theme'), dict):
            inferred_type = current_config.get('theme', {}).get('name')
        widget_type_value = (
            (full_widget.get('widget_type') if full_widget else None)
            or inferred_type
            or "now_playing"
        )
        
        widget_data = {
            "beatify_username": username,
            "widget_token": widget_token,
            "widget_name": new_widget_name
                or (full_widget.get('widget_name', "Spotify Widget") if full_widget else "Spotify Widget"),
            "widget_type": widget_type_value,
            "config_data": json.dumps(current_config),
            "spotify_user_id": full_widget.get('spotify_user_id') if full_widget else None
        }
        
        success = widget_repo.store_widget_config(widget_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Widget güncellendi",
                "widget_token": widget_token,
                "widget_name": widget_data["widget_name"],
                "widget_type": widget_data["widget_type"],
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }), 200
        else:
            return jsonify({"error": "Widget güncellenemedi"}), 500

    except Exception as e:
        logger.error(f"Widget config güncellenirken hata: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@spotify_widget_bp.route('/widget/create', methods=['POST'])
@login_required
def create_widget() -> Any:
    """
    Mevcut bir widget'ı baz alarak yeni bir widget kopyası oluşturur.

    Body:
      - base_widget_token (str)  (zorunlu)
      - widget_name (str)        (opsiyonel)
    """
    username = session_is_user_logged_in()
    try:
        data = request.get_json() or {}
        base_widget_token = data.get('base_widget_token')
        requested_name = data.get('widget_name')

        if not base_widget_token:
            return jsonify({"error": "Eksik parametre: base_widget_token"}), 400

        # Yetkilendirme: base token kullanıcıya ait mi?
        token_owner = widget_repo.get_username_by_widget_token(base_widget_token)
        if token_owner != username:
            return jsonify({"error": "Yetkisiz işlem"}), 403

        base_row = widget_repo.get_data_by_widget_token(base_widget_token)
        base_config = widget_repo.get_widget_config_by_token(base_widget_token) or {}
        if not isinstance(base_config, dict):
            base_config = {}

        # Tema adı üzerinden widget_type'ı türet
        theme_name = None
        if isinstance(base_config.get('theme'), dict):
            theme_name = base_config.get('theme', {}).get('name')
        widget_type_value = (theme_name or (base_row.get('widget_type') if base_row else None) or "now_playing")

        # İsim belirle
        base_name = (base_row.get('widget_name') if base_row else None) or "Spotify Widget"
        new_name = None
        if isinstance(requested_name, str) and requested_name.strip():
            new_name = requested_name.strip()[:255]
        else:
            suffix = "Kopya"
            new_name = f"{base_name} ({suffix})"
            if len(new_name) > 255:
                new_name = new_name[:255]

        spotify_user_id = base_row.get('spotify_user_id') if base_row else None

        # Yeni token üret ve kaydet (çakışma ihtimaline karşı birkaç deneme)
        new_token: Optional[str] = None
        for _ in range(5):
            candidate = widget_token_service.generate_widget_token(username)
            token_data = {
                "beatify_username": username,
                "widget_token": candidate,
                "widget_name": new_name,
                "widget_type": widget_type_value,
                "config_data": json.dumps(base_config),
                "spotify_user_id": spotify_user_id,
            }
            stored = widget_repo.store_widget_config(token_data)
            if stored:
                new_token = candidate
                break

        if not new_token:
            return jsonify({"error": "Widget oluşturulamadı"}), 500

        return jsonify({
            "success": True,
            "message": "Widget kaydedildi",
            "widget_token": new_token,
            "widget_name": new_name,
            "widget_type": widget_type_value,
            "config_data": base_config,
        }), 201
    except Exception as e:
        logger.error("Widget create sırasında hata: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@spotify_widget_bp.route('/widget/delete', methods=['POST'])
@login_required
def delete_widget() -> Any:
    """
    Widget'ı siler.

    Body:
      - widget_token (str) (zorunlu)
    """
    username = session_is_user_logged_in()
    try:
        data = request.get_json() or {}
        widget_token = data.get('widget_token')
        if not widget_token:
            return jsonify({"error": "Eksik parametre: widget_token"}), 400

        token_owner = widget_repo.get_username_by_widget_token(widget_token)
        if token_owner != username:
            return jsonify({"error": "Yetkisiz işlem"}), 403

        success = widget_repo.delete_widget_by_token(widget_token)
        if not success:
            return jsonify({"error": "Widget silinemedi"}), 500

        return jsonify({"success": True, "message": "Widget silindi", "widget_token": widget_token}), 200
    except Exception as e:
        logger.error("Widget delete sırasında hata: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@spotify_widget_bp.route('/debug/widgets', methods=['GET'])
@login_required
def debug_widgets() -> Any:
    """
    DEBUG AMAÇLI:
    widgets tablosundaki tüm satırları JSON olarak döndürür
    ve her satırı log'lara detaylı olarak yazar.
    """
    username = session_is_user_logged_in()
    logger.info("DEBUG /spotify/debug/widgets isteği: username='%s'", username)

    rows = SpotifyWidgetRepository().debug_get_all_widgets()
    logger.info("DEBUG widgets satır sayısı: %s", len(rows))

    for idx, row in enumerate(rows, start=1):
        logger.info("DEBUG widgets satır %s:", idx)
        for key, value in row.items():
            logger.info("    %s = %r", key, value)

    return jsonify(rows), 200

@spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
def spotify_widget(widget_token: str) -> Any:
    """Belirtilen widget_token ile ilişkili Spotify widget'ını render eder.

    Not:
        - Normal kullanımda canlı Spotify verisiyle çalışır.
        - Eğer ?demo=1 query parametresi gönderilirse, widget içindeki
          veri istekleri mock/demo verisiyle cevaplanacak şekilde
          yapılandırılır (önizleme modu).
    """
    logger.info("Spotify widget render talebi alındı: widget_token='%s', query_args=%s", widget_token, request.args)
    try:
        config = widget_repo.get_widget_config_by_token(widget_token)
        if not config:
            logger.warning("Spotify widget config bulunamadı, geçersiz token: widget_token='%s'", widget_token)
            return render_template("spotify/widgets/widget-error.html", error="Widget bulunamadı."), 404

        theme = config.get('theme', {}).get('name', 'modern')
        template_name = f"spotify/widgets/widget_{theme}/widget_{theme}.html"

        # Önizleme (demo) modu bilgisi – template içinde endpoint'e yansıtacağız
        is_demo_mode = request.args.get('demo') == '1'

        logger.info(
            "Spotify widget config yüklendi: widget_token='%s', theme='%s', template='%s', demo_mode=%s",
            widget_token,
            theme,
            template_name,
            is_demo_mode,
        )

        return render_template(
            template_name,
            config=config,
            widget_token=widget_token,
            preview_mode=is_demo_mode,
        )
    except Exception as e:
        logger.error("Widget render edilirken hata (Token: %s): %s", widget_token, e, exc_info=True)
        return render_template("spotify/widgets/widget-error.html", error="Widget yüklenirken bir hata oluştu."), 500

# -------------------------------------------------------------------------
# 5.2. API Rotaları (API Routes)
# -------------------------------------------------------------------------

@spotify_widget_bp.route('/widget-list', methods=['GET'])
@login_required
def get_widget_list() -> Tuple[Dict[str, Any], int]:
    """Mevcut kullanıcının widget'larını listeler."""
    username = session_is_user_logged_in()
    try:
        widgets = widget_repo.get_widgets_by_username(username)
        return jsonify(widgets), 200
    except Exception as e:
        logger.error(f"Widget listesi alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
        return jsonify({"error": "Widget listesi alınamadı."}), 500

@spotify_widget_bp.route('/api/widget-data/<string:widget_token>', methods=['GET'])
def widget_data(widget_token: str) -> Tuple[Dict[str, Any], int]:
    """Widget için gerekli verileri (örn: şu an çalan parça) JSON formatında sağlar.

    Normal kullanımda gerçek Spotify playback verisini döndürür.
    Eğer istek ?demo=1 ile gelirse, Spotify'a hiç gitmeden mock/demo
    verisi döndürülür. Böylece Widget Studio önizlemesinde gerçek
    çalma durumuna ihtiyaç kalmaz.
    """
    logger.debug(
        "widget_data(): API isteği alındı: widget_token='%s', query_args=%s",
        widget_token,
        request.args,
    )

    # Token'ı doğrula (demo modda bile güvenlik için token'ı kontrol ediyoruz)
    is_valid, payload = widget_token_service.validate_widget_token(widget_token)
    
    if not is_valid:
        logger.warning("Geçersiz widget token ile veri talebi: widget_token='%s'", widget_token)
        return jsonify({
            "error": "Geçersiz widget token",
            "details": "Lütfen widget token'ınızı kontrol edin veya yeni bir token oluşturun."
        }), 401
        
    username = payload.get('beatify_username')
    if not username:
        logger.error("widget_data(): Token geçerli ancak kullanıcı adı eksik: widget_token='%s'", widget_token)
        return jsonify({
            "error": "Widget yapılandırmasında hata",
            "details": "Widget yapılandırmasında kullanıcı bilgisi bulunamadı."
        }), 500

    # --------------------------------------------------------------
    # DEMO / MOCK MODU: ?demo=1 ise sabit örnek veri döndür
    # --------------------------------------------------------------
    if request.args.get('demo') == '1':
        logger.info(
            "widget_data(): demo=1 ile istek alındı, mock veri döndürülüyor. username='%s', widget_token='%s'",
            username,
            widget_token,
        )
        # Frontend'deki demo_data.js ile aynı şemaya yakın basit bir örnek
        demo_payload: Dict[str, Any] = {
            "is_playing": True,
            "progress_ms": 45000,
            "item": {
                "id": "demo-track-1",
                "name": "Bohemian Rhapsody (Demo)",
                "artists": [{"name": "Queen"}],
                "album": {
                    "images": [
                        {
                            # Aynı demo albüm görseli (Spotify CDN) – gerçek API çağrısı yok
                            "url": "https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a"
                        }
                    ]
                },
                "duration_ms": 355000,
            },
        }
        return jsonify(demo_payload), 200
    
    # --------------------------------------------------------------
    # GERÇEK MOD: Spotify playback servisine bağlan
    # --------------------------------------------------------------
    try:
        logger.debug("widget_data(): playback verisi isteniyor: username='%s', widget_token='%s'", username, widget_token)
        data = _get_widget_playback_data(username)
        if not data or 'error' in data:
            logger.warning(
                "widget_data(): Kullanıcı için çalma durumu alınamadı veya hata döndü: username='%s', error='%s'",
                username,
                (data or {}).get("error"),
            )
            return jsonify({
                "is_playing": False,
                "error": data.get('error', 'Çalma durumu alınamadı'),
                "details": "Spotify'da aktif bir çalma işlemi bulunamadı veya bağlantı hatası oluştu."
            }), 200
            
        logger.info(
            "widget_data(): veri başarıyla döndürüldü: username='%s', widget_token='%s', is_playing=%s, track_id=%s",
            username,
            widget_token,
            data.get("is_playing"),
            (data.get("item") or {}).get("id"),
        )
        return jsonify(data), 200
        
    except Exception as e:
        logger.error("widget_data(): beklenmeyen hata (widget_token='%s'): %s", widget_token, e, exc_info=True)
        return jsonify({
            "is_playing": False,
            "error": "Beklenmeyen bir hata oluştu",
            "details": str(e)
        }), 500

# =============================================================================
# 6.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_widget_routes(app: Flask) -> None:
    """Spotify widget blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_widget_bp, url_prefix='/spotify')
