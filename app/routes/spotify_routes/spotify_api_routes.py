# =============================================================================
# Spotify API Rotaları Modülü (Spotify API Routes Module)
# =============================================================================
# Bu modül, Spotify API'si ile etkileşim kuran ve Flask uygulamasına
# kaydedilen API rotalarını tanımlar. Oynatıcı kontrolü, oynatma durumu
# bilgisi ve çalma listesi işlemleri gibi çeşitli Spotify özelliklerine
# yönelik endpoint'leri içerir.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0 İÇE AKTARMALAR (IMPORTS)
#     : Gerekli Flask bileşenleri ve uygulama servislerinin içe aktarılması.
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
#     2.1. init_spotify_api_routes(app)
#          : Tüm Spotify API rotalarını belirtilen Flask uygulamasına kaydeder.
#          Servis örneklerini başlatır ve rota fonksiyonlarını tanımlar.
#
#     İÇ ROTALAR (init_spotify_api_routes içinde tanımlanır):
#     -------------------------------------------------------------------------
#     3.0 OYNATICI KONTROL İŞLEMLERİ (PLAYER CONTROL OPERATIONS)
#         3.1. api_spotify_player_control()
#              : Spotify oynatıcısını kontrol eder (oynat, duraklat, sonraki, önceki).
#                Rota: /api/spotify/player-control/ (POST)
#     4.0 OYNATICI BİLGİ İŞLEMLERİ (PLAYER INFORMATION OPERATIONS)
#         4.1. api_spotify_player_status()
#              : O anda çalmakta olan parça hakkında bilgi alır.
#                Rota: /api/spotify/player-status/ (GET)
#     5.0 ÇALMA LİSTESİ İŞLEMLERİ (PLAYLIST OPERATIONS)
#         5.1. api_spotify_playlists()
#              : Kullanıcının Spotify çalma listelerini alır.
#                Rota: /api/spotify/playlists/ (GET)
#         5.2. api_spotify_playlist_details(playlist_id)
#              : Belirli bir çalma listesinin detaylarını ve parçalarını alır.
#                Rota: /api/spotify/playlists/<playlist_id> (GET)
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
from flask import request, session, jsonify, Flask # Flask tipi eklendi
from app.services.spotify_services.spotify_player_service import SpotifyPlayerService
from app.services.spotify_services.spotify_playlist_service import SpotifyPlaylistService
from typing import Dict, Any, Tuple # Tip ipuçları için

