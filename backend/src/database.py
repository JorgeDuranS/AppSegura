"""
Database module for SQLite operations
Provides database initialization, connection management, and CRUD operations
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional, Tuple, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = 'app.db'


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


def init_database(db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Initialize the SQLite database with required tables
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if initialization successful, False otherwise
        
    Raises:
        DatabaseError: If database initialization fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(256) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) NOT NULL,
                    data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')
            
            # Create index for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users (username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_data_username 
                ON data (username)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized successfully at {db_path}")
            return True
            
    except sqlite3.Error as e:
        error_msg = f"Failed to initialize database: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager for database connections
    Ensures proper connection handling and cleanup
    
    Args:
        db_path: Path to the SQLite database file
        
    Yields:
        sqlite3.Connection: Database connection object
        
    Raises:
        DatabaseError: If connection fails
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        
        # Enable foreign key constraints for this connection
        conn.execute("PRAGMA foreign_keys = ON")
        
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        error_msg = f"Database connection error: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)
    finally:
        if conn:
            conn.close()


def create_user(username: str, password_hash: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Create a new user in the database
    
    Args:
        username: Username for the new user
        password_hash: Hashed password
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if user created successfully, False otherwise
        
    Raises:
        DatabaseError: If user creation fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password)
                VALUES (?, ?)
            ''', (username, password_hash))
            conn.commit()
            logger.info(f"User '{username}' created successfully")
            return True
            
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            logger.warning(f"User '{username}' already exists")
            raise DatabaseError(f"User '{username}' already exists")
        else:
            logger.error(f"Integrity error creating user: {e}")
            raise DatabaseError(f"Failed to create user: {e}")
    except sqlite3.Error as e:
        error_msg = f"Failed to create user '{username}': {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


def get_user_password(username: str, db_path: str = DEFAULT_DB_PATH) -> Optional[str]:
    """
    Get user's password hash from database
    
    Args:
        username: Username to look up
        db_path: Path to the SQLite database file
        
    Returns:
        str: Password hash if user exists, None otherwise
        
    Raises:
        DatabaseError: If database query fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT password
                FROM users
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            return result['password'] if result else None
            
    except sqlite3.Error as e:
        error_msg = f"Failed to get user password for '{username}': {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


def save_user_data(username: str, encrypted_data: bytes, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Save or update user's encrypted data
    
    Args:
        username: Username
        encrypted_data: Encrypted data as bytes
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if data saved successfully, False otherwise
        
    Raises:
        DatabaseError: If data save fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if user data already exists
            cursor.execute('''
                SELECT id FROM data WHERE username = ?
            ''', (username,))
            
            if cursor.fetchone():
                # Update existing data
                cursor.execute('''
                    UPDATE data 
                    SET data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE username = ?
                ''', (encrypted_data, username))
                logger.info(f"Updated data for user '{username}'")
            else:
                # Insert new data
                cursor.execute('''
                    INSERT INTO data (username, data)
                    VALUES (?, ?)
                ''', (username, encrypted_data))
                logger.info(f"Inserted new data for user '{username}'")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        error_msg = f"Failed to save data for user '{username}': {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


def get_user_data(username: str, db_path: str = DEFAULT_DB_PATH) -> Optional[bytes]:
    """
    Get user's encrypted data from database
    
    Args:
        username: Username to look up
        db_path: Path to the SQLite database file
        
    Returns:
        bytes: Encrypted data if exists, None otherwise
        
    Raises:
        DatabaseError: If database query fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data
                FROM data
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            return result['data'] if result else None
            
    except sqlite3.Error as e:
        error_msg = f"Failed to get data for user '{username}': {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


def user_exists(username: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Check if a user exists in the database
    
    Args:
        username: Username to check
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if user exists, False otherwise
        
    Raises:
        DatabaseError: If database query fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM users WHERE username = ?
            ''', (username,))
            
            return cursor.fetchone() is not None
            
    except sqlite3.Error as e:
        error_msg = f"Failed to check if user '{username}' exists: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)


def get_database_info(db_path: str = DEFAULT_DB_PATH) -> dict:
    """
    Get database information for debugging/monitoring
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        dict: Database information including table counts
        
    Raises:
        DatabaseError: If database query fails
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Get user count
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()['count']
            
            # Get data count
            cursor.execute('SELECT COUNT(*) as count FROM data')
            data_count = cursor.fetchone()['count']
            
            # Get database file size
            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            
            return {
                'database_path': db_path,
                'database_size_bytes': db_size,
                'user_count': user_count,
                'data_records_count': data_count,
                'database_exists': os.path.exists(db_path)
            }
            
    except sqlite3.Error as e:
        error_msg = f"Failed to get database info: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)