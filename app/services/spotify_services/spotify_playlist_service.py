# =============================================================================
# Spotify Çalma Listesi Servis Modülü (Spotify Playlist Service Module)
# =============================================================================
# Bu modül, Spotify çalma listeleri ile ilgili çeşitli işlemleri (çalma
# listelerini alma, oluşturma, güncelleme, takip etme, parça ekleme/çıkarma,
# yeniden sıralama, arama yapma ve formatlama) yöneten bir servis sınıfı
# (SpotifyPlaylistService) içerir. Temel API etkileşimleri için
# SpotifyApiService'i kullanır ve loglama için logging modülünü kullanır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modülleri, tipler ve alt servislerin içe aktarılması.
# 2.0  SPOTIFY ÇALMA LİSTESİ SERVİS SINIFI (SPOTIFY PLAYLIST SERVICE CLASS)
#      2.1. SpotifyPlaylistService
#           : Spotify çalma listesi işlemlerini yöneten ana servis sınıfı.
#           2.1.1.  __init__(api_service=None)
#                   : Başlatıcı metot. SpotifyApiService örneğini ve logger'ı ayarlar.
#
#           2.2. ÇALMA LİSTESİ ALMA METOTLARI (PLAYLIST RETRIEVAL METHODS)
#                2.2.1. Kullanıcı Çalma Listeleri (User Playlists)
#                       2.2.1.1. get_user_playlists(username, limit=50, offset=0)
#                                : Kullanıcının Spotify çalma listelerini alır.
#                       2.2.1.2. get_playlist(username, playlist_id)
#                                : Belirli bir ID'ye sahip çalma listesini alır.
#                       2.2.1.3. get_playlist_tracks(username, playlist_id, limit=100, offset=0)
#                                : Belirli bir çalma listesindeki parçaları alır. (Yeni Eklendi)
#                2.2.2. Öne Çıkan ve Kategori Çalma Listeleri (Featured and Category Playlists)
#                       2.2.2.1. get_featured_playlists(username, limit=20, offset=0)
#                                : Spotify'ın öne çıkan çalma listelerini alır.
#                       2.2.2.2. get_category_playlists(username, category_id, limit=20, offset=0)
#                                : Belirli bir kategoriye ait çalma listelerini alır.
#                       2.2.2.3. get_categories(username, limit=20, offset=0)
#                                : Mevcut Spotify kategori listesini alır.
#
#           2.3. ÇALMA LİSTESİ YÖNETİM METOTLARI (PLAYLIST MANAGEMENT METHODS)
#                2.3.1. Oluşturma ve Güncellemeler (Creation and Updates)
#                       2.3.1.1. create_playlist(username, user_id, name, public=True, description="")
#                                : Yeni bir çalma listesi oluşturur.
#                       2.3.1.2. update_playlist_details(username, playlist_id, name=None, public=None, description=None)
#                                : Bir çalma listesinin detaylarını günceller.
#                2.3.2. Takip Etme ve Takipten Çıkma (Following and Unfollowing)
#                       2.3.2.1. follow_playlist(username, playlist_id, public=True)
#                                : Bir çalma listesini takip eder.
#                       2.3.2.2. unfollow_playlist(username, playlist_id)
#                                : Bir çalma listesini takipten çıkar.
#
#           2.4. ÇALMA LİSTESİ ÖĞE METOTLARI (PLAYLIST ITEM METHODS)
#                2.4.1. Öğeleri Ekleme (Adding Items)
#                       2.4.1.1. add_items_to_playlist(username, playlist_id, uris, position=None)
#                                : Bir çalma listesine parça(lar) ekler.
#                2.4.2. Öğeleri Kaldırma (Removing Items)
#                       2.4.2.1. remove_items_from_playlist(username, playlist_id, uris)
#                                : Bir çalma listesinden parça(ları) kaldırır.
#                2.4.3. Öğeleri Yeniden Sıralama (Reordering Items)
#                       2.4.3.1. reorder_playlist_items(username, playlist_id, range_start, insert_before, range_length=1)
#                                : Bir çalma listesindeki parçaların sırasını değiştirir.
#
#           2.5. ARAMA VE FORMATLAMA METOTLARI (SEARCH AND FORMATTING METHODS)
#                2.5.1. search_items(username, query, item_type='track', limit=20)
#                       : Spotify'da parça, albüm, sanatçı veya çalma listesi arar.
#                2.5.2. format_playlist_for_display(playlist_data)
#                       : API'den gelen çalma listesi verisini gösterim için formatlar.
#                2.5.3. format_track_for_display(track_data)
#                       : API'den gelen parça verisini gösterim için formatlar. (Yeni Eklendi)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import logging # Hata ve bilgi loglaması için
import urllib.parse # URL encode işlemleri için (search_items içinde kullanılıyor)
from typing import Optional, Dict, Any, List, Union # Tip ipuçları için
from app.services.spotify_services.spotify_api_service import SpotifyApiService

