# =============================================================================
# Spotify API Servis Modülü (Spotify API Service Module)
# =============================================================================
# Bu modül, Spotify Web API'si ile etkileşim kurmak için bir servis sınıfı
# (SpotifyApiService) içerir. Kullanıcı profili, çalma listeleri, oynatıcı
# kontrolü, çalma durumu ve öneriler gibi çeşitli API endpoint'lerine
# istek yapma ve yanıtları işleme mantığını kapsar. Kimlik doğrulama
# (access token yönetimi) işlemleri için SpotifyAuthService'i kullanır.
#
# =============================================================================
# İÇİNDEKİLER
# =============================================================================
# 1.0  İÇE AKTARMALAR (IMPORTS)
#
# 2.0  SPOTIFY API SERVİS SINIFI (SPOTIFY API SERVICE CLASS)
#      : Spotify Web API'si ile etkileşimleri yöneten ana servis sınıfı.
#
#      2.1  TEMEL / İÇ METOTLAR (CORE / INTERNAL METHODS)
#           : Sınıfın çalışması için temel olan iç mantığı içeren metotlar.
#           2.1.1. __init__(auth_service=None)
#                  : Başlatıcı metot. Gerekli servisleri ve yapılandırmaları ayarlar.
#           2.1.2. handle_spotify_response(response)
#                  : Spotify API yanıtlarını işler ve durum kodlarına göre eylemler belirler.
#           2.1.3. _make_api_request(username, endpoint, method='GET', data=None)
#                  : Spotify API'sine genel bir istek yapar ve token yenileme mantığını içerir.
#
#      2.2  PROFİL VE KULLANICI VERİLERİ (PROFILE & USER DATA)
#           : Kullanıcıya özgü verilere erişim sağlayan metotlar.
#           2.2.1. get_user_profile(username)
#                  : Mevcut kullanıcının Spotify profil bilgilerini alır.
#           2.2.2. get_user_playlists(username, limit=20, offset=0)
#                  : Kullanıcının Spotify çalma listelerini alır.
#           2.2.3. get_user_top_items(username, item_type, time_range="medium_term", limit=20)
#                  : Kullanıcının en çok dinlediği sanatçıları veya parçaları alır.
#
#      2.3  OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
#           : Mevcut çalma durumu ve geçmişi hakkında bilgi alan metotlar.
#           2.3.1. get_playback_state(username)
#                  : Mevcut çalma durumu hakkında genel bilgi alır (cihaz, ilerleme vb.).
#           2.3.2. get_currently_playing(username)
#                  : O anda çalmakta olan parça hakkında detaylı bilgi alır.
#           2.3.3. get_recently_played(username, limit=20)
#                  : Kullanıcının son dinlediği parçaları alır.
#           2.3.4. get_available_devices(username)
#                  : Kullanıcının aktif Spotify cihazlarını listeler.
#
#      2.4  OYNATICI KONTROL METOTLARI (PLAYER CONTROL METHODS)
#           : Spotify oynatıcısını aktif olarak kontrol eden metotlar.
#           2.4.1. play(username, context_uri=None, uris=None, device_id=None)
#                  : Çalmayı başlatır veya devam ettirir.
#           2.4.2. pause(username, device_id=None)
#                  : Çalmayı duraklatır.
#           2.4.3. next_track(username, device_id=None)
#                  : Sonraki parçaya geçer.
#           2.4.4. previous_track(username, device_id=None)
#                  : Önceki parçaya geçer.
#           2.4.5. seek_to_position(username, position_ms, device_id=None)
#                  : Parçada belirli bir pozisyona atlar.
#           2.4.6. set_volume(username, volume_percent, device_id=None)
#                  : Çalma ses seviyesini ayarlar.
#           2.4.7. set_repeat_mode(username, repeat_state, device_id=None)
#                  : Tekrar modunu ayarlar (parça, context, kapalı).
#           2.4.8. set_shuffle(username, shuffle_state, device_id=None)
#                  : Karışık çalma modunu açar veya kapatır.
#
#      2.5  MÜZİK KEŞFİ VE ÖNERİLER (MUSIC DISCOVERY & RECOMMENDATIONS)
#           : Yeni müzikler bulmaya yönelik metotlar.
#           2.5.1. get_recommendations(username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20, **kwargs)
#                  : Belirtilen tohumlara göre müzik önerileri alır.
#
#      2.6  YARDIMCI METOTLAR (HELPER METHODS)
#           : Genel amaçlı yardımcı fonksiyonlar.
#           2.6.1. _ensure_datetime_naive(dt)
#                  : Datetime nesnesini zaman dilimi bilgisi olmayan (naive) hale getirir.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import requests
from datetime import datetime
from app.config.spotify_config import SpotifyConfig
from app.services.spotify_services.spotify_auth_service import SpotifyAuthService
from flask import session
from typing import Optional, Dict, Any, List, Union

