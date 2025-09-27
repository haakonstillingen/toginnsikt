-- Add expected_departure_time column to actual_departures table
ALTER TABLE actual_departures 
ADD COLUMN IF NOT EXISTS expected_departure_time TIMESTAMP WITH TIME ZONE;

-- Add collection_status and retry tracking to planned_departures table
ALTER TABLE planned_departures 
ADD COLUMN IF NOT EXISTS collection_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_retry_time TIMESTAMP WITH TIME ZONE;

-- Create index for collection_status for better performance
CREATE INDEX IF NOT EXISTS idx_planned_departures_status ON planned_departures(collection_status);
