-- Add unique constraint on planned_departure_id in actual_departures table
-- This allows ON CONFLICT to work properly
ALTER TABLE actual_departures 
ADD CONSTRAINT unique_planned_departure_id UNIQUE (planned_departure_id);
