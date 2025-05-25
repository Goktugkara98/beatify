# =============================================================================
# Spotify Player Service
# =============================================================================
# Contents:
# 1. Imports
# 2. SpotifyPlayerService Class
#    2.1. Initialization
#    2.2. Playback Control Methods
#       2.2.1. Basic Controls
#       2.2.2. Advanced Controls
#    2.3. Playback Information Methods
#       2.3.1. Current Track
#       2.3.2. Playback History
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from app.services.spotify_services.spotify_api_service import SpotifyApiService

# -----------------------------------------------------------------------------
# 2. SpotifyPlayerService Class
# -----------------------------------------------------------------------------
class SpotifyPlayerService:
    
    # 2.1. Initialization
    def __init__(self, api_service=None):
        self.api_service = api_service or SpotifyApiService()
    
    # 2.2. Playback Control Methods
    # -------------------------------------------------------------------------
    # 2.2.1. Basic Controls
    def play(self, username, context_uri=None, uris=None, device_id=None):
        return self.api_service.play(username, context_uri, uris, device_id)
    
    def pause(self, username, device_id=None):
        return self.api_service.pause(username, device_id)
    
    def next_track(self, username, device_id=None):
        return self.api_service.next_track(username, device_id)
    
    def previous_track(self, username, device_id=None):
        return self.api_service.previous_track(username, device_id)
    
    # 2.2.2. Advanced Controls
    def seek_to_position(self, username, position_ms, device_id=None):
        return self.api_service.seek_to_position(username, position_ms, device_id)
    
    def set_volume(self, username, volume_percent, device_id=None):
        return self.api_service.set_volume(username, volume_percent, device_id)
    
    def set_repeat_mode(self, username, repeat_state, device_id=None):
        return self.api_service.set_repeat_mode(username, repeat_state, device_id)
    
    def set_shuffle(self, username, shuffle_state, device_id=None):
        return self.api_service.set_shuffle(username, shuffle_state, device_id)
    
    # 2.3. Playback Information Methods
    # -------------------------------------------------------------------------
    # 2.3.1. Current Track
    def get_currently_playing(self, username):
        return self.api_service.get_currently_playing(username)
    
    def get_playback_state(self, username):
        return self.api_service.get_playback_state(username)
    
    def get_available_devices(self, username):
        return self.api_service.get_available_devices(username)
    
    # 2.3.2. Playback History
    def get_recently_played(self, username, limit=20):
        return self.api_service.get_recently_played(username, limit)
    
    def get_recommendations(self, username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20):
        return self.api_service.get_recommendations(username, seed_artists, seed_tracks, seed_genres, limit)
