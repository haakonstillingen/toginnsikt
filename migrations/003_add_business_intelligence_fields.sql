-- Migration 003: Add business intelligence fields to actual_departures table
-- This migration adds the 3-tier classification system fields

-- Add business intelligence fields to actual_departures table
ALTER TABLE actual_departures 
ADD COLUMN IF NOT EXISTS departure_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS expected_delay_minutes INTEGER,
ADD COLUMN IF NOT EXISTS classification_reason VARCHAR(100);

-- Add expected_departure_time column if it doesn't exist
ALTER TABLE actual_departures 
ADD COLUMN IF NOT EXISTS expected_departure_time TIMESTAMP WITH TIME ZONE;

-- Create index on departure_status for efficient querying
CREATE INDEX IF NOT EXISTS idx_actual_departures_status ON actual_departures(departure_status);

-- Create index on classification_reason for analysis
CREATE INDEX IF NOT EXISTS idx_actual_departures_reason ON actual_departures(classification_reason);

-- Add comments for documentation
COMMENT ON COLUMN actual_departures.departure_status IS 'Business intelligence classification: on_time, delayed, cancelled, severely_delayed, unknown';
COMMENT ON COLUMN actual_departures.expected_delay_minutes IS 'Expected delay in minutes (from expected_departure_time)';
COMMENT ON COLUMN actual_departures.classification_reason IS 'Reason for the classification (e.g., actual_departure_on_time, expected_time_reasonable_cancellation)';
COMMENT ON COLUMN actual_departures.expected_departure_time IS 'Expected departure time from API (may differ from actual)';
