# =============================================================================
# Services Paket Tanımı (app.services)
# =============================================================================
# Bu paket, uygulamanın servis katmanını içerir. Servisler; route katmanının
# ihtiyacı olan iş kurallarını uygular, dış servislerle (Spotify) konuşur ve
# repository katmanını kullanarak veri okuma/yazma işlerini koordine eder.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  ALT PAKETLER (SUBPACKAGES)
#      1.1. auth          : Kimlik doğrulama servisleri (paket).
#      1.2. users         : Kullanıcı domain servisleri (paket).
#      1.3. spotify       : Spotify domain servisleri (paket).
#
# 2.0  MODÜLLER (MODULES)
#      2.1. auth_service  : Uygulama genel auth helper/fonksiyonları.
# =============================================================================

