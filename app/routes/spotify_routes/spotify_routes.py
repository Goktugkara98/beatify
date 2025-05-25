# =============================================================================
# Spotify Routes Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Main Route Initialization Function
#    2.1. Widget Routes Initialization
#    2.2. Authentication Routes Initialization
#    2.3. UI Routes Initialization
#    2.4. API Routes Initialization
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from app.routes.spotify_routes.spotify_auth_routes import init_spotify_auth_routes
from app.routes.spotify_routes.spotify_ui_routes import init_spotify_ui_routes
from app.routes.spotify_routes.spotify_widget_routes import init_spotify_widget_routes
from app.routes.spotify_routes.spotify_api_routes import init_spotify_api_routes

# -----------------------------------------------------------------------------
# 2. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_spotify_routes(app):
    try:
        # ---------------------------------------------------------------------
        # 2.1. Widget Routes Initialization
        # ---------------------------------------------------------------------
        init_spotify_widget_routes(app)
        
        # ---------------------------------------------------------------------
        # 2.2. Authentication Routes Initialization
        # ---------------------------------------------------------------------
        init_spotify_auth_routes(app)
        
        # ---------------------------------------------------------------------
        # 2.3. UI Routes Initialization
        # ---------------------------------------------------------------------
        init_spotify_ui_routes(app)
        
        # ---------------------------------------------------------------------
        # 2.4. API Routes Initialization
        # ---------------------------------------------------------------------
        init_spotify_api_routes(app)

        
    except Exception as e:
        raise