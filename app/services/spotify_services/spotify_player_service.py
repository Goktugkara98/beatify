# =============================================================================
# Spotify Oynatıcı Servis Modülü (SpotifyPlayerService)
# =============================================================================
# Bu modül, Spotify oynatıcısı ile ilgili işlemleri (çalma, duraklatma,
# parça değiştirme, ses ayarı vb.) ve oynatma durumu hakkında bilgi almayı
# sağlayan bir servis sınıfı içerir.
# Temel API etkileşimleri için SpotifyApiService'i kullanır.
#
# =============================================================================
# İÇİNDEKİLER
# =============================================================================
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SPOTIFY OYNATICI SERVİS SINIFI (SpotifyPlayerService)
#
#      2.1  TEMEL METOTLAR (CORE METHODS)
#           2.1.1. __init__(api_service=None)
#                  : Başlatıcı metot.
#
#      2.2  OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
#           2.2.1. get_playback_state(username)
#                  : Mevcut çalma durumu hakkında genel bilgi alır.
#           2.2.2. get_currently_playing(username)
#                  : O anda çalmakta olan parça hakkında detaylı bilgi alır.
#           2.2.3. get_recently_played(username, limit=20)
#                  : Kullanıcının son dinlediği parçaları alır.
#           2.2.4. get_available_devices(username)
#                  : Kullanıcının aktif Spotify cihazlarını listeler.
#
#      2.3  OYNATICI KONTROL METOTLARI (PLAYER CONTROL METHODS)
#           2.3.1. play(username, context_uri=None, uris=None, device_id=None)
#                  : Çalmayı başlatır veya devam ettirir.
#           2.3.2. pause(username, device_id=None)
#                  : Çalmayı duraklatır.
#           2.3.3. next_track(username, device_id=None)
#                  : Sonraki parçaya geçer.
#           2.3.4. previous_track(username, device_id=None)
#                  : Önceki parçaya geçer.
#           2.3.5. seek_to_position(username, position_ms, device_id=None)
#                  : Parçada belirli bir pozisyona atlar.
#           2.3.6. set_volume(username, volume_percent, device_id=None)
#                  : Çalma ses seviyesini ayarlar.
#           2.3.7. set_repeat_mode(username, repeat_state, device_id=None)
#                  : Tekrar modunu ayarlar.
#           2.3.8. set_shuffle(username, shuffle_state, device_id=None)
#                  : Karışık çalma modunu açar veya kapatır.
#
#      2.4  MÜZİK KEŞFİ METOTLARI (MUSIC DISCOVERY METHODS)
#           2.4.1. get_recommendations(username, seed_artists, seed_tracks, seed_genres, limit, **kwargs)
#                  : Belirtilen tohumlara göre müzik önerileri alır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from typing import Optional, List, Dict, Any

# =============================================================================
# 2.0 SPOTIFY OYNATICI SERVİS SINIFI (SpotifyPlayerService)
# =============================================================================
class SpotifyPlayerService:
    """
    Spotify oynatıcı kontrolleri ve oynatma bilgisi alma işlemlerini yönetir.
    Bu sınıf, `SpotifyApiService` üzerinden Spotify API'si ile etkileşim kurar.
    """

    # -------------------------------------------------------------------------
    # 2.1 TEMEL METOTLAR (CORE METHODS)
    # -------------------------------------------------------------------------
    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        2.1.1. SpotifyPlayerService sınıfının başlatıcı metodu.
        """
        self.api_service: SpotifyApiService = api_service or SpotifyApiService()

    # =========================================================================
    # 2.2 OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
    # =========================================================================
    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """
        2.2.1. Kullanıcının mevcut çalma durumu hakkında genel bilgi alır.
        """
        return self.api_service.get_playback_state(username)

    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """
        2.2.2. Kullanıcının o anda çalmakta olduğu parça hakkında detaylı bilgi alır.
        """
        return self.api_service.get_currently_playing(username)

    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        2.2.3. Kullanıcının son dinlediği parçaları alır.
        """
        return self.api_service.get_recently_played(username, limit)

    def get_available_devices(self, username: str) -> List[Dict[str, Any]]:
        """
        2.2.4. Kullanıcının aktif Spotify cihazlarını listeler.
        """
        return self.api_service.get_available_devices(username)

    # =========================================================================
    # 2.3 OYNATICI KONTROL METOTLARI (PLAYER CONTROL METHODS)
    # =========================================================================
    def play(self, username: str, context_uri: Optional[str] = None, uris: Optional[List[str]] = None, device_id: Optional[str] = None) -> bool:
        """
        2.3.1. Kullanıcının aktif cihazında çalmayı başlatır/devam ettirir.
        """
        return self.api_service.play(username, context_uri, uris, device_id)

    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.3.2. Kullanıcının aktif cihazında çalmayı duraklatır.
        """
        return self.api_service.pause(username, device_id)

    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.3.3. Kullanıcının aktif cihazında sonraki parçaya geçer.
        """
        return self.api_service.next_track(username, device_id)

    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.3.4. Kullanıcının aktif cihazında önceki parçaya geçer.
        """
        return self.api_service.previous_track(username, device_id)

    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """
        2.3.5. O anda çalmakta olan parçada belirtilen milisaniye pozisyonuna atlar.
        """
        return self.api_service.seek_to_position(username, position_ms, device_id)

    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """
        2.3.6. Kullanıcının aktif cihazında çalma ses seviyesini ayarlar.
        """
        return self.api_service.set_volume(username, volume_percent, device_id)

    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """
        2.3.7. Kullanıcının aktif cihazında tekrar modunu ayarlar.
        """
        return self.api_service.set_repeat_mode(username, repeat_state, device_id)

    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """
        2.3.8. Kullanıcının aktif cihazında karışık çalma modunu açar veya kapatır.
        """
        return self.api_service.set_shuffle(username, shuffle_state, device_id)

    # =========================================================================
    # 2.4 MÜZİK KEŞFİ METOTLARI (MUSIC DISCOVERY METHODS)
    # =========================================================================
    def get_recommendations(self, username: str, seed_artists: Optional[List[str]] = None,
                            seed_tracks: Optional[List[str]] = None, seed_genres: Optional[List[str]] = None,
                            limit: int = 20, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        2.4.1. Belirtilen tohumlara göre Spotify'dan müzik önerileri alır.
        """
        return self.api_service.get_recommendations(username, seed_artists, seed_tracks, seed_genres, limit, **kwargs)
