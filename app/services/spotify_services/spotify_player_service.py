# =============================================================================
# Spotify Oynatıcı Servis Modülü (Spotify Player Service Module)
# =============================================================================
# Bu modül, Spotify oynatıcısı ile ilgili işlemleri (çalma, duraklatma,
# parça değiştirme, ses ayarı vb.) ve oynatma durumu hakkında bilgi almayı
# sağlayan bir servis sınıfı (SpotifyPlayerService) içerir.
# Temel API etkileşimleri için SpotifyApiService'i kullanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli alt servislerin (SpotifyApiService) içe aktarılması.
# 2.0  SPOTIFY OYNATICI SERVİS SINIFI (SPOTIFY PLAYER SERVICE CLASS)
#      2.1. SpotifyPlayerService
#           : Spotify oynatıcı işlemlerini yöneten ana servis sınıfı.
#           2.1.1.  __init__(api_service=None)
#                   : Başlatıcı metot. SpotifyApiService örneğini ayarlar.
#
#           2.2. OYNATICI KONTROL METOTLARI (PLAYBACK CONTROL METHODS)
#                2.2.1. Temel Kontroller (Basic Controls)
#                       2.2.1.1. play(username, context_uri=None, uris=None, device_id=None)
#                                : Çalmayı başlatır veya devam ettirir.
#                       2.2.1.2. pause(username, device_id=None)
#                                : Çalmayı duraklatır.
#                       2.2.1.3. next_track(username, device_id=None)
#                                : Sonraki parçaya geçer.
#                       2.2.1.4. previous_track(username, device_id=None)
#                                : Önceki parçaya geçer.
#                2.2.2. Gelişmiş Kontroller (Advanced Controls)
#                       2.2.2.1. seek_to_position(username, position_ms, device_id=None)
#                                : Parçada belirli bir pozisyona atlar.
#                       2.2.2.2. set_volume(username, volume_percent, device_id=None)
#                                : Çalma ses seviyesini ayarlar.
#                       2.2.2.3. set_repeat_mode(username, repeat_state, device_id=None)
#                                : Tekrar modunu ayarlar.
#                       2.2.2.4. set_shuffle(username, shuffle_state, device_id=None)
#                                : Karışık çalma modunu açar veya kapatır.
#
#           2.3. OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
#                2.3.1. Mevcut Parça Bilgisi (Current Track Information)
#                       2.3.1.1. get_currently_playing(username)
#                                : O anda çalmakta olan parça hakkında detaylı bilgi alır.
#                       2.3.1.2. get_playback_state(username)
#                                : Mevcut çalma durumu hakkında genel bilgi alır.
#                       2.3.1.3. get_available_devices(username)
#                                : Kullanıcının aktif Spotify cihazlarını listeler.
#                2.3.2. Çalma Geçmişi (Playback History)
#                       2.3.2.1. get_recently_played(username, limit=20)
#                                : Kullanıcının son dinlediği parçaları alır.
#
#           2.4. ÖNERİ METOTLARI (RECOMMENDATION METHODS)
#                2.4.1. get_recommendations(username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20)
#                       : Belirtilen tohumlara göre müzik önerileri alır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from typing import Optional, List, Dict, Any # Tip ipuçları için

