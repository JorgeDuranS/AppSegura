-- SQLite Schema Migration Script
-- Converted from PostgreSQL schema (pg_base.sql)
-- This script creates the necessary tables for the secure web application

-- Enable foreign key constraints (must be set for each connection)
PRAGMA foreign_keys = ON;

-- Create users table
-- Converted from PostgreSQL SERIAL to SQLite INTEGER PRIMARY KEY AUTOINCREMENT
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create data table for encrypted user data
-- Converted from PostgreSQL BYTEA to SQLite BLOB
-- Added timestamps for better data tracking
CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_data_username ON data (username);
CREATE INDEX IF NOT EXISTS idx_data_created_at ON data (created_at);

-- Insert some sample data for testing (optional - can be removed in production)
-- Note: These are just examples and should be removed or replaced with proper test data
-- INSERT OR IGNORE INTO users (username, password) VALUES 
--     ('testuser', 'pbkdf2:sha256:260000$test$hashed_password_here');