# =============================================================================
# Main Routes Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Main Route Initialization Function
# 3. Routes
#    3.1. Homepage Routes
#    3.2. Profile Management
#       3.2.1. GET Request Handling
#       3.2.2. POST Request Handling
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import render_template, request, redirect, url_for, session, flash
from app.database.models.database import UserRepository, SpotifyRepository
from app.services.auth_service import session_is_user_logged_in
from app.services.spotify_services.spotify_service import update_client_id_and_secret_data
from app.services.profile_services import handle_get_request

# -----------------------------------------------------------------------------
# 2. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_main_routes(app):
    # -----------------------------------------------------------------------------
    # 3. Routes
    # -----------------------------------------------------------------------------
    # 3.1. Homepage Routes
    @app.route('/')
    def index():
        return render_template('homepage.html')
        
    @app.route('/homepage')
    def homepage():
        return render_template('homepage.html')

    # 3.2. Profile Management
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        # Check if user is logged in
        username = session_is_user_logged_in()
        if not username:
            flash("Please log in to access your profile.", "warning")
            return redirect(url_for('login'))
            
        # Initialize repositories
        user_repo = UserRepository()
        spotify_repo = SpotifyRepository()
        
        # 3.2.1. GET Request Handling
        if request.method == 'GET':
            try:
                user_data, spotify_credentials, spotify_data = handle_get_request(username)
                
                return render_template('profile.html', 
                                     user_data=user_data, 
                                     spotify_credentials=spotify_credentials, 
                                     spotify_data=spotify_data)
                
            except Exception as e:
                flash(f"Database error: {str(e)}", "danger")
                return redirect(url_for('index'))
        
        # 3.2.2. POST Request Handling
        # Handle Spotify credential update
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
            
        try:
            # Validate inputs
            if not client_id or not client_secret:
                flash("Both Client ID and Client Secret are required.", "warning")
                return redirect(url_for('profile'))
                
            # Add or update Spotify client information
            if spotify_repo.spotify_insert_or_update_client_info(username, client_id, client_secret):
                flash('Spotify information successfully updated.', 'success')
            else:
                flash('Failed to update Spotify information.', 'danger')
                
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f"Error updating Spotify credentials: {str(e)}", "danger")
            return redirect(url_for('profile'))
