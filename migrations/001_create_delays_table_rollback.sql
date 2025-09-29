-- Rollback script for migration 001_create_delays_table.sql
-- WARNING: This will permanently delete all data in the delays table

-- Drop indexes first
DROP INDEX IF EXISTS idx_delays_timestamp;
DROP INDEX IF EXISTS idx_delays_line_code;
DROP INDEX IF EXISTS idx_delays_direction;
DROP INDEX IF EXISTS idx_delays_timestamp_line;
DROP INDEX IF EXISTS idx_delays_line_timestamp;

-- Drop the delays table
DROP TABLE IF EXISTS delays;
