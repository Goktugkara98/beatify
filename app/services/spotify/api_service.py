# =============================================================================
# Spotify API Servis Modülü (api_service.py)
# =============================================================================
# Bu modül, Spotify Web API'si ile etkileşim kurmak için `SpotifyApiService`
# sınıfını içerir. Kullanıcı profili, çalma listeleri, oynatıcı kontrolü,
# çalma durumu ve öneriler gibi çeşitli endpoint'lere istek yapma ve yanıtları
# işleme mantığını kapsar. Kimlik doğrulama (access token yönetimi) için
# `SpotifyAuthService` kullanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SINIFLAR (CLASSES)
#      2.1. SpotifyApiService
#           2.1.1. __init__(auth_service=None)
#           2.1.2. handle_spotify_response(response)
#           2.1.3. _make_api_request(username, endpoint, method=\"GET\", data=None)
#           2.1.4. get_user_profile(username)
#           2.1.5. get_user_playlists(username, limit=20, offset=0)
#           2.1.6. get_user_top_items(username, item_type, time_range=\"medium_term\", limit=20)
#           2.1.7. get_playback_state(username)
#           2.1.8. get_currently_playing(username)
#           2.1.9. get_recently_played(username, limit=20)
#           2.1.10. get_available_devices(username)
#           2.1.11. play(username, context_uri=None, uris=None, device_id=None)
#           2.1.12. pause(username, device_id=None)
#           2.1.13. next_track(username, device_id=None)
#           2.1.14. previous_track(username, device_id=None)
#           2.1.15. seek_to_position(username, position_ms, device_id=None)
#           2.1.16. set_volume(username, volume_percent, device_id=None)
#           2.1.17. set_repeat_mode(username, repeat_state, device_id=None)
#           2.1.18. set_shuffle(username, shuffle_state, device_id=None)
#           2.1.19. get_recommendations(username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20, **kwargs)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================

# Standart kütüphane
from typing import Any, Dict, List, Optional

# Üçüncü parti
import requests

# Uygulama içi
from app.config.spotify_config import SpotifyConfig
from app.services.spotify.auth_service import SpotifyAuthService