# =============================================================================
# 2.0 SPOTIFY API SERVİS SINIFI (SPOTIFY API SERVICE CLASS)
# =============================================================================
class SpotifyApiService:
    """
    Spotify Web API'si ile etkileşim kurmak için metotlar sağlayan servis sınıfı.
    Kimlik doğrulama, istek yapma, yanıt işleme ve çeşitli API endpoint'lerine
    özgü işlevleri içerir.
    """

    # =========================================================================
    # 2.1 TEMEL / İÇ METOTLAR (CORE / INTERNAL METHODS)
    # =========================================================================

    def __init__(self, auth_service: Optional[SpotifyAuthService] = None):
        """
        2.1.1. SpotifyApiService sınıfının başlatıcı metodu.
        """
        self.auth_service: SpotifyAuthService = auth_service or SpotifyAuthService()
        self.base_url: str = SpotifyConfig.API_BASE_URL
        self.profile_url: str = SpotifyConfig.PROFILE_URL

    def handle_spotify_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        2.1.2. Bir Spotify API isteğinden dönen `requests.Response` nesnesini işler.
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

        response_details: Dict[str, Any] = status_map.get(status_code, {"action": "unknown_status", "message": f"Bilinmeyen durum kodu: {status_code}"})

        if "error" in data and isinstance(data["error"], dict):
            response_details["message"] = data["error"].get("message", response_details["message"])
        elif "message" in data and status_code >= 400:
            response_details["message"] = data["message"]

        response_details["status_code"] = status_code
        return response_details

    def _make_api_request(self, username: str, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        2.1.3. Belirtilen Spotify API endpoint'ine bir HTTP isteği yapar.
        """
        try:
            access_token: Optional[str] = self.auth_service.get_valid_access_token(username)
            if not access_token:
                return {"error": "Geçerli erişim tokenı bulunamadı.", "status_code": 401}

            url: str = endpoint if endpoint.startswith('http') else f"{self.base_url}/{endpoint.lstrip('/')}"
            headers: Dict[str, str] = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            response: Optional[requests.Response] = None
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, timeout=10)
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, headers=headers, timeout=10)
                elif method.upper() == 'PUT':
                    response = requests.put(url, json=data, headers=headers, timeout=10)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=10)
                else:
                    return {"error": f"Desteklenmeyen HTTP metodu: {method}", "status_code": 405}
            except requests.exceptions.RequestException as req_err:
                return {"error": f"Spotify API'sine bağlanırken ağ hatası: {str(req_err)}", "status_code": 503}

            if response is None:
                return {"error": "API isteği yapılamadı (yanıt alınamadı).", "status_code": 500}

            response_info: Dict[str, Any] = self.handle_spotify_response(response)

            if response_info["action"] == "success":
                return response.json() if response.status_code != 204 and response.text else {"status": "success", "message": response_info["message"], "status_code": response.status_code}
            elif response_info["action"] == "refresh_access_token":
                new_token: Optional[str] = self.auth_service.refresh_access_token(username)
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    retry_response: Optional[requests.Response] = None
                    try:
                        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                            retry_response = requests.request(method, url, headers=headers, json=data, timeout=10)
                    except requests.exceptions.RequestException as retry_err:
                        return {"error": f"Token yenileme sonrası ağ hatası: {str(retry_err)}", "status_code": 503}
                    
                    if retry_response is not None:
                        retry_info: Dict[str, Any] = self.handle_spotify_response(retry_response)
                        if retry_info["action"] == "success":
                             return retry_response.json() if retry_response.status_code != 204 and retry_response.text else {"status": "success", "message": retry_info["message"], "status_code": retry_response.status_code}
                
                return {"error": response_info["message"], "status_code": response_info["status_code"], "details": "Token yenileme başarısız veya ikinci deneme de yetkisiz."}
            else:
                return {"error": response_info["message"], "status_code": response_info["status_code"], "action": response_info["action"]}
            
        except Exception as e:
            return {"error": f"API isteği sırasında beklenmedik bir hata oluştu: {str(e)}", "status_code": 500}

    # =========================================================================
    # 2.2 PROFİL VE KULLANICI VERİLERİ (PROFILE & USER DATA)
    # =========================================================================
    
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        2.2.1. Belirtilen kullanıcının Spotify profilini alır. (Endpoint: /v1/me)
        """
        return self._make_api_request(username, "me")

    def get_user_playlists(self, username: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        2.2.2. Belirtilen kullanıcının Spotify çalma listelerini alır. (Endpoint: /v1/me/playlists)
        """
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        return self._make_api_request(username, f"me/playlists?limit={limit}&offset={offset}")

    def get_user_top_items(self, username: str, item_type: str, time_range: str = "medium_term", limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        2.2.3. Kullanıcının en çok dinlediği sanatçıları veya parçaları alır. (Endpoint: /v1/me/top/{type})
        """
        if item_type not in ['artists', 'tracks']:
            return {"error": "Geçersiz öğe türü. 'artists' veya 'tracks' olmalı.", "status_code": 400}
        if time_range not in ['short_term', 'medium_term', 'long_term']:
            time_range = 'medium_term'
        limit = max(1, min(limit, 50))
        endpoint: str = f"me/top/{item_type}?time_range={time_range}&limit={limit}"
        return self._make_api_request(username, endpoint)

    # =========================================================================
    # 2.3 OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
    # =========================================================================

    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """
        2.3.1. Mevcut çalma durumu hakkında bilgi alır. (Endpoint: GET /v1/me/player)
        """
        return self._make_api_request(username=username, endpoint="me/player")

    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """
        2.3.2. O anda çalan parça hakkında detaylı bilgi alır. (Endpoint: GET /v1/me/player/currently-playing)
        """
        return self._make_api_request(username=username, endpoint="me/player/currently-playing")

    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        2.3.3. Son dinlenen parçaları alır. (Endpoint: GET /v1/me/player/recently-played)
        """
        limit = max(1, min(limit, 50))
        return self._make_api_request(username=username, endpoint=f"me/player/recently-played?limit={limit}")

    def get_available_devices(self, username: str) -> List[Dict[str, Any]]:
        """
        2.3.4. Aktif ve kontrol edilebilir cihazları listeler. (Endpoint: GET /v1/me/player/devices)
        """
        response_data = self._make_api_request(username=username, endpoint="me/player/devices")
        if response_data and isinstance(response_data.get("devices"), list) and not response_data.get("error"):
            return response_data["devices"]
        return []

    # =========================================================================
    # 2.4 OYNATICI KONTROL METOTLARI (PLAYER CONTROL METHODS)
    # =========================================================================

    def play(self, username: str, context_uri: Optional[str] = None, uris: Optional[List[str]] = None, device_id: Optional[str] = None) -> bool:
        """
        2.4.1. Çalmayı başlatır/devam ettirir. (Endpoint: PUT /v1/me/player/play)
        """
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

        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT", data=payload if payload else None)
        return response is not None and response.get("status") == "success"

    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.4.2. Çalmayı duraklatır. (Endpoint: PUT /v1/me/player/pause)
        """
        endpoint: str = "me/player/pause"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.4.3. Sonraki parçaya geçer. (Endpoint: POST /v1/me/player/next)
        """
        endpoint: str = "me/player/next"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        2.4.4. Önceki parçaya geçer. (Endpoint: POST /v1/me/player/previous)
        """
        endpoint: str = "me/player/previous"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """
        2.4.5. Parçada belirli bir pozisyona atlar. (Endpoint: PUT /v1/me/player/seek)
        """
        if not isinstance(position_ms, int) or position_ms < 0:
            return False
        endpoint: str = f"me/player/seek?position_ms={position_ms}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """
        2.4.6. Çalma ses seviyesini ayarlar. (Endpoint: PUT /v1/me/player/volume)
        """
        if not isinstance(volume_percent, int) or not (0 <= volume_percent <= 100):
            return False
        endpoint: str = f"me/player/volume?volume_percent={volume_percent}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """
        2.4.7. Tekrar modunu ayarlar. (Endpoint: PUT /v1/me/player/repeat)
        """
        if repeat_state not in ['track', 'context', 'off']:
            return False
        endpoint: str = f"me/player/repeat?state={repeat_state}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """
        2.4.8. Karışık çalma modunu ayarlar. (Endpoint: PUT /v1/me/player/shuffle)
        """
        if not isinstance(shuffle_state, bool):
            return False
        state_str: str = 'true' if shuffle_state else 'false'
        endpoint: str = f"me/player/shuffle?state={state_str}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # =========================================================================
    # 2.5 MÜZİK KEŞFİ VE ÖNERİLER (MUSIC DISCOVERY & RECOMMENDATIONS)
    # =========================================================================

    def get_recommendations(self, username: str, seed_artists: Optional[List[str]] = None,
                            seed_tracks: Optional[List[str]] = None, seed_genres: Optional[List[str]] = None,
                            limit: int = 20, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        2.5.1. Belirtilen tohumlara göre müzik önerileri alır. (Endpoint: GET /v1/recommendations)
        """
        seed_artists = seed_artists or []
        seed_tracks = seed_tracks or []
        seed_genres = seed_genres or []
        limit = max(1, min(limit, 100))

        total_seeds = len(seed_artists) + len(seed_tracks) + len(seed_genres)
        if total_seeds == 0:
            return {"error": "Öneri için en az bir tohum (seed) öğesi gereklidir.", "status_code": 400}
        if total_seeds > 5:
            # Tohum sayısını 5 ile sınırla (basit bir kırpma stratejisi)
            temp_seeds = (seed_tracks + seed_artists + seed_genres)[:5]
            # Bu basit örnekte türleri ayırt etmiyoruz, gerçek bir senaryoda daha zeki bir mantık gerekebilir.
            # Şimdilik varsayımsal olarak parçalara öncelik veriyoruz.
            seed_tracks = [s for s in temp_seeds if s in seed_tracks]
            seed_artists = [s for s in temp_seeds if s in seed_artists and s not in seed_tracks]
            seed_genres = [s for s in temp_seeds if s in seed_genres and s not in seed_tracks and s not in seed_artists]


        params_list: List[str] = []
        if seed_artists: params_list.append(f"seed_artists={','.join(seed_artists)}")
        if seed_tracks: params_list.append(f"seed_tracks={','.join(seed_tracks)}")
        if seed_genres: params_list.append(f"seed_genres={','.join(seed_genres)}")
        params_list.append(f"limit={limit}")

        for key, value in kwargs.items():
            if value is not None:
                params_list.append(f"{key}={value}")
        
        endpoint: str = f"recommendations?{'&'.join(params_list)}"
        return self._make_api_request(username=username, endpoint=endpoint)

    # =========================================================================
    # 2.6 YARDIMCI METOTLAR (HELPER METHODS)
    # =========================================================================

    def _ensure_datetime_naive(self, dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """
        2.6.1. Datetime'ı veya ISO string'ini naive datetime nesnesine dönüştürür.
        """
        if dt is None:
            return None
        if isinstance(dt, str):
            try:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return None
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            return None

        if dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None:
            return dt_obj.replace(tzinfo=None)
        
        return dt_obj

# =============================================================================
# Spotify API Servis Modülü Sonu
# =============================================================================