# =============================================================================
# 2.0 SPOTIFY OYNATICI SERVİS SINIFI (SPOTIFY PLAYER SERVICE CLASS)
# =============================================================================
class SpotifyPlayerService:
    """
    Spotify oynatıcı kontrolleri ve oynatma bilgisi alma işlemlerini yönetir.
    Bu sınıf, `SpotifyApiService` üzerinden Spotify API'si ile etkileşim kurar.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__(api_service=None) : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        SpotifyPlayerService sınıfının başlatıcı metodu.

        Args:
            api_service (SpotifyApiService, optional): Kullanılacak Spotify API servisi.
                                                       Eğer sağlanmazsa, yeni bir örneği oluşturulur.
        """
        self.api_service: SpotifyApiService = api_service or SpotifyApiService()
        # print("SpotifyPlayerService örneği oluşturuldu.") # Geliştirme için log

    # =========================================================================
    # 2.2. OYNATICI KONTROL METOTLARI (PLAYBACK CONTROL METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.2.1. Temel Kontroller (Basic Controls)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.2.1.1. play(...) : Çalmayı başlatır veya devam ettirir.
    # -------------------------------------------------------------------------
    def play(self, username: str, context_uri: Optional[str] = None, uris: Optional[List[str]] = None, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalmayı başlatır/devam ettirir.
        `SpotifyApiService.play` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            context_uri (Optional[str], optional): Çalınacak context URI'si (albüm, çalma listesi).
            uris (Optional[List[str]], optional): Çalınacak parça URI'leri listesi.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: play çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.play(username, context_uri, uris, device_id)

    # -------------------------------------------------------------------------
    # 2.2.1.2. pause(...) : Çalmayı duraklatır.
    # -------------------------------------------------------------------------
    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalmayı duraklatır.
        `SpotifyApiService.pause` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: pause çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.pause(username, device_id)

    # -------------------------------------------------------------------------
    # 2.2.1.3. next_track(...) : Sonraki parçaya geçer.
    # -------------------------------------------------------------------------
    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında sonraki parçaya geçer.
        `SpotifyApiService.next_track` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: next_track çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.next_track(username, device_id)

    # -------------------------------------------------------------------------
    # 2.2.1.4. previous_track(...) : Önceki parçaya geçer.
    # -------------------------------------------------------------------------
    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında önceki parçaya geçer.
        `SpotifyApiService.previous_track` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: previous_track çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.previous_track(username, device_id)

    # -------------------------------------------------------------------------
    # 2.2.2. Gelişmiş Kontroller (Advanced Controls)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.2.2.1. seek_to_position(...) : Parçada belirli bir pozisyona atlar.
    # -------------------------------------------------------------------------
    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """
        O anda çalmakta olan parçada belirtilen milisaniye pozisyonuna atlar.
        `SpotifyApiService.seek_to_position` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            position_ms (int): Atlanacak pozisyon (milisaniye cinsinden).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: seek_to_position çağrıldı - Kullanıcı={username}, Pozisyon={position_ms}") # Geliştirme için log
        return self.api_service.seek_to_position(username, position_ms, device_id)

    # -------------------------------------------------------------------------
    # 2.2.2.2. set_volume(...) : Çalma ses seviyesini ayarlar.
    # -------------------------------------------------------------------------
    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalma ses seviyesini ayarlar.
        `SpotifyApiService.set_volume` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            volume_percent (int): Ses seviyesi (0-100 arası).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: set_volume çağrıldı - Kullanıcı={username}, Ses={volume_percent}") # Geliştirme için log
        return self.api_service.set_volume(username, volume_percent, device_id)

    # -------------------------------------------------------------------------
    # 2.2.2.3. set_repeat_mode(...) : Tekrar modunu ayarlar.
    # -------------------------------------------------------------------------
    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında tekrar modunu ayarlar.
        `SpotifyApiService.set_repeat_mode` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            repeat_state (str): Tekrar modu ('track', 'context', 'off').
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: set_repeat_mode çağrıldı - Kullanıcı={username}, Mod={repeat_state}") # Geliştirme için log
        return self.api_service.set_repeat_mode(username, repeat_state, device_id)

    # -------------------------------------------------------------------------
    # 2.2.2.4. set_shuffle(...) : Karışık çalma modunu ayarlar.
    # -------------------------------------------------------------------------
    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında karışık çalma modunu açar veya kapatır.
        `SpotifyApiService.set_shuffle` metodunu çağırır.

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            shuffle_state (bool): Karışık çalma durumu (True: açık, False: kapalı).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"PlayerService: set_shuffle çağrıldı - Kullanıcı={username}, Durum={shuffle_state}") # Geliştirme için log
        return self.api_service.set_shuffle(username, shuffle_state, device_id)

    # =========================================================================
    # 2.3. OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.3.1. Mevcut Parça Bilgisi (Current Track Information)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.3.1.1. get_currently_playing(...) : O anda çalan parçayı alır.
    # -------------------------------------------------------------------------
    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının o anda çalmakta olduğu parça hakkında detaylı bilgi alır.
        `SpotifyApiService.get_currently_playing` metodunu çağırır.

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.

        Returns:
            Optional[Dict[str, Any]]: O anda çalan parça verileri veya None/hata sözlüğü.
        """
        # print(f"PlayerService: get_currently_playing çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.get_currently_playing(username)

    # -------------------------------------------------------------------------
    # 2.3.1.2. get_playback_state(...) : Mevcut çalma durumunu alır.
    # -------------------------------------------------------------------------
    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının mevcut çalma durumu hakkında genel bilgi alır.
        `SpotifyApiService.get_playback_state` metodunu çağırır.

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.

        Returns:
            Optional[Dict[str, Any]]: Çalma durumu verileri veya None/hata sözlüğü.
        """
        # print(f"PlayerService: get_playback_state çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.get_playback_state(username)

    # -------------------------------------------------------------------------
    # 2.3.1.3. get_available_devices(...) : Aktif cihazları listeler.
    # -------------------------------------------------------------------------
    def get_available_devices(self, username: str) -> List[Dict[str, Any]]:
        """
        Kullanıcının aktif Spotify cihazlarını listeler.
        `SpotifyApiService.get_available_devices` metodunu çağırır.

        Args:
            username (str): Cihazları listelenecek Beatify kullanıcısı.

        Returns:
            List[Dict[str, Any]]: Aktif cihazların listesi. Hata durumunda veya cihaz yoksa boş liste.
        """
        # print(f"PlayerService: get_available_devices çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.get_available_devices(username)

    # -------------------------------------------------------------------------
    # 2.3.2. Çalma Geçmişi (Playback History)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.3.2.1. get_recently_played(...) : Son dinlenenleri alır.
    # -------------------------------------------------------------------------
    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının son dinlediği parçaları alır.
        `SpotifyApiService.get_recently_played` metodunu çağırır.

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.
            limit (int, optional): Döndürülecek maksimum parça sayısı. Varsayılan 20.

        Returns:
            Optional[Dict[str, Any]]: Son dinlenen parçaları içeren sözlük veya None/hata sözlüğü.
        """
        # print(f"PlayerService: get_recently_played çağrıldı - Kullanıcı={username}, Limit={limit}") # Geliştirme için log
        return self.api_service.get_recently_played(username, limit)

    # =========================================================================
    # 2.4. ÖNERİ METOTLARI (RECOMMENDATION METHODS)
    # =========================================================================
    # Orijinal dosyada bu metot PlayerService içindeydi, mantıksal olarak burada da kalabilir
    # veya ayrı bir RecommendationService'e taşınabilir. Şimdilik burada bırakıyorum.

    # -------------------------------------------------------------------------
    # 2.4.1. get_recommendations(...) : Müzik önerileri alır.
    # -------------------------------------------------------------------------
    def get_recommendations(self, username: str, seed_artists: Optional[List[str]] = None,
                            seed_tracks: Optional[List[str]] = None, seed_genres: Optional[List[str]] = None,
                            limit: int = 20, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Belirtilen tohum (seed) sanatçılar, parçalar ve/veya türlere göre
        Spotify'dan müzik önerileri alır.
        `SpotifyApiService.get_recommendations` metodunu çağırır.

        Args:
            username (str): Öneri alınacak Beatify kullanıcısı.
            seed_artists (Optional[List[str]], optional): Tohum sanatçı ID'leri listesi.
            seed_tracks (Optional[List[str]], optional): Tohum parça ID'leri listesi.
            seed_genres (Optional[List[str]], optional): Tohum tür adları listesi.
            limit (int, optional): Döndürülecek maksimum öneri sayısı. Varsayılan 20.
            **kwargs: Diğer ayarlanabilir parametreler (Spotify API dokümanlarına bakınız).

        Returns:
            Optional[Dict[str, Any]]: Önerilen parçaları içeren sözlük veya None/hata sözlüğü.
        """
        # print(f"PlayerService: get_recommendations çağrıldı - Kullanıcı={username}") # Geliştirme için log
        return self.api_service.get_recommendations(username, seed_artists, seed_tracks, seed_genres, limit, **kwargs)

# =============================================================================
# Spotify Oynatıcı Servis Modülü Sonu
# =============================================================================
