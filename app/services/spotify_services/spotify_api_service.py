# =============================================================================
# Spotify API Servis Modülü (Spotify API Service Module)
# =============================================================================
# Bu modül, Spotify Web API'si ile etkileşim kurmak için bir servis sınıfı
# (SpotifyApiService) içerir. Kullanıcı profili, çalma listeleri, oynatıcı
# kontrolü, çalma durumu ve öneriler gibi çeşitli API endpoint'lerine
# istek yapma ve yanıtları işleme mantığını kapsar. Kimlik doğrulama
# (access token yönetimi) işlemleri için SpotifyAuthService'i kullanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modülleri, yapılandırmalar ve diğer servislerin içe aktarılması.
# 2.0  SPOTIFY API SERVİS SINIFI (SPOTIFY API SERVICE CLASS)
#      2.1. SpotifyApiService
#           : Spotify Web API'si ile etkileşimleri yöneten ana servis sınıfı.
#           2.1.1.  __init__(auth_service=None)
#                   : Başlatıcı metot. SpotifyAuthService ve API temel URL'lerini ayarlar.
#           2.1.2.  handle_spotify_response(response)
#                   : Spotify API yanıtlarını işler ve durum kodlarına göre eylemler belirler.
#           2.1.3.  _make_api_request(username, endpoint, method='GET', data=None)
#                   : Spotify API'sine genel bir istek yapar (GET, POST, PUT, DELETE).
#                     Token yenileme mantığını da içerir.
#
#           2.2. PROFİL METOTLARI (PROFILE METHODS)
#                : Kullanıcı profili ve ilgili verilere erişim metotları.
#                2.2.1. get_user_profile(username)
#                       : Mevcut kullanıcının Spotify profil bilgilerini alır.
#                2.2.2. get_user_playlists(username, limit=50)
#                       : Kullanıcının Spotify çalma listelerini alır.
#                2.2.3. get_user_top_items(username, item_type, time_range="medium_term", limit=20)
#                       : Kullanıcının en çok dinlediği sanatçıları veya parçaları alır.
#
#           2.3. OYNATICI KONTROL METOTLARI (PLAYBACK CONTROL METHODS)
#                : Spotify oynatıcısını kontrol etme metotları.
#                2.3.1.  play(username, context_uri=None, uris=None, device_id=None)
#                        : Çalmayı başlatır veya devam ettirir. Belirli parça/albüm/çalma listesi çalabilir.
#                2.3.2.  pause(username, device_id=None)
#                        : Çalmayı duraklatır.
#                2.3.3.  next_track(username, device_id=None)
#                        : Sonraki parçaya geçer.
#                2.3.4.  previous_track(username, device_id=None)
#                        : Önceki parçaya geçer.
#                2.3.5.  seek_to_position(username, position_ms, device_id=None)
#                        : Parçada belirli bir pozisyona atlar.
#                2.3.6.  set_volume(username, volume_percent, device_id=None)
#                        : Çalma ses seviyesini ayarlar.
#                2.3.7.  set_repeat_mode(username, repeat_state, device_id=None)
#                        : Tekrar modunu ayarlar (parça, çalma listesi/albüm, kapalı).
#                2.3.8.  set_shuffle(username, shuffle_state, device_id=None)
#                        : Karışık çalma modunu açar veya kapatır.
#
#           2.4. OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
#                : Mevcut çalma durumu ve geçmişi hakkında bilgi alma metotları.
#                2.4.1.  get_currently_playing(username)
#                        : O anda çalmakta olan parça hakkında detaylı bilgi alır.
#                2.4.2.  get_playback_state(username)
#                        : Mevcut çalma durumu hakkında genel bilgi alır (cihaz, ilerleme vb.).
#                2.4.3.  get_recently_played(username, limit=20)
#                        : Kullanıcının son dinlediği parçaları alır.
#                2.4.4.  get_available_devices(username)
#                        : Kullanıcının aktif Spotify cihazlarını listeler.
#
#           2.5. ÖNERİ METOTLARI (RECOMMENDATIONS METHODS)
#                2.5.1.  get_recommendations(username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20)
#                        : Belirtilen tohum (seed) sanatçı, parça veya türlere göre müzik önerileri alır.
#
#           2.6. YARDIMCI METOTLAR (HELPER METHODS)
#                2.6.1.  _ensure_datetime_naive(dt)
#                        : Verilen datetime nesnesinin zaman dilimi bilgisini (timezone-aware) kaldırarak
#                          saf (naive) hale getirir veya ISO formatındaki string'i datetime'a çevirir.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import requests # HTTP istekleri yapmak için
from datetime import datetime # Zaman ve tarih işlemleri için
from app.config.spotify_config import SpotifyConfig # Spotify API yapılandırmaları
from app.services.spotify_services.spotify_auth_service import SpotifyAuthService # Kimlik doğrulama servisi
from flask import session # Session yönetimi için (orijinalde import edilmiş ama doğrudan kullanılmamış)
from typing import Optional, Dict, Any, List, Union # Tip ipuçları için

