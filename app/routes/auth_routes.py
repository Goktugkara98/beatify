# =============================================================================
# Authentication Routes Module
# =============================================================================
# Contents:
# 1. Imports
# 2. Main Route Initialization Function
# 3. Authentication Routes
#    3.1. User Registration
#    3.2. User Login
#    3.3. User Logout
#    3.4. Password Reset (Future Implementation)
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import render_template, request, redirect, url_for, flash, session
from app.services import auth_service

# -----------------------------------------------------------------------------
# 2. Main Route Initialization Function
# -----------------------------------------------------------------------------
def init_auth_routes(app):
    # -----------------------------------------------------------------------------
    # 3. Authentication Routes
    # -----------------------------------------------------------------------------
    # 3.1. User Registration
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Redirect if already logged in
        if auth_service.session_is_user_logged_in():
            return redirect(url_for('profile'))
            
        # Handle form submission
        if request.method == 'POST':
            # Extract form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
                
            # Basic validation
            if not all([username, email, password]):
                flash('Please fill in all fields.', 'danger')
                return render_template('auth/register.html')
                
            # Password validation
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return render_template('auth/register.html')
                          
            try:
                # Register new user
                auth_service.beatify_register(username, email, password)
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'An error occurred during registration: {str(e)}', 'danger')
                return render_template('auth/register.html')
            
        # GET request - display registration form
        return render_template('auth/register.html')
    
    # 3.2. User Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Redirect if already logged in
        if auth_service.session_is_user_logged_in():
            return redirect(url_for('profile'))
            
        # Handle form submission
        if request.method == 'POST':
            # Extract form data
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember') == 'on'
                
            # Basic validation
            if not all([username, password]):
                flash('Please enter both username and password.', 'danger')
                return render_template('auth/login.html')
                
            try:
                # Authenticate user
                response = auth_service.beatify_log_in(username, password, remember_me)
                flash('You have successfully logged in.', 'success')
                
                # Return response if it exists (for remember_me cookie)
                if response:
                    return response
                return redirect(url_for('homepage'))
            except Exception as e:
                flash(f'An error occurred during login: {str(e)}', 'danger')
                return render_template('auth/login.html')
            
        # GET request - display login form
        return render_template('auth/login.html')
    
    # 3.3. User Logout
    @app.route('/logout')
    def logout():
        # Redirect if not logged in
        username = auth_service.session_is_user_logged_in()
        if not username:
            return redirect(url_for('homepage'))
                
        try:
            # End user session
            auth_service.beatify_log_out(username)
            flash('You have successfully logged out.', 'success')
            return redirect(url_for('homepage'))
        except Exception as e:
            # Clear session manually if service fails
            session.clear()
            flash('You have been logged out.', 'success')
            return redirect(url_for('homepage'))
    
    # 3.4. Password Reset (Future Implementation)
    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        # Future implementation
        return render_template('auth/reset_password.html')
