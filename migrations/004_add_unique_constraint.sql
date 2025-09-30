-- Add unique constraint on planned_departure_id in actual_departures table
-- This allows ON CONFLICT to work properly
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_planned_departure_id'
    ) THEN
        ALTER TABLE actual_departures 
        ADD CONSTRAINT unique_planned_departure_id UNIQUE (planned_departure_id);
    END IF;
END $$;
