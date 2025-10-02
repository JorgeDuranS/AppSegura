"""
Simplified integration tests for API endpoints
Tests complete user registration flow, login/logout functionality,
data save/retrieve with encryption, and error responses and edge cases
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app
from database import init_database, create_user, get_user_data
from crypto import read_secret_key, encrypt_data
from werkzeug.security import generate_password_hash


class TestAPIEndpointsSimple(unittest.TestCase):
    """Test API endpoints with mocked CSRF protection"""
    
    def setUp(self):
        """Set up test client and temporary database"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Create temporary key file
        self.key_fd, self.key_path = tempfile.mkstemp(suffix='.key')
        os.close(self.key_fd)
        os.unlink(self.key_path)  # Remove empty file so crypto can create proper one
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Mock CSRF validation to always pass
        self.csrf_patcher = patch('app.validate_csrf')
        mock_csrf = self.csrf_patcher.start()
        mock_csrf.return_value = None  # No exception means validation passed
        
        # Patch database path and key path
        self.db_patcher = patch('database.DEFAULT_DB_PATH', self.test_db_path)
        self.key_patcher = patch('app.fernet_key', read_secret_key(self.key_path))
        
        self.db_patcher.start()
        self.key_patcher.start()
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Create test client
        self.client = app.test_client()
        
        # Test data
        self.test_username = "testuser"
        self.test_password = "TestPass123"
        self.test_data = "This is test data to encrypt"
        
    def tearDown(self):
        """Clean up test files and patches"""
        self.csrf_patcher.stop()
        self.db_patcher.stop()
        self.key_patcher.stop()
        
        for path in [self.test_db_path, self.key_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_index_page_loads(self):
        """Test that index page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_loads(self):
        """Test that register page loads correctly"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_successful_user_registration(self):
        """Test successful user registration"""
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'NewPass123',
            'confirm-password': 'NewPass123',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Usuario registrado con éxito', data['message'])
        self.assertEqual(data['redirect'], '/login')
    
    def test_registration_with_invalid_username(self):
        """Test registration with invalid username"""
        response = self.client.post('/register', data={
            'username': 'ab',  # Too short
            'password': 'ValidPass123',
            'confirm-password': 'ValidPass123',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['field'], 'username')
    
    def test_registration_with_weak_password(self):
        """Test registration with weak password"""
        response = self.client.post('/register', data={
            'username': 'validuser',
            'password': 'weak',  # Too weak
            'confirm-password': 'weak',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['field'], 'password')
    
    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        response = self.client.post('/register', data={
            'username': 'validuser',
            'password': 'ValidPass123',
            'confirm-password': 'DifferentPass123',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Las contraseñas no coinciden', data['error'])
        self.assertEqual(data['field'], 'confirm-password')
    
    def test_registration_without_terms(self):
        """Test registration without accepting terms"""
        response = self.client.post('/register', data={
            'username': 'validuser',
            'password': 'ValidPass123',
            'confirm-password': 'ValidPass123',
            'csrf_token': 'dummy'
            # No 'terms': 'on'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('términos de servicio', data['error'])
        self.assertEqual(data['field'], 'terms')
    
    def test_registration_duplicate_user(self):
        """Test registration with duplicate username"""
        # Register user first time
        self.client.post('/register', data={
            'username': 'duplicateuser',
            'password': 'ValidPass123',
            'confirm-password': 'ValidPass123',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        # Try to register same user again
        response = self.client.post('/register', data={
            'username': 'duplicateuser',
            'password': 'ValidPass123',
            'confirm-password': 'ValidPass123',
            'terms': 'on',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('ya está en uso', data['error'])
        self.assertEqual(data['field'], 'username')


class TestLoginLogoutFlowSimple(unittest.TestCase):
    """Test login/logout functionality with mocked CSRF"""
    
    def setUp(self):
        """Set up test client and test user"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Mock CSRF validation
        self.csrf_patcher = patch('app.validate_csrf')
        mock_csrf = self.csrf_patcher.start()
        mock_csrf.return_value = None
        
        # Patch database path
        self.db_patcher = patch('database.DEFAULT_DB_PATH', self.test_db_path)
        self.db_patcher.start()
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Create test user
        self.test_username = "testuser"
        self.test_password = "TestPass123"
        password_hash = generate_password_hash(self.test_password)
        create_user(self.test_username, password_hash, self.test_db_path)
        
        # Create test client
        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up test files and patches"""
        self.csrf_patcher.stop()
        self.db_patcher.stop()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_successful_login(self):
        """Test successful user login"""
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password,
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Inicio de sesión exitoso', data['message'])
        self.assertEqual(data['redirect'], '/data')
    
    def test_login_with_invalid_username(self):
        """Test login with non-existent username"""
        response = self.client.post('/login', data={
            'username': 'nonexistent',
            'password': 'anypassword',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Usuario o contraseña incorrectos', data['error'])
        self.assertEqual(data['field'], 'username')
    
    def test_login_with_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': 'wrongpassword',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Usuario o contraseña incorrectos', data['error'])
        self.assertEqual(data['field'], 'username')
    
    def test_login_with_empty_fields(self):
        """Test login with empty username or password"""
        # Empty username
        response = self.client.post('/login', data={
            'username': '',
            'password': self.test_password,
            'csrf_token': 'dummy'
        })
        self.assertEqual(response.status_code, 400)
        
        # Empty password
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': '',
            'csrf_token': 'dummy'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_logout_functionality(self):
        """Test user logout"""
        # Login first
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        # Test logout
        response = self.client.post('/logout', data={'csrf_token': 'dummy'})
        self.assertEqual(response.status_code, 302)  # Redirect response
        
        # Verify session is cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn('username', sess)
    
    def test_data_page_requires_authentication(self):
        """Test that data page requires authentication"""
        response = self.client.get('/data')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_user_can_access_data_page(self):
        """Test that authenticated user can access data page"""
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        response = self.client.get('/data')
        self.assertEqual(response.status_code, 200)


class TestDataSaveRetrieveFlowSimple(unittest.TestCase):
    """Test data save/retrieve with encryption and mocked CSRF"""
    
    def setUp(self):
        """Set up test client, database, and authenticated user"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Create temporary key file
        self.key_fd, self.key_path = tempfile.mkstemp(suffix='.key')
        os.close(self.key_fd)
        os.unlink(self.key_path)
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Mock CSRF validation
        self.csrf_patcher = patch('app.validate_csrf')
        mock_csrf = self.csrf_patcher.start()
        mock_csrf.return_value = None
        
        # Patch database path and key
        self.db_patcher = patch('database.DEFAULT_DB_PATH', self.test_db_path)
        self.key_patcher = patch('app.fernet_key', read_secret_key(self.key_path))
        
        self.db_patcher.start()
        self.key_patcher.start()
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Create test user
        self.test_username = "testuser"
        self.test_password = "TestPass123"
        password_hash = generate_password_hash(self.test_password)
        create_user(self.test_username, password_hash, self.test_db_path)
        
        # Create test client
        self.client = app.test_client()
        
        # Test data
        self.test_data = "This is secret test data"
        
    def tearDown(self):
        """Clean up test files and patches"""
        self.csrf_patcher.stop()
        self.db_patcher.stop()
        self.key_patcher.stop()
        
        for path in [self.test_db_path, self.key_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_save_user_data_success(self):
        """Test successful data save"""
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        response = self.client.post('/api/data', data={
            'data': self.test_data,
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Datos guardados con éxito', data['message'])
    
    def test_retrieve_user_data_success(self):
        """Test successful data retrieval"""
        # First save some data
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        self.client.post('/api/data', data={
            'data': self.test_data,
            'csrf_token': 'dummy'
        })
        
        # Then retrieve it
        response = self.client.get('/api/data')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], self.test_data)
    
    def test_retrieve_data_when_none_exists(self):
        """Test retrieving data when user has no saved data"""
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        response = self.client.get('/api/data')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsNone(data['data'])
        self.assertIn('no tiene datos guardados', data['message'])
    
    def test_data_api_requires_authentication(self):
        """Test that data API requires authentication"""
        # Test GET without authentication
        response = self.client.get('/api/data')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Usuario no autenticado', data['error'])
        
        # Test POST without authentication
        response = self.client.post('/api/data', data={
            'data': self.test_data,
            'csrf_token': 'dummy'
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Usuario no autenticado', data['error'])
    
    def test_save_invalid_data(self):
        """Test saving invalid data"""
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        # Test with empty data
        response = self.client.post('/api/data', data={
            'data': '',
            'csrf_token': 'dummy'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_data_update_overwrites_previous(self):
        """Test that saving new data overwrites previous data"""
        with self.client.session_transaction() as sess:
            sess['username'] = self.test_username
        
        # Save initial data
        initial_data = "Initial data"
        self.client.post('/api/data', data={
            'data': initial_data,
            'csrf_token': 'dummy'
        })
        
        # Save updated data
        updated_data = "Updated data"
        self.client.post('/api/data', data={
            'data': updated_data,
            'csrf_token': 'dummy'
        })
        
        # Retrieve and verify updated data
        response = self.client.get('/api/data')
        data = json.loads(response.data)
        self.assertEqual(data['data'], updated_data)


class TestErrorResponsesAndEdgeCasesSimple(unittest.TestCase):
    """Test error responses and edge cases"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.client = app.test_client()
    
    def test_404_error_handling(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_method_not_allowed(self):
        """Test method not allowed errors"""
        # Try POST to GET-only endpoint
        response = self.client.post('/')
        self.assertEqual(response.status_code, 405)
    
    def test_large_data_input(self):
        """Test handling of very large data input"""
        # Create temporary database for this test
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)
        
        try:
            # Mock CSRF validation
            with patch('app.validate_csrf') as mock_csrf:
                mock_csrf.return_value = None
                
                with patch('database.DEFAULT_DB_PATH', test_db_path):
                    init_database(test_db_path)
                    
                    # Create test user
                    test_username = "testuser"
                    password_hash = generate_password_hash("TestPass123")
                    create_user(test_username, password_hash, test_db_path)
                    
                    with self.client.session_transaction() as sess:
                        sess['username'] = test_username
                    
                    # Try to save very large data (over 10KB limit)
                    large_data = "x" * 15000
                    response = self.client.post('/api/data', data={
                        'data': large_data,
                        'csrf_token': 'dummy'
                    })
                    
                    self.assertEqual(response.status_code, 400)
                    data = json.loads(response.data)
                    self.assertIn('error', data)
        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)


if __name__ == '__main__':
    unittest.main()