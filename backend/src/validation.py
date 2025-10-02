"""
Input validation module for the secure web application.
Provides comprehensive validation functions for user inputs.
"""

import re
from typing import Dict, List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format and constraints.
    
    Args:
        username: The username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "El nombre de usuario es requerido"
    
    # Strip whitespace
    username = username.strip()
    
    if not username:
        return False, "El nombre de usuario es requerido"
    
    # Length validation
    if len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    
    if len(username) > 50:
        return False, "El nombre de usuario no puede tener más de 50 caracteres"
    
    # Format validation - only alphanumeric and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números y guiones bajos"
    
    # Must start with letter or number (not underscore)
    if username.startswith('_'):
        return False, "El nombre de usuario debe comenzar con una letra o número"
    
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength requirements.
    
    Args:
        password: The password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "La contraseña es requerida"
    
    # Length validation
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña no puede tener más de 128 caracteres"
    
    # Strength requirements
    requirements = []
    
    if not re.search(r'[a-z]', password):
        requirements.append("una letra minúscula")
    
    if not re.search(r'[A-Z]', password):
        requirements.append("una letra mayúscula")
    
    if not re.search(r'\d', password):
        requirements.append("un número")
    
    if requirements:
        return False, f"La contraseña debe contener al menos: {', '.join(requirements)}"
    
    return True, None


def validate_data_input(data: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user data input.
    
    Args:
        data: The data to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "Los datos son requeridos"
    
    # Strip whitespace
    data = data.strip()
    
    if not data:
        return False, "Los datos son requeridos"
    
    # Length validation (10KB limit)
    if len(data) > 10000:
        return False, "Los datos son demasiado largos (máximo 10KB)"
    
    # Check for potentially dangerous content (basic XSS prevention)
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            return False, "Los datos contienen contenido no permitido"
    
    return True, None


def sanitize_input(input_str: str) -> str:
    """
    Sanitize input string by removing dangerous characters.
    
    Args:
        input_str: The string to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_form_data(form_data: Dict[str, str], required_fields: List[str]) -> Dict[str, str]:
    """
    Validate form data and return validation errors.
    
    Args:
        form_data: Dictionary of form field values
        required_fields: List of required field names
        
    Returns:
        Dictionary of field_name -> error_message for any validation errors
    """
    errors = {}
    
    # Check required fields
    for field in required_fields:
        if field not in form_data or not form_data[field].strip():
            errors[field] = f"El campo {field} es requerido"
    
    # Validate specific fields
    if 'username' in form_data:
        is_valid, error = validate_username(form_data['username'])
        if not is_valid:
            errors['username'] = error
    
    if 'password' in form_data:
        is_valid, error = validate_password(form_data['password'])
        if not is_valid:
            errors['password'] = error
    
    if 'data' in form_data:
        is_valid, error = validate_data_input(form_data['data'])
        if not is_valid:
            errors['data'] = error
    
    return errors


def is_safe_redirect_url(url: str) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect attacks).
    
    Args:
        url: The URL to check
        
    Returns:
        True if the URL is safe for redirect
    """
    if not url:
        return False
    
    # Only allow relative URLs that don't start with //
    if url.startswith('/') and not url.startswith('//'):
        return True
    
    # Reject protocol-relative URLs (//example.com)
    if url.startswith('//'):
        return False
    
    # Reject absolute URLs, javascript:, data:, etc.
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
        return False
    
    return True