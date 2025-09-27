-- Migration 004: Remove restrictive destination filtering from morning route
-- This allows capturing all L2 departures from Myrvoll to Oslo S direction

-- Update the morning commute route to remove destination filtering
UPDATE commute_routes 
SET final_destination_pattern = '' 
WHERE direction = 'morning' AND route_name = 'Morning Commute';

-- Verify the change
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
ORDER BY direction;
