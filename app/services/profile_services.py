# =============================================================================
# Profile Services Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Profile Data Functions
#    2.1. Request Handlers
# 3. Helper Functions
#    3.1. Default Data Creation
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import logging
from app.database.models.database import UserRepository, SpotifyRepository
from app.services.spotify_services.spotify_api_service import SpotifyApiService
from app.services.spotify_services.spotify_service import create_default_spotify_data

# -----------------------------------------------------------------------------
# 2. Profile Data Functions
# -----------------------------------------------------------------------------
# 2.1. Request Handlers
def handle_get_request(username):
    logger = logging.getLogger(__name__)
    logger.info(f"Handling GET request for profile data: {username}")
    
    try:
        # Get user data
        user_repo = UserRepository()
        user_data = user_repo.beatify_get_user_data(username)
        
        if not user_data:
            logger.error(f"User data not found: {username}")
            return {}, {}, create_default_spotify_data('No Data')
        
        # Get Spotify credentials
        spotify_repo = SpotifyRepository()
        spotify_credentials = spotify_repo.spotify_get_user_data(username)
        
        if not spotify_credentials:
            logger.warning(f"No Spotify credentials found: {username}")
            spotify_credentials = {}
            spotify_data = create_default_spotify_data('No Data')
            return user_data, spotify_credentials, spotify_data
        
        # Get Spotify profile data
        if not spotify_credentials.get('spotify_user_id'):
            spotify_data = create_default_spotify_data('Not Connected')
        else:
            spotify_data = SpotifyApiService().get_user_profile(username)
            if spotify_data:
                spotify_data['spotify_data_status'] = 'Connected'
            else:
                spotify_data = create_default_spotify_data('Error')
        
        return user_data, spotify_credentials, spotify_data
        
    except Exception as e:
        logger.error(f"Error handling GET request for profile data: {str(e)}", exc_info=True)
        return {}, {}, create_default_spotify_data('Error')

# -----------------------------------------------------------------------------
# 3. Helper Functions
# -----------------------------------------------------------------------------
# 3.1. Default Data Creation
def create_default_spotify_data(spotify_data_status: str = 'No Data'):
    """
    Create default Spotify data.
    
    This function generates a placeholder Spotify profile data structure
    when actual data cannot be retrieved.
    
    Args:
        spotify_data_status: Status of the Spotify data
        
    Returns:
        dict: Default Spotify profile data structure
    """
    return {
        'spotify_data_status': spotify_data_status,
        'display_name': 'Not Connected',
        'spotify_user_id': None,
        'email': None,
        'country': None,
        'images': [{'url': '/static/img/default_profile.png'}],
        'product': None,
        'followers': {'total': 0},
        'external_urls': {'spotify': '#'}
    }
