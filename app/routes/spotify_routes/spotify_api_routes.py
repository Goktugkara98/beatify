# =============================================================================
# Spotify API Routes
# =============================================================================
# Contents:
# 1. Imports
# 2. Main Route Initialization Function
# 3. Player Control Operations
#    3.1. Player Control (Play, Pause, Next, Previous)
# 4. Player Information Operations
#    4.1. Currently Playing Track Information
# 5. Playlist Operations
#    5.1. User Playlists
#    5.2. Playlist Details
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import request, session, jsonify
from app.services.spotify_services.spotify_player_service import SpotifyPlayerService
from app.services.spotify_services.spotify_playlist_service import SpotifyPlaylistService

# -----------------------------------------------------------------------------
# 2. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_spotify_api_routes(app):
    # Registers Spotify API routes to the Flask application
    # Initialize services
    spotify_player_service = SpotifyPlayerService()
    spotify_playlist_service = SpotifyPlaylistService()
    
    # -----------------------------------------------------------------------------
    # 3. Player Control Operations
    # -----------------------------------------------------------------------------
    # 3.1. Player Control (Play, Pause, Next, Previous)
    @app.route('/api/spotify/player-control/', methods=['POST'])
    def api_spotify_player_control():
        # Provides Spotify player controls (play, pause, next, previous)
        username = session.get('username')
        
        if not username:
            return {"error": "Unauthorized", "success": False}, 401
        
        # Get data from JSON body instead of URL parameters
        data = request.json or {}
        action = data.get('action')
        uri = data.get('uri')
        context_uri = data.get('context_uri')
        
        try:
            if action == 'play':
                if uri:
                    # Play a specific track
                    spotify_player_service.play(username, context_uri=context_uri, uris=[uri])
                elif context_uri:
                    # Play a playlist or album
                    spotify_player_service.play(username, context_uri=context_uri)
                else:
                    # Resume playback
                    spotify_player_service.play(username)
            elif action == 'pause':
                spotify_player_service.pause(username)
            elif action == 'next':
                spotify_player_service.next_track(username)
            elif action == 'previous':
                spotify_player_service.previous_track(username)
            else:
                return {"error": "Invalid action", "success": False}, 400
            
            return {"success": True}
        except Exception as e:
            return {"error": str(e), "success": False}, 500

    # -----------------------------------------------------------------------------
    # 4. Player Information Operations
    # -----------------------------------------------------------------------------
    # 4.1. Currently Playing Track Information
    @app.route('/api/spotify/player-status/')
    def api_spotify_player_status():
        # Retrieves information about the currently playing track
        username = session.get('username')
        
        if not username:
            return {"is_playing": False}, 200
        
        try:
            now_playing = spotify_player_service.get_playback_state(username)
            
            if now_playing and now_playing.get('is_playing'):
                track_data = {
                    "is_playing": True,
                    "track_name": now_playing.get('item', {}).get('name', 'No track information'),
                    "artist_name": now_playing.get('item', {}).get('artists', [{}])[0].get('name', 'No artist information'),
                    "album_image": now_playing.get('item', {}).get('album', {}).get('images', [{}])[0].get('url', ''),
                    "progress_ms": now_playing.get('progress_ms', 0),
                    "duration_ms": now_playing.get('item', {}).get('duration_ms', 0)
                }
                return track_data, 200
            else:
                return {"is_playing": False}, 200
        except Exception as e:
            return {"is_playing": False, "error": str(e)}, 200
            
    # -----------------------------------------------------------------------------
    # 5. Playlist Operations
    # -----------------------------------------------------------------------------
    # 5.1. User Playlists
    @app.route('/api/spotify/playlists/')
    def api_spotify_playlists():
        # Retrieves the user's playlists
        username = session.get('username')
        
        if not username:
            return {"error": "Unauthorized", "success": False}, 401
        
        try:
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            playlists = spotify_playlist_service.get_user_playlists(username, limit, offset)
            
            if not playlists:
                return {"items": [], "total": 0}, 200
                
            # Format the response
            formatted_playlists = []
            for playlist in playlists.get('items', []):
                formatted_playlists.append(spotify_playlist_service.format_playlist_for_display(playlist))
                
            return {
                "items": formatted_playlists,
                "total": playlists.get('total', 0),
                "limit": limit,
                "offset": offset
            }, 200
        except Exception as e:
            return {"error": str(e), "success": False}, 500
            
    # 5.2. Playlist Details
    @app.route('/api/spotify/playlists/<playlist_id>')
    def api_spotify_playlist_details(playlist_id):
        # Retrieves details for a specific playlist
        username = session.get('username')
        
        if not username:
            return {"error": "Unauthorized", "success": False}, 401
        
        try:
            playlist = spotify_playlist_service.get_playlist(username, playlist_id)
            
            if not playlist:
                return {"error": "Playlist not found", "success": False}, 404
                
            # Get tracks
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            tracks_response = spotify_playlist_service.get_playlist_tracks(username, playlist_id, limit, offset)
            
            # Format the response
            formatted_playlist = spotify_playlist_service.format_playlist_for_display(playlist)
            
            # Format tracks
            formatted_tracks = []
            if tracks_response and 'items' in tracks_response:
                for track_item in tracks_response['items']:
                    formatted_tracks.append(
                        spotify_playlist_service.format_track_for_display(track_item)
                    )
            
            # Add tracks to the response
            formatted_playlist['tracks'] = {
                "items": formatted_tracks,
                "total": tracks_response.get('total', 0) if tracks_response else 0,
                "limit": limit,
                "offset": offset
            }
            
            return formatted_playlist, 200
        except Exception as e:
            return {"error": str(e), "success": False}, 500