# =============================================================================
# 2.0 ROTA BAŞLATMA FONKSİYONU (ROUTE INITIALIZATION FUNCTION)
# =============================================================================
# -----------------------------------------------------------------------------
# 2.1. init_spotify_api_routes(app) : Tüm Spotify API rotalarını kaydeder.
# -----------------------------------------------------------------------------
def init_spotify_api_routes(app: Flask):
    """
    Spotify API ile ilgili tüm rotaları belirtilen Flask uygulamasına kaydeder.
    Bu fonksiyon içinde, API endpoint'leri olarak hizmet verecek olan
    iç içe fonksiyonlar tanımlanır ve Flask uygulamasına bağlanır.

    Args:
        app (Flask): Rotaların kaydedileceği Flask uygulama nesnesi.
    """
    # print("Spotify API rotaları başlatılıyor...") # Geliştirme için log

    # Servis örneklerinin başlatılması
    # Bu servisler, Spotify API ile gerçek etkileşimi yönetir.
    spotify_player_service = SpotifyPlayerService()
    spotify_playlist_service = SpotifyPlaylistService()

    # =========================================================================
    # 3.0 OYNATICI KONTROL İŞLEMLERİ (PLAYER CONTROL OPERATIONS)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 3.1. api_spotify_player_control() : Spotify oynatıcısını kontrol eder.
    #      Rota: /api/spotify/player-control/ (POST)
    # -------------------------------------------------------------------------
    @app.route('/api/spotify/player-control/', methods=['POST'])
    def api_spotify_player_control() -> Tuple[Dict[str, Any], int]:
        """
        Spotify oynatıcısını kontrol etmek için bir API endpoint'i.
        İstek gövdesinden alınan 'action' (play, pause, next, previous)
        ve diğer parametrelere (uri, context_uri) göre işlem yapar.
        Kullanıcının oturum açmış olması gerekir.

        Returns:
            Tuple[Dict[str, Any], int]: JSON yanıtı ve HTTP durum kodu.
        """
        # print("API çağrısı: /api/spotify/player-control/") # Geliştirme için log
        username: str | None = session.get('username')

        if not username:
            # print("Yetkisiz erişim denemesi: /api/spotify/player-control/") # Geliştirme için log
            return jsonify({"error": "Yetkisiz erişim. Lütfen giriş yapın.", "success": False}), 401

        data: Dict[str, Any] = request.json or {}
        action: str | None = data.get('action')
        uri: str | None = data.get('uri') # Çalınacak belirli bir parçanın URI'si
        context_uri: str | None = data.get('context_uri') # Çalınacak albüm veya çalma listesinin URI'si

        # print(f"Player control isteği: Kullanıcı={username}, Eylem={action}, URI={uri}, ContextURI={context_uri}") # Geliştirme için log

        try:
            if action == 'play':
                if uri: # Belirli bir parçayı çal
                    spotify_player_service.play(username, context_uri=context_uri, uris=[uri])
                    # print(f"Spotify: '{uri}' parçası çalınıyor (context: {context_uri}).") # Geliştirme için log
                elif context_uri: # Bir albümü veya çalma listesini çal
                    spotify_player_service.play(username, context_uri=context_uri)
                    # print(f"Spotify: '{context_uri}' çalınıyor.") # Geliştirme için log
                else: # Mevcut çalmayı devam ettir
                    spotify_player_service.play(username)
                    # print("Spotify: Çalma devam ettiriliyor.") # Geliştirme için log
            elif action == 'pause':
                spotify_player_service.pause(username)
                # print("Spotify: Çalma duraklatıldı.") # Geliştirme için log
            elif action == 'next':
                spotify_player_service.next_track(username)
                # print("Spotify: Sonraki parçaya geçildi.") # Geliştirme için log
            elif action == 'previous':
                spotify_player_service.previous_track(username)
                # print("Spotify: Önceki parçaya geçildi.") # Geliştirme için log
            else:
                # print(f"Geçersiz oynatıcı eylemi: {action}") # Geliştirme için log
                return jsonify({"error": "Geçersiz eylem. 'play', 'pause', 'next', 'previous' kullanın.", "success": False}), 400

            return jsonify({"message": f"Eylem '{action}' başarıyla gerçekleştirildi.", "success": True}), 200
        except Exception as e:
            # print(f"Spotify oynatıcı kontrol hatası ({username}, {action}): {str(e)}") # Geliştirme için log
            # Daha spesifik hata yönetimi eklenebilir (örn: Spotify API hataları için)
            return jsonify({"error": f"Spotify oynatıcı kontrolü sırasında bir hata oluştu: {str(e)}", "success": False}), 500

    # =========================================================================
    # 4.0 OYNATICI BİLGİ İŞLEMLERİ (PLAYER INFORMATION OPERATIONS)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 4.1. api_spotify_player_status() : O anda çalmakta olan parça bilgisini alır.
    #      Rota: /api/spotify/player-status/ (GET)
    # -------------------------------------------------------------------------
    @app.route('/api/spotify/player-status/', methods=['GET'])
    def api_spotify_player_status() -> Tuple[Dict[str, Any], int]:
        """
        Kullanıcının Spotify'da o anda çalmakta olduğu parça hakkında bilgi alır.
        Kullanıcının oturum açmış olması gerekir. Eğer oturum açık değilse veya
        bir şey çalmıyorsa, uygun bir yanıt döndürür.

        Returns:
            Tuple[Dict[str, Any], int]: JSON yanıtı ve HTTP durum kodu.
        """
        # print("API çağrısı: /api/spotify/player-status/") # Geliştirme için log
        username: str | None = session.get('username')

        if not username:
            # print("Spotify oynatıcı durumu için yetkisiz erişim (oturum yok).") # Geliştirme için log
            # Oturum yoksa, varsayılan olarak bir şey çalmıyor gibi davranılabilir.
            return jsonify({"is_playing": False, "message": "Kullanıcı oturumu bulunamadı."}), 200 # 401 yerine 200 dönebiliriz, widget'lar için.

        try:
            now_playing: Dict[str, Any] | None = spotify_player_service.get_playback_state(username)
            # print(f"Spotify oynatıcı durumu alındı ({username}): {now_playing is not None}") # Geliştirme için log

            if now_playing and now_playing.get('is_playing'):
                item: Dict[str, Any] = now_playing.get('item', {})
                album: Dict[str, Any] = item.get('album', {})
                artists: List[Dict[str, Any]] = item.get('artists', [{}])
                images: List[Dict[str, Any]] = album.get('images', [{}])

                track_data: Dict[str, Any] = {
                    "is_playing": True,
                    "track_name": item.get('name', 'Parça Bilgisi Yok'),
                    "artist_name": artists[0].get('name', 'Sanatçı Bilgisi Yok') if artists else 'Sanatçı Bilgisi Yok',
                    "album_image": images[0].get('url', '') if images else '',
                    "progress_ms": now_playing.get('progress_ms', 0),
                    "duration_ms": item.get('duration_ms', 0),
                    "track_uri": item.get('uri'),
                    "album_uri": album.get('uri'),
                    "artist_uri": artists[0].get('uri') if artists else None,
                    "context_uri": now_playing.get('context', {}).get('uri') if now_playing.get('context') else None,
                    "device_name": now_playing.get('device', {}).get('name', 'Cihaz Bilgisi Yok'),
                    "device_volume": now_playing.get('device', {}).get('volume_percent', 0)
                }
                # print(f"Şu an çalan parça ({username}): {track_data['track_name']}") # Geliştirme için log
                return jsonify(track_data), 200
            else:
                # print(f"Şu an bir şey çalmıyor ({username}).") # Geliştirme için log
                return jsonify({"is_playing": False, "message": "Şu anda aktif bir çalma durumu yok."}), 200
        except Exception as e:
            # print(f"Spotify oynatıcı durumu alınırken hata ({username}): {str(e)}") # Geliştirme için log
            return jsonify({"is_playing": False, "error": f"Oynatıcı durumu alınırken bir hata oluştu: {str(e)}"}), 500 # Hata durumunda 500 daha uygun olabilir.

    # =========================================================================
    # 5.0 ÇALMA LİSTESİ İŞLEMLERİ (PLAYLIST OPERATIONS)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 5.1. api_spotify_playlists() : Kullanıcının Spotify çalma listelerini alır.
    #      Rota: /api/spotify/playlists/ (GET)
    # -------------------------------------------------------------------------
    @app.route('/api/spotify/playlists/', methods=['GET'])
    def api_spotify_playlists() -> Tuple[Dict[str, Any], int]:
        """
        Oturum açmış kullanıcının Spotify çalma listelerini alır.
        Sayfalama için `limit` ve `offset` parametrelerini destekler.

        Returns:
            Tuple[Dict[str, Any], int]: JSON yanıtı ve HTTP durum kodu.
        """
        # print("API çağrısı: /api/spotify/playlists/") # Geliştirme için log
        username: str | None = session.get('username')

        if not username:
            # print("Yetkisiz erişim denemesi: /api/spotify/playlists/") # Geliştirme için log
            return jsonify({"error": "Yetkisiz erişim. Lütfen giriş yapın.", "success": False}), 401

        try:
            limit: int = request.args.get('limit', 20, type=int) # Varsayılan limit 20
            offset: int = request.args.get('offset', 0, type=int)
            # print(f"Çalma listeleri isteniyor: Kullanıcı={username}, Limit={limit}, Offset={offset}") # Geliştirme için log

            playlists_data: Dict[str, Any] | None = spotify_playlist_service.get_user_playlists(username, limit, offset)

            if not playlists_data or not playlists_data.get('items'):
                # print(f"Kullanıcının ({username}) hiç çalma listesi bulunamadı veya API'den boş yanıt geldi.") # Geliştirme için log
                return jsonify({"items": [], "total": 0, "limit": limit, "offset": offset, "message": "Çalma listesi bulunamadı."}), 200

            formatted_playlists: List[Dict[str, Any]] = [
                spotify_playlist_service.format_playlist_for_display(playlist)
                for playlist in playlists_data.get('items', [])
            ]
            # print(f"{len(formatted_playlists)} adet çalma listesi formatlandı ({username}).") # Geliştirme için log

            return jsonify({
                "items": formatted_playlists,
                "total": playlists_data.get('total', 0),
                "limit": playlists_data.get('limit', limit), # API'den gelen limit değerini kullanmak daha doğru
                "offset": playlists_data.get('offset', offset),# API'den gelen offset değerini kullanmak daha doğru
                "next": playlists_data.get('next'),
                "previous": playlists_data.get('previous')
            }), 200
        except Exception as e:
            # print(f"Spotify çalma listeleri alınırken hata ({username}): {str(e)}") # Geliştirme için log
            return jsonify({"error": f"Çalma listeleri alınırken bir hata oluştu: {str(e)}", "success": False}), 500

    # -------------------------------------------------------------------------
    # 5.2. api_spotify_playlist_details(playlist_id) : Belirli bir çalma listesinin detaylarını alır.
    #      Rota: /api/spotify/playlists/<playlist_id> (GET)
    # -------------------------------------------------------------------------
    @app.route('/api/spotify/playlists/<string:playlist_id>', methods=['GET'])
    def api_spotify_playlist_details(playlist_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Belirli bir `playlist_id`'ye sahip Spotify çalma listesinin detaylarını
        ve içindeki parçaları alır. Kullanıcının oturum açmış olması gerekir.
        Parçalar için sayfalama (`limit`, `offset`) destekler.

        Args:
            playlist_id (str): Detayları alınacak çalma listesinin Spotify ID'si.

        Returns:
            Tuple[Dict[str, Any], int]: JSON yanıtı ve HTTP durum kodu.
        """
        # print(f"API çağrısı: /api/spotify/playlists/{playlist_id}") # Geliştirme için log
        username: str | None = session.get('username')

        if not username:
            # print(f"Yetkisiz erişim denemesi (çalma listesi detayları): {playlist_id}") # Geliştirme için log
            return jsonify({"error": "Yetkisiz erişim. Lütfen giriş yapın.", "success": False}), 401

        try:
            # print(f"Çalma listesi detayları isteniyor: Kullanıcı={username}, PlaylistID={playlist_id}") # Geliştirme için log
            playlist_info: Dict[str, Any] | None = spotify_playlist_service.get_playlist(username, playlist_id)

            if not playlist_info:
                # print(f"Çalma listesi bulunamadı: {playlist_id}, Kullanıcı: {username}") # Geliştirme için log
                return jsonify({"error": "Çalma listesi bulunamadı veya erişim yetkiniz yok.", "success": False}), 404

            formatted_playlist: Dict[str, Any] = spotify_playlist_service.format_playlist_for_display(playlist_info)

            # Çalma listesi parçalarını al
            tracks_limit: int = request.args.get('limit', 50, type=int) # Varsayılan parça limiti 50
            tracks_offset: int = request.args.get('offset', 0, type=int)
            # print(f"Çalma listesi parçaları isteniyor: PlaylistID={playlist_id}, Limit={tracks_limit}, Offset={tracks_offset}") # Geliştirme için log

            tracks_response: Dict[str, Any] | None = spotify_playlist_service.get_playlist_tracks(
                username, playlist_id, tracks_limit, tracks_offset
            )

            formatted_tracks: List[Dict[str, Any]] = []
            if tracks_response and tracks_response.get('items'):
                for track_item in tracks_response['items']:
                    if track_item and track_item.get('track'): # Bazı parçalar None gelebilir (örn: yerel dosyalar)
                        formatted_tracks.append(
                            spotify_playlist_service.format_track_for_display(track_item.get('track')) # track_item['track'] olmalı
                        )
            # print(f"{len(formatted_tracks)} adet parça formatlandı (PlaylistID: {playlist_id}).") # Geliştirme için log
            
            formatted_playlist['tracks'] = {
                "items": formatted_tracks,
                "total": tracks_response.get('total', 0) if tracks_response else 0,
                "limit": tracks_response.get('limit', tracks_limit) if tracks_response else tracks_limit,
                "offset": tracks_response.get('offset', tracks_offset) if tracks_response else tracks_offset,
                "next": tracks_response.get('next') if tracks_response else None,
                "previous": tracks_response.get('previous') if tracks_response else None
            }
            # print(f"Çalma listesi detayları başarıyla alındı: {playlist_id}") # Geliştirme için log
            return jsonify(formatted_playlist), 200
        except Exception as e:
            # print(f"Spotify çalma listesi detayları ({playlist_id}, {username}) alınırken hata: {str(e)}") # Geliştirme için log
            return jsonify({"error": f"Çalma listesi detayları alınırken bir hata oluştu: {str(e)}", "success": False}), 500

    # print("Spotify API rotaları başarıyla yüklendi.") # Geliştirme için log
    # init_spotify_api_routes fonksiyonu bir şey döndürmez.
# =============================================================================
# Spotify API Rotaları Modülü Sonu
# =============================================================================
