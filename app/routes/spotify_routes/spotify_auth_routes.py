# =============================================================================
# Spotify Kimlik Doğrulama Rota Modülü (Spotify Auth Routes Module)
# =============================================================================
# Bu modül, uygulamanın Spotify ile OAuth 2.0 kimlik doğrulama akışını
# yöneten rotaları içerir. Kullanıcıların Spotify hesaplarını bağlaması,
# yetkilendirme sonrası geri çağrının işlenmesi ve hesap bağlantısının
# kaldırılması gibi işlemleri kapsar.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# 3.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      3.1. spotify_auth()      -> @spotify_auth_bp.route('/auth', methods=['GET'])
#      3.2. spotify_callback()  -> @spotify_auth_bp.route('/callback', methods=['GET'])
#      3.3. spotify_unlink()    -> @spotify_auth_bp.route('/unlink', methods=['GET'])
# 4.0  ROTA KAYDI (ROUTE REGISTRATION)
#      4.1. init_spotify_auth_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
import requests
from typing import Any, Optional, Dict
from flask import Blueprint, request, redirect, url_for, session, flash, Flask

# Servisler ve Depolar
from app.database.repositories.spotify_account_repository import SpotifyUserRepository
from app.services.spotify.auth_service import SpotifyAuthService
from app.services.auth_service import login_required, session_is_user_logged_in

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 BLUEPRINT VE SERVİS BAŞLATMA (BLUEPRINT & SERVICE INITIALIZATION)
# =============================================================================
spotify_auth_bp = Blueprint('spotify_auth_bp', __name__, template_folder='../templates')
spotify_auth_service = SpotifyAuthService()
spotify_repo = SpotifyUserRepository()

# =============================================================================
# 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================

@spotify_auth_bp.route('/auth', methods=['GET'])
@login_required
def spotify_auth() -> Any:
    """Kullanıcıyı Spotify'ın yetkilendirme URL'sine yönlendirerek kimlik doğrulama akışını başlatır."""
    username = session_is_user_logged_in()
    logger.info(f"Kullanıcı '{username}' için Spotify yetkilendirme akışı başlatılıyor.")
    
    try:
        credentials = spotify_repo.get_spotify_user_data(username)
        if not credentials or not credentials.get('client_id') or not credentials.get('client_secret'):
            logger.warning(f"Kullanıcı '{username}' için Spotify kimlik bilgileri eksik.")
            flash("Lütfen profil sayfanızdan Spotify Client ID ve Secret bilgilerinizi girin.", "error")
            return redirect(url_for('profile', tab='spotify'))

        auth_url = spotify_auth_service.get_authorization_url(username, credentials['client_id'])
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Spotify yetkilendirme URL'si alınırken hata (Kullanıcı: {username}): {e}", exc_info=True)
        flash(f"Spotify bağlantısı sırasında bir hata oluştu.", "error")
        return redirect(url_for('profile', tab='spotify'))

@spotify_auth_bp.route('/callback', methods=['GET'])
@login_required
def spotify_callback() -> Any:
    """Spotify tarafından yetkilendirme kodu ile çağrılır ve token'ları işler."""
    username = session_is_user_logged_in()
    logger.info(f"Kullanıcı '{username}' için Spotify geri çağrısı alındı.")

    if error := request.args.get('error'):
        logger.error(f"Spotify yetkilendirme hatası (Kullanıcı: {username}): {error}")
        flash(f"Spotify yetkilendirme hatası: {error}. Lütfen tekrar deneyin.", "error")
        return redirect(url_for('profile', tab='spotify'))

    if not (auth_code := request.args.get('code')):
        flash("Yetkilendirme kodu bulunamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for('profile', tab='spotify'))

    try:
        logger.info(f"[DEBUG] Starting Spotify callback for user: {username}")
        
        # Get user credentials from database
        credentials = spotify_repo.get_spotify_user_data(username)
        logger.info(f"[DEBUG] Retrieved user credentials: {bool(credentials)}")
        
        if not credentials or not credentials.get('client_id') or not credentials.get('client_secret'):
            logger.error("[DEBUG] Missing client_id or client_secret in credentials")
            flash("Spotify kimlik bilgileri bulunamadı. Lütfen profil sayfanızı kontrol edin.", "error")
            return redirect(url_for('profile', tab='spotify'))

        logger.info("[DEBUG] Exchanging authorization code for tokens...")
        token_info = spotify_auth_service.exchange_code_for_token(auth_code, credentials['client_id'], credentials['client_secret'])
        logger.info(f"[DEBUG] Token info received: {bool(token_info)}")
        
        if not token_info or 'access_token' not in token_info:
            logger.error("[DEBUG] Failed to get access token from token info")
            flash("Spotify erişim token'ı alınamadı. Lütfen tekrar deneyin.", "error")
            return redirect(url_for('profile', tab='spotify'))
            
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        
        logger.info(f"[DEBUG] Access token: {'Exists' if access_token else 'Missing'}")
        logger.info(f"[DEBUG] Refresh token: {'Exists' if refresh_token else 'Missing'}")
        
        logger.info("[DEBUG] Saving Spotify user info...")
        result = spotify_auth_service.save_spotify_user_info(username, access_token, refresh_token)
        logger.info(f"[DEBUG] Save user info result: {result}")
        
        if not result:
            logger.error("[DEBUG] Failed to save Spotify user info")
            flash("Spotify hesap bilgileri kaydedilemedi. Lütfen tekrar deneyin.", "error")
        else:
            logger.info(f"[DEBUG] Successfully saved Spotify info for user: {username}")
            # flash("Spotify hesabınız başarıyla bağlandı!", "success")
        return redirect(url_for('profile', tab='spotify'))
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Spotify callback ağ hatası (Kullanıcı: {username}): {req_err}", exc_info=True)
        flash(f"Spotify ile iletişim sırasında bir ağ hatası oluştu.", "error")
        return redirect(url_for('profile', tab='spotify'))
    except Exception as e:
        logger.error(f"Spotify callback işlenirken hata (Kullanıcı: {username}): {e}", exc_info=True)
        flash(f"Spotify bağlantısı sırasında beklenmedik bir hata oluştu.", "error")
        return redirect(url_for('profile', tab='spotify'))

@spotify_auth_bp.route('/unlink', methods=['GET'])
@login_required
def spotify_unlink() -> Any:
    """Kullanıcının Spotify hesap bağlantısını kaldırır."""
    username = session_is_user_logged_in()
    logger.info(f"Kullanıcı '{username}' Spotify hesap bağlantısını kaldırma talebi gönderdi.")
    
    try:
        success = spotify_auth_service.unlink_spotify_account(username)
        if success:
            logger.info(f"Kullanıcı '{username}' için Spotify hesap bağlantısı kaldırıldı.")
            flash("Spotify hesap bağlantınız başarıyla kaldırıldı.", "success")
        else:
            logger.warning(f"Kullanıcı '{username}' için Spotify bağlantısı kaldırılamadı (zaten bağlı olmayabilir).")
            flash("Spotify hesap bağlantısı kaldırılırken bir sorun oluştu.", "error")
        return redirect(url_for('profile', tab='spotify'))
    except Exception as e:
        logger.error(f"Spotify bağlantısı kesilirken hata (Kullanıcı: {username}): {e}", exc_info=True)
        flash(f"Spotify bağlantısı kesilirken bir hata oluştu.", "error")
        return redirect(url_for('profile', tab='spotify'))

# =============================================================================
# 4.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_auth_routes(app: Flask):
    """Spotify kimlik doğrulama blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_auth_bp, url_prefix='/spotify')
