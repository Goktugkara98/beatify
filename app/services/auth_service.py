# =============================================================================
# Authentication Service Module
# =============================================================================
# Contents:
# 1. Imports
# 2. User Authentication
#    2.1. User Registration
#    2.2. User Login
#    2.3. User Logout
#    2.4. Password Verification
# 3. Session Management
#    3.1. Session Creation
#    3.2. Session Verification
#    3.3. Session Termination
# 4. Token Management
#    4.1. Token Creation
#    4.2. Token Validation
# 5. Security
#    5.1. HTTPS Redirection
#    5.2. Authentication Decorators
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------
from flask import session, request, redirect, url_for, flash, make_response
from app.models.database import UserRepository
from app.config import DEBUG
from functools import wraps
from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from secrets import token_hex

# -----------------------------------------------------------------------------
# 2. User Management
# -----------------------------------------------------------------------------
# 2.1. User Registration
def beatify_register(username, email, password):
    user_repo = UserRepository()
    existing = user_repo.beatify_get_username_or_email_data(username, email)
    
    if existing:
        if existing[0] == username and existing[1] == email:
            flash('This username and email are already in use.', 'danger')
            return None
        elif existing[0] == username:
            flash('This username is already in use.', 'danger')
            return None
        elif existing[1] == email:
            flash('This email is already in use.', 'danger')
            return None
            
    user_repo.beatify_insert_new_user_data(username, email, generate_password_hash(password))
    flash('Registration successful! You can now log in.', 'success')
    return None

# 2.2. User Login
def beatify_log_in(username, password, remember_me):
    user_repo = UserRepository()
    database_password_hash = user_repo.beatify_get_password_hash_data(username)
    
    if not database_password_hash:
        flash('Invalid username or password.', 'danger')
        return None
        
    if beatify_check_user_password(username, password):
        session_log_in(username)
        if remember_me:
            return beatify_create_auth_token(username)
        return None
    else:
        flash('Invalid username or password.', 'danger')
        return None

# 2.3. User Logout
def beatify_log_out(username):
    auth_token = request.cookies.get('auth_token')
    if auth_token:
        user_repo = UserRepository()
        user_repo.beatify_deactivate_auth_token(username, auth_token)
    session.clear()

# 2.4. Password Verification
def beatify_check_user_password(username, password):
    user_repo = UserRepository()
    password_hash = user_repo.beatify_get_password_hash_data(username)
    
    if not password_hash:
        return False
        
    return check_password_hash(password_hash, password)

# -----------------------------------------------------------------------------
# 3. Session Management
# -----------------------------------------------------------------------------
# 3.1. Session Creation
def session_log_in(username):
    session['logged_in'] = True
    session['username'] = username
    
    user_repo = UserRepository()
    user_data = user_repo.beatify_get_user_data(username)
    
    if user_data and 'id' in user_data:
        session['user_id'] = user_data['id']

# 3.2. Session Verification
def session_is_user_logged_in():
    if session.get('logged_in') and session.get('username'):
        return session.get('username')
    return None

# 3.3. Session Termination
def session_log_out(username):
    auth_token = request.cookies.get('auth_token')
    if auth_token:
        user_repo = UserRepository()
        user_repo.beatify_deactivate_auth_token(username, auth_token)
    session.clear()

# -----------------------------------------------------------------------------
# 4. Token Management
# -----------------------------------------------------------------------------
# 4.1. Token Creation
def beatify_create_auth_token(username):
    token = token_hex(32)
    expires_at = datetime.now() + timedelta(days=30)
    
    user_repo = UserRepository()
    user_repo.beatify_insert_or_update_auth_token(username, token, expires_at)
    
    response = make_response(redirect(url_for('profile')))
    response.set_cookie(
        'auth_token', 
        token, 
        expires=expires_at, 
        httponly=True, 
        secure=not DEBUG,  
        samesite='Lax'
    )
    return response

# 4.2. Token Validation
def beatify_validate_auth_token(token):
    if not token:
        return None
        
    user_repo = UserRepository()
    return user_repo.beatify_validate_auth_token(token)

# -----------------------------------------------------------------------------
# 5. Security
# -----------------------------------------------------------------------------
# 5.1. HTTPS Redirection
def redirect_to_https(request):
    if DEBUG:
        return None
    if request.is_secure:
        return None
    if request.headers.get('X-Forwarded-Proto') == 'https':
        return None
        
    url = request.url.replace('http://', 'https://', 1)
    return redirect(url)

# 5.2. Authentication Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session_is_user_logged_in():
            return f(*args, **kwargs)
            
        auth_token = request.cookies.get('auth_token')
        if auth_token:
            username = beatify_validate_auth_token(auth_token)
            if username:
                session_log_in(username)
                return f(*args, **kwargs)
                
        flash('You must be logged in to view this page.', 'warning')
        return redirect(url_for('login'))
    return decorated_function
