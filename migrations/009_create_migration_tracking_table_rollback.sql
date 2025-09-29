-- Rollback script for migration 009_create_migration_tracking_table.sql
-- WARNING: This will permanently delete all migration tracking data

-- Drop indexes first
DROP INDEX IF EXISTS idx_schema_migrations_version;
DROP INDEX IF EXISTS idx_schema_migrations_applied_at;

-- Drop the schema_migrations table
DROP TABLE IF EXISTS schema_migrations;
