# =============================================================================
# Spotify Playlist Service
# =============================================================================
# Contents:
# 1. Imports
# 2. SpotifyPlaylistService Class
#    2.1. Initialization
#    2.2. Playlist Retrieval Methods
#       2.2.1. User Playlists
#       2.2.2. Featured and Category Playlists
#    2.3. Playlist Management Methods
#       2.3.1. Creation and Updates
#       2.3.2. Following and Unfollowing
#    2.4. Playlist Item Methods
#       2.4.1. Adding Items
#       2.4.2. Removing Items
#       2.4.3. Reordering Items
#    2.5. Search and Formatting Methods
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from app.services.spotify_services.spotify_api_service import SpotifyApiService

# -----------------------------------------------------------------------------
# 2. SpotifyPlaylistService Class
# -----------------------------------------------------------------------------
class SpotifyPlaylistService:
    """Service for managing Spotify playlists."""
    
    # 2.1. Initialization
    def __init__(self, api_service: Optional[SpotifyApiService] = None):
        """
        Initializes the Spotify playlist service.
        
        Args:
            api_service: Optional SpotifyApiService instance
        """
        self.api_service = api_service or SpotifyApiService()
        self.logger = logging.getLogger(__name__)
    
    # -------------------------------------------------------------------------
    # 2.2. Playlist Retrieval Methods
    # -------------------------------------------------------------------------
    # 2.2.1. User Playlists
    def get_user_playlists(self, username: str, limit: int = 50, 
                         offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gets the user's playlists.
        
        Args:
            username: Username
            limit: Maximum number of playlists to return
            offset: Index of the first playlist to return
            
        Returns:
            User playlists or None
        """
        try:
            if limit < 1 or limit > 50:
                self.logger.warning(f"Invalid limit value: {limit}, using default of 50")
                limit = 50
                
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"me/playlists?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Error getting user playlists: {str(e)}")
            return None
    
    def get_playlist(self, username: str, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a playlist by ID.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            
        Returns:
            Playlist information or None
        """
        try:
            if not playlist_id:
                self.logger.error("No playlist ID provided")
                return None
                
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}"
            )
        except Exception as e:
            self.logger.error(f"Error getting playlist {playlist_id}: {str(e)}")
            return None
    
    # 2.2.2. Featured and Category Playlists
    def get_featured_playlists(self, username: str, limit: int = 20, 
                             offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gets Spotify's featured playlists.
        
        Args:
            username: Username
            limit: Maximum number of playlists to return
            offset: Index of the first playlist to return
            
        Returns:
            Featured playlists or None
        """
        try:
            if limit < 1 or limit > 50:
                self.logger.warning(f"Invalid limit value: {limit}, using default of 20")
                limit = 20
                
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/featured-playlists?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Error getting featured playlists: {str(e)}")
            return None
    
    def get_category_playlists(self, username: str, category_id: str, 
                             limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gets playlists for a specific category.
        
        Args:
            username: Username
            category_id: Category ID
            limit: Maximum number of playlists to return
            offset: Index of the first playlist to return
            
        Returns:
            Category playlists or None
        """
        try:
            if not category_id:
                self.logger.error("No category ID provided")
                return None
                
            if limit < 1 or limit > 50:
                self.logger.warning(f"Invalid limit value: {limit}, using default of 20")
                limit = 20
                
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories/{category_id}/playlists?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Error getting category playlists for {category_id}: {str(e)}")
            return None
    
    def get_categories(self, username: str, limit: int = 20, 
                     offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gets a list of categories.
        
        Args:
            username: Username
            limit: Maximum number of categories to return
            offset: Index of the first category to return
            
        Returns:
            Categories or None
        """
        try:
            if limit < 1 or limit > 50:
                self.logger.warning(f"Invalid limit value: {limit}, using default of 20")
                limit = 20
                
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"browse/categories?limit={limit}&offset={offset}"
            )
        except Exception as e:
            self.logger.error(f"Error getting categories: {str(e)}")
            return None
    
    # -------------------------------------------------------------------------
    # 2.3. Playlist Management Methods
    # -------------------------------------------------------------------------
    # 2.3.1. Creation and Updates
    def create_playlist(self, username: str, user_id: str, name: str, 
                      public: bool = True, 
                      description: str = "") -> Optional[Dict[str, Any]]:
        """
        Creates a new playlist.
        
        Args:
            username: Username
            user_id: Spotify user ID
            name: Playlist name
            public: Whether the playlist should be public
            description: Playlist description
            
        Returns:
            Created playlist information or None
        """
        try:
            if not user_id or not name:
                self.logger.error("Missing required parameters for playlist creation")
                return None
                
            data = {
                "name": name,
                "public": public,
                "description": description
            }
            
            result = self.api_service._make_api_request(
                username=username,
                endpoint=f"users/{user_id}/playlists",
                method="POST",
                data=data
            )
            
            if result:
                self.logger.info(f"Successfully created playlist '{name}' for user {user_id}")
            
            return result
        except Exception as e:
            self.logger.error(f"Error creating playlist: {str(e)}")
            return None
    
    def update_playlist_details(self, username: str, playlist_id: str, 
                              name: Optional[str] = None, 
                              public: Optional[bool] = None, 
                              description: Optional[str] = None) -> bool:
        """
        Updates a playlist's details.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            name: New playlist name
            public: New public status
            description: New playlist description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id:
                self.logger.error("No playlist ID provided for update")
                return False
                
            data = {}
            
            if name is not None:
                data["name"] = name
                
            if public is not None:
                data["public"] = public
                
            if description is not None:
                data["description"] = description
                
            if not data:
                self.logger.info("No changes to update for playlist")
                return True  # Nothing to update
                
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}",
                method="PUT",
                data=data
            )
            
            if response is not None:
                self.logger.info(f"Successfully updated playlist {playlist_id}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error updating playlist details: {str(e)}")
            return False
    
    # 2.3.2. Following and Unfollowing
    def follow_playlist(self, username: str, playlist_id: str, 
                      public: bool = True) -> bool:
        """
        Follows a playlist.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            public: Whether to include the playlist in the user's public profile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id:
                self.logger.error("No playlist ID provided to follow")
                return False
                
            data = {
                "public": public
            }
            
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}/followers",
                method="PUT",
                data=data
            )
            
            if response is not None:
                self.logger.info(f"Successfully followed playlist {playlist_id}")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error following playlist: {str(e)}")
            return False
    
    def unfollow_playlist(self, username: str, playlist_id: str) -> bool:
        """
        Unfollows a playlist.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id:
                self.logger.error("No playlist ID provided to unfollow")
                return False
                
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}/followers",
                method="DELETE"
            )
            
            if response is not None:
                self.logger.info(f"Successfully unfollowed playlist {playlist_id}")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error unfollowing playlist: {str(e)}")
            return False
    
    # -------------------------------------------------------------------------
    # 2.4. Playlist Item Methods
    # -------------------------------------------------------------------------
    # 2.4.1. Adding Items
    def add_items_to_playlist(self, username: str, playlist_id: str, 
                            uris: List[str], 
                            position: Optional[int] = None) -> bool:
        """
        Adds tracks to a playlist.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            uris: List of Spotify track URIs
            position: Position to insert the tracks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id or not uris:
                self.logger.error("Missing required parameters for adding items to playlist")
                return False
                
            # Spotify API limits to 100 tracks per request
            if len(uris) > 100:
                self.logger.warning("More than 100 tracks provided, only the first 100 will be added")
                uris = uris[:100]
                
            data = {
                "uris": uris
            }
            
            if position is not None:
                data["position"] = position
                
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}/tracks",
                method="POST",
                data=data
            )
            
            if response is not None:
                self.logger.info(f"Successfully added {len(uris)} tracks to playlist {playlist_id}")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error adding items to playlist: {str(e)}")
            return False
    
    # 2.4.2. Removing Items
    def remove_items_from_playlist(self, username: str, playlist_id: str, 
                                 uris: List[str]) -> bool:
        """
        Removes tracks from a playlist.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            uris: List of Spotify track URIs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id or not uris:
                self.logger.error("Missing required parameters for removing items from playlist")
                return False
                
            # Format the tracks as required by the API
            tracks = [{"uri": uri} for uri in uris]
            
            data = {
                "tracks": tracks
            }
            
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}/tracks",
                method="DELETE",
                data=data
            )
            
            if response is not None:
                self.logger.info(f"Successfully removed {len(uris)} tracks from playlist {playlist_id}")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error removing items from playlist: {str(e)}")
            return False
    
    # 2.4.3. Reordering Items
    def reorder_playlist_items(self, username: str, playlist_id: str, 
                             range_start: int, insert_before: int, 
                             range_length: int = 1) -> bool:
        """
        Reorders tracks in a playlist.
        
        Args:
            username: Username
            playlist_id: Playlist ID
            range_start: Position of the first track to be reordered
            insert_before: Position where the tracks should be inserted
            range_length: Number of tracks to be reordered
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_id:
                self.logger.error("No playlist ID provided for reordering")
                return False
                
            data = {
                "range_start": range_start,
                "insert_before": insert_before,
                "range_length": range_length
            }
            
            response = self.api_service._make_api_request(
                username=username,
                endpoint=f"playlists/{playlist_id}/tracks",
                method="PUT",
                data=data
            )
            
            if response is not None:
                self.logger.info(f"Successfully reordered tracks in playlist {playlist_id}")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error reordering playlist items: {str(e)}")
            return False
    
    # -------------------------------------------------------------------------
    # 2.5. Search and Formatting Methods
    # -------------------------------------------------------------------------
    def search_items(self, username: str, query: str, item_type: str = 'track', 
                   limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Searches for items on Spotify.
        
        Args:
            username: Username
            query: Search query
            item_type: Type of item to search for (track, album, artist, playlist)
            limit: Maximum number of items to return
            
        Returns:
            Search results or None
        """
        try:
            if not query:
                self.logger.error("No search query provided")
                return None
                
            if item_type not in ['track', 'album', 'artist', 'playlist']:
                self.logger.error(f"Invalid item type: {item_type}")
                return None
                
            if limit < 1 or limit > 50:
                self.logger.warning(f"Invalid limit value: {limit}, using default of 20")
                limit = 20
                
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            return self.api_service._make_api_request(
                username=username,
                endpoint=f"search?q={encoded_query}&type={item_type}&limit={limit}"
            )
        except Exception as e:
            self.logger.error(f"Error searching for items: {str(e)}")
            return None
    
    def format_playlist_for_display(self, playlist_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats playlist data for display.
        
        Args:
            playlist_data: Raw playlist data from Spotify API
            
        Returns:
            Formatted playlist data
        """
        try:
            if not playlist_data:
                return {}
                
            # Get playlist image
            playlist_image = ""
            if "images" in playlist_data and playlist_data["images"]:
                playlist_image = playlist_data["images"][0]["url"]
                
            # Get playlist owner
            owner_name = ""
            if "owner" in playlist_data:
                owner_name = playlist_data["owner"].get("display_name", "")
                
            # Get track count
            track_count = 0
            if "tracks" in playlist_data:
                track_count = playlist_data["tracks"].get("total", 0)
                
            return {
                "id": playlist_data.get("id", ""),
                "name": playlist_data.get("name", "Unknown Playlist"),
                "description": playlist_data.get("description", ""),
                "image": playlist_image,
                "owner": owner_name,
                "track_count": track_count,
                "public": playlist_data.get("public", False),
                "external_url": playlist_data.get("external_urls", {}).get("spotify", ""),
                "uri": playlist_data.get("uri", "")
            }
        except Exception as e:
            self.logger.error(f"Error formatting playlist for display: {str(e)}")
            return {}
