# =============================================================================
# Spotify API Rota Modülü (Spotify API Routes Module)
# =============================================================================
# Bu modül, Spotify verilerine erişmek ve oynatıcıyı kontrol etmek için
# kullanılan tüm API endpoint'lerini içerir. Rotalar genellikle JSON
# formatında yanıt döndürür ve istemci tarafındaki (örn. JavaScript)
# uygulamalar tarafından kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# 3.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      3.1. Oynatıcı Kontrolü (Player Control)
#           3.1.1. api_spotify_player_control() -> @spotify_api_bp.route('/player-control', methods=['POST'])
#      3.2. Oynatıcı Durumu (Player Status)
#           3.2.1. api_spotify_player_status() -> @spotify_api_bp.route('/player-status', methods=['GET'])
#      3.3. Çalma Listeleri (Playlists)
#           3.3.1. api_spotify_playlists() -> @spotify_api_bp.route('/playlists', methods=['GET'])
#           3.3.2. api_spotify_playlist_details() -> @spotify_api_bp.route('/playlists/<string:playlist_id>', methods=['GET'])
# 4.0  ROTA KAYDI (ROUTE REGISTRATION)
#      4.1. init_spotify_api_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from typing import Dict, Any, Tuple, List, Optional
from flask import Blueprint, request, session, jsonify, Flask

# Servisler
from app.services.spotify_services.spotify_player_service import SpotifyPlayerService
from app.services.spotify_services.spotify_playlist_service import SpotifyPlaylistService

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# =============================================================================
spotify_api_bp = Blueprint(name='spotify_api_bp', import_name=__name__)
spotify_player_service = SpotifyPlayerService()
spotify_playlist_service = SpotifyPlaylistService()

# =============================================================================
# 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================

# -------------------------------------------------------------------------
# 3.1. Oynatıcı Kontrolü (Player Control)
# -------------------------------------------------------------------------

@spotify_api_bp.route('/player-control', methods=['POST'])
def api_spotify_player_control() -> Tuple[Dict[str, Any], int]:
    """Spotify oynatıcısını kontrol etmek için API endpoint'i (play, pause, next, previous)."""
    username: Optional[str] = session.get('username')
    if not username:
        logger.warning("Yetkisiz oynatıcı kontrol denemesi.")
        return jsonify({"error": "Yetkisiz erişim. Lütfen giriş yapın.", "success": False}), 401

    data: Dict[str, Any] = request.json or {}
    action: Optional[str] = data.get('action')
    context_uri: Optional[str] = data.get('context_uri')
    uri: Optional[str] = data.get('uri')
    logger.info(f"Kullanıcı '{username}' için oynatıcı eylemi: {action}")

    try:
        if action == 'play':
            spotify_player_service.play(username, context_uri=context_uri, uris=[uri] if uri else None)
        elif action == 'pause':
            spotify_player_service.pause(username)
        elif action == 'next':
            spotify_player_service.next_track(username)
        elif action == 'previous':
            spotify_player_service.previous_track(username)
        else:
            logger.warning(f"Geçersiz oynatıcı eylemi: {action}")
            return jsonify({"error": "Geçersiz eylem.", "success": False}), 400
        
        return jsonify({"message": f"Eylem '{action}' başarıyla gerçekleştirildi.", "success": True}), 200
    except Exception as e:
        logger.error(f"Oynatıcı kontrol hatası (Kullanıcı: {username}, Eylem: {action}): {e}", exc_info=True)
        return jsonify({"error": f"Spotify oynatıcı kontrolü sırasında bir hata oluştu.", "success": False}), 500

# -------------------------------------------------------------------------
# 3.2. Oynatıcı Durumu (Player Status)
# -------------------------------------------------------------------------

@spotify_api_bp.route('/player-status', methods=['GET'])
def api_spotify_player_status() -> Tuple[Dict[str, Any], int]:
    """Kullanıcının o an çaldığı parça hakkında bilgi alır."""
    username: Optional[str] = session.get('username')
    if not username:
        return jsonify({"is_playing": False, "message": "Kullanıcı oturumu bulunamadı."}), 200

    try:
        now_playing = spotify_player_service.get_playback_state(username)
        if now_playing and now_playing.get('is_playing'):
            track_data = spotify_player_service.format_playback_state(now_playing)
            return jsonify(track_data), 200
        else:
            return jsonify({"is_playing": False, "message": "Aktif bir çalma durumu yok."}), 200
    except Exception as e:
        logger.error(f"Oynatıcı durumu alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
        return jsonify({"is_playing": False, "error": f"Oynatıcı durumu alınırken bir hata oluştu."}), 500

# -------------------------------------------------------------------------
# 3.3. Çalma Listeleri (Playlists)
# -------------------------------------------------------------------------

@spotify_api_bp.route('/playlists', methods=['GET'])
def api_spotify_playlists() -> Tuple[Dict[str, Any], int]:
    """Kullanıcının Spotify çalma listelerini alır."""
    username: Optional[str] = session.get('username')
    if not username:
        logger.warning("Yetkisiz çalma listesi sorgulama denemesi.")
        return jsonify({"error": "Yetkisiz erişim.", "success": False}), 401

    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        playlists_data = spotify_playlist_service.get_user_playlists(username, limit, offset)

        if not playlists_data or not playlists_data.get('items'):
            return jsonify({"items": [], "total": 0, "message": "Çalma listesi bulunamadı."}), 200

        formatted_playlists = [
            spotify_playlist_service.format_playlist_for_display(p) for p in playlists_data.get('items', [])
        ]
        return jsonify({
            "items": formatted_playlists,
            "total": playlists_data.get('total', 0),
        }), 200
    except Exception as e:
        logger.error(f"Çalma listeleri alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
        return jsonify({"error": "Çalma listeleri alınırken bir hata oluştu.", "success": False}), 500

@spotify_api_bp.route('/playlists/<string:playlist_id>', methods=['GET'])
def api_spotify_playlist_details(playlist_id: str) -> Tuple[Dict[str, Any], int]:
    """Belirli bir çalma listesinin detaylarını alır."""
    username: Optional[str] = session.get('username')
    if not username:
        logger.warning(f"Yetkisiz çalma listesi detayı sorgulama: ID={playlist_id}")
        return jsonify({"error": "Yetkisiz erişim.", "success": False}), 401

    try:
        logger.info(f"Kullanıcı '{username}' çalma listesi detayını sorguluyor: ID={playlist_id}")
        playlist_info = spotify_playlist_service.get_playlist(username, playlist_id)
        if not playlist_info:
            return jsonify({"error": "Çalma listesi bulunamadı.", "success": False}), 404
        
        return jsonify(playlist_info), 200
    except Exception as e:
        logger.error(f"Çalma listesi detayı alınırken hata (Kullanıcı: {username}, ID: {playlist_id}): {e}", exc_info=True)
        return jsonify({"error": "Çalma listesi detayı alınırken bir hata oluştu.", "success": False}), 500

# =============================================================================
# 4.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_api_routes(app: Flask):
    """Spotify API blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_api_bp, url_prefix='/api/spotify')
