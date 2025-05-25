# =============================================================================
# Spotify Widget Routes
# =============================================================================
# Contents:
# 1. Imports
# 2. Blueprint Definition
# 3. Route Definitions
#    3.1. Widget Rendering
#    3.2. Widget Data API
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import Blueprint, render_template, request, jsonify, session, url_for
from app.services.spotify_services.spotify_api_service import SpotifyApiService

# -----------------------------------------------------------------------------
# 2. Blueprint Definition
# -----------------------------------------------------------------------------
spotify_widget_routes = Blueprint('spotify_widget_routes', __name__)

# -----------------------------------------------------------------------------
# 3. Route Definitions
# -----------------------------------------------------------------------------


#3.0 Widget Manager

@spotify_widget_routes.route('/widget-manager')
def widget_manager():
    return render_template('spotify/widget-manager.html')

# 3.1. Widget Rendering
@spotify_widget_routes.route('/widget/<widget_token>')
def spotify_widget(widget_token):
    try:
        # For now, we're using a fixed token "abcd" for testing purposes
        if widget_token == 'abcd':
            # Default widget config for testing
            widget_config = {
                'type': request.args.get('type', 'now-playing'),
                'background_color': '#121212',
                'text_color': '#ffffff',
                'accent_color': '#1DB954',
                'font_size': 'medium',
                # Veri API'sinin URL'sini temaya iletiyoruz
                'dataEndpoint': url_for('spotify_widget_routes.widget_data', widget_token=widget_token, _external=True)
            }
            
            # Determine which template to use based on widget type
            template = f"spotify/widgets/{widget_config['type']}.html"
            
            return render_template(template, config=widget_config)
        else:
            # Invalid token
            return "Invalid widget token", 404
    except Exception:
        return "An error occurred while rendering the widget", 500

# 3.2. Widget Data API
@spotify_widget_routes.route('/api/widget-data/<widget_token>')
def widget_data(widget_token):

    try:
        # DEBUG: Log the widget token
        print(f"DEBUG: Widget data requested for token: {widget_token}")
        
        # For now, we're using a fixed token "abcd" for testing purposes
        if widget_token != 'abcd':
            print(f"DEBUG: Invalid widget token: {widget_token}")
            return jsonify({"error": "Invalid widget token"}), 404
        
        # Use the SpotifyApiService to fetch real data
        # without checking for token in session
        spotify_service = SpotifyApiService()
        print(f"DEBUG: Calling spotify_service.get_currently_playing(None)")
        
        # Mock data for testing
        mock_data = {
            "is_playing": True,
            "item": {
                "name": "Shape of You",
                "artists": [{"name": "Ed Sheeran"}],
                "album": {
                    "images": [{"url": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96"}]
                },
                "duration_ms": 180000
            },
            "progress_ms": 30000
        }
        
        # Try to get real data, use mock data if it fails
        try:
            # When token system is implemented, use it here
            playback_data = spotify_service.get_currently_playing("serseriyim1")
            print(f"DEBUG: Real playback data received: {playback_data}")
            if not playback_data:
                print("DEBUG: No real data available, using mock data")
                playback_data = mock_data
        except Exception as e:
            print(f"DEBUG: Error getting real data: {str(e)}, using mock data")
            playback_data = mock_data
        
        # DEBUG: Log the playback data
        print(f"DEBUG: Final playback data: {playback_data}")
        
        # Format the response data
        if playback_data and "item" in playback_data:
            response_data = {
                "is_playing": playback_data.get("is_playing", False),
                "track_name": playback_data.get("item", {}).get("name", "Unknown"),
                "artist_name": playback_data.get("item", {}).get("artists", [{}])[0].get("name", "Unknown"),
                "album_image": playback_data.get("item", {}).get("album", {}).get("images", [{}])[0].get("url", ""),
                "progress_ms": playback_data.get("progress_ms", 0),
                "duration_ms": playback_data.get("item", {}).get("duration_ms", 0),
                "source": "Spotify"
            }
            print(f"DEBUG: Returning response data: {response_data}")
            return jsonify(response_data)
        else:
            # Return not playing data
            print("DEBUG: No playback data or item not found, returning not playing data")
            not_playing_data = {
                "is_playing": False,
                "track_name": "Not Playing",
                "artist_name": "No track is currently playing",
                "album_image": "",
                "progress_ms": 0,
                "duration_ms": 0,
                "source": "Spotify"
            }
            return jsonify(not_playing_data)
    except Exception as e:
        print(f"ERROR: Exception in widget_data: {str(e)}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to get widget data"}), 500

# -----------------------------------------------------------------------------
# 4. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_spotify_widget_routes(app):
    """
    Initialize and register all Spotify widget routes with the Flask application.
    
    Args:
        app: The Flask application instance
    
    Returns:
        None
    """
    app.register_blueprint(spotify_widget_routes, url_prefix='/spotify')