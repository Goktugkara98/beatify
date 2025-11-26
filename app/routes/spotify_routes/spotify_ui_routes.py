# =============================================================================
# Spotify Kullanıcı Arayüzü Rota Modülü (Spotify UI Routes Module)
# =============================================================================
# Bu modül, Spotify entegrasyonuyla ilgili kullanıcı arayüzü sayfalarını
# sunan rotaları içerir. Örneğin, bir Spotify kontrol paneli (dashboard)
# sayfası burada yer alabilir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
# 2.0  BLUEPRINT BAŞLATMA (BLUEPRINT INITIALIZATION)
# 3.0  ROTA TANIMLARI (ROUTE DEFINITIONS)
#      3.1. spotify_dashboard() -> @spotify_ui_bp.route('/dashboard', methods=['GET'])
# 4.0  ROTA KAYDI (ROUTE REGISTRATION)
#      4.1. init_spotify_ui_routes(app)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging
from typing import Any
from flask import Blueprint, redirect, url_for, Flask

# Servisler
from app.services.auth_service import login_required

# Logger kurulumu
logger = logging.getLogger(__name__)

# =============================================================================
# 2.0 BLUEPRINT BAŞLATMA (BLUEPRINT INITIALIZATION)
# =============================================================================
spotify_ui_bp = Blueprint('spotify_ui_bp', __name__, template_folder='../templates')

# =============================================================================
# 3.0 ROTA TANIMLARI (ROUTE DEFINITIONS)
# =============================================================================

@spotify_ui_bp.route('/dashboard', methods=['GET'])
@login_required
def spotify_dashboard() -> Any:
    """
    Spotify ile ilgili bir dashboard sayfası için bir endpoint.
    Mevcut implementasyonda, bu rota doğrudan profil sayfasına yönlendirir.
    """
    logger.info("Spotify dashboard sayfasına erişildi, profile yönlendiriliyor.")
    # İleride bu rota, render_template ile bir HTML sayfası döndürebilir.
    return redirect(url_for('profile', tab='spotify'))

# =============================================================================
# 4.0 ROTA KAYDI (ROUTE REGISTRATION)
# =============================================================================
def init_spotify_ui_routes(app: Flask) -> None:
    """Spotify UI blueprint'ini Flask uygulamasına kaydeder."""
    app.register_blueprint(spotify_ui_bp, url_prefix='/spotify')
