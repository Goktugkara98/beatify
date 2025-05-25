# =============================================================================
# General Application Configuration
# =============================================================================
# Contents:
# 1. Imports
# 2. General Configuration
# 3. Cookie Security Settings
# 4. Database Configuration
# 5. SSL Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import os
from datetime import timedelta

# -----------------------------------------------------------------------------
# 2. General Configuration
# -----------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key-here')

# -----------------------------------------------------------------------------
# 3. Cookie Security Settings
# -----------------------------------------------------------------------------
COOKIE_SECURE = True  # Should be True when running over SSL
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = 'Lax'
COOKIE_MAX_AGE = timedelta(days=30)

# -----------------------------------------------------------------------------
# 4. Database Configuration
# -----------------------------------------------------------------------------
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'test')
}

# -----------------------------------------------------------------------------
# 5. SSL Configuration
# -----------------------------------------------------------------------------
class SSL_CONFIG:
    CERTFILE = os.environ.get('SSL_CERTFILE', 'C:/Users/Goktu/Desktop/certs/server.crt')  # Path to certificate file
    KEYFILE = os.environ.get('SSL_KEYFILE', 'C:/Users/Goktu/Desktop/certs/server.key')  # Path to private key file
