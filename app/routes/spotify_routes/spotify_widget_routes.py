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
from typing import Dict, Any, Tuple, Optional
from flask import (Blueprint, render_template, request, jsonify, session, url_for, redirect, Flask, flash)

# Servisler ve Depolar
from app.services.auth_service import login_required, session_is_user_logged_in
from app.services.spotify_services.spotify_player_service import SpotifyPlayerService
from app.services.spotify_services.widget_token_service import WidgetTokenService
from app.database.spotify_widget_repository import SpotifyWidgetRepository

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
        playback_data = spotify_player_service.get_playback_state(username)
        if not playback_data:
            return {"is_playing": False, "error": "No active device or playback"}
        return playback_data
    except Exception as e:
        logger.error(f"Playback verisi alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
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
    logger.info(f"Kullanıcı '{username}' widget yöneticisine erişti.")
    widget_token = widget_token_service.get_or_create_widget_token(username)
    return render_template('spotify/widget-manager.html', title="Spotify Widget Yöneticisi", widget_token=widget_token)

@spotify_widget_bp.route('/widget/<string:widget_token>', methods=['GET'])
def spotify_widget(widget_token: str) -> Any:
    """Belirtilen widget_token ile ilişkili Spotify widget'ını render eder."""
    logger.info(f"Widget token '{widget_token}' için render talebi alındı.")
    try:
        config = widget_repo.get_widget_config_by_token(widget_token)
        if not config:
            logger.warning(f"Geçersiz widget token'ı: {widget_token}")
            return render_template("spotify/widgets/widget-error.html", error="Widget bulunamadı."), 404

        theme = config.get('themeName')
        print(theme)
        template_name = f"spotify/widgets/widget_{theme}/widget_{theme}.html"
        
        return render_template(template_name, config=config, widget_token=widget_token)
    except Exception as e:
        logger.error(f"Widget render edilirken hata (Token: {widget_token}): {e}", exc_info=True)
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
    is_valid, payload = widget_token_service.validate_widget_token(widget_token)
    if not is_valid or not (username := payload.get('beatify_username')):
        logger.warning(f"Geçersiz widget token ile veri talebi: {widget_token}")
        return jsonify({"error": "Geçersiz widget token"}), 401
    
    try:
        data = _get_widget_playback_data(username)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Widget verisi alınırken hata (Token: {widget_token}): {e}", exc_info=True)
        return jsonify({"error": "Widget verisi alınırken sunucu hatası oluştu."}), 500

# =============================================================================
# 5.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_widget_routes(app: Flask) -> None:
    """Spotify widget blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_widget_bp, url_prefix='/spotify')
