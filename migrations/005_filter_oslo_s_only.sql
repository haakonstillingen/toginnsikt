-- Migration 005: Filter for Oslo S bound departures only
-- This ensures we collect only the scheduled departures to Oslo S
-- Rush hours (6-9 AM, 3-6 PM): 4 departures per hour
-- Off-peak hours: 2 departures per hour

-- Update the morning commute route to filter for Oslo S only
UPDATE commute_routes 
SET final_destination_pattern = 'Oslo S' 
WHERE direction = 'morning' AND route_name = 'Morning Commute';

-- Verify the change
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
ORDER BY direction;