# =============================================================================
# 2.0 SPOTIFY ÇALMA LİSTESİ SERVİS SINIFI (SPOTIFY PLAYLIST SERVICE CLASS)
# =============================================================================
class SpotifyPlaylistService:
    """
    Spotify çalma listeleri ile ilgili işlemleri yönetmek için servis sınıfı.
    Bu sınıf, `SpotifyApiService` üzerinden Spotify API'si ile etkileşim kurar.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__(api_service=None) : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        SpotifyPlaylistService sınıfının başlatıcı metodu.

        Args:
            api_service (SpotifyApiService, optional): Kullanılacak Spotify API servisi.
                                                       Eğer sağlanmazsa, yeni bir örneği oluşturulur.
        """
        self.api_service: SpotifyApiService = api_service or SpotifyApiService()
        self.logger: logging.Logger = logging.getLogger(__name__) # Sınıfa özel logger
        # print("SpotifyPlaylistService örneği oluşturuldu.") # Geliştirme için log

    # =========================================================================
    # 2.2. ÇALMA LİSTESİ ALMA METOTLARI (PLAYLIST RETRIEVAL METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.2.1. Kullanıcı Çalma Listeleri (User Playlists)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.2.1.1. get_user_playlists(...) : Kullanıcının çalma listelerini alır.
    # -------------------------------------------------------------------------
    def get_user_playlists(self, username: str, limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Belirtilen Beatify kullanıcısının Spotify çalma listelerini alır.
        (Endpoint: GET /v1/me/playlists)

        Args:
            username (str): Çalma listeleri alınacak Beatify kullanıcısının adı.
            limit (int, optional): Döndürülecek maksimum çalma listesi sayısı (1-50). Varsayılan 50.
            offset (int, optional): Sonucun başlangıç indeksi (sayfalama için). Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Çalma listelerini içeren bir sözlük (Spotify Paging Object formatında)
                                      veya hata durumunda None.
        """
        # print(f"PlaylistService: Kullanıcı çalma listeleri isteniyor - Kullanıcı={username}, Limit={limit}, Offset={offset}") # Geliştirme için log
        try:
            # Spotify API limiti 1-50 arasıdır.
            if not (1 <= limit <= 50):
                self.logger.warning(f"Geçersiz limit değeri ({limit}) get_user_playlists için. Varsayılan 50 kullanılacak.")
                limit = 50
            if offset < 0:
                self.logger.warning(f"Geçersiz offset değeri ({offset}) get_user_playlists için. Varsayılan 0 kullanılacak.")
                offset = 0

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"me/playlists?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı ({username}) çalma listeleri alınırken hata: {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.2.1.2. get_playlist(...) : Belirli bir çalma listesini alır.
    # -------------------------------------------------------------------------
    def get_playlist(self, username: str, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Belirli bir `playlist_id`'ye sahip Spotify çalma listesinin detaylarını alır.
        (Endpoint: GET /v1/playlists/{playlist_id})

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Detayları alınacak çalma listesinin Spotify ID'si.

        Returns:
            Optional[Dict[str, Any]]: Çalma listesi bilgilerini içeren bir sözlük veya hata durumunda None.
        """
        # print(f"PlaylistService: Çalma listesi detayı isteniyor - Kullanıcı={username}, PlaylistID={playlist_id}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz veya boş playlist_id sağlandı (get_playlist).")
                return None

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}" # ID'de boşluk olmamalı
            )
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) detayları alınırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.2.1.3. get_playlist_tracks(...) : Çalma listesindeki parçaları alır. (Yeni Eklendi)
    # -------------------------------------------------------------------------
    def get_playlist_tracks(self, username: str, playlist_id: str, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Belirli bir `playlist_id`'ye sahip Spotify çalma listesindeki parçaları alır.
        (Endpoint: GET /v1/playlists/{playlist_id}/tracks)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Parçaları alınacak çalma listesinin Spotify ID'si.
            limit (int, optional): Döndürülecek maksimum parça sayısı (1-100). Varsayılan 100.
            offset (int, optional): Sonucun başlangıç indeksi. Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Çalma listesi parçalarını içeren bir sözlük (Paging Object)
                                      veya hata durumunda None.
        """
        # print(f"PlaylistService: Çalma listesi parçaları isteniyor - Kullanıcı={username}, PlaylistID={playlist_id}, Limit={limit}, Offset={offset}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz veya boş playlist_id sağlandı (get_playlist_tracks).")
                return None
            if not (1 <= limit <= 100): # Spotify API limiti 1-100
                self.logger.warning(f"Geçersiz limit değeri ({limit}) get_playlist_tracks için. Varsayılan 100 kullanılacak.")
                limit = 100
            if offset < 0:
                self.logger.warning(f"Geçersiz offset değeri ({offset}) get_playlist_tracks için. Varsayılan 0 kullanılacak.")
                offset = 0

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) parçaları alınırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.2.2. Öne Çıkan ve Kategori Çalma Listeleri (Featured and Category Playlists)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.2.2.1. get_featured_playlists(...) : Öne çıkan çalma listelerini alır.
    # -------------------------------------------------------------------------
    def get_featured_playlists(self, username: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Spotify tarafından öne çıkarılan çalma listelerini alır.
        (Endpoint: GET /v1/browse/featured-playlists)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            limit (int, optional): Döndürülecek maksimum çalma listesi sayısı (1-50). Varsayılan 20.
            offset (int, optional): Sonucun başlangıç indeksi. Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Öne çıkan çalma listelerini içeren bir sözlük veya hata durumunda None.
        """
        # print(f"PlaylistService: Öne çıkan çalma listeleri isteniyor - Kullanıcı={username}, Limit={limit}, Offset={offset}") # Geliştirme için log
        try:
            if not (1 <= limit <= 50):
                self.logger.warning(f"Geçersiz limit değeri ({limit}) get_featured_playlists için. Varsayılan 20 kullanılacak.")
                limit = 20
            if offset < 0:
                offset = 0

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/featured-playlists?limit={limit}&offset={offset}"
                # Ek parametreler eklenebilir: country, locale, timestamp
            )
        except Exception as e:
            self.logger.error(f"Öne çıkan çalma listeleri alınırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.2.2.2. get_category_playlists(...) : Kategori çalma listelerini alır.
    # -------------------------------------------------------------------------
    def get_category_playlists(self, username: str, category_id: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Belirli bir Spotify kategorisine ait çalma listelerini alır.
        (Endpoint: GET /v1/browse/categories/{category_id}/playlists)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            category_id (str): Çalma listeleri alınacak kategorinin ID'si.
            limit (int, optional): Döndürülecek maksimum çalma listesi sayısı (1-50). Varsayılan 20.
            offset (int, optional): Sonucun başlangıç indeksi. Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Kategoriye ait çalma listelerini içeren bir sözlük veya hata durumunda None.
        """
        # print(f"PlaylistService: Kategori çalma listeleri isteniyor - Kullanıcı={username}, KategoriID={category_id}, Limit={limit}, Offset={offset}") # Geliştirme için log
        try:
            if not category_id or not category_id.strip():
                self.logger.error("Geçersiz veya boş category_id sağlandı (get_category_playlists).")
                return None
            if not (1 <= limit <= 50):
                limit = 20
            if offset < 0:
                offset = 0

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories/{category_id.strip()}/playlists?limit={limit}&offset={offset}"
                # Ek parametre: country
            )
        except Exception as e:
            self.logger.error(f"Kategori ({category_id}) çalma listeleri alınırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.2.2.3. get_categories(...) : Mevcut Spotify kategorilerini alır.
    # -------------------------------------------------------------------------
    def get_categories(self, username: str, limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Spotify'da mevcut olan müzik kategorilerinin bir listesini alır.
        (Endpoint: GET /v1/browse/categories)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            limit (int, optional): Döndürülecek maksimum kategori sayısı (1-50). Varsayılan 20.
            offset (int, optional): Sonucun başlangıç indeksi. Varsayılan 0.

        Returns:
            Optional[Dict[str, Any]]: Kategorileri içeren bir sözlük (Paging Object içinde 'categories' anahtarı)
                                      veya hata durumunda None.
        """
        # print(f"PlaylistService: Kategoriler isteniyor - Kullanıcı={username}, Limit={limit}, Offset={offset}") # Geliştirme için log
        try:
            if not (1 <= limit <= 50):
                limit = 20
            if offset < 0:
                offset = 0

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories?limit={limit}&offset={offset}"
                # Ek parametreler: country, locale
            )
        except Exception as e:
            self.logger.error(f"Kategoriler alınırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return None

    # =========================================================================
    # 2.3. ÇALMA LİSTESİ YÖNETİM METOTLARI (PLAYLIST MANAGEMENT METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.3.1. Oluşturma ve Güncellemeler (Creation and Updates)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.3.1.1. create_playlist(...) : Yeni bir çalma listesi oluşturur.
    # -------------------------------------------------------------------------
    def create_playlist(self, username: str, user_id: str, name: str, public: bool = True, collaborative: bool = False, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Belirtilen Spotify kullanıcısı için yeni bir çalma listesi oluşturur.
        (Endpoint: POST /v1/users/{user_id}/playlists)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı (token almak için).
            user_id (str): Çalma listesinin oluşturulacağı Spotify kullanıcı ID'si.
            name (str): Oluşturulacak çalma listesinin adı.
            public (bool, optional): Çalma listesinin herkese açık olup olmayacağı. Varsayılan True.
                                     `collaborative` True ise `public` False olmalıdır.
            collaborative (bool, optional): Çalma listesinin işbirlikçi olup olmayacağı. Varsayılan False.
                                            İşbirlikçi ise otomatik olarak özel (public=False) olur.
            description (str, optional): Çalma listesi için açıklama. Varsayılan boş.

        Returns:
            Optional[Dict[str, Any]]: Oluşturulan çalma listesi bilgilerini içeren bir sözlük
                                      veya hata durumunda None.
        """
        # print(f"PlaylistService: Yeni çalma listesi oluşturuluyor - İstek Sahibi={username}, SpotifyKullanıcıID={user_id}, Ad={name}") # Geliştirme için log
        try:
            if not user_id or not user_id.strip() or not name or not name.strip():
                self.logger.error("Çalma listesi oluşturma için user_id veya name eksik/geçersiz.")
                return None

            payload: Dict[str, Union[str, bool]] = {
                "name": name.strip(),
                "public": public,
                "collaborative": collaborative,
                "description": description.strip()
            }
            # Spotify dokümantasyonuna göre: If true the playlist will be collaborative. Note that to create a collaborative playlist you must also set public to false.
            if collaborative:
                payload["public"] = False


            result = self.api_service._make_api_request(
                username=username,
                endpoint=f"users/{user_id.strip()}/playlists",
                method="POST",
                data=payload
            )

            if result and not result.get("error"): # _make_api_request hata durumunda error içeren dict dönebilir
                self.logger.info(f"'{name}' adlı çalma listesi kullanıcı ({user_id}) için başarıyla oluşturuldu.")
            else:
                self.logger.error(f"'{name}' adlı çalma listesi oluşturulamadı. Yanıt: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Çalma listesi ('{name}') oluşturulurken hata (Kullanıcı: {username}, SpotifyKullanıcıID: {user_id}): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.3.1.2. update_playlist_details(...) : Çalma listesi detaylarını günceller.
    # -------------------------------------------------------------------------
    def update_playlist_details(self, username: str, playlist_id: str, name: Optional[str] = None,
                                public: Optional[bool] = None, collaborative: Optional[bool] = None,
                                description: Optional[str] = None) -> bool:
        """
        Mevcut bir çalma listesinin adını, herkese açıklık durumunu, işbirlikçilik
        durumunu veya açıklamasını günceller.
        (Endpoint: PUT /v1/playlists/{playlist_id})

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Detayları güncellenecek çalma listesinin Spotify ID'si.
            name (Optional[str], optional): Yeni çalma listesi adı.
            public (Optional[bool], optional): Yeni herkese açıklık durumu.
            collaborative (Optional[bool], optional): Yeni işbirlikçilik durumu.
            description (Optional[str], optional): Yeni çalma listesi açıklaması.

        Returns:
            bool: Güncelleme başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesi detayları güncelleniyor - Kullanıcı={username}, PlaylistID={playlist_id}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz veya boş playlist_id sağlandı (update_playlist_details).")
                return False

            payload: Dict[str, Union[str, bool]] = {}
            if name is not None: payload["name"] = name.strip()
            if public is not None: payload["public"] = public
            if collaborative is not None: payload["collaborative"] = collaborative
            if description is not None: payload["description"] = description.strip()
            
            if not payload: # Güncellenecek bir şey yoksa
                self.logger.info(f"Çalma listesi ({playlist_id}) için güncellenecek bir detay sağlanmadı.")
                return True # Başarılı sayılabilir

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}",
                method="PUT",
                data=payload
            )
            # PUT istekleri genellikle 200 OK veya 204 No Content ile başarılı olur.
            # _make_api_request bunu {"status": "success"} olarak döndürür.
            if response and response.get("status") == "success":
                self.logger.info(f"Çalma listesi ({playlist_id}) detayları başarıyla güncellendi.")
                return True
            
            self.logger.error(f"Çalma listesi ({playlist_id}) detayları güncellenemedi. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) detayları güncellenirken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # 2.3.2. Takip Etme ve Takipten Çıkma (Following and Unfollowing)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.3.2.1. follow_playlist(...) : Bir çalma listesini takip eder.
    # -------------------------------------------------------------------------
    def follow_playlist(self, username: str, playlist_id: str, public: bool = True) -> bool:
        """
        Kullanıcının belirtilen Spotify çalma listesini takip etmesini sağlar.
        (Endpoint: PUT /v1/playlists/{playlist_id}/followers)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Takip edilecek çalma listesinin Spotify ID'si.
            public (bool, optional): Takip edilen çalma listesinin kullanıcının
                                     herkese açık profilinde görünüp görünmeyeceği. Varsayılan True.

        Returns:
            bool: Takip etme işlemi başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesi takip ediliyor - Kullanıcı={username}, PlaylistID={playlist_id}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz veya boş playlist_id sağlandı (follow_playlist).")
                return False

            payload: Dict[str, bool] = {"public": public}
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/followers",
                method="PUT",
                data=payload # Spotify API'si bu endpoint için boş gövde veya public parametresi kabul eder.
            )
            if response and response.get("status") == "success":
                self.logger.info(f"Çalma listesi ({playlist_id}) kullanıcı ({username}) tarafından başarıyla takip edildi.")
                return True
            
            self.logger.error(f"Çalma listesi ({playlist_id}) takip edilemedi. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) takip edilirken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # 2.3.2.2. unfollow_playlist(...) : Bir çalma listesini takipten çıkar.
    # -------------------------------------------------------------------------
    def unfollow_playlist(self, username: str, playlist_id: str) -> bool:
        """
        Kullanıcının belirtilen Spotify çalma listesini takipten çıkmasını sağlar.
        (Endpoint: DELETE /v1/playlists/{playlist_id}/followers)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Takipten çıkılacak çalma listesinin Spotify ID'si.

        Returns:
            bool: Takipten çıkma işlemi başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesi takipten çıkarılıyor - Kullanıcı={username}, PlaylistID={playlist_id}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz veya boş playlist_id sağlandı (unfollow_playlist).")
                return False

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/followers",
                method="DELETE"
            )
            if response and response.get("status") == "success":
                self.logger.info(f"Çalma listesi ({playlist_id}) kullanıcı ({username}) tarafından başarıyla takipten çıkarıldı.")
                return True
            
            self.logger.error(f"Çalma listesi ({playlist_id}) takipten çıkarılamadı. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) takipten çıkarılırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # =========================================================================
    # 2.4. ÇALMA LİSTESİ ÖĞE METOTLARI (PLAYLIST ITEM METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.4.1. Öğeleri Ekleme (Adding Items)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.4.1.1. add_items_to_playlist(...) : Çalma listesine parça(lar) ekler.
    # -------------------------------------------------------------------------
    def add_items_to_playlist(self, username: str, playlist_id: str, uris: List[str], position: Optional[int] = None) -> bool:
        """
        Belirtilen çalma listesine bir veya daha fazla parça ekler.
        (Endpoint: POST /v1/playlists/{playlist_id}/tracks)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Parçaların ekleneceği çalma listesinin Spotify ID'si.
            uris (List[str]): Eklenecek Spotify parça URI'lerinin listesi.
                              (örn: ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh", ...])
            position (Optional[int], optional): Parçaların ekleneceği pozisyon (0 tabanlı).
                                                Belirtilmezse listenin sonuna eklenir.

        Returns:
            bool: Ekleme işlemi başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesine öğe ekleniyor - Kullanıcı={username}, PlaylistID={playlist_id}, URI Sayısı={len(uris)}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip() or not uris:
                self.logger.error("Geçersiz playlist_id veya boş URI listesi sağlandı (add_items_to_playlist).")
                return False

            # Spotify API bir istekte en fazla 100 parça eklemeye izin verir.
            if len(uris) > 100:
                self.logger.warning(f"100'den fazla URI ({len(uris)}) sağlandı, sadece ilk 100'ü eklenecek (PlaylistID: {playlist_id}).")
                uris = uris[:100]

            payload: Dict[str, Any] = {"uris": uris}
            if position is not None and isinstance(position, int) and position >= 0:
                payload["position"] = position

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="POST",
                data=payload
            )
            # Başarılı POST genellikle 201 Created döndürür.
            if response and not response.get("error"): # snapshot_id döner, error yoksa başarılıdır
                self.logger.info(f"{len(uris)} parça çalma listesine ({playlist_id}) başarıyla eklendi.")
                return True
            
            self.logger.error(f"Çalma listesine ({playlist_id}) öğe eklenemedi. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesine ({playlist_id}) öğe eklenirken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # 2.4.2. Öğeleri Kaldırma (Removing Items)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.4.2.1. remove_items_from_playlist(...) : Çalma listesinden parça(lar) kaldırır.
    # -------------------------------------------------------------------------
    def remove_items_from_playlist(self, username: str, playlist_id: str, uris: List[str]) -> bool:
        """
        Belirtilen çalma listesinden bir veya daha fazla parçayı kaldırır.
        (Endpoint: DELETE /v1/playlists/{playlist_id}/tracks)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Parçaların kaldırılacağı çalma listesinin Spotify ID'si.
            uris (List[str]): Kaldırılacak Spotify parça URI'lerinin listesi.

        Returns:
            bool: Kaldırma işlemi başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesinden öğe kaldırılıyor - Kullanıcı={username}, PlaylistID={playlist_id}, URI Sayısı={len(uris)}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip() or not uris:
                self.logger.error("Geçersiz playlist_id veya boş URI listesi sağlandı (remove_items_from_playlist).")
                return False

            # API, {"tracks": [{"uri": "spotify:track:..."}]} formatında bekler.
            tracks_to_remove: List[Dict[str, str]] = [{"uri": uri} for uri in uris]
            
            # Bir istekte en fazla 100 parça
            if len(tracks_to_remove) > 100:
                 self.logger.warning(f"100'den fazla URI ({len(uris)}) sağlandı, sadece ilk 100'ü silinecek (PlaylistID: {playlist_id}).")
                 tracks_to_remove = tracks_to_remove[:100]


            payload: Dict[str, List[Dict[str, str]]] = {"tracks": tracks_to_remove}

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="DELETE",
                data=payload
            )
            if response and not response.get("error"): # snapshot_id döner
                self.logger.info(f"{len(uris)} parça çalma listesinden ({playlist_id}) başarıyla kaldırıldı.")
                return True
            
            self.logger.error(f"Çalma listesinden ({playlist_id}) öğe kaldırılamadı. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesinden ({playlist_id}) öğe kaldırılırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # 2.4.3. Öğeleri Yeniden Sıralama (Reordering Items)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 2.4.3.1. reorder_playlist_items(...) : Çalma listesindeki parçaların sırasını değiştirir.
    # -------------------------------------------------------------------------
    def reorder_playlist_items(self, username: str, playlist_id: str, range_start: int, insert_before: int, range_length: int = 1, snapshot_id: Optional[str] = None) -> bool:
        """
        Bir çalma listesindeki bir veya daha fazla parçanın sırasını değiştirir.
        (Endpoint: PUT /v1/playlists/{playlist_id}/tracks)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            playlist_id (str): Parçaları yeniden sıralanacak çalma listesinin Spotify ID'si.
            range_start (int): Yeniden sıralanacak ilk parçanın mevcut pozisyonu (0 tabanlı).
            insert_before (int): Parçaların taşınacağı yeni pozisyon (0 tabanlı).
            range_length (int, optional): Yeniden sıralanacak parça sayısı. Varsayılan 1.
            snapshot_id (Optional[str], optional): Eğer sağlanırsa, çalma listesinin belirli bir
                                                   versiyonu üzerinde işlem yapar.

        Returns:
            bool: Yeniden sıralama işlemi başarılıysa True, aksi halde False.
        """
        # print(f"PlaylistService: Çalma listesi öğeleri yeniden sıralanıyor - Kullanıcı={username}, PlaylistID={playlist_id}, Start={range_start}, Before={insert_before}") # Geliştirme için log
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("Geçersiz playlist_id sağlandı (reorder_playlist_items).")
                return False
            if not (isinstance(range_start, int) and range_start >= 0 and
                    isinstance(insert_before, int) and insert_before >= 0 and
                    isinstance(range_length, int) and range_length >= 1):
                self.logger.error("Geçersiz sıralama parametreleri (range_start, insert_before, range_length).")
                return False

            payload: Dict[str, Any] = {
                "range_start": range_start,
                "insert_before": insert_before,
                "range_length": range_length
            }
            if snapshot_id:
                payload["snapshot_id"] = snapshot_id

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="PUT",
                data=payload
            )
            if response and not response.get("error"): # snapshot_id döner
                self.logger.info(f"Çalma listesindeki ({playlist_id}) öğeler başarıyla yeniden sıralandı.")
                return True
            
            self.logger.error(f"Çalma listesindeki ({playlist_id}) öğeler yeniden sıralanamadı. Yanıt: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Çalma listesindeki ({playlist_id}) öğeler yeniden sıralanırken hata (Kullanıcı: {username}): {str(e)}", exc_info=True)
            return False

    # =========================================================================
    # 2.5. ARAMA VE FORMATLAMA METOTLARI (SEARCH AND FORMATTING METHODS)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 2.5.1. search_items(...) : Spotify'da öğe arar.
    # -------------------------------------------------------------------------
    def search_items(self, username: str, query: str, item_types: List[str] = ['track'], limit: int = 20, offset: int = 0, market: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Spotify'da belirtilen sorgu ile parça, albüm, sanatçı veya çalma listesi arar.
        (Endpoint: GET /v1/search)

        Args:
            username (str): İsteği yapan Beatify kullanıcısının adı.
            query (str): Arama sorgusu.
            item_types (List[str], optional): Aranacak öğe türlerinin listesi.
                                             Geçerli türler: 'album', 'artist', 'playlist', 'track', 'show', 'episode'.
                                             Varsayılan ['track'].
            limit (int, optional): Her öğe türü için döndürülecek maksimum sonuç sayısı (1-50). Varsayılan 20.
            offset (int, optional): Sonucun başlangıç indeksi. Varsayılan 0.
            market (Optional[str], optional): ISO 3166-1 alpha-2 ülke kodu. Sonuçları belirli bir pazara göre filtreler.

        Returns:
            Optional[Dict[str, Any]]: Arama sonuçlarını içeren bir sözlük (her öğe türü için ayrı bir anahtar altında
                                      Paging Object) veya hata durumunda None.
        """
        # print(f"PlaylistService: Spotify'da arama yapılıyor - Kullanıcı={username}, Sorgu='{query}', Türler={item_types}") # Geliştirme için log
        try:
            if not query or not query.strip():
                self.logger.error("Boş arama sorgusu sağlandı (search_items).")
                return None
            if not item_types:
                self.logger.error("Aranacak öğe türü belirtilmedi (search_items).")
                return {"error": "Aranacak en az bir öğe türü belirtmelisiniz.", "status_code": 400}

            valid_types = {'album', 'artist', 'playlist', 'track', 'show', 'episode'}
            sanitized_item_types = [t for t in item_types if t in valid_types]
            if not sanitized_item_types:
                self.logger.error(f"Geçersiz öğe türleri sağlandı: {item_types}")
                return {"error": f"Geçersiz arama türleri. Geçerli olanlar: {valid_types}", "status_code": 400}


            if not (1 <= limit <= 50):
                limit = 20
            if offset < 0:
                offset = 0

            encoded_query: str = urllib.parse.quote(query.strip())
            types_str: str = ",".join(sanitized_item_types)
            
            endpoint_url: str = f"search?q={encoded_query}&type={types_str}&limit={limit}&offset={offset}"
            if market:
                endpoint_url += f"&market={market}"

            return self.api_service._make_api_request(
                username=username,
                endpoint=endpoint_url
            )
        except Exception as e:
            self.logger.error(f"Spotify'da arama yapılırken hata (Kullanıcı: {username}, Sorgu: '{query}'): {str(e)}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # 2.5.2. format_playlist_for_display(...) : Çalma listesi verisini formatlar.
    # -------------------------------------------------------------------------
    def format_playlist_for_display(self, playlist_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Spotify API'sinden gelen ham çalma listesi verisini, kullanıcı arayüzünde
        gösterim için daha uygun bir formata dönüştürür.

        Args:
            playlist_data (Optional[Dict[str, Any]]): Spotify API'sinden alınan çalma listesi sözlüğü.

        Returns:
            Dict[str, Any]: Formatlanmış çalma listesi verilerini içeren bir sözlük.
                            Eğer `playlist_data` None veya boş ise boş bir sözlük döner.
        """
        if not playlist_data:
            return {}
        # print(f"PlaylistService: Çalma listesi formatlanıyor - ID={playlist_data.get('id')}") # Geliştirme için log
        try:
            images: List[Dict[str, Any]] = playlist_data.get("images", [])
            playlist_image_url: str = images[0]["url"] if images else ""

            owner_data: Dict[str, Any] = playlist_data.get("owner", {})
            owner_name: str = owner_data.get("display_name", "Bilinmeyen Sahip")

            tracks_data: Dict[str, Any] = playlist_data.get("tracks", {})
            track_count: int = tracks_data.get("total", 0)

            return {
                "id": playlist_data.get("id", ""),
                "name": playlist_data.get("name", "Bilinmeyen Çalma Listesi"),
                "description": playlist_data.get("description", ""),
                "image_url": playlist_image_url,
                "owner_name": owner_name,
                "owner_url": owner_data.get("external_urls", {}).get("spotify"),
                "track_count": track_count,
                "public": playlist_data.get("public", False),
                "collaborative": playlist_data.get("collaborative", False),
                "external_url": playlist_data.get("external_urls", {}).get("spotify", ""),
                "uri": playlist_data.get("uri", "")
                # Ek bilgiler eklenebilir: snapshot_id, followers.total vb.
            }
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_data.get('id')}) formatlanırken hata: {str(e)}", exc_info=True)
            return {"error": "Çalma listesi formatlanırken hata oluştu.", "id": playlist_data.get("id")}


    # -------------------------------------------------------------------------
    # 2.5.3. format_track_for_display(...) : Parça verisini formatlar. (Yeni Eklendi)
    # -------------------------------------------------------------------------
    def format_track_for_display(self, track_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Spotify API'sinden gelen ham parça verisini (Track Object), kullanıcı arayüzünde
        gösterim için daha uygun bir formata dönüştürür.

        Args:
            track_data (Optional[Dict[str, Any]]): Spotify API'sinden alınan parça sözlüğü.
                                                  Bu, bir çalma listesi öğesindeki 'track' alanı olabilir.

        Returns:
            Dict[str, Any]: Formatlanmış parça verilerini içeren bir sözlük.
                            Eğer `track_data` None veya boş ise boş bir sözlük döner.
        """
        if not track_data:
            return {}
        # print(f"PlaylistService: Parça formatlanıyor - ID={track_data.get('id')}") # Geliştirme için log
        try:
            album_data: Dict[str, Any] = track_data.get("album", {})
            album_images: List[Dict[str, Any]] = album_data.get("images", [])
            album_image_url: str = album_images[0]["url"] if album_images else ""

            artists_data: List[Dict[str, Any]] = track_data.get("artists", [])
            artist_names: List[str] = [artist.get("name", "") for artist in artists_data if artist.get("name")]
            
            duration_ms: Optional[int] = track_data.get("duration_ms")
            duration_str: str = ""
            if duration_ms is not None:
                seconds = int((duration_ms / 1000) % 60)
                minutes = int((duration_ms / (1000 * 60)) % 60)
                duration_str = f"{minutes:01}:{seconds:02}"


            return {
                "id": track_data.get("id", ""),
                "name": track_data.get("name", "Bilinmeyen Parça"),
                "artists": artist_names,
                "album_name": album_data.get("name", "Bilinmeyen Albüm"),
                "album_image_url": album_image_url,
                "duration_ms": duration_ms,
                "duration_str": duration_str, # mm:ss formatında süre
                "popularity": track_data.get("popularity"), # 0-100 arası
                "preview_url": track_data.get("preview_url"),
                "external_url": track_data.get("external_urls", {}).get("spotify", ""),
                "uri": track_data.get("uri", ""),
                "is_playable": track_data.get("is_playable", True), # Bazı marketlerde çalınamayabilir
                "explicit": track_data.get("explicit", False)
            }
        except Exception as e:
            self.logger.error(f"Parça ({track_data.get('id')}) formatlanırken hata: {str(e)}", exc_info=True)
            return {"error": "Parça formatlanırken hata oluştu.", "id": track_data.get("id")}

# =============================================================================
# Spotify Çalma Listesi Servis Modülü Sonu
# =============================================================================
