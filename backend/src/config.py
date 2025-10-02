"""
Configuration module for the secure web application.
Handles secure configuration management and environment variables.
"""

import os
import secrets
from datetime import timedelta
from typing import Dict, Any


class Config:
    """Application configuration class"""
    
    def __init__(self):
        self.SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), '..', '.secret.key')
        self.DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')
        
        # Load environment variables
        self.TEMPLATE_FOLDER = os.environ.get('TEMPLATE_FOLDER', 
                                            os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'templates'))
        self.STATIC_FOLDER = os.environ.get('STATIC_FOLDER',
                                          os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'static'))
        
        # Security settings
        self.SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour default
        self.MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
        self.LOGIN_ATTEMPT_WINDOW = int(os.environ.get('LOGIN_ATTEMPT_WINDOW', 900))  # 15 minutes
        
        # Session security settings
        self.SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'secure_session')
        self.SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)  # None for localhost
        
        # Development/Production settings
        self.DEBUG = True  # Enable debug mode temporarily
        self.TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
        
    def get_secret_key(self) -> bytes:
        """
        Get or generate the application secret key.
        
        Returns:
            Secret key as bytes
        """
        try:
            with open(self.SECRET_KEY_FILE, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new secret key if file doesn't exist
            secret_key = secrets.token_bytes(32)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.SECRET_KEY_FILE), exist_ok=True)
            
            # Write secret key to file with secure permissions
            with open(self.SECRET_KEY_FILE, 'wb') as f:
                f.write(secret_key)
            
            # Set secure file permissions (owner read/write only)
            if os.name != 'nt':  # Not Windows
                os.chmod(self.SECRET_KEY_FILE, 0o600)
            
            return secret_key
    
    def get_flask_config(self) -> Dict[str, Any]:
        """
        Get Flask configuration dictionary.
        
        Returns:
            Dictionary of Flask configuration options
        """
        return {
            'SECRET_KEY': self.get_secret_key(),
            'SESSION_COOKIE_NAME': self.SESSION_COOKIE_NAME,
            'SESSION_COOKIE_SECURE': not self.DEBUG,  # HTTPS only in production
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'SESSION_COOKIE_DOMAIN': self.SESSION_COOKIE_DOMAIN,
            'PERMANENT_SESSION_LIFETIME': timedelta(seconds=self.SESSION_TIMEOUT),
            'SESSION_REFRESH_EACH_REQUEST': True,  # Refresh session on each request
            'WTF_CSRF_TIME_LIMIT': self.SESSION_TIMEOUT,
            'WTF_CSRF_SSL_STRICT': not self.DEBUG,
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file upload
        }


# Global configuration instance
config = Config()