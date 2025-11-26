# =============================================================================
# Spotify Widget Rota Modülü (Spotify Widget Routes Module)
# =============================================================================
# Bu modül, gömülebilir Spotify widget'larının yönetimi, render edilmesi
# ve veri sağlaması için gerekli tüm rotaları içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# 3.0  YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
#      3.1. _get_widget_playback_data(username)
# 4.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      4.1. Arayüz Rotaları (UI Routes)
#           4.1.1. widget_manager() @spotify_widget_bp.route('/widget-manager', methods=['GET'])
#           4.1.2. spotify_widget() @spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
#      4.2. API Rotaları (API Routes)
#           4.2.1. get_widget_list() @spotify_widget_bp.route('/widget-list', methods=['GET'])
#           4.2.2. widget_data() @spotify_widget_bp.route('/api/widget-data/<string:widget_token>', methods=['GET'])
# 5.0  ROTA KAYDI (ROUTE REGISTRATION)
#      5.1. init_spotify_widget_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
import json
from typing import Dict, Any, Tuple, Optional
from flask import (Blueprint, render_template, request, jsonify, session, url_for, redirect, Flask, flash)

# Servisler ve Depolar
from app.services.auth_service import login_required, session_is_user_logged_in
from app.services.spotify.player_service import SpotifyPlayerService
from app.services.spotify.widget.token_service import WidgetTokenService
from app.database.repositories.widget_repository import SpotifyWidgetRepository

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# =============================================================================
spotify_widget_bp = Blueprint('spotify_widget_bp', __name__, template_folder='../templates')
widget_token_service = WidgetTokenService()
spotify_player_service = SpotifyPlayerService()
widget_repo = SpotifyWidgetRepository()

# =============================================================================
# 3.0 YARDIMCI FONKSİYONLAR (HELPER FUNCTIONS)
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
# 4.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================

# -------------------------------------------------------------------------
# 4.1. Arayüz Rotaları (UI Routes)
# -------------------------------------------------------------------------

@spotify_widget_bp.route('/widget-manager', methods=['GET'])
@login_required
def widget_manager() -> Any:
    """Kullanıcıların Spotify widget'larını yönetebileceği arayüzü sunar."""
    username = session_is_user_logged_in()
    logger.info("Kullanıcı widget yöneticisine erişti: username='%s'", username)
    widget_token = widget_token_service.get_or_create_widget_token(username)
    
    # Mevcut konfigürasyonu çek
    config = widget_repo.get_widget_config_by_token(widget_token)
    current_theme = 'modern'
    if config and isinstance(config, dict):
        current_theme = config.get('theme', {}).get('name', 'modern')

    logger.info("Widget yöneticisi için token hazır: username='%s', widget_token='%s', theme='%s'", username, widget_token, current_theme)
    return render_template('spotify/widget-manager.html', 
                         title="Spotify Widget Yöneticisi", 
                         widget_token=widget_token,
                         current_theme=current_theme)

@spotify_widget_bp.route('/widget/update-config', methods=['POST'])
@login_required
def update_widget_config() -> Any:
    """Widget konfigürasyonunu günceller (tema seçimi vb.)."""
    username = session_is_user_logged_in()
    try:
        data = request.get_json()
        widget_token = data.get('widget_token')
        theme = data.get('theme')
        
        if not widget_token or not theme:
            return jsonify({"error": "Eksik parametreler"}), 400
            
        # Token'ın kullanıcıya ait olup olmadığını kontrol et
        token_owner = widget_repo.get_username_by_widget_token(widget_token)
        if token_owner != username:
            return jsonify({"error": "Yetkisiz işlem"}), 403
            
        # Mevcut konfigürasyonu al
        current_config = widget_repo.get_widget_config_by_token(widget_token) or {}
        if not isinstance(current_config, dict):
            current_config = {}
        
        # Temayı güncelle
        if 'theme' not in current_config:
            current_config['theme'] = {}
        current_config['theme']['name'] = theme
        
        # Kayıt için veriyi hazırla
        # Mevcut widget kaydından diğer bilgileri alalım
        full_widget = widget_repo.get_data_by_widget_token(widget_token)
        
        widget_data = {
            "beatify_username": username,
            "widget_token": widget_token,
            "widget_name": full_widget.get('widget_name', "Spotify Widget") if full_widget else "Spotify Widget",
            "widget_type": full_widget.get('widget_type', "now_playing") if full_widget else "now_playing",
            "config_data": json.dumps(current_config),
            "spotify_user_id": full_widget.get('spotify_user_id') if full_widget else None
        }
        
        success = widget_repo.store_widget_config(widget_data)
        
        if success:
            return jsonify({"success": True, "message": "Widget güncellendi"}), 200
        else:
            return jsonify({"error": "Widget güncellenemedi"}), 500

    except Exception as e:
        logger.error(f"Widget config güncellenirken hata: {e}", exc_info=True)
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
    """Belirtilen widget_token ile ilişkili Spotify widget'ını render eder."""
    logger.info("Spotify widget render talebi alındı: widget_token='%s'", widget_token)
    try:
        config = widget_repo.get_widget_config_by_token(widget_token)
        if not config:
            logger.warning("Spotify widget config bulunamadı, geçersiz token: widget_token='%s'", widget_token)
            return render_template("spotify/widgets/widget-error.html", error="Widget bulunamadı."), 404

        theme = config.get('theme', {}).get('name', 'modern')
        template_name = f"spotify/widgets/widget_{theme}/widget_{theme}.html"
        logger.info(
            "Spotify widget config yüklendi: widget_token='%s', theme='%s', template='%s'",
            widget_token,
            theme,
            template_name,
        )

        return render_template(template_name, config=config, widget_token=widget_token)
    except Exception as e:
        logger.error("Widget render edilirken hata (Token: %s): %s", widget_token, e, exc_info=True)
        return render_template("spotify/widgets/widget-error.html", error="Widget yüklenirken bir hata oluştu."), 500

# -------------------------------------------------------------------------
# 4.2. API Rotaları (API Routes)
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
    """Widget için gerekli verileri (örn: şu an çalan parça) JSON formatında sağlar."""
    logger.debug("widget_data(): API isteği alındı: widget_token='%s'", widget_token)
    # Token'ı doğrula
    is_valid, payload = widget_token_service.validate_widget_token(widget_token)
    
    # Token geçerli değilse veya kullanıcı adı yoksa hata döndür
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
    
    try:
        # Kullanıcının çalma durumunu al
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
# 5.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_widget_routes(app: Flask) -> None:
    """Spotify widget blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_widget_bp, url_prefix='/spotify')
