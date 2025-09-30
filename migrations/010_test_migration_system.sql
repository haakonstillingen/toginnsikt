-- Migration 010: Test Migration System
-- This is a safe test migration to verify the migration system works

-- Create a test table to verify migration execution
CREATE TABLE IF NOT EXISTS migration_test (
    id SERIAL PRIMARY KEY,
    test_message VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert a test record
INSERT INTO migration_test (test_message) 
VALUES ('Migration system test - ' || NOW()::text)
ON CONFLICT DO NOTHING;

-- Add a comment for documentation
COMMENT ON TABLE migration_test IS 'Test table to verify migration system functionality';