class SpotifyApiService:
    """
    Spotify Web API'si ile etkileşim kurmak için metotlar sağlayan servis sınıfı.
    Kimlik doğrulama, istek yapma, yanıt işleme ve çeşitli API endpoint'lerine
    özgü işlevleri içerir.
    """

    def __init__(self, auth_service: Optional[SpotifyAuthService] = None):
        """
        Başlatıcı metot. Gerekli servisleri ve yapılandırmaları ayarlar.
        """
        self.auth_service: SpotifyAuthService = auth_service or SpotifyAuthService()
        self.base_url: str = SpotifyConfig.API_BASE_URL
        self.profile_url: str = SpotifyConfig.PROFILE_URL

    # -------------------------------------------------------------------------
    # İç yardımcılar
    # -------------------------------------------------------------------------
    def handle_spotify_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Bir Spotify API isteğinden dönen `requests.Response` nesnesini işler.
        """
        status_code: int = response.status_code
        try:
            data: Dict[str, Any] = response.json() if response.text else {}
        except requests.exceptions.JSONDecodeError:
            data = {"error": {"message": "Yanıt JSON formatında değil veya boş."}}

        status_map: Dict[int, Dict[str, str]] = {
            200: {"action": "success", "message": "İstek başarılı."},
            201: {"action": "success", "message": "Kaynak başarıyla oluşturuldu."},
            202: {"action": "success", "message": "İstek kabul edildi, işleniyor."},
            204: {"action": "success", "message": "İstek başarılı, içerik yok."},
            304: {"action": "not_modified", "message": "Kaynak değiştirilmedi."},
            400: {"action": "client_error", "message": "Geçersiz istek."},
            401: {"action": "refresh_access_token", "message": "Yetkisiz erişim. Token süresi dolmuş veya geçersiz."},
            403: {"action": "forbidden_error", "message": "Erişim reddedildi. Gerekli izinler yok."},
            404: {"action": "not_found_error", "message": "Kaynak bulunamadı."},
            429: {"action": "rate_limit_error", "message": "Çok fazla istek yapıldı. Bir süre bekleyin."},
            500: {"action": "server_error", "message": "Spotify sunucusunda dahili bir hata oluştu."},
            502: {"action": "server_error", "message": "Geçersiz ağ geçidi. Spotify altyapı sorunu."},
            503: {"action": "server_error", "message": "Servis kullanılamıyor. Spotify geçici olarak devre dışı."}
        }

        response_details: Dict[str, Any] = status_map.get(
            status_code,
            {"action": "unknown_status", "message": f"Bilinmeyen durum kodu: {status_code}"}
        )

        if "error" in data and isinstance(data["error"], dict):
            response_details["message"] = data["error"].get("message", response_details["message"])
        elif "message" in data and status_code >= 400:
            response_details["message"] = data["message"]

        response_details["status_code"] = status_code
        return response_details

    def _make_api_request(
        self,
        username: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Belirtilen Spotify API endpoint'ine bir HTTP isteği yapar.
        """
        try:
            access_token: Optional[str] = self.auth_service.get_valid_access_token(username)
            if not access_token:
                return {"error": "Geçerli erişim tokenı bulunamadı.", "status_code": 401}

            url: str = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"
            headers: Dict[str, str] = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response: Optional[requests.Response] = None
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, headers=headers, timeout=10)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, headers=headers, timeout=10)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=10)
                else:
                    return {"error": f"Desteklenmeyen HTTP metodu: {method}", "status_code": 405}
            except requests.exceptions.RequestException as req_err:
                return {"error": f"Spotify API'sine bağlanırken ağ hatası: {str(req_err)}", "status_code": 503}

            if response is None:
                return {"error": "API isteği yapılamadı (yanıt alınamadı).", "status_code": 500}

            response_info: Dict[str, Any] = self.handle_spotify_response(response)

            if response_info["action"] == "success":
                return (
                    response.json()
                    if response.status_code != 204 and response.text
                    else {"status": "success", "message": response_info["message"], "status_code": response.status_code}
                )
            elif response_info["action"] == "refresh_access_token":
                new_token: Optional[str] = self.auth_service.refresh_access_token(username)
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    retry_response: Optional[requests.Response] = None
                    try:
                        if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                            retry_response = requests.request(method, url, headers=headers, json=data, timeout=10)
                    except requests.exceptions.RequestException as retry_err:
                        return {"error": f"Token yenileme sonrası ağ hatası: {str(retry_err)}", "status_code": 503}

                    if retry_response is not None:
                        retry_info: Dict[str, Any] = self.handle_spotify_response(retry_response)
                        if retry_info["action"] == "success":
                            return (
                                retry_response.json()
                                if retry_response.status_code != 204 and retry_response.text
                                else {
                                    "status": "success",
                                    "message": retry_info["message"],
                                    "status_code": retry_response.status_code,
                                }
                            )

                return {
                    "error": response_info["message"],
                    "status_code": response_info["status_code"],
                    "details": "Token yenileme başarısız veya ikinci deneme de yetkisiz.",
                }
            else:
                return {
                    "error": response_info["message"],
                    "status_code": response_info["status_code"],
                    "action": response_info["action"],
                }

        except Exception as e:
            return {"error": f"API isteği sırasında beklenmedik bir hata oluştu: {str(e)}", "status_code": 500}

    # -------------------------------------------------------------------------
    # Profil ve kullanıcı verileri
    # -------------------------------------------------------------------------
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Belirtilen kullanıcının Spotify profilini alır. (Endpoint: /v1/me)"""
        return self._make_api_request(username, "me")

    def get_user_playlists(self, username: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Kullanıcının Spotify çalma listelerini alır. (Endpoint: /v1/me/playlists)"""
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        return self._make_api_request(username, f"me/playlists?limit={limit}&offset={offset}")

    def get_user_top_items(
        self,
        username: str,
        item_type: str,
        time_range: str = "medium_term",
        limit: int = 20,
    ) -> Optional[Dict[str, Any]]:
        """Kullanıcının en çok dinlediği sanatçıları veya parçaları alır. (Endpoint: /v1/me/top/{type})"""
        if item_type not in ["artists", "tracks"]:
            return {"error": "Geçersiz öğe türü. 'artists' veya 'tracks' olmalı.", "status_code": 400}
        if time_range not in ["short_term", "medium_term", "long_term"]:
            time_range = "medium_term"
        limit = max(1, min(limit, 50))
        endpoint: str = f"me/top/{item_type}?time_range={time_range}&limit={limit}"
        return self._make_api_request(username, endpoint)

    # -------------------------------------------------------------------------
    # Oynatma bilgisi
    # -------------------------------------------------------------------------
    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """Mevcut çalma durumu hakkında bilgi alır. (Endpoint: GET /v1/me/player)"""
        return self._make_api_request(username=username, endpoint="me/player")

    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """O anda çalan parça hakkında detaylı bilgi alır. (Endpoint: GET /v1/me/player/currently-playing)"""
        return self._make_api_request(username=username, endpoint="me/player/currently-playing")

    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Son dinlenen parçaları alır. (Endpoint: GET /v1/me/player/recently-played)"""
        limit = max(1, min(limit, 50))
        return self._make_api_request(username=username, endpoint=f"me/player/recently-played?limit={limit}")

    def get_available_devices(self, username: str) -> List[Dict[str, Any]]:
        """Aktif ve kontrol edilebilir cihazları listeler. (Endpoint: GET /v1/me/player/devices)"""
        response_data = self._make_api_request(username=username, endpoint="me/player/devices")
        if response_data and isinstance(response_data.get("devices"), list) and not response_data.get("error"):
            return response_data["devices"]
        return []

    # -------------------------------------------------------------------------
    # Oynatıcı kontrol
    # -------------------------------------------------------------------------
    def play(
        self,
        username: str,
        context_uri: Optional[str] = None,
        uris: Optional[List[str]] = None,
        device_id: Optional[str] = None,
    ) -> bool:
        """Çalmayı başlatır/devam ettirir. (Endpoint: PUT /v1/me/player/play)"""
        payload: Dict[str, Any] = {}
        if context_uri:
            payload["context_uri"] = context_uri
        if uris:
            payload["uris"] = uris
            if "context_uri" in payload:
                del payload["context_uri"]

        endpoint: str = "me/player/play"
        if device_id:
            endpoint += f"?device_id={device_id}"

        response = self._make_api_request(
            username=username,
            endpoint=endpoint,
            method="PUT",
            data=payload if payload else None,
        )
        return response is not None and response.get("status") == "success"

    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """Çalmayı duraklatır. (Endpoint: PUT /v1/me/player/pause)"""
        endpoint: str = "me/player/pause"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """Sonraki parçaya geçer. (Endpoint: POST /v1/me/player/next)"""
        endpoint: str = "me/player/next"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """Önceki parçaya geçer. (Endpoint: POST /v1/me/player/previous)"""
        endpoint: str = "me/player/previous"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """Parçada belirli bir pozisyona atlar. (Endpoint: PUT /v1/me/player/seek)"""
        if not isinstance(position_ms, int) or position_ms < 0:
            return False
        endpoint: str = f"me/player/seek?position_ms={position_ms}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """Çalma ses seviyesini ayarlar. (Endpoint: PUT /v1/me/player/volume)"""
        if not isinstance(volume_percent, int) or not (0 <= volume_percent <= 100):
            return False
        endpoint: str = f"me/player/volume?volume_percent={volume_percent}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """Tekrar modunu ayarlar. (Endpoint: PUT /v1/me/player/repeat)"""
        if repeat_state not in ["track", "context", "off"]:
            return False
        endpoint: str = f"me/player/repeat?state={repeat_state}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """Karışık çalma modunu ayarlar. (Endpoint: PUT /v1/me/player/shuffle)"""
        if not isinstance(shuffle_state, bool):
            return False
        state_str: str = "true" if shuffle_state else "false"
        endpoint: str = f"me/player/shuffle?state={state_str}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # Müzik keşfi & öneriler
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
        """Belirtilen tohumlara göre müzik önerileri alır. (Endpoint: GET /v1/recommendations)"""
        seed_artists = seed_artists or []
        seed_tracks = seed_tracks or []
        seed_genres = seed_genres or []
        limit = max(1, min(limit, 100))

        total_seeds = len(seed_artists) + len(seed_tracks) + len(seed_genres)
        if total_seeds == 0:
            return {"error": "Öneri için en az bir tohum (seed) öğesi gereklidir.", "status_code": 400}
        if total_seeds > 5:
            temp_seeds = (seed_tracks + seed_artists + seed_genres)[:5]
            seed_tracks = [s for s in temp_seeds if s in seed_tracks]
            seed_artists = [s for s in temp_seeds if s in seed_artists and s not in seed_tracks]
            seed_genres = [
                s for s in temp_seeds if s in seed_genres and s not in seed_tracks and s not in seed_artists
            ]

        params_list: List[str] = []
        if seed_artists:
            params_list.append(f"seed_artists={','.join(seed_artists)}")
        if seed_tracks:
            params_list.append(f"seed_tracks={','.join(seed_tracks)}")
        if seed_genres:
            params_list.append(f"seed_genres={','.join(seed_genres)}")
        params_list.append(f"limit={limit}")

        for key, value in kwargs.items():
            if value is not None:
                params_list.append(f"{key}={value}")

        endpoint: str = f"recommendations?{'&'.join(params_list)}"
        return self._make_api_request(username=username, endpoint=endpoint)


__all__ = ["SpotifyApiService"]
