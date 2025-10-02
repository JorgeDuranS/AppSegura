#!/usr/bin/env python3
"""
SQLite Migration Script
Automatically creates SQLite database with proper schema
Can be run standalone or imported as a module
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Add the backend/src directory to the path so we can import database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

try:
    from database import init_database, get_database_info, DatabaseError
except ImportError:
    print("Warning: Could not import database module. Running with basic functionality.")
    init_database = None
    get_database_info = None
    DatabaseError = Exception

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_sql_file(db_path: str, sql_file_path: str) -> bool:
    """
    Execute SQL commands from a file
    
    Args:
        db_path: Path to SQLite database
        sql_file_path: Path to SQL file to execute
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(sql_file_path):
            logger.error(f"SQL file not found: {sql_file_path}")
            return False
            
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split SQL content by semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for statement in statements:
                # Skip comments and empty statements
                if statement.startswith('--') or not statement:
                    continue
                    
                try:
                    cursor.execute(statement)
                    logger.debug(f"Executed: {statement[:50]}...")
                except sqlite3.Error as e:
                    logger.warning(f"Statement failed (may be expected): {e}")
                    logger.debug(f"Failed statement: {statement}")
            
            conn.commit()
            logger.info(f"Successfully executed SQL file: {sql_file_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to execute SQL file {sql_file_path}: {e}")
        return False


def migrate_to_sqlite(db_path: str = 'app.db', force: bool = False) -> bool:
    """
    Main migration function to create SQLite database
    
    Args:
        db_path: Path where SQLite database should be created
        force: If True, recreate database even if it exists
        
    Returns:
        bool: True if migration successful, False otherwise
    """
    try:
        # Get absolute paths
        db_path = os.path.abspath(db_path)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(script_dir, 'sqlite_schema.sql')
        
        logger.info(f"Starting SQLite migration to: {db_path}")
        
        # Check if database already exists
        if os.path.exists(db_path) and not force:
            logger.info(f"Database already exists at {db_path}")
            
            # Try to get database info to verify it's working
            if init_database and get_database_info:
                try:
                    info = get_database_info(db_path)
                    logger.info(f"Existing database info: {info}")
                    return True
                except DatabaseError as e:
                    logger.warning(f"Existing database may be corrupted: {e}")
                    logger.info("Proceeding with migration...")
            else:
                logger.info("Cannot verify existing database. Use --force to recreate.")
                return True
        
        # Remove existing database if force is True
        if force and os.path.exists(db_path):
            logger.info(f"Removing existing database: {db_path}")
            os.remove(db_path)
        
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
        
        # Method 1: Use the database module if available
        if init_database:
            logger.info("Using database module for initialization...")
            try:
                success = init_database(db_path)
                if success:
                    logger.info("Database initialized successfully using database module")
                    
                    # Get and display database info
                    if get_database_info:
                        info = get_database_info(db_path)
                        logger.info(f"Database info: {info}")
                    
                    return True
                else:
                    logger.warning("Database module initialization failed, trying SQL file method...")
            except DatabaseError as e:
                logger.warning(f"Database module failed: {e}, trying SQL file method...")
        
        # Method 2: Use SQL file as fallback
        logger.info("Using SQL file for initialization...")
        success = run_sql_file(db_path, sql_file_path)
        
        if success:
            logger.info(f"SQLite migration completed successfully!")
            logger.info(f"Database created at: {db_path}")
            
            # Verify the database was created properly
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check if tables exist
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Created tables: {tables}")
                    
                    # Check foreign key support
                    cursor.execute("PRAGMA foreign_keys")
                    fk_status = cursor.fetchone()[0]
                    logger.info(f"Foreign key support: {'enabled' if fk_status else 'disabled'}")
                    
            except sqlite3.Error as e:
                logger.warning(f"Could not verify database: {e}")
            
            return True
        else:
            logger.error("Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        return False


def main():
    """Command line interface for the migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate to SQLite database')
    parser.add_argument(
        '--db-path', 
        default='app.db',
        help='Path to SQLite database file (default: app.db)'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force recreation of database even if it exists'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = migrate_to_sqlite(args.db_path, args.force)
    
    if success:
        print(f"✅ Migration completed successfully!")
        print(f"Database created at: {os.path.abspath(args.db_path)}")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()