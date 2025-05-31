# =============================================================================
# Spotify Service Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Spotify Service Functions
#    2.1. Client Information Management
#    2.2. Profile Data Retrieval
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from app.database.models.database import SpotifyRepository
from app.services.spotify_services.spotify_api_service import SpotifyApiService

# -----------------------------------------------------------------------------
# 2. Spotify Service Functions
# -----------------------------------------------------------------------------
# 2.1. Client Information Management
def update_client_id_and_secret_data(username, client_id, client_secret):
    try:
        # Initialize repository
        spotify_repo = SpotifyRepository()
        
        # Add or update Spotify client info
        result = spotify_repo.spotify_add_or_update_client_info(username, client_id, client_secret)
        return result
    except Exception:
        return False

# 2.2. Profile Data Retrieval
def get_spotify_profile_data(username):
    try:
        # Get Spotify profile data
        spotify_data = SpotifyApiService().get_user_profile(username)
        
        if spotify_data:
            spotify_data['spotify_data_status'] = 'Connected'
            return spotify_data
        else:
            # Check if user has credentials but not connected
            spotify_repo = SpotifyRepository()
            credentials = spotify_repo.spotify_get_user_data(username)
            
            if credentials and credentials.get('client_id') and credentials.get('client_secret'):
                return create_default_spotify_data('Not Connected')
            else:
                return create_default_spotify_data('No Data')
    except Exception:
        return create_default_spotify_data('Error')

def create_default_spotify_data(status):
    return {
        'display_name': 'Not Connected',
        'spotify_user_id': None,
        'email': None,
        'country': None,
        'images': [{'url': '/static/img/default_profile.png'}],
        'product': None,
        'followers': {'total': 0},
        'external_urls': {'spotify': '#'},
        'spotify_data_status': status
    }