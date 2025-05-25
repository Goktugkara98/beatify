# =============================================================================
# Spotify API Service
# =============================================================================
# Contents:
# 1. Imports
# 2. SpotifyApiService Class
#    2.1. Initialization
#    2.2. Response Handling
#    2.3. API Request Methods
#    2.4. Profile Methods
#    2.5. Playback Control Methods
#    2.6. Playback Information Methods
#    2.7. Recommendations Methods
#    2.8. Helper Methods
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import requests
from datetime import datetime
from app.config.spotify_config import SpotifyConfig
from app.services.spotify_services.spotify_auth_service import SpotifyAuthService
from flask import session

# -----------------------------------------------------------------------------
# 2. SpotifyApiService Class
# -----------------------------------------------------------------------------
class SpotifyApiService:
    # 2.1. Initialization
    def __init__(self, auth_service=None):
        self.auth_service = auth_service or SpotifyAuthService()
        self.base_url = SpotifyConfig.API_BASE_URL
        self.profile_url = SpotifyConfig.PROFILE_URL
    
    # 2.2. Response Handling
    def handle_spotify_response(self, response):
        status_code = response.status_code
        data = response.json() if response.text else {}

        status_map = {
            200: {"action": "success", "message": "OK"},
            201: {"action": "success", "message": "Created"},
            202: {"action": "success", "message": "Accepted"},
            204: {"action": "success", "message": "No Content"},
            304: {"action": "not_modified", "message": "Not Modified"},
            400: {"action": "client_error", "message": "Bad Request"},
            401: {"action": "refresh_access_token", "message": "Unauthorized"},
            403: {"action": "unauthorized", "message": "Forbidden"},
            404: {"action": "not_found", "message": "Not Found"},
            429: {"action": "rate_limited", "message": "Too Many Requests"},
            500: {"action": "server_error", "message": "Internal Server Error"},
            502: {"action": "server_error", "message": "Bad Gateway"},
            503: {"action": "server_error", "message": "Service Unavailable"}
        }

        response_data = status_map.get(status_code, {"action": "unknown_status", "message": "Unknown error"})

        if "error" in data and isinstance(data["error"], dict):
            response_data["message"] = data["error"].get("message", response_data["message"])

        return response_data
        
    # 2.3. API Request Methods
    def _make_api_request(self, username, endpoint, method='GET', data=None):
        try:
            access_token = self.auth_service.get_valid_access_token(username)
            if not access_token:
                return None
                
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers)
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, headers=headers)
                elif method.upper() == 'PUT':
                    response = requests.put(url, json=data, headers=headers)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers)
                else:
                    return None
            except requests.exceptions.RequestException:
                return None
                
            response_info = self.handle_spotify_response(response)
            
            if response_info["action"] == "success":
                return response.json() if response.text else {"status": "success"}
            elif response_info["action"] == "refresh_access_token":
                new_token = self.auth_service.refresh_access_token(username)
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    try:
                        if method.upper() == 'GET':
                            retry_response = requests.get(url, headers=headers)
                        elif method.upper() == 'POST':
                            retry_response = requests.post(url, json=data, headers=headers)
                        elif method.upper() == 'PUT':
                            retry_response = requests.put(url, json=data, headers=headers)
                        elif method.upper() == 'DELETE':
                            retry_response = requests.delete(url, headers=headers)
                    except requests.exceptions.RequestException:
                        return None
                        
                    retry_info = self.handle_spotify_response(retry_response)
                    if retry_info["action"] == "success":
                        return retry_response.json() if retry_response.text else {"status": "success"}
                
                return None
            else:
                return None
            
        except Exception:
            return None

    # 2.4. Profile Methods
    def get_user_profile(self, username):
        return self._make_api_request(username, "me")
    
    def get_user_playlists(self, username, limit=50):
        return self._make_api_request(username, f"me/playlists?limit={limit}")
    
    def get_user_top_items(self, username, item_type, time_range="medium_term", limit=20):
        if item_type not in ['artists', 'tracks']:
            return None
        
        if time_range not in ['short_term', 'medium_term', 'long_term']:
            time_range = 'medium_term'
            
        return self._make_api_request(
            username, 
            f"me/top/{item_type}?time_range={time_range}&limit={limit}"
        )
    
    # 2.5. Playback Control Methods
    def play(self, username, context_uri=None, uris=None, device_id=None):
        try:
            data = {}
            
            if context_uri:
                data["context_uri"] = context_uri
                
            if uris:
                data["uris"] = uris
                
            endpoint = "me/player/play"
            if device_id:
                endpoint += f"?device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT",
                data=data
            ) is not None
            
        except Exception:
            return False
    
    def pause(self, username, device_id=None):
        try:
            endpoint = "me/player/pause"
            if device_id:
                endpoint += f"?device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT"
            ) is not None
            
        except Exception:
            return False
    
    def next_track(self, username, device_id=None):
        try:
            endpoint = "me/player/next"
            if device_id:
                endpoint += f"?device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="POST"
            ) is not None
            
        except Exception:
            return False
    
    def previous_track(self, username, device_id=None):
        try:
            endpoint = "me/player/previous"
            if device_id:
                endpoint += f"?device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="POST"
            ) is not None
            
        except Exception:
            return False
    
    def seek_to_position(self, username, position_ms, device_id=None):
        try:
            endpoint = f"me/player/seek?position_ms={position_ms}"
            if device_id:
                endpoint += f"&device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT"
            ) is not None
            
        except Exception:
            return False
    
    def set_volume(self, username, volume_percent, device_id=None):
        try:
            if volume_percent < 0 or volume_percent > 100:
                return False
                
            endpoint = f"me/player/volume?volume_percent={volume_percent}"
            if device_id:
                endpoint += f"&device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT"
            ) is not None
            
        except Exception:
            return False
    
    def set_repeat_mode(self, username, repeat_state, device_id=None):
        try:
            if repeat_state not in ['track', 'context', 'off']:
                return False
                
            endpoint = f"me/player/repeat?state={repeat_state}"
            if device_id:
                endpoint += f"&device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT"
            ) is not None
            
        except Exception:
            return False
    
    def set_shuffle(self, username, shuffle_state, device_id=None):
        try:
            endpoint = f"me/player/shuffle?state={'true' if shuffle_state else 'false'}"
            if device_id:
                endpoint += f"&device_id={device_id}"
                
            return self._make_api_request(
                username=username,
                endpoint=endpoint,
                method="PUT"
            ) is not None
            
        except Exception:
            return False
    
    # 2.6. Playback Information Methods
    def get_currently_playing(self, username):
        try:
            return self._make_api_request(
                username=username,
                endpoint="me/player/currently-playing"
            )
        except Exception:
            return None
    
    def get_playback_state(self, username):
        try:
            return self._make_api_request(
                username=username,
                endpoint="me/player"
            )
        except Exception:
            return None
    
    def get_recently_played(self, username, limit=20):
        try:
            if limit < 1 or limit > 50:
                limit = 20
                
            return self._make_api_request(
                username=username,
                endpoint=f"me/player/recently-played?limit={limit}"
            )
        except Exception:
            return None
    
    def get_available_devices(self, username):
        try:
            response = self._make_api_request(
                username=username,
                endpoint="me/player/devices"
            )
            
            return response.get("devices", []) if response else []
        except Exception:
            return []
    
    # 2.7. Recommendations Methods
    def get_recommendations(self, username, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20):
        try:
            seed_artists = seed_artists or []
            seed_tracks = seed_tracks or []
            seed_genres = seed_genres or []
            
            if not seed_artists and not seed_tracks and not seed_genres:
                return None
                
            seed_count = len(seed_artists) + len(seed_tracks) + len(seed_genres)
            if seed_count > 5:
                if len(seed_tracks) > 5:
                    seed_tracks = seed_tracks[:5]
                    seed_artists = []
                    seed_genres = []
                else:
                    remaining = 5 - len(seed_tracks)
                    if len(seed_artists) > remaining:
                        seed_artists = seed_artists[:remaining]
                        seed_genres = []
                    else:
                        remaining -= len(seed_artists)
                        if len(seed_genres) > remaining:
                            seed_genres = seed_genres[:remaining]
            
            params = []
            
            if seed_artists:
                params.append(f"seed_artists={','.join(seed_artists)}")
                
            if seed_tracks:
                params.append(f"seed_tracks={','.join(seed_tracks)}")
                
            if seed_genres:
                params.append(f"seed_genres={','.join(seed_genres)}")
                
            params.append(f"limit={limit}")
            
            endpoint = f"recommendations?{'&'.join(params)}"
            
            return self._make_api_request(
                username=username,
                endpoint=endpoint
            )
        except Exception:
            return None
    
    # 2.8. Helper Methods
    def _ensure_datetime_naive(self, dt):
        if dt is None:
            return None
            
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                return None
                
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        return dt