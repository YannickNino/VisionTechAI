"""
Simple user authentication module for VisionTech
"""
import hashlib
import secrets
from datetime import datetime, timedelta

# Simple in-memory user store (for production, use a database)
users_db = {
    'admin': {
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'name': 'Administrateur'
    }
}

# Active sessions store
sessions = {}

def hash_password(password):
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    if username not in users_db:
        return None
    
    user = users_db[username]
    password_hash = hash_password(password)
    
    if password_hash == user['password_hash']:
        # Create session token
        token = secrets.token_urlsafe(32)
        sessions[token] = {
            'username': username,
            'name': user['name'],
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }
        return {
            'token': token,
            'username': username,
            'name': user['name']
        }
    
    return None

def validate_token(token):
    """Validate a session token"""
    if token not in sessions:
        return None
    
    session = sessions[token]
    
    # Check if token is expired
    if datetime.now() > session['expires_at']:
        del sessions[token]
        return None
    
    return session

def logout(token):
    """Logout a user by removing their session"""
    if token in sessions:
        del sessions[token]
        return True
    return False

def add_user(username, password, name):
    """Add a new user (admin function)"""
    if username in users_db:
        return False
    
    users_db[username] = {
        'password_hash': hash_password(password),
        'name': name
    }
    return True
