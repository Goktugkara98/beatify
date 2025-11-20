"""
Spotify Çalma Listesi Servis Modülü (SpotifyPlaylistService)

Spotify çalma listeleri ile ilgili çeşitli işlemleri yöneten servis sınıfı.
API etkileşimleri için SpotifyApiService'i kullanır.
"""

import logging
import urllib.parse
from typing import Optional, Dict, Any, List, Union
from app.services.spotify.api_service import SpotifyApiService


class SpotifyPlaylistService:
    """
    Spotify çalma listeleri ile ilgili işlemleri yönetmek için servis sınıfı.
    """

    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        SpotifyPlaylistService sınıfının başlatıcı metodu.
        """
        self.api_service: SpotifyApiService = api_service or SpotifyApiService()
        self.logger: logging.Logger = logging.getLogger(__name__)

    # -------------------------------------------------------------------------
    # ÇALMA LİSTESİ VERİSİ ALMA (PLAYLIST DATA RETRIEVAL)
    # -------------------------------------------------------------------------
    def get_user_playlists(
        self,
        username: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Belirtilen kullanıcının Spotify çalma listelerini alır."""
        try:
            limit = max(1, min(limit, 50))
            offset = max(0, offset)
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"me/playlists?limit={limit}&offset={offset}",
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı ({username}) çalma listeleri alınırken hata: {e}", exc_info=True)
            return None

    def get_playlist(self, username: str, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Belirli bir ID'ye sahip çalma listesinin detaylarını alır."""
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("get_playlist için geçersiz playlist_id.")
                return None
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}",
            )
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) detayları alınırken hata: {e}", exc_info=True)
            return None

    def get_playlist_tracks(
        self,
        username: str,
        playlist_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Belirli bir çalma listesindeki parçaları alır."""
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("get_playlist_tracks için geçersiz playlist_id.")
                return None
            limit = max(1, min(limit, 100))
            offset = max(0, offset)
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks?limit={limit}&offset={offset}",
            )
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) parçaları alınırken hata: {e}", exc_info=True)
            return None

    def get_featured_playlists(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Spotify'ın öne çıkan çalma listelerini alır."""
        try:
            limit = max(1, min(limit, 50))
            offset = max(0, offset)
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/featured-playlists?limit={limit}&offset={offset}",
            )
        except Exception as e:
            self.logger.error(f"Öne çıkan çalma listeleri alınırken hata: {e}", exc_info=True)
            return None

    def get_category_playlists(
        self,
        username: str,
        category_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Belirli bir kategoriye ait çalma listelerini alır."""
        try:
            if not category_id or not category_id.strip():
                self.logger.error("get_category_playlists için geçersiz category_id.")
                return None
            limit = max(1, min(limit, 50))
            offset = max(0, offset)
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories/{category_id.strip()}/playlists?limit={limit}&offset={offset}",
            )
        except Exception as e:
            self.logger.error(f"Kategori ({category_id}) çalma listeleri alınırken hata: {e}", exc_info=True)
            return None

    def get_categories(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Spotify'da mevcut olan müzik kategorilerini alır."""
        try:
            limit = max(1, min(limit, 50))
            offset = max(0, offset)
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories?limit={limit}&offset={offset}",
            )
        except Exception as e:
            self.logger.error(f"Kategoriler alınırken hata: {e}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # ÇALMA LİSTESİ YÖNETİMİ (PLAYLIST MANAGEMENT)
    # -------------------------------------------------------------------------
    def create_playlist(
        self,
        username: str,
        user_id: str,
        name: str,
        public: bool = True,
        collaborative: bool = False,
        description: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Belirtilen Spotify kullanıcısı için yeni bir çalma listesi oluşturur."""
        try:
            if not user_id or not user_id.strip() or not name or not name.strip():
                self.logger.error("Çalma listesi oluşturma için user_id veya name eksik/geçersiz.")
                return None

            payload: Dict[str, Union[str, bool]] = {
                "name": name.strip(),
                "public": public,
                "collaborative": collaborative,
                "description": description.strip(),
            }
            if collaborative:
                payload["public"] = False

            return self.api_service._make_api_request(
                username=username,
                endpoint=f"users/{user_id.strip()}/playlists",
                method="POST",
                data=payload,
            )
        except Exception as e:
            self.logger.error(f"Çalma listesi ('{name}') oluşturulurken hata: {e}", exc_info=True)
            return None

    def update_playlist_details(
        self,
        username: str,
        playlist_id: str,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        collaborative: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Mevcut bir çalma listesinin detaylarını günceller."""
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("update_playlist_details için geçersiz playlist_id.")
                return False

            payload: Dict[str, Union[str, bool]] = {}
            if name is not None:
                payload["name"] = name.strip()
            if public is not None:
                payload["public"] = public
            if collaborative is not None:
                payload["collaborative"] = collaborative
            if description is not None:
                payload["description"] = description.strip()

            if not payload:
                return True

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}",
                method="PUT",
                data=payload,
            )
            return response is not None and response.get("status") == "success"
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) detayları güncellenirken hata: {e}", exc_info=True)
            return False

    def follow_playlist(self, username: str, playlist_id: str, public: bool = True) -> bool:
        """Kullanıcının belirtilen çalma listesini takip etmesini sağlar."""
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("follow_playlist için geçersiz playlist_id.")
                return False

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/followers",
                method="PUT",
                data={"public": public},
            )
            return response is not None and response.get("status") == "success"
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) takip edilirken hata: {e}", exc_info=True)
            return False

    def unfollow_playlist(self, username: str, playlist_id: str) -> bool:
        """Kullanıcının belirtilen çalma listesini takipten çıkmasını sağlar."""
        try:
            if not playlist_id or not playlist_id.strip():
                self.logger.error("unfollow_playlist için geçersiz playlist_id.")
                return False

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/followers",
                method="DELETE",
            )
            return response is not None and response.get("status") == "success"
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) takipten çıkarılırken hata: {e}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # ÇALMA LİSTESİ ÖĞELERİNİ YÖNETME (PLAYLIST ITEM MANAGEMENT)
    # -------------------------------------------------------------------------
    def add_items_to_playlist(
        self,
        username: str,
        playlist_id: str,
        uris: List[str],
        position: Optional[int] = None,
    ) -> bool:
        """Belirtilen çalma listesine bir veya daha fazla parça ekler."""
        try:
            if not playlist_id or not playlist_id.strip() or not uris:
                self.logger.error("add_items_to_playlist için geçersiz playlist_id veya boş URI listesi.")
                return False

            payload: Dict[str, Any] = {"uris": uris[:100]}  # En fazla 100 URI
            if position is not None and isinstance(position, int) and position >= 0:
                payload["position"] = position

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="POST",
                data=payload,
            )
            return response is not None and "snapshot_id" in response
        except Exception as e:
            self.logger.error(f"Çalma listesine ({playlist_id}) öğe eklenirken hata: {e}", exc_info=True)
            return False

    def remove_items_from_playlist(self, username: str, playlist_id: str, uris: List[str]) -> bool:
        """Belirtilen çalma listesinden bir veya daha fazla parçayı kaldırır."""
        try:
            if not playlist_id or not playlist_id.strip() or not uris:
                self.logger.error("remove_items_from_playlist için geçersiz playlist_id veya boş URI listesi.")
                return False

            tracks_to_remove = [{"uri": uri} for uri in uris[:100]]  # En fazla 100 URI
            payload = {"tracks": tracks_to_remove}

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="DELETE",
                data=payload,
            )
            return response is not None and "snapshot_id" in response
        except Exception as e:
            self.logger.error(f"Çalma listesinden ({playlist_id}) öğe kaldırılırken hata: {e}", exc_info=True)
            return False

    def reorder_playlist_items(
        self,
        username: str,
        playlist_id: str,
        range_start: int,
        insert_before: int,
        range_length: int = 1,
        snapshot_id: Optional[str] = None,
    ) -> bool:
        """Bir çalma listesindeki bir veya daha fazla parçanın sırasını değiştirir."""
        try:
            if not all(
                [
                    isinstance(range_start, int),
                    range_start >= 0,
                    isinstance(insert_before, int),
                    insert_before >= 0,
                    isinstance(range_length, int),
                    range_length >= 1,
                ]
            ):
                self.logger.error("reorder_playlist_items için geçersiz sıralama parametreleri.")
                return False

            payload: Dict[str, Any] = {
                "range_start": range_start,
                "insert_before": insert_before,
                "range_length": range_length,
            }
            if snapshot_id:
                payload["snapshot_id"] = snapshot_id

            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id.strip()}/tracks",
                method="PUT",
                data=payload,
            )
            return response is not None and "snapshot_id" in response
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_id}) öğeleri yeniden sıralanırken hata: {e}", exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # ARAMA VE FORMATLAMA (SEARCH & FORMATTING)
    # -------------------------------------------------------------------------
    def search_items(
        self,
        username: str,
        query: str,
        item_types: List[str] = ["track"],
        limit: int = 20,
        offset: int = 0,
        market: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Spotify'da belirtilen sorgu ile arama yapar."""
        try:
            if not query or not query.strip() or not item_types:
                self.logger.error("search_items için geçersiz sorgu veya öğe türü.")
                return None

            valid_types = {"album", "artist", "playlist", "track", "show", "episode"}
            types_str = ",".join([t for t in item_types if t in valid_types])
            if not types_str:
                return {"error": "Geçersiz arama türleri."}

            encoded_query = urllib.parse.quote(query.strip())
            endpoint = f"search?q={encoded_query}&type={types_str}&limit={limit}&offset={offset}"
            if market:
                endpoint += f"&market={market}"

            return self.api_service._make_api_request(username=username, endpoint=endpoint)
        except Exception as e:
            self.logger.error(f"Spotify araması sırasında hata (sorgu: '{query}'): {e}", exc_info=True)
            return None

    def format_playlist_for_display(self, playlist_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Ham çalma listesi verisini arayüz için uygun formata dönüştürür."""
        if not playlist_data:
            return {}
        try:
            images = playlist_data.get("images", [])
            owner = playlist_data.get("owner", {})
            return {
                "id": playlist_data.get("id"),
                "name": playlist_data.get("name", "Bilinmeyen Çalma Listesi"),
                "description": playlist_data.get("description", ""),
                "image_url": images[0]["url"] if images else "",
                "owner_name": owner.get("display_name", "Bilinmeyen Sahip"),
                "owner_url": owner.get("external_urls", {}).get("spotify"),
                "track_count": playlist_data.get("tracks", {}).get("total", 0),
                "public": playlist_data.get("public"),
                "external_url": playlist_data.get("external_urls", {}).get("spotify"),
                "uri": playlist_data.get("uri"),
            }
        except Exception as e:
            self.logger.error(f"Çalma listesi ({playlist_data.get('id')}) formatlanırken hata: {e}", exc_info=True)
            return {"error": "Formatlama hatası."}

    def format_track_for_display(self, track_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Ham parça verisini arayüz için uygun formata dönüştürür."""
        if not track_data:
            return {}
        try:
            album = track_data.get("album", {})
            album_images = album.get("images", [])
            artists = track_data.get("artists", [])
            duration_ms = track_data.get("duration_ms", 0)

            duration_str = ""
            if duration_ms:
                seconds = int((duration_ms / 1000) % 60)
                minutes = int((duration_ms / (1000 * 60)) % 60)
                duration_str = f"{minutes:01}:{seconds:02}"

            return {
                "id": track_data.get("id"),
                "name": track_data.get("name", "Bilinmeyen Parça"),
                "artists": [artist.get("name") for artist in artists],
                "album_name": album.get("name", "Bilinmeyen Albüm"),
                "album_image_url": album_images[0]["url"] if album_images else "",
                "duration_ms": duration_ms,
                "duration_str": duration_str,
                "preview_url": track_data.get("preview_url"),
                "external_url": track_data.get("external_urls", {}).get("spotify"),
                "uri": track_data.get("uri"),
            }
        except Exception as e:
            self.logger.error(f"Parça ({track_data.get('id')}) formatlanırken hata: {e}", exc_info=True)
            return {"error": "Formatlama hatası."}


__all__ = ["SpotifyPlaylistService"]

