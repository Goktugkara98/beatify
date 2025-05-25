# =============================================================================
# Flask Application - Main Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Application Creation
#    2.1. Flask App Initialization
#    2.2. Database Connection
#    2.3. Security Settings
#    2.4. Jinja2 Filters
#    2.5. Route Registration
# 3. Application Execution
#    3.1. Development Server Configuration
#    3.2. SSL Configuration (Commented)
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import Flask
from app.models.database import DatabaseConnection
from app.routes import main_routes, auth_routes
import datetime
from app.routes.spotify_routes import spotify_routes
from app.config.general_config import DEBUG, SECRET_KEY
import os

# -----------------------------------------------------------------------------
# 2. Application Creation
# -----------------------------------------------------------------------------
def create_app():
    # 2.1. Flask App Initialization
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static',
                template_folder='templates')
    
    # 2.2. Database Connection
    database = DatabaseConnection()
    database.connect()
    database.create_all_tables()
    
    # 2.3. Security Settings
    app.secret_key = SECRET_KEY
    
    # 2.4. Jinja2 Filters
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(date_str, fmt=None):
        if fmt is None:
            fmt = '%H:%M:%S'
        if isinstance(date_str, str):
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            date = datetime.datetime.now()
        return date.strftime(fmt)
    
    # 2.5. Route Registration
    main_routes.init_main_routes(app)
    auth_routes.init_auth_routes(app)
    spotify_routes.init_spotify_routes(app)
    
    return app
    
# -----------------------------------------------------------------------------
# 3. Application Execution
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    
    # 3.1. Development Server Configuration
    # With DEBUG=True, Flask's built-in reloader will handle auto-reloading
    app.run(debug=DEBUG, 
            host="0.0.0.0", 
            port=5000,
            threaded=True)

    # 3.2. SSL Configuration (Commented)
    """
    try:
        # SSL Configuration
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            certfile=SSL_CONFIG.CERTFILE,
            keyfile=SSL_CONFIG.KEYFILE
        )
        
        # Run with SSL
        app.run(debug=DEBUG, 
                host="0.0.0.0", 
                port=5000,
                ssl_context=ssl_context)
    except Exception as e:
        # Fallback to HTTP (for development)
        print(f"SSL error: {e}")
        print("Falling back to HTTP...")
        app.run(debug=DEBUG, host="0.0.0.0", port=5000)
    """
