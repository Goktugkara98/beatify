# =============================================================================
# Genel Uygulama Yapılandırması
# =============================================================================
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 1.1  ENV YÜKLEME (dotenv)
#      1.1.1. _load_dotenv_if_available()
#
# 1.2  ENV OKUMA YARDIMCILARI (ENV HELPERS)
#      1.2.1. _get_env(name, allow_empty=False)
#      1.2.2. _get_env_int(name)
#      1.2.3. _get_env_bool(name)
#
# 2.0  GENEL AYARLAR (GENERAL CONFIGURATION)
#      2.1. DEBUG
#      2.2. SECRET_KEY
#
# 3.0  ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
#      3.1. COOKIE_SECURE
#      3.2. COOKIE_HTTPONLY
#      3.3. COOKIE_SAMESITE
#      3.4. COOKIE_MAX_AGE
#
# 4.0  VERİTABANI AYARLARI (DATABASE CONFIGURATION)
#      4.1. DB_CONFIG
#
# 5.0  SSL AYARLARI (SSL CONFIGURATION)
#      5.1. SSL_CONFIG
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
import os
from datetime import timedelta
from typing import Optional

# =============================================================================
# 1.1 ENV YÜKLEME (dotenv)
# =============================================================================

def _load_dotenv_if_available() -> None:
    """
    .env dosyasını ortam değişkenlerine yükler (python-dotenv kuruluysa).

    Not:
    - Bu fonksiyon burada tutulur ki, projede config değerleri import edilir edilmez
      .env yüklenmiş olsun (SpotifyConfig doğrudan import edildiğinde bile).
    """
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        # python-dotenv yoksa veya .env bulunamazsa sessizce geç
        pass


_load_dotenv_if_available()


# =============================================================================
# 1.2 ENV OKUMA YARDIMCILARI (ENV HELPERS)
# =============================================================================

def _get_env(name: str, *, allow_empty: bool = False) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(
            f"Eksik ortam değişkeni: {name}. Lütfen .env dosyanıza ekleyin (env.example'a bakın)."
        )
    if not allow_empty and value == "":
        raise RuntimeError(
            f"Boş ortam değişkeni: {name}. Lütfen .env dosyanızda değer verin (env.example'a bakın)."
        )
    return value


def _get_env_int(name: str) -> int:
    raw = _get_env(name, allow_empty=False)
    try:
        return int(raw)
    except ValueError as e:
        raise RuntimeError(f"Geçersiz int ortam değişkeni: {name}={raw!r}") from e


def _get_env_bool(name: str) -> bool:
    raw = _get_env(name, allow_empty=False).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise RuntimeError(f"Geçersiz bool ortam değişkeni: {name}={raw!r} (true/false bekleniyor)")

# =============================================================================
# 2.0 GENEL AYARLAR (GENERAL CONFIGURATION)
# =============================================================================
DEBUG: bool = _get_env_bool("FLASK_DEBUG")
SECRET_KEY: str = _get_env("SECRET_KEY", allow_empty=False)

# =============================================================================
# 3.0 ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
# =============================================================================
COOKIE_SECURE: bool = _get_env_bool("COOKIE_SECURE")
COOKIE_HTTPONLY: bool = _get_env_bool("COOKIE_HTTPONLY")
COOKIE_SAMESITE: str = _get_env("COOKIE_SAMESITE", allow_empty=False)
COOKIE_MAX_AGE: timedelta = timedelta(days=_get_env_int("COOKIE_MAX_AGE_DAYS"))

# =============================================================================
# 4.0 VERİTABANI AYARLARI (DATABASE CONFIGURATION)
# =============================================================================
DB_CONFIG: dict[str, object] = {
    "host": _get_env("DB_HOST", allow_empty=False),
    "user": _get_env("DB_USER", allow_empty=False),
    # Parola bazı yerel kurulumlarda boş olabilir; boşluğa izin veriyoruz.
    "password": _get_env("DB_PASSWORD", allow_empty=True),
    "database": _get_env("DB_NAME", allow_empty=False),
    "port": _get_env_int("DB_PORT"),
}

# =============================================================================
# 5.0 SSL AYARLARI (SSL CONFIGURATION)
# =============================================================================
class SSL_CONFIG:
    CERTFILE: Optional[str] = os.environ.get("SSL_CERTFILE") or None
    KEYFILE: Optional[str] = os.environ.get("SSL_KEYFILE") or None

