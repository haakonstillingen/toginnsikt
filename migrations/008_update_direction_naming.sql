-- Migration 008: Update direction naming to use geographical references
-- Change from time-based (morning/afternoon) to geographical (westbound/eastbound)
-- This makes the naming more intuitive and location-based

-- Update morning route (Myrvoll → Oslo S) to westbound
UPDATE commute_routes 
SET direction = 'westbound'
WHERE direction = 'morning' AND route_name = 'Morning Commute';

-- Update afternoon route (Oslo S → Myrvoll) to eastbound  
UPDATE commute_routes 
SET direction = 'eastbound'
WHERE direction = 'afternoon' AND route_name = 'Afternoon Commute';

-- Verify the changes
SELECT route_name, direction, source_station_name, target_station_name, final_destination_pattern
FROM commute_routes 
ORDER BY direction;
