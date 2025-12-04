-- Migration 009: Remove destination filtering from morning route
-- Collect ALL L2 departures from Myrvoll (they all go through Oslo S)
-- The destination filter was too restrictive, causing us to miss 2 departures per hour
-- VY.no shows 4 departures per hour, but we were only collecting 2

-- Update the morning commute route to collect all L2 trains (no destination filter)
UPDATE commute_routes 
SET final_destination_pattern = '' 
WHERE route_name = 'Morning Commute' AND direction = 'westbound';

-- Verify the change
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
WHERE route_name = 'Morning Commute'
ORDER BY direction;


