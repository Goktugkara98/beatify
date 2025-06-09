# =============================================================================
# Genel Uygulama Yapılandırması
# =============================================================================
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
# 2.0 GENEL AYARLAR (GENERAL CONFIGURATION)
# 3.0 ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
# 4.0 VERİTABANI AYARLARI (DATABASE CONFIGURATION)
# 5.0 SSL AYARLARI (SSL CONFIGURATION)
# =============================================================================

# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import os
from datetime import timedelta

# 2.0 GENEL AYARLAR (GENERAL CONFIGURATION)
# =============================================================================
DEBUG: bool = True
SECRET_KEY: str = os.environ.get('SECRET_KEY', 'varsayilan-cok-gizli-bir-anahtar-buraya-yazin')

# 3.0 ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
# =============================================================================
COOKIE_SECURE: bool = True
COOKIE_HTTPONLY: bool = True
COOKIE_SAMESITE: str = 'Lax'
COOKIE_MAX_AGE: timedelta = timedelta(days=30)

# 4.0 VERİTABANI AYARLARI (DATABASE CONFIGURATION)
# =============================================================================
DB_CONFIG: dict[str, str | None] = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'beatify')
}

# 5.0 SSL AYARLARI (SSL CONFIGURATION)
# =============================================================================
class SSL_CONFIG:
    CERTFILE: str | None = os.environ.get('SSL_CERTFILE')
    KEYFILE: str | None = os.environ.get('SSL_KEYFILE')

