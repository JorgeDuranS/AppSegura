#!/usr/bin/env python3
"""
End-to-end test script for the secure web application
Tests the complete workflow from installation to usage
"""

import os
import sys
import tempfile
import sqlite3
import subprocess
import time
from pathlib import Path

# Add backend src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_database_creation():
    """Test that database is created properly"""
    print("Testing database creation...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        from database import init_database
        init_database(db_path)
        
        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None, "Users table not created"
        
        # Check data table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data'")
        assert cursor.fetchone() is not None, "Data table not created"
        
        conn.close()
        print("✓ Database creation test passed")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_crypto_functions():
    """Test encryption and decryption functions"""
    print("Testing crypto functions...")
    
    # Create a temporary file path but don't create the file
    import tempfile
    key_fd, key_path = tempfile.mkstemp(suffix='.key')
    os.close(key_fd)
    os.unlink(key_path)  # Remove the empty file so crypto can create it properly
    
    try:
        from crypto import read_secret_key, encrypt_data, decrypt_data
        
        # Test key generation
        fernet = read_secret_key(key_path)
        assert fernet is not None, "Failed to create Fernet key"
        
        # Test encryption/decryption
        test_data = "This is secret test data"
        encrypted = encrypt_data(test_data, fernet)
        assert encrypted != test_data, "Data not encrypted"
        
        decrypted = decrypt_data(encrypted, fernet)
        assert decrypted == test_data, f"Decryption failed: {decrypted} != {test_data}"
        
        print("✓ Crypto functions test passed")
        
    finally:
        if os.path.exists(key_path):
            os.unlink(key_path)

def test_user_operations():
    """Test user creation and authentication"""
    print("Testing user operations...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        from database import init_database, create_user, get_user_password, user_exists
        from werkzeug.security import generate_password_hash, check_password_hash
        
        init_database(db_path)
        
        # Test user creation
        username = "testuser"
        password = "TestPass123"
        password_hash = generate_password_hash(password)
        
        result = create_user(username, password_hash, db_path)
        assert result is True, "Failed to create user"
        
        # Test user exists
        assert user_exists(username, db_path), "User not found after creation"
        
        # Test password verification
        stored_hash = get_user_password(username, db_path)
        assert stored_hash is not None, "Failed to retrieve user password"
        assert check_password_hash(stored_hash, password), "Password verification failed"
        
        print("✓ User operations test passed")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_validation_functions():
    """Test input validation functions"""
    print("Testing validation functions...")
    
    from validation import validate_username, validate_password, validate_data_input
    
    # Test username validation
    valid, msg = validate_username("testuser")
    assert valid, f"Valid username rejected: {msg}"
    
    valid, msg = validate_username("ab")  # Too short
    assert not valid, "Invalid username accepted"
    
    # Test password validation
    valid, msg = validate_password("TestPass123")
    assert valid, f"Valid password rejected: {msg}"
    
    valid, msg = validate_password("123")  # Too short
    assert not valid, "Invalid password accepted"
    
    # Test data validation
    valid, msg = validate_data_input("Some test data")
    assert valid, f"Valid data rejected: {msg}"
    
    valid, msg = validate_data_input("")  # Empty data
    assert not valid, "Empty data accepted"
    
    print("✓ Validation functions test passed")

def main():
    """Run all end-to-end tests"""
    print("Starting end-to-end testing...")
    print("=" * 50)
    
    tests = [
        test_database_creation,
        test_crypto_functions,
        test_user_operations,
        test_validation_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All end-to-end tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())