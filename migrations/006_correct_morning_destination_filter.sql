-- Migration 006: Correct morning route destination filtering
-- The morning route should filter for trains going to Stabekk or Lysaker (final destinations)
-- Oslo S is just an intermediate stop on the route to these destinations

-- Update the morning commute route to use correct destination pattern
UPDATE commute_routes 
SET final_destination_pattern = 'Lysaker|Stabekk' 
WHERE direction = 'morning' AND route_name = 'Morning Commute';

-- Verify the change
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
ORDER BY direction;
