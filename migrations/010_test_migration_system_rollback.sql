-- Rollback script for migration 010_test_migration_system.sql
-- This will clean up the test migration

-- Drop the test table
DROP TABLE IF EXISTS migration_test;
