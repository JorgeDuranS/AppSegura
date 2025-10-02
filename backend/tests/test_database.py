"""
Unit tests for database operations
Tests database connection, initialization, user CRUD operations, 
data encryption/decryption with database, and error handling scenarios
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import (
    init_database,
    get_db_connection,
    create_user,
    get_user_password,
    save_user_data,
    get_user_data,
    user_exists,
    get_database_info,
    DatabaseError
)
from crypto import read_secret_key, encrypt_data, decrypt_data


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations with temporary database files"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)  # Close file descriptor, keep path
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Test data
        self.test_username = "testuser"
        self.test_password_hash = "hashed_password_123"
        self.test_data = "test encrypted data"
        
    def tearDown(self):
        """Clean up test database after each test"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database connection and initialization"""
        # Test that database file was created
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Test that tables were created
        with get_db_connection(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Check users table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            self.assertIsNotNone(cursor.fetchone())
            
            # Check data table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='data'
            """)
            self.assertIsNotNone(cursor.fetchone())
            
            # Check indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_users_username'
            """)
            self.assertIsNotNone(cursor.fetchone())
    
    def test_database_connection_context_manager(self):
        """Test database connection context manager"""
        # Test successful connection
        with get_db_connection(self.test_db_path) as conn:
            self.assertIsNotNone(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_create_user_success(self):
        """Test successful user creation"""
        result = create_user(self.test_username, self.test_password_hash, self.test_db_path)
        self.assertTrue(result)
        
        # Verify user was created
        self.assertTrue(user_exists(self.test_username, self.test_db_path))
    
    def test_create_user_duplicate(self):
        """Test creating duplicate user raises error"""
        # Create user first time
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Try to create same user again
        with self.assertRaises(DatabaseError) as context:
            create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Check for either error message format
        error_msg = str(context.exception)
        self.assertTrue(
            "already exists" in error_msg or "UNIQUE constraint failed" in error_msg,
            f"Expected duplicate user error, got: {error_msg}"
        )
    
    def test_get_user_password_existing_user(self):
        """Test getting password for existing user"""
        # Create user first
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Get password
        password = get_user_password(self.test_username, self.test_db_path)
        self.assertEqual(password, self.test_password_hash)
    
    def test_get_user_password_nonexistent_user(self):
        """Test getting password for non-existent user returns None"""
        password = get_user_password("nonexistent", self.test_db_path)
        self.assertIsNone(password)
    
    def test_user_exists_true(self):
        """Test user_exists returns True for existing user"""
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        self.assertTrue(user_exists(self.test_username, self.test_db_path))
    
    def test_user_exists_false(self):
        """Test user_exists returns False for non-existent user"""
        self.assertFalse(user_exists("nonexistent", self.test_db_path))
    
    def test_save_user_data_new(self):
        """Test saving new user data"""
        # Create user first
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Save data
        test_data_bytes = self.test_data.encode('utf-8')
        result = save_user_data(self.test_username, test_data_bytes, self.test_db_path)
        self.assertTrue(result)
        
        # Verify data was saved
        retrieved_data = get_user_data(self.test_username, self.test_db_path)
        self.assertEqual(retrieved_data, test_data_bytes)
    
    def test_save_user_data_update(self):
        """Test updating existing user data"""
        # Create user and save initial data
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        initial_data = b"initial data"
        save_user_data(self.test_username, initial_data, self.test_db_path)
        
        # Update data
        updated_data = b"updated data"
        result = save_user_data(self.test_username, updated_data, self.test_db_path)
        self.assertTrue(result)
        
        # Verify data was updated
        retrieved_data = get_user_data(self.test_username, self.test_db_path)
        self.assertEqual(retrieved_data, updated_data)
    
    def test_get_user_data_existing(self):
        """Test getting data for user with saved data"""
        # Create user and save data
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        test_data_bytes = self.test_data.encode('utf-8')
        save_user_data(self.test_username, test_data_bytes, self.test_db_path)
        
        # Get data
        retrieved_data = get_user_data(self.test_username, self.test_db_path)
        self.assertEqual(retrieved_data, test_data_bytes)
    
    def test_get_user_data_nonexistent(self):
        """Test getting data for user with no saved data returns None"""
        # Create user but don't save data
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Try to get data
        retrieved_data = get_user_data(self.test_username, self.test_db_path)
        self.assertIsNone(retrieved_data)
    
    def test_get_database_info(self):
        """Test getting database information"""
        # Create some test data
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        save_user_data(self.test_username, b"test data", self.test_db_path)
        
        # Get database info
        info = get_database_info(self.test_db_path)
        
        # Verify info structure
        self.assertIn('database_path', info)
        self.assertIn('database_size_bytes', info)
        self.assertIn('user_count', info)
        self.assertIn('data_records_count', info)
        self.assertIn('database_exists', info)
        
        # Verify counts
        self.assertEqual(info['user_count'], 1)
        self.assertEqual(info['data_records_count'], 1)
        self.assertTrue(info['database_exists'])
        self.assertGreater(info['database_size_bytes'], 0)


class TestDatabaseErrorHandling(unittest.TestCase):
    """Test database error handling scenarios"""
    
    def test_init_database_invalid_path(self):
        """Test database initialization with invalid path"""
        invalid_path = "/invalid/path/database.db"
        with self.assertRaises(DatabaseError):
            init_database(invalid_path)
    
    def test_connection_to_nonexistent_database(self):
        """Test connection to non-existent database directory"""
        invalid_path = "/nonexistent/directory/test.db"
        with self.assertRaises(DatabaseError):
            with get_db_connection(invalid_path) as conn:
                pass
    
    @patch('database.sqlite3.connect')
    def test_database_connection_error(self, mock_connect):
        """Test database connection error handling"""
        mock_connect.side_effect = sqlite3.Error("Connection failed")
        
        with self.assertRaises(DatabaseError) as context:
            with get_db_connection("test.db") as conn:
                pass
        
        self.assertIn("Connection failed", str(context.exception))
    
    @patch('database.get_db_connection')
    def test_create_user_database_error(self, mock_connection):
        """Test create_user with database error"""
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("Database error")
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        with self.assertRaises(DatabaseError):
            create_user("testuser", "password", "test.db")
    
    @patch('database.get_db_connection')
    def test_get_user_password_database_error(self, mock_connection):
        """Test get_user_password with database error"""
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("Database error")
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        with self.assertRaises(DatabaseError):
            get_user_password("testuser", "test.db")


class TestDatabaseWithEncryption(unittest.TestCase):
    """Test database operations with actual encryption/decryption"""
    
    def setUp(self):
        """Set up test database and encryption key"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Create temporary key file
        self.key_fd, self.key_path = tempfile.mkstemp(suffix='.key')
        os.close(self.key_fd)
        # Remove the empty key file so read_secret_key can create a proper one
        os.unlink(self.key_path)
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Get encryption key (this will create the key file)
        self.fernet_key = read_secret_key(self.key_path)
        
        # Test data
        self.test_username = "testuser"
        self.test_password_hash = "hashed_password_123"
        self.test_plain_data = "This is secret test data that should be encrypted"
        
    def tearDown(self):
        """Clean up test files"""
        for path in [self.test_db_path, self.key_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_data_encryption_decryption_with_database(self):
        """Test complete flow: encrypt data, save to DB, retrieve from DB, decrypt"""
        # Create user
        create_user(self.test_username, self.test_password_hash, self.test_db_path)
        
        # Encrypt data
        encrypted_data = encrypt_data(self.test_plain_data, self.fernet_key)
        self.assertIsInstance(encrypted_data, bytes)
        self.assertNotEqual(encrypted_data, self.test_plain_data.encode())
        
        # Save encrypted data to database
        result = save_user_data(self.test_username, encrypted_data, self.test_db_path)
        self.assertTrue(result)
        
        # Retrieve encrypted data from database
        retrieved_encrypted_data = get_user_data(self.test_username, self.test_db_path)
        self.assertEqual(retrieved_encrypted_data, encrypted_data)
        
        # Decrypt retrieved data
        decrypted_data = decrypt_data(retrieved_encrypted_data, self.fernet_key)
        self.assertEqual(decrypted_data, self.test_plain_data)
    
    def test_multiple_users_data_isolation(self):
        """Test that different users' encrypted data is properly isolated"""
        # Create two users
        user1 = "user1"
        user2 = "user2"
        create_user(user1, "hash1", self.test_db_path)
        create_user(user2, "hash2", self.test_db_path)
        
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


if __name__ == '__main__':
    unittest.main()