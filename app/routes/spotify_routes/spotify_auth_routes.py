# =============================================================================
# Spotify Auth Routes
# =============================================================================
# Contents:
# 1. Imports
# 2. Main Route Initialization Function
# 3. Authentication Routes
#    3.1. Spotify OAuth Flow Initiation
#    3.2. Spotify OAuth Callback Processing
#    3.3. Spotify Account Unlinking
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import request, redirect, url_for, session, flash
import requests
from datetime import datetime, timedelta
from app.services.spotify_services.spotify_auth_service import SpotifyAuthService
from app.models.database import SpotifyRepository
from app.services.auth_service import session_is_user_logged_in

# -----------------------------------------------------------------------------
# 2. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_spotify_auth_routes(app):
    # Initialize services
    spotify_auth_service = SpotifyAuthService()
    spotify_repo = SpotifyRepository()
    
    # -----------------------------------------------------------------------------
    # 3. Authentication Routes
    # -----------------------------------------------------------------------------
    # 3.1. Spotify OAuth Flow Initiation
    @app.route('/spotify/auth')
    def spotify_auth():
        # Check if user is logged in
        username = session_is_user_logged_in()

        if not username:
            flash("Please log in first!", "error")
            return redirect(url_for('login'))
            
        try:
            # Get Spotify credentials
            spotify_credentials = spotify_repo.spotify_get_user_data(username)
            
            # Validate client ID
            if not spotify_credentials['client_id'] or not spotify_credentials['client_secret']:
                flash("Please add your Spotify Client ID and Client Secret from your profile page first.", "error")
                return redirect(url_for('profile'))
            
            if spotify_credentials['client_id'].strip() == "":
                flash("Invalid Client ID.", "error")
                return redirect(url_for('profile'))
            
            # Generate authorization URL
            auth_url = spotify_auth_service.get_authorization_url(username)
            
            return redirect(auth_url)
            
        except Exception as e:
            flash(f"An error occurred during Spotify connection: {str(e)}", "error")
            return redirect(url_for('profile'))

    # 3.2. Spotify OAuth Callback Processing
    @app.route('/spotify/callback')
    def spotify_callback():
        # Check for errors
        error = request.args.get('error')
        if error:
            flash(f"Spotify authorization error: {error}", "error")
            print("spotify_callback error: ", error)
            return redirect(url_for('profile'))
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            flash("Failed to get Spotify authorization code!", "error")
            return redirect(url_for('profile'))
        
        try:
            # Get username from session
            username = session.get('username')
            if not username:
                flash("User session may have timed out, please log in again.", "error")
                return redirect(url_for('login'))
            
            # Get Spotify credentials
            spotify_credentials = spotify_repo.spotify_get_user_data(username)
            client_id = spotify_credentials.get('client_id')
            client_secret = spotify_credentials.get('client_secret')
            
            # Validate credentials
            if not client_id or not client_secret:
                flash("Spotify credentials are missing!", "error")
                return redirect(url_for('profile'))
            
            # Exchange code for token
            token_info = spotify_auth_service.exchange_code_for_token(code, client_id, client_secret)
            if not token_info:
                flash("Failed to get Spotify token!", "error")
                return redirect(url_for('profile'))
            
            # Extract token information
            access_token = token_info['access_token']
            refresh_token = token_info.get('refresh_token', '')
            expires_in = token_info.get('expires_in', 3600)
            
            # Store token in session
            session['access_token'] = access_token
            session['token_expires_at'] = datetime.now() + timedelta(seconds=expires_in)
            
            # Get user profile information
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
            
            if user_response.status_code != 200:
                flash("Failed to get Spotify user information!", "error")
                return redirect(url_for('profile'))
            
            # Extract user information
            spotify_user = user_response.json()
            spotify_user_id = spotify_user.get('id')
            
            # Update user information
            spotify_auth_service.save_spotify_user_info(
                username=username,
                spotify_user_id=spotify_user_id,
                refresh_token=refresh_token,
            )
            
            flash("Spotify account connected successfully!", "success")
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash(f"An error occurred during Spotify connection: {str(e)}", "error")
            return redirect(url_for('profile'))

    # 3.3. Spotify Account Unlinking
    @app.route('/spotify/unlink')
    def spotify_unlink():
        # Check if user is logged in
        if not session.get('logged_in'):
            flash("Please log in first!", "error")
            return redirect(url_for('login'))
        
        # Get username from session
        username = session.get('username')
        
        try:
            # Unlink account
            success = spotify_auth_service.unlink_spotify_account(username)
            
            if success:
                flash("Spotify account unlinked successfully!", "success")
            else:
                flash("Failed to unlink Spotify account!", "error")
                
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash(f"An error occurred during Spotify unlinking: {str(e)}", "error")
            return redirect(url_for('profile'))