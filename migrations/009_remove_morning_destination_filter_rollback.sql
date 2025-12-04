-- Rollback script for migration 009_remove_morning_destination_filter.sql
-- Restores the destination filter pattern for Morning Commute route
-- WARNING: This will restore the restrictive filter that was causing missing departures

-- Restore the destination pattern filter for morning commute route
UPDATE commute_routes 
SET final_destination_pattern = 'Lysaker|Stabekk' 
WHERE route_name = 'Morning Commute' AND direction = 'westbound';

-- Verify the rollback
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
WHERE route_name = 'Morning Commute'
ORDER BY direction;

