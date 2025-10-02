#!/usr/bin/env python3
"""
Application initialization script
Ensures all required components are properly set up before starting the app
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def setup_logging():
    """Configure logging for initialization"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_and_create_directories():
    """Ensure all required directories exist"""
    logger = logging.getLogger(__name__)
    
    required_dirs = [
        Path(__file__).parent,  # src directory
        Path(__file__).parent.parent,  # backend directory
        Path(__file__).parent / 'logs',  # logs directory (if needed)
    ]
    
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return False
    
    return True

def initialize_encryption():
    """Initialize encryption key with multiple fallback options"""
    logger = logging.getLogger(__name__)
    
    # Try multiple key locations
    key_locations = [
        Path(__file__).parent / '.secret.key',  # src/.secret.key
        Path(__file__).parent.parent / '.secret.key',  # backend/.secret.key
        Path.home() / '.webapp_secret.key',  # user home directory
    ]
    
    for key_path in key_locations:
        try:
            logger.info(f"Attempting to initialize encryption key at: {key_path}")
            
            from crypto import read_secret_key
            fernet_key = read_secret_key(str(key_path))
            
            logger.info(f"SUCCESS: Encryption key initialized at {key_path}")
            return fernet_key, str(key_path)
            
        except Exception as e:
            logger.warning(f"Failed to initialize key at {key_path}: {e}")
            continue
    
    logger.error("Failed to initialize encryption key at any location")
    return None, None

def initialize_database():
    """Initialize database with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        from database import init_database
        init_database()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def validate_dependencies():
    """Check that all required modules are available"""
    logger = logging.getLogger(__name__)
    
    required_modules = [
        'flask',
        'cryptography',
        'werkzeug',
        'flask_wtf',
        'dotenv',
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"Module available: {module}")
        except ImportError:
            missing_modules.append(module)
            logger.error(f"Missing module: {module}")
    
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.info("Install missing modules with: pip install " + " ".join(missing_modules))
        return False
    
    return True

def main():
    """Main initialization function"""
    logger = setup_logging()
    logger.info("Starting application initialization...")
    
    # Step 1: Validate dependencies
    logger.info("Step 1: Validating dependencies...")
    if not validate_dependencies():
        logger.error("Dependency validation failed")
        return False
    
    # Step 2: Create required directories
    logger.info("Step 2: Creating required directories...")
    if not check_and_create_directories():
        logger.error("Directory creation failed")
        return False
    
    # Step 3: Initialize database
    logger.info("Step 3: Initializing database...")
    if not initialize_database():
        logger.error("Database initialization failed")
        return False
    
    # Step 4: Initialize encryption
    logger.info("Step 4: Initializing encryption...")
    fernet_key, key_path = initialize_encryption()
    if not fernet_key:
        logger.error("Encryption initialization failed")
        return False
    
    logger.info("=" * 50)
    logger.info("🎉 Application initialization completed successfully!")
    logger.info(f"📁 Database: app.db")
    logger.info(f"🔐 Encryption key: {key_path}")
    logger.info("=" * 50)
    logger.info("You can now start the application with: python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)