# =============================================================================
# Routes Paket Tanımı (app.routes)
# =============================================================================
# Bu paket, uygulamanın tüm rota (route) modüllerini içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  DIŞA AKTARILAN MODÜLLER (EXPORTS)
#      1.1. main_routes
#      1.2. auth_routes
# =============================================================================

from . import auth_routes
from . import main_routes

__all__ = [
    "main_routes",
    "auth_routes",
]
