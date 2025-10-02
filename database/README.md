# Database Migration to SQLite

This directory contains the SQLite migration files for converting the application from PostgreSQL to SQLite.

## Files

- `sqlite_schema.sql` - SQLite schema definition converted from PostgreSQL
- `migrate_to_sqlite.py` - Python script to automatically create and initialize the SQLite database
- `pg_base.sql` - Original PostgreSQL schema (kept for reference)

## Schema Changes

### PostgreSQL to SQLite Conversions

| PostgreSQL | SQLite | Notes |
|------------|--------|-------|
| `SERIAL PRIMARY KEY` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Auto-incrementing primary key |
| `BYTEA` | `BLOB` | Binary data storage |
| `VARCHAR(n)` | `VARCHAR(n)` | Text with length limit (advisory in SQLite) |

### New Features Added

- **Timestamps**: Added `created_at` and `updated_at` columns for better data tracking
- **Indexes**: Added performance indexes on frequently queried columns
- **Foreign Key Constraints**: Proper referential integrity with CASCADE delete
- **Error Handling**: Comprehensive error handling in migration script

## Usage

### Automatic Migration (Recommended)

```bash
# Run migration script
python database/migrate_to_sqlite.py

# With custom database path
python database/migrate_to_sqlite.py --db-path /path/to/database.db

# Force recreation of existing database
python database/migrate_to_sqlite.py --force

# Verbose output for debugging
python database/migrate_to_sqlite.py --verbose
```

### Manual Migration

```bash
# Create database and run schema
sqlite3 app.db < database/sqlite_schema.sql
```

### Using Python Database Module

```python
from backend.src.database import init_database

# Initialize database
success = init_database('app.db')
if success:
    print("Database initialized successfully")
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Table
```sql
CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
);
```

## Verification

After migration, you can verify the database was created correctly:

```bash
# Check tables exist
sqlite3 app.db ".tables"

# Check schema
sqlite3 app.db ".schema"

# Check foreign key support
sqlite3 app.db "PRAGMA foreign_keys;"
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the directory is writable
2. **Import Errors**: Make sure you're running from the project root
3. **Foreign Key Issues**: SQLite requires `PRAGMA foreign_keys = ON` for each connection

### Database Location

By default, the database is created as `app.db` in the project root. This can be changed by:

1. Modifying the `DEFAULT_DB_PATH` in `backend/src/database.py`
2. Using the `--db-path` argument with the migration script
3. Setting an environment variable (if implemented in the application)