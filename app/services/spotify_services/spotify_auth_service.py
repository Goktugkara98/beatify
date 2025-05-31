# =============================================================================
# Spotify Authentication Service
# =============================================================================
# Contents:
# 1. Imports
# 2. SpotifyAuthService Class
#    2.1. Initialization
#    2.2. OAuth Flow Methods
#    2.3. Token Management
#    2.4. Account Management
#    2.5. Helper Methods
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import base64
import requests
from datetime import datetime, timedelta
from flask import session
from app.config.spotify_config import SpotifyConfig
from app.database.models.database import SpotifyRepository

# -----------------------------------------------------------------------------
# 2. SpotifyAuthService Class
# -----------------------------------------------------------------------------
class SpotifyAuthService:
    # 2.1. Initialization
    def __init__(self):
        self.auth_url = SpotifyConfig.AUTH_URL
        self.token_url = SpotifyConfig.TOKEN_URL
        self.redirect_uri = SpotifyConfig.REDIRECT_URI
        self.scopes = SpotifyConfig.SCOPES
        self.spotify_repo = SpotifyRepository()
    
    # 2.2. OAuth Flow Methods
    def get_authorization_url(self, username):
        # Get Spotify credentials
        spotify_credentials = self.spotify_repo.spotify_get_user_data(username)
        client_id = spotify_credentials.get('client_id')
        client_secret = spotify_credentials.get('client_secret')
        
        # Validate client ID
        if not client_id or not client_secret:
            return None
        
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes
        }
        
        url_args = "&".join([f"{key}={requests.utils.quote(str(val))}" for key, val in auth_params.items()])
        return f"{self.auth_url}?{url_args}"
    
    def exchange_code_for_token(self, code, client_id, client_secret):
        try:
            # Encode API credentials in Base64
            credentials = f"{client_id}:{client_secret}"
            base64_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Prepare request data
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            headers = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Send token request
            response = requests.post(self.token_url, data=data, headers=headers)
            
            if response.status_code != 200:
                return None
                
            token_info = response.json()
            
            # Store token information in session
            session['access_token'] = token_info.get('access_token')
            session['token_expires_at'] = (datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))).isoformat()

            return token_info
            
        except Exception:
            return None
    
    # 2.3. Token Management
    def refresh_access_token(self, username):
        try:
            # Get Spotify credentials
            spotify_credentials = self.spotify_repo.spotify_get_user_data(username)
            if not spotify_credentials:
                return None
                
            client_id = spotify_credentials.get('client_id')
            client_secret = spotify_credentials.get('client_secret')
            refresh_token = spotify_credentials.get('refresh_token')
            
            if not all([client_id, client_secret, refresh_token]):
                return None
                
            # Encode API credentials in Base64
            credentials = f"{client_id}:{client_secret}"
            base64_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Prepare request data
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            headers = {
                "Authorization": f"Basic {base64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Send token request
            response = requests.post(self.token_url, data=data, headers=headers)
            
            if response.status_code != 200:
                return None
                
            # Get token information
            token_info = response.json()
            access_token = token_info.get('access_token')
            
            # Update session with naive datetime
            session['access_token'] = access_token
            expires_at = datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
            session['token_expires_at'] = expires_at.isoformat()
            
            # Update database if there's a new refresh token
            if 'refresh_token' in token_info:
                session['refresh_token'] = token_info['refresh_token']
                self.spotify_repo.spotify_update_user_info(
                    username=username,
                    spotify_user_id=spotify_credentials.get('spotify_user_id'),
                    refresh_token=token_info['refresh_token']
                )
            else:
                self.spotify_repo.spotify_update_user_info(
                    username=username,
                    spotify_user_id=spotify_credentials.get('spotify_user_id'),
                    refresh_token=refresh_token
                )
            
            return access_token
            
        except Exception:
            return None
    
    def get_valid_access_token(self, username):
        # First check session
        access_token = session.get('access_token')
        token_expires_at = session.get('token_expires_at')
        
        # If token exists in session and is valid, use it
        if access_token and token_expires_at:
            # Convert string to datetime if needed
            if isinstance(token_expires_at, str):
                try:
                    token_expires_at = datetime.fromisoformat(token_expires_at)
                except ValueError:
                    token_expires_at = None
            
            # Ensure both datetimes are timezone-naive for comparison
            now = datetime.now()
            
            # Make sure token_expires_at has no timezone info
            if token_expires_at and hasattr(token_expires_at, 'tzinfo') and token_expires_at.tzinfo is not None:
                token_expires_at = token_expires_at.replace(tzinfo=None)
            
            # Compare with buffer time
            if token_expires_at and token_expires_at > now + timedelta(minutes=5):
                return access_token
        
        # Otherwise, refresh the token
        return self.refresh_access_token(username)
    
    # 2.4. Account Management
    def save_spotify_user_info(self, username, spotify_user_id, refresh_token):
        try:
            # Save tokens to session
            session['refresh_token'] = refresh_token
            session['spotify_user_id'] = spotify_user_id
            
            # Save to database
            result = self.spotify_repo.spotify_update_user_info(
                username=username,
                spotify_user_id=spotify_user_id,
                refresh_token=refresh_token
            )
            
            if not result:
                return False
                
            return True
            
        except Exception:
            return False
    
    def unlink_spotify_account(self, username):
        try:
            # Clear Spotify session data
            session.pop('access_token', None)
            session.pop('token_expires_at', None)

            
            # Clear from database
            result = self.spotify_repo.spotify_delete_linked_account_data(username)
            
            if not result:
                return False
                
            return True
            
        except Exception:
            return False

    # 2.5. Helper Methods
    def _ensure_datetime_naive(self, dt):
        if dt is None:
            return None
            
        # Convert string to datetime if needed
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                return None
                
        # Remove timezone info if present
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        return dt
