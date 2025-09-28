-- Migration 007: Fix route directions that got swapped
-- Morning route should be Myrvoll → Oslo S (going to Stabekk/Lysaker)
-- Afternoon route should be Oslo S → Myrvoll (going to Ski)

-- Fix morning route: Myrvoll → Oslo S
UPDATE commute_routes 
SET source_station_id = 'NSR:StopPlace:59638',
    source_station_name = 'Myrvoll',
    target_station_id = 'NSR:StopPlace:337',
    target_station_name = 'Oslo S',
    final_destination_pattern = 'Lysaker|Stabekk'
WHERE direction = 'morning' AND route_name = 'Morning Commute';

-- Fix afternoon route: Oslo S → Myrvoll  
UPDATE commute_routes 
SET source_station_id = 'NSR:StopPlace:337',
    source_station_name = 'Oslo S',
    target_station_id = 'NSR:StopPlace:59638',
    target_station_name = 'Myrvoll',
    final_destination_pattern = 'Ski'
WHERE direction = 'afternoon' AND route_name = 'Afternoon Commute';

-- Verify the changes
SELECT route_name, direction, final_destination_pattern, source_station_name, target_station_name 
FROM commute_routes 
ORDER BY direction;
