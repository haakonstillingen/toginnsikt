# Database Migration System

This document describes the database migration system implemented to address [Issue #15](https://github.com/haakonstillingen/toginnsikt/issues/15).

## Overview

The migration system provides:
- **Versioned migrations** with tracking
- **Rollback capabilities** for safe schema changes
- **Integrity validation** to prevent data corruption
- **CLI management tools** for easy operation
- **Separate execution** from application startup

## Security Improvements

### Before (HIGH RISK)
- All migrations run on every application startup
- No tracking of applied migrations
- No rollback mechanism
- Risk of data corruption from repeated execution

### After (SECURE)
- Migrations tracked in `schema_migrations` table
- Only new migrations are executed
- Full rollback capabilities
- Integrity validation prevents corruption
- Separate migration execution from application startup

## Files Structure

```
migrations/
├── 001_create_delays_table.sql                    # Original migration
├── 001_create_delays_table_rollback.sql          # Rollback script
├── 002_create_commute_routes_table.sql           # Original migration
├── 002_create_commute_routes_table_rollback.sql  # Rollback script
├── 003_add_business_intelligence_fields.sql      # Original migration
├── 003_add_business_intelligence_fields_rollback.sql # Rollback script
├── 009_create_migration_tracking_table.sql       # Migration system setup
└── 009_create_migration_tracking_table_rollback.sql # Rollback script

migration_runner.py        # Core migration execution engine
migration_manager.py       # CLI management tool
run_migrations.py          # Standalone migration runner
test_migration_system.py   # Test suite
```

## Usage

### 1. Check Migration Status

```bash
python migration_manager.py status
```

Shows all migrations, their status, and rollback availability.

### 2. Run Pending Migrations

```bash
# Preview what will be executed
python migration_manager.py migrate --dry-run

# Execute pending migrations
python migration_manager.py migrate
```

### 3. Rollback a Migration

```bash
# Rollback specific migration (with confirmation)
python migration_manager.py rollback 003

# Rollback without confirmation
python migration_manager.py rollback 003 --yes
```

### 4. Create New Migration

```bash
python migration_manager.py create "add_users_table" --description "Add users table for authentication"
```

This creates:
- `migrations/010_add_users_table.sql`
- `migrations/010_add_users_table_rollback.sql`

### 5. Validate Migration Integrity

```bash
python migration_manager.py validate
```

Checks that applied migrations haven't been modified.

### 6. View Migration History

```bash
python migration_manager.py history
```

Shows when each migration was applied.

## Migration File Format

### Migration File (e.g., `010_add_users_table.sql`)

```sql
-- Migration 010: Add Users Table
-- Description of what this migration does

-- Add your migration SQL here
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts for authentication';
```

### Rollback File (e.g., `010_add_users_table_rollback.sql`)

```sql
-- Rollback script for migration 010_add_users_table.sql
-- WARNING: This will permanently delete data

-- Drop indexes first
DROP INDEX IF EXISTS idx_users_username;
DROP INDEX IF EXISTS idx_users_email;

-- Drop the table
DROP TABLE IF EXISTS users;
```

## Migration Tracking Table

The system uses a `schema_migrations` table to track applied migrations:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    rollback_script TEXT,
    description TEXT
);
```

## Integration with Cloud Build

The migration system is integrated into the Cloud Build pipeline:

1. **Build** container image
2. **Push** to Container Registry
3. **Run migrations** using the new system
4. **Deploy** to Cloud Run

This ensures migrations are applied before the new application version starts.

## Testing

Run the comprehensive test suite:

```bash
python test_migration_system.py
```

Tests include:
- Migration discovery
- Status checking
- Validation
- Dry run functionality
- Migration creation
- Rollback simulation
- Error handling

## Best Practices

### 1. Always Create Rollback Scripts
Every migration should have a corresponding rollback script.

### 2. Test Migrations Locally
```bash
# Test the migration
python migration_manager.py migrate --dry-run

# Apply the migration
python migration_manager.py migrate

# Test rollback
python migration_manager.py rollback 010
```

### 3. Use Descriptive Names
```bash
# Good
python migration_manager.py create "add_user_authentication"

# Bad
python migration_manager.py create "update1"
```

### 4. Validate Before Deployment
```bash
python migration_manager.py validate
```

### 5. Document Changes
Include clear descriptions in migration files.

## Error Recovery

### If Migration Fails
1. Check the logs for specific error
2. Fix the migration file
3. Re-run the migration

### If Rollback is Needed
1. Identify the problematic migration
2. Run rollback: `python migration_manager.py rollback VERSION`
3. Fix the issue
4. Re-apply the migration

### If Database is Corrupted
1. Restore from backup
2. Run migrations from the beginning
3. Verify data integrity

## Security Considerations

- **Checksum validation** prevents modified migrations from running
- **Rollback scripts** allow safe recovery
- **Separate execution** prevents application startup issues
- **Transaction safety** ensures atomic operations
- **Version tracking** provides audit trail

## Migration from Old System

The system includes a baseline migration (version 000) that marks migrations 001-008 as applied before the versioning system. This allows seamless transition without re-running existing migrations.

## Troubleshooting

### Common Issues

1. **"No migrations found"**
   - Check that migration files are in the `migrations/` directory
   - Verify file naming convention: `NNN_description.sql`

2. **"Migration integrity check failed"**
   - A migration file has been modified since application
   - Check the file hasn't been accidentally edited
   - Re-apply the migration if changes are intentional

3. **"Database connection failed"**
   - Check database credentials in `config_cloud.py`
   - Verify database is running and accessible

4. **"No rollback script available"**
   - Create a rollback script for the migration
   - Follow the naming convention: `NNN_description_rollback.sql`

### Getting Help

- Check logs in `migration_runner.log`
- Use `--verbose` flag for detailed output
- Run the test suite to verify system health
