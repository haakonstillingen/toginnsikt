-- Rollback script for migration 003_add_business_intelligence_fields.sql
-- WARNING: This will permanently delete all business intelligence data

-- Drop indexes first
DROP INDEX IF EXISTS idx_actual_departures_status;
DROP INDEX IF EXISTS idx_actual_departures_reason;

-- Remove business intelligence columns from actual_departures table
ALTER TABLE actual_departures 
DROP COLUMN IF EXISTS departure_status,
DROP COLUMN IF EXISTS expected_delay_minutes,
DROP COLUMN IF EXISTS classification_reason,
DROP COLUMN IF EXISTS expected_departure_time;
