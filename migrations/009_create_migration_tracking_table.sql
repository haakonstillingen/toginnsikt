-- Migration 009: Create migration tracking table
-- This migration creates the infrastructure for tracking applied migrations

-- Create migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    rollback_script TEXT,
    description TEXT
);

-- Create index for efficient version lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at);

-- Add comments for documentation
COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations for version control and rollback';
COMMENT ON COLUMN schema_migrations.version IS 'Migration version number (e.g., 001, 002, 003a)';
COMMENT ON COLUMN schema_migrations.filename IS 'Name of the migration file';
COMMENT ON COLUMN schema_migrations.checksum IS 'SHA-256 checksum of migration file for integrity verification';
COMMENT ON COLUMN schema_migrations.rollback_script IS 'SQL script to rollback this migration';
COMMENT ON COLUMN schema_migrations.description IS 'Human-readable description of what this migration does';

-- Insert a special record to mark the baseline (existing migrations)
-- This allows us to track that migrations 001-008 were applied before versioning
INSERT INTO schema_migrations (version, filename, description, applied_at) 
VALUES ('000', 'baseline', 'Baseline - migrations 001-008 applied before versioning system', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;
