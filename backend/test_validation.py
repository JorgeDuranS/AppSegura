#!/usr/bin/env python3
"""
Simple test script to verify validation and security features.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from validation import (
    validate_username,
    validate_password,
    validate_data_input,
    sanitize_input,
    validate_form_data,
    is_safe_redirect_url
)


def test_username_validation():
    """Test username validation"""
    print("Testing username validation...")
    
    # Valid usernames
    valid_usernames = ['user123', 'test_user', 'admin', 'user_123']
    for username in valid_usernames:
        is_valid, error = validate_username(username)
        assert is_valid, f"Username '{username}' should be valid but got error: {error}"
    
    # Invalid usernames
    invalid_cases = [
        ('', 'El nombre de usuario es requerido'),
        ('ab', 'El nombre de usuario debe tener al menos 3 caracteres'),
        ('a' * 51, 'El nombre de usuario no puede tener más de 50 caracteres'),
        ('user@123', 'El nombre de usuario solo puede contener letras, números y guiones bajos'),
        ('_user', 'El nombre de usuario debe comenzar con una letra o número'),
        ('user-123', 'El nombre de usuario solo puede contener letras, números y guiones bajos'),
    ]
    
    for username, expected_error in invalid_cases:
        is_valid, error = validate_username(username)
        assert not is_valid, f"Username '{username}' should be invalid"
        assert expected_error in error, f"Expected error containing '{expected_error}' but got '{error}'"
    
    print("✓ Username validation tests passed")


def test_password_validation():
    """Test password validation"""
    print("Testing password validation...")
    
    # Valid passwords
    valid_passwords = ['Password123', 'MySecure1', 'Test123A']
    for password in valid_passwords:
        is_valid, error = validate_password(password)
        assert is_valid, f"Password '{password}' should be valid but got error: {error}"
    
    # Invalid passwords
    invalid_cases = [
        ('', 'La contraseña es requerida'),
        ('short', 'La contraseña debe tener al menos 8 caracteres'),
        ('a' * 129, 'La contraseña no puede tener más de 128 caracteres'),
        ('password123', 'una letra mayúscula'),
        ('PASSWORD123', 'una letra minúscula'),
        ('PasswordABC', 'un número'),
    ]
    
    for password, expected_error in invalid_cases:
        is_valid, error = validate_password(password)
        assert not is_valid, f"Password '{password}' should be invalid"
        assert expected_error in error, f"Expected error containing '{expected_error}' but got '{error}'"
    
    print("✓ Password validation tests passed")


def test_data_validation():
    """Test data input validation"""
    print("Testing data input validation...")
    
    # Valid data
    valid_data = ['Hello world', 'Some important data', 'A' * 1000]
    for data in valid_data:
        is_valid, error = validate_data_input(data)
        assert is_valid, f"Data '{data[:20]}...' should be valid but got error: {error}"
    
    # Invalid data
    invalid_cases = [
        ('', 'Los datos son requeridos'),
        ('   ', 'Los datos son requeridos'),
        ('A' * 10001, 'Los datos son demasiado largos'),
        ('<script>alert("xss")</script>', 'Los datos contienen contenido no permitido'),
        ('javascript:alert(1)', 'Los datos contienen contenido no permitido'),
    ]
    
    for data, expected_error in invalid_cases:
        is_valid, error = validate_data_input(data)
        assert not is_valid, f"Data '{data[:20]}...' should be invalid"
        assert expected_error in error, f"Expected error containing '{expected_error}' but got '{error}'"
    
    print("✓ Data validation tests passed")


def test_sanitize_input():
    """Test input sanitization"""
    print("Testing input sanitization...")
    
    test_cases = [
        ('  hello world  ', 'hello world'),
        ('test\x00data', 'testdata'),
        ('normal text', 'normal text'),
        ('', ''),
    ]
    
    for input_str, expected in test_cases:
        result = sanitize_input(input_str)
        assert result == expected, f"Expected '{expected}' but got '{result}'"
    
    print("✓ Input sanitization tests passed")


def test_safe_redirect():
    """Test safe redirect URL validation"""
    print("Testing safe redirect URL validation...")
    
    safe_urls = ['/login', '/data', '/register', '/']
    for url in safe_urls:
        assert is_safe_redirect_url(url), f"URL '{url}' should be safe"
    
    unsafe_urls = [
        'http://evil.com',
        'javascript:alert(1)',
        '//evil.com',
        'data:text/html,<script>alert(1)</script>',
        'ftp://example.com'
    ]
    
    for url in unsafe_urls:
        assert not is_safe_redirect_url(url), f"URL '{url}' should be unsafe"
    
    print("✓ Safe redirect URL tests passed")


def test_form_validation():
    """Test form data validation"""
    print("Testing form data validation...")
    
    # Valid form data
    valid_form = {
        'username': 'testuser',
        'password': 'Password123',
        'data': 'Some test data'
    }
    
    errors = validate_form_data(valid_form, ['username', 'password'])
    assert len(errors) == 0, f"Valid form should have no errors but got: {errors}"
    
    # Invalid form data
    invalid_form = {
        'username': 'ab',  # too short
        'password': 'weak',  # too weak
        'data': '<script>alert(1)</script>'  # dangerous content
    }
    
    errors = validate_form_data(invalid_form, ['username', 'password', 'data'])
    assert len(errors) == 3, f"Expected 3 errors but got {len(errors)}: {errors}"
    
    print("✓ Form validation tests passed")


if __name__ == '__main__':
    print("Running validation and security tests...\n")
    
    try:
        test_username_validation()
        test_password_validation()
        test_data_validation()
        test_sanitize_input()
        test_safe_redirect()
        test_form_validation()
        
        print("\n🎉 All tests passed! Validation and security features are working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)