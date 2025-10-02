"""
Frontend functionality tests
Tests form submissions and validations, responsive design concepts,
error message display, and user interaction flows
"""

import unittest
import tempfile
import os
import re
from unittest.mock import patch

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app
from database import init_database, create_user
from crypto import read_secret_key
from werkzeug.security import generate_password_hash


class TestFormSubmissionsAndValidations(unittest.TestCase):
    """Test form submissions and client-side validation logic"""
    
    def setUp(self):
        """Set up test client and temporary database"""
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
        
        # Patch database path and key
        self.db_patcher = patch('database.DEFAULT_DB_PATH', self.test_db_path)
        self.key_patcher = patch('app.fernet_key', read_secret_key(self.key_path))
        
        self.db_patcher.start()
        self.key_patcher.start()
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Create test client
        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up test files and patches"""
        self.db_patcher.stop()
        self.key_patcher.stop()
        
        for path in [self.test_db_path, self.key_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_login_form_structure(self):
        """Test that login form has proper structure and validation elements"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for form elements
        self.assertIn('id="loginForm"', html_content)
        self.assertIn('name="username"', html_content)
        self.assertIn('name="password"', html_content)
        self.assertIn('name="csrf_token"', html_content)
        
        # Check for validation elements
        self.assertIn('id="username-error"', html_content)
        self.assertIn('id="password-error"', html_content)
        
        # Check for JavaScript validation
        self.assertIn('validateForm', html_content)
        self.assertIn('showError', html_content)
        
        # Check for accessibility features
        self.assertIn('required', html_content)
        self.assertIn('autocomplete="username"', html_content)
        self.assertIn('autocomplete="current-password"', html_content)
        
        # Check for password visibility toggle
        self.assertIn('toggle-password', html_content)
        self.assertIn('eye-open', html_content)
        self.assertIn('eye-closed', html_content)
    
    def test_register_form_structure(self):
        """Test that register form has proper structure and validation elements"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for form elements
        self.assertIn('id="registerForm"', html_content)
        self.assertIn('name="username"', html_content)
        self.assertIn('name="password"', html_content)
        self.assertIn('name="confirm-password"', html_content)
        self.assertIn('name="terms"', html_content)
        
        # Check for validation elements
        self.assertIn('id="username-error"', html_content)
        self.assertIn('id="password-error"', html_content)
        self.assertIn('id="confirm-password-error"', html_content)
        
        # Check for password strength indicator
        self.assertIn('password-strength-bar', html_content)
        self.assertIn('password-strength-text', html_content)
        self.assertIn('password-requirements', html_content)
        
        # Check for password requirements
        self.assertIn('req-length', html_content)
        self.assertIn('req-uppercase', html_content)
        self.assertIn('req-lowercase', html_content)
        self.assertIn('req-number', html_content)
        
        # Check for JavaScript functions
        self.assertIn('checkPasswordStrength', html_content)
        self.assertIn('checkPasswordConfirmation', html_content)
        self.assertIn('validateForm', html_content)
    
    def test_data_form_structure(self):
        """Test that data management form has proper structure"""
        # Create test user and login
        test_username = "testuser"
        password_hash = generate_password_hash("TestPass123")
        create_user(test_username, password_hash, self.test_db_path)
        
        with self.client.session_transaction() as sess:
            sess['username'] = test_username
        
        response = self.client.get('/data')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for form elements
        self.assertIn('id="dataForm"', html_content)
        self.assertIn('id="data-input"', html_content)
        self.assertIn('name="csrf_token"', html_content)
        
        # Check for UI elements
        self.assertIn('id="char-count"', html_content)
        self.assertIn('id="save-button"', html_content)
        self.assertIn('id="clear-button"', html_content)
        self.assertIn('id="refresh-button"', html_content)
        
        # Check for data display elements
        self.assertIn('id="data-display"', html_content)
        self.assertIn('id="no-data-state"', html_content)
        self.assertIn('id="data-error-state"', html_content)
        self.assertIn('id="data-loading"', html_content)
        
        # Check for interactive elements
        self.assertIn('id="copy-button"', html_content)
        self.assertIn('id="edit-button"', html_content)
        
        # Check for JavaScript functions
        self.assertIn('loadData', html_content)
        self.assertIn('showState', html_content)
        self.assertIn('setButtonLoading', html_content)


class TestResponsiveDesignElements(unittest.TestCase):
    """Test responsive design elements and mobile-first approach"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
    
    def test_base_template_responsive_structure(self):
        """Test that base template has responsive design elements"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for responsive meta tag
        self.assertIn('name="viewport"', html_content)
        self.assertIn('width=device-width, initial-scale=1.0', html_content)
        
        # Check for Tailwind CSS responsive classes
        responsive_classes = [
            'sm:', 'md:', 'lg:', 'xl:',  # Responsive prefixes
            'max-w-', 'min-h-',  # Responsive containers
            'px-4 sm:px-6 lg:px-8',  # Responsive padding
            'grid-cols-1 lg:grid-cols-2',  # Responsive grid
            'flex-col sm:flex-row',  # Responsive flex direction
        ]
        
        for css_class in responsive_classes:
            self.assertIn(css_class, html_content, f"Missing responsive class: {css_class}")
        
        # Check for mobile navigation considerations
        self.assertIn('space-x-4', html_content)  # Navigation spacing
        self.assertIn('justify-between', html_content)  # Navigation layout
    
    def test_form_responsive_design(self):
        """Test that forms are responsive"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for responsive form classes
        responsive_form_classes = [
            'max-w-md w-full',  # Form container
            'space-y-',  # Vertical spacing
            'sm:text-sm',  # Responsive text size
            'px-4 sm:px-6 lg:px-8',  # Responsive padding
        ]
        
        for css_class in responsive_form_classes:
            self.assertIn(css_class, html_content, f"Missing responsive form class: {css_class}")
    
    def test_data_page_responsive_grid(self):
        """Test that data page has responsive grid layout"""
        # Create test user for authentication
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)
        
        try:
            with patch('database.DEFAULT_DB_PATH', test_db_path):
                init_database(test_db_path)
                test_username = "testuser"
                password_hash = generate_password_hash("TestPass123")
                create_user(test_username, password_hash, test_db_path)
                
                with self.client.session_transaction() as sess:
                    sess['username'] = test_username
                
                response = self.client.get('/data')
                html_content = response.data.decode('utf-8')
                
                # Check for responsive grid
                self.assertIn('grid-cols-1 lg:grid-cols-2', html_content)
                self.assertIn('gap-8', html_content)
                
                # Check for responsive button layouts
                self.assertIn('flex-col sm:flex-row', html_content)
                
        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)


