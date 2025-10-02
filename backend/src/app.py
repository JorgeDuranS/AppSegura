import json
import os
import sqlite3
import logging
import secrets

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_wtf.csrf import CSRFProtect, validate_csrf
from werkzeug.security import (
    generate_password_hash as generate_phash,
    check_password_hash as check_phash
)

from crypto import (
    read_secret_key,
    encrypt_data,
    decrypt_data
)
from database import (
    init_database,
    get_db_connection,
    create_user,
    get_user_password,
    save_user_data,
    get_user_data,
    user_exists,
    DatabaseError
)
from validation import (
    validate_username,
    validate_password,
    validate_data_input,
    sanitize_input,
    validate_form_data,
    is_safe_redirect_url
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import config

# Declaración de la aplicación Flask
app = Flask(__name__,
    template_folder=config.TEMPLATE_FOLDER,
    static_folder=config.STATIC_FOLDER,
    static_url_path='/static/',
)

# Configure Flask with security settings
app.config.update(config.get_flask_config())

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Login attempt tracking (in production, use Redis or database)
login_attempts = {}

# Initialize database on startup
try:
    init_database()
    logger.info("Database initialized successfully")
except DatabaseError as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Initialize encryption key with robust error handling
try:
    key_path = os.path.join(os.path.dirname(__file__), '.secret.key')
    fernet_key = read_secret_key(key_path)
    logger.info("Encryption key initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize encryption key: {e}")
    logger.info("Attempting to create new encryption key...")
    try:
        # Try alternative path in case of permission issues
        alt_key_path = os.path.join(os.path.dirname(__file__), '..', '.secret.key')
        fernet_key = read_secret_key(alt_key_path)
        logger.info("Encryption key initialized successfully with alternative path")
    except Exception as e2:
        logger.critical(f"Failed to initialize encryption key with both paths: {e2}")
        raise Exception("Cannot initialize application without encryption key")


def get_client_ip():
    """Get client IP address for rate limiting"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']


def is_rate_limited(ip_address: str) -> bool:
    """
    Check if IP address is rate limited for login attempts.
    
    Args:
        ip_address: Client IP address
        
    Returns:
        True if rate limited, False otherwise
    """
    import time
    
    current_time = time.time()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    
    # Clean old attempts outside the window
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if current_time - attempt_time < config.LOGIN_ATTEMPT_WINDOW
    ]
    
    # Check if exceeded max attempts
    return len(login_attempts[ip_address]) >= config.MAX_LOGIN_ATTEMPTS


def record_login_attempt(ip_address: str):
    """Record a failed login attempt"""
    import time
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    
    login_attempts[ip_address].append(time.time())


def clear_login_attempts(ip_address: str):
    """Clear login attempts for successful login"""
    if ip_address in login_attempts:
        del login_attempts[ip_address]


@app.route('/', methods=['GET'])
def index():
    # Redirect authenticated users to data page
    if 'username' in session:
        return redirect(url_for('data_page'))
    return render_template('html/index.html')


@app.route('/data', methods=['GET'])
def data_page():
    """Serve the data management page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('data.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """Handle user logout"""
    try:
        # For POST requests, validate CSRF token
        if request.method == 'POST':
            csrf_token = request.form.get('csrf_token') or request.json.get('csrf_token') if request.is_json else None
            if csrf_token:
                validate_csrf(csrf_token)
        
        username = session.get('username')
        if username:
            logger.info(f"User logged out: {username}")
        
        # Clear session completely and invalidate
        session.clear()
        
        # Handle different request types
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': 'Sesión cerrada correctamente', 'redirect': '/'}), 200
        else:
            # For form submissions, redirect directly
            return redirect(url_for('index'))
        
    except Exception as e:
        if "CSRF" in str(e):
            logger.warning(f"CSRF token validation failed for logout attempt")
            if request.is_json:
                return jsonify({'error': 'Token de seguridad inválido'}), 400
            else:
                return redirect(url_for('index'))
        
        logger.error(f"Unexpected error during logout: {e}")
        if request.is_json:
            return jsonify({'error': 'Error interno del servidor'}), 500
        else:
            return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    client_ip = get_client_ip()
    
    try:
        # Check rate limiting
        if is_rate_limited(client_ip):
            logger.warning(f"Rate limited login attempt from IP: {client_ip}")
            return jsonify({
                'error': 'Demasiados intentos de inicio de sesión. Intenta de nuevo en 15 minutos.',
                'field': 'username'
            }), 429
        
        # Validate CSRF token
        validate_csrf(request.form.get('csrf_token'))
        
        # Sanitize and validate input data
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        # Validate username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            logger.warning(f"Login attempt with invalid username format: {username}")
            record_login_attempt(client_ip)
            return jsonify({'error': error_msg, 'field': 'username'}), 400
        
        # Validate password (basic check)
        if not password:
            logger.warning(f"Login attempt with empty password for user: {username}")
            record_login_attempt(client_ip)
            return jsonify({'error': 'La contraseña es requerida', 'field': 'password'}), 400
        
        if len(password) > 128:  # Prevent extremely long passwords
            logger.warning(f"Login attempt with overly long password for user: {username}")
            record_login_attempt(client_ip)
            return jsonify({'error': 'Contraseña demasiado larga', 'field': 'password'}), 400
        
        # Get user password hash from database
        user_password_hash = get_user_password(username)
        
        # Handle case when user doesn't exist
        if user_password_hash is None:
            logger.warning(f"Login attempt for non-existent user: {username}")
            record_login_attempt(client_ip)
            return jsonify({'error': 'Usuario o contraseña incorrectos', 'field': 'username'}), 401
        
        # Verify password
        if check_phash(user_password_hash, password):
            # Successful login
            clear_login_attempts(client_ip)
            
            # Clear existing session data and regenerate session ID for security (prevent session fixation)
            session.clear()
            
            session['username'] = username
            session.permanent = True  # Enable session timeout
            logger.info(f"Successful login for user: {username}")
            return jsonify({
                'success': True, 
                'message': 'Inicio de sesión exitoso',
                'redirect': '/data'
            }), 200
        else:
            logger.warning(f"Failed login attempt for user: {username} - incorrect password")
            record_login_attempt(client_ip)
            return jsonify({'error': 'Usuario o contraseña incorrectos', 'field': 'username'}), 401
            
    except Exception as e:
        if "CSRF" in str(e):
            logger.warning(f"CSRF token validation failed for login attempt")
            return jsonify({'error': 'Token de seguridad inválido. Recarga la página.', 'field': 'username'}), 400
        
        logger.error(f"Unexpected error during login: {e}")
        return jsonify({'error': 'Error interno del servidor', 'field': 'username'}), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        # Validate CSRF token
        validate_csrf(request.form.get('csrf_token'))
        
        # Sanitize and validate input data
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm-password', '')
        
        # Validate username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            logger.warning(f"Registration attempt with invalid username: {username}")
            return jsonify({'error': error_msg, 'field': 'username'}), 400
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Registration attempt with weak password for user: {username}")
            return jsonify({'error': error_msg, 'field': 'password'}), 400
        
        # Validate password confirmation
        if password != confirm_password:
            return jsonify({'error': 'Las contraseñas no coinciden', 'field': 'confirm-password'}), 400
        
        # Check if terms are accepted (if provided)
        terms_accepted = request.form.get('terms') == 'on'
        if not terms_accepted:
            return jsonify({'error': 'Debes aceptar los términos de servicio', 'field': 'terms'}), 400
        
        # Generate password hash
        password_hash = generate_phash(password)
        
        # Attempt to create user
        create_user(username, password_hash)
        
        logger.info(f"User registered successfully: {username}")
        return jsonify({
            'success': True,
            'message': 'Usuario registrado con éxito',
            'redirect': '/login'
        }), 201
        
    except Exception as e:
        if "CSRF" in str(e):
            logger.warning(f"CSRF token validation failed for registration attempt")
            return jsonify({'error': 'Token de seguridad inválido. Recarga la página.', 'field': 'username'}), 400
        
        if "already exists" in str(e) or "UNIQUE constraint failed" in str(e):
            logger.warning(f"Registration attempt for existing user: {username}")
            return jsonify({'error': 'El nombre de usuario ya está en uso', 'field': 'username'}), 409
        
        logger.error(f"Unexpected error during registration: {e}")
        return jsonify({'error': 'Error interno del servidor', 'field': 'username'}), 500


@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    # Check authentication first
    if 'username' not in session:
        logger.warning("Unauthenticated access attempt to /api/data")
        return jsonify({'error': 'Usuario no autenticado'}), 401
    
    username = session['username']
    
    if request.method == 'GET':
        return get_user_data_route(username)
    elif request.method == 'POST':
        return save_user_data_route(username)


def get_user_data_route(username: str):
    """Handle GET requests for user data"""
    try:
        # Get encrypted data from database
        encrypted_data = get_user_data(username)
        
        # Handle case when no data exists for user
        if encrypted_data is None:
            logger.info(f"No data found for user: {username}")
            return jsonify({'success': True, 'data': None, 'message': 'El usuario no tiene datos guardados'}), 200
        
        # Decrypt data
        decrypted_data = decrypt_data(encrypted_data, fernet_key)
        
        logger.info(f"Data retrieved successfully for user: {username}")
        return jsonify({'success': True, 'data': decrypted_data}), 200
        
    except DatabaseError as e:
        logger.error(f"Database error retrieving data for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving data for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


def save_user_data_route(username: str):
    """Handle POST requests for saving user data"""
    try:
        # Validate CSRF token
        validate_csrf(request.form.get('csrf_token'))
        
        # Get and sanitize data from request
        data = sanitize_input(request.form.get('data', ''))
        
        # Validate data input
        is_valid, error_msg = validate_data_input(data)
        if not is_valid:
            logger.warning(f"Invalid data input for user {username}: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Encrypt data
        encrypted_data = encrypt_data(data, fernet_key)
        
        # Save to database (handles both insert and update)
        save_user_data(username, encrypted_data)
        
        logger.info(f"Data saved successfully for user: {username}")
        return jsonify({'success': True, 'message': 'Datos guardados con éxito'}), 200
        
    except Exception as e:
        if "CSRF" in str(e):
            logger.warning(f"CSRF token validation failed for data save attempt by user: {username}")
            return jsonify({'error': 'Token de seguridad inválido. Recarga la página.'}), 400
        
        logger.error(f"Unexpected error saving data for user {username}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@app.before_request
def check_session_timeout():
    """Check if session has expired and clear it if necessary"""
    if 'username' in session:
        # Flask automatically handles session timeout with PERMANENT_SESSION_LIFETIME
        # But we can add additional checks here if needed
        pass


@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    if not config.DEBUG:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    
    return response


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('html/index.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    app.run(debug=config.DEBUG, host='127.0.0.1', port=5000)