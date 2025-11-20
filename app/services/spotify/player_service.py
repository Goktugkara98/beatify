"""
Spotify Oynatıcı Servis Modülü (SpotifyPlayerService)

Spotify oynatıcısı ile ilgili işlemleri (çalma, duraklatma, parça değiştirme,
ses ayarı vb.) ve oynatma durumu hakkında bilgi almayı sağlayan bir servis
sınıfı içerir. Temel API etkileşimleri için SpotifyApiService'i kullanır.
"""

from app.services.spotify.api_service import SpotifyApiService
from typing import Optional, List, Dict, Any


class SpotifyPlayerService:
    """
    Spotify oynatıcı kontrolleri ve oynatma bilgisi alma işlemlerini yönetir.
    Bu sınıf, `SpotifyApiService` üzerinden Spotify API'si ile etkileşim kurar.
    """

    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        SpotifyPlayerService sınıfının başlatıcı metodu.
        """
        self.api_service: SpotifyApiService = api_service or SpotifyApiService()

    # -------------------------------------------------------------------------
    # OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
    # -------------------------------------------------------------------------
    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcının mevcut çalma durumu hakkında genel bilgi alır."""
        return self.api_service.get_playback_state(username)

    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcının o anda çalmakta olduğu parça hakkında detaylı bilgi alır."""
        return self.api_service.get_currently_playing(username)

    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Kullanıcının son dinlediği parçaları alır."""
        return self.api_service.get_recently_played(username, limit)

    def get_available_devices(self, username: str) -> List[Dict[str, Any]]:
        """Kullanıcının aktif Spotify cihazlarını listeler."""
        return self.api_service.get_available_devices(username)

    # -------------------------------------------------------------------------
    # OYNATICI KONTROL METOTLARI (PLAYER CONTROL METHODS)
    # -------------------------------------------------------------------------
    def play(
        self,
        username: str,
        context_uri: Optional[str] = None,
        uris: Optional[List[str]] = None,
        device_id: Optional[str] = None,
    ) -> bool:
        """Kullanıcının aktif cihazında çalmayı başlatır/devam ettirir."""
        return self.api_service.play(username, context_uri, uris, device_id)

    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında çalmayı duraklatır."""
        return self.api_service.pause(username, device_id)

    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında sonraki parçaya geçer."""
        return self.api_service.next_track(username, device_id)

    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında önceki parçaya geçer."""
        return self.api_service.previous_track(username, device_id)

    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """O anda çalmakta olan parçada belirtilen milisaniye pozisyonuna atlar."""
        return self.api_service.seek_to_position(username, position_ms, device_id)

    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında çalma ses seviyesini ayarlar."""
        return self.api_service.set_volume(username, volume_percent, device_id)

    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında tekrar modunu ayarlar."""
        return self.api_service.set_repeat_mode(username, repeat_state, device_id)

    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """Kullanıcının aktif cihazında karışık çalma modunu açar veya kapatır."""
        return self.api_service.set_shuffle(username, shuffle_state, device_id)

    # -------------------------------------------------------------------------
    # MÜZİK KEŞFİ METOTLARI (MUSIC DISCOVERY METHODS)
    # -------------------------------------------------------------------------
    def get_recommendations(
        self,
        username: str,
        seed_artists: Optional[List[str]] = None,
        seed_tracks: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Belirtilen tohumlara göre Spotify'dan müzik önerileri alır."""
        return self.api_service.get_recommendations(username, seed_artists, seed_tracks, seed_genres, limit, **kwargs)


__all__ = ["SpotifyPlayerService"]