# =============================================================================
# 2.0 SPOTIFY API SERVİS SINIFI (SPOTIFY API SERVICE CLASS)
# =============================================================================
class SpotifyApiService:
    """
    Spotify Web API'si ile etkileşim kurmak için metotlar sağlayan servis sınıfı.
    Kimlik doğrulama, istek yapma, yanıt işleme ve çeşitli API endpoint'lerine
    özgü işlevleri içerir.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__(auth_service=None) : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self, auth_service: Optional[SpotifyAuthService] = None):
        """
        SpotifyApiService sınıfının başlatıcı metodu.

        Args:
            auth_service (SpotifyAuthService, optional): Kullanılacak kimlik doğrulama servisi.
                                                       Eğer sağlanmazsa, yeni bir örneği oluşturulur.
        """
        self.auth_service: SpotifyAuthService = auth_service or SpotifyAuthService()
        self.base_url: str = SpotifyConfig.API_BASE_URL
        self.profile_url: str = SpotifyConfig.PROFILE_URL # SpotifyConfig'den alınmalı
        # print(f"SpotifyApiService örneği oluşturuldu. Base URL: {self.base_url}") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 2.1.2. handle_spotify_response(response) : Spotify API yanıtlarını işler.
    # -------------------------------------------------------------------------
    def handle_spotify_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Bir Spotify API isteğinden dönen `requests.Response` nesnesini işler.
        Durum koduna göre bir eylem ve mesaj içeren bir sözlük döndürür.
        Hata mesajlarını API yanıtından almaya çalışır.

        Args:
            response (requests.Response): İşlenecek API yanıtı.

        Returns:
            Dict[str, Any]: Yanıtın durumunu ve mesajını içeren bir sözlük.
                            Örn: {"action": "success", "message": "OK"}
                                 {"action": "refresh_access_token", "message": "The access token expired"}
        """
        status_code: int = response.status_code
        try:
            data: Dict[str, Any] = response.json() if response.text else {}
        except requests.exceptions.JSONDecodeError:
            data = {"error": {"message": "Yanıt JSON formatında değil veya boş."}}
            # print(f"JSON decode hatası: {response.text}") # Geliştirme için log

        # print(f"Spotify yanıtı işleniyor: Durum Kodu={status_code}, Veri={data}") # Geliştirme için log

        # Bilinen durum kodları için eylem ve varsayılan mesajlar
        status_map: Dict[int, Dict[str, str]] = {
            200: {"action": "success", "message": "İstek başarılı."},
            201: {"action": "success", "message": "Kaynak başarıyla oluşturuldu."},
            202: {"action": "success", "message": "İstek kabul edildi, işleniyor."},
            204: {"action": "success", "message": "İstek başarılı, içerik yok."}, # Genellikle PUT, DELETE sonrası
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

        # API'den gelen hata mesajını kullan (varsa)
        if "error" in data and isinstance(data["error"], dict):
            response_details["message"] = data["error"].get("message", response_details["message"])
        elif "message" in data and status_code >= 400 : # Bazı hatalar direkt message alanında gelebilir
             response_details["message"] = data["message"]


        response_details["status_code"] = status_code # Durum kodunu da yanıta ekle
        # print(f"İşlenmiş yanıt detayı: {response_details}") # Geliştirme için log
        return response_details

    # -------------------------------------------------------------------------
    # 2.1.3. _make_api_request(...) : Spotify API'sine genel bir istek yapar.
    # -------------------------------------------------------------------------
    def _make_api_request(self, username: str, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Belirtilen Spotify API endpoint'ine bir HTTP isteği yapar.
        Kimlik doğrulama için geçerli bir erişim token'ı alır ve gerekirse yeniler.

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            endpoint (str): API endpoint yolu (örn: "me/player/currently-playing") veya tam URL.
            method (str, optional): HTTP metodu ('GET', 'POST', 'PUT', 'DELETE'). Varsayılan 'GET'.
            data (Optional[Dict[str, Any]], optional): POST veya PUT istekleri için gönderilecek JSON verisi.

        Returns:
            Optional[Dict[str, Any]]: Başarılı API yanıtından dönen JSON verisi.
                                      Hata durumunda veya içerik olmadığında None veya {"status": "success"} dönebilir.
        """
        # print(f"_make_api_request çağrıldı: Kullanıcı={username}, Endpoint={endpoint}, Metot={method}") # Geliştirme için log
        try:
            access_token: Optional[str] = self.auth_service.get_valid_access_token(username)
            if not access_token:
                # print(f"Geçerli erişim token'ı alınamadı: {username}") # Geliştirme için log
                # Belki burada bir istisna fırlatmak veya özel bir hata nesnesi döndürmek daha iyi olabilir.
                return {"error": "Geçerli erişim tokenı bulunamadı.", "status_code": 401}

            # Endpoint tam URL mi yoksa sadece yol mu kontrol et
            url: str = endpoint if endpoint.startswith('http') else f"{self.base_url}/{endpoint.lstrip('/')}"

            headers: Dict[str, str] = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # print(f"API isteği yapılıyor: URL={url}, Headers={headers.get('Authorization')[:20]}...") # Geliştirme için log
            response: Optional[requests.Response] = None
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, timeout=10) # Timeout eklendi
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, headers=headers, timeout=10)
                elif method.upper() == 'PUT':
                    response = requests.put(url, json=data, headers=headers, timeout=10)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=10)
                else:
                    # print(f"Geçersiz HTTP metodu: {method}") # Geliştirme için log
                    return {"error": f"Desteklenmeyen HTTP metodu: {method}", "status_code": 405}
            except requests.exceptions.RequestException as req_err:
                # print(f"API isteği sırasında ağ hatası ({url}): {str(req_err)}") # Geliştirme için log
                return {"error": f"Spotify API'sine bağlanırken ağ hatası: {str(req_err)}", "status_code": 503} # Servis kullanılamıyor gibi

            if response is None: # Yukarıdaki if/elif bloğuna girmezse (teorik olarak olmamalı)
                return {"error": "API isteği yapılamadı (yanıt alınamadı).", "status_code": 500}

            response_info: Dict[str, Any] = self.handle_spotify_response(response)
            # print(f"İlk API yanıtı işlendi: {response_info}") # Geliştirme için log

            if response_info["action"] == "success":
                # 204 No Content durumunda response.text boş olabilir.
                return response.json() if response.status_code != 204 and response.text else {"status": "success", "message": response_info["message"], "status_code": response.status_code}
            elif response_info["action"] == "refresh_access_token":
                # print(f"Erişim token'ı ({username}) süresi dolmuş, yenileniyor...") # Geliştirme için log
                new_token: Optional[str] = self.auth_service.refresh_access_token(username)
                if new_token:
                    # print(f"Yeni erişim token'ı alındı ({username}), istek tekrarlanıyor.") # Geliştirme için log
                    headers["Authorization"] = f"Bearer {new_token}"
                    retry_response: Optional[requests.Response] = None
                    try:
                        if method.upper() == 'GET':
                            retry_response = requests.get(url, headers=headers, timeout=10)
                        elif method.upper() == 'POST':
                            retry_response = requests.post(url, json=data, headers=headers, timeout=10)
                        # Diğer metotlar için de retry eklenebilir (PUT, DELETE)
                    except requests.exceptions.RequestException as retry_err:
                        # print(f"Token yenileme sonrası API isteği sırasında ağ hatası ({url}): {str(retry_err)}") # Geliştirme için log
                        return {"error": f"Token yenileme sonrası ağ hatası: {str(retry_err)}", "status_code": 503}
                    
                    if retry_response is not None:
                        retry_info: Dict[str, Any] = self.handle_spotify_response(retry_response)
                        # print(f"Yenilenmiş token ile API yanıtı işlendi: {retry_info}") # Geliştirme için log
                        if retry_info["action"] == "success":
                             return retry_response.json() if retry_response.status_code != 204 and retry_response.text else {"status": "success", "message": retry_info["message"], "status_code": retry_response.status_code}
                
                # print(f"Token yenileme başarısız veya yenileme sonrası istek başarısız ({username}).") # Geliştirme için log
                # Token yenilenemezse veya ikinci deneme de başarısız olursa, orijinal hatayı döndür.
                return {"error": response_info["message"], "status_code": response_info["status_code"], "details": "Token yenileme başarısız veya ikinci deneme de yetkisiz."}
            else:
                # Diğer hata durumları (400, 403, 404, 429, 500 vb.)
                # print(f"Spotify API hatası ({username}, {url}): {response_info}") # Geliştirme için log
                return {"error": response_info["message"], "status_code": response_info["status_code"], "action": response_info["action"]}
            
        except Exception as e:
            # print(f"_make_api_request içinde genel bir hata oluştu ({username}, {endpoint}): {str(e)}") # Geliştirme için log
            # import traceback
            # print(traceback.format_exc()) # Detaylı hata için
            return {"error": f"API isteği sırasında beklenmedik bir hata oluştu: {str(e)}", "status_code": 500}

    # =========================================================================
    # 2.2. PROFİL METOTLARI (PROFILE METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.2.1. get_user_profile(username) : Kullanıcının Spotify profilini alır.
    # -------------------------------------------------------------------------
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Belirtilen Beatify kullanıcısının bağlı olduğu Spotify hesabının
        profil bilgilerini alır. (Endpoint: /v1/me)

        Args:
            username (str): Profil bilgileri alınacak Beatify kullanıcısının adı.

        Returns:
            Optional[Dict[str, Any]]: Kullanıcının Spotify profil verileri veya hata durumunda None/hata sözlüğü.
        """
        # print(f"Spotify kullanıcı profili isteniyor: {username}") # Geliştirme için log
        return self._make_api_request(username, "me")

    # -------------------------------------------------------------------------
    # 2.2.2. get_user_playlists(username, limit=50) : Kullanıcının çalma listelerini alır.
    # -------------------------------------------------------------------------
    def get_user_playlists(self, username: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Belirtilen Beatify kullanıcısının Spotify çalma listelerini alır.
        Sayfalama için `limit` ve `offset` parametreleri kullanılabilir.
        (Endpoint: /v1/me/playlists)

        Args:
            username (str): Çalma listeleri alınacak Beatify kullanıcısının adı.
            limit (int, optional): Döndürülecek maksimum çalma listesi sayısı (1-50). Varsayılan 20.
            offset (int, optional): Sonucun başlangıç indeksi (sayfalama için). Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Çalma listelerini içeren bir sözlük (Spotify Paging Object formatında)
                                      veya hata durumunda None/hata sözlüğü.
        """
        limit = max(1, min(limit, 50)) # Spotify limiti 1-50 arası
        offset = max(0, offset)
        # print(f"Spotify kullanıcı çalma listeleri isteniyor: {username}, Limit={limit}, Offset={offset}") # Geliştirme için log
        return self._make_api_request(username, f"me/playlists?limit={limit}&offset={offset}")

    # -------------------------------------------------------------------------
    # 2.2.3. get_user_top_items(...) : Kullanıcının en çok dinlediklerini alır.
    # -------------------------------------------------------------------------
    def get_user_top_items(self, username: str, item_type: str, time_range: str = "medium_term", limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının belirli bir zaman aralığında en çok dinlediği
        sanatçıları (`artists`) veya parçaları (`tracks`) alır.
        (Endpoint: /v1/me/top/{type})

        Args:
            username (str): Verileri alınacak Beatify kullanıcısının adı.
            item_type (str): Alınacak öğe türü. 'artists' veya 'tracks' olmalıdır.
            time_range (str, optional): Zaman aralığı. 'short_term' (son 4 hafta),
                                      'medium_term' (son 6 ay), 'long_term' (tüm zamanlar).
                                      Varsayılan 'medium_term'.
            limit (int, optional): Döndürülecek maksimum öğe sayısı (1-50). Varsayılan 20.

        Returns:
            Optional[Dict[str, Any]]: En çok dinlenen öğeleri içeren bir sözlük
                                      veya hata/geçersiz parametre durumunda None/hata sözlüğü.
        """
        if item_type not in ['artists', 'tracks']:
            # print(f"Geçersiz top item türü: {item_type}") # Geliştirme için log
            return {"error": "Geçersiz öğe türü. 'artists' veya 'tracks' olmalı.", "status_code": 400}
        if time_range not in ['short_term', 'medium_term', 'long_term']:
            time_range = 'medium_term' # Geçersizse varsayılana dön
        limit = max(1, min(limit, 50))

        # print(f"Spotify kullanıcı top öğeleri isteniyor: {username}, Tür={item_type}, ZamanAralığı={time_range}, Limit={limit}") # Geliştirme için log
        endpoint: str = f"me/top/{item_type}?time_range={time_range}&limit={limit}"
        return self._make_api_request(username, endpoint)

    # =========================================================================
    # 2.3. OYNATICI KONTROL METOTLARI (PLAYBACK CONTROL METHODS)
    # =========================================================================
    # Bu metotlar genellikle 204 No Content veya hata döndürür.
    # Başarı durumunu kontrol etmek için dönüş değerinin None olup olmadığına bakılabilir
    # veya _make_api_request'ten dönen {"status": "success"} kontrol edilebilir.
    # Daha net olması için bool döndürecek şekilde ayarlandı.

    # -------------------------------------------------------------------------
    # 2.3.1. play(...) : Çalmayı başlatır veya devam ettirir.
    # -------------------------------------------------------------------------
    def play(self, username: str, context_uri: Optional[str] = None, uris: Optional[List[str]] = None, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalmayı başlatır/devam ettirir.
        Belirli bir context (albüm/çalma listesi) veya parça(lar) çalabilir.
        (Endpoint: PUT /v1/me/player/play)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            context_uri (Optional[str], optional): Çalınacak context'in URI'si (albüm, çalma listesi, sanatçı).
            uris (Optional[List[str]], optional): Çalınacak parçaların URI listesi. `context_uri` ile birlikte kullanılamaz.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si. Belirtilmezse aktif cihaz kullanılır.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"Spotify play isteği: {username}, Context={context_uri}, URIs={uris}, Device={device_id}") # Geliştirme için log
        payload: Dict[str, Any] = {}
        if context_uri:
            payload["context_uri"] = context_uri
        if uris: # uris ve context_uri aynı anda gönderilirse Spotify hata verir. Öncelik uris'e verilebilir.
            payload["uris"] = uris
            if "context_uri" in payload and uris: # Eğer ikisi de varsa context_uri'yi kaldır
                del payload["context_uri"]


        endpoint: str = "me/player/play"
        if device_id:
            endpoint += f"?device_id={device_id}"

        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT", data=payload if payload else None)
        return response is not None and response.get("status") == "success"


    # -------------------------------------------------------------------------
    # 2.3.2. pause(username, device_id=None) : Çalmayı duraklatır.
    # -------------------------------------------------------------------------
    def pause(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalmayı duraklatır.
        (Endpoint: PUT /v1/me/player/pause)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"Spotify pause isteği: {username}, Device={device_id}") # Geliştirme için log
        endpoint: str = "me/player/pause"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.3. next_track(username, device_id=None) : Sonraki parçaya geçer.
    # -------------------------------------------------------------------------
    def next_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında sonraki parçaya geçer.
        (Endpoint: POST /v1/me/player/next)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"Spotify next_track isteği: {username}, Device={device_id}") # Geliştirme için log
        endpoint: str = "me/player/next"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.4. previous_track(username, device_id=None) : Önceki parçaya geçer.
    # -------------------------------------------------------------------------
    def previous_track(self, username: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında önceki parçaya geçer.
        (Endpoint: POST /v1/me/player/previous)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        # print(f"Spotify previous_track isteği: {username}, Device={device_id}") # Geliştirme için log
        endpoint: str = "me/player/previous"
        if device_id:
            endpoint += f"?device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="POST")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.5. seek_to_position(...) : Parçada belirli bir pozisyona atlar.
    # -------------------------------------------------------------------------
    def seek_to_position(self, username: str, position_ms: int, device_id: Optional[str] = None) -> bool:
        """
        O anda çalmakta olan parçada belirtilen milisaniye pozisyonuna atlar.
        (Endpoint: PUT /v1/me/player/seek)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            position_ms (int): Atlanacak pozisyon (milisaniye cinsinden).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        if not isinstance(position_ms, int) or position_ms < 0:
            # print(f"Geçersiz pozisyon değeri: {position_ms}") # Geliştirme için log
            return False
        # print(f"Spotify seek isteği: {username}, PositionMs={position_ms}, Device={device_id}") # Geliştirme için log
        endpoint: str = f"me/player/seek?position_ms={position_ms}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.6. set_volume(...) : Çalma ses seviyesini ayarlar.
    # -------------------------------------------------------------------------
    def set_volume(self, username: str, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında çalma ses seviyesini ayarlar.
        (Endpoint: PUT /v1/me/player/volume)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            volume_percent (int): Ses seviyesi (0-100 arası).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        if not isinstance(volume_percent, int) or not (0 <= volume_percent <= 100):
            # print(f"Geçersiz ses seviyesi: {volume_percent}") # Geliştirme için log
            return False
        # print(f"Spotify volume isteği: {username}, Volume={volume_percent}, Device={device_id}") # Geliştirme için log
        endpoint: str = f"me/player/volume?volume_percent={volume_percent}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.7. set_repeat_mode(...) : Tekrar modunu ayarlar.
    # -------------------------------------------------------------------------
    def set_repeat_mode(self, username: str, repeat_state: str, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında tekrar modunu ayarlar.
        (Endpoint: PUT /v1/me/player/repeat)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            repeat_state (str): Tekrar modu. 'track', 'context' veya 'off' olmalıdır.
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        if repeat_state not in ['track', 'context', 'off']:
            # print(f"Geçersiz tekrar modu: {repeat_state}") # Geliştirme için log
            return False
        # print(f"Spotify repeat_mode isteği: {username}, State={repeat_state}, Device={device_id}") # Geliştirme için log
        endpoint: str = f"me/player/repeat?state={repeat_state}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # -------------------------------------------------------------------------
    # 2.3.8. set_shuffle(...) : Karışık çalma modunu ayarlar.
    # -------------------------------------------------------------------------
    def set_shuffle(self, username: str, shuffle_state: bool, device_id: Optional[str] = None) -> bool:
        """
        Kullanıcının aktif cihazında karışık çalma modunu açar veya kapatır.
        (Endpoint: PUT /v1/me/player/shuffle)

        Args:
            username (str): İşlemi yapacak Beatify kullanıcısı.
            shuffle_state (bool): Karışık çalma durumu (True: açık, False: kapalı).
            device_id (Optional[str], optional): İşlemin yapılacağı cihazın ID'si.

        Returns:
            bool: İşlem başarılıysa True, aksi halde False.
        """
        if not isinstance(shuffle_state, bool):
            return False # Veya bir hata fırlat
        # print(f"Spotify shuffle isteği: {username}, State={shuffle_state}, Device={device_id}") # Geliştirme için log
        state_str: str = 'true' if shuffle_state else 'false'
        endpoint: str = f"me/player/shuffle?state={state_str}"
        if device_id:
            endpoint += f"&device_id={device_id}"
        response = self._make_api_request(username=username, endpoint=endpoint, method="PUT")
        return response is not None and response.get("status") == "success"

    # =========================================================================
    # 2.4. OYNATMA BİLGİSİ METOTLARI (PLAYBACK INFORMATION METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.4.1. get_currently_playing(username) : O anda çalan parçayı alır.
    # -------------------------------------------------------------------------
    def get_currently_playing(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının o anda çalmakta olduğu parça hakkında detaylı bilgi alır.
        Eğer bir şey çalmıyorsa, yanıtın `item` alanı null olabilir veya `is_playing` false olabilir.
        (Endpoint: GET /v1/me/player/currently-playing)

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.

        Returns:
            Optional[Dict[str, Any]]: O anda çalan parça verileri veya hata/içerik yoksa None/hata sözlüğü.
                                      Başarılı ama içerik yoksa Spotify 204 dönebilir, bu durumda
                                      _make_api_request {"status": "success", "message": "..."} döner.
        """
        # print(f"Spotify get_currently_playing isteği: {username}") # Geliştirme için log
        return self._make_api_request(username=username, endpoint="me/player/currently-playing")

    # -------------------------------------------------------------------------
    # 2.4.2. get_playback_state(username) : Mevcut çalma durumunu alır.
    # -------------------------------------------------------------------------
    def get_playback_state(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının mevcut çalma durumu hakkında bilgi alır (cihaz, çalma ilerlemesi,
        karışık çalma/tekrar modu, o anda çalan parça vb.).
        (Endpoint: GET /v1/me/player)

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.

        Returns:
            Optional[Dict[str, Any]]: Çalma durumu verileri veya hata/içerik yoksa None/hata sözlüğü.
        """
        # print(f"Spotify get_playback_state isteği: {username}") # Geliştirme için log
        return self._make_api_request(username=username, endpoint="me/player")

    # -------------------------------------------------------------------------
    # 2.4.3. get_recently_played(username, limit=20) : Son dinlenenleri alır.
    # -------------------------------------------------------------------------
    def get_recently_played(self, username: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının son dinlediği parçaları alır.
        (Endpoint: GET /v1/me/player/recently-played)

        Args:
            username (str): Bilgisi alınacak Beatify kullanıcısı.
            limit (int, optional): Döndürülecek maksimum parça sayısı (1-50). Varsayılan 20.

        Returns:
            Optional[Dict[str, Any]]: Son dinlenen parçaları içeren bir sözlük
                                      veya hata durumunda None/hata sözlüğü.
        """
        limit = max(1, min(limit, 50)) # Spotify limiti 1-50 arası
        # print(f"Spotify get_recently_played isteği: {username}, Limit={limit}") # Geliştirme için log
        return self._make_api_request(username=username, endpoint=f"me/player/recently-played?limit={limit}")

    # -------------------------------------------------------------------------
    # 2.4.4. get_available_devices(username) : Aktif cihazları listeler.
    # -------------------------------------------------------------------------
    def get_available_devices(self, username: str) -> List[Dict[str, Any]]: # Her zaman liste döner (başarılıysa dolu, değilse boş)
        """
        Kullanıcının Spotify hesabına bağlı ve kontrol edilebilir aktif cihazları listeler.
        (Endpoint: GET /v1/me/player/devices)

        Args:
            username (str): Cihazları listelenecek Beatify kullanıcısı.

        Returns:
            List[Dict[str, Any]]: Aktif cihazların listesi. Hata durumunda veya cihaz yoksa boş liste.
        """
        # print(f"Spotify get_available_devices isteği: {username}") # Geliştirme için log
        response_data = self._make_api_request(username=username, endpoint="me/player/devices")
        if response_data and isinstance(response_data.get("devices"), list) and not response_data.get("error"):
            return response_data["devices"]
        # print(f"Aktif cihaz alınamadı veya bulunamadı ({username}). Yanıt: {response_data}") # Geliştirme için log
        return []

    # =========================================================================
    # 2.5. ÖNERİ METOTLARI (RECOMMENDATIONS METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.5.1. get_recommendations(...) : Müzik önerileri alır.
    # -------------------------------------------------------------------------
    def get_recommendations(self, username: str, seed_artists: Optional[List[str]] = None,
                            seed_tracks: Optional[List[str]] = None, seed_genres: Optional[List[str]] = None,
                            limit: int = 20, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Belirtilen tohum (seed) sanatçılar, parçalar ve/veya türlere göre
        Spotify'dan müzik önerileri alır. En fazla 5 tohum öğesi kullanılabilir.
        (Endpoint: GET /v1/recommendations)

        Args:
            username (str): Öneri alınacak Beatify kullanıcısı.
            seed_artists (Optional[List[str]], optional): Tohum sanatçı ID'leri listesi.
            seed_tracks (Optional[List[str]], optional): Tohum parça ID'leri listesi.
            seed_genres (Optional[List[str]], optional): Tohum tür adları listesi.
            limit (int, optional): Döndürülecek maksimum öneri sayısı (1-100). Varsayılan 20.
            **kwargs: Diğer ayarlanabilir parametreler (örn: market, min_popularity, target_danceability).
                      Spotify API dokümanlarına bakınız.

        Returns:
            Optional[Dict[str, Any]]: Önerilen parçaları içeren bir sözlük
                                      veya hata/geçersiz parametre durumunda None/hata sözlüğü.
        """
        seed_artists = seed_artists or []
        seed_tracks = seed_tracks or []
        seed_genres = seed_genres or []
        limit = max(1, min(limit, 100)) # Spotify limiti 1-100 arası

        # print(f"Spotify öneri isteği: {username}, Sanatçılar={seed_artists}, Parçalar={seed_tracks}, Türler={seed_genres}, Limit={limit}, EkParametreler={kwargs}") # Geliştirme için log

        # En fazla 5 tohum öğesi kontrolü
        total_seeds = len(seed_artists) + len(seed_tracks) + len(seed_genres)
        if total_seeds == 0:
            # print("Öneri için en az bir tohum öğesi (sanatçı, parça veya tür) gereklidir.") # Geliştirme için log
            return {"error": "Öneri için en az bir tohum (seed) öğesi gereklidir.", "status_code": 400}
        if total_seeds > 5:
            # print(f"Çok fazla tohum öğesi ({total_seeds}). En fazla 5 adet olabilir. Kırpılıyor...") # Geliştirme için log
            # Basit bir kırpma stratejisi (öncelik sırasına göre ayarlanabilir)
            temp_seed_artists, temp_seed_tracks, temp_seed_genres = [], [], []
            current_count = 0
            for item_list, temp_list in [(seed_tracks, temp_seed_tracks), (seed_artists, temp_seed_artists), (seed_genres, temp_seed_genres)]:
                can_add = 5 - current_count
                if can_add <= 0: break
                added_count = min(len(item_list), can_add)
                temp_list.extend(item_list[:added_count])
                current_count += added_count
            seed_artists, seed_tracks, seed_genres = temp_seed_artists, temp_seed_tracks, temp_seed_genres
            # print(f"Kırpılmış tohumlar: Sanatçılar={seed_artists}, Parçalar={seed_tracks}, Türler={seed_genres}") # Geliştirme için log


        params_list: List[str] = []
        if seed_artists: params_list.append(f"seed_artists={','.join(seed_artists)}")
        if seed_tracks: params_list.append(f"seed_tracks={','.join(seed_tracks)}")
        if seed_genres: params_list.append(f"seed_genres={','.join(seed_genres)}")
        params_list.append(f"limit={limit}")

        # Ekstra parametreleri ekle (kwargs)
        for key, value in kwargs.items():
            if value is not None: # Sadece değeri olan parametreleri ekle
                params_list.append(f"{key}={value}")
        
        endpoint: str = f"recommendations?{'&'.join(params_list)}"
        return self._make_api_request(username=username, endpoint=endpoint)

    # =========================================================================
    # 2.6. YARDIMCI METOTLAR (HELPER METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.6.1. _ensure_datetime_naive(dt) : Datetime'ı saf (naive) hale getirir.
    # -------------------------------------------------------------------------
    def _ensure_datetime_naive(self, dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
        """
        Verilen datetime nesnesini veya ISO formatındaki string'i,
        zaman dilimi bilgisi olmayan (naive) bir datetime nesnesine dönüştürür.
        Bu, farklı sistemler arasında zaman karşılaştırmalarını basitleştirmek
        veya veritabanına kaydederken tutarlılık sağlamak için kullanılabilir.

        Args:
            dt (Optional[Union[datetime, str]]): Dönüştürülecek datetime nesnesi veya ISO formatında string.

        Returns:
            Optional[datetime]: Zaman dilimi bilgisi olmayan (naive) datetime nesnesi veya None.
        """
        if dt is None:
            return None

        if isinstance(dt, str):
            try:
                # String'i datetime nesnesine çevirirken, eğer string'de zaman dilimi bilgisi
                # varsa (örn: +00:00 veya Z), fromisoformat bunu dikkate alarak aware bir nesne oluşturur.
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00')) # 'Z' UTC demek
            except ValueError:
                # print(f"Geçersiz ISO formatında tarih string'i: {dt}") # Geliştirme için log
                return None # Veya hata fırlat
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            # print(f"Beklenmeyen tarih tipi: {type(dt)}") # Geliştirme için log
            return None # Veya hata fırlat

        # Eğer datetime nesnesi zaman dilimi bilgisine sahipse (aware), naive yap.
        # Genellikle UTC'ye çevirip sonra tzinfo'yu kaldırmak daha güvenlidir,
        # ama burada sadece tzinfo'yu kaldırıyoruz.
        if dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None:
            # print(f"Zaman dilimi bilgisi olan tarih ({dt_obj}) naive yapılıyor.") # Geliştirme için log
            return dt_obj.replace(tzinfo=None)
        
        return dt_obj # Zaten naive ise veya tzinfo yoksa olduğu gibi döndür

# =============================================================================
# Spotify API Servis Modülü Sonu
# =============================================================================