class TestErrorMessageDisplay(unittest.TestCase):
    """Test error message display and user feedback"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
    
    def test_error_message_structure_in_forms(self):
        """Test that forms have proper error message structure"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for error message containers
        error_elements = [
            'id="username-error"',
            'id="password-error"',
            'class="text-sm text-red-600 hidden"',
        ]
        
        for element in error_elements:
            self.assertIn(element, html_content, f"Missing error element: {element}")
        
        # Check for error styling classes
        error_classes = [
            'border-red-300',  # Error input border
            'text-red-600',    # Error text color
            'hidden',          # Initially hidden
        ]
        
        for css_class in error_classes:
            self.assertIn(css_class, html_content, f"Missing error class: {css_class}")
    
    def test_success_message_structure(self):
        """Test that success messages are properly structured"""
        response = self.client.get('/register')
        html_content = response.data.decode('utf-8')
        
        # Check for success feedback elements
        success_elements = [
            'text-green-600',   # Success color
            'bg-green-100',     # Success background
            'border-green-200', # Success border
        ]
        
        for element in success_elements:
            self.assertIn(element, html_content, f"Missing success element: {element}")
    
    def test_loading_state_indicators(self):
        """Test that loading states are properly implemented"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for loading indicators
        loading_elements = [
            'id="loading-icon"',
            'animate-spin',
            'disabled:opacity-50',
            'disabled:cursor-not-allowed',
        ]
        
        for element in loading_elements:
            self.assertIn(element, html_content, f"Missing loading element: {element}")
        
        # Check for loading state management in JavaScript
        self.assertIn('setLoading', html_content)
        self.assertIn('disabled = loading', html_content)


class TestUserInteractionFlows(unittest.TestCase):
    """Test user interaction flows and JavaScript functionality"""
    
    def setUp(self):
        """Set up test client and database"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Patch database path
        self.db_patcher = patch('database.DEFAULT_DB_PATH', self.test_db_path)
        self.db_patcher.start()
        
        # Initialize test database
        init_database(self.test_db_path)
        
        # Create test client
        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up test files and patches"""
        self.db_patcher.stop()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_navigation_flow(self):
        """Test navigation between pages"""
        # Test index page
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html_content = response.data.decode('utf-8')
        
        # Check for navigation links
        self.assertIn('href="/login"', html_content)
        self.assertIn('href="/register"', html_content)
        self.assertIn('Iniciar Sesión', html_content)
        self.assertIn('Registrarse', html_content)
        
        # Test login page navigation
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        self.assertIn('href="/register"', html_content)
        self.assertIn('Regístrate aquí', html_content)
        
        # Test register page navigation
        response = self.client.get('/register')
        html_content = response.data.decode('utf-8')
        self.assertIn('href="/login"', html_content)
        self.assertIn('Inicia sesión aquí', html_content)
    
    def test_authenticated_user_navigation(self):
        """Test navigation for authenticated users"""
        # Create test user
        test_username = "testuser"
        password_hash = generate_password_hash("TestPass123")
        create_user(test_username, password_hash, self.test_db_path)
        
        # Simulate login
        with self.client.session_transaction() as sess:
            sess['username'] = test_username
        
        # Test authenticated navigation
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for authenticated user elements
        self.assertIn(f'Hola, <span class="font-medium">{test_username}</span>', html_content)
        self.assertIn('href="/data"', html_content)
        self.assertIn('Mis Datos', html_content)
        self.assertIn('Cerrar Sesión', html_content)
        
        # Check that login/register links are not present
        self.assertNotIn('Iniciar Sesión', html_content)
        self.assertNotIn('Registrarse', html_content)
    
    def test_form_interaction_elements(self):
        """Test interactive form elements"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for interactive JavaScript elements
        interactive_elements = [
            'addEventListener',
            'toggle-password',
            'validateForm',
            'preventDefault',
            'fetch(',
            'response.json()',
        ]
        
        for element in interactive_elements:
            self.assertIn(element, html_content, f"Missing interactive element: {element}")
    
    def test_data_page_interactions(self):
        """Test data page interactive elements"""
        # Create test user
        test_username = "testuser"
        password_hash = generate_password_hash("TestPass123")
        create_user(test_username, password_hash, self.test_db_path)
        
        with self.client.session_transaction() as sess:
            sess['username'] = test_username
        
        response = self.client.get('/data')
        html_content = response.data.decode('utf-8')
        
        # Check for data management interactions
        data_interactions = [
            'loadData',
            'showState',
            'copy-button',
            'edit-button',
            'clear-button',
            'refresh-button',
            'char-count',
            'navigator.clipboard.writeText',
        ]
        
        for interaction in data_interactions:
            self.assertIn(interaction, html_content, f"Missing data interaction: {interaction}")
    
    def test_accessibility_features(self):
        """Test accessibility features in forms"""
        response = self.client.get('/register')
        html_content = response.data.decode('utf-8')
        
        # Check for accessibility features
        accessibility_features = [
            'aria-',           # ARIA attributes
            'role=',           # Role attributes
            'for="',           # Label associations
            'required',        # Required field indicators
            'autocomplete=',   # Autocomplete attributes
            'tabindex',        # Tab navigation (if present)
        ]
        
        # Count accessibility features present
        accessibility_count = 0
        for feature in accessibility_features:
            if feature in html_content:
                accessibility_count += 1
        
        # Should have at least some accessibility features
        self.assertGreater(accessibility_count, 2, "Should have multiple accessibility features")
    
    def test_security_features_in_forms(self):
        """Test security features in forms"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for security features
        security_features = [
            'csrf_token',
            'autocomplete="current-password"',
            'type="password"',
            'method="POST"',
        ]
        
        for feature in security_features:
            self.assertIn(feature, html_content, f"Missing security feature: {feature}")
    
    def test_user_feedback_mechanisms(self):
        """Test user feedback and notification systems"""
        # Create test user
        test_username = "testuser"
        password_hash = generate_password_hash("TestPass123")
        create_user(test_username, password_hash, self.test_db_path)
        
        with self.client.session_transaction() as sess:
            sess['username'] = test_username
        
        response = self.client.get('/data')
        html_content = response.data.decode('utf-8')
        
        # Check for feedback mechanisms
        feedback_elements = [
            'success',
            'error',
            'loading',
            'alert(',
            'confirm(',
            'setTimeout',
            'classList.add',
            'classList.remove',
        ]
        
        feedback_count = 0
        for element in feedback_elements:
            if element in html_content:
                feedback_count += 1
        
        # Should have multiple feedback mechanisms
        self.assertGreater(feedback_count, 4, "Should have multiple feedback mechanisms")


class TestFormValidationLogic(unittest.TestCase):
    """Test client-side form validation logic"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
    
    def test_login_validation_logic(self):
        """Test login form validation logic"""
        response = self.client.get('/login')
        html_content = response.data.decode('utf-8')
        
        # Check for validation logic
        validation_checks = [
            'value.trim()',
            'length < 3',
            'length < 4',
            'El nombre de usuario es requerido',
            'La contraseña es requerida',
            'debe tener al menos',
        ]
        
        for check in validation_checks:
            self.assertIn(check, html_content, f"Missing validation check: {check}")
    
    def test_register_validation_logic(self):
        """Test register form validation logic"""
        response = self.client.get('/register')
        html_content = response.data.decode('utf-8')
        
        # Check for password strength validation
        strength_checks = [
            'checkPasswordStrength',
            '/[A-Z]/.test',
            '/[a-z]/.test',
            '/\\d/.test',
            'length >= 8',
            'requirements',
        ]
        
        for check in strength_checks:
            self.assertIn(check, html_content, f"Missing strength check: {check}")
        
        # Check for password confirmation validation
        confirmation_checks = [
            'checkPasswordConfirmation',
            'password === confirmPassword',
            'Las contraseñas no coinciden',
        ]
        
        for check in confirmation_checks:
            self.assertIn(check, html_content, f"Missing confirmation check: {check}")
    
    def test_data_validation_logic(self):
        """Test data form validation logic"""
        # Create test user
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)
        
        try:
            with patch('database.DEFAULT_DB_PATH', test_db_path):
                init_database(test_db_path)
                test_username = "testuser"
                password_hash = generate_password_hash("TestPass123")
                create_user(test_username, password_hash, test_db_path)
                
                with self.client.session_transaction() as sess:
                    sess['username'] = test_username
                
                response = self.client.get('/data')
                html_content = response.data.decode('utf-8')
                
                # Check for data validation
                data_validation = [
                    'data.trim()',
                    'Por favor ingresa algunos datos',
                    'char-count',
                    'count > 1000',
                    'border-red-300',
                ]
                
                for validation in data_validation:
                    self.assertIn(validation, html_content, f"Missing data validation: {validation}")
                    
        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)


if __name__ == '__main__':
    unittest.main()