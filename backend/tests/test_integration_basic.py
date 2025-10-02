"""
Basic integration tests for API endpoints
Tests core functionality without CSRF complications
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import (
    init_database, create_user, get_user_password, 
    save_user_data, get_user_data, user_exists
)
from crypto import read_secret_key, encrypt_data, decrypt_data
from validation import validate_username, validate_password, validate_data_input
from werkzeug.security import generate_password_hash, check_password_hash


class TestCompleteUserFlow(unittest.TestCase):
    """Test complete user registration and data flow without Flask app"""
    
    def setUp(self):
        """Set up test database and encryption"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Create temporary key file
        self.key_fd, self.key_path = tempfile.mkstemp(suffix='.key')
        os.close(self.key_fd)
        os.unlink(self.key_path)  # Remove empty file
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Get encryption key
        self.fernet_key = read_secret_key(self.key_path)
        
        # Test data
        self.test_username = "testuser"
        self.test_password = "TestPass123"
        self.test_data = "This is secret test data"
        
    def tearDown(self):
        """Clean up test files"""
        for path in [self.test_db_path, self.key_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_complete_user_registration_flow(self):
        """Test complete user registration flow"""
        # 1. Validate username
        is_valid, error = validate_username(self.test_username)
        self.assertTrue(is_valid, f"Username validation failed: {error}")
        
        # 2. Validate password
        is_valid, error = validate_password(self.test_password)
        self.assertTrue(is_valid, f"Password validation failed: {error}")
        
        # 3. Check user doesn't exist
        self.assertFalse(user_exists(self.test_username, self.test_db_path))
        
        # 4. Create user with hashed password
        password_hash = generate_password_hash(self.test_password)
        result = create_user(self.test_username, password_hash, self.test_db_path)
        self.assertTrue(result)
        
        # 5. Verify user exists
        self.assertTrue(user_exists(self.test_username, self.test_db_path))
        
        # 6. Verify password can be retrieved and verified
        stored_hash = get_user_password(self.test_username, self.test_db_path)
        self.assertIsNotNone(stored_hash)
        self.assertTrue(check_password_hash(stored_hash, self.test_password))
        self.assertFalse(check_password_hash(stored_hash, "wrongpassword"))
    
    def test_complete_login_flow(self):
        """Test complete login flow"""
        # Setup: Create user
        password_hash = generate_password_hash(self.test_password)
        create_user(self.test_username, password_hash, self.test_db_path)
        
        # 1. Validate input username
        is_valid, error = validate_username(self.test_username)
        self.assertTrue(is_valid)
        
        # 2. Check if user exists
        self.assertTrue(user_exists(self.test_username, self.test_db_path))
        
        # 3. Get stored password hash
        stored_hash = get_user_password(self.test_username, self.test_db_path)
        self.assertIsNotNone(stored_hash)
        
        # 4. Verify password
        self.assertTrue(check_password_hash(stored_hash, self.test_password))
        
        # 5. Test with wrong password
        self.assertFalse(check_password_hash(stored_hash, "wrongpassword"))
        
        # 6. Test with non-existent user
        nonexistent_hash = get_user_password("nonexistent", self.test_db_path)
        self.assertIsNone(nonexistent_hash)
    
    def test_complete_data_save_retrieve_flow(self):
        """Test complete data save and retrieve flow with encryption"""
        # Setup: Create user
        password_hash = generate_password_hash(self.test_password)
        create_user(self.test_username, password_hash, self.test_db_path)
        
        # 1. Validate data input
        is_valid, error = validate_data_input(self.test_data)
        self.assertTrue(is_valid, f"Data validation failed: {error}")
        
        # 2. Encrypt data
        encrypted_data = encrypt_data(self.test_data, self.fernet_key)
        self.assertIsInstance(encrypted_data, bytes)
        self.assertNotEqual(encrypted_data, self.test_data.encode())
        
        # 3. Save encrypted data
        result = save_user_data(self.test_username, encrypted_data, self.test_db_path)
        self.assertTrue(result)
        
        # 4. Retrieve encrypted data
        retrieved_encrypted = get_user_data(self.test_username, self.test_db_path)
        self.assertIsNotNone(retrieved_encrypted)
        self.assertEqual(retrieved_encrypted, encrypted_data)
        
        # 5. Decrypt retrieved data
        decrypted_data = decrypt_data(retrieved_encrypted, self.fernet_key)
        self.assertEqual(decrypted_data, self.test_data)
        
        # 6. Test data update
        updated_data = "Updated secret data"
        updated_encrypted = encrypt_data(updated_data, self.fernet_key)
        result = save_user_data(self.test_username, updated_encrypted, self.test_db_path)
        self.assertTrue(result)
        
        # 7. Verify data was updated
        retrieved_updated = get_user_data(self.test_username, self.test_db_path)
        decrypted_updated = decrypt_data(retrieved_updated, self.fernet_key)
        self.assertEqual(decrypted_updated, updated_data)
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios"""
        # 1. Invalid username validation
        invalid_usernames = ["", "ab", "a" * 51, "_invalid", "user@name"]
        for username in invalid_usernames:
            is_valid, error = validate_username(username)
            self.assertFalse(is_valid, f"Username '{username}' should be invalid")
            self.assertIsNotNone(error)
        
        # 2. Invalid password validation
        invalid_passwords = ["", "short", "nouppercase123", "NOLOWERCASE123", "NoNumbers"]
        for password in invalid_passwords:
            is_valid, error = validate_password(password)
            self.assertFalse(is_valid, f"Password '{password}' should be invalid")
            self.assertIsNotNone(error)
        
        # 3. Invalid data validation
        invalid_data = ["", "   ", "x" * 10001]  # Empty, whitespace, too long
        for data in invalid_data:
            is_valid, error = validate_data_input(data)
            self.assertFalse(is_valid, f"Data should be invalid")
            self.assertIsNotNone(error)
        
        # 4. Duplicate user creation
        password_hash = generate_password_hash(self.test_password)
        create_user(self.test_username, password_hash, self.test_db_path)
        
        # Try to create same user again
        with self.assertRaises(Exception) as context:
            create_user(self.test_username, password_hash, self.test_db_path)
        
        error_msg = str(context.exception)
        self.assertTrue(
            "already exists" in error_msg or "UNIQUE constraint" in error_msg,
            f"Expected duplicate user error, got: {error_msg}"
        )
        
        # 5. Get data for user with no saved data
        no_data = get_user_data(self.test_username, self.test_db_path)
        self.assertIsNone(no_data)
    
    def test_multiple_users_data_isolation(self):
        """Test that multiple users' data is properly isolated"""
        # Create two users
        user1 = "user1"
        user2 = "user2"
        password_hash = generate_password_hash("TestPass123")
        
        create_user(user1, password_hash, self.test_db_path)
        create_user(user2, password_hash, self.test_db_path)
        
        # Save different data for each user
        data1 = "User 1 secret data"
        data2 = "User 2 different secret data"
        
        encrypted_data1 = encrypt_data(data1, self.fernet_key)
        encrypted_data2 = encrypt_data(data2, self.fernet_key)
        
        save_user_data(user1, encrypted_data1, self.test_db_path)
        save_user_data(user2, encrypted_data2, self.test_db_path)
        
        # Retrieve and verify each user's data
        retrieved_data1 = get_user_data(user1, self.test_db_path)
        retrieved_data2 = get_user_data(user2, self.test_db_path)
        
        decrypted_data1 = decrypt_data(retrieved_data1, self.fernet_key)
        decrypted_data2 = decrypt_data(retrieved_data2, self.fernet_key)
        
        self.assertEqual(decrypted_data1, data1)
        self.assertEqual(decrypted_data2, data2)
        self.assertNotEqual(decrypted_data1, decrypted_data2)
        
        # Verify users exist independently
        self.assertTrue(user_exists(user1, self.test_db_path))
        self.assertTrue(user_exists(user2, self.test_db_path))
        self.assertFalse(user_exists("nonexistent", self.test_db_path))


class TestValidationFunctions(unittest.TestCase):
    """Test validation functions comprehensively"""
    
    def test_username_validation_edge_cases(self):
        """Test username validation with various edge cases"""
        # Valid usernames
        valid_usernames = ["user123", "testUser", "user_name", "a1b2c3", "User_123"]
        for username in valid_usernames:
            is_valid, error = validate_username(username)
            self.assertTrue(is_valid, f"Username '{username}' should be valid, got error: {error}")
        
        # Invalid usernames
        invalid_cases = [
            ("", "El nombre de usuario es requerido"),
            ("  ", "El nombre de usuario es requerido"),
            ("ab", "debe tener al menos 3 caracteres"),
            ("a" * 51, "no puede tener más de 50 caracteres"),
            ("_invalid", "debe comenzar con una letra o número"),
            ("user@name", "solo puede contener letras, números y guiones bajos"),
            ("user-name", "solo puede contener letras, números y guiones bajos"),
            ("user name", "solo puede contener letras, números y guiones bajos"),
        ]
        
        for username, expected_error_part in invalid_cases:
            is_valid, error = validate_username(username)
            self.assertFalse(is_valid, f"Username '{username}' should be invalid")
            self.assertIn(expected_error_part, error, f"Error message should contain '{expected_error_part}'")
    
    def test_password_validation_edge_cases(self):
        """Test password validation with various edge cases"""
        # Valid passwords
        valid_passwords = ["TestPass123", "MySecure1", "Abcdef123", "P@ssw0rd"]
        for password in valid_passwords:
            is_valid, error = validate_password(password)
            self.assertTrue(is_valid, f"Password '{password}' should be valid, got error: {error}")
        
        # Invalid passwords
        invalid_cases = [
            ("", "La contraseña es requerida"),
            ("short", "debe tener al menos 8 caracteres"),
            ("a" * 129, "no puede tener más de 128 caracteres"),
            ("nouppercase123", "una letra mayúscula"),
            ("NOLOWERCASE123", "una letra minúscula"),
            ("NoNumbers", "un número"),
            ("nonumber", "una letra mayúscula"),  # Multiple issues
        ]
        
        for password, expected_error_part in invalid_cases:
            is_valid, error = validate_password(password)
            self.assertFalse(is_valid, f"Password '{password}' should be invalid")
            self.assertIn(expected_error_part, error, f"Error message should contain '{expected_error_part}'")
    
    def test_data_validation_edge_cases(self):
        """Test data input validation with various edge cases"""
        # Valid data
        valid_data = ["Hello world", "Some data with numbers 123", "Special chars: !@#$%"]
        for data in valid_data:
            is_valid, error = validate_data_input(data)
            self.assertTrue(is_valid, f"Data '{data}' should be valid, got error: {error}")
        
        # Invalid data
        invalid_cases = [
            ("", "Los datos son requeridos"),
            ("   ", "Los datos son requeridos"),
            ("x" * 10001, "demasiado largos"),
            ("<script>alert('xss')</script>", "contenido no permitido"),
            ("javascript:alert('xss')", "contenido no permitido"),
            ("<iframe src='evil'></iframe>", "contenido no permitido"),
        ]
        
        for data, expected_error_part in invalid_cases:
            is_valid, error = validate_data_input(data)
            self.assertFalse(is_valid, f"Data should be invalid")
            self.assertIn(expected_error_part, error, f"Error message should contain '{expected_error_part}'")


if __name__ == '__main__':
    unittest.main()