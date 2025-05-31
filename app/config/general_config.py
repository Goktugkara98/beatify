# =============================================================================
# Genel Uygulama Yapılandırma Modülü (General Application Configuration Module)
# =============================================================================
# Bu modül, uygulamanın temel yapılandırma ayarlarını içerir.
# Veritabanı bağlantıları, güvenlik anahtarları, çerez ayarları ve
# SSL yapılandırması gibi genel parametreler burada tanımlanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Python modüllerinin içe aktarılması.
# 2.0 GENEL AYARLAR (GENERAL CONFIGURATION)
#     : Uygulamanın genel çalışma modları ve gizli anahtar gibi temel ayarlar.
# 3.0 ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
#     : HTTP çerezlerinin güvenliği ve davranışları ile ilgili ayarlar.
# 4.0 VERİTABANI AYARLARI (DATABASE CONFIGURATION)
#     : Uygulamanın kullanacağı veritabanı bağlantı bilgileri.
# 5.0 SSL AYARLARI (SSL CONFIGURATION)
#     : HTTPS için SSL sertifikası ve anahtar dosyası yolları.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import os
from datetime import timedelta

# =============================================================================
# 2.0 GENEL AYARLAR (GENERAL CONFIGURATION)
# =============================================================================
# DEBUG: Uygulamanın hata ayıklama modunda olup olmadığını belirtir.
#        Geliştirme ortamında True, canlı (production) ortamda False olmalıdır.
DEBUG: bool = True

# SECRET_KEY: Oturum yönetimi, parola sıfırlama tokenları gibi kriptografik
#             işlemler için kullanılan gizli bir anahtar. Güvenli ve tahmin
#             edilemez bir değer olmalıdır. Ortam değişkeninden alınması önerilir.
SECRET_KEY: str = os.environ.get('SECRET_KEY', 'varsayilan-cok-gizli-bir-anahtar-buraya-yazin')

# =============================================================================
# 3.0 ÇEREZ GÜVENLİK AYARLARI (COOKIE SECURITY SETTINGS)
# =============================================================================
# COOKIE_SECURE: True ise, çerezler sadece HTTPS üzerinden gönderilir.
#                Canlı ortamda SSL kullanılıyorsa True olmalıdır.
COOKIE_SECURE: bool = True

# COOKIE_HTTPONLY: True ise, çerezlere JavaScript tarafından erişilemez.
#                  XSS (Cross-Site Scripting) saldırılarına karşı koruma sağlar.
COOKIE_HTTPONLY: bool = True

# COOKIE_SAMESITE: Çerezlerin siteler arası isteklerde nasıl gönderileceğini kontrol eder.
#                  'Lax' (varsayılan) veya 'Strict' olarak ayarlanabilir.
#                  CSRF (Cross-Site Request Forgery) saldırılarına karşı koruma sağlar.
COOKIE_SAMESITE: str = 'Lax'

# COOKIE_MAX_AGE: Çerezin tarayıcıda ne kadar süreyle saklanacağını belirtir.
#                 timedelta objesi veya saniye cinsinden bir tam sayı olabilir.
COOKIE_MAX_AGE: timedelta = timedelta(days=30)

# =============================================================================
# 4.0 VERİTABANI AYARLARI (DATABASE CONFIGURATION)
# =============================================================================
# DB_CONFIG: Veritabanı bağlantısı için gerekli parametreleri içeren bir sözlük.
#            Bu bilgiler genellikle ortam değişkenlerinden okunur.
DB_CONFIG: dict[str, str | None] = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''), # Canlıda boş parola kullanılmamalıdır!
    'database': os.environ.get('DB_NAME', 'beatify')
}

# =============================================================================
# 5.0 SSL AYARLARI (SSL CONFIGURATION)
# =============================================================================
# SSL_CONFIG: SSL/TLS sertifikası ve özel anahtar dosyalarının yollarını tutan sınıf.
#             Uygulama doğrudan SSL sonlandırması yapıyorsa kullanılır.
#             Genellikle bir web sunucusu (Nginx, Apache) SSL'i yönetir.
class SSL_CONFIG:
    """
    SSL yapılandırma ayarlarını içeren sınıf.
    Eğer uygulama doğrudan SSL sonlandırması yapacaksa bu ayarlar kullanılır.
    """
    # CERTFILE: SSL sertifika dosyasının tam yolu.
    #           Ortam değişkeninden alınması önerilir.
    CERTFILE: str | None = os.environ.get('SSL_CERTFILE') # Örn: '/etc/ssl/certs/server.crt'

    # KEYFILE: SSL özel anahtar dosyasının tam yolu.
    #          Ortam değişkeninden alınması önerilir.
    KEYFILE: str | None = os.environ.get('SSL_KEYFILE')   # Örn: '/etc/ssl/private/server.key'

# =============================================================================
# Yapılandırma Dosyası Sonu
# =============================================================================
